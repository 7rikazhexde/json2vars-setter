# Compatibility Notes

This page tracks known OS / version combinations that require a workaround in the
example CI workflows. Each entry records **what the workaround is**, **why it is
needed**, and **what must happen before it can be removed**.

The matrix JSON files (`examples/<lang>/<lang>_project_matrix.json`) always declare
the full set of platforms and versions that `json2vars-setter` supports. Workarounds
live exclusively in the per-language `*_test.yml` workflows, so the declared support
surface stays accurate even while a temporary CI fix is in place.

---

## Swift — versions capped at 6.2.1 (setup-swift@v2.4.0 limit)

| Field | Detail |
|---|---|
| **Affected setup action** | `swift-actions/setup-swift@v2.4.0` |
| **Workaround** | `swift_project_matrix.json` uses `["6.2", "6.2.1"]` instead of version-cache `stable`/`latest` (`6.2.4`/`6.3.2`) |
| **Introduced** | PR #618 (2026-07) |

### Root cause

`swift-actions/setup-swift@v2.4.0` contains a **hardcoded version list**
(`src/swift-versions.ts`) that ends at `6.2.1`. Versions `6.2.2`, `6.2.3`,
`6.2.4`, and `6.3.x` are not in the list and produce:

```text
Error: Version "6.3.2" is not available
```

At the same time, the `macos-latest` runner was upgraded to macOS 26 (Xcode 26.5,
Swift 6.3.2 SDK), which made Swift 6.1.x incompatible. The highest version in the
v2.4.0 list that still works on macOS 26 is `6.2.1`.

`setup-swift@v3.0.0-beta.1` (2025-11-30) rewrites the action to use
[Swiftly](https://github.com/swiftlang/swiftly) and installs any version from
swift.org dynamically — no hardcoded list. It is beta and has not reached a stable
release yet.

### How to restore

1. Confirm `swift-actions/setup-swift` v3 stable is released.
2. Update the `uses: swift-actions/setup-swift@<sha>` pin in `swift_test.yml` to
   the v3 stable SHA (via Dependabot or manually; remove the Dependabot `ignore`
   rule for major-version bumps if one exists).
3. Update `examples/swift/swift_project_matrix.json` to the version-cache
   `stable` and `latest` values (currently `6.2.4` / `6.3.2`).
4. Remove the WORKAROUND comment in `swift_test.yml`.
5. Open a PR and close this item.

---

## Zig — macOS runner pinned to `macos-15`

| Field | Detail |
|---|---|
| **Affected versions** | Zig 0.14.1, 0.15.2 (all current releases) |
| **Affected runner** | `macos-latest` (= macOS 26 as of 2026-07) |
| **Workaround** | `zig_test.yml` maps `macos-latest` → `macos-15` at the `runs-on` level |
| **Introduced** | PR #618 (2026-07) |

### Root cause

`macos-latest` was upgraded to macOS 26 (arm64) + Xcode 26.5, which ships a
new macOS 26 SDK. Zig's bundled libc shim does not yet recognise the SDK's
revised symbol layout, causing linker errors for basic C library symbols
(`_abort`, `_bzero`, `_free`, `_clock_gettime`, etc.) even in a minimal program.

This is an upstream Zig issue unrelated to `json2vars-setter`. The matrix JSON
keeps `macos-latest` to accurately show the action supports that platform;
only the actual runner used in CI is temporarily downgraded.

### How to restore

1. Confirm Zig releases SDK support for macOS 26 (watch
   [ziglang/zig releases](https://github.com/ziglang/zig/releases) or the
   `Refresh data files` workflow output).
2. In `.github/workflows/zig_test.yml`, change `run_tests.runs-on` back to
   `${{ matrix.os }}` and remove the mapping comment.
3. Open a PR; CI should pass on `macos-latest` with the new Zig release.

---

## Ruby — 3.4.0 excluded on `windows-latest`

| Field | Detail |
|---|---|
| **Affected version** | Ruby 3.4.0 |
| **Affected runner** | `windows-latest` |
| **Workaround** | `ruby_test.yml` matrix `exclude:` block skips `(windows-latest, 3.4.0)` |
| **Introduced** | commit `e22a9b83` (pre-v1.9.0) |

### Root cause

Ruby 3.4.0 has a known build/runtime issue on Windows that was fixed in Ruby 3.4.1.
The exact failure mode is a native-extension or MSYS2 toolchain incompatibility
specific to the 3.4.0 point release; 3.4.1 and later run cleanly on Windows.

The matrix JSON keeps 3.4.0 so that `json2vars-setter`'s version-variable output
for that release string is still exercised on Linux and macOS. Only the
`windows-latest` + `3.4.0` leg is skipped.

### How to restore

Once Ruby 3.4.0 is confirmed fixed on Windows (or once 3.4.0 is no longer in the
supported matrix because newer patch releases supersede it):

1. Remove the `exclude:` block from `.github/workflows/ruby_test.yml`.
2. Open a PR; the `(windows-latest, 3.4.0)` leg should pass.

Alternatively, if 3.4.0 is dropped from `ruby_project_matrix.json` because
`stable` has moved to 3.4.x+ in the version cache, simply remove the version
from the matrix JSON and the exclusion becomes moot.

---

## Adding a new workaround

When you discover a new OS / version incompatibility that is **not** a
`json2vars-setter` bug:

1. Keep the affected platform/version in the matrix JSON.
2. Add the minimum workaround in the `*_test.yml` workflow (runner mapping,
   matrix `exclude:`, or `continue-on-error`).
3. Add a comment in the workflow pointing to this page.
4. Add a new section here following the template above.
5. Open a tracking entry in `.issues/` if the fix is non-trivial.
