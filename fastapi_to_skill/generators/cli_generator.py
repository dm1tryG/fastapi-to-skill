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


def _schema_type_str(field: dict) -> str:
    """Get a human-readable type string from a resolved JSON Schema field."""
    # Enum
    if "enum" in field:
        values = ", ".join(repr(v) for v in field["enum"])
        return f"enum({values})"
    ftype = field.get("type", "any")
    # Nested object with properties
    if ftype == "object" and "properties" in field:
        title = field.get("title", "object")
        return title
    # Array
    if ftype == "array":
        items = field.get("items", {})
        inner = _schema_type_str(items)
        return f"list[{inner}]"
    return ftype


def _body_schema_help(schema: dict, *, _indent: int = 0) -> str:
    """Render a JSON schema into a readable body description for docstrings."""
    if not schema:
        return ""
    props = schema.get("properties", {})
    required = set(schema.get("required", []))
    if not props:
        return ""
    prefix = "  " * _indent
    lines = []
    if _indent == 0:
        lines.append("Body fields:")
    for name, field in props.items():
        ftype = _schema_type_str(field)
        req = " (required)" if name in required else ""
        default = f"  default: {field['default']}" if "default" in field else ""
        desc = f"  — {field['description']}" if field.get("description") else ""
        lines.append(f"  {prefix}{name}: {ftype}{req}{default}{desc}")
        # Show nested object fields inline (one level)
        if field.get("type") == "object" and "properties" in field and _indent < 1:
            nested = _body_schema_help(field, _indent=_indent + 1)
            if nested:
                lines.append(nested)
    return "\\n".join(lines)


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
    env.filters["body_schema_help"] = _body_schema_help

    template = env.get_template("cli.py.jinja2")

    result = template.render(
        spec=spec,
        env_prefix=_env_prefix(spec.title),
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "cli.py"
    output_path.write_text(result, encoding="utf-8")
    return output_path
