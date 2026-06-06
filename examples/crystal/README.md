# Crystal Example for json2vars-setter

This is a Crystal implementation example for parsing JSON configuration files in
GitHub Actions matrix testing.

## Requirements

- Crystal 1.x (uses only the standard-library `JSON` module — no shard dependencies)

## Project Structure

```bash
.
├── json_parser.cr              # Main implementation (stdlib JSON)
├── json_parser_spec.cr         # Spec (Crystal `spec` framework)
├── shard.yml                   # Minimal shard manifest (no dependencies)
└── crystal_project_matrix.json # Matrix definition consumed by json2vars-setter
```

## Setup & Running

Run the tests:

```bash
cd examples/crystal
crystal spec json_parser_spec.cr
```

## Matrix file

`crystal_project_matrix.json` defines the OS list and Crystal versions used by the
matrix testing workflow. The versions use the form accepted by
[`crystal-lang/install-crystal`](https://github.com/marketplace/actions/install-crystal)
(e.g. an exact `1.20.2`, or aliases like `latest` / `nightly`):

```json
{
    "os": ["ubuntu-latest", "macos-latest"],
    "versions": {
        "crystal": ["1.19.2", "1.20.2"]
    },
    "ghpages_branch": "ghgapes"
}
```

The `.github/workflows/crystal_test.yml` workflow reads this file through json2vars-setter
and runs the tests across every OS / Crystal version combination. Crystal targets
`ubuntu`/`macos` (its first-class CI platforms).
