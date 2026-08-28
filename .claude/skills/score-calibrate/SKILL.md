---
name: score-calibrate
description: Apply a scoring-weight-scheme change to engine/score.py based on backtest evidence, and log the calibration decision. Use after /gw-backtest has produced at least one result recommending a change.
---

# Score Calibrate

Loads `.claude/docs/SCORING.md` and the last 3 entries of `records/gameweek_reviews.md` /
`records/scoring_backtest.md`. Run from the repo root.

## Precondition

**Requires at least one `/gw-backtest` result to cite.** Don't change the live formula on a
hunch — if no backtest has been run yet, run `/gw-backtest` first.

## Steps

1. **Cite the evidence.** Pull the specific backtest result(s) from `records/scoring_backtest.md`
   that justify the change (scheme name, RMSE/MAE/bias, which gameweek(s)).

2. **Check for consistency across gameweeks if possible.** One gameweek's backtest is a signal,
   not a verdict (see `.claude/docs/SCORING.md`'s GW1 entry, which explicitly recommends
   re-confirming at GW2/GW3 before treating a scheme choice as settled). If only one data point
   exists, say so plainly in the calibration entry rather than presenting it as fully proven.

3. **Update `engine/score.py`** to use the recommended scheme's parameters (form multiplier,
   ease range, reliability divisor, injury penalty, ownership weights). Keep the change isolated
   to the weighting constants — don't restructure the function's shape while calibrating.

4. **Update `.claude/docs/SCORING.md`** to reflect which scheme is now live vs. which are
   documented alternatives.

5. **Log to `records/decisions_log.md`** as a "Model calibration" entry: what changed, the
   backtest evidence cited, and the expected impact (project it using the last 3 gameweeks of
   data where possible).

6. **Do not apply retroactively.** The change takes effect starting the *next*
   `/fpl-weekly-review` run — never mid-analysis, and never by re-scoring an already-logged past
   gameweek.

## Constraints

- This skill changes production scoring logic — treat it with the same care as any other code
  change: read `engine/score.py` fully before editing, and check `tests/test_optimize.py` still
  passes afterward (the optimizer's tests use synthetic pools, so they shouldn't break from a
  weighting change, but confirm rather than assume).
- If the user hasn't explicitly asked for the change to be applied (vs. just wanting the
  calibration *proposal*), confirm before editing `engine/score.py` — proposing a number and
  writing it into production code are different levels of commitment.
