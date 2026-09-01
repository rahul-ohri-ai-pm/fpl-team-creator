---
name: gw-backtest
description: Backtest the scoring model's weight scheme(s) against a confirmed-finished gameweek's real results. Use after a gameweek finishes, or when deciding whether to change the live scoring formula.
---

# GW Backtest

Loads only `.claude/docs/SCORING.md`, `records/gameweek_reviews.md`, and `config/settings.md` —
not the full weekly-review context. Run from the repo root.

`engine/weight_scheme_backtest.py` is the reusable simulator behind this skill — it already implements the
precondition check, the reconstruction/caching, and the scoring/comparison math below. Don't
re-derive that math by hand; call the module.

## Preconditions

**Do not run this until the target gameweek is confirmed finished** — `engine.weight_scheme_backtest.check_gameweek_finished(gw)`
(and the CLI, which calls it automatically) already enforces `bootstrap['events'][n]['finished'] == True`
and refuses with a clear error otherwise. This is the verification loop from `CLAUDE.md` applied to
backtesting specifically — a backtest against provisional data produces a garbage recommendation
and has burned this project before.

## Steps

1. **Confirm the gameweek is finished** — handled automatically when you run the CLI below; if it
   refuses, stop and say so, don't work around it.

2. **Identify test squads.** `engine.weight_scheme_backtest.TEST_SQUADS` already has the 3 real GW1 squads
   (the user's real squad plus the other real, previously-recorded squads from
   `records/team_history.md`). For a different gameweek or squad set, build a
   `{name: [player_id, ...]}` dict and pass it as `squads=` to `engine.weight_scheme_backtest.backtest()` — don't
   fabricate synthetic squads unless the user asks for more; real historical squads make the
   backtest meaningful, not just illustrative.

3. **Run the backtest.** For each of the 4 named schemes:
   ```
   python engine/weight_scheme_backtest.py --gw <n> --scheme <baseline|conservative|aggressive|new_signing_aware>
   ```
   This already reconstructs pre-gameweek inputs (caching to `records/snapshots/gw{n}_preseason_reconstruction.json`
   via `load_or_build_snapshot()` — no manual `element-summary` fetching needed for the default test
   squads), picks one shared best-XI per squad from the Baseline scheme's scores so all 4 schemes
   are judged on identical lineups, pulls actual per-player points from `/api/event/{n}/live/` (no
   captain multiplier), and prints RMSE/MAE/bias per scheme. A `--custom '<json>'` flag is
   available for a weight combination outside the 4 named schemes.

4. **Log to `records/scoring_backtest.md`** (append-only, use the template in
   `.claude/docs/RECORDS.md`) with a clear recommendation — which scheme (if any) should replace
   the current live formula, and why.

5. **Report back concisely**: the winning scheme, its RMSE/bias vs. Baseline, and one sentence on
   whether this is enough evidence to act on yet (a single gameweek's backtest is a signal, not a
   verdict — say so if this is the first data point).

## Constraints

- This skill only recommends — applying a scheme change to `engine/score.py` is `/score-calibrate`'s
  job, not this one's.
- Don't dump full per-player prediction tables into the chat; the recommendation and the
  aggregate metrics are what matters. Full detail goes in the logged record, not the summary.
