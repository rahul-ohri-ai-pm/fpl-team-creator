# Weekly Workflow

The canonical process behind the `/fpl-weekly-review` skill (`.claude/skills/fpl-weekly-review/SKILL.md`).
Don't duplicate this logic ad hoc — invoke the skill, or one of the narrower skills
(`/gw-backtest`, `/injury-check`, `/fixture-run`, `/score-calibrate`) for a sub-task.

## Steps

1. **Confirm the deadline.** Use the `fpl` MCP's gameweek/deadline tool, or `bootstrap['events']`,
   to get the next gameweek's real deadline. Warn up front if running within ~2 hours of it.

2. **Fetch data.** `python engine/fetch.py --team <team_id from config/settings.md>` for the
   entry's bank/value/free-transfers/current picks. Also pull `get_bootstrap()` / `get_fixtures()`
   directly for the full player pool and fixture list (see `.claude/docs/DATA_SOURCES.md`).

3. **Score and optimize.** `engine.score.score_players(bootstrap, fixtures, next_event,
   risk_profile)` then `engine.optimize.recommend_transfers(players, current_squad, bank,
   free_transfers)` for the recommended 0-2 transfers (or "hold"). Run
   `engine.optimize.best_lineup(...)` on the result for starting XI, formation, captain,
   vice-captain. See `.claude/docs/SCORING.md` for the formula and any currently-recommended
   weight-scheme override.

4. **Cross-check with the `fpl` MCP.** Injury/news tools and rival/mini-league comparison for
   context raw stats miss. Only override the optimizer with a concrete, stated reason.

5. **Review last week first.** Read the latest `records/gameweek_reviews.md` entry before
   finalizing this week's call.

6. **Verify before concluding.** Apply the verification loop in `CLAUDE.md` — gameweek-finished
   status, per-player injury/rotation fields, and transfer-execution confirmation — before writing
   anything to `records/` or reporting a conclusion to the user.

7. **Log to records/** (append-only — see `.claude/docs/RECORDS.md` for templates):
   - `records/gameweek_reviews.md` — how the *previous* gameweek's held squad actually scored.
   - `records/decisions_log.md` — this week's decision with reasoning and hit-adjusted net score.
   - `records/team_history.md` — new squad snapshot: bank, value, free transfers, chips, full
     squad, starting XI/formation, captain/vice.

8. **Report back concisely.** Final squad changes (if any), captain/vice, one-line reason each.
   No full player-pool dumps — see `CLAUDE.md`'s "Token discipline."

## Constraints

- Never attempt to execute a transfer against the live FPL account — advisory only.
- If the optimizer errors (e.g. infeasible squad), report the error plainly rather than
  improvising a squad by hand.
- A stale/broken `fpl` MCP should never block steps 2-3 (the core fetch → score → optimize
  pipeline) — MCP is context enrichment, not a dependency.
