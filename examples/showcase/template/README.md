# Showcase: Template from Cache (no API calls)

A runnable example of **template-only mode**: generate a matrix from an **existing
version cache** without making any GitHub API requests. This is the fast,
rate-limit-free way to (re)build a matrix once a cache has been populated — ideal as
a pre-build step.

This runs in this repository via
[`Sample - Template from Cache`](../../../.github/workflows/sample_template.yml); the
green badge in the [README](../../../README.md#sample-workflows) is proof it works.

## How it works

The action is called with **`template-only: 'true'`**, pointed at the repository's
cache file ([`.github/json2vars-setter/cache/version_cache.json`](../../../.github/json2vars-setter/cache/version_cache.json)):

```yaml
- uses: 7rikazhexde/json2vars-setter@v1.9.1
  with:
    json-file: examples/showcase/template/matrix.json   # generated at runtime
    use-cache: 'true'
    template-only: 'true'
    cache-languages: 'python,nodejs'
    output-count: '3'                                    # newest 3 per language
    cache-file: .github/json2vars-setter/cache/version_cache.json
```

The committed [`matrix.json`](matrix.json) is only a **seed**: in template-only mode the
action **regenerates** it from the cache at runtime (the action requires the target file
to exist first), then parses it into outputs. `output-count: '3'` trims each language to
its newest 3 cached versions, so a large cache can back a small matrix.

## Try it locally (no API, no GitHub)

**Linux / macOS (bash):**

```bash
uv run json2vars cache-version --template-only \
  --languages python --languages nodejs --output-count 3 \
  --cache-file .github/json2vars-setter/cache/version_cache.json \
  --template-file out-matrix.json
cat out-matrix.json
```

**Windows (PowerShell):**

```powershell
uv run json2vars cache-version --template-only `
  --languages python --languages nodejs --output-count 3 `
  --cache-file .github/json2vars-setter/cache/version_cache.json `
  --template-file out-matrix.json
Get-Content out-matrix.json
```

## Adopt it

1. Populate a cache once (`json2vars cache-version`, or the action with
   `use-cache: 'true'` — see [Version Caching](../../../docs/features/version-caching.md)).
2. Use `template-only: 'true'` in fast/offline jobs to rebuild the matrix from that
   cache without spending API quota.
