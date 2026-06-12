# Clang (C++) Example

A tiny, dependency-free C++ project that demonstrates consuming a
`json2vars-setter` matrix file. It is exercised by the
[`Clang Test`](../../.github/workflows/clang_test.yml) workflow across a matrix of
Clang/LLVM versions.

> **Clang vs "C++":** json2vars-setter tracks the **compiler** version stream
> (`clang`, from [`llvm/llvm-project`](https://github.com/llvm/llvm-project)
> releases), which is the axis real C++ CI matrices vary over
> (`clang-19`, `clang-20`, …). The C++ **language standard** (`-std=c++17/20/23`)
> is a static list you can hand-write in your matrix JSON, so it needs no fetcher.

## Files

| File | Purpose |
|------|---------|
| `json_parser.hpp` | Header-only helper that extracts the matrix's string arrays (`os`, `versions.clang`) with a small regex — no JSON library required. |
| `json_parser_test.cpp` | Framework-free test runner (uses only the C++ standard library); exits non-zero on a failed assertion. |
| `clang_project_matrix.json` | The matrix consumed by the action: OS list + the Clang versions to test. |

## Run it locally

With any Clang toolchain installed (`clang++`):

```bash
cd examples/clang

# Build and run the tests
clang++ -std=c++17 json_parser_test.cpp -o json_parser_test
./json_parser_test
```

## How the matrix is used in CI

`clang_test.yml` reads `clang_project_matrix.json` through json2vars-setter, then
compiles and runs the tests once per Clang version. There is no official Clang/LLVM
setup action, and — unlike a language such as Kotlin that ships a single,
predictably-named archive — the LLVM release assets are named inconsistently across
versions and platforms (`LLVM-X-Linux-X64`, `clang+llvm-X-<triple>`, …). So the
example uses [`aminya/setup-cpp`](https://github.com/aminya/setup-cpp), the
de-facto, actively-maintained action for installing a specific compiler version
cross-platform:

```yaml
- name: Set up Clang ${{ matrix.clang-version }}
  uses: aminya/setup-cpp@<sha> # vX
  with:
    compiler: llvm-${{ matrix.clang-version }}
```

The matrix targets `ubuntu-latest` and `macos-latest` (both have official LLVM
prebuilt binaries for the pinned versions).
