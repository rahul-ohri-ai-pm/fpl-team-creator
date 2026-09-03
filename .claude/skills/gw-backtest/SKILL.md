---
name: gw-backtest
description: Check the live scoring model's calibration (predicted vs actual) against confirmed-finished gameweeks. Use after a gameweek finishes, or when deciding whether engine/score.py's weights need retuning.
---

# GW Backtest

Loads `.claude/docs/SCORING.md`, `records/gameweek_reviews.md`, and `config/settings.md` — not
the full weekly-review context. Run from the repo root.

`engine/evaluate.py` is the live model's actual calibration tool — `evaluate_gameweek()` replays a
recorded prediction against real results, `calibration()` aggregates the error across every
gameweek that's been evaluated so far. This skill runs that, it doesn't re-derive the math by hand.

(There is a second, older module, `engine/weight_scheme_backtest.py` — it predates the current
xGI-blended formula and only compares 4 historical weight schemes against the original GW1
squads. Its own docstring says to treat its numbers as historical; don't reach for it here.)

## Preconditions

**Only evaluate a gameweek once it's confirmed finished** — check
`bootstrap['events'][n]['finished'] == True` before trusting its points as final. This is the
verification loop from `CLAUDE.md` applied to backtesting: a check against provisional data
produces a garbage calibration read.

## Steps

1. **Confirm which gameweeks are finished.**
   ```python
   from engine.fetch import get_bootstrap
   bootstrap = get_bootstrap()
   ```
   Check `bootstrap['events'][n-1]['finished']` for each candidate gameweek before evaluating it.

2. **Evaluate every finished gameweek that has a recorded prediction.**
   ```python
   from engine.fetch import get_event_live
   from engine.evaluate import evaluate_gameweek, load_predictions, calibration

   evals = []
   for gw in range(1, current_finished_gw + 1):
       result = evaluate_gameweek(gw, get_event_live(gw))
       if result:
           evals.append(result)
       else:
           print(f"GW{gw}: no recorded prediction to evaluate against")
   ```
   `evaluate_gameweek` returns `None` when nothing was recorded for that gameweek (a run that
   skipped step 9 of `/fpl-weekly-review`, or predates this project's calibration loop). Report
   that plainly — don't invent a review for a gameweek with no baseline. For each gameweek that
   *does* evaluate, note `predicted_total` vs `actual_total`, the signed `error`, and the two or
   three players in `per_player` with the largest errors. `error > 0` means the model
   under-predicted that week.

3. **Aggregate.**
   ```python
   cal = calibration(evaluations=evals)
   ```
   `cal["gameweeks"]` is how many data points this rests on — **say so explicitly if it's 1 or 2**;
   one or two gameweeks is a signal, not a verdict, and this project has been burned before by
   acting on single-gameweek evidence (see the GW2 Sangaré/De Cuyper decision, or the GW1
   weight-scheme backtest's own re-confirm caveat). `cal["mean_error"]` is the number that matters:
   persistent, same-direction error across several gameweeks is what actually justifies a
   `/score-calibrate` change — a single outlier week doesn't.

4. **Log a narrative entry to `records/gameweek_reviews.md`** (append-only) when there's something
   new to report — the raw numbers already persist in `records/predictions.jsonl`, so this is
   about capturing the *reasoning* (biggest misses, whether a bias looks systematic yet), not
   re-duplicating the machine-readable log.

5. **Report back concisely**: predicted vs actual per evaluated gameweek, the aggregate
   `mean_error`/`mean_abs_error`, and one sentence on whether there's enough evidence yet to act on
   (name the gameweek count).

## Related, separate tool

`engine/ceiling_signal_backtest.py` + `records/ceiling_signal_backtest.md` test a different
question — whether per-gameweek signals like `threat`/`ict_index` predict *next*-gameweek points
better than a player's own recent points do (a possible gap in `score.py`'s `form` term). Don't
conflate the two: this skill checks the live model's overall calibration; that one probes for a
specific missing input. Run it separately (`python engine/ceiling_signal_backtest.py --from <n>
--to <n+1>`) when there's a new gameweek transition to test.

## Constraints

- This skill only measures and reports — applying a weight change to `engine/score.py` is
  `/score-calibrate`'s job, not this one's.
- Don't dump full per-player prediction tables into the chat; the aggregate numbers and the
  biggest misses are what matters. Full detail belongs in `records/predictions.jsonl`, not the
  chat summary.
