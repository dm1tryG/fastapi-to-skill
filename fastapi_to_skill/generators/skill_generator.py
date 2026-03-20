from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Literal

from jinja2 import Environment, FileSystemLoader

from ..models import APISpec

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

SkillTarget = Literal["claude-code", "openclaw"]


def _slugify(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text)
    return text.strip("-").lower()


def _env_prefix(title: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", title.upper()).strip("_")


def _oneline(text: str) -> str:
    return " ".join(text.replace("\n", " ").split())


def _truncate(text: str, length: int = 1024) -> str:
    if len(text) <= length:
        return text
    return text[: length - 3] + "..."


def _group_by_tag(spec: APISpec) -> dict[str, list]:
    groups: dict[str, list] = defaultdict(list)
    for ep in spec.endpoints:
        tag = ep.tags[0] if ep.tags else "General"
        groups[tag].append(ep)
    return dict(groups)


def _get_env_vars(spec: APISpec, env_prefix: str) -> list[str]:
    """Collect all environment variables the generated CLI uses."""
    env_vars = [f"{env_prefix}_BASE_URL"]
    for auth in spec.auth_schemes:
        if auth.type == "apiKey":
            env_vars.append(f"{env_prefix}_API_KEY")
        elif auth.type in ("http", "oauth2"):
            env_vars.append(f"{env_prefix}_TOKEN")
    return env_vars


def _template_name(target: SkillTarget) -> str:
    return f"skill.{target}.md.jinja2"


def generate_skill(spec: APISpec, output_dir: Path, target: SkillTarget = "claude-code") -> Path:
    """Generate a SKILL.md file from an APISpec for the given target platform."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["slugify"] = _slugify
    env.filters["oneline"] = _oneline
    env.filters["truncate"] = _truncate

    template = env.get_template(_template_name(target))

    prefix = _env_prefix(spec.title)
    result = template.render(
        spec=spec,
        env_prefix=prefix,
        env_vars=_get_env_vars(spec, prefix),
        endpoints_by_tag=_group_by_tag(spec),
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "SKILL.md"
    output_path.write_text(result, encoding="utf-8")
    return output_path
