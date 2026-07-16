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
   - **Also check setup-swift's hardcoded version list** — `swift-actions/setup-swift@v2`
     has a hardcoded `VERSIONS_LIST` in `src/swift-versions.ts`. Versions not in that list
     produce "Version X.Y.Z is not available" even if they exist on swift.org. The list
     maxes out at `6.2.1` as of v2.4.0. Do NOT blindly copy cache `stable`/`latest` into
     the matrix; verify first that setup-swift supports those version strings.
   - Use the highest versions available in setup-swift's list that also work with the new
     macOS SDK (e.g. `["6.2", "6.2.1"]` for the macOS 26 / setup-swift v2.4.0 combo).
   - When **setup-swift v3 stable** releases (it uses Swiftly and supports any version
     from swift.org dynamically), update the action pin in `swift_test.yml` and then
     update the matrix to the cache `stable`/`latest`.
   - Run `uv run pre-commit run --all-files` locally (or let CI do it) — the
     `gen-language-docs` hook regenerates `docs/languages/swift.md` automatically.

3. **Zig (or other language) linker/SDK errors on macOS**:
   - Do NOT remove macOS from the OS list entirely — that would suggest the language is
     unsupported on macOS, which is misleading.
   - Instead, **pin to the previous macOS runner** (e.g. `macos-15`) so macOS coverage
     continues at a version the toolchain actually supports.
   - Restore `macos-latest` once the language releases support for the new macOS SDK.

4. **Open a PR** with the matrix changes. The Merge Gate will re-aggregate and turn
   green once Swift/Zig tests pass.

5. **After the fix PR merges**, rebase any blocked Dependabot PR — it will now inherit
   the corrected matrices and its CI will pass.

## Restore Zig macOS (when Zig supports macOS 26)

Check the Zig release notes or run a quick test in a `workflow_dispatch` run with the
new Zig version. When it succeeds, restore `macos-latest` in
`examples/zig/zig_project_matrix.json` and open a small PR.
