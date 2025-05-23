# Version Caching

The Version Cache Manager (`cache_version_info.py`) manages version information cache to optimize API usage and workflow performance.

## Overview

This component reduces external API calls by caching version information, making your workflows faster and more resilient. It's especially useful for frequently run workflows or environments with API rate limits.

## Component Overview

```mermaid
graph TD
    Start[json2vars-setter Action] -->|Input Parameters| GHACondition{use-cache?}
    GHACondition --> |true| MainPurpose1[cache_version_info.py]

    MainPurpose1[cache_version_info.py] --> MainPurpose2{Main Functions}

    MainPurpose2 -->|Create Template JSON| TemplateCreation[Template Creation]
    MainPurpose2 -->|Cache Version Info| CacheCreation[Cache Creation]

    TemplateCreation --> TemplateSource{Information Source}
    TemplateSource -->|From Existing Cache| UseCache[--template-only]
    TemplateSource -->|From API| UseAPI[Default or --force]

    CacheCreation --> UpdateFrequency{Update Frequency}
    UpdateFrequency -->|Force Update| ForceUpdate[--force]
    UpdateFrequency -->|Conditional Update| ConditionalUpdate[--max-age N]
    UpdateFrequency -->|Build History| History[--incremental]

    %% Common options
    UseCache --> CommonOptions{Additional Options}
    UseAPI --> CommonOptions
    ForceUpdate --> CommonOptions
    ConditionalUpdate --> CommonOptions
    History --> CommonOptions

    CommonOptions --> Languages[--languages #91;*1#93;]
    CommonOptions --> KeepExisting[--keep-existing]
    CommonOptions --> FilePaths[--cache-file #91;*2#93;,<br/> --template-file #91;*2#93;,<br/> --existing-template #91;*2#93;]
    CommonOptions --> CacheCount[--count N]
    CommonOptions --> VersionCount[--output-count N]
    CommonOptions --> SortOrder[--sort asc/desc]
    CommonOptions --> CacheOnly[--cache-only]
    CommonOptions --> VerboseLog[--verbose]

    %% Style definitions for better visibility in dark mode
    classDef ghacondition fill:#42a5f5,stroke:#1976d2,stroke-width:1px,color:#fff
    classDef start fill:#9c27b0,stroke:#6a1b9a,stroke-width:2px,color:#ffffff
    classDef main fill:#43a047,stroke:#2e7d32,stroke-width:2px,color:#ffffff
    classDef condition fill:#ff9800,stroke:#e65100,stroke-width:2px,color:#000000
    classDef option fill:#42a5f5,stroke:#1976d2,stroke-width:1px,color:#ffffff
    classDef common fill:#42a5f5,stroke:#1976d2,stroke-width:1px,color:#ffffff

    class Start start
    class GHACondition ghacondition
    class MainPurpose1,MainPurpose2,TemplateCreation,CacheCreation main
    class TemplateSource,UpdateFrequency,CommonOptions condition
    class UseCache,UseAPI,ForceUpdate,ConditionalUpdate,History option
    class Languages,FilePaths,CacheCount,VersionCount,SortOrder,KeepExisting,CacheOnly,VerboseLog common
```

### Tips

!!! tip "[*1]: Specify language"

    - Specify languages separated by **spaces**; if `all` is specified, all target languages are retrieved.
    - Target languages: `python`, `nodejs`, `ruby`, `go`, `rust`

!!! tip "[*2]: specify a path"

    - If the file does not exist in the path, an error will occur, so please create it beforehand.

