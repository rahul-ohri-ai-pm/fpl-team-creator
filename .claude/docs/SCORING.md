# Scoring Model

`engine/score.py` predicts a per-player point value for the upcoming gameweek. This is the single
number `engine/optimize.py`'s MILP maximizes (as `XI + BENCH_WEIGHT * bench`, see
`engine/optimize.py`'s docstring) — everything downstream (transfer recommendations, captain
picks, lineup selection) depends on this number being reasonably calibrated.

## Current formula (live, post-master-merge)

**This section describes `engine/score.py` as it actually is today.** The "Four weight schemes"
section below it is historical — it documents an earlier, simpler formula shape from before this
project merged with a more advanced parallel line of development; see
`engine/weight_scheme_backtest.py`'s own docstring. Don't confuse the two.

```
predicted = form * ease_mult * reliability * injury_mult
```
(`ownership` is a separate `tiebreak` field, never inside `predicted` — see "Scoring conventions"
in `CLAUDE.md`.)

| Factor | Meaning | Current value |
|---|---|---|
| `form` | This season's last-30-days avg points/match, **shrunk toward a price-implied prior early in the season** — see below. Pre-season (`finished == 0`) falls back to `ppg` (xGI-blended for MID/FWD, price-baseline for a player with no record at all) | `engine/score.py`'s `score_players`, ~line 366 |
| `ease_mult` | Fixture difficulty over the next 4 GWs, decay-weighted toward the imminent one, blended with a position-aware opponent-matchup read where team strength data supports it | `fixture_ease()` / `opponent_matchup_ease()` |
| `reliability` | Minutes-played discount, blended with pre-season minutes-share data early on | `min(1.0, minutes / (games_reference * 90 * 0.6))` |
| `injury_mult` | `chance_of_playing_next_round`, falling back to pre-season fitness-doubt data, further scaled by club-level availability | `score_players`'s `injury_mult` |

Change `config/settings.md`'s `risk_profile` to switch the `ownership_weight` used for the
`tiebreak` field — that's the only intended lever for user-facing risk tuning.

### Form shrinkage (`FORM_SHRINKAGE_K`, added 2026-09-07)

**Measured, not assumed**: a GW3 backtest over 172 players (predicting GW3 from their GW1-2
`form`) found raw form scored *worse* than a naive price-implied baseline — RMSE 4.032 (raw form)
vs 3.266 (price+position prior) vs 3.135 (a flat pool-mean, the honest noise floor) — see
`records/gameweek_reviews.md`'s "GW3 review" entry. Early-season `form` is an average of 1-3
matches; at that sample size it isn't signal, it's noise the model was treating as real.

Fix: `form` is now shrunk toward a price-implied prior (`preseason.price_baselines`, refit at a
games-scaled minutes threshold so it works well before the pre-season model's 900-minute bar),
weighted by games actually played:
```
form = (finished * raw_form + FORM_SHRINKAGE_K * price_prior) / (finished + FORM_SHRINKAGE_K)
```
`FORM_SHRINKAGE_K = 10` — form and the price prior are weighted equally at ~10 games played, form
dominates by season's end. Re-validated end-to-end against real GW1-3 data (not just the backtest
in isolation): RMSE 4.032 → 3.274. **K itself is a first estimate** — the backtest's RMSE kept
improving with diminishing returns out to K=50; 10 was chosen as a defensible middle ground, not
the literal optimum of one data point. Re-fit as more gameweeks accumulate.

## Four weight schemes

`engine/weight_scheme_backtest.py`'s `SCHEMES` dict is now the source of truth for these values (this table is
a human-readable mirror — if the two ever disagree, trust the code). It also accepts a `--custom`
JSON scheme with the same shape, so any weight combination can be backtested, not just these 4 —
see "Weight simulator" below.

| Scheme | Form mult | Ease range | Reliability divisor | Injury penalty | Ownership weight (safe/balanced/differential) | Rationale |
|---|---|---|---|---|---|---|
| **Baseline** | 1.0x | 0.8–1.2 | `38×90×0.6` | none | 1.5 / 0.3 / -1.5 | Current formula |
| **Conservative** | 0.9x | 0.8–1.15 | `38×90×0.5` (stricter) | -0.1 flat | 2.0 / 0.5 / -1.0 | Lower variance; penalize low-minutes and rotation risk harder |
| **Aggressive** | 1.1x | 0.75–1.25 | `38×90×0.75` (looser) | none | 1.0 / 0.0 / -2.0 | Trust form more; chase fixture swings and differentials |
| **New-signing-aware** | 1.0x (same as Baseline) | 0.8–1.2 | `38×90×0.6` | none | 1.5 / 0.3 / -1.5 | Baseline + ×0.85 downweight when last-season PL minutes < 270 (i.e. genuinely no top-flight track record) |

### Weight simulator

`engine/weight_scheme_backtest.py` is a reusable CLI, not a one-off script — it's how you experiment with a
weight combination instead of guessing:

