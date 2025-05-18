import json
import re

import click
import asyncio
import logging
from pathlib import Path
from subprocess import check_output

import tiktoken
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Dict, Optional, Any

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.models.openai import OpenAIChat
from agno.tools.mcp import MCPTools
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class Repository(BaseModel):
    type: str = "git"
    url: Optional[HttpUrl]
    branch: Optional[str]


class Service(BaseModel):
    build: str = Field(default=".")
    image: Optional[str] = None
    ports: List[str] = Field(default_factory=list)
    environment: Dict[str, str] = Field(default_factory=dict)
    depends_on: List[str] = Field(default_factory=list)


class DockerCompose(BaseModel):
    version: str = Field(default="3.9")
    services: Dict[str, Service]
    volumes: Dict[str, Any] = Field(default_factory=dict)


class CIConfig(BaseModel):
    provider: str = Field(default="github-actions")
    workflow_file: str = Field(default=".github/workflows/ci.yml")
    stages: List[str] = Field(default_factory=lambda: ["lint", "test", "build"])
    lint_cmd: str = Field(default="flake8 .")
    test_cmd: str = Field(default="pytest --junitxml=reports/junit.xml")
    build_cmd: str
    artifact_paths: List[str] = Field(default_factory=lambda: ["reports/", "dist/"])


class CDConfig(BaseModel):
    provider: str = Field(default="github-actions")
    workflow_file: str = Field(default=".github/workflows/cd.yml")
    deploy_cmd: str = Field(default="kubectl apply -f k8s/")
    environments: List[str] = Field(default_factory=lambda: ["staging", "production"])


class SecurityConfig(BaseModel):
    scanner: str = Field(default="trivy")
    scan_cmd: str
    policies: List[str] = Field(default_factory=lambda: ["cis-docker", "cis-k8s"])


class Notifications(BaseModel):
    slack_webhook: Optional[HttpUrl] = None
    email: List[str] = Field(default_factory=list)


class Manifest(BaseModel):
    project_name: str
    version: str
    repository: Repository
    python_base: str
    dependency_file: Optional[str]
    install_cmd: str
    source_dirs: List[str]
    entrypoint_list: List[str]
    cache_dirs: List[str] = Field(
        default_factory=lambda: ["__pycache__", "~/.cache/pip"]
    )
    docker_compose: DockerCompose
    ci: CIConfig
    cd: CDConfig
    security: SecurityConfig
    notifications: Notifications


@click.group()
def main():
    pass


@main.command()
def hello():
    click.echo("👋 Welcome to Orchify!")


