# macOS runner upgrade breaks language matrix CI

**Type**: docs / runbook  
**Status**: resolved (macOS 26 case fixed in PR #618)

## Problem

When GitHub upgrades `macos-latest` to a new major macOS version, language toolchains
in the example matrices can break because the new Xcode SDK may require a newer compiler
than the pinned matrix versions, or because a language's libc shim doesn't yet support
the new SDK.

Observed in 2026-07 when `macos-latest` moved to macOS 26 (arm64) + Xcode 26.5
(Swift 6.3.2 SDK):

- **Swift < 6.3.x**: compile fails with "this SDK is not supported by the compiler"
- **Zig 0.14.1 / 0.15.2**: linker fails with `undefined symbol: _abort`, `_bzero`, etc.

The failures surface on Dependabot PRs that touch all `*_test.yml` files (e.g. a badge
action bump), making it look like the bump caused the problem.

## How to detect

Weekly badge runs (every language `*_test.yml` has a `schedule:`) will turn red when
a runner upgrade breaks a matrix. Check the badge in README / `docs/index.md` or watch
the Actions tab for a failing weekly run.

## Fix procedure

1. **Identify which versions fail**: open the failing run's log, look for the actual
   compiler/linker error (not just "exit code 1").

2. **Swift SDK mismatch** (`this SDK is not supported by the compiler`):
   - Check `version_cache.json` for current `stable` and `latest` Swift versions.
   - Update `examples/swift/swift_project_matrix.json` to those versions.
   - Run `uv run pre-commit run --all-files` locally (or let CI do it) — the
     `gen-language-docs` hook regenerates `docs/languages/swift.md` automatically.

3. **Zig (or other language) linker/SDK errors on macOS**:
   - Remove `macos-latest` from `examples/zig/zig_project_matrix.json` temporarily.
   - Add a comment in the PR explaining why (upstream doesn't support the new SDK yet).
   - Restore `macos-latest` once the language releases support for the new macOS SDK.

4. **Open a PR** with the matrix changes. The Merge Gate will re-aggregate and turn
   green once Swift/Zig tests pass.

5. **After the fix PR merges**, rebase any blocked Dependabot PR — it will now inherit
   the corrected matrices and its CI will pass.

## Restore Zig macOS (when Zig supports macOS 26)

Check the Zig release notes or run a quick test in a `workflow_dispatch` run with the
new Zig version. When it succeeds, restore `macos-latest` in
`examples/zig/zig_project_matrix.json` and open a small PR.
