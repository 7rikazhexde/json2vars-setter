# Showcase: Zero `fromJson`, zero command (reusable workflow)

A runnable example where the **consumer writes zero `fromJson` and no command**. The caller
delegates the whole matrix and test run to a reusable workflow
([`sample_zero_fromjson_lib.yml`](../../../.github/workflows/sample_zero_fromjson_lib.yml)),
which absorbs the single required `fromJson` internally **and runs the project's tests by
convention** (`pytest`). The caller only points at the JSON file and the project directory.

This runs in this repository via
[`Sample - Zero fromJson`](../../../.github/workflows/sample_zero_fromjson.yml); the green
badge in the [README](../../../README.md#sample-workflows) is proof you can reproduce it.

## The caller (no `fromJson`, no matrix block, no command)

```yaml
jobs:
  test:
    uses: 7rikazhexde/json2vars-setter/.github/workflows/run-matrix.yml@vX.Y.Z
    with:
      json-file: examples/showcase/zero-fromjson/matrix.json
      working-directory: examples/showcase/zero-fromjson
```

That is the entire consumer surface — no `fromJson`, no matrix, no shell command. The
library parses the JSON, builds the matrix, and runs the tests in `working-directory` by
convention. It runs them with **uv** — `uv run --no-project --python <matrix> --with
pytest pytest` — so there is **no install step** either (uv provisions the matrix's Python
and pytest in one ephemeral, PEP 723-compatible run).

## Trade-off vs. the matrix-aggregate showcase

| | Zero fromJson (this) | [Matrix aggregate](../matrix-aggregate/README.md) |
|---|---|---|
| `fromJson` in consumer | **0** | 1 (whole matrix) |
| Command in consumer | **none** (convention: `pytest`) | n/a (your own steps) |
| Test steps | **delegated** (convention-based) | full control (your own steps) |
| Best for | projects that follow the convention | arbitrary, multi-step jobs |

GitHub Actions requires at least one `fromJson` to turn a string output into a matrix;
this pattern does not remove it, it **relocates** it into the reusable workflow so the
caller never sees it. The price is that the test run is delegated to a convention.

## What it demonstrates

- The caller invokes the reusable workflow with just `json-file` + `working-directory`.
- The reusable workflow parses the JSON, builds the matrix from `matrix_python`, and runs
  `pytest` (the convention) across the matrix with uv — no setup-python and no install step.

## Adopt it

1. Copy `sample_zero_fromjson_lib.yml` into your org's central repo (or this repo) and
   adapt the setup + convention step for your language (read `matrix_<lang>`).
2. From any project, call it with `uses:` + `json-file:` + `working-directory:` — no
   `fromJson` and no command anywhere in the caller.
3. Point the `uses:` ref at the [latest release](https://github.com/7rikazhexde/json2vars-setter/releases).

> Try the parsing locally first:
> `GITHUB_OUTPUT=out.txt uv run json2vars parse examples/showcase/zero-fromjson/matrix.json && cat out.txt`
