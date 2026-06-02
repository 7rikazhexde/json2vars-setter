#!/usr/bin/env python3
"""
json2vars_setter CLI tool.
Unified interface that runs the package features in-process via Typer.
"""

from typing import Callable, List

import typer

from json2vars_setter.features import matrix_update, version_cache

# Create application instance
app = typer.Typer(
    name="json2vars",
    help="json2vars_setter CLI: Manages multiple scripts within the project",
)

# Pass-through settings: forward every argument to the feature's own argparse
# parser (including --help/-h, by disabling Typer's built-in help option).
_PASSTHROUGH = {
    "allow_extra_args": True,
    "ignore_unknown_options": True,
    "help_option_names": [],
}


def _run_feature(name: str, run: Callable[[List[str]], None], args: List[str]) -> None:
    """Run a feature's ``main`` in-process, mapping failures to a Typer exit.

    argparse raises ``SystemExit`` for ``--help`` (code 0) and usage errors
    (non-zero); any other exception is surfaced as a CLI error.
    """
    try:
        run(args)
    except SystemExit as exc:
        code = exc.code
        if code is None or code == 0:
            return
        raise typer.Exit(code if isinstance(code, int) else 1)
    except Exception as exc:  # noqa: BLE001 - surface any failure as a CLI error
        typer.echo(f"Error: Failed to execute {name} ({exc})", err=True)
        raise typer.Exit(1)


@app.command(
    "cache-version",
    help="version_cache: Caches version information of programming languages",
    context_settings=_PASSTHROUGH,
)
def cache_version(ctx: typer.Context) -> None:
    """Run the version-cache feature. All arguments are passed through as-is."""
    _run_feature("version_cache", version_cache.main, ctx.args)


@app.command(
    "update-matrix",
    help="matrix_update: Dynamically updates matrix.json with the latest or stable versions",
    context_settings=_PASSTHROUGH,
)
def update_matrix(ctx: typer.Context) -> None:
    """Run the update-matrix feature. All arguments are passed through as-is."""
    _run_feature("matrix_update", matrix_update.main, ctx.args)


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
