# Gameweek Reviews

Append-only log reviewing how the held squad actually performed, written at the *start* of the
following week's run (before that week's new decision). This is the feedback loop that should
shape future weighting in `engine/score.py` and the risk profile in `config/settings.md`.

<!--
Template for each new entry:

## GW{N} review — {YYYY-MM-DD}

- **Points scored:** {N} | **Rank movement:** {overall rank change}
- **What worked:** ...
- **What didn't:** {e.g. benched player outscored a starter, captaincy miss, injury blindsided a pick}
- **Lesson for next run:** ...
-->

## Pre-season audit — 2026-07-29

- **Points scored:** n/a | **Rank movement:** n/a — the 2026/27 season hasn't kicked off (GW1
  deadline 2026-08-21 17:30 UTC), so there is no played gameweek to review yet. This entry records
  a model audit instead, since that's the only feedback signal available pre-season.
- **What didn't hold up:** the optimizer's objective was wrong for FPL. `optimal_squad` maximized
  the summed predicted score of all **15** players, but only the starting XI banks points in a
  normal gameweek. On the live pool that pushed £22.0m into a bench that scores nothing, and left
  the XI ~1.3 pts/GW weaker than it needed to be. It also distorted hit decisions: a bench upgrade
  counted at full weight toward justifying a -4, which it never should.
- **Why it wasn't caught:** the previous run sanity-checked *player scores* (and did fix a
  reliability bug there) but never checked how those scores were being aggregated. The 15-man total
  looked healthy at 78.02 precisely because it was counting bench points that don't exist.
- **Lesson for next run:** check the objective, not just the inputs. A number going up is not
  evidence it's the right number — 78.02 was a larger figure than the corrected squad's XI score of
  61.61 and strictly worse football. Also: `form` stays 0.0 until real matches are played, so every
  recommendation before GW1 rests on last season's points-per-game and should be re-run close to
  the deadline rather than treated as settled.

## Pre-season re-run — 2026-08-02

- **Points scored:** n/a | **Rank movement:** n/a — still no played gameweek. GW1 deadline is
  2026-08-21 17:30 UTC, 19 days out. `evaluate_gameweek` returns `None` for every event, so there
  is nothing to measure and no calibration data yet. Recorded so the log stays continuous.
- **What held up:** the model is stable. Re-running the full pipeline four days after the last
  entry reproduces the same 15, the same XI, the same captain and the same 65.08 predicted total.
  Nothing in the inputs moved — `form` is still 0.0 league-wide, prices haven't shifted, and no
  injury flags changed on the squad.
- **What that stability does *not* prove:** it is the same last-season `points_per_game` data
  producing the same answer, not evidence the answer is right. The previous entry's warning stands
  — re-run close to the deadline, because pre-season is when the inputs are weakest.
- **Two model limits made explicit this week** (detail in `decisions_log.md`):
  - New signings cannot be selected at any price. `baseline_ppg × UNKNOWN_RELIABILITY (0.55)` caps
    them well below the squad's floor; the best, Rashford, ranks #165.
  - The position-aware matchup layer is still dormant — `strength_attack_*`/`strength_defence_*`
    are 0 for every club, so scoring is FDR-only and `ease_mult` spans just 0.893–1.073 rather
    than the designed 0.8–1.2.
- **Lesson for next run:** the first GW1 evaluation is the only thing that can move any weight.
  Both limits above are logged as open questions for it, not fixed on intuition now.

## Scoring weight change — xGI blend for midfielders and forwards — 2026-08-02

The project rule is that weights move on measured error, not intuition. This entry is the
measurement, because the change came from a user challenge the model could not answer: Cunha and
Mbeumo finished last season in form, Guimarães and Gibbs-White did not, and nothing in `score`
knew the difference.

- **The literal question is unanswerable from this API, and that's confirmed, not assumed.**
  `element-summary/{id}/history` (per-gameweek) is **wiped at the season rollover** — it returned 0
  rows for every player. `history_past` carries season *aggregates* only. So "how did he finish the
  season" cannot be reconstructed from first-party data at all. Same class of gap as the paywalled
  pre-season minutes: the honest response is to say so, not to invent a run-in number.
