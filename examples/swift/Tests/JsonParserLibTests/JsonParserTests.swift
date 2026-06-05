import XCTest

@testable import JsonParserLib

final class JsonParserTests: XCTestCase {
    let sample = """
        {
          "os": ["ubuntu-latest", "macos-latest"],
          "versions": { "swift": ["6.1.3", "6.2.1"] },
          "ghpages_branch": "ghgapes"
        }
        """

    func testParsesExpectedValues() throws {
        let config = try XCTUnwrap(JsonParser.parseConfig(sample))

        let os = try XCTUnwrap(config["os"] as? [String])
        XCTAssertEqual(os, ["ubuntu-latest", "macos-latest"])

        let versions = try XCTUnwrap(config["versions"] as? [String: Any])
        XCTAssertEqual(versions["swift"] as? [String], ["6.1.3", "6.2.1"])

        XCTAssertEqual(config["ghpages_branch"] as? String, "ghgapes")
    }

    func testReturnsNilForInvalidJSON() {
        XCTAssertNil(JsonParser.parseConfig("not json"))
    }
}
