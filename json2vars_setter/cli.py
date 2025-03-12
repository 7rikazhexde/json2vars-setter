#!/usr/bin/env python3
"""
json2vars_setter CLI tool.
Unified interface for calling existing scripts using Typer.
"""

import subprocess
import sys
from pathlib import Path

import typer

# Create application instance
app = typer.Typer(
    name="json2vars",
    help="json2vars_setter CLI: Manages multiple scripts within the project",
)


@app.command(
    "cache-version",
    help="cache_version_info.py: Caches version information of programming languages",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def cache_version(
    ctx: typer.Context,
    help: bool = typer.Option(False, "--help", "-h", is_flag=True, help="Show help"),
) -> None:
    """
    Executes the cache_version_info.py script. All arguments are passed as is.
    """
    script_path = Path(__file__).parent / "cache_version_info.py"

    # If the --help flag is specified, display the original script's help
    if help:
        args = ["--help"]
    else:
        args = ctx.args

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)] + args,
            check=True,
        )
        sys.exit(result.returncode)
    except subprocess.CalledProcessError as e:
        typer.echo(f"Error: Failed to execute cache_version_info.py ({e})", err=True)
        sys.exit(e.returncode)


@app.command(
    "update-matrix",
    help="update_matrix_dynamic.py: Dynamically updates matrix.json with the latest or stable versions",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def update_matrix(
    ctx: typer.Context,
    help: bool = typer.Option(False, "--help", "-h", is_flag=True, help="Show help"),
) -> None:
    """
    Executes the update_matrix_dynamic.py script. All arguments are passed as is.
    """
    script_path = Path(__file__).parent / "update_matrix_dynamic.py"

    # If the --help flag is specified, display the original script's help
    if help:
        args = ["--help"]
    else:
        args = ctx.args

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)] + args,
            check=True,
        )
        sys.exit(result.returncode)
    except subprocess.CalledProcessError as e:
        typer.echo(f"Error: Failed to execute update_matrix_dynamic.py ({e})", err=True)
        sys.exit(e.returncode)


@app.command("usage", help="Displays available commands and their usage")
def usage() -> None:
    """Displays usage examples for all commands"""
    typer.echo("=== json2vars_setter Usage Examples ===\n")

    typer.echo("Available commands:")
    typer.echo("  cache-version    - Update cache version information")
    typer.echo("  update-matrix    - Update matrix JSON")
    typer.echo("  usage            - Display this usage information")
    typer.echo("\nAdd the --help option to display detailed help for each command:")
    typer.echo("  json2vars cache-version --help")
    typer.echo("  json2vars update-matrix --help")
    typer.echo("\nExamples:")

    typer.echo("● Cache Version Information:")
    typer.echo("  # Update version information for all languages")
    typer.echo("  json2vars cache-version")
    typer.echo("  # Force update for specific languages")
    typer.echo("  json2vars cache-version --languages python nodejs --force")
    typer.echo("")

    typer.echo("● Update Matrix:")
    typer.echo("  # Update all languages to the latest version")
    typer.echo("  json2vars update-matrix --all latest")
    typer.echo("  # Update specific languages with different strategies")
    typer.echo("  json2vars update-matrix --python stable --nodejs latest")


if __name__ == "__main__":
    app()