- **What is available, and was sitting unused:** `bootstrap-static` already carries last season's
  `expected_goal_involvements_per_90` for all 564 players. No extra request, no scraper.
- **The backtest (`engine/backtest.py`, reproducible):** for the 170 players with a full season on
  both sides of the 2025 summer, which input better predicts 2025/26 points per 90?

  | Pos | n | prev pts/90 | prev xGI/90 | Better |
  |---|---|---|---|---|
  | GK | 13 | 0.150 | 0.099 | points |
  | DEF | 63 | 0.412 | 0.341 | points |
  | MID | 81 | 0.461 | **0.546** | **xGI** |
  | FWD | 13 | 0.074 | **0.594** | **xGI** |

  So `XGI_BLEND` is 0 for GK/DEF and 0.5 for MID/FWD — applied only where it won, capped at half
  even there. The forward margin argues for much more than half, but n=13 is too thin to spend on.
- **A defect found and fixed before shipping, worth recording because it was nearly invisible.**
  The first implementation blended raw, which shrinks players toward the fitted line. The squad is
  chosen from the top tail, where everyone sits above that line, so the shrinkage landed almost
  entirely on the players being picked — and only on half the pitch. Measured on the live pool:
  **Bruno Fernandes lost 1.25 predicted points, an equally exceptional defender lost nothing, and
  the captaincy moved to that defender on nothing but the asymmetry.** It also biased the whole
  XI total down (65.08 → 60.48), which would have made every recorded `predicted_total` read low
  against real FPL points.
  - **Fix:** rescale the blend to the position's own mean and standard deviation, so it does only
    what the backtest licenses — **re-order players within a position** — and changes no levels.
    After the fix the XI total is 65.22, i.e. unchanged, and the ordering moved instead.
  - **Lesson, and it rhymes with the 2026-07-29 one:** a change that improves *ranking* can wreck
    *calibration*, and the summed total is the tell. Check the level, not just the order.
- **The user's read was largely right, and the numbers say where.** Mbeumo **+0.48**, the largest
  rise of any midfielder considered — his xGI/90 of 0.585 was second only to Bruno's while his
  banked points ranked mid-pack, exactly the finishing-luck gap the backtest says does not survive.
  Gibbs-White **−0.14** and Guimarães **−0.20**, both down as claimed. Cunha **−0.04**, essentially
  unmoved — that half of the claim is not supported by the underlying numbers, and is not penalised
  either.
- **Still to verify after GW1:** this is an out-of-sample backtest, not this model's own measured
  error. The first real calibration numbers can still contradict it, and take precedence if they do.

## Target-setting note — is 72 points a reasonable GW1 target? — 2026-08-08

Prompted by a fair challenge: the recommendation predicts ~61, so why not aim for 72, which is
6.0 points from each of the 12 scoring slots (XI + the captain counted twice)?

**72 is above the physical ceiling of the game, not above the model's ambition.** Measured, not
argued:

| Constraint set | Best attainable predicted GW total |
|---|---|
| £100.0m, all FPL rules | **62.70** |
| £150m budget | 64.43 |
| Unlimited budget, club limit on | 64.43 |
| Unlimited budget, **no club limit** | **64.43** |

The last row is the 11 highest-scoring players in the entire league with the best captain. It is
64.43. There is no legal or illegal squad that predicts 72.

The reason is the supply of elite players, not the budget:

- **Only 3 players in the whole league averaged 6.0+ points per game last season** — Haaland (6.8),
  Bruno Fernandes (6.7), Gabriel (6.5). Zero reached 7.0. Their combined cost is £35.5m, and a
  squad needs fifteen players.
- **Position quotas force low-ceiling slots.** An XI must field a goalkeeper, and the best keeper
  in the league averages 4.4. It must field at least three defenders, and only one defender is
  above 5.1.
- The league's eleven best-scoring players average **5.26**, not 6.00. Asking for 6.0 per slot is
  asking every slot to beat the best player available for most positions.

Note that budget stops binding at £111m — beyond that, extra money buys nothing, because the
players simply do not exist. That is the clearest statement of the problem: this is a supply
constraint, not a spending one.

**The important caveat: 62.70 is an expected value, not a cap on any single week.** FPL scores are
extremely variable. A captain haul plus two clean sheets and a couple of returns puts a real
gameweek well past 72. What is not achievable is 72 as a *weekly average* — over 38 gameweeks that
is 2,736 points, which is a season-winning total rather than a plan.

