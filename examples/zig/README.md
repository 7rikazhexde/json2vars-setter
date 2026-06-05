# Zig Example for json2vars-setter

This is a Zig implementation example for parsing JSON configuration files in
GitHub Actions matrix testing.

## Requirements

- Zig 0.14.x or 0.15.x

## Project Structure

```bash
.
├── json_parser.zig          # Main implementation
├── json_parser_test.zig     # Test implementation (std.testing)
└── zig_project_matrix.json  # Matrix definition consumed by json2vars-setter
```

## Setup & Running

Run the parser:

```bash
cd examples/zig
zig run json_parser.zig
```

Run the tests:

```bash
zig test json_parser_test.zig
```

## Matrix file

`zig_project_matrix.json` defines the OS list and Zig versions used by the matrix
testing workflow. The versions use the exact form accepted by
[`mlugg/setup-zig`](https://github.com/marketplace/actions/setup-zig-compiler)
(e.g. `0.14.1`, `0.15.2`, or `master`):

```json
{
    "os": ["ubuntu-latest", "windows-latest", "macos-latest"],
    "versions": {
        "zig": ["0.14.1", "0.15.2"]
    },
    "ghpages_branch": "ghgapes"
}
```

The `.github/workflows/zig_test.yml` workflow reads this file through json2vars-setter
and runs the tests across every OS / Zig version combination.

The implementation deliberately uses only APIs that are stable across the matrix
Zig versions (`std.json.parseFromSlice`, `std.heap.page_allocator`, `@embedFile`)
so the same source compiles on each.
