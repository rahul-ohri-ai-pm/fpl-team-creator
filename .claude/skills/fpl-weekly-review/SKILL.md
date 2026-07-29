---
name: fpl-weekly-review
description: Weekly FPL squad check-in - fetches live data, scores players, runs the transfer optimizer, cross-checks qualitative context via the fpl MCP server, and logs the decision to records/. Use before a gameweek deadline, or whenever asked to check, update, or review the FPL team.
---

# FPL Weekly Review

Run this from the repo root. Read `config/settings.md` first for the team ID, risk profile, and
hit tolerance - don't hardcode any of these.

## Steps

1. **Confirm the deadline.** Use the `fpl` MCP server's gameweek/deadline tool or resource to get
   the next gameweek's real deadline. If running within ~2 hours of it, warn the user up front -
   don't silently proceed as if there's plenty of time.

2. **Fetch data.**
   ```
   python engine/fetch.py --team <team_id from config/settings.md>
   ```
   This returns the current gameweek, and the entry's bank/value/free-transfers/current picks.
   Also fetch bootstrap-static and fixtures (fetch.py's `get_bootstrap()` / `get_fixtures()`) for
   the full player pool - import and call these directly in a short script if you need the raw
   JSON rather than just the summarized CLI output.

3. **Score and optimize.** Using `engine.score.score_players(bootstrap, fixtures, next_event,
   risk_profile)` and `engine.optimize.recommend_transfers(players, current_squad, bank,
   free_transfers)`, get the recommended 0-2 transfers (or "hold"). Then run
   `engine.optimize.best_lineup(...)` on the resulting squad for the starting XI, formation,
   captain, and vice-captain.

4. **Cross-check with the `fpl` MCP.** Before finalizing, check its injury/news tools and any
   rival/mini-league comparison for context the raw stats wouldn't catch (e.g. a press-conference
   knock, a fixture postponement). Adjust the recommendation only if there's a concrete reason to
   override the optimizer - state that reason explicitly if you do.

5. **Review last week first.** Read the most recent entry in `records/gameweek_reviews.md` before
   finalizing this week's call - it's the feedback loop for whether last week's reasoning held up.

6. **Log to records/** (append, never rewrite past entries):
   - `records/gameweek_reviews.md` - how the *previous* gameweek's held squad actually scored.
   - `records/decisions_log.md` - this week's decision (hold, or the specific transfer(s)) with
     the reasoning and the optimizer's net (hit-adjusted) score.
   - `records/team_history.md` - the new squad snapshot: bank, value, free transfers, chip status,
     full squad, starting XI/formation, captain/vice.

7. **Report back concisely.** Final squad changes (if any), captain/vice, and a one-line reason
   each. Do not dump the full player pool or raw stats table into the chat - that defeats the
   point of running this as a lean weekly check-in.

## Constraints

- Never attempt to execute a transfer against the live FPL account - this is advisory only.
- If the optimizer errors (e.g. infeasible squad), report the error plainly rather than
  improvising a squad by hand.
