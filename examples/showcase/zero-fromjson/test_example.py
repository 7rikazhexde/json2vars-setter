"""A minimal pytest test the reusable workflow discovers and runs across the matrix.

It stands in for a real project's test suite so the sample is self-contained: the caller
does not specify any command — the reusable workflow runs ``pytest`` by convention.
"""

import sys


def test_runs_on_expected_python() -> None:
    # The matrix selects the interpreter; confirm it is one the example lists (3.12+).
    assert sys.version_info[:2] >= (3, 12)
