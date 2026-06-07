# Showcase: Version Cache (fewer API calls)

A runnable example of the **version-cache** feature: drive a multi-version test
matrix from a **committed version cache** so the build makes **zero GitHub API calls**
on the hot path. A busy repo can test against many language versions without spending
API quota on every run — the cache is refreshed only when it goes stale.

This runs in this repository via
[`Sample - Version Cache`](../../../.github/workflows/sample_version_cache.yml); the
green badge in the [README](../../../README.md#sample-workflows) is proof it works.

## How it works

The action is called with **`use-cache: 'true'`** (and **without** `template-only`),
pointed at the repository's cache file
([`.github/json2vars-setter/cache/version_cache.json`](../../../.github/json2vars-setter/cache/version_cache.json)):

```yaml
- uses: 7rikazhexde/json2vars-setter@v1.9.1
  with:
    json-file: examples/showcase/version-cache/matrix.json
    use-cache: 'true'
    cache-languages: 'python,nodejs'
    cache-max-age: '3650'  # treat the cache as fresh -> no API call (a cache HIT)
    output-count: '3'      # newest 3 cached versions per language
    cache-file: .github/json2vars-setter/cache/version_cache.json
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

The `test` job then fans out over **three** Python versions and a `node_check` job
uses the newest cached Node.js — all from that one cache, with no API requests.

### The `cache-max-age` knob (cache hit vs. refresh)

`cache-max-age` is the whole point: when the cache is **younger** than N days it is a
**hit** (no API call); when it is **older**, the action **refreshes** that language
from the live API and rewrites the cache. The committed cache fixture here is
intentionally old, so this sample uses a deliberately large `3650` to keep it a
guaranteed hit (deterministic and quota-free). In a real project use a small value
(e.g. `7`) so the cache self-refreshes weekly — that refresh path needs `GITHUB_TOKEN`.

### `use-cache` vs. `template-only`

- **`template-only: 'true'`** ([Template sample](../template/README.md)) — *always*
  regenerate from the cache, never call the API.
- **`use-cache: 'true'`** (this sample) — use the cache, but transparently refresh it
  from the API when `cache-max-age` says it is stale. The cache lifecycle in one input.

> `use-cache` and `update-matrix` are mutually exclusive — caching reuses fetched
> versions, dynamic update always fetches.

## Try it locally (no API on a fresh cache)

```bash
uv run json2vars cache-version \
  --languages python nodejs --output-count 3 \
  --max-age 365 \
  --cache-file .github/json2vars-setter/cache/version_cache.json \
  --template-file out-matrix.json
cat out-matrix.json
```

## Adopt it

1. Populate a cache once (`json2vars cache-version`, or the action with
   `use-cache: 'true'` — see [Version Caching](../../../docs/features/version-caching.md)).
2. Commit `version_cache.json`, then use `use-cache: 'true'` with a sensible
   `cache-max-age` so most runs are cache hits and only the occasional run refreshes.
