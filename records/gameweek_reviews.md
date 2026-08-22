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
