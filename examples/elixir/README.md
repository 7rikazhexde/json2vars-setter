# Elixir Example for json2vars-setter

This is an Elixir implementation example for parsing JSON configuration files in
GitHub Actions matrix testing.

## Requirements

- Elixir 1.18+ (uses the built-in `JSON` standard-library module — no external
  dependencies)

## Project Structure

```bash
.
├── json_parser.exs             # Main implementation
├── json_parser_test.exs        # Test implementation (ExUnit)
└── elixir_project_matrix.json  # Matrix definition consumed by json2vars-setter
```

## Setup & Running

Run the parser:

```bash
cd examples/elixir
elixir -r json_parser.exs -e "JsonParser.main()"
```

Run the tests:

```bash
elixir json_parser_test.exs
```

## Matrix file

`elixir_project_matrix.json` defines the OS list and Elixir versions used by the
matrix testing workflow. The versions use the form accepted by
[`erlef/setup-beam`](https://github.com/marketplace/actions/erlang-otp-elixir-setup)
(e.g. `1.18`, `1.19`, or an exact `1.18.4`):

```json
{
    "os": ["ubuntu-latest", "windows-latest", "macos-latest"],
    "versions": {
        "elixir": ["1.18", "1.19"]
    },
    "ghpages_branch": "ghgapes"
}
```

`erlef/setup-beam` also requires an Erlang/OTP version; the `.github/workflows/elixir_test.yml`
workflow pins a single OTP version compatible with every Elixir version in the matrix
and reads this file through json2vars-setter to run the tests across every OS / Elixir
version combination.
