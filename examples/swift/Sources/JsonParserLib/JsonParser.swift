import Foundation

/// Minimal JSON configuration parser used to demonstrate consuming the
/// json2vars-setter matrix file in a Swift project. It uses only Foundation
/// (`JSONSerialization`), so no package dependencies are required.
public enum JsonParser {
    /// Parse `text` (JSON) into a dictionary. Returns `nil` on parse failure.
    public static func parseConfig(_ text: String) -> [String: Any]? {
        guard let data = text.data(using: .utf8) else { return nil }
        let object = try? JSONSerialization.jsonObject(with: data)
        return object as? [String: Any]
    }
}