!!! tip "count vs output-count"

    - `--count` controls how many versions to retrieve and store in the cache
    - `--output-count` controls how many of these versions appear in the output template (matrix.json)
    - When `--output-count` is 0 or not specified, it automatically uses the value of `--count`
    - This allows you to cache many versions (e.g., `--count 10`) but limit how many appear in your matrix file (e.g., `--output-count 3`)
    - Example use case: Cache 10 recent versions for history but only use the 3 most recent in your CI/CD matrix

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--template-only` | Generate template from existing cache (`version_cache.json`) without API requests | None |
| `--force` | Force update regardless of existing cache | None |
| `--max-age N` | Update cache only after N days<br>Compares with `last_updated` value in existing cache | 1 day |
| `--incremental` | Add new versions to existing cache (build history) | None |
| `--languages` | Specify target languages<br>Separate multiple languages with spaces<br>Supported: python, nodejs, ruby, go, rust | all |
| `--count N` | Number of versions to fetch and cache per language | 10 |
| `--output-count N` | Number of versions to include in output template<br>When 0 or not specified, uses the value of `--count` | 0 |
| `--keep-existing` | Maintain information for non-specified languages | None |
| `--cache-file` | Path to cache file | Default path |
| `--template-file` | Path to output template file | Default path |
| `--existing-template` | Path to existing template to maintain structure | None |
| `--sort` | Version sort order (desc: newest first, asc: oldest first) | desc |
| `--cache-only` | Update cache only, don't generate template | None |
| `--verbose` | Output detailed logs | None |

## Common Usage Examples

### Template Creation

#### Generate template from existing cache without API calls

```bash
python json2vars_setter/cache_version_info.py --template-only
```

#### Update specific languages only (maintain other language information)

```bash
python json2vars_setter/cache_version_info.py --template-only --languages python --keep-existing
```

#### Fetch latest information from API and create template

```bash
python json2vars_setter/cache_version_info.py
```

#### Cache many versions but limit output to most recent ones

```bash
python json2vars_setter/cache_version_info.py --count 10 --output-count 3
```

### Cache Creation and Management

#### Force fetch latest information

```bash
python json2vars_setter/cache_version_info.py --force
```

#### Update only after a certain period (e.g., 7 days)

```bash
python json2vars_setter/cache_version_info.py --max-age 7
```

#### Accumulate version history (add new versions)

```bash
python json2vars_setter/cache_version_info.py --incremental --count 30
```

## Advanced Usage

### Custom File Specification

#### Output to specific file

##### Write support language version (python,nodejs,ruby,go,rust)

```bash
python json2vars_setter/cache_version_info.py --template-file ./your_project_matrix.json
```

##### Write specified support language version (python,nodejs)

```bash
python json2vars_setter/cache_version_info.py --lang python nodejs --template-file ./your_project_matrix.json
```

##### Write specified support language version (python)

```bash
python json2vars_setter/cache_version_info.py --lang python --template-file ./your_python_matrix.json
```

#### Maintain existing file structure

```bash
python json2vars_setter/cache_version_info.py --existing-template ./project_matrix.json --template-file ./updated_matrix.json
```

### Version Control Flexibility

#### Cache complete history but test only latest versions

```bash
python json2vars_setter/cache_version_info.py --count 15 --output-count 3
```

### CI/CD Integration

#### Scheduled job (cache update only)

```bash
python json2vars_setter/cache_version_info.py --max-age 7 --cache-only
```

#### Pre-build processing (template generation only)

```bash
python json2vars_setter/cache_version_info.py --template-only
```

## GitHub Actions Integration

In GitHub Actions, these options are mapped to action inputs:

```yaml
- name: Set variables with cached versions
  id: json2vars
  uses: 7rikazhexde/json2vars-setter@v1.0.1
  with:
    json-file: .github/json2vars-setter/sample/matrix.json
    use-cache: 'true'
    cache-languages: 'python,nodejs'
    cache-max-age: '7'
    cache-count: '10'
    output-count: '3'  # Cache 10 versions but only use 3 in matrix
    keep-existing: 'true'
    sort-order: 'desc'
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

Note that the version caching strategy (`use-cache: 'true'`) and dynamic update strategy (`update-matrix: 'true'`) cannot be used together as they represent different approaches to managing version information.

## How It Works

