# Vertical (arrow-navigable) completion candidate display in PowerShell

**Status:** idea / future improvement — not scheduled.
**Origin:** follow-up to the CLI shell-completion work (PR #552 option+value
completion, PR #553 robust PowerShell completer in `scripts/json2vars-completion.ps1`).

## What we'd want

When completing `json2vars` in PowerShell, show the candidates as a **vertical list**
(one per line) navigable with the ↑/↓ arrow keys, instead of the horizontal grid that
PSReadLine's `MenuComplete` renders.

## Findings (verified 2026-06)

- PSReadLine's `MenuComplete` (bound to `Tab`) is a **horizontal grid**; the column
  count is derived from the terminal width. **There is no PSReadLine option to force a
  single-column / vertical layout.** The only menu-adjacent options are
  `CompletionQueryItems` (threshold before "display all N?") and `PredictionViewStyle`.
- Tested env: PowerShell 7.5.5, PSReadLine 2.3.6.

## Options to get a vertical list

| Approach | Vertical? | Shows our completer's candidates? | Effort | Notes |
|---|---|---|---|---|
| **PSFzf** (`Install-Module PSFzf` + `fzf`) | Yes (fzf list, with filtering) | Yes — hooks `Tab` and feeds existing completions to fzf | Low–Med | Applies shell-wide (git, docker, … all become vertical/fuzzy), not json2vars-only. Recommended if pursued. |
| **`Out-ConsoleGridView`** (`Microsoft.PowerShell.ConsoleGuiTools`) + custom key handler | Yes (in-terminal grid) | Yes — handler collects completions and pipes to the picker | Med | Requires writing a `Set-PSReadLineKeyHandler` that gathers completions and inserts the selection. |
| **PSReadLine ListView** (`-PredictionViewStyle ListView`) | Yes (vertical dropdown) | **No** — ListView is for *predictions* (history / predictor plugins), not Tab completion. Would need a custom `ICommandPredictor` plugin. | High | Not a fit for surfacing our argument completer. |

## Trade-offs / why it's parked

- The cleanest route (PSFzf) is a **shell-wide** UX change and an **extra dependency**
  (`fzf` + `PSFzf`) the user must install — out of scope for a per-tool completer that
  ships in this repo.
- The current `scripts/json2vars-completion.ps1` already gives correct subcommand /
  option / value completion; the horizontal grid is a cosmetic preference.

## Promotion criteria

Promote to a real issue/PR if we decide to **document an opt-in PSFzf recipe** in
`docs/getting-started.md`, or if multiple users ask for vertical/fuzzy completion.
