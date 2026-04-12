from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint

from . import __version__
from .generators import SkillTarget, generate_cli, generate_pyproject, generate_skill
from .parser import parse_spec
from .spec_loader import load_spec

app = typer.Typer(
    name="fastapi-to-skill",
    help="Convert FastAPI apps and OpenAPI specs into CLI tools and AI agent skills.",
)


@app.command()
def generate(
    app_path: str = typer.Argument(..., help="FastAPI app path, e.g. myapp:app"),
    output: Path = typer.Option("./skills/", "-o", "--output", help="Output directory"),
    target: SkillTarget = typer.Option("claude-code", "--target", "-t", help="Skill target: claude-code or openclaw"),
    base_url: Optional[str] = typer.Option(None, "--base-url", help="Override API base URL"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing files"),
    validate: bool = typer.Option(False, "--validate", help="Validate spec only, do not generate"),
):
    """Generate CLI + SKILL.md from a FastAPI app."""
    # Load
    rprint("[blue]Loading spec...[/blue]")
    try:
        raw = load_spec(app_path)
    except Exception as e:
        rprint(f"[red]Failed to load spec:[/red] {e}")
        raise typer.Exit(1)

    # Parse
    api_spec = parse_spec(raw)
    if base_url:
        api_spec.base_url = base_url

    rprint(f"  Title: [bold]{api_spec.title}[/bold] v{api_spec.version}")
    rprint(f"  Base URL: {api_spec.base_url}")
    rprint(f"  Endpoints: {len(api_spec.endpoints)}")
    rprint(f"  Auth schemes: {len(api_spec.auth_schemes)}")
    rprint(f"  Target: [cyan]{target}[/cyan]")

    if validate:
        rprint("[green]Spec is valid![/green]")
        raise typer.Exit(0)

    if dry_run:
        rprint("\n[yellow]Dry run — would generate:[/yellow]")
        rprint(f"  {output / 'cli.py'}")
        rprint(f"  {output / 'SKILL.md'} ({target})")
        rprint(f"  {output / 'openapi.json'}")
        rprint("\n[yellow]Commands:[/yellow]")
        for ep in api_spec.endpoints:
            rprint(f"  {ep.operation_id.replace('_', '-'):30s}  {ep.method:6s} {ep.path}")
        raise typer.Exit(0)

    # Generate
    cli_path = generate_cli(api_spec, output)
    skill_path = generate_skill(api_spec, output, target=target)
    pyproject_path = generate_pyproject(api_spec, output)

    # Save spec copy
    output.mkdir(parents=True, exist_ok=True)
    spec_path = output / "openapi.json"
    spec_path.write_text(json.dumps(raw, indent=2, ensure_ascii=False), encoding="utf-8")

    import re
    cmd_name = re.sub(r"[^a-zA-Z0-9]+", "-", api_spec.title).strip("-").lower()

    rprint(f"\n[green]Generated ({target}):[/green]")
    rprint(f"  {cli_path}")
    rprint(f"  {skill_path}")
    rprint(f"  {spec_path}")
    rprint(f"  {pyproject_path}")
    rprint("\n[bold]Next steps:[/bold]")
    rprint(f"  cd {output} && pip install -e .")
    rprint(f"  {cmd_name}              # shows SKILL.md")
    rprint(f"  {cmd_name} --help       # lists all commands")


@app.command()
def version():
    """Show version."""
    rprint(f"fastapi-to-skill v{__version__}")


if __name__ == "__main__":
    app()
