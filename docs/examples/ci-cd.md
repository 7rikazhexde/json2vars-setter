# CI/CD Integration Examples

This page demonstrates how to integrate the JSON to Variables Setter action into comprehensive CI/CD pipelines. These examples build upon the [basic usage patterns](basic.md) to show more advanced workflow integrations.

## Complete CI/CD Pipeline Example

This example shows a complete CI/CD pipeline that uses json2vars-setter for both testing and deployment environments.

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 0 * * 1'  # Weekly update every Monday

jobs:
  # Step 1: Update matrix configuration (weekly or on main branch)
  update_matrix:
    if: github.event_name == 'schedule' || (github.event_name == 'push' && github.ref == 'refs/heads/main')
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Update matrix configuration
        uses: 7rikazhexde/json2vars-setter@main
        with:
          json-file: .github/json2vars-setter/matrix.json
          update-matrix: 'true'
          python-strategy: 'stable'
          nodejs-strategy: 'stable'

      - name: Commit updated matrix
        run: |
          git config --local user.email "actions@github.com"
          git config --local user.name "GitHub Actions"
          git add .github/json2vars-setter/matrix.json
          git commit -m "Update testing matrix with latest stable versions" || echo "No changes to commit"
          git push

  # Step 2: Define variables from matrix (always runs)
  set_variables:
    needs: [update_matrix]
    if: always()  # Run even if update_matrix is skipped
    runs-on: ubuntu-latest
    outputs:
      os: ${{ steps.json2vars.outputs.os }}
      versions_python: ${{ steps.json2vars.outputs.versions_python }}
      versions_nodejs: ${{ steps.json2vars.outputs.versions_nodejs }}
      ghpages_branch: ${{ steps.json2vars.outputs.ghpages_branch }}

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set variables from JSON
        id: json2vars
        uses: 7rikazhexde/json2vars-setter@main
        with:
          json-file: .github/json2vars-setter/matrix.json

  # Step 3: Run tests across matrix
  test:
    needs: [set_variables]
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false  # Continue with other jobs even if one fails
      matrix:
        os: ${{ fromJson(needs.set_variables.outputs.os) }}
        python-version: ${{ fromJson(needs.set_variables.outputs.versions_python) }}

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pytest
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

      - name: Run tests
        run: pytest
```

## Environment-Specific Configurations

This example demonstrates using different configurations for development and production environments.

```yaml
name: Environment-Specific Testing

on:
  push:
    branches: [ main, dev ]
  pull_request:
    branches: [ main, dev ]

jobs:
  set_variables:
    runs-on: ubuntu-latest
    outputs:
      matrix_config: ${{ steps.matrix_config.outputs.config }}

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Determine environment
        id: environment
        run: |
          if [[ "${{ github.ref }}" == "refs/heads/main" || "${{ github.base_ref }}" == "main" ]]; then
            echo "env=production" >> $GITHUB_OUTPUT
          else
            echo "env=development" >> $GITHUB_OUTPUT
          fi

      - name: Set variables for production
        id: json2vars_prod
        if: steps.environment.outputs.env == 'production'
        uses: 7rikazhexde/json2vars-setter@main
        with:
          json-file: .github/json2vars-setter/production_matrix.json

      - name: Set variables for development
        id: json2vars_dev
        if: steps.environment.outputs.env == 'development'
        uses: 7rikazhexde/json2vars-setter@main
        with:
          json-file: .github/json2vars-setter/development_matrix.json
          update-matrix: 'true'
          all: 'latest'

      - name: Set matrix configuration
        id: matrix_config
        run: |
          if [[ "${{ steps.environment.outputs.env }}" == "production" ]]; then
            echo "config={\"os\":${{ steps.json2vars_prod.outputs.os }},\"python-version\":${{ steps.json2vars_prod.outputs.versions_python }}}" >> $GITHUB_OUTPUT
          else
            echo "config={\"os\":${{ steps.json2vars_dev.outputs.os }},\"python-version\":${{ steps.json2vars_dev.outputs.versions_python }}}" >> $GITHUB_OUTPUT
          fi

  test:
    needs: set_variables
    runs-on: ${{ matrix.os }}
    strategy:
      matrix: ${{ fromJson(needs.set_variables.outputs.matrix_config) }}

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Run tests
        run: |
          python -m pip install --upgrade pip
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
          pytest