When you set `use-cache: 'true'`, the action performs these steps internally:

1. **Check Cache Freshness**: The manager checks if the cache is fresh based on `cache-max-age`
2. **Fetch Version Info**: If needed, it fetches new version information from APIs for the specified languages
3. **Update Cache**: It updates the cache file with the new information
4. **Generate Template**: It creates or updates the matrix JSON file based on the cached data, respecting version limits
    - If `output-count` is specified, only that many versions are included in the template
    - Otherwise, `cache-count` versions are included
5. **Parse JSON**: The matrix JSON file is processed by json_to_github_output.py
6. **Set Outputs**: The values from the JSON file are set as GitHub Actions outputs

```mermaid
sequenceDiagram
    participant Workflow as GitHub Workflow
    participant Action as json2vars-setter
    participant CacheMgr as cache_version_info.py
    participant Parser as json_to_github_output.py
    participant API as Language APIs
    participant Cache as version_cache.json
    participant File as matrix.json

    Workflow->>Action: Run with use-cache: 'true'
    Action->>CacheMgr: Execute with options

    alt Cache needs updating
        CacheMgr->>Cache: Check freshness
        CacheMgr->>API: Fetch version info
        API->>CacheMgr: Return versions
        CacheMgr->>Cache: Update cache
    else Cache is fresh or template-only
        CacheMgr->>Cache: Read cached data
    end

    CacheMgr->>File: Generate/update matrix file
    CacheMgr->>Action: Return control
    Action->>Parser: Execute with matrix JSON
    Parser->>File: Read JSON
    Parser->>Workflow: Set GitHub outputs
```

## Best Practices

- **Use `use-cache: 'true'` with `cache-max-age`** to avoid unnecessary API calls while keeping versions updated
- **Use template-only mode** (`template-only: 'true'`) for quick template generation from existing cache
- **Use incremental mode** (`cache-incremental: 'true'`) with `cache-count` to build comprehensive version history
- **Use `keep-existing: 'true'`** when updating only specific languages to maintain existing configuration
- **Use `output-count`** to limit the number of versions in your matrix while maintaining a larger history in cache
- **Set up a scheduled job** for cache maintenance and a separate job for template generation
- **Never use `use-cache: 'true'` and `update-matrix: 'true'` together** as they are mutually exclusive approaches

## GitHub API Authentication

When fetching version information from GitHub APIs, you might encounter rate limits, especially in CI/CD environments where many workflows run frequently.

!!! tip "Avoiding API Rate Limits"
    To increase your API rate limits, add the `GITHUB_TOKEN` as an environment variable:

    ```yaml
    - name: Set variables with cached versions
      id: json2vars
      uses: 7rikazhexde/json2vars-setter@v1.0.1
      with:
        json-file: .github/json2vars-setter/sample/matrix.json
        use-cache: 'true'
        cache-languages: 'python,nodejs'
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    ```

    This allows the action to authenticate with GitHub, significantly increasing your API rate limits.

!!! warning "API Rate Limit Issues"
    If you encounter `API rate limit exceeded` errors, refer to the [Troubleshooting Guide](../examples/troubleshooting.md#api-rate-limit-exceeded) for more detailed solutions.

## Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| API rate limits | Use GitHub authentication by setting up the `GITHUB_TOKEN` environment variable |
| Missing versions | Increase the `cache-count` value to fetch more versions |
| Too many versions in matrix | Use `output-count` to limit matrix versions while keeping more in cache |
| Incorrect sort order | Explicitly set `sort-order: 'asc'` or `sort-order: 'desc'` as needed |
| Cache not updating | Use `force-cache-update: 'true'` to force an update |
| Empty template | Check that the cache file exists or use `force-cache-update: 'true'` to create it |

## Next Steps

- Learn how to [dynamically update](dynamic-update.md) your matrix configurations
- See [basic examples](../examples/basic.md) for simple cache usage patterns
- Review the [command options](../reference/options.md) reference for all available options
