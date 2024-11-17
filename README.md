# JSON to Variables Setter

[![GitHub Marketplace](https://img.shields.io/badge/Marketplace-JSON%20to%20Variables%20Setter-green?colorA=24292e&colorB=3fb950&logo=github)](https://github.com/marketplace/actions/json-to-variables-setter)

## Overview

**JSON to Variables Setter (json2vars-setter)** is a GitHub Action designed to parse a JSON file and set the resulting variables (such as operating systems, programming language versions, and GitHub Pages branch) as outputs in a GitHub Actions workflow.

## Table of Contents

- [JSON to Variables Setter](#json-to-variables-setter)
  - [Overview](#overview)
  - [Table of Contents](#table-of-contents)
  - [Supported GitHub Actions Matrix Components](#supported-github-actions-matrix-components)
  - [Usage](#usage)
    - [Action Configuration](#action-configuration)
    - [Inputs](#inputs)
    - [Outputs](#outputs)
  - [Examples](#examples)
    - [Variable Reference Examples](#variable-reference-examples)
    - [1. Basic Usage (Within Same Job)](#1-basic-usage-within-same-job)
    - [2. Cross-Job Usage (Using needs Context)](#2-cross-job-usage-using-needs-context)
    - [3. Advanced Shell Processing](#3-advanced-shell-processing)
  - [Language-specific Workflows](#language-specific-workflows)
  - [License](#license)

## Supported GitHub Actions Matrix Components

| Languages | Test Status |
|-------|-------|
| [![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)](.github/workflows/python_test.yml) | [![Python Test](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/7rikazhexde/26cb492ab0cfff920c516a622b2bfa44/raw/python-test-badge.json&cacheSeconds=0)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/python_test.yml) |
| [![Node.js](https://img.shields.io/badge/Node.js-339933?style=flat&logo=node.js&logoColor=white)](.github/workflows/nodejs_test.yml) | [![Node.js Test](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/7rikazhexde/11f46ff9ef47d3362dabe767255b0d9e/raw/nodejs-test-badge.json&cacheSeconds=0)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/nodejs_test.yml) |
| [![Ruby](https://img.shields.io/badge/Ruby-CC342D?style=flat&logo=ruby&logoColor=white)](.github/workflows/ruby_test.yml) | [![Ruby Test](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/7rikazhexde/511ba5b5711e66c507292ba00cf0a219/raw/ruby-test-badge.json&cacheSeconds=0)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/ruby_test.yml) |
| [![Go](https://img.shields.io/badge/Go-00ADD8?style=flat&logo=go&logoColor=white)](.github/workflows/go_test.yml) | [![Go Test](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/7rikazhexde/c334da204406866563668140885d170e/raw/go-test-badge.json&cacheSeconds=0)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/go_test.yml) |
| [![Rust](https://img.shields.io/badge/Rust-000000?style=flat&logo=rust&logoColor=white)](.github/workflows/rust_test.yml) | [![Rust Test](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/7rikazhexde/5e160d06cfffd42a8f0e4ae6e8e8f025/raw/rust-test-badge.json&cacheSeconds=0)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/rust_test.yml) |

## Usage

This action reads a JSON file (default path: `.github/workflows/matrix.json`) and sets GitHub Actions outputs based on the parsed data.

> [!NOTE]
> - Please create the JSON file by referring to the [Examples](#examples).
> - By default, the JSON file path is `.github/workflows/matrix.json`. If you create a custom file, specify it in the `7rikazhexde/json2vars-setter` action.
> - In the workflow, only the variables specified in the Outputs section are available.
> - Language versions are optional. If a language is not defined in the JSON, its corresponding output will be empty.

### Action Configuration

```yml
jobs:
  set_variables:
    runs-on: ubuntu-latest
    outputs:
      os: ${{ steps.json2vars.outputs.os }}
      versions_python: ${{ steps.json2vars.outputs.versions_python }}
      ghpages_branch: ${{ steps.json2vars.outputs.ghpages_branch }}
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4.2.2
        with:
          fetch-depth: 0

      - name: Set variables from JSON
        id: json2vars
        uses: 7rikazhexde/json2vars-setter@main
        with:
          json-file: .github/workflows/python_project_matrix.json
```

### Inputs

| Input             | Description                                                        | Required |
|-------------------|--------------------------------------------------------------------|----------|
| `json-file`       | Path to the JSON file.<br>Default: `.github/workflows/matrix.json` | No       |

### Outputs

> [!IMPORTANT]  
> - In order to reference them in both steps and jobs, outputs must be specified.<br>Please check the [Examples](#examples) section for details.

| Output            | Description                |
|-------------------|----------------------------|
| `os`              | List of operating systems  |
| `versions_python` | List of Python versions    |
| `versions_ruby`   | List of Ruby versions      |
| `versions_nodejs` | List of Node.js versions   |
| `versions_go`     | List of Go versions        |
| `versions_rust`   | List of Rust versions      |
| `ghpages_branch`  | GitHub Pages branch name   |

## Examples

This action uses a JSON configuration file (e.g. [matrix.json](.github/workflows/matrix.json)) to define your matrix testing environments.

<details>
<summary>Complete Configuration Example</summary>

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
            "3.12",
            "3.13"
        ],
        "ruby": [
            "3.0.6",
            "3.1.6",
            "3.2.6"
        ],
        "nodejs": [
            "16",
            "18",
            "20"
        ],
        "go": [
            "1.21.0",
            "1.22.0"
        ],
        "rust": [
            "1.75.0",
            "1.76.0",
            "stable"
        ]
    },
    "ghpages_branch": "gh-pages"
}
```

</details>

You can also create a simplified configuration by including only the languages you need. For example, if your project only uses `Python`(e.g. [python_project_matrix.json](.github/workflows/python_project_matrix.json)).

> [!TIP]
> - Only specify the languages you actually use.
> - Outputs for undefined languages will be empty arrays.
> - This helps keep your JSON configuration concise and maintainable.

<details>
<summary>Simplified Configuration Example</summary>

```jsonc
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
            "3.12",
            "3.13"
        ]
        // Other language versions can be omitted if not used
    },
    "ghpages_branch": "gh-pages"
}
```

</details>

### Variable Reference Examples

This section demonstrates various ways to reference the output variables in your workflow.

> [!TIP]
> - For list variables, always remember to use `fromJson()` when accessing individual elements
> - When setting list variables in shell scripts, use single quotes (`'`) to preserve the JSON structure
> - Use `jq` for complex JSON array manipulations in shell scripts

### 1. Basic Usage (Within Same Job)

The simplest way to access variables is within the same job using the `steps` context:

<details>
<summary>Code Example</summary>

```yaml
steps:
  - name: Access Variables
    run: |
      # Direct access to list variables
      echo "os: ${{ steps.json2vars.outputs.os }}"
      echo "versions_python: ${{ steps.json2vars.outputs.versions_python }}"

      # Access individual elements
      echo "First OS: ${{ fromJson(steps.json2vars.outputs.os)[0] }}"
      echo "First Python version: ${{ fromJson(steps.json2vars.outputs.versions_python)[0] }}"

      # Access non-list variables
      echo "Branch: ${{ steps.json2vars.outputs.ghpages_branch }}"
```

</details>

<details>
<summary>Example Output</summary>

```bash
os: ["ubuntu-latest", "windows-latest", "macos-latest"]
versions_python: ["3.10", "3.11", "3.12", "3.13"]
First OS: ubuntu-latest
First Python version: 3.10
Branch: ghpages
```

</details>

### 2. Cross-Job Usage (Using needs Context)

To use variables across different jobs, use the `needs` context and ensure outputs are properly defined in the source job.

<details>
<summary>Matrix Strategy Usage</summary>

```yaml
strategy:
  matrix:
    os: ${{ fromJson(needs.job1.outputs.os) }}
    python-version: ${{ fromJson(needs.job1.outputs.versions_python) }}
```

</details>

<details>
<summary>Variable Access in Steps</summary>

```yaml
steps:
  - name: Access Variables
    run: |
      # Non-list variables
      branch="${{ needs.job1.outputs.ghpages_branch }}"

      # List variables (note the single quotes)
      os='${{ needs.job1.outputs.os }}'
      versions_python='${{ needs.job1.outputs.versions_python }}'

      # Individual elements
      first_os="${{ fromJson(needs.job1.outputs.os)[0] }}"
      first_version="${{ fromJson(needs.job1.outputs.versions_python)[0] }}"
```

</details>

### 3. Advanced Shell Processing

For more complex operations, you can process the JSON arrays using shell commands with `jq`.

<details>
<summary>Processing Arrays in Shell</summary>

```yaml
steps:
  - name: Process Variables
    run: |
      # Convert JSON arrays to space-separated lists
      os_list=$(echo '${{ needs.job1.outputs.os }}' | jq -r '.[]' | tr '\n' ' ' | sed 's/ $//')
      versions_list=$(echo '${{ needs.job1.outputs.versions_python }}' | jq -r '.[]' | tr '\n' ' ' | sed 's/ $//')

      # Example: Generate combinations
      for os in ${os_list}; do
        for version in ${versions_list}; do
          echo "OS: ${os}, Python Version: ${version}"
        done
      done
```

</details>

<details>
<summary>Example Output</summary>

```bash
OS: ubuntu-latest, Python Version: 3.10
OS: ubuntu-latest, Python Version: 3.11
OS: ubuntu-latest, Python Version: 3.12
OS: ubuntu-latest, Python Version: 3.13
OS: windows-latest, Python Version: 3.10
OS: windows-latest, Python Version: 3.11
OS: windows-latest, Python Version: 3.12
OS: windows-latest, Python Version: 3.13
OS: macos-latest, Python Version: 3.10
OS: macos-latest, Python Version: 3.11
OS: macos-latest, Python Version: 3.12
OS: macos-latest, Python Version: 3.13
```

</details>

## Language-specific Workflows

For language-specific workflow examples, please refer to:

- Python: [python_test.yml](.github/workflows/python_test.yml)
- Node.js: [nodejs_test.yml](.github/workflows/nodejs_test.yml)
- Ruby: [ruby_test.yml](.github/workflows/ruby_test.yml)
- Go: [go_test.yml](.github/workflows/go_test.yml)
- Rust: [rust_test.yml](.github/workflows/rust_test.yml)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
