# Records

Four append-only logs — the persistent, GitHub-visible memory of this project. **Always append,
never rewrite past entries.** Corrections are appended as new dated entries that reference what
they're correcting, not edits to the original.

| File | What it tracks |
|---|---|
| `records/team_history.md` | Squad snapshots — bank, value, free transfers, chip status, full squad, starting XI/formation, captain/vice. One entry per `/fpl-weekly-review` run. |
| `records/decisions_log.md` | Every transfer decision (including "held, no transfer") with reasoning and the optimizer's hit-adjusted net score. |
| `records/gameweek_reviews.md` | How the *previous* gameweek's held squad actually performed, written at the start of the following week's run — the feedback loop for whether last week's reasoning held up. |
| `records/scoring_backtest.md` | Backtests of `engine/score.py`'s weighting scheme(s) against confirmed-finished gameweek results — see `.claude/docs/SCORING.md`. |

## Rules

- **Read `gameweek_reviews.md` before making a new recommendation** — it's the feedback loop for
  whether last week's reasoning actually held up.
- **Never log a transfer as "made" without explicit user confirmation** that they executed it in
  the live FPL app. A recommendation is not an execution.
- **Never treat a gameweek as final** for logging purposes until `bootstrap['events'][n]['finished']
  == True` (and ideally each fixture's `started`/`finished_provisional` flags checked too). See
  the verification loop in `CLAUDE.md` — this bit the project once (2026-08-24) and the correction
  entries in all three original logs document exactly what went wrong and why.
- **Corrections are appended, not edited in place.** If a past entry turns out wrong, add a new
  entry titled `### Correction — {date}` immediately after it (or as its own dated section)
  explaining what was wrong and what the corrected facts are. This keeps the audit trail honest —
  anyone reading the file later can see both the mistake and the fix.

## Entry templates

```markdown
<!-- team_history.md -->
## GW{N} — {YYYY-MM-DD}
- **Bank:** £{X.X}m | **Squad value:** £{X.X}m | **Free transfers:** {N} | **Chip active:** {none/wildcard/...}
- **Squad:** GK: ..., DEF: ..., MID: ..., FWD: ...
- **Starting XI ({formation}):** ...
- **Captain:** {name} | **Vice:** {name}

<!-- decisions_log.md -->
## GW{N} — {YYYY-MM-DD}
- **Decision:** {Held / Transferred X for Y / Used chip Z}
- **Hit taken:** {0 / -4 / -8}
- **Reasoning:** {form, fixtures, injury news, optimizer's predicted point delta}
- **Optimizer net score (post-hit):** {value}

<!-- gameweek_reviews.md -->
## GW{N} review — {YYYY-MM-DD}
- **Points scored:** {N} | **Rank movement:** {overall rank change}
- **What worked:** ...
- **What didn't:** {e.g. benched player outscored a starter, captaincy miss, injury blindsided a pick}
- **Lesson for next run:** ...

<!-- scoring_backtest.md -->
## GW{N} Backtest — {YYYY-MM-DD}
- **Data:** GW{N} final results, confirmed `finished: True`
- **Test squads:** ...
- **Methodology:** ...
- **Results table:** ...
- **Recommendation:** ...
```
