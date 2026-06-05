const std = @import("std");
const parser = @import("json_parser.zig");

const sample =
    \\{
    \\  "os": ["ubuntu-latest", "windows-latest", "macos-latest"],
    \\  "versions": { "zig": ["0.14.1", "0.15.2"] },
    \\  "ghpages_branch": "ghgapes"
    \\}
;

test "parses the expected values" {
    const parsed = try parser.parseConfig(std.testing.allocator, sample);
    defer parsed.deinit();

    const matrix = parsed.value;

    try std.testing.expectEqual(@as(usize, 3), matrix.os.len);
    try std.testing.expectEqualStrings("ubuntu-latest", matrix.os[0]);
    try std.testing.expectEqualStrings("windows-latest", matrix.os[1]);
    try std.testing.expectEqualStrings("macos-latest", matrix.os[2]);

    try std.testing.expectEqual(@as(usize, 2), matrix.versions.zig.len);
    try std.testing.expectEqualStrings("0.14.1", matrix.versions.zig[0]);
    try std.testing.expectEqualStrings("0.15.2", matrix.versions.zig[1]);

    try std.testing.expectEqualStrings("ghgapes", matrix.ghpages_branch);
}

test "returns an error for invalid JSON" {
    // Use the capture form so the test does not depend on the exact error tag,
    // which can differ between Zig versions.
    if (parser.parseConfig(std.testing.allocator, "not json")) |parsed| {
        parsed.deinit();
        try std.testing.expect(false);
    } else |_| {}
}
