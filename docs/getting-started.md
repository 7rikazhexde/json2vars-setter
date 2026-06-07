# Getting Started

This guide will help you set up and use the JSON to Variables Setter action in your GitHub workflow.

## Prerequisites

- A GitHub repository where you want to implement the action
- Basic understanding of GitHub Actions workflows

## Installation

As this is a GitHub Action, there's no installation required. You simply reference the action in your workflow file.

## Try It Locally (No GitHub Needed)

Before wiring the action into a workflow, you can run the **exact same parsing logic** on your own machine and see precisely which outputs it would expose. The package ships a `json2vars` CLI. Inside a workflow the action writes its outputs to the file named by `$GITHUB_OUTPUT`; locally that is simply a file path you choose, so you can open it and read the result.

### Step 1: Create a small matrix file

Save this as `matrix.json`:

```json
{
  "os": ["ubuntu-latest", "macos-latest"],
  "versions": { "python": ["3.12", "3.13"] },
  "ghpages_branch": "gh-pages"
}
```

### Step 2: Run the parser

From a clone of this repository (uses [uv](https://docs.astral.sh/uv/)):

```bash
uv sync
GITHUB_OUTPUT=out.txt uv run json2vars parse matrix.json
```

Or without cloning — `uvx` fetches and runs the CLI straight from GitHub:

```bash
GITHUB_OUTPUT=out.txt uvx --from git+https://github.com/7rikazhexde/json2vars-setter json2vars parse matrix.json
```

### Step 3: Inspect the outputs

```bash
cat out.txt
```

```text
OS=["ubuntu-latest", "macos-latest"]
OS_0=ubuntu-latest
OS_1=macos-latest
VERSIONS_PYTHON=["3.12", "3.13"]
VERSIONS_PYTHON_0=3.12
VERSIONS_PYTHON_1=3.13
GHPAGES_BRANCH=gh-pages
```

Each line is one workflow output: the full JSON list (`VERSIONS_PYTHON`), each indexed element (`VERSIONS_PYTHON_0`, `VERSIONS_PYTHON_1`), and scalars such as `GHPAGES_BRANCH`. This is exactly what `${{ steps.json2vars.outputs.* }}` reads when the action runs in a workflow — so what you see locally is what you get in CI.

!!! tip "Explore the other commands"
    Run `json2vars usage` for a task-oriented guide. Beyond `parse`, the CLI also exposes `update-matrix` (rewrite the matrix file with the latest/stable versions fetched from upstream) and `cache-version` (maintain a version cache) — the same engines behind the action's [dynamic update](features/dynamic-update.md) and [version caching](features/version-caching.md) features. Those two reach out to GitHub APIs, so set `GITHUB_TOKEN` to avoid rate limits.

### Tab completion (bash & PowerShell)

The CLI ships shell completion for the command names (`parse`, `update-matrix`,
`cache-version`, `usage`). Install it once with the built-in command, which
auto-detects your shell:

```bash
json2vars --install-completion
```

Then restart the shell. Typing `json2vars <TAB>` now lists the subcommands.

To wire it up by hand (or inspect what gets installed), print the script with
`json2vars --show-completion` and add it to your shell profile:

=== "bash"

    ```bash
    # Append the generated script to your shell profile, then restart the shell
    json2vars --show-completion >> ~/.bashrc
    ```

=== "PowerShell"

    ```powershell
    # Append the generated script to your $PROFILE, then restart the shell
    json2vars --show-completion | Out-String | Add-Content $PROFILE
    ```

!!! note "Command names only"
    Completion covers the **subcommand names**. Per-command options
    (`--languages`, `--max-age`, `--cache-file`, …) are forwarded to each
    feature's own parser, so they do **not** tab-complete — run
    `json2vars <command> --help` (e.g. `json2vars cache-version --help`) to list them.

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
        uses: actions/checkout@v6.0.3

      - name: Set variables from JSON
        id: json2vars
        uses: 7rikazhexde/json2vars-setter@v1.9.1
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
      uses: actions/setup-python@v6.2.0
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
