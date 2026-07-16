# Restore OS/version compatibility workarounds when upstream fixes land

**Type**: enhancement (maintenance)  
**Status**: open — waiting on upstream

Two active workarounds exist in the example CI workflows. Each must be removed
once the upstream issue is resolved. See `docs/reference/compatibility-notes.md`
for the full rationale and restore instructions.

---

## 1. Zig — macOS runner pinned to `macos-15`

**File**: `.github/workflows/zig_test.yml` (`run_tests.runs-on`)  
**Introduced**: PR #618 (2026-07)

**Upstream condition**: Zig releases a version whose bundled libc shim supports
the macOS 26 SDK (fixes `undefined symbol: _abort`, `_bzero`, `_free`, etc.).

**Restore steps**:
1. Confirm the new Zig version passes on `macos-latest` (run a `workflow_dispatch`
   on `zig_test.yml` after updating `zig_project_matrix.json` to the new version).
2. In `zig_test.yml`, change `run_tests.runs-on` back to `${{ matrix.os }}`.
3. Remove the WORKAROUND comment block.
4. Open a PR and close this item.

---

## 2. Ruby 3.4.0 excluded on `windows-latest`

**File**: `.github/workflows/ruby_test.yml` (`run_tests.strategy.matrix.exclude`)  
**Introduced**: commit `e22a9b83` (pre-v1.9.0)

**Upstream condition**: Ruby 3.4.0 is confirmed working on Windows (unlikely —
the issue was fixed in 3.4.1), **or** Ruby 3.4.0 is no longer in
`ruby_project_matrix.json` because stable has moved to 3.4.x+.

**Restore steps (if 3.4.0 is fixed)**:
1. Remove the `exclude:` block (and its comment) from `ruby_test.yml`.
2. Open a PR; the `(windows-latest, 3.4.0)` leg should now pass.

**More likely path**: when the version cache `stable` advances past 3.4.x, drop
3.4.0 from `ruby_project_matrix.json` via the normal `Refresh data files`
workflow — the exclusion then becomes moot and can be removed at the same time.
