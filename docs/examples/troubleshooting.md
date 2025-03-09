# Troubleshooting Guide

This guide helps you diagnose and resolve common issues when using the JSON to Variables Setter action. It also provides debugging techniques and best practices for handling edge cases.

## Common Issues and Solutions

### API Rate Limit Exceeded

**Symptom**: Actions fail with `API rate limit exceeded` error in logs.

**Solution**: Add GitHub authentication token to increase rate limits.

```yaml
- name: Set variables with authentication
  id: json2vars
  uses: 7rikazhexde/json2vars-setter@main
  with:
    json-file: .github/json2vars-setter/matrix.json
    update-matrix: 'true'
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Missing or Empty Outputs

**Symptom**: Expected outputs are not available or are empty.

**Possible Causes and Solutions**:

1. **Missing `id` attribute**:

   ```yaml
   # Incorrect - missing id
   - name: Set variables from JSON
     uses: 7rikazhexde/json2vars-setter@main

   # Correct
   - name: Set variables from JSON
     id: json2vars  # This is required to reference outputs
     uses: 7rikazhexde/json2vars-setter@main
   ```

2. **JSON structure issue**:

   - Ensure your JSON file has the expected structure:

   ```json
   {
     "os": ["ubuntu-latest"],
     "versions": {
       "python": ["3.10", "3.11"]
     }
   }
   ```

   - Language versions must be under `versions.<language>` key

3. **Output references**:

   ```yaml
   # Incorrect output reference
   echo "Python versions: ${{ steps.json2vars.versions_python }}"

   # Correct output reference
   echo "Python versions: ${{ steps.json2vars.outputs.versions_python }}"
   ```

### Matrix Strategy Failures

**Symptom**: Matrix strategy fails with error like `The value of 'matrix.python-version' is invalid`.

**Solutions**:

1. **Check JSON parsing**:

   ```yaml
   # Incorrect - missing fromJson
   matrix:
     python-version: ${{ needs.set_variables.outputs.versions_python }}

   # Correct
   matrix:
     python-version: ${{ fromJson(needs.set_variables.outputs.versions_python) }}
   ```

2. **Verify output content**:

   ```yaml
   - name: Debug outputs
     run: |
       echo "Raw output: ${{ steps.json2vars.outputs.versions_python }}"
       echo "Type: ${{ typeof(steps.json2vars.outputs.versions_python) }}"
   ```

### Cache-Related Issues

**Symptom**: Cache is not updating or is generating incorrect templates.

**Solutions**:

1. **Force cache update**:

   ```yaml
   - name: Force cache update
     uses: 7rikazhexde/json2vars-setter@main
     with:
       json-file: .github/json2vars-setter/matrix.json
       use-cache: 'true'
       force-cache-update: 'true'
   ```

2. **Check cache file location**:
   The default cache location is `.github/json2vars-setter/cache/version_cache.json`. Ensure this directory exists and is writable.

3. **Commit cache files**:

   ```yaml
   - name: Commit updated cache
     run: |
       git config --local user.email "actions@github.com"
       git config --local user.name "GitHub Actions"
       git add .github/json2vars-setter/cache/version_cache.json
       git commit -m "Update version cache"
       git push
   ```

### Conflicting Strategies

**Symptom**: Unexpected behavior when using multiple strategies.

**Solution**: Never use `update-matrix: 'true'` and `use-cache: 'true'` together. They are mutually exclusive strategies.

```yaml
# Incorrect - conflicting strategies
- name: Set variables
  uses: 7rikazhexde/json2vars-setter@main
  with:
    json-file: .github/json2vars-setter/matrix.json
    update-matrix: 'true'
    use-cache: 'true'  # Will be ignored when update-matrix is true

# Correct - choose one strategy
- name: Set variables with dynamic update
  uses: 7rikazhexde/json2vars-setter@main
  with:
    json-file: .github/json2vars-setter/matrix.json
    update-matrix: 'true'
```

## Debugging Techniques

### Enable Verbose Logging

Add the `--verbose` flag to see detailed logs:

```yaml
- name: Debug cache version info
  run: |
    python ${{ github.action_path }}/json2vars_setter/cache_version_info.py --verbose
```

Or use the built-in debug output:

```yaml
- name: Set variables with debug
  id: json2vars
  uses: 7rikazhexde/json2vars-setter@main
  with:
    json-file: .github/json2vars-setter/matrix.json
    update-matrix: 'true'
    verbose: 'true'  # Enable verbose logging
```

### Test Configurations Locally

You can test the scripts locally before using them in GitHub Actions:

```bash
# Test cache_version_info.py
python path/to/cache_version_info.py --template-only --verbose

# Test update_matrix_dynamic.py
python path/to/update_matrix_dynamic.py --json-file ./matrix.json --all stable --dry-run
```

### Inspect Generated Files

Examine the generated files for debugging:

```yaml
- name: Inspect generated files
  run: |
    echo "Matrix JSON content:"
    cat .github/json2vars-setter/matrix.json

    echo "Cache content:"
    cat .github/json2vars-setter/cache/version_cache.json
