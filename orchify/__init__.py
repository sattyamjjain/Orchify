"""Orchify: AI-driven Dockerfile and .dockerignore generator for Python projects."""

__version__ = "0.2.0"

# Optional: expose your main entry-point and generator helper at package level
from .cli import main  # so you can programmatically invoke Orchify
from .generator import render_dockerfile

__all__ = ["__version__", "main", "render_dockerfile"]
