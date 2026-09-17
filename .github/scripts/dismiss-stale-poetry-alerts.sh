#!/usr/bin/env bash
# GitHub's dependency graph keeps a stale snapshot of poetry.lock (removed in the
# Poetry->uv migration, commit 5157d99, 2026-06-01) and keeps matching NEW advisories
# against it forever - so Dependabot periodically opens security alerts against a
# manifest that no longer exists (see alerts #57, #63, #67, #72, #76, #77). There is
# no public-repo API/UI to purge a stale manifest from the graph, so this dismisses
# each new alert automatically, with a safety check that poetry.lock is genuinely
# absent before touching anything.
#
# Anything this script is NOT certain about (any other open alert, or a poetry.lock
# alert while poetry.lock unexpectedly exists) is left untouched and instead reported
# in a tracking issue, so it surfaces for a human/Claude Code review rather than being
# silently auto-resolved.
#
# Usage: dismiss-stale-poetry-alerts.sh
# Requires: gh CLI authenticated with a token that has Dependabot alerts write access
#           (GH_TOKEN / GH_REPO env vars, as set by gh auth or the workflow).
set -euo pipefail

tracking_title="Dependabot alerts need manual review"

poetry_lock_exists="false"
if git ls-files --error-unmatch poetry.lock >/dev/null 2>&1; then
  poetry_lock_exists="true"
  echo "poetry.lock exists in the repo - will NOT auto-dismiss any poetry.lock alert (would be a real alert)." >&2
fi

comment='poetry.lock removed in Poetry->uv migration (5157d99, 2026-06-01). Stale orphan manifest confirmed via GraphQL (dead blobPath). Real dep (uv.lock) already patched or not a real dep. No API/UI exists to purge a stale manifest on public repos. See also #57.'

mapfile -t open_alerts < <(
  gh api repos/"${GH_REPO}"/dependabot/alerts --paginate \
    --jq '.[] | select(.state == "open") | [.number, .dependency.manifest_path] | @tsv'
)

dismissed=()
needs_review=()

for line in "${open_alerts[@]:-}"; do
  [ -z "${line}" ] && continue
  number="${line%%$'\t'*}"
  manifest="${line#*$'\t'}"

  if [ "${manifest}" = "poetry.lock" ] && [ "${poetry_lock_exists}" = "false" ]; then
    echo "Dismissing alert #${number} (poetry.lock, confirmed stale)"
    gh api --method PATCH "repos/${GH_REPO}/dependabot/alerts/${number}" \
      -f state="dismissed" \
      -f dismissed_reason="inaccurate" \
      -f "dismissed_comment=${comment}" \
      --jq '{number, state, dismissed_reason}'
    dismissed+=("${number}")
  else
    needs_review+=("${number}")
  fi
done

if [ "${#dismissed[@]}" -gt 0 ]; then
  printf 'Dismissed %d stale poetry.lock alert(s): %s\n' \
    "${#dismissed[@]}" "$(printf '#%s ' "${dismissed[@]}")"
else
  echo "No open poetry.lock alerts to dismiss."
fi

# Escalate anything left over (not the confirmed-safe poetry.lock case) via a single,
# reused tracking issue - created if needed, updated in place on later runs, and
# closed automatically once nothing is left to review.
existing_issue="$(
  gh issue list --state open --search "in:title \"${tracking_title}\"" \
    --json number --jq '.[0].number // empty'
)"

if [ "${#needs_review[@]}" -gt 0 ]; then
  body="Dependabot alerts that dismiss-stale-poetry-alerts.sh could NOT auto-resolve (not the confirmed-stale poetry.lock case) - please review manually or ask Claude Code to look:"$'\n\n'
  for number in "${needs_review[@]}"; do
    body+="- #${number}: https://github.com/${GH_REPO}/security/dependabot/${number}"$'\n'
  done
  body+=$'\n'"_Auto-updated by \`.github/workflows/dismiss-stale-poetry-alerts.yml\` - do not edit the title._"

  if [ -n "${existing_issue}" ]; then
    echo "Updating existing tracking issue #${existing_issue}"
    gh issue edit "${existing_issue}" --body "${body}"
  else
    echo "Opening tracking issue for ${#needs_review[@]} alert(s) needing review"
    gh label create "security" --color "d73a4a" \
      --description "Security alerts and hardening" --force >/dev/null 2>&1 || true
    gh issue create --title "${tracking_title}" --body "${body}" --label "security"
  fi
else
  if [ -n "${existing_issue}" ]; then
    echo "Closing tracking issue #${existing_issue} - nothing left to review"
    gh issue close "${existing_issue}" --comment "All previously-listed alerts are resolved or dismissed."
  fi
fi
