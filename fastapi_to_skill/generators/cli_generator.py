from __future__ import annotations

import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from ..models import APISpec

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def _slugify(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text)
    return text.strip("_").lower()


def _env_prefix(title: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", title.upper()).strip("_")


def _escape_quotes(text: str) -> str:
    return text.replace('"', '\\"').replace("\n", " ")


def _python_repr(value) -> str:
    if value is None:
        return "None"
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, str):
        return f'"{value}"'
    return repr(value)


def generate_cli(spec: APISpec, output_dir: Path) -> Path:
    """Generate a Typer CLI file from an APISpec."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["slugify"] = _slugify
    env.filters["escape_quotes"] = _escape_quotes
    env.filters["python_repr"] = _python_repr

    template = env.get_template("cli.py.jinja2")

    result = template.render(
        spec=spec,
        env_prefix=_env_prefix(spec.title),
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "cli.py"
    output_path.write_text(result, encoding="utf-8")
    return output_path
