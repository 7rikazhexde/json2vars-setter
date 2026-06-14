# Showcase: Matrix aggregate output (one `fromJson`, no indexing)

A runnable example of the **`matrix_<lang>` aggregate output**: the action emits a
ready-to-use matrix object per language, so the consumer assigns a whole matrix with a
**single** `fromJson` and reads `${{ matrix.version }}` / `${{ matrix.os }}` directly —
**no per-axis `fromJson`, no `[0]` index access.**

This runs in this repository via
[`Sample - Matrix Aggregate`](../../../.github/workflows/sample_matrix_aggregate.yml);
the green badge in the [README](../../../README.md#sample-workflows) is proof you can
reproduce it.

## The output

For the matrix below, the action exposes (in addition to the usual `os` /
`versions_python` / `versions_nodejs` outputs):

```jsonc
// steps.json2vars.outputs.matrix_python
{ "os": ["ubuntu-latest", "macos-latest"], "version": ["3.12", "3.13"] }
// steps.json2vars.outputs.matrix_nodejs
{ "os": ["ubuntu-latest", "macos-latest"], "version": ["20", "22"] }
```

## Before / after

```yaml
# BEFORE — fromJson per axis, plus index access for single elements
strategy:
  matrix:
    os: ${{ fromJson(needs.vars.outputs.os) }}
    python-version: ${{ fromJson(needs.vars.outputs.versions_python) }}
steps:
  - uses: actions/setup-python@v6
    with:
      python-version: ${{ matrix.python-version }}

# AFTER — one fromJson for the whole matrix, intuitive matrix.* access
strategy:
  matrix: ${{ fromJson(needs.vars.outputs.matrix_python) }}
steps:
  - uses: actions/setup-python@v6
    with:
      python-version: ${{ matrix.version }}   # ${{ matrix.os }} also available
```

> GitHub Actions cannot reduce this below **one** `fromJson`: `strategy.matrix` needs an
> array/object but job outputs are always strings, so a single conversion is required.
> For a consumer that writes **zero** `fromJson`, see the reusable-workflow showcase
> ([`examples/showcase/zero-fromjson/`](../zero-fromjson/README.md)).

## What it demonstrates

- `vars` parses `matrix.json` → exposes `matrix_python` and `matrix_nodejs`.
- `python_test` / `nodejs_test` each assign a whole matrix with one `fromJson` and use
  `${{ matrix.version }}` — the language axes stay independent (no cross product).

## Adopt it

1. Copy `examples/showcase/matrix-aggregate/` and `sample_matrix_aggregate.yml` into
   your repository.
2. Point `json-file:` at your matrix JSON and forward `matrix_<lang>` as a job output.
3. Make `uses: 7rikazhexde/json2vars-setter@vX.Y.Z` point at the
   [latest release](https://github.com/7rikazhexde/json2vars-setter/releases), then push.

> Try it locally first:
> `GITHUB_OUTPUT=out.txt uv run json2vars parse examples/showcase/matrix-aggregate/matrix.json && cat out.txt`
