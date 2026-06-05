//! Minimal JSON configuration parser used to demonstrate consuming the
//! json2vars-setter matrix file in a Zig project. It sticks to APIs that are
//! stable across the Zig versions exercised by the matrix (std.json.parseFromSlice,
//! std.heap.page_allocator, @embedFile) so the same source compiles on each.

const std = @import("std");

/// Shape of the matrix JSON consumed by json2vars-setter.
pub const Matrix = struct {
    os: [][]const u8,
    versions: Versions,
    ghpages_branch: []const u8,

    pub const Versions = struct {
        zig: [][]const u8,
    };
};

/// Parse `data` into a `Matrix`. The caller owns the returned
/// `std.json.Parsed(Matrix)` and must call `deinit()` on it.
pub fn parseConfig(
    allocator: std.mem.Allocator,
    data: []const u8,
) !std.json.Parsed(Matrix) {
    return std.json.parseFromSlice(
        Matrix,
        allocator,
        data,
        .{ .ignore_unknown_fields = true },
    );
}

pub fn main() !void {
    const allocator = std.heap.page_allocator;

    // Embed the matrix file at compile time to avoid file-IO API differences
    // between Zig versions.
    const data = @embedFile("zig_project_matrix.json");

    const parsed = try parseConfig(allocator, data);
    defer parsed.deinit();

    const matrix = parsed.value;

    std.debug.print("os:\n", .{});
    for (matrix.os) |os| {
        std.debug.print("  - {s}\n", .{os});
    }
    std.debug.print("zig versions:\n", .{});
    for (matrix.versions.zig) |version| {
        std.debug.print("  - {s}\n", .{version});
    }
    std.debug.print("ghpages_branch: {s}\n", .{matrix.ghpages_branch});
}
