from __future__ import annotations

import importlib
import sys
from pathlib import Path


def load_spec(app_path: str) -> dict:
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
