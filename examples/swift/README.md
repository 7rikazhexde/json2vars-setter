# Swift Example for json2vars-setter

This is a Swift implementation example for parsing JSON configuration files in
GitHub Actions matrix testing.

## Requirements

- Swift 6.x (uses only Foundation's `JSONSerialization` — no package dependencies)

## Project Structure

```bash
.
├── Package.swift                                  # Swift package manifest
├── Sources/JsonParserLib/JsonParser.swift         # Main implementation
├── Tests/JsonParserLibTests/JsonParserTests.swift # Tests (XCTest)
└── swift_project_matrix.json                      # Matrix consumed by json2vars-setter
```

## Setup & Running

Run the tests:

```bash
cd examples/swift
swift test
```

## Matrix file

`swift_project_matrix.json` defines the OS list and Swift versions used by the matrix
testing workflow. The versions use the form accepted by
[`swift-actions/setup-swift`](https://github.com/marketplace/actions/setup-swift-environment)
(e.g. an exact `6.2.1`, or the `6.2` short form):

```json
{
    "os": ["ubuntu-latest", "macos-latest"],
    "versions": {
        "swift": ["6.1.3", "6.2.1"]
    },
    "ghpages_branch": "ghgapes"
}
```

> **Version availability:** `swift-actions/setup-swift` installs from its own bundled
> list of known Swift versions, which can lag behind the very latest swift.org
> release. Pick example/matrix versions that the action supports.

> **OS note:** the Swift matrix targets `ubuntu-latest` and `macos-latest` — Swift's
> first-class CI platforms via `swift-actions/setup-swift`. Windows is intentionally
> omitted because the Windows Swift toolchain setup is less reliable in CI.

The `.github/workflows/swift_test.yml` workflow reads this file through json2vars-setter
and runs the tests across every OS / Swift version combination.
