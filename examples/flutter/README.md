# Flutter Example

A tiny Flutter package that demonstrates consuming a `json2vars-setter` matrix
file. It is exercised by the
[`Flutter Test`](../../.github/workflows/flutter_test.yml) workflow across a matrix
of Flutter versions.

> **Flutter vs Dart:** Flutter bundles its own Dart SDK and has its own release
> stream, so json2vars-setter tracks it as a **separate** language (`flutter`,
> sourced from the official Flutter release manifest — the `flutter/flutter` GitHub
> tags are stale and unusable). Use `dart` if you build a pure-Dart project.

## Files

| File | Purpose |
|------|---------|
| `lib/json_parser.dart` | Minimal helper that parses the matrix JSON with `dart:convert` — no extra packages. |
| `test/json_parser_test.dart` | A `flutter_test` unit test (run with `flutter test`). |
| `pubspec.yaml` | Flutter package manifest (`flutter` + `flutter_test` SDK deps). |
| `flutter_project_matrix.json` | The matrix consumed by the action: OS list + the Flutter versions to test. |

## Run it locally

With Flutter installed:

```bash
cd examples/flutter
flutter pub get
flutter test
```

## How the matrix is used in CI

`flutter_test.yml` reads `flutter_project_matrix.json` through json2vars-setter,
then runs `flutter test` once per Flutter version. There is no official Flutter
setup action, so the example uses
[`subosito/flutter-action`](https://github.com/subosito/flutter-action), the
de-facto, actively-maintained action for installing a specific Flutter version:

```yaml
- name: Set up Flutter ${{ matrix.flutter-version }}
  uses: subosito/flutter-action@<sha> # vX
  with:
    flutter-version: ${{ matrix.flutter-version }}
    channel: stable
```

The matrix targets `ubuntu-latest` and `macos-latest`.
