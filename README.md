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
  - [Sample Workflows](#sample-workflows)
  - [Quick Start](#quick-start)
  - [Components](#components)
  - [Documentation](#documentation)
  - [License](#license)

## Key Features

- **JSON Parsing**: Convert JSON files into GitHub Actions output variables for use in your workflows
- **Dynamic Version Management**: Automatically update your testing matrix with latest language versions from official sources
- **Version Caching**: Cache version information to reduce API calls and improve workflow performance
- **Support for Multiple Languages**: Compatible with Python, Ruby, Node.js, Go, Rust, PHP, .NET (C#), Java, Deno, Bun, Zig, Elixir, Dart, Swift, Julia, Crystal, Haskell, and OCaml
- **Flexible Configuration**: Maintain a single source of truth for your matrix testing environments

## Supported Matrix Components

| Languages | Actions | Example Test Status |
|-------|-------|-------|
| ![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white) | [![setup-python](https://img.shields.io/badge/setup--python-3776AB?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/setup-python) | [![Python Test](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/python_test.yml/badge.svg)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/python_test.yml) |
| ![Ruby](https://img.shields.io/badge/Ruby-CC342D?style=flat&logo=ruby&logoColor=white) | [![setup-ruby](https://img.shields.io/badge/setup--ruby-CC342D?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/setup-ruby-jruby-and-truffleruby) | [![Ruby Test](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/ruby_test.yml/badge.svg)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/ruby_test.yml) |
| ![Node.js](https://img.shields.io/badge/Node.js-339933?style=flat&logo=node.js&logoColor=white) | [![setup-node](https://img.shields.io/badge/setup--node-339933?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/setup-node-js-environment) | [![Node.js Test](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/nodejs_test.yml/badge.svg)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/nodejs_test.yml) |
| ![Go](https://img.shields.io/badge/Go-00ADD8?style=flat&logo=go&logoColor=white) | [![setup-go](https://img.shields.io/badge/setup--go-00ADD8?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/setup-go-environment) | [![Go Test](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/go_test.yml/badge.svg)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/go_test.yml) |
| ![Rust](https://img.shields.io/badge/Rust-000000?style=flat&logo=rust&logoColor=white) | [![rust-toolchain](https://img.shields.io/badge/rust--toolchain-000000?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/rustup-toolchain-install) | [![Rust Test](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/rust_test.yml/badge.svg)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/rust_test.yml) |
| ![PHP](https://img.shields.io/badge/PHP-777BB4?style=flat&logo=php&logoColor=white) | [![setup-php](https://img.shields.io/badge/setup--php-777BB4?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/setup-php-action) | [![PHP Test](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/php_test.yml/badge.svg)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/php_test.yml) |
| ![.NET](https://img.shields.io/badge/.NET-512BD4?style=flat&logo=dotnet&logoColor=white) | [![setup-dotnet](https://img.shields.io/badge/setup--dotnet-512BD4?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/setup-net-core-sdk) | [![.NET Test](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/dotnet_test.yml/badge.svg)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/dotnet_test.yml) |
| ![Java](https://img.shields.io/badge/Java-007396?style=flat&logo=openjdk&logoColor=white) | [![setup-java](https://img.shields.io/badge/setup--java-007396?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/setup-java-jdk) | [![Java Test](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/java_test.yml/badge.svg)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/java_test.yml) |
| ![Deno](https://img.shields.io/badge/Deno-000000?style=flat&logo=deno&logoColor=white) | [![setup-deno](https://img.shields.io/badge/setup--deno-000000?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/setup-deno) | [![Deno Test](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/deno_test.yml/badge.svg)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/deno_test.yml) |
| ![Bun](https://img.shields.io/badge/Bun-000000?style=flat&logo=bun&logoColor=white) | [![setup-bun](https://img.shields.io/badge/setup--bun-000000?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/setup-bun) | [![Bun Test](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/bun_test.yml/badge.svg)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/bun_test.yml) |
| ![Zig](https://img.shields.io/badge/Zig-F7A41D?style=flat&logo=zig&logoColor=white) | [![setup-zig](https://img.shields.io/badge/setup--zig-F7A41D?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/setup-zig-compiler) | [![Zig Test](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/zig_test.yml/badge.svg)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/zig_test.yml) |
| ![Elixir](https://img.shields.io/badge/Elixir-4B275F?style=flat&logo=elixir&logoColor=white) | [![setup-beam](https://img.shields.io/badge/setup--beam-4B275F?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/setup-beam) | [![Elixir Test](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/elixir_test.yml/badge.svg)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/elixir_test.yml) |
| ![Dart](https://img.shields.io/badge/Dart-0175C2?style=flat&logo=dart&logoColor=white) | [![setup-dart](https://img.shields.io/badge/setup--dart-0175C2?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/setup-dart-sdk) | [![Dart Test](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/dart_test.yml/badge.svg)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/dart_test.yml) |
| ![Swift](https://img.shields.io/badge/Swift-F05138?style=flat&logo=swift&logoColor=white) | [![setup-swift](https://img.shields.io/badge/setup--swift-F05138?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/setup-swift) | [![Swift Test](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/swift_test.yml/badge.svg)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/swift_test.yml) |
| ![Julia](https://img.shields.io/badge/Julia-9558B2?style=flat&logo=julia&logoColor=white) | [![setup-julia](https://img.shields.io/badge/setup--julia-9558B2?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/setup-julia-environment) | [![Julia Test](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/julia_test.yml/badge.svg)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/julia_test.yml) |
| ![Crystal](https://img.shields.io/badge/Crystal-000000?style=flat&logo=crystal&logoColor=white) | [![install-crystal](https://img.shields.io/badge/install--crystal-000000?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/install-crystal) | [![Crystal Test](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/crystal_test.yml/badge.svg)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/crystal_test.yml) |
| ![Haskell](https://img.shields.io/badge/Haskell-5e5086?style=flat&logo=haskell&logoColor=white) | [![setup-haskell](https://img.shields.io/badge/setup--haskell-5e5086?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/setup-haskell) | [![Haskell Test](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/haskell_test.yml/badge.svg)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/haskell_test.yml) |
| ![OCaml](https://img.shields.io/badge/OCaml-EC6813?style=flat&logo=ocaml&logoColor=white) | [![setup-ocaml](https://img.shields.io/badge/setup--ocaml-EC6813?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/set-up-ocaml) | [![OCaml Test](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/ocaml_test.yml/badge.svg)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/ocaml_test.yml) |

## Sample Workflows

Beyond the per-language tests above, these **runnable use-case samples** live in this repository and execute on real GitHub Actions. The green badge is proof you can reproduce the result, then copy the files into your own project — no local setup required to gain confidence.

| Use case | Status | What it demonstrates | Files |
|----------|--------|----------------------|-------|
| [Single source of truth](https://7rikazhexde.github.io/json2vars-setter/features/json-to-variables/) | [![Sample: Single Source of Truth](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/sample_single_source.yml/badge.svg)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/sample_single_source.yml) | One JSON parsed once, then consumed by an independent `test` matrix **and** a separate `lint` job — define versions in one place, use them everywhere | [![workflow](https://img.shields.io/badge/workflow-2088FF?logo=githubactions&logoColor=white)](.github/workflows/sample_single_source.yml) [![example](https://img.shields.io/badge/example-24292f?logo=github&logoColor=white)](examples/showcase) |
| [Monorepo](https://7rikazhexde.github.io/json2vars-setter/examples/ci-cd/#monorepo-project-configuration) | [![Sample: Monorepo](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/sample_monorepo.yml/badge.svg)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/sample_monorepo.yml) | Several projects in one repo, each with its **own** matrix JSON (Python backend + Node.js frontend) and an independent test matrix | [![workflow](https://img.shields.io/badge/workflow-2088FF?logo=githubactions&logoColor=white)](.github/workflows/sample_monorepo.yml) [![example](https://img.shields.io/badge/example-24292f?logo=github&logoColor=white)](examples/showcase/monorepo) |
| [Template from cache](https://7rikazhexde.github.io/json2vars-setter/features/version-caching/) | [![Sample: Template (cache)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/sample_template.yml/badge.svg)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/sample_template.yml) | Generate a matrix from an existing version cache with **no API calls** (`template-only`), trimmed via `output-count` | [![workflow](https://img.shields.io/badge/workflow-2088FF?logo=githubactions&logoColor=white)](.github/workflows/sample_template.yml) [![example](https://img.shields.io/badge/example-24292f?logo=github&logoColor=white)](examples/showcase/template) |
| [Version cache](https://7rikazhexde.github.io/json2vars-setter/features/version-caching/) | [![Sample: Version Cache](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/sample_version_cache.yml/badge.svg)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/sample_version_cache.yml) | Drive a multi-version matrix from a committed cache (`use-cache`) — **zero API calls** on a cache hit, auto-refresh when `cache-max-age` is exceeded | [![workflow](https://img.shields.io/badge/workflow-2088FF?logo=githubactions&logoColor=white)](.github/workflows/sample_version_cache.yml) [![example](https://img.shields.io/badge/example-24292f?logo=github&logoColor=white)](examples/showcase/version-cache) |
| [Dynamic update (scheduled)](https://7rikazhexde.github.io/json2vars-setter/features/dynamic-update/) | [![Sample: Dynamic Update](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/sample_dynamic_update.yml/badge.svg)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/sample_dynamic_update.yml) | Weekly scheduled maintenance: fetch the latest language versions from the live API (`update-matrix`) and rebuild the matrix — side-effect-free (no commit) | [![workflow](https://img.shields.io/badge/workflow-2088FF?logo=githubactions&logoColor=white)](.github/workflows/sample_dynamic_update.yml) [![example](https://img.shields.io/badge/example-24292f?logo=github&logoColor=white)](examples/showcase/dynamic-update) |
| [Conditional matrix](https://7rikazhexde.github.io/json2vars-setter/examples/ci-cd/#environment-specific-configurations) | [![Sample: Conditional Matrix](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/sample_conditional_matrix.yml/badge.svg)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/sample_conditional_matrix.yml) | Pick the matrix by event — a light, fast matrix on pull requests and the full cross-OS matrix on schedule / dispatch | [![workflow](https://img.shields.io/badge/workflow-2088FF?logo=githubactions&logoColor=white)](.github/workflows/sample_conditional_matrix.yml) [![example](https://img.shields.io/badge/example-24292f?logo=github&logoColor=white)](examples/showcase/conditional) |
| [Reusable workflow](https://7rikazhexde.github.io/json2vars-setter/examples/ci-cd/) | [![Sample: Reusable Workflow](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/sample_reusable_workflow.yml/badge.svg)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/sample_reusable_workflow.yml) | Define the matrix once in a `workflow_call` library and consume its outputs from a caller — maintain the version set in one place | [![workflow](https://img.shields.io/badge/workflow-2088FF?logo=githubactions&logoColor=white)](.github/workflows/sample_reusable_workflow.yml) [![example](https://img.shields.io/badge/example-24292f?logo=github&logoColor=white)](examples/showcase/reusable) |

## Quick Start

> [!NOTE]
> See [Basic Usage Examples](https://7rikazhexde.github.io/json2vars-setter/examples/basic/) for details.

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
        uses: actions/checkout@v6.0.3

      - name: Set variables from JSON
        id: json2vars
        uses: 7rikazhexde/json2vars-setter@v1.9.1
        with:
          json-file: .github/json2vars-setter/sample/matrix.json

  run_tests:
    needs: set_variables
    strategy:
      matrix:
        os: ${{ fromJson(needs.set_variables.outputs.os) }}
        python-version: ${{ fromJson(needs.set_variables.outputs.versions_python) }}
    runs-on: ${{ matrix.os }}
    steps:
      - name: Checkout repository
        uses: actions/checkout@v6.0.3
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v6.2.0
        with:
          python-version: ${{ matrix.python-version }}
      # Other steps
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
