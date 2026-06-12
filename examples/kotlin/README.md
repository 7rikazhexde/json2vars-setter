# Kotlin Example

A tiny, dependency-free Kotlin project that demonstrates consuming a
`json2vars-setter` matrix file. It is exercised by the
[`Kotlin Test`](../../.github/workflows/kotlin_test.yml) workflow across a matrix
of Kotlin versions.

## Files

| File | Purpose |
|------|---------|
| `JsonParser.kt` | Minimal helper that extracts the matrix's string arrays (`os`, `versions.kotlin`) with a small regex — no JSON library required. |
| `JsonParserTest.kt` | Framework-free test runner (uses only the Kotlin stdlib); exits non-zero on a failed assertion. |
| `kotlin_project_matrix.json` | The matrix consumed by the action: OS list + the Kotlin versions to test. |

## Run it locally

Install the Kotlin compiler (e.g. via [SDKMAN!](https://sdkman.io/): `sdk install kotlin`), then:

```bash
cd examples/kotlin

# Run the tests
kotlinc JsonParser.kt JsonParserTest.kt -include-runtime -d app.jar
kotlin -classpath app.jar JsonParserTestKt

# Or run the parser against the matrix file
kotlin -classpath app.jar JsonParserKt
```

## How the matrix is used in CI

`kotlin_test.yml` reads `kotlin_project_matrix.json` through json2vars-setter,
then runs the tests once per Kotlin version. There is no official Kotlin setup
action, and the runner's pre-installed Kotlin is a single fixed version, so the
example downloads the exact compiler for each matrix version straight from the
[JetBrains release](https://github.com/JetBrains/kotlin/releases) (the same source
the version fetcher reads), verifies its published SHA-256, and adds `kotlinc` to
`PATH` — no third-party setup action required:

```yaml
- name: Set up Kotlin ${{ matrix.kotlin-version }}
  shell: bash
  run: |
    version="${{ matrix.kotlin-version }}"
    base="https://github.com/JetBrains/kotlin/releases/download/v${version}"
    curl -fsSL -o kotlin-compiler.zip "${base}/kotlin-compiler-${version}.zip"
    curl -fsSL -o kotlin-compiler.zip.sha256 "${base}/kotlin-compiler-${version}.zip.sha256"
    echo "$(cat kotlin-compiler.zip.sha256)  kotlin-compiler.zip" | shasum -a 256 -c -
    unzip -q kotlin-compiler.zip -d "$HOME/kotlin"
    echo "$HOME/kotlin/kotlinc/bin" >> "$GITHUB_PATH"
```

> **Note on OS coverage:** the matrix uses `ubuntu-latest` and `macos-latest`
> only. The example drives the Kotlin **CLI** compiler from a `bash` step, and
> invoking the Windows `kotlinc.bat` from Git Bash is brittle; since the compiled
> output is platform-independent JVM bytecode, the two Unix runners already prove
> the example works. A Gradle-based project would add Windows back easily.
