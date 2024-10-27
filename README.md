
# JSON to Variables Setter

## Overview

**JSON to Variables Setter (json2vars-setter)** is a GitHub Action designed to parse a JSON file and set the resulting variables (such as operating systems, Python versions, and GitHub Pages branch) as outputs in a GitHub Actions workflow.

## Table of contents

- [JSON to Variables Setter](#json-to-variables-setter)
  - [Overview](#overview)
  - [Table of contents](#table-of-contents)
  - [Usage](#usage)
    - [Inputs](#inputs)
    - [Outputs](#outputs)
  - [Example JSON File](#example-json-file)
  - [Example Workflow](#example-workflow)
  - [License](#license)

## Usage

This action reads a JSON file (default path: `.github/workflows/matrix.json`) and sets GitHub Actions outputs based on the parsed data.

> [!NOTE]
> - Please create the JSON file by referring to the [Example JSON File](#example-json-file).
> - By default, the JSON file path is `.github/workflows/matrix.json`. If you create a custom file, specify it in the `7rikazhexde/json2vars-setter` action.
> - In the workflow, only the variables specified in the Outputs section are available.

### Inputs

| Input             | Description                                                        | Required |
|-------------------|--------------------------------------------------------------------|----------|
| `json-file`       | Path to the JSON file.<br>Default: `.github/workflows/matrix.json` | No       |

### Outputs

> [!IMPORTANT]  
> Please chack [Example Workflow](#example-workflow)\
> (*1): In order to reference them in both steps and jobs, outputs must be specified.\
> (*2): For lists, explicitly enclose the list in "" to make it a string. (Note that it is not '').

| Input             | Description                |
|-------------------|----------------------------|
| `os`              | List of operating systems  |
| `versions_python` | List of Python versions    |
| `ghpages_branch`  | GitHub Pages branch name   |

## Example JSON File

Here is an example of a JSON file that can be used with this action

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
    "ghpages_branch": "ghgapes"
}
```

## Example Workflow

Below is an example of how to use the ***name: Set variables from JSON*** in a GitHub Actions workflow

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
          echo "versions_python: ${{ steps.json2vars.outputs.versions_python }}"
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

          echo "os: $os"
          echo "versions_python: ${versions_python}"
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

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
