# fastapi-to-skill

[![PyPI version](https://img.shields.io/pypi/v/fastapi-to-skill)](https://pypi.org/project/fastapi-to-skill/)
[![GitHub stars](https://img.shields.io/github/stars/dm1tryG/fastapi-to-skill)](https://github.com/dm1tryG/fastapi-to-skill)
[![Author](https://img.shields.io/badge/author-Dmitrii%20Galkin-blue)](https://github.com/dm1tryG)

> Convert any FastAPI app into a CLI + SKILL.md for AI agents — in one command.

![From API Chaos to Agent Skills](https://raw.githubusercontent.com/dm1tryG/fastapi-to-skill/main/assets/cover-problem.png)

```bash
pip install fastapi-to-skill
fastapi-to-skill generate main:app
```

![One Command. Agent-Ready.](https://raw.githubusercontent.com/dm1tryG/fastapi-to-skill/main/assets/cover-pipeline.png)

---

## The Problem

A year ago, APIs served frontends. Developers read docs, learned the UI, wrote integration code.

Now APIs serve AI agents. And agents don't read docs — they read **skill files**.

If your product has no `SKILL.md`, agents can't discover it, can't use it, and will use a competitor that does have one.

The new distribution channel is not the App Store. It's the agent skill registry.

---

## The Solution

`fastapi-to-skill` takes your existing FastAPI app and generates everything an AI agent needs to use your API:

| Output | What it is |
|--------|-----------|
| `cli.py` | Standalone Typer CLI — one command per endpoint, no deps on this tool |
| `SKILL.md` | Agent Skills file — works in Claude Code and any Agent Skills-compatible platform |

**No MCP server. No AI costs. No infrastructure. Just files.**

---

## Why FastAPI?

FastAPI auto-generates an OpenAPI spec from your Python type hints. You write:

```python
@app.post("/tasks")
def create_task(task: Task) -> TaskOut:
    ...
```

FastAPI gives you a full API contract for free — endpoints, parameters, request bodies, types, auth schemes. Always in sync with your code. No manual YAML.

`fastapi-to-skill` reads that spec with one call to `app.openapi()` and turns it into agent-ready tools. The whole pipeline is: **your type hints → OpenAPI spec → CLI + SKILL.md**.

Big thanks to [@sebastianramirez](https://github.com/tiangolo) for building FastAPI + Typer — an ecosystem where this kind of tooling is possible in a weekend.

---

## Quick Start

### Install

```bash
pip install fastapi-to-skill
# or for global CLI tools (recommended)
pipx install fastapi-to-skill
```

### Generate from a FastAPI app

```python
# main.py
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Task Manager API")

class Task(BaseModel):
    title: str
    done: bool = False

@app.post("/tasks")
def create_task(task: Task):
    ...

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    ...
```

```bash
fastapi-to-skill generate main:app
```

Output (folder name is derived from your API title):
```
skills/task-manager-api/
├── cli.py      ← standalone CLI
└── SKILL.md    ← agent skill file
```

### Use the generated CLI

```bash
cd skills/task-manager-api/
pip install typer httpx rich

# Run without a command — shows SKILL.md (AI-friendly)
python cli.py

# List all commands
python cli.py --help

# See body schema for any command
python cli.py create-task --help
# Body fields:
#   title: string (required)
#   done: boolean  default: False

# Call the API
python cli.py create-task --body '{"title": "Ship the feature"}'
python cli.py get-task 1
python cli.py list-tasks --done false

# Search commands by keyword
python cli.py search "task"
```

### Other options

```bash
# Preview without writing files
fastapi-to-skill generate main:app --dry-run

# Validate spec only
fastapi-to-skill generate main:app --validate

# Override base URL
fastapi-to-skill generate main:app --base-url https://api.myapp.com
```

---

## Authentication

Set your credentials via environment variables before calling any command:

```bash
# API key
export MYAPI_API_KEY="sk-your-key"

# Bearer token
export MYAPI_TOKEN="your-token"

# Custom base URL
export MYAPI_BASE_URL="https://api.myapp.com"
```

The env var prefix is derived from your API title automatically.

---

## How the SKILL.md works

When an AI agent encounters your CLI, it runs:

```bash
task-manager-api          # reads SKILL.md, understands the API
task-manager-api --help   # sees all available commands
task-manager-api create-task --help  # sees body schema
```

No human needed. The agent discovers capabilities, reads the contract, and starts calling commands.

The `SKILL.md` follows the [Agent Skills open standard](https://agentskills.io) — compatible with Claude Code and any platform that supports it.

---

## License

MIT

---

*Built on [FastAPI](https://github.com/fastapi/fastapi) + [Typer](https://github.com/fastapi/typer) by Sebastian Ramirez.*