@main.command()
@click.option(
    "--dir",
    "-d",
    default=".",
    type=click.Path(exists=True, file_okay=False),
    help="Project directory to scan.",
)
def scan(dir: str):
    async def _run_scan():
        project_path = Path(dir).resolve()
        logger.info("Starting scan for %s", project_path)

        proj: Dict[str, Any] = {}
        try:
            import tomllib

            cfg = tomllib.loads((project_path / "pyproject.toml").read_bytes())
            proj = cfg.get("project", {}) or {}
            name = proj.get("name", project_path.name)
            version = proj.get("version", "0.0.0")
        except Exception:
            name, version = project_path.name, "0.0.0"
        logger.info("Project: %s v%s", name, version)

        try:
            url = check_output(
                ["git", "config", "--get", "remote.origin.url"],
                cwd=project_path,
                text=True,
            ).strip()
            branch = check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=project_path,
                text=True,
            ).strip()
        except Exception:
            url, branch = None, None
        repo = Repository(url=url, branch=branch)

        srv = StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", str(project_path)],
        )
        async with stdio_client(srv) as (r, w), ClientSession(r, w) as session:
            mcp = MCPTools(session=session)
            await mcp.initialize()
            logger.debug("MCP initialized")

            async def fetch_tree(path: Path, depth: Optional[int] = None) -> str:
                args = {"path": str(path)}
                if depth is not None:
                    args["depth"] = depth
                chunks = await session.call_tool("directory_tree", args)
                return "".join(
                    getattr(c, "text", getattr(c, "content", str(c))) for c in chunks
                )

            full_tree = await fetch_tree(project_path)
            files = [
                project_path / l.strip()
                for l in full_tree.splitlines()
                if l.strip() and not l.strip().endswith("/")
            ]
            logger.info("Found %d files", len(files))

            preview_chunks: List[str] = []
            for f in files[:5]:
                try:
                    folder = project_path / f.relative_to(project_path).parents[0]
                    preview_chunks.append(await fetch_tree(folder, depth=1))
                except Exception as e:
                    logger.error("Preview fetch failed for %s: %s", f, e)
            small_preview = "".join(preview_chunks)

            enc = tiktoken.encoding_for_model("gpt-4")
            token_count = len(enc.encode(full_tree + small_preview))
            logger.info("Estimated tokens: %d", token_count)

            if token_count <= 200_000:
                model = Claude(id="claude-3-7-sonnet-latest")
            else:
                model = OpenAIChat(id="gpt-4.1")
            logger.info("Using model: %s", model.id)

            dep_path = project_path / "requirements.txt"
            dep_file = dep_path.name if dep_path.exists() else None
            install_cmd = (
                f"pip install --no-cache-dir -r {dep_file}" if dep_file else ""
            )

            services = {name: Service(build=".", ports=["8000:8000"], depends_on=[])}
            compose = DockerCompose(services=services)
            ci = CIConfig(build_cmd=f"docker build -t {name}:$GITHUB_SHA .")
            cd = CDConfig()
            sec = SecurityConfig(scan_cmd=f"trivy image {name}:latest")
            notif = Notifications()

            raw_dirs = await fetch_tree(project_path, depth=1)
            source_dirs = [
                d.rstrip("/") for d in raw_dirs.splitlines() if d.strip().endswith("/")
            ]

            entrypoints = [
                f.name for f in files if f.parent == project_path and f.suffix == ".py"
            ]

            manifest = Manifest(
                project_name=name,
                version=version,
                repository=repo,
                python_base=proj.get("requires-python", "python:3.10-slim"),
                dependency_file=dep_file,
                install_cmd=install_cmd,
                source_dirs=source_dirs,
                entrypoint_list=entrypoints,
                docker_compose=compose,
                ci=ci,
                cd=cd,
                security=sec,
                notifications=notif,
            )

            out = project_path / "orchify.json"
            out.write_text(manifest.model_dump_json(indent=2))
            logger.info("Written orchify.json to %s", out)

    asyncio.run(_run_scan())


@main.command()
@click.option("--model-id", "-m", default="claude-3-7-sonnet-latest")
@click.option("--output", "-o", default="Dockerfile")
def gen(model_id: str, output: str):
    meta = json.loads(Path("orchify.json").read_text())
    cache_dirs = meta.get("cache_dirs", [])

    prompt = f"""
    You are an expert DevOps engineer. Generate a production-grade, multi-stage Dockerfile and matching .dockerignore for a Python project with no commentary.
    
    Project metadata:
    • Base: {meta['python_base']}
    • Install: {meta['install_cmd']}
    • Sources: {meta['source_dirs']}
    • Entrypoint: {meta['entrypoint_list']}
    • Cache: {cache_dirs}
    
    <DOCKERFILE>
    # Dockerfile content
    </DOCKERFILE>
    <DOCKERIGNORE>
    # .dockerignore content
    </DOCKERIGNORE>
    """
    agent = Agent(model=Claude(id=model_id), tools=[])
    raw = agent.run(prompt)
    text = raw.content if hasattr(raw, "content") else str(raw)

    dfm = re.search(r"<DOCKERFILE>(.*?)</DOCKERFILE>", text, re.DOTALL)
    if not dfm:
        raise click.ClickException("Missing <DOCKERFILE> section")
    dockerfile = dfm.group(1).strip()

    dim = re.search(r"<DOCKERIGNORE>(.*?)</DOCKERIGNORE>", text, re.DOTALL)
    if not dim:
        raise click.ClickException("Missing <DOCKERIGNORE> section")
    dockerignore = dim.group(1).strip()

    Path(output).write_text(dockerfile)
    Path(".dockerignore").write_text(dockerignore)
    logger.info("Written Dockerfile to %s and .dockerignore", output)


if __name__ == "__main__":
    main()
