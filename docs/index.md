# JSON to Variables Setter

[![GitHub Marketplace](https://img.shields.io/badge/Marketplace-JSON%20to%20Variables%20Setter-green?colorA=24292e&colorB=3fb950&logo=github)](https://github.com/marketplace/actions/json-to-variables-setter)

## Overview

**JSON to Variables Setter (json2vars-setter)** is a GitHub Action that parses a JSON file and sets its values as output variables in GitHub Actions workflows. This action streamlines the management of matrix testing configurations and other workflow variables, making your CI/CD processes more maintainable and adaptable.

By centralizing your configuration in JSON files, you gain the ability to easily manage and update testing environments across multiple workflows, reducing duplication and maintenance overhead.

## Key Features

- **JSON Parsing**: Convert JSON files into GitHub Actions output variables for use in your workflows
- **Dynamic Version Management**: Automatically update your testing matrix with latest language versions from official sources
- **Version Caching**: Cache version information to reduce API calls and improve workflow performance
- **Support for Multiple Languages**: Compatible with Python, Ruby, Node.js, Go, Rust, PHP, .NET (C#), Java, Deno, Bun, Zig, Elixir, Dart, and Swift
- **Flexible Configuration**: Maintain a single source of truth for your matrix testing environments

## Supported Matrix Components

| Languages | Actions | Example Test Status |
|-------|-------|-------|
| ![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white) | [![setup-python](https://img.shields.io/badge/setup--python-3776AB?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/setup-python) | [![Python Test](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/7rikazhexde/26cb492ab0cfff920c516a622b2bfa44/raw/python-test-badge.json&cacheSeconds=0)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/python_test.yml) |
| ![Ruby](https://img.shields.io/badge/Ruby-CC342D?style=flat&logo=ruby&logoColor=white) | [![setup-ruby](https://img.shields.io/badge/setup--ruby-CC342D?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/setup-ruby-jruby-and-truffleruby) | [![Ruby Test](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/7rikazhexde/511ba5b5711e66c507292ba00cf0a219/raw/ruby-test-badge.json&cacheSeconds=0)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/ruby_test.yml) |
| ![Node.js](https://img.shields.io/badge/Node.js-339933?style=flat&logo=node.js&logoColor=white) | [![setup-node](https://img.shields.io/badge/setup--node-339933?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/setup-node-js-environment) | [![Node.js Test](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/7rikazhexde/11f46ff9ef47d3362dabe767255b0d9e/raw/nodejs-test-badge.json&cacheSeconds=0)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/nodejs_test.yml) |
| ![Go](https://img.shields.io/badge/Go-00ADD8?style=flat&logo=go&logoColor=white) | [![setup-go](https://img.shields.io/badge/setup--go-00ADD8?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/setup-go-environment) | [![Go Test](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/7rikazhexde/c334da204406866563668140885d170e/raw/go-test-badge.json&cacheSeconds=0)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/go_test.yml) |
| ![Rust](https://img.shields.io/badge/Rust-000000?style=flat&logo=rust&logoColor=white) | [![rust-toolchain](https://img.shields.io/badge/rust--toolchain-000000?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/rustup-toolchain-install) | [![Rust Test](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/7rikazhexde/5e160d06cfffd42a8f0e4ae6e8e8f025/raw/rust-test-badge.json&cacheSeconds=0)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/rust_test.yml) |
| ![PHP](https://img.shields.io/badge/PHP-777BB4?style=flat&logo=php&logoColor=white) | [![setup-php](https://img.shields.io/badge/setup--php-777BB4?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/setup-php-action) | [![PHP Test](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/7rikazhexde/a9bc428c9f5a2f998bd7307038e557e1/raw/php-test-badge.json&cacheSeconds=0)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/php_test.yml) |
| ![.NET](https://img.shields.io/badge/.NET-512BD4?style=flat&logo=dotnet&logoColor=white) | [![setup-dotnet](https://img.shields.io/badge/setup--dotnet-512BD4?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/setup-net-core-sdk) | [![.NET Test](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/7rikazhexde/33c8a05d3ed6c038877d847ffc12b2f9/raw/dotnet-test-badge.json&cacheSeconds=0)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/dotnet_test.yml) |
| ![Java](https://img.shields.io/badge/Java-007396?style=flat&logo=openjdk&logoColor=white) | [![setup-java](https://img.shields.io/badge/setup--java-007396?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/setup-java-jdk) | [![Java Test](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/7rikazhexde/813e5201a834d06253014b66ee8fd154/raw/java-test-badge.json&cacheSeconds=0)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/java_test.yml) |
| ![Deno](https://img.shields.io/badge/Deno-000000?style=flat&logo=deno&logoColor=white) | [![setup-deno](https://img.shields.io/badge/setup--deno-000000?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/setup-deno) | [![Deno Test](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/7rikazhexde/5a34d5cdfb2b13ed4ab1939009b6f5b1/raw/deno-test-badge.json&cacheSeconds=0)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/deno_test.yml) |
| ![Bun](https://img.shields.io/badge/Bun-000000?style=flat&logo=bun&logoColor=white) | [![setup-bun](https://img.shields.io/badge/setup--bun-000000?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/setup-bun) | [![Bun Test](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/7rikazhexde/431a19225ef80b473e7eee8e060b7516/raw/bun-test-badge.json&cacheSeconds=0)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/bun_test.yml) |
| ![Zig](https://img.shields.io/badge/Zig-F7A41D?style=flat&logo=zig&logoColor=white) | [![setup-zig](https://img.shields.io/badge/setup--zig-F7A41D?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/setup-zig-compiler) | [![Zig Test](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/7rikazhexde/35f4914a9b707f6570a2c7b508e1f675/raw/zig-test-badge.json&cacheSeconds=0)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/zig_test.yml) |
| ![Elixir](https://img.shields.io/badge/Elixir-4B275F?style=flat&logo=elixir&logoColor=white) | [![setup-beam](https://img.shields.io/badge/setup--beam-4B275F?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/setup-beam) | [![Elixir Test](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/7rikazhexde/b93c2abf130e91304761df9da4bb5533/raw/elixir-test-badge.json&cacheSeconds=0)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/elixir_test.yml) |
| ![Dart](https://img.shields.io/badge/Dart-0175C2?style=flat&logo=dart&logoColor=white) | [![setup-dart](https://img.shields.io/badge/setup--dart-0175C2?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/setup-dart-sdk) | [![Dart Test](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/7rikazhexde/838b360075fcd8c54f8ccdb2a8ff2e88/raw/dart-test-badge.json&cacheSeconds=0)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/dart_test.yml) |
| ![Swift](https://img.shields.io/badge/Swift-F05138?style=flat&logo=swift&logoColor=white) | [![setup-swift](https://img.shields.io/badge/setup--swift-F05138?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/setup-swift) | [![Swift Test](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/7rikazhexde/c20279820e1c89d7864bf440e8c7cfa2/raw/swift-test-badge.json&cacheSeconds=0)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/swift_test.yml) |
| ![Julia](https://img.shields.io/badge/Julia-9558B2?style=flat&logo=julia&logoColor=white) | [![setup-julia](https://img.shields.io/badge/setup--julia-9558B2?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/setup-julia-environment) | [![Julia Test](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/7rikazhexde/2d784d1513f73b0cd94f974742f33340/raw/julia-test-badge.json&cacheSeconds=0)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/julia_test.yml) |
| ![Crystal](https://img.shields.io/badge/Crystal-000000?style=flat&logo=crystal&logoColor=white) | [![install-crystal](https://img.shields.io/badge/install--crystal-000000?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/install-crystal) | [![Crystal Test](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/7rikazhexde/09c90cf4e8e97865f6213085c82716e4/raw/crystal-test-badge.json&cacheSeconds=0)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/crystal_test.yml) |
| ![Haskell](https://img.shields.io/badge/Haskell-5e5086?style=flat&logo=haskell&logoColor=white) | [![setup-haskell](https://img.shields.io/badge/setup--haskell-5e5086?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/setup-haskell) | [![Haskell Test](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/7rikazhexde/ac694a2ecdc91ee32dda6afa49863aa4/raw/haskell-test-badge.json&cacheSeconds=0)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/haskell_test.yml) |
| ![OCaml](https://img.shields.io/badge/OCaml-EC6813?style=flat&logo=ocaml&logoColor=white) | [![setup-ocaml](https://img.shields.io/badge/setup--ocaml-EC6813?style=flat&logo=github-actions&logoColor=white)](https://github.com/marketplace/actions/set-up-ocaml) | [![OCaml Test](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/7rikazhexde/ac8d039239f77264250f852a38143043/raw/ocaml-test-badge.json&cacheSeconds=0)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/ocaml_test.yml) |

## Sample Workflows

Beyond the per-language tests above, these **runnable use-case samples** live in the repository and execute on real GitHub Actions. The green badge is proof you can reproduce the result, then copy the files into your own project — no local setup required to gain confidence.

| Use case | Status | What it demonstrates | Files |
|----------|--------|----------------------|-------|
| Single source of truth | [![Sample: Single Source of Truth](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/7rikazhexde/43c16c21c735a80b673a65e1bb0d9619/raw/sample-single-source-badge.json&cacheSeconds=0)](https://github.com/7rikazhexde/json2vars-setter/actions/workflows/sample_single_source.yml) | One JSON parsed once, then consumed by an independent `test` matrix **and** a separate `lint` job — define versions in one place, use them everywhere | [workflow](https://github.com/7rikazhexde/json2vars-setter/blob/main/.github/workflows/sample_single_source.yml) · [example](https://github.com/7rikazhexde/json2vars-setter/tree/main/examples/showcase) |

## Quick Start

!!! info "See [Basic Usage Examples](https://7rikazhexde.github.io/json2vars-setter/examples/basic/) for details."

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

```mermaid
graph TD
    subgraph "JSON to Variables Setter"
        A[JSON to Variables Parser ] -->|Reads| B[Matrix JSON File]
        A -->|Sets| C[GitHub Actions Outputs]

        D[Dynamic Matrix Updater] -->|Updates| B
        D -->|Fetches from| E[GitHub API]

        F[Version Cache Manager] -->|Caches| G[Version Information]
        F -->|Fetches from| E
        F -->|Generates| B
    end

    C -->|Used by| I[GitHub Workflows]

    classDef core fill:#43a047,stroke:#2e7d32,stroke-width:2px,color:#fff
    classDef file fill:#ffca28,stroke:#fb8c00,stroke-width:1px,color:#333333
    classDef output fill:#42a5f5,stroke:#1976d2,stroke-width:1px
    classDef external fill:#78909c,stroke:#546e7a,stroke-width:1px
    classDef api fill:#e91e63,stroke:#c2185b,stroke-width:1px,color:#fff

    class A,D,F core
    class B,G file
    class C output
    class I external
    class E api
```

1. **JSON to Variables Parser** (`github_output.py`): Core component that parses JSON and converts it to GitHub Actions outputs. Makes your configuration data accessible throughout your workflow.

2. **Dynamic Matrix Updater** (`matrix_update.py`): Updates your matrix configuration with the latest or stable language versions. Ensures your CI/CD tests run against current language versions without manual updates.

3. **Version Cache Manager** (`version_cache.py`): Manages cached version information to optimize API usage. Reduces external API calls by intelligently caching data, improving workflow performance and reliability.

## Learn More

- [Getting Started](getting-started.md) - Basic setup and configuration
- [Features](features/index.md) - Detailed explanation of all features
- [Usage Examples](examples/basic.md) - Common usage patterns and examples
- [Command Options](reference/options.md) - Complete reference of all available options
