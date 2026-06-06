# Version Sources

This page documents, for every supported language, **where json2vars-setter fetches
versions from**, which candidate sources were considered, **why** the chosen source was
picked, and the language-specific characteristics that follow from it.

## How fetching works

Each language has a fetcher under `json2vars_setter/version/fetchers/`. Most fetchers
extend `BaseVersionFetcher`, which reads **Git tags from a GitHub repository** via the
GitHub REST API, filters them to stable releases, and derives:

- **`latest`** — the most recent stable release
- **`stable`** — a "known-good" release (usually the previous minor/major line)
- **`recent_releases`** — the most recent stable releases (used by the cache feature)

A language whose versions are not cleanly expressed as a single repo's tags (currently
**Java**, **Dart**, and **Swift**) overrides `fetch_versions` and queries an official
API instead.

The dynamic-update strategies map onto these fields:

- `stable` → `[stable]`
- `latest` → `[latest]`
- `both` → `[stable, latest]`

> The **example matrices** under `examples/<lang>/` are hand-curated to the version
> format the language's `setup-*` action expects, which may differ from the raw
> fetcher output (e.g. major-only vs full `X.Y.Z`).

## What the example projects are for

Each `examples/<lang>/` project is a small, self-contained example that the matching
`<lang>_test.yml` workflow runs across the matrix — demonstrating json2vars-setter
driving the language's `setup-*` action end to end.

They are examples only: their exact contents are illustrative and may change. In
particular they are **not** a check that a specific version is installable — that is the
`setup-*` action's responsibility, and its supported-version list can lag the upstream
source the fetcher reads (see the Swift caveat below).

## Summary

