# JSON to Variables Setter

[![GitHub Marketplace](https://img.shields.io/badge/Marketplace-JSON%20to%20Variables%20Setter-green?colorA=24292e&colorB=3fb950&logo=github)](https://github.com/marketplace/actions/json-to-variables-setter)

## Overview

**JSON to Variables Setter (json2vars-setter)** is a GitHub Action designed to parse a JSON file and set the resulting variables (such as operating systems, programming language versions, and GitHub Pages branch) as outputs in a GitHub Actions workflow.

## Supported GitHub Actions Matrix Components

| Languages | Test Status |
|-------|-------|
| [![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)](.github/workflows/python_test.yml) | [![Python Test](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/7rikazhexde/26cb492ab0cfff920c516a622b2bfa44/raw/python-test-badge.json&cacheSeconds=0)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/python_test.yml) |
| [![Node.js](https://img.shields.io/badge/Node.js-339933?style=flat&logo=node.js&logoColor=white)](.github/workflows/nodejs_test.yml) | [![Node.js Test](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/7rikazhexde/11f46ff9ef47d3362dabe767255b0d9e/raw/nodejs-test-badge.json&cacheSeconds=0)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/nodejs_test.yml) |
| [![Ruby](https://img.shields.io/badge/Ruby-CC342D?style=flat&logo=ruby&logoColor=white)](.github/workflows/ruby_test.yml) | [![Ruby Test](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/7rikazhexde/511ba5b5711e66c507292ba00cf0a219/raw/ruby-test-badge.json&cacheSeconds=0)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/ruby_test.yml) |
| [![Go](https://img.shields.io/badge/Go-00ADD8?style=flat&logo=go&logoColor=white)](.github/workflows/go_test.yml) | [![Go Test](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/7rikazhexde/c334da204406866563668140885d170e/raw/go-test-badge.json&cacheSeconds=0)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/go_test.yml) |
| [![Rust](https://img.shields.io/badge/Rust-000000?style=flat&logo=rust&logoColor=white)](.github/workflows/rust_test.yml) | [![Rust Test](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/7rikazhexde/5e160d06cfffd42a8f0e4ae6e8e8f025/raw/rust-test-badge.json&cacheSeconds=0)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/rust_test.yml) |

## Table of contents

- [JSON to Variables Setter](#json-to-variables-setter)
  - [Overview](#overview)
  - [Supported GitHub Actions Matrix Components](#supported-github-actions-matrix-components)
  - [Table of contents](#table-of-contents)
  - [Usage](#usage)
    - [Inputs](#inputs)
    - [Outputs](#outputs)
  - [Example JSON File](#example-json-file)
  - [Example Workflow](#example-workflow)
  - [Language-specific Workflows](#language-specific-workflows)
  - [License](#license)

## Usage

This action reads a JSON file (default path: `.github/workflows/matrix.json`) and sets GitHub Actions outputs based on the parsed data.

> [!NOTE]
> - Please create the JSON file by referring to the [Example JSON File](#example-json-file).
> - By default, the JSON file path is `.github/workflows/matrix.json`. If you create a custom file, specify it in the `7rikazhexde/json2vars-setter` action.
> - In the workflow, only the variables specified in the Outputs section are available.
> - Language versions are optional. If a language is not defined in the JSON, its corresponding output will be empty.

### Inputs

| Input             | Description                                                        | Required |
|-------------------|--------------------------------------------------------------------|----------|
| `json-file`       | Path to the JSON file.<br>Default: `.github/workflows/matrix.json` | No       |

### Outputs

> [!IMPORTANT]  
> Please check [Example Workflow](#example-workflow).\
> (*1): In order to reference them in both steps and jobs, outputs must be specified.\
> (*2): For lists, explicitly enclose the list in "" to make it a string. (Note that it is not '').

| Output            | Description                |
|-------------------|----------------------------|
| `os`              | List of operating systems  |
| `versions_python` | List of Python versions    |
| `versions_ruby`   | List of Ruby versions      |
| `versions_nodejs` | List of Node.js versions   |
| `versions_go`     | List of Go versions        |
| `versions_rust`   | List of Rust versions      |
| `ghpages_branch`  | GitHub Pages branch name   |

## Example JSON File

Here is an example of a JSON file that can be used with this action.

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
            "20",
            "22"
        ],
        "go": [
            "1.23.0",
            "1.23.1",
            "1.23.2"
        ],
        "rust": [
            "1.79.0",
            "1.80.0",
            "1.81.0",
            "1.82.0",
            "stable"
        ]
    },
    "ghpages_branch": "ghgapes"
}
```

You can also define only specific languages.\
Undefined language versions will result in empty outputs(*3).

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
        //(*3)
    },
    "ghpages_branch": "ghgapes"
}
```

## Example Workflow

Below is a **Python Example** of how to use the ***name: Set variables from JSON*** in a GitHub Actions workflow.  

See [Language-specific Workflows](#language-specific-workflows) for workflow examples in other languages(**Node.js**, **Ruby**, **Go**, **Rust**).  

```yaml
name: Test on PR by matrix.json (Except Dependabot)

on:
  pull_request:
    branches: ["main"]

jobs:
  set_variables:
    if: github.actor != 'dependabot[bot]' && !startsWith(github.event.pull_request.title, 'Bump version')
    runs-on: ubuntu-latest
    outputs: # (*1)
      os: ${{ steps.json2vars.outputs.os }}
      versions_python: ${{ steps.json2vars.outputs.versions_python }}
      ghpages_branch: ${{ steps.json2vars.outputs.ghpages_branch }}
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4.2.1
        with:
          fetch-depth: 0

      - name: Set variables from JSON
        id: json2vars
        uses: 7rikazhexde/json2vars-setter@main
        # Not required if using .github/workflows/matrix.json
        with:
          json-file: .github/workflows/python_project_matrix.json

      - name: Debug output values
        run: |
          echo "os: ${{ steps.json2vars.outputs.os }}"
          echo "os[0]: ${{ fromJson(steps.json2vars.outputs.os)[0] }}"
          echo "os[1]: ${{ fromJson(steps.json2vars.outputs.os)[1] }}"
          echo "os[2]: ${{ fromJson(steps.json2vars.outputs.os)[2] }}"
          echo "versions_python: ${{ steps.json2vars.outputs.versions_python }}"
          echo "versions_python[0]: ${{ fromJson(steps.json2vars.outputs.versions_python)[0] }}"
          echo "versions_python[1]: ${{ fromJson(steps.json2vars.outputs.versions_python)[1] }}"
          echo "versions_python[2]: ${{ fromJson(steps.json2vars.outputs.versions_python)[2] }}"
          echo "versions_python[3]: ${{ fromJson(steps.json2vars.outputs.versions_python)[3] }}"
          echo "ghpages_branch: ${{ steps.json2vars.outputs.ghpages_branch }}"

  run_tests:
    needs: set_variables
    strategy:
      matrix:
        os: ${{ fromJson(needs.set_variables.outputs.os) }}
        python-version: ${{ fromJson(needs.set_variables.outputs.versions_python) }}
    runs-on: ${{ matrix.os }}
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4.2.1
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5.2.0
        with:
          python-version: ${{ matrix.python-version }}

      - name: Show variables
        shell: bash
        run: |
          # For non-list case
          ghpages_branch="${{ needs.set_variables.outputs.ghpages_branch }}"

          # For list case, explicitly enclose the list in “” to make it a string. (Note that it is not ''.)(*2)
          os='${{ needs.set_variables.outputs.os }}'
          versions_python='${{ needs.set_variables.outputs.versions_python }}'

          # For list index case
          os_0="${{ fromJson(needs.set_variables.outputs.os)[0] }}"
          os_1="${{ fromJson(needs.set_variables.outputs.os)[1] }}"
          os_2="${{ fromJson(needs.set_variables.outputs.os)[2] }}"

          versions_python_0="${{ fromJson(needs.set_variables.outputs.versions_python)[0] }}"
          versions_python_1="${{ fromJson(needs.set_variables.outputs.versions_python)[1] }}"
          versions_python_2="${{ fromJson(needs.set_variables.outputs.versions_python)[2] }}"
          versions_python_3="${{ fromJson(needs.set_variables.outputs.versions_python)[3] }}"

          echo "os: ${os}"
          echo "os_0: ${os_0}"
          echo "os_1: ${os_1}"
          echo "os_2: ${os_2}"
          echo "versions_python: ${versions_python}"
          echo "versions_python_0: ${versions_python_0}"
          echo "versions_python_1: ${versions_python_1}"
          echo "versions_python_2: ${versions_python_2}"
          echo "versions_python_3: ${versions_python_3}"
          echo "ghpages_branch: ${ghpages_branch}"

          # For loop case
          os_list=$(echo "${os}" | jq -r '.[]' | tr '\n' ' ' | sed 's/ $//')
          python_versions_list=$(echo "${versions_python}" | jq -r '.[]' | tr '\n' ' ' | sed 's/ $//')

          for current_os in ${os_list}; do
            for version in ${python_versions_list}; do
              echo "Current OS: ${current_os}, Current Python Version: ${version}"
            done
          done

      - name: Run pytest
        id: pytest
        shell: bash
        run: |
          output="$(poetry run pytest)"
          echo "${output}"
```

## Language-specific Workflows

For language-specific workflow examples, please refer to

- Node.js: [nodejs_test.yml](.github/workflows/nodejs_test.yml)
- Ruby: [ruby_test.yml](.github/workflows/ruby_test.yml)
- Go: [go_test.yml](.github/workflows/go_test.yml)
- Rust: [rust_test.yml](.github/workflows/rust_test.yml)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