```

### Check GitHub API Quota

Monitor your GitHub API quota:

```yaml
- name: Check API rate limit
  run: |
    curl -s -H "Authorization: token ${{ secrets.GITHUB_TOKEN }}" https://api.github.com/rate_limit
```

## Edge Cases and Advanced Solutions

### Handling Large Matrices

If your matrix becomes too large, you can split it into smaller jobs:

```yaml
jobs:
  set_variables:
    # ... set variables job ...

  python_tests:
    needs: set_variables
    strategy:
      matrix:
        python-version: ${{ fromJson(needs.set_variables.outputs.versions_python) }}
        group: [1, 2, 3]  # Split tests into groups

    steps:
      # ... setup ...
      - name: Run tests for group ${{ matrix.group }}
        run: |
          pytest tests/group${{ matrix.group }} --verbose
```

### Handling Missing Languages

Create a fallback for languages not defined in your JSON:

```yaml
- name: Set fallback versions
  id: fallback
  run: |
    # Default values if not found in matrix.json
    echo "versions_ruby=[\"3.1\",\"3.2\"]" >> $GITHUB_OUTPUT

- name: Use actual or fallback versions
  run: |
    if [[ "${{ steps.json2vars.outputs.versions_ruby }}" == "" ]]; then
      echo "Using fallback Ruby versions: ${{ steps.fallback.outputs.versions_ruby }}"
      echo "RUBY_VERSIONS=${{ steps.fallback.outputs.versions_ruby }}" >> $GITHUB_ENV
    else
      echo "Using configured Ruby versions: ${{ steps.json2vars.outputs.versions_ruby }}"
      echo "RUBY_VERSIONS=${{ steps.json2vars.outputs.versions_ruby }}" >> $GITHUB_ENV
    fi
```

### Dynamic File Path Selection

Choose a JSON file dynamically based on context:

```yaml
- name: Determine config file
  id: config_file
  run: |
    if [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
      echo "file=.github/json2vars-setter/production_matrix.json" >> $GITHUB_OUTPUT
    else
      echo "file=.github/json2vars-setter/development_matrix.json" >> $GITHUB_OUTPUT
    fi

- name: Set variables from dynamic path
  id: json2vars
  uses: 7rikazhexde/json2vars-setter@main
  with:
    json-file: ${{ steps.config_file.outputs.file }}
```

### Conditional Strategy Selection

Select update strategy based on specific conditions:

```yaml
- name: Determine strategy
  id: strategy
  run: |
    DAY_OF_WEEK=$(date +%u)
    if [[ $DAY_OF_WEEK -eq 1 ]]; then  # Monday
      echo "update=true" >> $GITHUB_OUTPUT
      echo "strategy=latest" >> $GITHUB_OUTPUT
    else
      echo "update=false" >> $GITHUB_OUTPUT
    fi

- name: Set variables
  id: json2vars
  uses: 7rikazhexde/json2vars-setter@main
  with:
    json-file: .github/json2vars-setter/matrix.json
    update-matrix: ${{ steps.strategy.outputs.update }}
    all: ${{ steps.strategy.outputs.strategy }}
```

## GitHub API Rate Limit Management

### Authentication for Higher Limits

Use GitHub authentication to increase API rate limits:

```yaml
- name: Set up GitHub token
  run: |
    echo "GITHUB_TOKEN=${{ secrets.GITHUB_TOKEN }}" >> $GITHUB_ENV

- name: Set variables with authentication
  id: json2vars
  uses: 7rikazhexde/json2vars-setter@main
  with:
    json-file: .github/json2vars-setter/matrix.json
    update-matrix: 'true'
  env:
    GITHUB_TOKEN: ${{ env.GITHUB_TOKEN }}
```

### Minimize API Calls

Optimize your workflow to reduce API calls:

1. **Use caching with appropriate `max-age`**

   ```yaml
   - name: Set variables with caching
     uses: 7rikazhexde/json2vars-setter@main
     with:
       json-file: .github/json2vars-setter/matrix.json
       use-cache: 'true'
       cache-max-age: '7'  # Update weekly
   ```

2. **Use template-only mode when cache exists**

   ```yaml
   - name: Set variables from cache
     uses: 7rikazhexde/json2vars-setter@main
     with:
       json-file: .github/json2vars-setter/matrix.json
       use-cache: 'true'
       template-only: 'true'  # No API calls
   ```

3. **Schedule updates during low-traffic periods**

   ```yaml
   on:
     schedule:
       - cron: '0 3 * * 0'  # Sunday 3 AM
   ```

### Using Cache with Incremental Updates

Keep a comprehensive version history while minimizing API usage:

```yaml
- name: Update cache incrementally
  uses: 7rikazhexde/json2vars-setter@main
  with:
    json-file: .github/json2vars-setter/matrix.json
    use-cache: 'true'
    cache-max-age: '7'
    cache-incremental: 'true'
    cache-count: '30'  # Store up to 30 versions
```

## Next Steps

- Check the [basic examples](basic.md) for simple configurations
- See the [CI/CD examples](ci-cd.md) for integration patterns
- Review the [command options](../reference/options.md) reference for all available options
