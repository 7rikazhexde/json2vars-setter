# Rust Example for json2vars-setter

This is a Rust implementation example for parsing JSON configuration files in GitHub Actions matrix testing.

## Project Structure

```bash
.
├── Cargo.toml          # Project configuration and dependencies
├── src/
│   ├── lib.rs          # Library implementation
│   └── main.rs         # Binary entrypoint
└── tests/
    └── json_parser.rs  # Integration tests
```

## Setup

```bash
# Clone the repository
git clone <repository-url>
cd json2vars-setter/examples/rust

# Rust toolchain will be automatically installed based on rust-toolchain.toml
# Build the project
cargo build
```

## Usage

Clone the repository

```bash
git clone https://github.com/7rikazhexde/json2vars-setter.git
cd json2vars-setter/examples/rust
```

Run the JSON parser

```bash
cargo run
```

Run tests

```bash
cargo test

# Run tests with output
cargo test -- --nocapture
```

## Implementation Details

### src/lib.rs

Contains the core functionality

- `MatrixConfig` struct: Represents the JSON structure
- `parse_config`: Function to parse JSON configuration file
  - Parameters:
    - `file_path`: Path to the JSON file
    - `silent`: Boolean to suppress error messages

### src/main.rs

Command-line interface to parse and display JSON configuration.

## JSON Configuration Format

Please check [Releases](https://github.com/rust-lang/rust/releases) and create `.github/workflows/rust_project_matrix.json`

```json
{
    "os": [
        "ubuntu-latest",
        "windows-latest",
        "macos-latest"
    ],
    "versions": {
        "rust": [
            "1.79.0",
            "1.80.0",
            "1.81.0",
            "1.82.0",
            "1.83.0",
            "1.84.0",
            "1.84.1",
            "stable"
        ]
    },
    "ghpages_branch": "ghgapes"
}
```
