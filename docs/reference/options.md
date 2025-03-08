# Command Options Reference

This page provides a comprehensive reference for all configuration options available in the JSON to Variables Setter action.

## Input Parameters

### Basic Settings

| Parameter | Description | Required | Default | Notes |
|-----------|-------------|:--------:|:-------:|-------|
| `json-file` | Path to the JSON file | ✓ | - | The JSON file containing matrix configuration |

### Dynamic Update Options

| Parameter | Description | Required | Default | Notes |
|-----------|-------------|:--------:|:-------:|-------|
| `update-matrix` | Whether to dynamically update the matrix before parsing | ✗ | `false` | Enables the dynamic update feature |
| `update-strategy` | Default update strategy for all languages | ✗ | - | Valid values: `stable`, `latest`, `both` |
| `python-strategy` | Update strategy for Python versions | ✗ | - | Same valid values as `update-strategy` |
| `nodejs-strategy` | Update strategy for Node.js versions | ✗ | - | Same valid values as `update-strategy` |
| `ruby-strategy` | Update strategy for Ruby versions | ✗ | - | Same valid values as `update-strategy` |
| `go-strategy` | Update strategy for Go versions | ✗ | - | Same valid values as `update-strategy` |
| `rust-strategy` | Update strategy for Rust versions | ✗ | - | Same valid values as `update-strategy` |
| `dry-run` | Run in dry-run mode without updating the JSON file | ✗ | `false` | For testing update strategies |

### Cache Version Options

| Parameter | Description | Required | Default | Notes |
|-----------|-------------|:--------:|:-------:|-------|
| `use-cache` | Whether to use cached version information | ✗ | `false` | Enables the version caching feature |
| `cache-languages` | Languages to include in cache operations | ✗ | `all` | Comma-separated list (e.g., `python,nodejs`) |
| `force-cache-update` | Force cache update even if it is fresh | ✗ | `false` | Bypasses freshness checks |
| `cache-max-age` | Maximum age of cache in days before update | ✗ | `1` | How old the cache can be before refresh |
| `cache-count` | Number of versions to fetch per language | ✗ | `10` | Controls how many versions to retrieve |
| `cache-incremental` | Add only new versions without replacing existing cache | ✗ | `false` | Build a version history over time |
| `cache-file` | Custom cache file path | ✗ | `.github/workflows/cache/version_cache.json` | Where to store cache data |
| `template-only` | Only generate template from existing cache (no API calls) | ✗ | `false` | Skip updating cache, just use existing data |
| `cache-only` | Only update the cache, do not generate the template | ✗ | `false` | Update cache but don't modify JSON file |
| `keep-existing` | Maintain existing version information when generating template | ✗ | `true` | Preserves information for unspecified languages |
| `sort-order` | Version sort order | ✗ | `desc` | Valid values: `desc` (newest first), `asc` (oldest first) |

## Output Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `os` | List of operating systems | `["ubuntu-latest", "windows-latest", "macos-latest"]` |
| `versions_python` | List of Python versions | `["3.10", "3.11", "3.12"]` |
| `versions_ruby` | List of Ruby versions | `["3.0", "3.1", "3.2"]` |
| `versions_nodejs` | List of Node.js versions | `["16", "18", "20"]` |
| `versions_go` | List of Go versions | `["1.19", "1.20", "1.21"]` |
| `versions_rust` | List of Rust versions | `["1.70.0", "1.71.0", "stable"]` |
| `ghpages_branch` | GitHub Pages branch name | `"gh-pages"` |

## Usage Notes

### Strategy Types

The dynamic update feature supports three different strategies:

- **`stable`**: Include only stable versions (recommended for production)
- **`latest`**: Include only the latest versions, including pre-releases (for testing cutting-edge features)
- **`both`**: Include both stable and latest versions (for maximum compatibility testing)

### Input Relationships and Constraints

Some input parameters have relationships or constraints:

1. **Mutually Exclusive Strategies**:
   - `update-matrix: 'true'` and `use-cache: 'true'` cannot be used together
   - If both are specified, `update-matrix` takes precedence

2. **Strategy Hierarchy**:
   - If `update-strategy` is specified, it applies to all languages
   - Language-specific strategies (e.g., `python-strategy`) override the global strategy

3. **Cache-Related Dependencies**:
   - `template-only` requires an existing cache file
   - `force-cache-update` is only relevant when `use-cache: 'true'`
   - `cache-incremental` works best with a higher `cache-count` value

### Example Usage

#### Dynamic Update Strategy

```yaml
- name: Set variables with dynamic update
  id: json2vars
  uses: 7rikazhexde/json2vars-setter@main
  with:
    json-file: .github/workflows/matrix.json
    update-matrix: 'true'
    python-strategy: 'stable'
    nodejs-strategy: 'latest'
```

#### Caching Strategy

```yaml
- name: Set variables with caching
  id: json2vars
  uses: 7rikazhexde/json2vars-setter@main
  with:
    json-file: .github/workflows/matrix.json
    use-cache: 'true'
    cache-max-age: '7'
    cache-languages: 'python,nodejs'
    keep-existing: 'true'
```

#### Basic Usage (No Updates)

```yaml
- name: Set variables from static JSON
  id: json2vars
  uses: 7rikazhexde/json2vars-setter@main
  with:
    json-file: .github/workflows/matrix.json
```

## Best Practices

- **Always set an `id`** for the step to reference the outputs
- **Use caching with `cache-max-age`** to reduce API calls in frequently run workflows
- **Use `dry-run: 'true'`** to test update strategies before applying them
- **Set up `GITHUB_TOKEN`** environment variable to avoid API rate limits
- **For scheduled updates**, use a dedicated job that commits changes to the repository

## Error Handling

Common error scenarios and how to handle them:

- **API Rate Limits**: Add `env: GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}` to your step
- **Missing Outputs**: Check if you've specified the correct `id` and using the outputs correctly
- **Cache File Errors**: Ensure the cache directory exists; use `force-cache-update: 'true'` to reset

For more troubleshooting help, see the [Troubleshooting Guide](../examples/troubleshooting.md).

## Next Steps

- Learn about [basic usage](../examples/basic.md)
- See [CI/CD integration examples](../examples/ci-cd.md)
- Check [troubleshooting tips](../examples/troubleshooting.md)
