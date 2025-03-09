# Go Example for json2vars-setter

This is a Go implementation example for parsing JSON configuration files in GitHub Actions matrix testing.

## Requirements

- Go 1.20 or higher

## Project Structure

```bash
.
├── go.mod                # Go module definition
├── gomvm/                # Go version manager (submodule)
├── jsonparser/           # Package for JSON parsing
│   ├── parser.go         # Main parser implementation
│   └── parser_test.go    # Parser tests
├── main.go               # Main application
└── main_test.go          # Main package tests
```

## Setup

```bash
# Clone the repository with submodules
git clone https://github.com/7rikazhexde/json2vars-setter.git
cd json2vars-setter/examples/go

# Or if you already cloned the repository
git submodule update --init --recursive

# Install Go and switch to the installed version
cd gomvm/scripts/ubuntu
source ./switch_go_version.sh 1.23.2

# Download dependencies
# If external packages are added in the future, uncomment and run
# cd ../../../
# go mod download
```

## Usage

Run the application

```bash
go run main.go
```

Run tests

```bash
# Run all tests
go test ./...

# Run tests with verbose output
go test -v ./...

# Run tests with coverage
go test -cover ./...
```

## Switching Go Versions

Please check [the govmv project](https://github.com/7rikazhexde/go-multi-version-manager) for usage details

```bash
cd gomvm/scripts/ubuntu

# List available versions
./list_go_versions.sh

# Install a new version
./install_go_with_command.sh <version>

# Switch to a different version
source ./switch_go_version.sh <version>
```

## Package Documentation

### jsonparser

The `jsonparser` package provides functionality to parse JSON configuration files for GitHub Actions matrix testing.

#### Main functions

- `ParseConfig(filePath string, silent bool) (*MatrixConfig, error)`: Parses a JSON configuration file and returns a MatrixConfig structure.

## JSON Configuration Format

Please check [All Releases](https://go.dev/dl/) and create `.github/json2vars-setter/go_project_matrix.json`

```json
{
    "os": [
        "ubuntu-latest",
        "windows-latest",
        "macos-latest"
    ],
    "versions": {
        "go": [
            "1.23.0",
            "1.23.1",
            "1.23.2",
            "1.23.3",
            "1.23.4",
            "1.23.5",
            "1.23.6",
            "1.24.0"
        ]
    },
    "ghpages_branch": "ghgapes"
}
```
