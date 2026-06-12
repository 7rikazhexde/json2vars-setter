#include "json_parser.hpp"

#include <iostream>
#include <string>
#include <vector>

// Tiny, framework-free test runner for json_parser. It needs only the C++
// standard library (no test framework), so the example compiles with just a GCC
// toolchain. A failed assertion prints to stderr and the process exits non-zero,
// which fails the CI matrix leg; a clean run prints "All tests passed." and
// exits 0.

namespace {

int failures = 0;

void assert_equals(const std::vector<std::string>& expected,
                   const std::vector<std::string>& actual,
                   const std::string& msg) {
    if (expected != actual) {
        std::cerr << "FAIL: " << msg << '\n';
        ++failures;
    } else {
        std::cout << "PASS: " << msg << '\n';
    }
}

}  // namespace

int main() {
    const std::string sample = R"({
      "os": ["ubuntu-latest", "macos-latest"],
      "versions": { "gcc": ["14", "13"] },
      "ghpages_branch": "gh-pages"
    })";

    assert_equals({"ubuntu-latest", "macos-latest"},
                  json_parser::parse_string_array(sample, "os"),
                  "parse the os array");
    assert_equals({"14", "13"}, json_parser::parse_string_array(sample, "gcc"),
                  "parse the gcc versions");
    assert_equals({}, json_parser::parse_string_array(sample, "missing"),
                  "absent key yields an empty vector");

    if (failures > 0) {
        std::cerr << failures << " test(s) failed.\n";
        return 1;
    }
    std::cout << "All tests passed.\n";
    return 0;
}
