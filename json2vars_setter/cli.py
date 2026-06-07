#!/usr/bin/env python3
"""
json2vars_setter CLI.

A guided entry point that runs the package features in-process via Typer.
"""

from importlib.metadata import version as _dist_version
from typing import Callable, List, Optional

import typer

from json2vars_setter.features import github_output, matrix_update, version_cache

# Create application instance
app = typer.Typer(
    name="json2vars",
    help=(
        "json2vars-setter CLI - manage the language versions behind your "
        "GitHub Actions matrix.\n\n"
        "Which command?  update-matrix: rewrite matrix.json with the latest/"
        "stable versions.  cache-version: maintain a version cache and matrix "
        "template (fewer API calls).  parse: expand a JSON file into "
        "GITHUB_OUTPUT (automatic inside the Action).  "
        "Run 'json2vars usage' for task-oriented examples."
    ),
    no_args_is_help=True,
)

# Pass-through settings: forward every argument to the feature's own argparse
# parser (including --help/-h, by disabling Typer's built-in help option).
_PASSTHROUGH = {
    "allow_extra_args": True,
    "ignore_unknown_options": True,
    "help_option_names": [],
}


def _version_callback(value: bool) -> None:
    """Print the installed package version and exit (for --version/-V)."""
    if value:
        typer.echo(f"json2vars-setter {_dist_version('json2vars-setter')}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Show the installed json2vars-setter version and exit.",
    ),
) -> None:
    """json2vars-setter command-line interface."""


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
        raise typer.Exit(code if isinstance(code, int) else 1) from exc
    except Exception as exc:
        typer.echo(f"Error: Failed to execute {name} ({exc})", err=True)
        raise typer.Exit(1) from exc


@app.command(
    "update-matrix",
    help="Rewrite matrix.json in place with the latest/stable versions from official sources.",
    context_settings=_PASSTHROUGH,
)
def update_matrix(ctx: typer.Context) -> None:
    """Run the matrix-update feature. All arguments are passed through as-is."""
    _run_feature("matrix_update", matrix_update.main, ctx.args)


@app.command(
    "cache-version",
    help="Maintain a TTL version cache and generate a matrix template (fewer API calls).",
    context_settings=_PASSTHROUGH,
)
def cache_version(ctx: typer.Context) -> None:
    """Run the version-cache feature. All arguments are passed through as-is."""
    _run_feature("version_cache", version_cache.main, ctx.args)


@app.command(
    "parse",
    help="Expand a JSON file into GITHUB_OUTPUT (runs automatically inside the Action).",
    context_settings=_PASSTHROUGH,
)
def parse(ctx: typer.Context) -> None:
    """Run the github-output feature. Pass the JSON file path (and optional --debug)."""
    _run_feature("github_output", github_output.main, ctx.args)


@app.command("usage", help="Task-oriented guide: which command for which goal.")
def usage() -> None:
    """Print a task-oriented guide mapping goals to commands."""
    typer.echo("=== json2vars-setter - what do you want to do? ===\n")

    typer.echo("Pin the latest/stable versions into matrix.json:")
    typer.echo("  json2vars update-matrix --all latest")
    typer.echo("  json2vars update-matrix --python stable --nodejs latest")
    typer.echo("")

    typer.echo("Maintain a version cache and matrix template (fewer GitHub API calls):")
    typer.echo("  json2vars cache-version")
    typer.echo("  json2vars cache-version --languages python nodejs --force")
    typer.echo("")

    typer.echo("Parse a JSON file into GITHUB_OUTPUT (automatic inside the Action):")
    typer.echo(
        "  GITHUB_OUTPUT=out.txt json2vars parse .github/json2vars-setter/matrix.json"
    )
    typer.echo("")

    typer.echo("See every option for a command:")
    typer.echo("  json2vars update-matrix --help")
    typer.echo("  json2vars cache-version --help")
    typer.echo("")

    typer.echo("Enable <Tab> completion of these command names (bash / PowerShell):")
    typer.echo("  json2vars --install-completion")


if __name__ == "__main__":
    app()
