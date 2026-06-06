# Showcase: Single Source of Truth

This is a **runnable, copy-it-and-get-the-same-result** example of the core value
of json2vars-setter: define your build matrix **once** in a JSON file, then consume
it from **multiple independent jobs** — no version lists duplicated across jobs or
workflows.

Unlike a documentation snippet, this example **actually runs in this repository**.
The [`Sample - Single Source of Truth`](../../.github/workflows/sample_single_source.yml)
workflow executes on every change here, so its green check is proof you can
reproduce — not a promise you have to take on faith.

## The two files

| File | Role |
|------|------|
| [`matrix.json`](matrix.json) | The single source of truth: OS list + Python versions + Pages branch. |
| [`../../.github/workflows/sample_single_source.yml`](../../.github/workflows/sample_single_source.yml) | Reads the JSON once (`set_variables`), then two independent jobs (`test`, `lint`) consume it. |

`matrix.json`:

```json
{
    "os": ["ubuntu-latest", "macos-latest"],
    "versions": { "python": ["3.12", "3.13"] },
    "ghpages_branch": "gh-pages"
}
```

## What it demonstrates

- **`set_variables`** parses `matrix.json` and exposes `os`, `versions_python`, and
  `ghpages_branch` as job outputs.
- **`test`** builds a full `os × python-version` matrix straight from those outputs —
  the version list is never repeated.
- **`lint`** is a *separate* job that reuses the *same* outputs (it pins the lowest
  supported Python via `versions_python[0]`), showing that one JSON drives many jobs.

Change `matrix.json` and **every** job updates together. That is the single source
of truth.

## Try it locally first (no GitHub needed)

```bash
GITHUB_OUTPUT=out.txt uv run json2vars parse examples/showcase/matrix.json
cat out.txt
```

You will see exactly the outputs the workflow consumes. See
[Getting Started → Try It Locally](../../docs/getting-started.md#try-it-locally-no-github-needed)
for the full walkthrough.

## Adopt it in your project

1. Copy `matrix.json` and `sample_single_source.yml` into your repository
   (rename / relocate as you like; keep the `json-file:` path pointing at your JSON).
2. Edit `matrix.json` for the OS and versions you support.
3. Make `uses: 7rikazhexde/json2vars-setter@vX.Y.Z` point at the
   [latest release](https://github.com/7rikazhexde/json2vars-setter/releases).
4. Push. The same green result you see on this repo is what you get.

> Tip: `versions` also accepts `nodejs`, `ruby`, `go`, `rust`, and many more — see
> [Reference → Options](../../docs/reference/options.md). To keep the versions fresh
> automatically, layer on [Dynamic Update](../../docs/features/dynamic-update.md).
