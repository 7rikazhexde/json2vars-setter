# Java Example for json2vars-setter

This is a Java implementation example for parsing JSON configuration files in
GitHub Actions matrix testing.

## Requirements

- JDK 11 or newer
- Maven

## Project Structure

```bash
.
├── pom.xml                                              # Maven build + dependencies
├── java_project_matrix.json                            # Matrix definition
└── src
    ├── main/java/io/github/json2varssetter/JsonParser.java       # Main implementation
    └── test/java/io/github/json2varssetter/JsonParserTest.java   # Test implementation
```

## Setup & Running

Run the tests with Maven:

```bash
cd examples/java
mvn -B test
```

## Matrix file

`java_project_matrix.json` defines the OS list and Java versions used by the matrix
testing workflow. The versions use the major form accepted by
[`actions/setup-java`](https://github.com/marketplace/actions/setup-java-jdk)
(distribution `temurin`):

```json
{
    "os": ["ubuntu-latest", "windows-latest", "macos-latest"],
    "versions": {
        "java": ["11", "17", "21"]
    },
    "ghpages_branch": "ghgapes"
}
```

The project targets Java 11 bytecode (`maven.compiler.release=11`), so the same code
builds and runs on every JDK in the matrix. The `.github/workflows/java_test.yml`
workflow reads this file through json2vars-setter and runs the tests across every
OS / Java version combination.

> Note: json2vars-setter's dynamic version fetcher sources Java versions from the
> [Adoptium API](https://api.adoptium.net/) (`latest` = newest feature release,
> `stable` = newest LTS), because OpenJDK GA/LTS versions are not cleanly available
> from a single GitHub repository's tags. See the
> [Version Sources reference](../../docs/reference/version-sources.md) for details.