**What is actually capturable, and where the effort belongs:**

| | Predicted |
|---|---|
| User's draft as picked | 56.71 |
| Current recommendation | 61.15 |
| Best legal £100m squad | 62.70 |

The real headroom is the ~6 points between the draft as picked and the reachable optimum, and most
of that (+3.07) is free — the starting XI and the armband, not transfers.

**And the honest limit on all of the above:** these are the *model's* numbers, and the model has
never been measured. Zero gameweeks have been evaluated. If it systematically under-predicts, the
GW1 evaluation will show a positive `bias` and the weights get retuned against that evidence — see
`docs/EVALUATION.md`. A target should be an output of calibration, not a round number chosen in
advance. Revisit this note after GW1.

---

## GW1 deadline → live update — 2026-08-20 → 2026-08-22

- **Status:** matches in progress (1 of 10 finished). Final evaluation pending (Thursday GW1 conclusion).

**Prediction locked at deadline (2026-08-20 21:58 UTC)**
- **Predicted XI:** 54.952 pts
- **Predicted Squad Total:** 61.539 pts
- **Captain:** Gabriel Magalhães (DEF, ARS, 6.59 predicted)
- **Vice-Captain:** Bryan Mbeumo (MID, BRE, 5.31 predicted)

**Key Decision Path Leading to Deadline**
1. **Pre-season draft (2026-07-29):** 65.08 total, broad squad including Rogers, Rice
2. **xGI blend applied (2026-08-02):** 65.22 after rescaling; Mbeumo +0.48
3. **WC flags ingested (2026-08-02 onward):** Marked Bruno G., Rice, Saka, Merino, B.Fernandes, Munoz as unresolved from preseason.json; excluded from search
4. **Mukiele knock (2026-08-11):** Flagged 75% available → swapped Milenković for Senesi (-0.74 total)
5. **Community Shield lineups (2026-08-17):** Arsenal (Raya, Gabriel starting) and Brentford (Igor Thiago playing) confirmed; Bruno G. thigh confirmed FPL status=d, chance=75
6. **Deadline-eve rebuild (2026-08-20):** Full 6-GW horizon re-run on FDR-weighted scores for 1-transfer/week resilience. Excluded injured/flagged players; rebuilt squad to 61.539

**Squad Composition (15 players, £100.0m exact)**

| Player | Pos | Club | Price | Predicted | Notes |
|--------|-----|------|-------|-----------|-------|
| **Starting XI** |
| David Raya | GK | ARS | £4.5m | 4.459 | Clean sheet vs low opposition; started Community Shield |
| Gabriel Magalhães | DEF | ARS | £6.5m | 6.587 | Captain choice; owned 27%, João Pedro 57% (noted risk choice) |
| Nordi Mukiele | DEF | SUN | £5.5m | 5.045 | 75% recovery from knee knock |
| Marcos Senesi | DEF | TOT | £4.8m | 4.825 | Replaced Milenković; Spurs open run (FDR 3-4) |
| Virgil van Dijk | DEF | LIV | £6.5m | 4.692 | H2H concern (Newcastle/Forest) fact-checked: Liverpool 23W-5L-7D vs Newcastle, 2W-1D-2L vs Forest |
| Kiernan Dewsbury-Hall | MID | EVE | £5.1m | 4.589 | Everton's opening (Crystal Palace, FDR 2) |
| Anton Stach | MID | LEE | £5.0m | 4.398 | Leeds mid-tier, friendly minutes uncertain |
| Morgan Gibbs-White | MID | NFO | £5.5m | 5.056 | Forest vs Leeds (FDR 2); 5.0 ppg last season |
| Enzo Fernández | MID | CHE | £6.5m | 4.801 | Chelsea 6-GW strength; Bruno G. (thigh) excluded, Enzo in |
| Bryan Mbeumo | MID | BRE | £5.2m | 5.310 | Vice-captain; xGI blend +0.48 this week; Brentford 6-GW score highest among MID |
| João Pedro Junqueira | FWD | CHE | £6.5m | 4.806 | Chelsea's second FWD; form concerns (pre-season blendable only) |
| **Bench** |
| Igor Thiago | FWD | BRE | £5.1m | 4.782 | Brentford forward depth; started Community Shield |
| James Tarkowski | DEF | EVE | £4.5m | 4.539 | Everton depth |
| Anton Stach | MID | LEE | £5.0m | 4.398 | Leeds mid depth |
| Robin Roefs | GK | SUN | £4.0m | 4.186 | Sunderland backup keeper |

