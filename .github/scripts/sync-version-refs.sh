#!/usr/bin/env bash
# Pin every `uses: 7rikazhexde/json2vars-setter@vX.Y.Z` reference (README, docs,
# example workflows) to the version being released, so usage examples never lag
# behind the latest tag (see the CLAUDE.md "Versioning Rule").
#
# Usage: sync-version-refs.sh <new-version>   (e.g. sync-version-refs.sh 1.3.0)
# Invoked by semantic-release via @semantic-release/exec prepareCmd.
set -euo pipefail

new_version="${1:?usage: sync-version-refs.sh <new-version>}"

mapfile -t files < <(
  grep -rlE "7rikazhexde/json2vars-setter@v[0-9]+\.[0-9]+\.[0-9]+" \
    --include="*.md" --include="*.yml" .
)

if [ "${#files[@]}" -eq 0 ]; then
  echo "No action version references found to sync."
  exit 0
fi

sed -E -i "s#(7rikazhexde/json2vars-setter@v)[0-9]+\.[0-9]+\.[0-9]+#\1${new_version}#g" "${files[@]}"
printf 'Synced action version reference to v%s in:\n%s\n' \
  "${new_version}" "$(printf '  %s\n' "${files[@]}")"
