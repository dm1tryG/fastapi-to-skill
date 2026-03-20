from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import yaml


def load_from_file(path: Path) -> dict:
    """Load OpenAPI spec from a JSON or YAML file."""
    text = path.read_text(encoding="utf-8")
    if path.suffix in (".yaml", ".yml"):
        return yaml.safe_load(text)
    return json.loads(text)


def load_from_fastapi(app_path: str) -> dict:
    """Load OpenAPI spec from a FastAPI app (e.g. 'myapp:app' or 'myapp.main:app')."""
    module_path, _, attr_name = app_path.partition(":")
    if not attr_name:
        attr_name = "app"

    # Add CWD to sys.path so local imports work
    cwd = str(Path.cwd())
    if cwd not in sys.path:
        sys.path.insert(0, cwd)

    module = importlib.import_module(module_path)
    app = getattr(module, attr_name)
    return app.openapi()


def load_spec(app_path: str | None = None, spec_path: Path | None = None) -> dict:
    """Load OpenAPI spec from either a FastAPI app or a spec file."""
    if spec_path:
        return load_from_file(spec_path)
    if app_path:
        return load_from_fastapi(app_path)
    raise ValueError("Either app_path or spec_path must be provided")
