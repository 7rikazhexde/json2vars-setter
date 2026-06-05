// Dependency-free test runner for json_parser.dart. Uses plain assertions that
// throw on failure (a non-zero exit fails the CI matrix leg), so it needs no
// external test package.

import 'json_parser.dart';

int _failures = 0;

void check(bool condition, String message) {
  if (!condition) {
    _failures++;
    print('FAIL: $message');
  }
}

const sample = '''
{
  "os": ["ubuntu-latest", "windows-latest", "macos-latest"],
  "versions": { "dart": ["3.11.6", "3.12.1"] },
  "ghpages_branch": "ghgapes"
}
''';

void main() {
  final config = parseConfig(sample);
  check(config != null, 'config should not be null');

  final os = (config!['os'] as List).cast<String>();
  check(os.length == 3, 'os should have 3 entries');
  check(os.contains('ubuntu-latest'), 'os should contain ubuntu-latest');
  check(os.contains('windows-latest'), 'os should contain windows-latest');
  check(os.contains('macos-latest'), 'os should contain macos-latest');

  // Assert structure, not specific version values, so bumping the matrix
  // versions never requires editing this test.
  final versions = ((config['versions'] as Map)['dart'] as List).cast<String>();
  check(versions.isNotEmpty, 'dart versions should be a non-empty list');
  check(
    versions.every((v) => v.isNotEmpty),
    'each dart version should be a non-empty string',
  );

  check(config['ghpages_branch'] == 'ghgapes', 'ghpages_branch should match');

  check(parseConfig('not json', silent: true) == null, 'invalid JSON -> null');

  if (_failures > 0) {
    throw StateError('$_failures test(s) failed');
  }
  print('All tests passed');
}
