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

        // Assert structure, not specific version values, so bumping the matrix
        // versions never requires editing this test.
        let versionsMap = try XCTUnwrap(config["versions"] as? [String: Any])
        let swiftVersions = try XCTUnwrap(versionsMap["swift"] as? [String])
        XCTAssertFalse(swiftVersions.isEmpty)
        XCTAssertTrue(swiftVersions.allSatisfy { !$0.isEmpty })

        XCTAssertEqual(config["ghpages_branch"] as? String, "ghgapes")
    }

    func testReturnsNilForInvalidJSON() {
        XCTAssertNil(JsonParser.parseConfig("not json"))
    }
}