```
python engine/weight_scheme_backtest.py --gw 1 --scheme conservative
python engine/weight_scheme_backtest.py --gw 1 --custom '{"form_mult": 0.95, "ease_min": 0.8, "ease_max": 1.15, \
  "reliability_divisor_factor": 0.55, "injury_penalty_flat": -0.05, \
  "ownership_weight": {"safe": 1.8, "balanced": 0.4, "differential": -1.2}, \
  "new_signing_downweight_factor": 0.9, "new_signing_minutes_threshold": 270}'
```

It refuses to run against a gameweek that isn't `finished` yet (the verification loop applied to
backtesting), caches the reconstructed pre-gameweek inputs under
`records/snapshots/gw{N}_preseason_reconstruction.json` so re-runs cost no API calls, and always
scores the same Baseline-selected XI across schemes so squad-selection doesn't confound scoring
accuracy. `tests/test_backtest.py` pins the 4 named schemes' GW1 numbers as a regression check.

### GW1 backtest result (see `records/scoring_backtest.md` for full methodology)

| Scheme | RMSE | MAE | Bias |
|---|---|---|---|
| Baseline | 10.94 | 10.15 | +10.15 |
| **Conservative** | **4.30** | **3.61** | **+0.97** |
| Aggressive | 14.41 | 13.82 | +13.82 |
| New-signing-aware | 10.94 | 10.15 | +10.15 (identical to Baseline this test — see caveat below) |

**Current recommendation: use Conservative for pre-season/early-season predictions** (through
roughly GW3-4, until real in-season `form` data accumulates). It cut RMSE by ~61% and brought bias
from consistently over-confident (+10.15) to essentially unbiased (+0.97) against real GW1
results.

**New-signing-aware caveat**: it only fires when a player has < 270 minutes in the *prior
completed* PL season. In the GW1 test, João Pedro (the presumed "invisible new signing") already
had a 2025/26 PL season on record (he moved from Brighton, not from outside the league), so the
downweight never triggered. This scheme is still worth keeping for a genuinely new-to-the-PL
signing (e.g., a Championship promotion or first-time overseas transfer) — just don't expect it to
help with a player who already has top-flight minutes elsewhere.

**Not yet adopted in `engine/score.py`** — this is a documented recommendation pending a second
confirming backtest (GW2 or GW3) before changing the live formula. See `/score-calibrate` for how
a scheme change gets applied and logged.

## Backtest methodology (used by `/gw-backtest`)

1. **Only run once `bootstrap['events'][n]['finished'] == True`** — see the verification loop.
2. Reconstruct the pre-gameweek inputs each scheme would have used. If `form` was 0 pre-gameweek,
   this means pulling `history_past` from `/api/element-summary/{id}/` for the relevant prior
   season, since bootstrap's live `points_per_game`/`minutes` fields reset each season and can't
   be un-reset retroactively (this is why `records/scoring_backtest.md` recommends snapshotting
   `bootstrap-static` before each deadline going forward — skip the reconstruction step once
   snapshots exist).
3. Score every player in the test squad(s) under each scheme; pick one shared best-XI (using
   Baseline's scores) so all schemes are compared on identical starting lineups — isolates scoring
   accuracy from squad-selection differences.
4. Compare each scheme's predicted XI total against the actual XI total from `/api/event/{n}/live/`
   (no captain multiplier — the model doesn't choose a captain, so don't apply one when judging it).
5. Compute RMSE, MAE, and bias (mean signed error) per scheme across all test squads.
6. Log results to `records/scoring_backtest.md` (append-only) with a recommendation.

## Applying a scheme change

Changing which scheme is live in `engine/score.py` is a deliberate, logged decision — not
something a backtest run should do automatically. Use `/score-calibrate`, which:
- requires at least one backtest result to cite
- projects the impact using the last 3 gameweeks of data before recommending the change
- logs the change (and its rationale) to `records/decisions_log.md` under a "Model calibration"
  entry
- only takes effect starting the *next* `/fpl-weekly-review` run, never mid-analysis

## Ceiling-signal backtest (separate from the weight-scheme one above)

Everything above tests *weight schemes* against the older, now-superseded formula shape (see
`engine/weight_scheme_backtest.py`'s docstring). A different, live question: does `form` (backward-
looking box-score points) miss a player's underlying *ceiling* — the difference between a
consistent 5-pointer and someone capable of a 20-point haul? `engine/ceiling_signal_backtest.py`
tests candidate per-gameweek signals (`threat`, `bps`, `ict_index`) against next-gameweek actual
points, position by position. First result (`records/ceiling_signal_backtest.md`, GW1→GW2): for
MID/FWD, a player's own recent points barely predict next week's (correlation ≈0), but `threat`/
`ict_index` do (0.25–0.43) — a real gap `form` doesn't currently see. One transition isn't enough
to act on; re-run it each week (`python engine/ceiling_signal_backtest.py --from N --to N+1`) and
append to the log — a change to `engine/score.py`'s MID/FWD `form` term still goes through
`/score-calibrate` once the pattern holds across a few gameweeks.
