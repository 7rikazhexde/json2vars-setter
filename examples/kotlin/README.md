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
then runs the tests once per Kotlin version with
[`fwilhe2/setup-kotlin`](https://github.com/fwilhe2/setup-kotlin) (there is no
official `setup-kotlin`; this is the de-facto action for the Kotlin CLI compiler):

```yaml
- uses: fwilhe2/setup-kotlin@<sha> # v1.8
  with:
    version: ${{ matrix.kotlin-version }}
```

> **Note on OS coverage:** the matrix uses `ubuntu-latest` and `macos-latest`
> only. The example drives the Kotlin **CLI** compiler from a `bash` step, and
> invoking the Windows `kotlinc.bat` from Git Bash is brittle; since the compiled
> output is platform-independent JVM bytecode, the two Unix runners already prove
> the example works. A Gradle-based project would add Windows back easily.