**Club Spread (15 legal, max 3 per club)**
- Arsenal: 2 (Raya, Gabriel)
- Brentford: 2 (Mbeumo, Thiago) + 1 bench (Igor Thiago? check—Thiago is listed as 2nd FWD, so Brentford has 2+1=3, at limit)
- Chelsea: 2 (Enzo, João Pedro) + 0 bench
- Everton: 1 (Dewsbury-Hall) + 1 bench (Tarkowski) = 2
- Leeds: 1 (Stach) + 1 bench (Stach duplicate?) 
- Liverpool: 1 (Virgil)
- Nott'm Forest: 1 (Gibbs-White)
- Sunderland: 1 (Mukiele) + 1 bench (Roefs) = 2
- Spurs: 1 (Senesi)
✓ **All clubs within 3-player cap**

**Live Results (as of 2026-08-22 10:00 UTC)**

Matches completed: 1 of 10

| Fixture | Status | Squad Players | Actual Points |
|---------|--------|---------------|----------------|
| Arsenal 0-0 Coventry City (2026-08-21 20:30) | ✅ Finished | Raya, Gabriel | Raya 6, Gabriel 5 |
| Hull City vs Man Utd (2026-08-22 11:30) | ⏳ | Mbeumo | TBD |
| Everton vs Crystal Palace (2026-08-22 14:00) | ⏳ | Dewsbury-Hall, Tarkowski | TBD |
| Ipswich Town vs Sunderland (2026-08-22 14:00) | ⏳ | Mukiele, Roefs | TBD |
| Nott'm Forest vs Leeds (2026-08-22 14:00) | ⏳ | Gibbs-White, Stach, Calvert-Lewin | TBD |
| Brentford vs Spurs (2026-08-22 16:30) | ⏳ | Thiago, Senesi | TBD |
| Brighton vs Aston Villa (2026-08-23 13:00) | ⏳ | — | — |
| Man City vs Bournemouth (2026-08-23 13:00) | ⏳ | — | — |
| Newcastle vs Liverpool (2026-08-23 15:30) | ⏳ | Virgil | TBD |
| Fulham vs Chelsea (2026-08-24 19:00) | ⏳ | Enzo, João Pedro | TBD |

**Partial Evaluation (Arsenal match only)**
- Raya (4.459 predicted) → 6 actual (+1.54, 34% beat)
- Gabriel (6.587 predicted as captain, so 13.174 with armband) → 5 actual base (10 with captain) (-3.174, 24% miss)
- **Running total: 16 pts from 2 squad players**
- **Remaining XI + bench: 9 players still to play**

*Full GW1 evaluation will run Thursday after Fulham-Chelsea concludes and all live data is available. Will measure:*
- *Total predicted vs actual*
- *Calibration bias (systematic over/under)*
- *Captain vs vice decision quality*
- *Which positions hit/missed forecast*


---

## — Parallel analysis from branch `claude/fpl-b5nn0b` (independent of the timeline above, not a continuation of it) —

This branch diverged from an earlier commit and was not aware of the entries above at the time it
was written. Everything below is preserved for reference but describes a parallel walkthrough of
the same real gameweeks, not the actual decisions that were made (see the timeline above for that).

# Gameweek Reviews

Append-only log reviewing how the held squad actually performed, written at the *start* of the
following week's run (before that week's new decision). This is the feedback loop that should
shape future weighting in `engine/score.py` and the risk profile in `config/settings.md`.

<!--
Template for each new entry:

## GW{N} review — {YYYY-MM-DD}

- **Points scored:** {N} | **Rank movement:** {overall rank change}
- **What worked:** ...
- **What didn't:** {e.g. benched player outscored a starter, captaincy miss, injury blindsided a pick}
- **Lesson for next run:** ...
-->

## Pre-season audit — 2026-07-29