```

With production_matrix.json:

```json
{
    "os": [
        "ubuntu-latest",
        "windows-latest",
        "macos-latest"
    ],
    "versions": {
        "python": [
            "3.10",
            "3.11"
        ]
    }
}
```

And development_matrix.json:

```json
{
    "os": [
        "ubuntu-latest"
    ],
    "versions": {
        "python": [
            "3.11",
            "3.12"
        ]
    }
}
```

## Optimized Strategy for Large Projects

This example shows an optimized approach for large projects with multiple languages, using caching to reduce API calls.

```yaml
name: Multi-Language Project CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  update_cache:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Update version cache
        uses: 7rikazhexde/json2vars-setter@main
        with:
          json-file: .github/json2vars-setter/matrix.json
          use-cache: 'true'
          force-cache-update: 'true'
          cache-incremental: 'true'
          cache-count: '20'
          cache-only: 'true'  # Only update cache, don't generate template

      - name: Commit updated cache
        run: |
          git config --local user.email "actions@github.com"
          git config --local user.name "GitHub Actions"
          git add .github/json2vars-setter/cache
          git commit -m "Update version cache" || echo "No changes to commit"
          git push

  set_variables:
    runs-on: ubuntu-latest
    needs: [update_cache]
    if: always()  # Run even if update_cache is skipped or fails
    outputs:
      versions_python: ${{ steps.json2vars.outputs.versions_python }}
      versions_nodejs: ${{ steps.json2vars.outputs.versions_nodejs }}
      versions_ruby: ${{ steps.json2vars.outputs.versions_ruby }}
      versions_go: ${{ steps.json2vars.outputs.versions_go }}

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set variables from cache
        id: json2vars
        uses: 7rikazhexde/json2vars-setter@main
        with:
          json-file: .github/json2vars-setter/matrix.json
          use-cache: 'true'
          template-only: 'true'  # Use existing cache
          sort-order: 'desc'

  test_python:
    needs: set_variables
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ${{ fromJson(needs.set_variables.outputs.versions_python) }}
      fail-fast: false

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Run Python tests
        run: pytest python_tests/

  test_nodejs:
    needs: set_variables
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: ${{ fromJson(needs.set_variables.outputs.versions_nodejs) }}
      fail-fast: false

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
      - name: Run Node.js tests
        run: npm test

  # Similar jobs for Ruby and Go
```

## Scheduled Maintenance Workflow

This example demonstrates a dedicated maintenance workflow that runs on a schedule to keep your matrix configuration up-to-date.

```yaml
name: Matrix Maintenance

on:
  schedule:
    - cron: '0 0 * * 0'  # Run every Sunday at midnight
  workflow_dispatch:     # Allow manual triggering

jobs:
  update_cache:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Update version cache
        uses: 7rikazhexde/json2vars-setter@main
        with:
          json-file: .github/json2vars-setter/matrix.json
          use-cache: 'true'
          cache-max-age: '1'  # Force update
          cache-incremental: 'true'
          cache-languages: 'python,nodejs,ruby,go,rust'
          keep-existing: 'true'

      - name: Update dynamic versions
        uses: 7rikazhexde/json2vars-setter@main
        with:
          json-file: .github/json2vars-setter/latest_matrix.json
          update-matrix: 'true'
          all: 'latest'

      - name: Commit updated files
        run: |
          git config --local user.email "actions@github.com"
          git config --local user.name "GitHub Actions"
          git add .github/json2vars-setter/matrix.json
          git add .github/json2vars-setter/latest_matrix.json
          git add .github/json2vars-setter/cache
          git commit -m "Weekly matrix configuration update" || echo "No changes to commit"
          git push
```

## Monorepo Project Configuration

This example demonstrates how to handle multiple projects in a monorepo, each with their own language requirements.

```yaml
name: Monorepo CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
    paths:
      - 'project-a/**'
      - 'project-b/**'
      - '.github/json2vars-setter/**'

jobs:
  detect_changes:
    runs-on: ubuntu-latest
    outputs:
      project_a: ${{ steps.filter.outputs.project_a }}
      project_b: ${{ steps.filter.outputs.project_b }}

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Check for changes
        uses: dorny/paths-filter@v2
        id: filter
        with:
          filters: |
            project_a:
              - 'project-a/**'
            project_b:
              - 'project-b/**'

  # Project A (Python)
  set_variables_a:
    needs: detect_changes
    if: needs.detect_changes.outputs.project_a == 'true'
    runs-on: ubuntu-latest
    outputs:
      versions_python: ${{ steps.json2vars.outputs.versions_python }}

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set variables for Project A
        id: json2vars
        uses: 7rikazhexde/json2vars-setter@main
        with:
          json-file: project-a/.github/matrix.json
          use-cache: 'true'
          cache-languages: 'python'
          keep-existing: 'true'

  test_project_a:
    needs: [detect_changes, set_variables_a]
    if: needs.detect_changes.outputs.project_a == 'true'
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ${{ fromJson(needs.set_variables_a.outputs.versions_python) }}

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Test Project A
        run: |
          cd project-a
          pip install -r requirements.txt
          pytest

  # Project B (Node.js)
  set_variables_b:
    needs: detect_changes
    if: needs.detect_changes.outputs.project_b == 'true'
    runs-on: ubuntu-latest
    outputs:
      versions_nodejs: ${{ steps.json2vars.outputs.versions_nodejs }}

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set variables for Project B
        id: json2vars
        uses: 7rikazhexde/json2vars-setter@main
        with:
          json-file: project-b/.github/matrix.json
          use-cache: 'true'
          cache-languages: 'nodejs'
          keep-existing: 'true'

  test_project_b:
    needs: [detect_changes, set_variables_b]
    if: needs.detect_changes.outputs.project_b == 'true'
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: ${{ fromJson(needs.set_variables_b.outputs.versions_nodejs) }}

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}

      - name: Test Project B
        run: |
          cd project-b
          npm install
          npm test
```

## Next Steps

- For simpler usage patterns, see [Basic Examples](basic.md)
- For full command line options, see the [Command Options Reference](../reference/options.md)
