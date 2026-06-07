# Showcase: Dynamic Update (scheduled maintenance)

A runnable example of the **dynamic-update** feature used as **scheduled
maintenance**: on a weekly schedule, fetch the latest language versions from the
live GitHub release APIs and rebuild the matrix — so your test matrix tracks
upstream releases without anyone hand-editing JSON.

This runs in this repository via
[`Sample - Dynamic Update`](../../../.github/workflows/sample_dynamic_update.yml); the
green badge in the [README](../../../README.md#sample-workflows) is proof it works
against the live API every week (and catches upstream drift, like the per-language
tests do).

## How it works

The committed [`matrix.json`](matrix.json) is a deliberately **stale seed**
(`python 3.11` / `node 20`). The action is called with **`update-matrix: 'true'`**
and a per-language strategy, which overwrites the matrix **in the runner workspace**
with the latest releases, then parses it into outputs:

```yaml
- uses: 7rikazhexde/json2vars-setter@v1.9.1
  with:
    json-file: examples/showcase/dynamic-update/matrix.json
    update-matrix: 'true'
    python-strategy: 'stable'   # newest stable Python
    nodejs-strategy: 'stable'   # newest stable Node.js
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}   # required: queries the live API
```

`*-strategy` accepts `stable`, `latest`, or `both`. Use `update-strategy: 'stable'`
to apply one strategy to every language at once.

## Side-effect-free by design

This sample **does not commit anything** — it updates the workspace copy and parses
it, which is enough to prove the fetch + rebuild pipeline works. A real maintenance
workflow runs your tests against the updated matrix and **then** commits it (or opens
a pull request) only if they pass. See the **Scheduled Maintenance Workflow** and the
branch-protection (open-a-PR) variant in
[`docs/examples/ci-cd.md`](../../../docs/examples/ci-cd.md).

To turn this into a pure *preview* that fetches and logs the candidate versions
without touching even the workspace file, add `dry-run: 'true'`.

## Try it locally

**Linux / macOS (bash):**

```bash
# Preview what the update would do, without modifying the file:
uv run json2vars update-matrix \
  --json-file examples/showcase/dynamic-update/matrix.json \
  --python stable --nodejs stable --dry-run
```

**Windows (PowerShell):**

```powershell
# Preview what the update would do, without modifying the file:
uv run json2vars update-matrix `
  --json-file examples/showcase/dynamic-update/matrix.json `
  --python stable --nodejs stable --dry-run
```

## Adopt it

1. Commit a seed `matrix.json` with the languages you care about.
2. Add a scheduled workflow calling the action with `update-matrix: 'true'` and the
   strategies you want, passing `GITHUB_TOKEN`.
3. Run your tests against the outputs, then commit/PR the matrix only on success.
