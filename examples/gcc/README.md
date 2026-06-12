# GCC (C++) Example

A tiny, dependency-free C++ project that demonstrates consuming a
`json2vars-setter` matrix file. It is exercised by the
[`GCC Test`](../../.github/workflows/gcc_test.yml) workflow across a matrix of GCC
versions.

> **GCC vs "C++":** json2vars-setter tracks the **compiler** version stream (`gcc`,
> from [`gcc-mirror/gcc`](https://github.com/gcc-mirror/gcc) releases), which is the
> axis real C++ CI matrices vary over (`gcc-13`, `gcc-14`, …). The C++ **language
> standard** (`-std=c++17/20/23`) is a static list you hand-write in your matrix
> JSON, so it needs no fetcher.

## Files

| File | Purpose |
|------|---------|
| `json_parser.hpp` | Header-only helper that extracts the matrix's string arrays (`os`, `versions.gcc`) with a small regex — no JSON library required. |
| `json_parser_test.cpp` | Framework-free test runner (uses only the C++ standard library); exits non-zero on a failed assertion. |
| `gcc_project_matrix.json` | The matrix consumed by the action: OS list + the GCC versions to test. |

## Run it locally

With any GCC toolchain installed (`g++`):

```bash
cd examples/gcc

# Build and run the tests
g++ -std=c++17 json_parser_test.cpp -o json_parser_test
./json_parser_test
```

## How the matrix is used in CI

`gcc_test.yml` reads `gcc_project_matrix.json` through json2vars-setter, then
compiles and runs the tests once per GCC version. There is no official GCC setup
action, so the example uses
[`aminya/setup-cpp`](https://github.com/aminya/setup-cpp), the de-facto,
actively-maintained action for installing a specific compiler version
cross-platform:

```yaml
- name: Set up GCC ${{ matrix.gcc-version }}
  uses: aminya/setup-cpp@<sha> # vX
  with:
    compiler: gcc-${{ matrix.gcc-version }}
```

> **Note on version granularity:** GCC's distributable unit (apt / Homebrew) is the
> **major series**, so the matrix pins majors (`14`, `13`) rather than full `X.Y.Z`
> patch versions — that is the axis real GCC CI selects on. (Clang/LLVM ships
> full-version binaries, so the Clang example pins `X.Y.Z`.)

The matrix targets `ubuntu-latest` and `macos-latest`.
