# Dart Example for json2vars-setter

This is a Dart implementation example for parsing JSON configuration files in
GitHub Actions matrix testing.

## Requirements

- Dart SDK 3.x (uses only `dart:convert` — no package dependencies)

## Project Structure

```bash
.
├── json_parser.dart          # Main implementation
├── json_parser_test.dart     # Test runner (dependency-free assertions)
├── pubspec.yaml              # Minimal Dart package manifest (no dependencies)
└── dart_project_matrix.json  # Matrix definition consumed by json2vars-setter
```

## Setup & Running

```bash
cd examples/dart
dart pub get
```

Run the parser:

```bash
dart run json_parser.dart
```

Run the tests:

```bash
dart run json_parser_test.dart
```

## Matrix file

`dart_project_matrix.json` defines the OS list and Dart versions used by the matrix
testing workflow. The versions use the form accepted by
[`dart-lang/setup-dart`](https://github.com/marketplace/actions/setup-dart-sdk)
(e.g. an exact `3.12.1`, the `3.12` short form, or a channel like `stable`):

```json
{
    "os": ["ubuntu-latest", "windows-latest", "macos-latest"],
    "versions": {
        "dart": ["3.11.6", "3.12.1"]
    },
    "ghpages_branch": "ghgapes"
}
```

The `.github/workflows/dart_test.yml` workflow reads this file through json2vars-setter
and runs the tests across every OS / Dart version combination.
