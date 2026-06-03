"""Command-line interface for api-gen-agent.

Usage examples::

    # Basic usage
    api-gen-agent create "A REST API for managing blog posts with tags"

    # Custom output directory and framework
    api-gen-agent create "A bookstore inventory API" --output ./my_api

    # Verbose mode
    api-gen-agent create "A task management API" --verbose
"""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .agent import ApiGenAgent

console = Console()


@click.group()
@click.version_option(package_name="api-gen-agent")
def cli() -> None:
    """api-gen-agent: Generate FastAPI boilerplate from plain English."""


@cli.command("create")
@click.argument("description")
@click.option(
    "--framework",
    default="fastapi",
    show_default=True,
    help="Target framework (currently only fastapi is supported).",
)
@click.option(
    "--output",
    default="./generated",
    show_default=True,
    type=click.Path(file_okay=False, path_type=Path),
    help="Output directory for generated files.",
)
@click.option(
    "--model",
    default="claude-sonnet-4-6",
    show_default=True,
    help="Anthropic model to use.",
)
@click.option(
    "--api-key",
    envvar="ANTHROPIC_API_KEY",
    default=None,
    help="Anthropic API key (defaults to ANTHROPIC_API_KEY env var).",
)
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="Print agent reasoning and tool calls.",
)
def create(
    description: str,
    framework: str,
    output: Path,
    model: str,
    api_key: str | None,
    verbose: bool,
) -> None:
    """Generate a FastAPI project from a plain-English API DESCRIPTION.

    DESCRIPTION is a sentence or paragraph describing the API you want to build.

    Example:

        api-gen-agent create "A REST API for a pet store that manages pets,
        owners, and appointments."
    """
    if framework.lower() != "fastapi":
        console.print(
            f"[yellow]Warning:[/yellow] Only 'fastapi' is supported; "
            f"ignoring --framework={framework!r}."
        )
        framework = "fastapi"

    console.print(
        Panel(
            f"[bold]API Description:[/bold]\n{description}",
            title="api-gen-agent",
            border_style="blue",
        )
    )

    agent = ApiGenAgent(
        api_key=api_key,
        model=model,
        output_dir=output,
        framework=framework,
        verbose=verbose,
    )

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task(description="Generating API...", total=None)
            result = agent.generate(description)

    except anthropic_import_error() as exc:  # noqa: F821 – dynamic name resolved below
        console.print(f"[red]Error:[/red] {exc}")
        sys.exit(1)
    except Exception as exc:  # pylint: disable=broad-except
        console.print(f"[red]Unexpected error:[/red] {exc}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)

    # Print results table
    table = Table(title="Generated Files", show_lines=True)
    table.add_column("File", style="cyan")
    for file_path in result["files_written"]:
        table.add_row(file_path)

    console.print(table)
    console.print(
        Panel(
            result["summary"] or "Generation complete.",
            title="Summary",
            border_style="green",
        )
    )
    console.print(
        f"\n[bold green]Output directory:[/bold green] {result['output_dir']}"
    )


def anthropic_import_error():
    """Return the anthropic APIError class for exception handling."""
    try:
        import anthropic
        return anthropic.APIError
    except ImportError:
        return Exception


def main() -> None:
    """Entry point for the api-gen-agent CLI."""
    cli()


if __name__ == "__main__":
    main()
