import jinja2
from pathlib import Path


def render_dockerfile(context: dict, template_dir: Path):
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(template_dir)),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    docker_tmpl = env.get_template("Dockerfile.j2")
    ignore_tmpl = env.get_template(".dockerignore.j2")

    dockerfile = docker_tmpl.render(**context)
    dockerignore = ignore_tmpl.render(**context)
    return dockerfile, dockerignore
