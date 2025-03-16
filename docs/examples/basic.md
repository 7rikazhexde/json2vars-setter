# Basic Usage Examples

This page demonstrates basic usage patterns for the JSON to Variables Setter action. These examples cover common scenarios and provide a foundation for integrating the action into your workflows.

## Simple JSON Parsing

The most basic use case is parsing a JSON file to make its values available as GitHub Actions outputs.

### Configuration File

First, create a matrix.json file in `.github/json2vars-setter/`:

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
            "3.11",
            "3.12"
        ]
    },
    "ghpages_branch": "gh-pages"
}
```

### Basic Workflow

```yaml
name: Basic Example

jobs:
  set_variables:
    runs-on: ubuntu-latest
    outputs:
      os: ${{ steps.json2vars.outputs.os }}
      versions_python: ${{ steps.json2vars.outputs.versions_python }}
      ghpages_branch: ${{ steps.json2vars.outputs.ghpages_branch }}

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set variables from JSON
        id: json2vars
        uses: 7rikazhexde/json2vars-setter@v1.0.1
        with:
          json-file: .github/json2vars-setter/sample/matrix.json

      - name: Check outputs
        run: |
          echo "Operating Systems: ${{ steps.json2vars.outputs.os }}"
          echo "Python Versions: ${{ steps.json2vars.outputs.versions_python }}"
          echo "GitHub Pages Branch: ${{ steps.json2vars.outputs.ghpages_branch }}"
```

## Matrix Strategy Example

This example demonstrates how to use the parsed values in a matrix strategy for parallel testing.

```yaml
name: Matrix Testing

jobs:
  set_variables:
    runs-on: ubuntu-latest
    outputs:
      os: ${{ steps.json2vars.outputs.os }}
      versions_python: ${{ steps.json2vars.outputs.versions_python }}

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set variables from JSON
        id: json2vars
        uses: 7rikazhexde/json2vars-setter@v1.0.1
        with:
          json-file: .github/json2vars-setter/sample/matrix.json

  test:
    needs: set_variables
    runs-on: ${{ matrix.os }}
    strategy:
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

      - name: Run tests
        run: |
          python -m pip install --upgrade pip
          pip install pytest
          pytest
```

## Dynamic Update Example

This example shows how to dynamically update your matrix JSON with the latest language versions.

```yaml
name: Dynamic Matrix Update

jobs:
  build_and_test:
    runs-on: ubuntu-latest
    outputs:
      os: ${{ steps.json2vars.outputs.os }}
      versions_python: ${{ steps.json2vars.outputs.versions_python }}
      versions_nodejs: ${{ steps.json2vars.outputs.versions_nodejs }}

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set variables with dynamic update
        id: json2vars
        uses: 7rikazhexde/json2vars-setter@v1.0.1
        with:
          json-file: .github/json2vars-setter/sample/matrix.json
          update-matrix: 'true'
          python-strategy: 'stable'
          nodejs-strategy: 'latest'

      - name: Show updated matrix
        run: |
          echo "Python versions: ${{ steps.json2vars.outputs.versions_python }}"
          echo "Node.js versions: ${{ steps.json2vars.outputs.versions_nodejs }}"

  test_python:
    needs: build_and_test
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ${{ fromJson(needs.build_and_test.outputs.versions_python) }}

    steps:
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Check Python version
        run: python --version
```

## Version Caching Example

This example demonstrates how to use the version caching feature to reduce API calls.

```yaml
name: Cached Version Matrix

jobs:
  set_variables:
    runs-on: ubuntu-latest
    outputs:
      os: ${{ steps.json2vars.outputs.os }}
      versions_python: ${{ steps.json2vars.outputs.versions_python }}

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set variables with cached versions
        id: json2vars
        uses: 7rikazhexde/json2vars-setter@v1.0.1
        with:
          json-file: .github/json2vars-setter/sample/matrix.json
          use-cache: 'true'
          cache-max-age: '7'  # Update cache if older than 7 days
          cache-languages: 'python'
          keep-existing: 'true'

      - name: Show cached versions
        run: |
          echo "Python versions: ${{ steps.json2vars.outputs.versions_python }}"
```

## Custom Matrix Configuration

This example shows how to use a custom matrix configuration file.

```yaml
name: Custom Matrix Configuration

jobs:
  set_variables:
    runs-on: ubuntu-latest
    outputs:
      os: ${{ steps.json2vars.outputs.os }}
      versions_python: ${{ steps.json2vars.outputs.versions_python }}

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set variables from custom JSON
        id: json2vars
        uses: 7rikazhexde/json2vars-setter@v1.0.1
        with:
          json-file: .github/json2vars-setter/sample/python_project_matrix.json

      - name: Show configured versions
        run: |
          echo "Python versions: ${{ steps.json2vars.outputs.versions_python }}"
```

With custom matrix file `.github/json2vars-setter/python_project_matrix.json`:

```json
{
    "os": [
        "ubuntu-latest"
    ],
    "versions": {
        "python": [
            "3.9",
            "3.10",
            "3.11"
        ]
    }
}
```

## Multiple Language Example

This example demonstrates testing with multiple programming languages configured in the matrix.

```yaml
name: Multi-language Tests

jobs:
  set_variables:
    runs-on: ubuntu-latest
    outputs:
      os: ${{ steps.json2vars.outputs.os }}
      versions_python: ${{ steps.json2vars.outputs.versions_python }}
      versions_nodejs: ${{ steps.json2vars.outputs.versions_nodejs }}

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set variables from JSON
        id: json2vars
        uses: 7rikazhexde/json2vars-setter@v1.0.1
        with:
          json-file: .github/json2vars-setter/sample/matrix.json

  test_python:
    needs: set_variables
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ${{ fromJson(needs.set_variables.outputs.versions_python) }}

    steps:
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Run Python tests
        run: |
          python --version
          # ... run your Python tests ...

  test_nodejs:
    needs: set_variables
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: ${{ fromJson(needs.set_variables.outputs.versions_nodejs) }}

    steps:
      - name: Set up Node.js ${{ matrix.node-version }}
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}

      - name: Run Node.js tests
        run: |
          node --version
          # ... run your Node.js tests ...
```

## Weekly Matrix Update Example

This example demonstrates how to set up a scheduled workflow to update your matrix weekly.

```yaml
name: Weekly Matrix Update

on:
  schedule:
    - cron: '0 0 * * 0'  # Run every Sunday at midnight

jobs:
  update_matrix:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Update matrix.json
        uses: 7rikazhexde/json2vars-setter@v1.0.1
        with:
          json-file: .github/json2vars-setter/sample/matrix.json
          update-matrix: 'true'
          all: 'stable'  # Use stable versions for all languages

      - name: Commit changes
        run: |
          git config --local user.email "actions@github.com"
          git config --local user.name "GitHub Actions"
          git add .github/json2vars-setter/matrix.json
          git commit -m "Update testing matrix with latest stable versions" || echo "No changes to commit"
          git push
```

## Next Steps

- See the [CI/CD examples](ci-cd.md) for integration patterns
- Visit [Troubleshooting](troubleshooting.md) for help with common issues
- Review the [command options](../reference/options.md) reference for all available options