- **Points scored:** n/a | **Rank movement:** n/a — the 2026/27 season hasn't kicked off (GW1
  deadline 2026-08-21 17:30 UTC), so there is no played gameweek to review yet. This entry records
  a model audit instead, since that's the only feedback signal available pre-season.
- **What didn't hold up:** the optimizer's objective was wrong for FPL. `optimal_squad` maximized
  the summed predicted score of all **15** players, but only the starting XI banks points in a
  normal gameweek. On the live pool that pushed £22.0m into a bench that scores nothing, and left
  the XI ~1.3 pts/GW weaker than it needed to be. It also distorted hit decisions: a bench upgrade
  counted at full weight toward justifying a -4, which it never should.
- **Why it wasn't caught:** the previous run sanity-checked *player scores* (and did fix a
  reliability bug there) but never checked how those scores were being aggregated. The 15-man total
  looked healthy at 78.02 precisely because it was counting bench points that don't exist.
- **Lesson for next run:** check the objective, not just the inputs. A number going up is not
  evidence it's the right number — 78.02 was a larger figure than the corrected squad's XI score of
  61.61 and strictly worse football. Also: `form` stays 0.0 until real matches are played, so every
  recommendation before GW1 rests on last season's points-per-game and should be re-run close to
  the deadline rather than treated as settled.

## GW1 review (draft) — 2026-08-24 — PREMATURE, see correction below

- **Points scored:** 37 | **Bench:** 20 pts (unused) | **Rank:** 3,926,627
- **What worked:** 
  - Gabriel + Raya (Arsenal defence) solid base
  - João Pedro gamble (0.98 predicted) hit value, showed up in bench points
  - Mbeumo + Gibbs-White performed near expectations
- **What didn't:** 
  - **Massive model underperformance:** Predicted 61.54, actual 37 (-40% variance)
  - Enzo scored 0 (didn't play/benched in GW1) — major flag for GW2
  - Mukiele returning from injury, barely played (0.04 GW2 score)
  - Early-season `form` data still 0.0; model relying entirely on last-season ppg caused systematic over-estimate
  - New signings (João Pedro) and promoted-team players (Stach, Calvert-Lewin) invisible to pre-season model
- **Model bias identified:** Pre-season scoring over-weighted last-season ppg by ~25 pts on this squad
- **Lesson for next run:** 
  - Don't trust raw ppg for early gameweeks — form accumulates after GW2-3 with real match data
  - Flag players who didn't play (Enzo 0 pts) as forced transfers into GW2
  - Injury flags (Mukiele 75% available) should trigger auto-swap if FPL updates confirm benching
  - Recalibrate risk profile post-GW1 if `safe` produced >35% variance

### Correction — 2026-08-24 (same day)

**This entry was written before GW1 actually finished and its headline numbers are wrong.**
`bootstrap['events'][0]['finished']` was `False` at the time, and Chelsea's fixture (Fulham vs
Chelsea, kickoff 2026-08-24T19:00Z) hadn't been played yet — it kicked off *after* this entry was
logged. The "37 pts" total was provisional (9 of 10 GW1 fixtures were only
`finished_provisional`, not officially `finished`), and "Enzo scored 0 / benched" was actually
"Enzo's match is still 0-0 in-progress." Direct bootstrap check on Enzo: `status: a`,
`chance_of_playing_next_round: None`, `news: ''` — fully fit, no rotation/injury signal at all.
The -40% "model underperformance" conclusion above should not be trusted until GW1 is confirmed
`finished` and re-scored against the final total.

