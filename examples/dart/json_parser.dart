// Minimal JSON configuration parser used to demonstrate consuming the
// json2vars-setter matrix file in a Dart project. It uses only the Dart SDK
// (dart:convert), so no package dependencies are required.

import 'dart:convert';
import 'dart:io';

/// Parse [contents] (JSON text) into a map. Returns `null` on parse failure.
Map<String, dynamic>? parseConfig(String contents, {bool silent = false}) {
  try {
    return jsonDecode(contents) as Map<String, dynamic>;
  } catch (e) {
    if (!silent) {
      stderr.writeln('Error parsing JSON: $e');
    }
    return null;
  }
}

void main() {
  final file = File('dart_project_matrix.json');
  final result = parseConfig(file.readAsStringSync());
  if (result != null) {
    print(const JsonEncoder.withIndent('  ').convert(result));
  }
}
