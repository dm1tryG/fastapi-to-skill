from __future__ import annotations

import re
from pathlib import Path

from ..models import APISpec


def _slugify_name(title: str) -> str:
    """Convert API title to a valid package/command name."""
    name = re.sub(r"[^a-zA-Z0-9]+", "-", title)
    return name.strip("-").lower()


def generate_pyproject(spec: APISpec, output_dir: Path) -> Path:
    """Generate a pyproject.toml so the CLI can be installed as a command."""
    name = _slugify_name(spec.title)
    content = f"""\
[project]
name = "{name}-cli"
version = "0.1.0"
description = "Auto-generated CLI for {spec.title}"
requires-python = ">=3.10"
dependencies = ["typer>=0.9.0", "httpx>=0.24", "rich>=13.0"]

[project.scripts]
{name} = "cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["."]
include = ["cli.py", "SKILL.md", "openapi.json"]
"""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "pyproject.toml"
    path.write_text(content, encoding="utf-8")
    return path
