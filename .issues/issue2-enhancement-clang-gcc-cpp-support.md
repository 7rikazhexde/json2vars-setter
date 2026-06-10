# issue2 — enhancement — Clang / GCC (C++ toolchain) support

**Status:** backlog (approved direction, not started)
**Decided:** 2026-06-11

## Problem / request

User asked whether the action can add **Clang** and **C++** as supported
languages (following the Kotlin addition, #571). The action's model is "fetch an
**evolving version stream** from an upstream API and feed it into the CI matrix"
— so the candidates must be evaluated against that model, and "C++" in particular
does not map cleanly.

## Findings (verified 2026-06-11 via `gh api`)

- **Clang (LLVM)** — `llvm/llvm-project`, tags `llvmorg-22.1.7` form.
  - Newest-first ordering holds (`22.1.7, 22.1.6, … 22.1.0`); a non-release
    `llvmorg-23-init` and `-rc3` tags also appear at the top.
  - Stable = `^llvmorg-\d+\.\d+\.\d+$` (rejects `-rc*` and `-init`).
  - Closest existing model: **`haskell.py`** (prefixed `ghc-X.Y.Z` tag, custom
    regex). Likely **no** sort override needed (like `kotlin.py`/`ruby.py`), but
    confirm against a fuller tag page before relying on it.
- **GCC** — `gcc-mirror/gcc`, tags `releases/gcc-16.1.0` form, **but** the tag list
  is mixed: `libgcj-*`, `libf2c-*`, `vendors/ARM/*`, `basepoints/*` are interleaved
  and it is **not** newest-first. Needs: filter to `^releases/gcc-\d+\.\d+\.\d+$`
  **plus** a semantic-version sort override (the `julia`/`haskell`/`ocaml` pattern).
- **"C++" as a language standard** (C++11/14/17/20/23/26) is a **static ISO
  enumeration**, not a fetchable stream — there is nothing to dynamically update or
  cache. Users can already list `[17, 20, 23]` directly in their matrix JSON (the
  action passes any JSON through), so it gains nothing from a fetcher.

## Decision (chosen direction = Option B)

Add **two separate languages: `clang` and `gcc`**, because real C++ CI matrices
vary over the **compiler-version axis** (e.g. `gcc-13, gcc-14, clang-17, clang-18`),
which is exactly the dynamic axis this action serves. The C++ **standard** axis
(`-std=c++NN`) is static (a new standard ~every 3 years) and is best left as a
hand-written list in the user's matrix JSON — so **do not** add a static `cpp`
"standard list" pseudo-language (low value, breaks the fetch-from-API model).

- **Setup side:** no official GitHub setup action for either; use
  **`aminya/setup-cpp`** (supports both gcc and llvm/clang versions) in the example
  and the `*_test.yml` workflow. Pin to a commit SHA per the repo's actions policy.
- **Process:** one language = one PR, following the 9-item "Adding a New Language"
  checklist in CLAUDE.md. Order: **Clang first** (cleaner fetcher), then **GCC**
  (filter + sort override).

## Effort

- Clang: ~Kotlin-sized (clean GitHub-tags fetcher with a custom prefix regex).
- GCC: slightly more (tag filtering + semantic-version `_get_github_tags` override,
  mirroring `julia.py`/`haskell.py`).
- Each: fetcher + registry + matrix_update CLI + action.yml + tests (keep 100%) +
  `examples/<lang>/` + `.github/workflows/<lang>_test.yml` (`uses: ./` two-phase) +
  README/docs badges + a dedicated badge gist (owner-created). No Dependabot entry
  if the example ships no supported build manifest (decide per example).

## Open items to resolve when promoting

- Confirm LLVM stable-tag ordering on a deeper tag page (sort override or not).
- Decide the example project shape (a tiny `.cpp` JSON parser built with
  `setup-cpp` selecting the matrix compiler/version), and which OSes (ubuntu always;
  macos uses Apple clang — pin carefully; windows optional).
- Create the two badge gists (`clang-test-badge.json`, `gcc-test-badge.json`).
