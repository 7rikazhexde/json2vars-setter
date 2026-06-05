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
**Java**) overrides `fetch_versions` and queries an official API instead.

The dynamic-update strategies map onto these fields:

- `stable` → `[stable]`
- `latest` → `[latest]`
- `both` → `[stable, latest]`

> The **example matrices** under `examples/<lang>/` are hand-curated to the version
> format the language's `setup-*` action expects, which may differ from the raw
> fetcher output (e.g. major-only vs full `X.Y.Z`).

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

## Adding another language

See the **"Adding a New Language"** checklist in `CLAUDE.md` for the full set of files to
touch (fetcher, registry, action contract, tests, example, workflow, badges, docs). When
choosing a version source, prefer the language's **canonical GitHub repository tags**;
if those don't cleanly express installable releases (as with Java), use the official
project API and override `fetch_versions`.
