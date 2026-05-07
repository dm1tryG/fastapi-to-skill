from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint

from . import __version__
from .generators import generate_cli, generate_skill
from .parser import parse_spec
from .spec_loader import load_spec


def _slugify_title(title: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", title).strip("-").lower() or "skill"

app = typer.Typer(
    name="fastapi-to-skill",
    help="Convert FastAPI apps into Agent Skills (CLI + SKILL.md).",
)


@app.command()
def generate(
    app_path: str = typer.Argument(..., help="FastAPI app path, e.g. myapp:app"),
    output: Path = typer.Option("./skills/", "-o", "--output", help="Parent directory; a subfolder is created from the API title"),
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

    # Auto-create a named subdirectory from the API title.
    skill_dir = output / _slugify_title(api_spec.title)

    rprint(f"  Title: [bold]{api_spec.title}[/bold] v{api_spec.version}")
    rprint(f"  Base URL: {api_spec.base_url}")
    rprint(f"  Endpoints: {len(api_spec.endpoints)}")
    rprint(f"  Auth schemes: {len(api_spec.auth_schemes)}")
    rprint(f"  Output: [cyan]{skill_dir}[/cyan]")

    if validate:
        rprint("[green]Spec is valid![/green]")
        raise typer.Exit(0)

    if dry_run:
        rprint("\n[yellow]Dry run — would generate:[/yellow]")
        rprint(f"  {skill_dir / 'cli.py'}")
        rprint(f"  {skill_dir / 'SKILL.md'}")
        rprint("\n[yellow]Commands:[/yellow]")
        for ep in api_spec.endpoints:
            rprint(f"  {ep.operation_id.replace('_', '-'):30s}  {ep.method:6s} {ep.path}")
        raise typer.Exit(0)

    # Generate
    cli_path = generate_cli(api_spec, skill_dir)
    skill_path = generate_skill(api_spec, skill_dir)

    rprint("\n[green]Generated:[/green]")
    rprint(f"  {cli_path}")
    rprint(f"  {skill_path}")
    rprint("\n[bold]Next steps:[/bold]")
    rprint("  pip install typer httpx rich")
    rprint(f"  python {cli_path}              # shows SKILL.md")
    rprint(f"  python {cli_path} --help       # lists all commands")


@app.command()
def version():
    """Show version."""
    rprint(f"fastapi-to-skill v{__version__}")


if __name__ == "__main__":
    app()
