#!/usr/bin/env python3
"""
json2vars_setter CLI.

A guided entry point that runs the package features in-process via Typer.

Each feature module owns its own ``argparse`` parser (``build_parser()``) and
``main(argv)`` entry point (also used by ``python -m`` and the Action). To give
shell completion of the per-command **options** (``--languages``, ``--max-age``,
``--python`` …) *and their values*, this module bridges each argparse parser to
Typer's Click layer: it generates the matching ``TyperOption``s dynamically
(argparse stays the single source of truth), lets Click parse them, then
reconstructs the argv list and calls the feature's ``main()`` unchanged.

The bridged options are built as ``typer.core.TyperOption`` (not plain
``click.Option``) **on purpose**: Typer's completion only resolves the value of
an option when the parameter is a ``TyperOption``, and value completion for
``choices`` is supplied via each option's ``shell_complete`` callback. Building
plain ``click.Option``s makes option *names* complete but silently drops value
completion.
"""

import argparse
from importlib.metadata import version as _dist_version
from types import ModuleType
from typing import TYPE_CHECKING, Callable, Dict, List, Optional, cast

import typer
from typer.core import TyperArgument, TyperCommand, TyperGroup, TyperOption

if TYPE_CHECKING:
    from typer._click.core import Parameter  # pragma: no cover

from json2vars_setter.features import github_output, matrix_update, version_cache

