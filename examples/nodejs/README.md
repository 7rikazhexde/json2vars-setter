# JSON Parser Node.js Example

This is a Node.js implementation example for parsing JSON configuration files in GitHub Actions matrix testing.

## Requirements

- Node.js >= 16.0.0

## Project Structure

```bash
.
├── package.json                # Node.js project definition and dependencies
├── package-lock.json           # Locked versions of dependencies
├── src/                        # Source code directory
│   ├── config/                 # Configuration related files
│   │   ├── index.js            # Configuration entry point
│   │   └── paths.js            # Path definitions and resolution
│   ├── utils/                  # Utility functions
│   │   └── jsonParser.js       # JSON parsing implementation
│   └── index.js                # Application entry point
└── tests/                      # Test files directory
    └── utils/                  # Tests for utility functions
        └── jsonParser.test.js  # Tests for JSON parser
```

## Setup

```bash
# Install dependencies
npm ci
```

## Usage

Run the application:

```bash
# Using npm script
npm start
```

Run tests:

```bash
npm test
```

## Implementation Details

### Configuration (`src/config/`)

#### paths.js

- Defines path resolution for project files
- Resolves the path to JSON configuration file relative to project root

#### index.js

- Exports configuration modules
- Centralizes configuration management

### Utilities (`src/utils/`)

#### jsonParser.js

- Main JSON parsing functionality
- `parseConfigJson(filePath, silent)`: Parse JSON configuration file
  - `filePath`: Path to JSON file (defaults to matrix configuration)
  - `silent`: Boolean to suppress error messages (defaults to false)
- Returns parsed JSON object or null on error

### Testing (`tests/`)

#### jsonParser.test.js

- Test suite using Jest framework
- Validates JSON parsing functionality
- Tests error handling and edge cases

## JSON Configuration

The parser expects a JSON file with the following structure:

```json
{
  "os": [
    "ubuntu-latest",
    "windows-latest",
    "macos-latest"
  ],
  "versions": {
    "nodejs": [
      "16",
      "18",
      "20",
      "22"
    ]
  },
  "ghpages_branch": "ghgapes"
}
```

The default path for this configuration is `.github/workflows/nodejs_project_matrix.json` relative to the project root.

## Development

This project uses

- Jest for testing
- Node.js native `fs` module for file operations
- Node.js native `path` module for path resolution

Development workflow

1. Make changes to source code
2. Update tests if necessary
3. Run `npm test` to verify changes
4. Update documentation if needed

## Dependencies

Main dependencies:
- jest: Testing framework

Note: The project uses npm workspaces and is part of a larger monorepo demonstrating matrix configuration parsing in various languages.
