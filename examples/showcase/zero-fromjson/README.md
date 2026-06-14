# Showcase: Zero `fromJson` (reusable workflow)

A runnable example where the **consumer writes zero `fromJson`**. The caller delegates the
whole matrix and test run to a reusable workflow
([`sample_zero_fromjson_lib.yml`](../../../.github/workflows/sample_zero_fromjson_lib.yml)),
which absorbs the single required `fromJson` internally. The caller only names the JSON
file and the test command.

This runs in this repository via
[`Sample - Zero fromJson`](../../../.github/workflows/sample_zero_fromjson.yml); the green
badge in the [README](../../../README.md#sample-workflows) is proof you can reproduce it.

## The caller (no `fromJson`, no matrix block)

```yaml
jobs:
  test:
    uses: 7rikazhexde/json2vars-setter/.github/workflows/run-matrix.yml@vX.Y.Z
    with:
      json-file: examples/showcase/zero-fromjson/matrix.json
      test-command: 'python -c "print(1 + 1)"'
```

That is the entire consumer surface — the `fromJson` lives inside the reusable workflow,
out of sight.

## Trade-off vs. the matrix-aggregate showcase

| | Zero fromJson (this) | [Matrix aggregate](../matrix-aggregate/README.md) |
|---|---|---|
| `fromJson` in consumer | **0** | 1 (whole matrix) |
| Test steps | **delegated** (a `test-command` input) | full control (your own steps) |
| Best for | simple, uniform jobs | arbitrary, multi-step jobs |

GitHub Actions requires at least one `fromJson` to turn a string output into a matrix;
this pattern does not remove it, it **relocates** it into the reusable workflow so the
caller never sees it. The price is that the caller delegates its steps.

## What it demonstrates

- The caller invokes the reusable workflow with just `json-file` + `test-command`.
- The reusable workflow parses the JSON, builds the matrix from `matrix_python`, sets up
  Python per `${{ matrix.version }}`, and runs the command across the matrix.

## Adopt it

1. Copy `sample_zero_fromjson_lib.yml` into your org's central repo (or this repo) and
   adapt the "Set up Python" step for your language (read `matrix_<lang>`).
2. From any project, call it with `uses:` + `json-file:` + `test-command:` — no
   `fromJson` anywhere in the caller.
3. Point the `uses:` ref at the [latest release](https://github.com/7rikazhexde/json2vars-setter/releases).

> Try the parsing locally first:
> `GITHUB_OUTPUT=out.txt uv run json2vars parse examples/showcase/zero-fromjson/matrix.json && cat out.txt`