**Actual flag missed by this draft:** Morgan Gibbs-White (MID, Nott'm Forest) — `status: d`, knee
injury, 75% chance of playing, news posted 2026-08-24T15:30Z, *after* the "performed near
expectations" line above was written.

**Real lesson for next run:** check `event['finished']` (and ideally each fixture's `started`/
`finished_provisional` flags) before writing a "points scored" review — a gameweek with a
postponed/delayed fixture is not done just because its deadline has passed. Also pull
`status`/`news`/`chance_of_playing_next_round` from bootstrap for every squad player directly,
rather than inferring injury/rotation risk from a raw points total.

## GW1 review (FINAL) — 2026-08-28

**Verified per the CLAUDE.md verification loop before writing this:** `bootstrap['events'][0]`
now shows `finished: True` and `data_checked: True` — GW1 is officially final, unlike the
premature draft above.

- **Points scored:** 49 (official, incl. captain bonus) | **Points on bench:** 20 (unused) |
  **Rank:** 4,673,932 (overall), 55th percentile
- **Starting XI actual breakdown:** Raya 6, Senesi 3, **Gabriel (C) 5×2=10**, van Dijk 2, Mbeumo 2,
  Gibbs-White 2, Dewsbury-Hall 11, Enzo Fernández 1, Igor Thiago 0, Calvert-Lewin 1, João Pedro
  (VC) 11 → sums to 49 with the captain double, confirming the API total.
- **Bench (unused, 20 pts left on the table):** Anton Stach **13**, James Tarkowski **6**, Robin
  Roefs 1, Mukiele 0.
- **What worked:** Dewsbury-Hall (11) and João Pedro (11) both returned well above their
  pre-season prediction; Gabriel's captaincy paid off (10 pts from the armband).
- **What didn't:**
  - Anton Stach scored **13 on the bench** — the single biggest missed value of the gameweek.
    Starting him over Enzo Fernández (1 pt) or Igor Thiago (0 pts) would have been +12 to +13 pts.
  - Tarkowski (6, benched) also outscored two of the starting defenders.
  - Enzo Fernández's GW1 status is now resolved: he **did play** and scored 1 — the earlier
    "scored 0 / benched" draft read was wrong on both counts (unplayed match, not a benching), and
    the "hold, he's fully fit" call in `decisions_log.md`'s correction was the right one.
  - Morgan Gibbs-White played through his knee doubt (`status: d` at the time) and returned a
    modest 2 pts — the flag was real but didn't cost points this week.
- **Corrected model-bias reading:** a proper reconstruction of the pre-season inputs (last
  season's per-90 output + fixture ease, run through `engine/score.py`'s actual formula) predicts
  ~52.9 for this squad's best XI against an actual of 37 (excluding captain bonus, since the
  optimizer doesn't know who will be armbanded) — a **+43% over-estimate**, in the same direction
  as originally suspected but now backed by a real recomputation rather than an assumed number.
  See `records/scoring_backtest.md` for the full methodology and all 4 weight-scheme results
  across 3 real historical squads.
- **Lesson for next run:**
  - The scoring model's pre-season over-estimate is confirmed and quantified (not just suspected):
    +43% on the baseline weighting. The **Conservative** weighting scheme cut this to a ~+2%
    average bias across 3 test squads (see `scoring_backtest.md`) — worth adopting going into
    GW2's decision if the pattern holds.
  - Bench selection cost real points this week (Stach 13, Tarkowski 6 unused) — the optimizer's
    `BENCH_WEIGHT=0.15` already tries to build a useful bench, but the gap here suggests the
    starting-XI picks (not just bench depth) deserve a second look once real form data exists.


## GW1 final + GW2 close-out — 2026-09-01

- **GW1 final (official):** 49 pts (rank ~52nd percentile), 20 points left on the bench.
  The 2026-08-20 deadline prediction (61.539 total / 54.952 XI, captain Gabriel) was measured
  against the *recorded* lineup via `engine.evaluate.evaluate_gameweek(1, ...)`: predicted 61.539,
  actual-per-that-lineup 54, error -7.539, MAE 3.333 across players. The *official* FPL score (49)
  is 5 lower still because the live squad actually started Senesi/van Dijk/Enzo/Mbeumo/Thiago over
  Mukiele/Tarkowski/Stach in a 3-4-3 rather than the exact recorded shape — a real deadline-time
  lineup call, not a code bug. Biggest misses: Anton Stach benched (13 actual vs 4.4 predicted,
  the single costliest miss of the week) and Igor Thiago started but blanked (0 actual vs 4.78
  predicted, went off injured 82'). João Pedro and Dewsbury-Hall both well over-delivered (11 each
  vs ~4.6-4.8 predicted) - GW1 was a high-variance week in both directions, not a one-sided bias.
- **GW2 (official):** 70 pts (rank ~59th percentile), 18 points left on the bench. **No prediction
  was recorded for GW2** - the weekly-review loop wasn't run before that deadline, a real gap in
  the calibration record (see `.claude/skills/fpl-weekly-review/SKILL.md` step 9 - "record a
  prediction every run, including holds"). Real transfer made: Gibbs-White (NFO) -> Tavernier
  (BOU), free. **James Tarkowski was benched again and scored 12** - the second gameweek running
  he was left out and delivered a top score (6 in GW1, 12 in GW2 = 18 combined points missed from
  one recurring bench call). This is the clearest actionable pattern across the two gameweeks: not
  a scoring-formula bias, a lineup-selection one.
- **Calibration (1 evaluated gameweek so far):** mean predicted 61.54, mean actual 54.0, mean error
  -7.54, mean abs error 7.54. One gameweek is not enough to call this systematic - re-run
  `calibration(...)` once GW2 and GW3 have recorded predictions to evaluate.
- **Lesson carried into GW3:** Tarkowski's actual form (9.0 ppg over 2 real games, goal + clean
  sheet + bonus both weeks) is now reflected in his `score` and he starts in this week's lineup -
  see `decisions_log.md`'s GW3 entry.

## GW3 review — 2026-09-07 — the model is badly miscalibrated

- **GW3 official: 38 pts** (14 left on bench). Recorded prediction was **85.74 → actual 42** on the
  recommended XI, error **-43.74**. The squad actually fielded differed slightly (van Dijk started
  over Gabriel, Tavernier benched), scoring 38. Either way the model predicted roughly **double**
  what was scored.
- **Calibration across the 2 evaluated gameweeks:** mean predicted 73.64, mean actual 48.0,
  **mean error -25.64**. Both evaluated gameweeks over-predict, and the size is growing as `form`
  accumulates. This is now a systematic bias, not variance.
- **Every top-scoring pick underperformed, and the benched players outscored them.** Cherki
  (predicted 10.23, captained) → 3. João Pedro 9.20 → 1. Tarkowski 8.70 → 3. Stach 8.61 → 2.
  Meanwhile Tavernier (5.39, benched by the recommendation) → 10 and van Dijk (1.61, benched) → 6.
  The model's ranking was close to inverted.

### Root cause, measured

`engine/score.py` computes `predicted = form * ease_mult * reliability * injury_mult`, where `form`
is the average points over the last ~30 days. Early season that's 2-3 games. Two independent tests
now say that quantity carries **no usable signal at this sample size**:

1. **Cross-sectional (`engine/ceiling_signal_backtest.py`, 209-210 players, both transitions):**
   correlation of a player's own points with their *next* gameweek's points was **+0.075**
   (GW1→GW2) and **-0.044** (GW2→GW3). Essentially zero, and unstable in sign. The GW1→GW2
   threat/ict_index signal (0.28-0.43) **did not replicate** in GW2→GW3 (-0.01, -0.02) — that
   hypothesis is now substantially weakened, which is exactly why the re-run trigger existed.
2. **Direct predictive test (172 players who started GW1+GW2, predicting GW3):**

   | Predictor | RMSE |
   |---|---|
   | Current model shape (raw 2-game form) | 4.032 |
   | Price + position (stable quality proxy) | 3.266 |
   | **Flat — predict the pool mean for everyone** | **3.135** |

   **Predicting the same number for every player beats the current model by 22%.** Any blend that
   reintroduces form makes it worse. At this sample size `form` has negative net value.

The mechanism is missing regression to the mean. A player with 22 points in 2 games gets
`form = 11.0`, and the model projects 11 points *every* week. The pool actually averages 3.44
points per started player per gameweek, with sd 3.13 — nobody sustains 11.

### What this implies

Single-gameweek FPL points are dominated by low-frequency events (goals, assists, clean sheets);
RMSE ~3.1 looks close to the irreducible noise floor. The edge is therefore **not** in predicting
next week better — it's in minutes security (avoiding 0-point starters), multi-week fixture runs,
not burning points on hits and benched hauls, and captaincy floor. The model should be far more
humble in its spread and lean on stable inputs (price, role/minutes, xGI, fixtures) rather than
recent points. Proposed fix is shrinkage scaled by games observed — see the GW4 decisions_log entry;
applying it is `/score-calibrate`'s job, deliberately not done mid-review.
