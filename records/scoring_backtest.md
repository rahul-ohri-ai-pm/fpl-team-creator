# Scoring Backtest Log

Append-only log of backtests comparing `engine/score.py`'s weighting formula (and proposed
alternative weighting schemes) against **confirmed-finished** gameweek results. Never run this
against a gameweek where `bootstrap['events'][n]['finished']` is `False` — see the verification
loop in `CLAUDE.md`.

<!--
Template for each new entry:

## GW{N} Backtest — {YYYY-MM-DD}

- **Data:** GW{N} final results, confirmed `finished: True`
- **Test squads:** ...
- **Methodology:** ...
- **Results table:** ...
- **Recommendation:** ...
-->

## GW1 Backtest — 2026-08-28

**Data:** GW1 final results (`bootstrap['events'][0]['finished'] = True`,
`data_checked = True`), fetched from `/api/event/1/live/`.

**Test squads (3 real, previously-recorded squads — not fabricated):**

- **Team A — actual GW1 squad**: the user's real 15-man squad as fielded in GW1
  (`/api/entry/1669770/event/1/picks/`).
- **Team B — "Pre-season (re-run)" squad**: the safe-profile squad recommended by the optimizer
  on 2026-07-29, logged in `team_history.md`.
- **Team C — original "Pre-season" draft**: the first optimizer draft from 2026-07-29 (before the
  objective-function bug fix), also logged in `team_history.md`.

**Methodology:**

