// Run with `flutter test`. Uses the flutter_test framework (test/expect),
// so the example exercises a real Flutter package toolchain. A failing
// expectation fails this CI matrix leg.

import 'package:flutter_test/flutter_test.dart';
import 'package:json2vars_flutter_example/json_parser.dart';

const sample = '''
{
  "os": ["ubuntu-latest", "macos-latest"],
  "versions": { "flutter": ["3.44.2", "3.41.9"] },
  "ghpages_branch": "gh-pages"
}
''';

void main() {
  test('parses the matrix config', () {
    final config = parseConfig(sample);
    expect(config, isNotNull);

    final os = (config!['os'] as List).cast<String>();
    expect(os, ['ubuntu-latest', 'macos-latest']);

    // Assert structure, not specific version values, so bumping the matrix
    // versions never requires editing this test.
    final versions =
        ((config['versions'] as Map)['flutter'] as List).cast<String>();
    expect(versions, isNotEmpty);
    expect(versions.every((v) => v.isNotEmpty), isTrue);

    expect(config['ghpages_branch'], 'gh-pages');
  });

  test('invalid JSON returns null', () {
    expect(parseConfig('not json'), isNull);
  });
}
