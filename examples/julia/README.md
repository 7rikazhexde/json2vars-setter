# Julia Example for json2vars-setter

This is a Julia implementation example for parsing JSON configuration files in
GitHub Actions matrix testing.

## Requirements

- Julia 1.x
- [`JSON.jl`](https://github.com/JuliaIO/JSON.jl) (declared in `Project.toml`;
  Julia has no JSON parser in its standard library)

## Project Structure

```bash
.
├── json_parser.jl            # Main implementation (uses JSON.jl)
├── json_parser_test.jl       # Test runner (Julia `Test` standard library)
├── Project.toml              # Project environment declaring the JSON dependency
└── julia_project_matrix.json # Matrix definition consumed by json2vars-setter
```

## Setup & Running

```bash
cd examples/julia
julia --project=. -e 'using Pkg; Pkg.instantiate()'
```

Run the parser:

```bash
julia --project=. json_parser.jl
```

Run the tests:

```bash
julia --project=. json_parser_test.jl
```

## Matrix file

`julia_project_matrix.json` defines the OS list and Julia versions used by the
matrix testing workflow. The versions use the form accepted by
[`julia-actions/setup-julia`](https://github.com/marketplace/actions/setup-julia-environment)
(e.g. the `1.11` short form, an exact `1.11.2`, or aliases like `lts` / `nightly`):

```json
{
    "os": ["ubuntu-latest", "windows-latest", "macos-latest"],
    "versions": {
        "julia": ["1.10", "1.11"]
    },
    "ghpages_branch": "ghgapes"
}
```

The `.github/workflows/julia_test.yml` workflow reads this file through json2vars-setter
and runs the tests across every OS / Julia version combination.
