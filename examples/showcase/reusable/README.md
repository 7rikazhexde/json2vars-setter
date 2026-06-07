# Showcase: Reusable Workflow (`workflow_call`)

A runnable example of **defining the matrix once and reusing it**: a reusable
workflow ([`sample_reusable_lib.yml`](../../../.github/workflows/sample_reusable_lib.yml))
parses a JSON file and exposes the OS / version lists as `workflow_call` **outputs**;
a caller ([`sample_reusable_workflow.yml`](../../../.github/workflows/sample_reusable_workflow.yml))
invokes it and runs its test matrix from those outputs.

In a real organization the library lives in a central repository and every project
calls it, so the supported version set is maintained in **one** place.

This runs in this repository via
[`Sample - Reusable Workflow`](../../../.github/workflows/sample_reusable_workflow.yml);
the green badge in the [README](../../../README.md#sample-workflows) is proof it works.

## How it works

**The library** (`workflow_call`) parses the JSON and re-exports the outputs:

```yaml
on:
  workflow_call:
    inputs:
      json-file: { required: true, type: string }
    outputs:
      os:              { value: ${{ jobs.vars.outputs.os }} }
      versions_python: { value: ${{ jobs.vars.outputs.versions_python }} }
      versions_nodejs: { value: ${{ jobs.vars.outputs.versions_nodejs }} }

jobs:
  vars:
    runs-on: ubuntu-latest
    outputs:
      os: ${{ steps.json2vars.outputs.os }}
      # ...
    steps:
      - uses: actions/checkout@v6.0.3
      - id: json2vars
        uses: 7rikazhexde/json2vars-setter@v1.9.1
        with:
          json-file: ${{ inputs.json-file }}
```

**The caller** invokes it with `uses:` and consumes the outputs:

```yaml
jobs:
  vars:
    uses: ./.github/workflows/sample_reusable_lib.yml
    with:
      json-file: examples/showcase/reusable/matrix.json

  test:
    needs: vars
    strategy:
      matrix:
        os: ${{ fromJson(needs.vars.outputs.os) }}
        python-version: ${{ fromJson(needs.vars.outputs.versions_python) }}
    # ...
```

In another repository, reference the library by its full path and a ref instead of
the local `./` path, e.g.
`uses: your-org/ci-workflows/.github/workflows/matrix.yml@v1`.

## Adopt it

1. Put the reusable workflow (the `workflow_call` library) in a central repo.
2. Commit the matrix [`matrix.json`](matrix.json) wherever the parse should run.
3. From each project, `uses:` the library and feed its outputs into your matrices —
   update versions in one place, everyone gets them.
