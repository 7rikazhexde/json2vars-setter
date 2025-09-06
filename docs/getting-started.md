# Getting Started

This guide will help you set up and use the JSON to Variables Setter action in your GitHub workflow.

## Prerequisites

- A GitHub repository where you want to implement the action
- Basic understanding of GitHub Actions workflows

## Installation

As this is a GitHub Action, there's no installation required. You simply reference the action in your workflow file.

## Basic Setup

### Step 1: Create a JSON Configuration File

First, create a JSON file to define your matrix testing environment. By default, the action looks for this file at `.github/json2vars-setter/matrix.json`.

Here's a basic example:

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

You only need to include the languages your project uses. For example, if your project only uses Python, you don't need to include other languages like Ruby or Node.js.

### Step 2: Configure Your Workflow

Add the JSON to Variables Setter action to your workflow file. Here's a basic example:

```yaml
name: Build and Test

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
        uses: 7rikazhexde/json2vars-setter@v1.0.2
        with:
          json-file: .github/json2vars-setter/sample/matrix.json
```

!!! important
    Make sure to define the outputs at the job level if you plan to use them in other jobs.

### Step 3: Use the Generated Variables

Now you can use the variables in your workflow. There are several ways to access them:

#### Within the Same Job

```yaml
- name: Access Variables
  run: |
    echo "OS List: ${{ steps.json2vars.outputs.os }}"
    echo "First OS: ${{ fromJson(steps.json2vars.outputs.os)[0] }}"
    echo "Python Versions: ${{ steps.json2vars.outputs.versions_python }}"
```

#### With a Matrix Strategy

```yaml
test_matrix:
  needs: set_variables
  strategy:
    matrix:
      os: ${{ fromJson(needs.set_variables.outputs.os) }}
      python-version: ${{ fromJson(needs.set_variables.outputs.versions_python) }}

  runs-on: ${{ matrix.os }}

  steps:
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}
```

## Available Outputs

The action provides the following outputs:

| Output            | Description                |
|-------------------|----------------------------|
| `os`              | List of operating systems  |
| `versions_python` | List of Python versions    |
| `versions_ruby`   | List of Ruby versions      |
| `versions_nodejs` | List of Node.js versions   |
| `versions_go`     | List of Go versions        |
| `versions_rust`   | List of Rust versions      |
| `ghpages_branch`  | GitHub Pages branch name   |

!!! tip "How to refer to Output in subsequent steps or jobs"

    - When accessing list variables (like `os` or `versions_python`), always use the `fromJson()` function to parse the JSON string.
    - For shell scripts, use single quotes (`'`) around the JSON string to preserve its structure.
    - If you don't define a language in your JSON file, its corresponding output will be an empty array.
    - You can create language-specific JSON files (e.g., `python_project_matrix.json`) for different projects.

## Next Steps

- Learn about [JSON to Variables](features/json-to-variables.md) transformation
- Explore [Dynamic Version Updates](features/dynamic-update.md) to automatically keep your matrix up-to-date
- Check out [Version Caching](features/version-caching.md) to optimize your workflow performance
