"""
Command-execution tests for the ``json2vars`` console script.

Unlike ``tests/test_cli.py`` (in-process, ``CliRunner`` + mocked feature ``main``),
these run the **installed console script as a real subprocess** — the same path a
shell takes. They guard two things the unit tests cannot see:

1. End-to-end execution: ``json2vars parse`` actually writes ``GITHUB_OUTPUT``.
2. Shell-completion robustness: the ``complete_powershell`` protocol output stays
   parseable by the documented PowerShell completer even when an option's help is
   long enough that Typer wraps it across lines.

The regression this locks in: ``cache-version`` has long option help (``--output-count``,
``--cache-file``, …). Typer wraps it to ~80 cols when stdout is a pipe; the wrapped
fragment has no ``:::`` separator. A naive ``$_ -split ':::'`` PowerShell completer then
builds a ``CompletionResult`` with an empty tooltip, which throws and makes the *whole*
command return zero completions. The documented robust completer (and ``_robust_parse``
below, which mirrors it) keeps only ``:::`` lines and splits on the first separator.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

import pytest

from json2vars_setter.features import matrix_update, version_cache


def _console_script() -> Optional[Path]:
    """Locate the installed ``json2vars`` entry point for this interpreter."""
    scripts_dir = Path(sys.executable).parent
    for name in ("json2vars.exe", "json2vars"):
        candidate = scripts_dir / name
        if candidate.exists():
            return candidate
    found = shutil.which("json2vars")
    return Path(found) if found else None


_JSON2VARS = _console_script()
requires_script = pytest.mark.skipif(
    _JSON2VARS is None, reason="json2vars console script is not installed"
)


def _long_opts(parser: "object") -> set[str]:
    """Long (``--``) option strings declared by an argparse parser."""
    actions = parser._actions  # type: ignore[attr-defined]
    return {
        opt
        for action in actions
        for opt in action.option_strings
        if opt.startswith("--")
    }


def _robust_parse(raw: str) -> List[str]:
    """Parse ``value:::help`` completion output the way the docs' PowerShell
    completer does: keep only lines that contain ``:::`` (dropping wrapped help
    fragments) and split on the **first** separator."""
    values: List[str] = []
    for line in raw.splitlines():
        if ":::" not in line:
            continue
        value = line.split(":::", 1)[0]
        if value.strip():
            values.append(value)
    return values


def _complete(args: str, word: str = "", columns: str = "20") -> str:
    """Run the console script under the PowerShell completion protocol.

    ``columns`` is forced small so Typer/rich wraps long help across lines —
    reproducing the condition that broke the naive completer.
    """
    assert _JSON2VARS is not None
    env = {
        **os.environ,
        "_JSON2VARS_COMPLETE": "complete_powershell",
        "_TYPER_COMPLETE_ARGS": args,
        "_TYPER_COMPLETE_WORD_TO_COMPLETE": word,
        "COLUMNS": columns,
    }
    result = subprocess.run(
        [str(_JSON2VARS)],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return result.stdout


@requires_script
def test_parse_writes_github_output(tmp_path: Path) -> None:
    """`json2vars parse` expands a JSON file into the GITHUB_OUTPUT file."""
    matrix = tmp_path / "matrix.json"
    matrix.write_text(
        '{"os": ["ubuntu-latest"], "versions": {"python": ["3.12"]}, '
        '"ghpages_branch": "gh-pages"}',
        encoding="utf-8",
    )
    out = tmp_path / "out.txt"
    env = {**os.environ, "GITHUB_OUTPUT": str(out)}

    result = subprocess.run(
        [str(_JSON2VARS), "parse", str(matrix)],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr
    content = out.read_text(encoding="utf-8")
    assert 'OS=["ubuntu-latest"]' in content
    assert 'VERSIONS_PYTHON=["3.12"]' in content
    assert "GHPAGES_BRANCH=gh-pages" in content


@requires_script
def test_completion_lists_subcommands() -> None:
    """`json2vars <TAB>` completes the four subcommands."""
    values = _robust_parse(_complete("json2vars "))
    assert {"usage", "update-matrix", "cache-version", "parse"} <= set(values)


@requires_script
@pytest.mark.parametrize("command", ["cache-version", "update-matrix"])
def test_completion_options_survive_wrapped_help(command: str) -> None:
    """`json2vars <command> -<TAB>` recovers every long option even when help wraps.

    With COLUMNS forced small, ``cache-version``'s long-help options wrap — the
    exact case that made the naive completer return nothing. Robust parsing must
    still recover the full option set declared by the argparse parser.
    """
    parser = (
        version_cache.build_parser()
        if command == "cache-version"
        else matrix_update.build_parser()
    )
    expected = _long_opts(parser)

    recovered = set(_robust_parse(_complete(f"json2vars {command} -", word="-")))

    missing = expected - recovered
    assert not missing, f"{command}: completion dropped {sorted(missing)}"


@requires_script
def test_completion_values_languages_and_strategy() -> None:
    """Value completion works through the real process for choices."""
    langs = _robust_parse(_complete("json2vars cache-version --languages "))
    assert "python" in langs
    assert "all" in langs

    strategies = _robust_parse(_complete("json2vars update-matrix --python "))
    assert set(strategies) == {"stable", "latest", "both"}


def test_robust_parse_recovers_value_from_wrapped_help() -> None:
    """The robust parser tolerates wrapped help (the documented PowerShell logic).

    A naive ``split(':::')[0]`` would treat the wrapped continuation line as a
    bogus completion value; the robust parser drops lines without a separator.
    This is deterministic and needs no subprocess.
    """
    wrapped = (
        "--output-count:::Number of versions to include in output template "
        "(default: 0, uses count value\n"
        "if not specified)\n"
        "--cache-file:::Custom cache file path (default:\n"
        ".github\\json2vars-setter\\cache\\version_cache.json)\n"
        "--help:::Show this message and exit.\n"
    )

    values = _robust_parse(wrapped)

    assert values == ["--output-count", "--cache-file", "--help"]
    # The wrapped continuation lines must not leak in as bogus candidates.
    assert "if not specified)" not in values


if __name__ == "__main__":
    pytest.main([__file__])