# The top-level Typer app owns --version, Typer's
# --install-completion/--show-completion, and `usage`. The public entry point
# `app` (assigned at the bottom) is its Click group, augmented with the three
# bridged feature commands.
_typer_app = typer.Typer(
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


def _version_callback(value: bool) -> None:
    """Print the installed package version and exit (for --version/-V)."""
    if value:
        typer.echo(f"json2vars-setter {_dist_version('json2vars-setter')}")
        raise typer.Exit()


@_typer_app.callback()
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


def _iter_options(parser: argparse.ArgumentParser) -> List[argparse.Action]:
    """Return the parser's optional actions, skipping the auto -h/--help."""
    return [
        a
        for a in parser._actions
        if a.option_strings and not isinstance(a, argparse._HelpAction)
    ]


def _long_option(action: argparse.Action) -> str:
    """Pick the long (``--``) option string, falling back to the first one."""
    longs = [o for o in action.option_strings if o.startswith("--")]
    return longs[0] if longs else action.option_strings[0]


def _choice_completer(
    choices: List[str],
) -> Callable[[object, object, str], List[str]]:
    """Build a ``shell_complete`` callback that offers an option's choices.

    Typer invokes this with ``(ctx, param, incomplete)``; returning the matching
    choice strings is what makes ``--languages <TAB>`` / ``--python <TAB>``
    complete their values.
    """

    def complete(ctx: object, param: object, incomplete: str) -> List[str]:
        return [c for c in choices if c.startswith(incomplete)]

    return complete


def _make_option(action: argparse.Action) -> TyperOption:
    """Map a single argparse optional action to a ``TyperOption``."""
    decls = list(action.option_strings)
    completer = (
        _choice_completer([str(c) for c in action.choices])
        if action.choices is not None
        else None
    )
    if action.nargs == 0:  # store_true flag
        return TyperOption(
            param_decls=decls, is_flag=True, default=False, help=action.help
        )
    # int values round-trip through Click's INT; everything else (str, Path)
    # stays STRING — argparse re-validates/casts when main() runs.
    opt_type = int if action.type is int else str
    if action.nargs == "+":
        # Repeated option (e.g. --languages x --languages y); Click leaves this
        # as an empty tuple when unset.
        return TyperOption(
            param_decls=decls,
            type=opt_type,
            multiple=True,
            default=None,
            help=action.help,
            shell_complete=completer,
        )
    # Sentinel default so only user-supplied options are forwarded and argparse
    # applies its own defaults.
    return TyperOption(
        param_decls=decls,
        type=opt_type,
        default=None,
        help=action.help,
        shell_complete=completer,
    )


def _params_from_parser(parser: argparse.ArgumentParser) -> "List[Parameter]":
    """Generate Typer options mirroring an argparse parser (for completion)."""
    return [_make_option(action) for action in _iter_options(parser)]


def _argv_from_values(
    parser: argparse.ArgumentParser, values: Dict[str, object]
) -> List[str]:
    """Rebuild an argv list from Click-parsed values for the feature parser."""
    argv: List[str] = []
    for action in _iter_options(parser):
        value = values.get(action.dest)
        opt = _long_option(action)
        if action.nargs == 0:  # flag
            if value:
                argv.append(opt)
        elif action.nargs == "+":  # repeated -> one flag followed by all values
            if isinstance(value, (list, tuple)) and value:
                argv.append(opt)
                argv.extend(str(v) for v in value)
        elif value is not None:
            argv.extend([opt, str(value)])
    return argv


def _make_feature_command(
    name: str,
    parser: argparse.ArgumentParser,
    module: ModuleType,
    help_text: str,
) -> TyperCommand:
    """Build a Click command whose options are bridged from an argparse parser.

    ``module.main`` is resolved at call time (not captured) so tests can patch it.
    """

    def callback(**values: object) -> None:
        _run_feature(name, module.main, _argv_from_values(parser, values))

    return TyperCommand(
        name=name,
        params=_params_from_parser(parser),
        callback=callback,
        help=help_text,
    )


def _parse_command() -> TyperCommand:
    """Build the `parse` command (github_output has no argparse parser)."""

    def callback(json_file: str, debug: bool) -> None:
        argv = [json_file, *(["--debug"] if debug else [])]
        _run_feature("github_output", github_output.main, argv)

    return TyperCommand(
        name="parse",
        params=[
            TyperArgument(param_decls=["json_file"], type=str),
            TyperOption(
                param_decls=["--debug"],
                is_flag=True,
                default=False,
                help="Enable debug output.",
            ),
        ],
        callback=callback,
        help="Expand a JSON file into GITHUB_OUTPUT (runs automatically inside the Action).",
    )


@_typer_app.command("usage", help="Task-oriented guide: which command for which goal.")
def usage() -> None:
    """Print a task-oriented guide mapping goals to commands."""
    typer.echo("=== json2vars-setter - what do you want to do? ===\n")

    typer.echo("Pin the latest/stable versions into matrix.json:")
    typer.echo("  json2vars update-matrix --all latest")
    typer.echo("  json2vars update-matrix --python stable --nodejs latest")
    typer.echo("")

    typer.echo("Maintain a version cache and matrix template (fewer GitHub API calls):")
    typer.echo("  json2vars cache-version")
    typer.echo(
        "  json2vars cache-version --languages python --languages nodejs --force"
    )
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

    typer.echo("Enable <Tab> completion of commands and options (bash / PowerShell):")
    typer.echo("  json2vars --install-completion")


# Build the public entry point: the Typer app supplies the top-level options and
# `usage`; the three feature commands are bridged from their argparse parsers so
# their options (and values) participate in shell completion. `app` is the
# augmented Typer/Click group (so the existing `cli:app` console-script entry
# point keeps working).
app = cast("TyperGroup", typer.main.get_command(_typer_app))
app.add_command(
    _make_feature_command(
        "update-matrix",
        matrix_update.build_parser(),
        matrix_update,
        "Rewrite matrix.json in place with the latest/stable versions from official sources.",
    )
)
app.add_command(
    _make_feature_command(
        "cache-version",
        version_cache.build_parser(),
        version_cache,
        "Maintain a TTL version cache and generate a matrix template (fewer API calls).",
    )
)
app.add_command(_parse_command())

# Back-compat alias.
cli = app


if __name__ == "__main__":
    app()
