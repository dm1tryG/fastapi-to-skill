# fastapi-to-skill

Convert any OpenAPI spec or FastAPI app into a CLI + SKILL.md for AI agents.

## Why

APIs don't serve frontends anymore. They serve AI agents. If your product has no SKILL.md — agents can't discover and use it.

This tool takes your OpenAPI spec (or FastAPI app directly) and generates:
- **cli.py** — standalone Typer CLI, one command per endpoint
- **SKILL.md** — skill file for Claude Code, OpenClaw, or any platform supporting the [Agent Skills](https://agentskills.io) standard

No MCP server. No AI costs. No infrastructure. Just files.

## Quick Start

```bash
pip install fastapi-to-skill
```

From an OpenAPI spec:
```bash
fastapi-to-skill generate --spec openapi.json -o ./skills/myapi/
```

From a FastAPI app:
```bash
fastapi-to-skill generate myapp:app -o ./skills/myapi/
```

Choose your target platform:
```bash
fastapi-to-skill generate --spec openapi.json -t claude-code   # default
fastapi-to-skill generate --spec openapi.json -t openclaw
```

Use the generated CLI:
```bash
pip install typer httpx rich
python skills/myapi/cli.py --help
python skills/myapi/cli.py search "users"
```

## License

MIT
