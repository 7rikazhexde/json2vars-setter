# Contributing Guide

Thank you for your interest in contributing to my JSON to Variables Setter action! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Contributing Guide](#contributing-guide)
  - [Table of Contents](#table-of-contents)
  - [Code of Conduct](#code-of-conduct)
  - [Getting Started](#getting-started)
    - [Development Environment Setup](#development-environment-setup)
    - [Project Structure](#project-structure)
  - [Development Workflow](#development-workflow)
    - [Creating Issues](#creating-issues)
    - [Making Changes](#making-changes)
    - [Testing Changes](#testing-changes)
    - [Pull Requests](#pull-requests)
  - [Coding Guidelines](#coding-guidelines)
  - [Documentation](#documentation)
  - [Core Components Development](#core-components-development)
    - [JSON to GitHub Output Parser (`json_to_github_output.py`)](#json-to-github-output-parser-json_to_github_outputpy)
    - [Dynamic Matrix Updater (`update_matrix_dynamic.py`)](#dynamic-matrix-updater-update_matrix_dynamicpy)
    - [Version Cache Manager (`cache_version_info.py`)](#version-cache-manager-cache_version_infopy)
  - [Release Process](#release-process)
  - [Feedback](#feedback)

## Code of Conduct

Please be respectful to all contributors and users. I aim to foster an inclusive and welcoming community.

## Getting Started

### Development Environment Setup

1. **Clone the repository**:

    ```bash
    git clone https://github.com/7rikazhexde/json2vars-setter.git
    cd json2vars-setter
    ```

2. **Set up a virtual environment**:

    !!! note "When using the `poetry install` command, venv is created under the project, so there is no need to manually create a virtual environment (venv)."

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. **Install dependencies**:

    Option 1: Using Poetry (recommended)

    ```bash
    # Install Poetry if not already installed
    pip install poetry

    # Install all dependencies
    poetry install
    ```

    Option 2: Using pip with requirements files

    ```bash
    # Download requirements-dev.txt from my official Gist
    curl -O https://gist.githubusercontent.com/7rikazhexde/ee63b33bcb6bb21ac872c5ed41dbf4a6/raw/requirements-dev.txt

    # Install development dependencies
    pip install -r requirements-dev.txt
    ```

4. **Set up pre-commit hooks**:

    ```bash
    pre-commit install
    ```

### Project Structure

My project is organized as follows:

```text
json2vars-setter/
├── .github/           # GitHub specific files (workflows, templates)
├── json2vars_setter/  # Core Python module
│   ├── __init__.py
│   ├── json_to_github_output.py  # JSON parser component
│   ├── update_matrix_dynamic.py  # Dynamic update component
│   ├── cache_version_info.py     # Version caching component
│   └── version/       # Version fetching modules
├── tests/             # Test files
├── docs/              # Documentation files
├── action.yml         # Action definition
└── README.md          # Project documentation
```

## Development Workflow

### Creating Issues

Before starting any work, please check existing issues or create a new one to discuss the changes you'd like to make.

- For bugs, include steps to reproduce, expected behavior, and actual behavior
- For features, explain the use case and proposed implementation

### Making Changes

1. **Create a branch**:

    ```bash
    git checkout -b feature-your-feature-name
    ```

    Branch naming conventions:  
    Branches must follow the format: `<type>-<short-description>`.  
    Use the following prefixes based on the purpose of the branch:

    - `feature-<description>`: For implementing new features (e.g., feature-newlang-supprt).
    - `bugfix-<description>`: For fixing bugs (e.g., bugfix-fetch-python-version-error).
    - `docs-<description>`: For documentation updates (e.g., docs-update-readme).
    - `refactor-<description>`: For code refactoring without functional changes (e.g., refactor-cleanup-utils).

2. **Make your changes**:

    - Follow my [coding guidelines](#coding-guidelines)
    - Keep changes focused on a single issue/feature

3. **Commit your changes** using [gitmoji](https://gitmoji.dev/):

    ```bash
    git commit -m "✨ Add new feature"
    git commit -m "🐛 Fix bug in function X"
    git commit -m "📝 Update documentation"
    ```

    Recommended gitmoji conventions:

    - ✨ (`:sparkles:`) - New feature
    - 🐛 (`:bug:`) - Bug fix
    - 📝 (`:memo:`) - Documentation updates
    - ♻️ (`:recycle:`) - Code refactoring
    - 🚀 (`:rocket:`) - Performance improvements
    - 🎨 (`:art:`) - Code style/structure improvements
    - 🧪 (`:test_tube:`) - Add or update tests

    Write clear commit messages that explain what changes were made and why.

### Testing Changes

!!! note "About the Testing Policy"

      - Test code should be created using pytest
      - Coverage must be at least 95% (ideally 100%)

1. **Run unit tests** (required):

    ```bash
    # Run basic tests
    pytest
    # Or use poetry
    poetry run pytest
    ```

    ```bash
    # Run verbose coverage tests and create report
    poetry run task testcoverageverbose
    ```

2. **Run linters** (required):

    ```bash
    # Run all pre-commit hooks
    pre-commit run --all-files
    # Or use poetry to run pre-commit
    poetry run pre-commit run --all-files

    # Run specific linters
    ruff check json2vars_setter
    ruff format json2vars_setter
    mypy json2vars_setter
    ```

3. **Manual testing**:

    Test the action by using it in a test workflow with various configurations.

### Pull Requests

1. **Push your branch**:

    ```bash
    git push origin feature/your-feature-name
    ```

2. **Create a pull request**:

    - Go to the GitHub repository
    - Click "Pull requests" > "New pull request"
    - Select your branch
    - Fill in the PR template

3. **Code review**:

    - Respond to feedback and make necessary changes
    - Keep the PR focused on a single issue/feature

## Coding Guidelines

**Python code**:

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use type hints as defined in my mypy configuration
- Document functions and classes with docstrings
      - Keep functions focused on a single responsibility

**Linting and Formatting** (required)

- My project uses pre-commit hooks for consistent code quality
- All code must pass pre-commit checks before submitting PRs
- Configuration is defined in `.pre-commit-config.yaml` and `pyproject.toml`
- Key linting tools:
      - [Ruff](https://github.com/charliermarsh/ruff) for linting and formatting
      - [mypy](https://mypy.readthedocs.io/) for static type checking
      - [markdownlint](https://github.com/DavidAnson/markdownlint) for Markdown files
      - [actionlint](https://github.com/rhysd/actionlint) for GitHub Actions workflows
      - [shellcheck](https://github.com/shellcheck-py/shellcheck-py) for shell script checking
- You can run all linters at once using: `poetry run pre-commit run --all-files`

**Testing** (required)

- Write unit tests for all new functionality
- Test edge cases and error conditions
- Maintain or improve test coverage

## Documentation

- Update documentation when making changes that affect user-facing functionality
- Follow my existing documentation style
- Include examples for new features
- Update the README.md if necessary

For MkDocs documentation:

1. **Test documentation locally**:

    ```bash
    mkdocs serve
    ```

2. **Build documentation**:

    ```bash
    mkdocs build
    ```

## Core Components Development

When working on my core components, consider the following guidelines:

### JSON to GitHub Output Parser (`json_to_github_output.py`)

- Maintain backward compatibility with existing JSON structures
- Ensure proper error handling for malformed JSON
- Optimize for performance with large JSON files

### Dynamic Matrix Updater (`update_matrix_dynamic.py`)

- Keep the code DRY (Don't Repeat Yourself) when implementing different language fetchers
- Handle API rate limits gracefully
- Implement proper error handling and logging

### Version Cache Manager (`cache_version_info.py`)

- Ensure thread-safety for file operations
- Optimize disk I/O and API calls
- Maintain backward compatibility with existing cache formats

## Release Process

Version updates and releases are managed through an automated workflow that is only available to repository administrators (currently only me). The process involves:

1. **Version bumping**

     - Handled by the automated workflow that updates the version in relevant files

2. **Creating a release**

     - The workflow automatically creates a tag and a GitHub release
     - Tags follow the format `json2vars-setter-vX.Y.Z` (e.g., `json2vars-setter-v0.2.5`)

3. **Documentation deployment**

     - Occurs automatically when changes are merged/pushed to the main branch
     - Handled by a dedicated deployment workflow

## Feedback

If you have any questions or need help, feel free to:

- Open an issue for discussion
- Contact me directly via X (formerly Twitter) - DMs preferred

Thank you for contributing to my json2vars-setter!
