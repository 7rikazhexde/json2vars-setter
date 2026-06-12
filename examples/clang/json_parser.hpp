#ifndef JSON_PARSER_HPP
#define JSON_PARSER_HPP

#include <regex>
#include <string>
#include <vector>

// Minimal, dependency-free helper to consume the json2vars-setter matrix file in
// a C++ project.
//
// It is intentionally tiny: it extracts the flat string arrays the matrix uses
// (e.g. "os", or "clang" under "versions") with a small regex. That is enough to
// demonstrate reading the action's output without pulling in a JSON library, so
// the example compiles with nothing but a Clang C++ toolchain and the standard
// library.
namespace json_parser {

// Extract the first array of strings associated with `key` in `json`.
// Returns an empty vector when the key is absent.
inline std::vector<std::string> parse_string_array(const std::string& json,
                                                    const std::string& key) {
    std::vector<std::string> result;

    // "<key>" : [ ... ]  — the body matches everything up to the closing ']',
    // which also spans newlines without needing a dot-all flag.
    const std::regex array_re("\"" + key + "\"\\s*:\\s*\\[([^\\]]*)\\]");
    std::smatch array_match;
    if (!std::regex_search(json, array_match, array_re)) {
        return result;
    }

    const std::string body = array_match[1].str();
    const std::regex item_re("\"([^\"]*)\"");
    for (auto it = std::sregex_iterator(body.begin(), body.end(), item_re);
         it != std::sregex_iterator(); ++it) {
        result.push_back((*it)[1].str());
    }
    return result;
}

}  // namespace json_parser

#endif  // JSON_PARSER_HPP
