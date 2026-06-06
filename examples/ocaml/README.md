# OCaml Example for json2vars-setter

This is an OCaml implementation example for parsing JSON configuration files in
GitHub Actions matrix testing.

## Requirements

- OCaml 5.x with opam and dune
- [`yojson`](https://opam.ocaml.org/packages/yojson/) (declared in the `.opam`
  file; OCaml has no JSON parser in its standard library)

## Project Structure

```bash
.
├── bin/main.ml                # Main implementation + checks (Yojson, dependency-free assertions)
├── bin/dune                   # Dune executable stanza
├── dune-project               # Dune project file
├── json_parser_example.opam   # opam package manifest (depends on yojson)
└── ocaml_project_matrix.json  # Matrix definition consumed by json2vars-setter
```

## Setup & Running

```bash
cd examples/ocaml
opam install . --deps-only
opam exec -- dune exec ./bin/main.exe
```

`opam install . --deps-only` installs `yojson` (and `dune`); `dune exec` builds and
runs the checks; a non-zero exit fails the run.

## Matrix file

`ocaml_project_matrix.json` defines the OS list and OCaml versions used by the matrix
testing workflow. The versions use the form accepted by
[`ocaml/setup-ocaml`](https://github.com/marketplace/actions/set-up-ocaml)
(an exact compiler version such as `5.2.1`, or the `5.2` short form):

```json
{
    "os": ["ubuntu-latest", "macos-latest"],
    "versions": {
        "ocaml": ["5.2.1", "5.3.0"]
    },
    "ghpages_branch": "ghgapes"
}
```

The `.github/workflows/ocaml_test.yml` workflow reads this file through json2vars-setter
and runs the program across every OS / OCaml version combination. OCaml targets
`ubuntu`/`macos` (its first-class CI platforms).
