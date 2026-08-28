---
name: gw-backtest
description: Backtest the scoring model's weight scheme(s) against a confirmed-finished gameweek's real results. Use after a gameweek finishes, or when deciding whether to change the live scoring formula.
---

# GW Backtest

Loads only `.claude/docs/SCORING.md`, `records/gameweek_reviews.md`, and `config/settings.md` —
not the full weekly-review context. Run from the repo root.

## Preconditions

**Do not run this until the target gameweek is confirmed finished**: check
`bootstrap['events'][n]['finished'] == True` (and `data_checked == True` if available) before
fetching anything else. This is the verification loop from `CLAUDE.md` applied to backtesting
specifically — a backtest against provisional data produces a garbage recommendation and has
burned this project before.

## Steps

1. **Confirm the gameweek is finished** (see above). If not, stop and say so — don't backtest
   provisional data.

2. **Identify test squads.** Default to 3: the user's real squad for that gameweek (from
   `/api/entry/{team_id}/event/{n}/picks/`) plus any other real, previously-recorded squads in
   `records/team_history.md` (don't fabricate synthetic squads unless the user asks for more —
   real historical squads make the backtest meaningful, not just illustrative).

3. **Reconstruct pre-gameweek inputs.** If a pre-gameweek `bootstrap-static` snapshot exists
   under `records/snapshots/`, use it directly. Otherwise (as with GW1), reconstruct from
   `/api/element-summary/{id}/`'s `history_past` for the relevant prior season — see the
   methodology section in `.claude/docs/SCORING.md`. Note explicitly in the output which path was
   used; a reconstruction is an approximation, not an exact replay.

4. **Score every player in each test squad under each of the 4 schemes** (definitions in
   `.claude/docs/SCORING.md`). Pick one shared best-XI per squad using the Baseline scheme's
   scores, so all 4 schemes are judged on identical lineups.

5. **Compare to actual.** Pull real per-player points from `/api/event/{n}/live/` (no captain
   multiplier — the model doesn't pick a captain). Compute RMSE, MAE, and bias per scheme across
   all test squads.

6. **Log to `records/scoring_backtest.md`** (append-only, use the template in
   `.claude/docs/RECORDS.md`) with a clear recommendation — which scheme (if any) should replace
   the current live formula, and why.

7. **Report back concisely**: the winning scheme, its RMSE/bias vs. Baseline, and one sentence on
   whether this is enough evidence to act on yet (a single gameweek's backtest is a signal, not a
   verdict — say so if this is the first data point).

## Constraints

- This skill only recommends — applying a scheme change to `engine/score.py` is `/score-calibrate`'s
  job, not this one's.
- Don't dump full per-player prediction tables into the chat; the recommendation and the
  aggregate metrics are what matters. Full detail goes in the logged record, not the summary.
