// Minimal JSON configuration parser used to demonstrate consuming the
// json2vars-setter matrix file in a Flutter package. It uses only the Dart SDK
// (dart:convert), so no extra package dependencies are required.

import 'dart:convert';

/// Parse [contents] (JSON text) into a map. Returns `null` on parse failure.
Map<String, dynamic>? parseConfig(String contents) {
  try {
    return jsonDecode(contents) as Map<String, dynamic>;
  } catch (_) {
    return null;
  }
}
