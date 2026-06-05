# Deno Example for json2vars-setter

This is a Deno implementation example for parsing JSON configuration files in
GitHub Actions matrix testing.

## Requirements

- Deno 1.x or 2.x

## Project Structure

```bash
.
├── json_parser.ts            # Main implementation
├── json_parser_test.ts       # Test implementation
└── deno_project_matrix.json  # Matrix definition consumed by json2vars-setter
```

## Setup & Running

Run the parser:

```bash
cd examples/deno
deno run --allow-read json_parser.ts
```

Run the tests:

```bash
deno test --allow-read
```

## Matrix file

`deno_project_matrix.json` defines the OS list and Deno versions used by the matrix
testing workflow. The versions use the form accepted by
[`denoland/setup-deno`](https://github.com/marketplace/actions/setup-deno)
(e.g. `v1.x`, `v2.x`, or an exact `2.1.4`):

```json
{
    "os": ["ubuntu-latest", "windows-latest", "macos-latest"],
    "versions": {
        "deno": ["v1.x", "v2.x"]
    },
    "ghpages_branch": "ghgapes"
}
```

The `.github/workflows/deno_test.yml` workflow reads this file through json2vars-setter
and runs the tests across every OS / Deno version combination.
