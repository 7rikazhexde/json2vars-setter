#!/usr/bin/env python3
"""Sync third-party / official GitHub Action version refs in the docs to the workflows.

The docs and README carry ```yaml``` usage examples that reference actions such as
``actions/checkout`` and ``actions/setup-python``. Those references have no automatic
updater:

* Dependabot's ``github-actions`` ecosystem only rewrites the real workflow /
  ``action.yml`` ``uses:`` entries -- it never touches Markdown code blocks.
* ``sync-version-refs.sh`` (run by semantic-release) deliberately syncs *only* the
  ``7rikazhexde/json2vars-setter@vX.Y.Z`` self-reference.

So the example snippets silently drift behind the real workflows. This script closes
that gap by treating the real workflows (``.github/workflows/**``) and ``action.yml`` --
the SHA-pinned source of truth that Dependabot keeps current -- as canonical, and
rewriting the version *tag* of each matching action in the docs to match.

Scope / non-goals:
  * The ``json2vars-setter@vX.Y.Z`` self-reference is never touched here.
  * Actions that appear only in the docs with no real-workflow usage
    (e.g. ``dorny/paths-filter``) are left as-is -- there is no source-of-truth
    version to sync them to.
  * Only the readable tag form (``@vX[.Y[.Z]]``) is rewritten; docs examples use tags,
    not SHA pins, by design (see docs/contributing.md).

Implemented in pure-stdlib Python (not bash) so the pre-commit hook runs identically on
Windows, macOS and Linux.

Usage:
    sync_doc_action_refs.py            # rewrite the docs in place
    sync_doc_action_refs.py --check    # exit 1 if any doc ref is out of date
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SELF_ACTION = "7rikazhexde/json2vars-setter"

# Matches a SHA-pinned action with a trailing "# vX.Y.Z" comment in a workflow:
#   actions/checkout@df4cb1c...0 # v6.0.3
PIN_RE = re.compile(
    r"(?P<repo>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@[0-9a-f]{40} # (?P<tag>v[0-9][0-9.]*)"
)


def _version_key(tag: str) -> tuple[int, ...]:
    """Sort key for a ``vX.Y.Z`` tag (missing components sort low)."""
    return tuple(int(part) for part in tag.lstrip("v").split("."))


def build_source_of_truth() -> dict[str, str]:
    """Map ``owner/repo`` -> highest pinned tag found in the real workflows + action.yml."""
    sources = sorted((REPO_ROOT / ".github" / "workflows").glob("*.yml"))
    action_yml = REPO_ROOT / "action.yml"
    if action_yml.exists():
        sources.append(action_yml)

    want: dict[str, str] = {}
    for path in sources:
        for match in PIN_RE.finditer(path.read_text(encoding="utf-8")):
            repo, tag = match.group("repo"), match.group("tag")
            if repo == SELF_ACTION:
                continue
            current = want.get(repo)
            if current is None or _version_key(tag) > _version_key(current):
                want[repo] = tag
    return want


def doc_files() -> list[Path]:
    """README.md plus every Markdown file under docs/."""
    docs = [REPO_ROOT / "README.md"]
    docs.extend(sorted((REPO_ROOT / "docs").rglob("*.md")))
    return [p for p in docs if p.exists()]


def sync(check_only: bool) -> int:
    want = build_source_of_truth()
    if not want:
        print("No SHA-pinned actions found in workflows/action.yml; nothing to sync.")
        return 0

    patterns = {
        repo: re.compile(rf"(uses: {re.escape(repo)})@v[0-9][0-9.]*") for repo in want
    }

    changed: list[Path] = []
    for path in doc_files():
        original = path.read_text(encoding="utf-8")
        updated = original
        for repo, tag in want.items():
            updated = patterns[repo].sub(rf"\1@{tag}", updated)
        if updated != original:
            changed.append(path)
            if not check_only:
                # newline="\n" keeps the repo's LF policy (files.eol) — without it
                # write_text would emit CRLF on Windows and churn every line.
                path.write_text(updated, encoding="utf-8", newline="\n")

    if not changed:
        print("All documentation action references are up to date.")
        return 0

    rels = [p.relative_to(REPO_ROOT).as_posix() for p in changed]
    if check_only:
        print("Documentation action references are out of date in:")
        print("\n".join(f"  {r}" for r in rels))
        print("Run: python .github/scripts/sync_doc_action_refs.py")
        return 1
    print("Synced documentation action references in:")
    print("\n".join(f"  {r}" for r in rels))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    return sync(check_only="--check" in args)


if __name__ == "__main__":
    raise SystemExit(main())
