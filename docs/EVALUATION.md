# Evaluation

How the project measures itself, how to read the output, and what is allowed to change a weight.

The short version: **every recommendation is written down with a numeric prediction before the
gameweek is played, and scored against reality afterwards.** Without that, no claim about the
scoring model is falsifiable.

## The loop

```
  weekly run (before deadline)                 next weekly run
 ┌──────────────────────────────┐            ┌──────────────────────────────┐
 │ recommend XI, bench,         │            │ 1. fetch /event/{gw}/live/   │
 │ captain, vice                │            │ 2. replay against the stored │
 │            │                 │            │    prediction                │
 │            ▼                 │            │ 3. report predicted vs actual│
 │ build_prediction(...)        │            │ 4. write gameweek_reviews.md │
 │ record_prediction(...)       │───────────►│ 5. THEN recommend this week  │
 │            │                 │            └──────────────────────────────┘
 │            ▼                 │
 │ records/predictions.jsonl    │
 └──────────────────────────────┘
```

Step 5 comes last on purpose. See [Ordering](#ordering).

## What gets recorded

One JSON object per line in `records/predictions.jsonl`, appended, never rewritten:

| Field | Meaning |
|---|---|
| `event` | Gameweek this prediction is for |
| `starters` / `bench` | Player IDs; bench is in auto-sub priority order |
| `captain` / `vice_captain` | Player IDs |
| `predicted_xi` | Sum of predicted points across the XI |
| `predicted_total` | `predicted_xi` + the captain's score again |
| `predicted` | Per-player predicted score, for error attribution |
| `names` / `positions` | Denormalised so an old line stays readable after transfers |
| `meta` | Free-form: the decision, risk profile, deadline, supersession notes |

`predicted_total` counts the captain twice **because FPL does**. It is directly comparable to the
entry's real gameweek score, with no adjustment needed at comparison time.

Re-running a gameweek appends a second line rather than replacing the first. The reader takes the
latest; the superseded prediction stays visible, because "we changed our mind and why" is data.

## What gets measured

`evaluate_gameweek(event, live)` returns:

| Field | Meaning |
|---|---|
| `predicted_total` / `actual_total` | The headline comparison |
| `error` | `actual − predicted`. **Signed** — positive means we under-predicted |
| `mae` | Mean absolute per-player error across the XI that actually counted |
| `bias` | Mean signed per-player error. Positive = systematically under-predicting |
| `auto_subs` | `(out, in)` pairs that FPL would have applied |
| `captain` / `captain_changed` | Who actually wore the armband |
| `per_player` | Sorted worst-error first, for attribution |

Returns `None` when nothing was recorded for that gameweek. A first run, or a week that was skipped,
reports that honestly rather than inventing a review.

### Two corrections that keep it fair

**Auto-substitutions are applied.** A starter who doesn't play is replaced from the bench under real
FPL rules — keepers swap only with keepers, and the resulting formation must stay legal (1 GK,
3-5 DEF, 2-5 MID, 1-3 FWD). Scoring the blank as a zero would report a worse result than the manager
actually got and make the model look wrong in a way reality wouldn't support.

**The vice-captain armband transfers.** If the captain doesn't play, the vice is doubled.

Both are tested. Skipping them would have been easier and would have made every measurement quietly,
permanently pessimistic.

### What is deliberately not counted

Bench points don't count unless a bench player was auto-subbed on — matching FPL, and matching the
`BENCH_WEIGHT` assumption in the optimizer. A huge bench is not a good week.

## Ordering

**Evaluation runs before this week's recommendation** — step 2 of `/fpl-weekly-review`, before data
is even fetched for the new gameweek.

The failure mode this prevents: reviewing last week *after* deciding this week turns the review into
a justification exercise. Reading "we under-predicted defenders by 1.2 last week" before choosing
this week's defenders is the entire point.

## Reading the numbers

| Observation | Reading |
|---|---|
| `error` large, `bias` near zero | Variance, not model error. FPL gameweeks swing hugely. Do nothing. |
| `bias` consistently positive over 4+ gameweeks | Systematic under-prediction. Evidence for retuning. |
| `mae` high but `bias` near zero | Player-level noise cancelling out. Look at `per_player`, not the total. |
| One player dominating `per_player` error | Usually a minutes/injury miss, not a scoring-weight problem. |

`calibration()` reports `mean_error` **and** `mean_abs_error` together on purpose. A model that is
+10 one week and −10 the next has a mean error of zero and is useless; only the absolute figure
exposes that.

## What is allowed to change a weight

**Measured error, not intuition.** A weight change needs:

1. Bias visible across **several** gameweeks, not one.
2. A stated mechanism — *why* would this term be systematically off?
3. The reasoning written into `records/gameweek_reviews.md`, next to the numbers that justified it.

Single-gameweek results are dominated by variance and are never sufficient. This rule exists because
the alternative — adjusting weights after a bad week — reliably fits noise.

Changes argued from first principles are permitted before any data exists (all of them so far have
been), but they must be logged as such in [PRODUCT_LOG.md](PRODUCT_LOG.md) so they can be revisited
once real evidence arrives.

## Current status

The 2026/27 season has not kicked off. `predictions.jsonl` holds two GW1 predictions — the second
supersedes the first after the ownership-tiebreak and fixture-weighting fixes — and there is nothing
to evaluate against.

**No claim in this repository about model quality has been measured.** Every one is an argument from
first principles. The first real evidence arrives after GW1 (deadline 2026-08-21 17:30 UTC).

## Running it manually

```python
from engine.fetch import get_event_live
from engine.evaluate import evaluate_gameweek, load_predictions, calibration

result = evaluate_gameweek(1, get_event_live(1))
if result is None:
    print("nothing was recorded for that gameweek")
else:
    print(result["predicted_total"], "->", result["actual_total"], f"({result['error']:+})")
    for p in result["per_player"][:3]:
        print(" worst miss:", p["name"], p["predicted"], "->", p["actual"])
```
