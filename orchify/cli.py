import json
import re

import click
import asyncio
from pathlib import Path
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.tools.mcp import MCPTools
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@click.group()
def main():
    """Orchify CLI"""
    pass


@main.command()
def hello():
    """Prints a welcome message."""
    click.echo("👋 Welcome to Orchify!")


@main.command()
@click.option(
    "--prompt", "-p", default="Read and summarize the entire project structure."
)
@click.option(
    "--dir",
    "-d",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
)
def scan(prompt: str, dir: str):
    """
    Spin up an MCP filesystem server via Agno, stream back
    agent responses, and write orchify.json metadata.
    """

    async def _run_mcp():
        project_path = Path(dir).resolve()
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", str(project_path)],
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # 1. Initialize MCP tools & agent
                mcp_tools = MCPTools(session=session)
                await mcp_tools.initialize()
                agent = Agent(
                    model=Claude(id="claude-3-7-sonnet-latest"),
                    tools=[mcp_tools],
                )

                # 2. Stream the natural-language summary
                await agent.aprint_response(prompt, stream=True)

        # 3. AFTER the AI summary, collect structured metadata
        #    (you can make this smarter by inspecting session.tools, etc.)
        #    For now we'll use simple heuristics:
        dep_file = (
            "requirements.txt" if (project_path / "requirements.txt").exists() else None
        )
        install_cmd = f"pip install --no-cache-dir -r {dep_file}" if dep_file else ""
        src_dirs = []
        for p in project_path.iterdir():
            name = p.name
            # skip hidden, egg-info, IDE, and tests
            if (
                name.startswith(".")
                or name.endswith(".egg-info")
                or name in {"tests", ".idea"}
            ):
                continue
            # include packages (has __init__.py) or any .py script
            if p.is_dir():
                if (p / "__init__.py").exists() or any(
                    f.suffix == ".py" for f in p.iterdir()
                ):
                    src_dirs.append(name)
            elif p.suffix == ".py":
                src_dirs.append(name)
        # Example entrypoint: try to look for a uvicorn or flask runner in your codebase.
        entrypoint = ["python", "-m", "orchify.cli", "hello"]

        metadata = {
            "python_base": "python:3.11-slim",
            "dependency_file": dep_file,
            "install_cmd": install_cmd,
            "source_dirs": src_dirs,
            "entrypoint_list": entrypoint,
            "cache_dirs": ["__pycache__"],
        }

        # 4. Write orchify.json next to your project root
        meta_path = project_path / "orchify.json"
        meta_path.write_text(json.dumps(metadata, indent=2))
        click.echo(f"🔖 Wrote metadata to {meta_path}")

    # run it
    asyncio.run(_run_mcp())


@main.command()
@click.option("--model-id", "-m", default="claude-3-7-sonnet-latest")
@click.option("--output", "-o", default="Dockerfile")
def gen(model_id: str, output: str):
    meta = json.loads(Path("orchify.json").read_text())
    prompt = f"""
        You are an expert DevOps engineer. Generate a production-grade, multi-stage Dockerfile and a matching .dockerignore for a generic Python project, **with absolutely no commentary**—just the files themselves.
        
        Project metadata:
        • Base image: {meta['python_base']}
        • Install command: {meta['install_cmd']}
        • Source dirs: {meta['source_dirs']}
        • Entrypoint: {meta['entrypoint_list']}
        • Cache dirs: {meta['cache_dirs']}
        
        Output **only** two sections wrapped in these tags:
        
        <DOCKERFILE>
        # content of Dockerfile …
        </DOCKERFILE>
        <DOCKERIGNORE>
        # content of .dockerignore …
        </DOCKERIGNORE>
        """

    agent = Agent(model=Claude(id=model_id), tools=[])
    raw = agent.run(prompt)
    text = raw.content if hasattr(raw, "content") else str(raw)

    # extract Dockerfile
    m_df = re.search(r"<DOCKERFILE>(.*?)</DOCKERFILE>", text, re.DOTALL)
    if not m_df:
        raise click.ClickException("Missing <DOCKERFILE> section")
    dockerfile = m_df.group(1).strip()

    # extract .dockerignore
    m_di = re.search(r"<DOCKERIGNORE>(.*?)</DOCKERIGNORE>", text, re.DOTALL)
    if not m_di:
        raise click.ClickException("Missing <DOCKERIGNORE> section")
    dockerignore = m_di.group(1).strip()

    Path(output).write_text(dockerfile)
    Path(".dockerignore").write_text(dockerignore)
    click.echo("✨ Written Dockerfile and .dockerignore.")
