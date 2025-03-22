# JSON to Variables Setter

[![GitHub Marketplace](https://img.shields.io/badge/Marketplace-JSON%20to%20Variables%20Setter-green?colorA=24292e&colorB=3fb950&logo=github)](https://github.com/marketplace/actions/json-to-variables-setter)
[![DOCS](https://img.shields.io/badge/Docs-Click%20Here-blue?colorA=24292e&colorB=0366d6&logo=github)](https://7rikazhexde.github.io/json2vars-setter/)

## Overview

**JSON to Variables Setter (json2vars-setter)** is a GitHub Action that parses a JSON file and sets its values as output variables in GitHub Actions workflows. This action streamlines the management of matrix testing configurations and other workflow variables, making your CI/CD processes more maintainable and adaptable.

By centralizing your configuration in JSON files, you gain the ability to easily manage and update testing environments across multiple workflows, reducing duplication and maintenance overhead.

## Table of Contents

- [JSON to Variables Setter](#json-to-variables-setter)
  - [Overview](#overview)
  - [Table of Contents](#table-of-contents)
  - [Key Features](#key-features)
  - [Supported Matrix Components](#supported-matrix-components)
  - [Quick Start](#quick-start)
  - [Components](#components)
  - [Documentation](#documentation)
  - [License](#license)

## Key Features

- **JSON Parsing**: Convert JSON files into GitHub Actions output variables for use in your workflows
- **Dynamic Version Management**: Automatically update your testing matrix with latest language versions from official sources
- **Version Caching**: Cache version information to reduce API calls and improve workflow performance
- **Support for Multiple Languages**: Compatible with Python, Ruby, Node.js, Go, and Rust
- **Flexible Configuration**: Maintain a single source of truth for your matrix testing environments

## Supported Matrix Components

| Languages | Actions | Example Test Status |
|-------|-------|-------|
| ![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white) | [![setup-python](https://img.shields.io/badge/setup--python-3776AB?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/setup-python) | [![Python Test](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/7rikazhexde/26cb492ab0cfff920c516a622b2bfa44/raw/python-test-badge.json&cacheSeconds=0)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/python_test.yml) |
| ![Ruby](https://img.shields.io/badge/Ruby-CC342D?style=flat&logo=ruby&logoColor=white) | [![setup-ruby](https://img.shields.io/badge/setup--ruby-CC342D?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/setup-ruby-jruby-and-truffleruby) | [![Ruby Test](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/7rikazhexde/511ba5b5711e66c507292ba00cf0a219/raw/ruby-test-badge.json&cacheSeconds=0)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/ruby_test.yml) |
| ![Node.js](https://img.shields.io/badge/Node.js-339933?style=flat&logo=node.js&logoColor=white) | [![setup-node](https://img.shields.io/badge/setup--node-339933?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/setup-node-js-environment) | [![Node.js Test](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/7rikazhexde/11f46ff9ef47d3362dabe767255b0d9e/raw/nodejs-test-badge.json&cacheSeconds=0)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/nodejs_test.yml) |
| ![Go](https://img.shields.io/badge/Go-00ADD8?style=flat&logo=go&logoColor=white) | [![setup-go](https://img.shields.io/badge/setup--go-00ADD8?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/setup-go-environment) | [![Go Test](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/7rikazhexde/c334da204406866563668140885d170e/raw/go-test-badge.json&cacheSeconds=0)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/go_test.yml) |
| ![Rust](https://img.shields.io/badge/Rust-000000?style=flat&logo=rust&logoColor=white) | [![rust-toolchain](https://img.shields.io/badge/rust--toolchain-000000?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/rustup-toolchain-install) | [![Rust Test](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/7rikazhexde/5e160d06cfffd42a8f0e4ae6e8e8f025/raw/rust-test-badge.json&cacheSeconds=0)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/rust_test.yml) |

## Quick Start

```yaml
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

      - name: Set variables from JSON
        id: json2vars
        uses: 7rikazhexde/json2vars-setter@v1.0.1
        with:
          json-file: .github/json2vars-setter/sample/matrix.json
```

## Components

The action consists of three main components that work together to provide a powerful, flexible solution:

<img src="./mermaid/diagram.svg" alt="Mermaid Diagram" width="1200">

1. **JSON to Variables Parser**: Core component that parses JSON and converts it to GitHub Actions outputs
2. **Dynamic Matrix Updater**: Updates your matrix configuration with the latest or stable language versions
3. **Version Cache Manager**: Manages cached version information to optimize API usage

## Documentation

For detailed information, please check the [Documentation Site](https://7rikazhexde.github.io/json2vars-setter/).

The documentation includes:
- Getting Started guide
- Detailed feature explanations
- Usage examples
- Complete reference of all configuration options

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
