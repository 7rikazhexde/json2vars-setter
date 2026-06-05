# Bun Example for json2vars-setter

This is a Bun implementation example for parsing JSON configuration files in
GitHub Actions matrix testing.

## Requirements

- Bun 1.x

## Project Structure

```bash
.
├── json_parser.ts            # Main implementation
├── json_parser.test.ts       # Test implementation (bun:test)
└── bun_project_matrix.json   # Matrix definition consumed by json2vars-setter
```

## Setup & Running

Run the parser:

```bash
cd examples/bun
bun run json_parser.ts
```

Run the tests:

```bash
bun test
```

## Matrix file

`bun_project_matrix.json` defines the OS list and Bun versions used by the matrix
testing workflow. The versions use the form accepted by
[`oven-sh/setup-bun`](https://github.com/marketplace/actions/setup-bun)
(e.g. `1.2.x`, `1.3.x`, `latest`, or an exact `1.3.14`):

```json
{
    "os": ["ubuntu-latest", "windows-latest", "macos-latest"],
    "versions": {
        "bun": ["1.2.x", "1.3.x"]
    },
    "ghpages_branch": "ghgapes"
}
```

The `.github/workflows/bun_test.yml` workflow reads this file through json2vars-setter
and runs the tests across every OS / Bun version combination.
