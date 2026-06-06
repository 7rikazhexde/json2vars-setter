# Haskell Example for json2vars-setter

This is a Haskell implementation example for parsing JSON configuration files in
GitHub Actions matrix testing.

## Requirements

- GHC 9.x and Cabal
- [`aeson`](https://hackage.haskell.org/package/aeson) (declared in the `.cabal`
  file; Haskell has no JSON parser in `base`)

## Project Structure

```bash
.
├── app/Main.hs                  # Main implementation + checks (Aeson, dependency-free assertions)
├── json-parser-example.cabal    # Cabal package manifest (depends on aeson)
└── haskell_project_matrix.json  # Matrix definition consumed by json2vars-setter
```

## Setup & Running

```bash
cd examples/haskell
cabal update
cabal run json-parser-test
```

`cabal run` builds the project (fetching `aeson` from Hackage on first run) and runs
the checks; a non-zero exit fails the run.

## Matrix file

`haskell_project_matrix.json` defines the OS list and GHC versions used by the matrix
testing workflow. The versions use the form accepted by
[`haskell-actions/setup`](https://github.com/marketplace/actions/setup-haskell)
(an exact GHC version such as `9.8.4` or `9.10.1`):

```json
{
    "os": ["ubuntu-latest", "macos-latest"],
    "versions": {
        "haskell": ["9.8.4", "9.10.1"]
    },
    "ghpages_branch": "ghgapes"
}
```

The `.github/workflows/haskell_test.yml` workflow reads this file through json2vars-setter
and runs the program across every OS / GHC version combination. Haskell targets
`ubuntu`/`macos` (its first-class CI platforms).
