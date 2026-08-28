# Scoring Model

`engine/score.py` predicts a per-player point value for the upcoming gameweek. This is the single
number `engine/optimize.py`'s MILP maximizes (as `XI + BENCH_WEIGHT * bench`, see
`engine/optimize.py`'s docstring) — everything downstream (transfer recommendations, captain
picks, lineup selection) depends on this number being reasonably calibrated.

## Current formula (Baseline scheme)

```
predicted = form * ease_mult * reliability * injury_mult + (ownership/100) * ownership_weight
```

| Factor | Meaning | Current value |
|---|---|---|
| `form` | Last-30-days avg points/match; falls back to last season's points-per-game when `form` is 0 (pre-season/early season) | `float(p["form"] or 0) or float(p["points_per_game"] or 0)` |
| `ease_mult` | Upcoming fixture difficulty over the next 4 GWs, scaled 0.8 (hard run) – 1.2 (easy run) | `0.8 + ease * 0.4` |
| `reliability` | Minutes-played discount, normalized against a 38-game season reference (falls back to full-season reference pre-season, since 0 games have been "finished" this season) | `min(1.0, minutes / (38 * 90 * 0.6))` |
| `injury_mult` | `chance_of_playing_next_round` as a fraction; 1.0 if unset (assumed fit) | `chance / 100` |
| `ownership_weight` | Risk-profile-driven nudge toward/away from high-ownership players | `{"safe": 1.5, "balanced": 0.3, "differential": -1.5}` |

Change `config/settings.md`'s `risk_profile` to switch the `ownership_weight` used — that's the
only intended lever for user-facing risk tuning. Everything else in the table above is a project
default, changed only through the calibration process below.

## Known bias (confirmed, not just suspected)

Pre-season and early-season, `form` is 0 for every player (no matches in the last 30 days), so the
formula falls back entirely to last season's points-per-game. That fallback **over-estimates
systematically** — confirmed by the GW1 backtest (`records/scoring_backtest.md`): **+43% bias on
the Baseline scheme** across 3 real test squads. Last season's output doesn't discount for a new
season's fixture difficulty shifts, new-manager effects, or squad changes at other clubs.

## Four weight schemes

`engine/backtest.py`'s `SCHEMES` dict is now the source of truth for these values (this table is
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

`engine/backtest.py` is a reusable CLI, not a one-off script — it's how you experiment with a
weight combination instead of guessing:

```
python engine/backtest.py --gw 1 --scheme conservative
python engine/backtest.py --gw 1 --custom '{"form_mult": 0.95, "ease_min": 0.8, "ease_max": 1.15, \
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