| Language | Source | `latest` | `stable` | setup action |
|----------|--------|----------|----------|--------------|
| Python | `python/cpython` tags | newest stable | previous minor | `actions/setup-python` |
| Node.js | `nodejs/node` tags + LTS metadata | newest stable | newest **LTS** | `actions/setup-node` |
| Ruby | `ruby/ruby` tags | newest stable | previous minor | `ruby/setup-ruby` |
| Go | `golang/go` tags | newest stable | previous minor | `actions/setup-go` |
| Rust | `rust-lang/rust` tags + channel info | newest stable | previous minor | `dtolnay`/rustup toolchain |
| PHP | `php/php-src` tags | newest stable | previous minor | `shivammathur/setup-php` |
| .NET (C#) | `dotnet/sdk` tags | newest SDK | previous **major** | `actions/setup-dotnet` |
| Java | **Adoptium API** | newest **feature** | newest **LTS** | `actions/setup-java` |
| Deno | `denoland/deno` tags | newest stable | previous minor | `denoland/setup-deno` |
| Bun | `oven-sh/bun` tags | newest stable | previous minor | `oven-sh/setup-bun` |
| Zig | `ziglang/zig` tags | newest stable | previous minor | `mlugg/setup-zig` |
| Elixir | `elixir-lang/elixir` tags | newest stable | previous minor | `erlef/setup-beam` |
| Dart | **Dart release archive** | newest stable | previous minor | `dart-lang/setup-dart` |
| Swift | **swift.org install API** | newest stable | previous minor | `swift-actions/setup-swift` |
| Julia | `JuliaLang/julia` tags (sorted) | newest stable | previous minor line | `julia-actions/setup-julia` |

## Per-language details

### Python — `python/cpython`

- **Source:** tags of the official CPython repository (`vX.Y.Z`).
- **Why:** CPython is the reference implementation; its tags are the canonical version
  list. Direct fit for the GitHub-tags fetcher.
- **Characteristics:** pre-releases (`a`/`b`/`rc`) are excluded; `stable` is the previous
  minor line of `latest`.

### Node.js — `nodejs/node`

- **Source:** tags of the official Node.js repository, **plus LTS metadata** to identify
  Long-Term-Support lines.
- **Candidates:** plain tags only (rejected — Node's notion of "stable" is the current
  **LTS**, which tags alone don't convey).
- **Why:** Node users target LTS releases, so `stable` is resolved to the most recent LTS
  rather than simply the previous minor.

### Ruby — `ruby/ruby`

- **Source:** tags of the official Ruby repository (underscore form, e.g. `v3_4_2`).
- **Why:** canonical source; clean fit for the GitHub-tags fetcher.
- **Characteristics:** pre-release suffixes are excluded; `stable` is the previous minor.

### Go — `golang/go`

- **Source:** tags of the official Go repository (`goX.Y.Z`).
- **Why:** canonical source; clean fit.
- **Characteristics:** the `go` prefix is stripped; `rc`/`beta` builds are excluded;
  `stable` is the previous minor.

### Rust — `rust-lang/rust`

- **Source:** tags of the official Rust repository (`1.XX.Y`), **plus channel info** from
  `static.rust-lang.org`.
- **Why:** canonical source; channel info documents the `stable`/`beta`/`nightly`
  availability alongside the concrete version.

### PHP — `php/php-src`

- **Source:** tags of the official PHP source repository (`php-X.Y.Z`).
- **Candidates:** none better — there is no official "setup-php" from GitHub, but the
  source repo's tags are authoritative for versions.
- **Why:** clean fit for the GitHub-tags fetcher.
- **Characteristics:** only tags matching `php-X.Y.Z` exactly are kept (`...RC1`,
  `...beta1`, `...alpha1`, and unrelated tags like `yaf-*` are excluded); `stable` is the
  previous minor. The consumer side uses `shivammathur/setup-php` (the de-facto standard,
  since no official action exists).

### .NET (C#) — `dotnet/sdk`

- **Source:** tags of the official .NET SDK repository (`vX.Y.Z`, e.g. `v8.0.100`).
- **Candidates considered:**
    - **`dotnet/sdk` tags** (chosen) — consistent with the other languages' GitHub-tags
      approach.
    - **`releases-index.json`** release metadata (not chosen) — richer (LTS/STS, support
      phase, per-channel latest), but diverges from the common fetcher pattern.
- **Why:** keeps .NET on the same simple, consistent GitHub-tags mechanism as the other
  languages.
- **Characteristics:** the SDK **minor is always `0`**, so the meaningful release line is
  the **major** (8.0, 9.0, 10.0). `latest` is the newest SDK; `stable` is the newest SDK
  of the **previous major**. `preview`/`rc` tags are excluded. Example matrices use the
  channel form (`"8.0"`, `"9.0"`) that `actions/setup-dotnet` accepts.

### Java — Adoptium API

- **Source:** the **Adoptium API** `GET /v3/info/available_releases`.
- **Candidates considered:**
    - **`openjdk/jdk` tags** (rejected) — that repository carries only **early-access
      builds of the in-development release** (e.g. `jdk-28+0`); GA and LTS lines live in
      separate update repositories, so a single repo's tags cannot represent stable Java
      versions.
    - **`openjdk/jdkXXu` update repos** (rejected) — would require juggling many
      repositories and still mixes build metadata.
    - **Adoptium API** (chosen) — a single authoritative endpoint that reports
      `available_releases`, `available_lts_releases`, `most_recent_feature_release`, and
      `most_recent_lts`.
- **Why:** it is the only clean, single-source way to enumerate real, installable Java
  versions and to distinguish LTS from feature releases.
- **Characteristics:** this is the **only fetcher that does not use GitHub tags** — it
  overrides `fetch_versions`. `latest` = most recent **feature** release (e.g. `26`);
  `stable` = most recent **LTS** (e.g. `25`); `recent_releases` = the available **LTS**
  releases, newest first. The consumer side uses the official `actions/setup-java` with
  the `temurin` distribution; example matrices use major versions (`"11"`, `"17"`,
  `"21"`).

### Deno — `denoland/deno`

- **Source:** tags of the official Deno repository (`vX.Y.Z`).
- **Why:** Deno publishes clean, stable-only release tags (no pre-release noise), so it is
  a direct fit for the GitHub-tags fetcher.
- **Characteristics:** the `v` prefix is stripped; `stable` is the previous minor of
  `latest`. Example matrices use the channel form (`"v1.x"`, `"v2.x"`) that
  `denoland/setup-deno` accepts.

### Bun — `oven-sh/bun`

- **Source:** tags of the official Bun repository (`bun-vX.Y.Z`).
- **Why:** Bun's release tags are a clean, direct fit for the GitHub-tags fetcher.
- **Characteristics:** only tags matching `bun-vX.Y.Z` are kept (`canary` and the legacy
  `v0.x` tags are excluded); the `bun-v` prefix is stripped; `stable` is the previous
  minor of `latest`. Example matrices use the form (`"1.2.x"`, `"1.3.x"`) that
  `oven-sh/setup-bun` accepts.

### Zig — `ziglang/zig`

- **Source:** tags of the official Zig repository (plain `X.Y.Z`).
- **Why:** Zig's stable release tags are bare semantic versions — a clean, direct
  fit for the GitHub-tags fetcher.
- **Characteristics:** only tags matching `X.Y.Z` are kept (`master` and
  `X.Y.Z-dev.*` nightly builds are excluded); Zig is still pre-1.0, so `stable` is
  the previous **minor** (second component) of `latest`. Example matrices use the
  exact form (`"0.14.1"`, `"0.15.2"`) that `mlugg/setup-zig` accepts.

### Elixir — `elixir-lang/elixir`

- **Source:** tags of the official Elixir repository (`vX.Y.Z`).
- **Why:** Elixir's release tags are a clean, direct fit for the GitHub-tags fetcher.
- **Characteristics:** only tags matching `vX.Y.Z` are kept (release candidates
  `vX.Y.Z-rc.N` and the moving `vX.Y-latest` tags are excluded); the `v` prefix is
  stripped; `stable` is the previous minor of `latest`. Example matrices use the form
  (`"1.18"`, `"1.19"`) that `erlef/setup-beam` accepts. `setup-beam` also requires an
  Erlang/OTP version, which the example workflow pins separately.

### Dart — Dart release archive

- **Source:** the Dart SDK release archive on Google Cloud Storage
  (`channels/stable/release/`), listed via the GCS JSON API.
- **Why:** the `dart-lang/sdk` GitHub tags are dominated by per-package tags
  (`analyzer-*`, `meta-*`) with the plain SDK version tags buried, so — like Java —
  Dart uses a dedicated source rather than the GitHub-tags fetcher.
- **Characteristics:** release "folders" matching `X.Y.Z` are extracted and sorted
  **numerically** (the listing is lexicographic, so `3.9.x` sorts after `3.12.x`);
  `latest` is the newest version and `stable` is the previous minor. Example matrices
  use the form (`"3.11.6"`, `"3.12.1"`) that `dart-lang/setup-dart` accepts.

### Swift — swift.org install API

- **Source:** the official swift.org install API
  (`https://www.swift.org/api/v1/install/releases.json`).
- **Why:** the `apple/swift` GitHub tags are dominated by `DEVELOPMENT-SNAPSHOT`
  tags and the `swift-X.Y.Z-RELEASE` tags do not appear within the first pages of
  the tags listing, so — like Java and Dart — Swift uses a dedicated source.
- **Characteristics:** release `name`s matching `X.Y[.Z]` are kept and sorted
  **numerically**; `latest` is the newest and `stable` is the previous minor. Example
  matrices use the form (`"6.1.3"`, `"6.2.1"`) that `swift-actions/setup-swift`
  accepts, and target `ubuntu`/`macos` (Swift's first-class CI platforms).
- **Caveat:** `swift-actions/setup-swift` installs from its own bundled list of known
  Swift versions, which can lag behind the newest swift.org release. When using the
  dynamic update, pin to versions the action supports if the very latest is not yet
  available there.

### Julia — `JuliaLang/julia`

- **Source:** `JuliaLang/julia` GitHub tags.
- **Characteristics:** stable tags look like `vX.Y.Z`; pre-releases (`-rc`, `-beta`,
  `-alpha`) are excluded. Unlike most repositories, the JuliaLang/julia tag API is **not
  reliably newest-first**, so `julia.py` overrides `_get_github_tags` to sort the stable
  tags **numerically** by semantic version before selecting; `latest` is the newest and
  `stable` is the newest release from the previous minor line. Example matrices use the
  short form (`"1.10"`, `"1.11"`) that `julia-actions/setup-julia` accepts (it also
  accepts an exact `X.Y.Z` or aliases such as `lts` / `nightly`).

## Adding another language

See the **"Adding a New Language"** checklist in `CLAUDE.md` for the full set of files to
touch (fetcher, registry, action contract, tests, example, workflow, badges, docs). When
choosing a version source, prefer the language's **canonical GitHub repository tags**;
if those don't cleanly express installable releases (as with Java), use the official
project API and override `fetch_versions`.
