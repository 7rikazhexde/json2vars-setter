# Showcase: Conditional Matrix (PR vs full)

A runnable example of **choosing the matrix by event**: a small, fast matrix on
**pull requests** for quick feedback, and the **full** cross-OS matrix on the weekly
**schedule** and on manual **dispatch** for thorough coverage. Both come from
json2vars-setter parsing a different JSON file picked at runtime.

This runs in this repository via
[`Sample - Conditional Matrix`](../../../.github/workflows/sample_conditional_matrix.yml);
the green badge in the [README](../../../README.md#sample-workflows) is proof it works.

## How it works

A tiny shell step picks the JSON file based on `github.event_name`, then the action
parses whichever file was chosen — the rest of the workflow is event-agnostic:

```yaml
- name: Pick the matrix profile for this event
  id: pick
  run: |
    if [[ "${{ github.event_name }}" == "pull_request" ]]; then
      echo "json-file=examples/showcase/conditional/matrix.light.json" >> "$GITHUB_OUTPUT"
    else
      echo "json-file=examples/showcase/conditional/matrix.full.json" >> "$GITHUB_OUTPUT"
    fi

- uses: 7rikazhexde/json2vars-setter@v1.9.1
  with:
    json-file: ${{ steps.pick.outputs.json-file }}
```

| Event | File | Matrix |
|-------|------|--------|
| `pull_request` | [`matrix.light.json`](matrix.light.json) | 1 OS × Python 3.13 |
| `schedule` / `workflow_dispatch` | [`matrix.full.json`](matrix.full.json) | 3 OS × Python 3.11–3.13 |

So opening a PR against this sample runs the **light** leg (fast), while the weekly
badge run exercises the **full** matrix.

## Why this is useful

Keep PR feedback fast and cheap, but never lose full cross-platform coverage — the
expensive matrix runs on a schedule (or on demand) instead of on every push. The same
pattern handles "production vs. development" configs (see the *Environment-Specific
Configurations* example in [`docs/examples/ci-cd.md`](../../../docs/examples/ci-cd.md)).

## Adopt it

1. Commit one JSON per profile (e.g. `matrix.light.json`, `matrix.full.json`).
2. Pick the file in a small step keyed on `github.event_name` (or `github.ref`).
3. Feed the chosen file to the action — everything downstream stays the same.
