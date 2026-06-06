# Showcase: Monorepo (per-project matrices)

A runnable example of the **monorepo pattern**: one repository holding several
projects, each with its **own** matrix JSON. json2vars-setter is invoked once per
project, so each gets an independent test matrix — edit one project's JSON and only
that project's matrix changes.

This runs in this repository via
[`Sample - Monorepo`](../../../.github/workflows/sample_monorepo.yml); the green
badge in the [README](../../../README.md#sample-workflows) is proof you can reproduce it.

## The files

| File | Project | Matrix |
|------|---------|--------|
| [`backend.json`](backend.json) | Python "backend" | `os × python` |
| [`frontend.json`](frontend.json) | Node.js "frontend" | `os × node` |

```jsonc
// backend.json
{ "os": ["ubuntu-latest"], "versions": { "python": ["3.12", "3.13"] }, "ghpages_branch": "gh-pages" }

// frontend.json
{ "os": ["ubuntu-latest"], "versions": { "nodejs": ["20", "22"] }, "ghpages_branch": "gh-pages" }
```

## What it demonstrates

- `backend_vars` parses `backend.json` → its `versions_python`; `backend_test` builds
  the Python matrix from it.
- `frontend_vars` parses `frontend.json` → its `versions_nodejs`; `frontend_test`
  builds the Node.js matrix from it.
- The two projects evolve **independently** — there is no shared, tangled matrix.

## Adopt it

1. Copy `examples/showcase/monorepo/` (rename to your project folders) and
   `sample_monorepo.yml` into your repository.
2. Point each `json-file:` at the matrix JSON living next to each project.
3. Make `uses: 7rikazhexde/json2vars-setter@vX.Y.Z` point at the
   [latest release](https://github.com/7rikazhexde/json2vars-setter/releases), then push.

> Try it locally first: `GITHUB_OUTPUT=out.txt uv run json2vars parse examples/showcase/monorepo/backend.json && cat out.txt`