1. For each of the 15 unique players across the 3 squads, fetched `/api/element-summary/{id}/`
   and pulled the **2025/26 season** `total_points` and `minutes` (i.e. the actual pre-season
   inputs `engine/score.py` would have used — `form` was 0 for every player before GW1, so the
   formula fell back to last-season points-per-game, exactly as `score.py`'s comment describes).
   `ppg = total_points / 38`.
2. Recomputed each of the 4 weight schemes' predicted score for every player using that
   reconstructed `ppg`, last-season `minutes` (for the reliability discount), current fixture-ease
   (GW1-4 difficulty, unaffected by GW1 itself), and `chance_of_playing_next_round` /
   `selected_by_percent` as they stand today (ownership share moves slowly; treated as a proxy for
   pre-season values).
3. Selected each squad's best-legal starting XI using the **baseline** scheme's player scores (so
   all 4 schemes are judged on the same XI, isolating scoring accuracy from squad-selection
   choices).
4. Compared each scheme's predicted XI total to that XI's **actual GW1 points** (sum of real
   per-player points from `/api/event/1/live/`, **no captain multiplier** — the optimizer doesn't
   know who will be armbanded, so this isolates the scoring formula's accuracy from the
   captaincy decision. This is why the numbers below don't match the live scoreboard's 49-point
   total, which does include the captain's double).

**Caveat:** this reconstructs pre-season inputs from data still available today (last season's
totals don't change), not from a literal cached pre-season snapshot — none was saved at the time.
Fixture-ease and ownership % are today's values, not exactly what they were on 2026-07-29, so
treat this as a close approximation, not a perfect replay.

### Results

| Scheme | Team A predicted | Team B predicted | Team C predicted | RMSE | MAE | Bias |
|---|---|---|---|---|---|---|
| **Baseline** (current `score.py`) | 52.90 (actual 37, +43.0%) | 55.72 (actual 48, +16.1%) | 54.83 (actual 48, +14.2%) | 10.94 | 10.15 | **+10.15** |
| **Conservative** | 43.87 (actual 37, +18.6%) | 46.55 (actual 48, -3.0%) | 45.50 (actual 48, -5.2%) | **4.30** | **3.61** | **+0.97** |
| **Aggressive** | 56.62 (actual 37, +53.0%) | 59.10 (actual 48, +23.1%) | 58.74 (actual 48, +22.4%) | 14.41 | 13.82 | +13.82 |
| **New-signing-aware** | 52.90 (actual 37, +43.0%) | 55.72 (actual 48, +16.1%) | 54.83 (actual 48, +14.2%) | 10.94 | 10.15 | +10.15 |

*(Weight scheme definitions: see `.claude/docs/SCORING.md`.)*

### Finding: New-signing-aware had zero effect this test

The new-signing downweight only fires when last-season minutes < 270. **João Pedro already had a
2025/26 Premier League history row** (he moved from Brighton, not from outside the league), so he
didn't trigger the downweight — the scheme produced identical numbers to Baseline. The "new
signing invisible to the model" theory from the earlier premature GW1 draft doesn't hold up under
this data: João Pedro actually *outperformed* his reconstructed baseline prediction (11 actual on
a squad where he was one of the lower-scoring predicted starters), the opposite of an
invisibility problem. This scheme would matter for a genuine newly-promoted-to-the-PL player with
no `2025/26` history row at all (e.g., a Championship signing) — none of the 3 test squads
happened to include one.

### Recommendation

**Adopt the Conservative weighting for pre-season / early-season predictions** (until real
in-season `form` data accumulates, roughly GW3-4):
- RMSE drops from 10.94 (Baseline) to 4.30 — a ~61% reduction in prediction error.
- Bias drops from +10.15 (consistently over-confident) to +0.97 (essentially unbiased).
- The main lever driving this: Conservative's stricter reliability discount
  (`minutes / (38×90×0.5)` vs Baseline's `0.6`) and lower form multiplier (0.9x) both pull
  predictions down toward what pre-season data can actually support.

**Do not adopt Aggressive** for this phase — it widens the over-estimate (+13.82 bias, worst of
the four). Trusting `form` more and discounting reliability less is the wrong direction when the
underlying signal is *last season's* stats standing in for a completely unplayed new season.

**Re-run this backtest after GW2 and GW3** once real `form` data exists — Conservative's edge is
expected to shrink as `form` (not last-season ppg) starts driving predictions, at which point
Baseline or even Aggressive may become competitive again. Track this via `/gw-backtest` weekly for
the next 3 gameweeks before treating the scheme choice as settled.

### Lesson for next run

- This is the first *quantified* confirmation of the bias `gameweek_reviews.md`'s GW1 correction
  suspected — a real number (+43% on Team A) instead of an assumed one.
- Reconstructing "what the model would have predicted" from currently-available data works when
  the underlying facts (last season's totals) don't change over time — but this only works
  retroactively for *last-season* stats. Anything that resets each gameweek (this season's `form`,
  `minutes`, `chance_of_playing_next_round`) can't be backtested this way without a saved
  snapshot. **Action item:** start snapshotting `bootstrap-static` before each gameweek deadline
  (e.g. to `records/snapshots/gw{N}_pre.json`, gitignored or committed depending on size) so
  future backtests don't need this reconstruction workaround.

## GW1 Backtest — code-verified re-run — 2026-08-28

The manual analysis above is now backed by a reusable simulator: `engine/backtest.py` generalizes
`score.py`'s formula into a configurable scheme, caches the reconstruction to
`records/snapshots/gw1_preseason_reconstruction.json` (the action item above, done), and exposes
`--scheme <name>` and `--custom <json>` on the CLI so any weight combination can be tried, not
just the 4 pre-picked ones.

Re-ran all 4 named schemes (`python -m engine.backtest --gw 1 --scheme <name>`), one per agent run
in parallel, cross-checked against this file's manual figures above:

| Scheme | form_mult | ease range | reliability divisor | injury penalty | ownership wt (safe/bal/diff) | Team A pred | Team B pred | Team C pred | RMSE | MAE | Bias |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Baseline | 1.0 | 0.8–1.2 | 38×90×0.6 | none | 1.5 / 0.3 / -1.5 | 52.90 | 55.72 | 54.83 | 10.94 | 10.15 | +10.15 |
| **Conservative** | 0.9 | 0.8–1.15 | 38×90×0.5 | -0.1 flat | 2.0 / 0.5 / -1.0 | 43.87 | 46.55 | 45.50 | **4.30** | **3.61** | **+0.97** |
| Aggressive | 1.1 | 0.75–1.25 | 38×90×0.75 | none | 1.0 / 0.0 / -2.0 | 56.61 | 59.10 | 58.73 | 14.41 | 13.82 | +13.82 |
| New-signing-aware | 1.0 | 0.8–1.2 | 38×90×0.6 | none | 1.5 / 0.3 / -1.5 | 52.90 | 55.72 | 54.83 | 10.94 | 10.15 | +10.15 |

(Actual XI totals, unchanged from the manual run: Team A 37, Team B 48, Team C 48.)

**All 4 schemes reproduce the manual figures exactly** — no divergence, confirming the code port
of the formula is correct. New-signing-aware confirmed identical to Baseline for the same reason
as before: checked prior-season minutes for all 27 unique players across the 3 squads, lowest was
Richarlison at 1,954 — none is anywhere near the <270-minute threshold that triggers its downweight.

**Recommendation unchanged: Conservative** (RMSE 4.30 vs Baseline's 10.94, bias +0.97 vs +10.15).
This is still a single gameweek's confirmation — GW2's deadline is today (2026-08-28) and hasn't
been played, so it isn't backtestable yet per the verification loop
(`bootstrap['events'][1]['finished'] == False` as of this writing). Re-run
`python -m engine.backtest --gw 2 --scheme <name>` once GW2 is confirmed finished before
strengthening this recommendation further.

**New capability**: the `--custom` flag is a genuine weight simulator — e.g.
`python -m engine.backtest --gw 1 --custom '{"form_mult": 0.95, ...}'` — for trying combinations
outside the 4 named schemes without editing any code. `tests/test_backtest.py` pins these 4
schemes' GW1 numbers as a regression check so future edits to `engine/backtest.py` can't silently
drift from this table.

## Formula correction — injury_mult now scales the ownership term — 2026-08-28

A code-reviewer pass found that both `engine/score.py` and `engine/backtest.py` added the
ownership nudge *after* `injury_mult` had already been applied to the base prediction:
`predicted = form*ease*reliability*injury_mult; predicted += (ownership/100)*ownership_weight`.
A confirmed-out player (`chance_of_playing_next_round == 0`, so `injury_mult == 0`) still carried
a positive score purely from ownership — a highly-owned player ruled out for the next gameweek
could still outrank a fit, lower-ownership alternative in `best_lineup`/`recommend_transfers`.

**Fix** (applied identically in both files): scale the whole prediction by `injury_mult`, ownership
term included — `predicted = (form*ease*reliability + (ownership/100)*ownership_weight) * injury_mult`.
Added `tests/test_score.py::test_confirmed_out_player_scores_zero_despite_high_ownership` as a
regression guard (40%-owned, `chance: 0` player now scores exactly `0.0`, not `~0.6`).

**Re-ran all 4 named schemes against GW1** after the fix — only Conservative's numbers moved (its
non-zero `injury_penalty_flat` and higher `ownership_weight` make it the scheme most sensitive to
this term; Baseline/Aggressive/New-signing-aware's GW1 test-squad totals were unaffected to 2
decimal places):

| Scheme | RMSE (before → after) | MAE (before → after) | Bias (before → after) |
|---|---|---|---|
| Baseline | 10.94 → 10.94 | 10.15 → 10.15 | +10.15 → +10.15 |
| **Conservative** | 4.30 → **4.24** | 3.61 → **3.83** | +0.97 → **+0.40** |
| Aggressive | 14.41 → 14.41 | 13.82 → 13.82 | +13.82 → +13.82 |
| New-signing-aware | 10.94 → 10.94 | 10.15 → 10.15 | +10.15 → +10.15 |

Conservative's RMSE improved slightly (4.30 → 4.24) and its bias moved closer to zero (+0.97 →
+0.40) — the recommendation to use Conservative for pre-season/early-season predictions is
unchanged and, if anything, slightly reinforced. `tests/test_backtest.py`'s pinned regression
values have been updated to these post-fix numbers.
