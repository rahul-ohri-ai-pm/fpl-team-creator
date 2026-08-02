# Decisions Log

Append-only log of every transfer decision (including "held, no transfer") and the reasoning behind it.

<!--
Template for each new entry:

## GW{N} — {YYYY-MM-DD}

- **Decision:** {Held / Transferred X for Y / Used chip Z}
- **Hit taken:** {0 / -4 / -8}
- **Reasoning:** {form, fixtures, injury news, optimizer's predicted point delta}
- **Optimizer net score (post-hit):** {value}
-->

## Pre-season — 2026-07-29

- **Decision:** Initial squad draft (no existing GW picks to transfer from yet - season hasn't
  started). See `team_history.md` for the full squad.
- **Hit taken:** n/a
- **Reasoning:** `form` (last-30-days average) is 0 for every player right now since no PL match
  has been played in that window - so the scoring model fell back to last season's
  `points_per_game`, adjusted for upcoming fixture ease and a minutes-reliability discount (risk
  profile: safe, so ownership% gets a small positive weight). This is a weaker signal than in-season
  form and should be treated as a starting point, not a confident pick - revisit once real
  gameweek data starts coming in.
- **Bug fixed during this run:** a backup goalkeeper (90 total minutes last season, one big game)
  was initially ranked above his actual quality because the reliability discount only checked
  *this season's* games-played count, which is 0 pre-season. Fixed to fall back to a full-season
  reference (see `engine/score.py` history).
- **Optimizer net score:** 78.02 (sum of predicted scores across the 15-man squad, no hit).

## Pre-season (re-run) — 2026-07-29

- **Decision:** Redraft of the initial squad. Supersedes the earlier 2026-07-29 entry above (that
  entry stays as written — this log is append-only). Five changes vs. that draft:
  **out** Roefs, Kelleher, Van Hecke, Stach, Igor Thiago → **in** Raya, Dubravka, Mitchell,
  Semenyo, Richarlison.
- **Hit taken:** n/a — pre-season, unlimited changes until the GW1 deadline.
- **Reasoning:** the changes are almost entirely a consequence of fixing the optimizer's objective
  (see below), not of new information about the players. Correcting it freed money that had been
  parked on the bench and moved it into the XI — most visibly Semenyo (£8.5m, 202 pts and 17 goals
  last season, now at Man City) coming into midfield and Raya (£6.0m, 19 clean sheets) replacing a
  £5.0m keeper, paid for by dropping to a genuine budget bench.
- **Bug fixed during this run:** `engine/optimize.py` maximized the summed score of all 15 players.
  Only the XI scores in a normal gameweek, so this bought bench players with real budget and let
  bench upgrades justify -4 hits. Replaced with a joint squad+lineup MILP maximizing
  `XI + BENCH_WEIGHT * bench` (`BENCH_WEIGHT = 0.15`). Weight 0 was rejected: it produced four
  £4.0m players who never take the pitch, which loses points to auto-subs. `recommend_transfers`
  now scores options on that same quantity, so its net figure is comparable to the -4 hit in real
  points. Added `tests/test_optimize.py` (quotas, budget, club limit, formation legality,
  captain/vice, objective behaviour, hit thresholds) — the optimizer previously had no tests.
- **Optimizer net score:** 63.854 (XI 61.611 + 0.15 x bench 14.954), no hit. Not comparable to the
  78.02 in the entry above: that was the old all-15 sum. On the same measure this squad's XI is
  61.611 vs 60.305 for the previous draft, ~+1.3 pts/GW.
- **Caveat:** `form` is 0.0 for every player until real matches are played, so this is last
  season's points-per-game adjusted for fixture ease and minutes reliability. Treat as a starting
  point and re-run nearer 2026-08-21 — prices, transfers and pre-season injury news will all move.

## Pre-season (pre-season data layer) — 2026-07-29

- **Decision:** No squad change. The 15 in `team_history.md` from the re-run entry above still
  stands after adding pre-season data to the model.
- **Hit taken:** n/a — pre-season, unlimited changes until the GW1 deadline.
- **Reasoning / what changed in the model:** confirmed the FPL API carries *no* pre-season data by
  design — `/fixtures/` returns exactly 380 league games with the earliest kickoff on the GW1 date,
  `form` is 0.0 for all 564 players, and none of the 105 element fields reference friendlies. Added
  `data/preseason.json` + `engine/preseason.py` to carry what the API can't:
  - **Price-implied baseline.** 164 of 564 players had `points_per_game` 0 (new signings, returning
    loanees, seasons missed injured) and were scored ~0, so they could never be selected regardless
    of FPL's valuation — Rashford £7.0m, Kulusevski £6.5m, N.Jackson £6.5m among them. Now fitted
    from the live pool: ppg ~ price per position, correlation 0.73-0.83. Fitted per run so it
    recalibrates as prices drift rather than being hardcoded.
  - **Pre-season minutes** blended into reliability at weight 0.4 (blend, not replace — a handful of
    friendlies shouldn't outvote a full season). Left null for now: player-level minutes are
    paywalled behind Fantasy Football Scout's Chief Scout tier, and inventing them would corrupt
    every downstream score. Team-level friendly results (28 played) are recorded from the free
    premierleague.com listing.
  - **Availability flags** for fitness risk FPL hasn't flagged yet. The 2026 World Cup ended ~33
    days before GW1, so deep-run players may only rejoin club training around 10-12 August. Saka and
    Rice flagged at 0.75 on that basis — an editorial risk flag, not a confirmed absence, and FPL's
    own `chance_of_playing_next_round` overrides it once set. Consistent with the `safe` risk
    profile in `config/settings.md`.
- **Bug caught by a test during this run:** the pre-season minutes blend was applied *before* the
  unknown-player reliability fallback, so a player with a perfect pre-season minutes record scored
  **lower** (2.15) than an identical player with no data at all (2.90) — recording good data
  penalised the player. Reordered so the fallback lands first.
- **Effect on the squad:** none of the 164 newly-selectable players earned a place, so the price
  baseline widened the search without degrading the pick. The availability flag did bite: Rice drops
  out of contention (5.300 -> 4.056), as does Saka (5.133 -> 3.890).
- **Optimizer net score:** 63.854 (XI 61.611 + 0.15 x bench 14.954), unchanged — the squad is stable
  under the richer model, which is mild evidence for it rather than against.

## Pre-season (ownership as tiebreak + prediction tracking) — 2026-07-29

- **Decision:** Squad adjusted by three players as a direct consequence of the scoring fix below.
  **out** Szoboszlai, Muñoz, Dúbravka → **in** Stach, Senesi, Verbruggen. Captain/vice unchanged
  (Fernandes / Gabriel).
- **Hit taken:** n/a — pre-season, unlimited changes until the GW1 deadline.
- **Why the squad moved:** ownership is no longer added to `score`. It was worth up to +0.79 points
  per player, which is not a small nudge — Szoboszlai (47.3% owned) was carrying +0.71 of padding
  and ranked above Stach on 4.62 vs 4.82 of *actual* predicted points. Stripping the padding
  reversed that. Ownership now lives in a separate `tiebreak` field applied by the optimizer at
  epsilon 0.02, i.e. at most 0.02 points of influence, so it can only separate players who are
  otherwise near-identical. That is what a tiebreak should mean.
- **What this fixes beyond the squad:** the reported total is now genuinely predicted points.
  Previous runs reported 69.21 for a squad whose honest expectation was ~63.8; the gap was 4.29 of
  ownership padding plus fixture-ease gains, and it made the headline number uncomparable to
  anything the team could actually score. New predicted total: **64.50** (XI 57.64 + captain 6.87).
  Independent check: a separate optimizer run on raw last-season ppg put the *theoretical ceiling*
  for any £100m squad at 64.80, so 64.50 now lands where it should instead of above it.
- **Prediction tracking added.** `records/predictions.jsonl` (append-only, one JSON line per run)
  stores the recommended XI/bench, captain and predicted points. `engine/evaluate.py` replays a
  gameweek's real FPL points against it — applying auto-substitutions and the vice-captain armband,
  so a blanked starter isn't scored as a zero the real team never took — and reports predicted vs
  actual, per-player error, MAE and signed bias. The weekly skill now runs this *first*, before any
  recommendation, so each week's call is made in light of the last week's measured result.
- **GW1 prediction recorded:** predicted_total 64.504. First measurable entry; nothing to evaluate
  against yet since no gameweek has been played.
- **Test note:** a test caught my own arithmetic error rather than a code bug (XI total with a
  captain double). 57 tests now pass, covering the optimizer, pre-season layer and evaluation.

## Pre-season (fixture weighting + managerial change) — 2026-07-29

- **Decision:** Five changes. **out** Semenyo, Guéhi, Harry Wilson, Richarlison, Verbruggen →
  **in** Gibbs-White, Igor Thiago, Dewsbury-Hall, Ballard, Dúbravka. Captain/vice unchanged
  (Fernandes / Gabriel). Formation moves 4-5-1 → 3-5-2.
- **Hit taken:** n/a — pre-season, unlimited changes until the GW1 deadline.
- **Prompted by:** a direct question about whether the Leeds/Chelsea away openers and Man City's
  new manager were being accounted for. Answer was: venue partially, managerial change not at all.
- **Fix 1 — fixture weighting.** `fixture_ease` took a *flat* mean of the next four fixtures, so
  the imminent game carried only 25% of the weight. Leeds' away opener at Forest was being
  out-voted by their easier GW2-4 run, leaving them on a 1.025 multiplier — a net *boost* going
  into an away trip. Now decayed at 0.5 (weights ~53/27/13/7), so next gameweek dominates while
  keeping some lookahead, which matters because only ~1 free transfer a week is available.
  Effect: LEE 1.025 → 1.007, NFO 0.975 → 1.020, SUN 1.025 → 1.073.
  - Note for future runs: home/away needs no separate term. FPL's FDR already rates the two sides
    of a fixture differently (Leeds away at Forest is 3, Forest at home is 2), so venue was always
    present — it just wasn't being *weighted* onto the right gameweek. Adding an explicit
    home/away multiplier on top would double-count.
- **Fix 2 — club-level uncertainty.** Nothing in the model represented a managerial change. Enzo
  Maresca replaced Pep Guardiola at Man City on a three-year deal, ending a decade under one
  manager, so last season's minutes are a weak guide to this season's XI. Added a `clubs` section
  to `data/preseason.json` applying a club-wide availability multiplier, compounding with any
  per-player flag and applying even to players FPL rates fully fit — a fitness rating says nothing
  about whether a new manager picks someone. MCI set to 0.90.
  - **This 0.90 is a judgment call, not a measurement.** It is sized to break a tie against an
    equivalent player at a settled club without excluding a genuinely better one. It was enough to
    drop both City players: Semenyo 5.54 → 4.98, Guéhi 5.13 → 4.62.
  - **Incomplete by design:** eight clubs changed manager in summer 2026 and only Man City is
    flagged, being the one asked about. The others should be added as their pre-season XIs become
    readable, or the flag quietly advantages them.
- **Predicted GW total:** 65.08 (XI 57.89 + captain 7.19). Higher than the 64.80 "ceiling" quoted
  in the previous entry, and not a contradiction: that ceiling was computed on raw points-per-game
  with no fixture adjustment at all, whereas `ease_mult` can exceed 1.0 for a favourable run.
  The two numbers measure different things.
- **Correction to a working note made during this run:** an interim table reported Harry Wilson as
  a Brentford player scoring 1.58. That was a name-collision in throwaway analysis code — the pool
  holds three players with `web_name` "Wilson" and it matched Callum Wilson (BRE, 0 minutes).
  Harry Wilson (LEE, id 260) is the squad player. The squad selection itself was never affected;
  only that diagnostic line was wrong.

## Pre-season (position-aware opponent matchup) — 2026-07-29

- **Decision:** No squad change. The 15 in the entry above stand; predicted total still 65.08.
- **Hit taken:** n/a — pre-season.
- **What was added and why:** FDR compresses an opponent into a single integer that is identical
  for a goalkeeper and a striker. That is wrong in an obvious direction — a clean sheet depends on
  how well the opponent *attacks*, an attacking return on how badly they *defend* — and it was the
  model's crudest remaining assumption. `engine/score.py` now derives a position-aware matchup from
  FPL's own `strength_attack_*` / `strength_defence_*` fields, weighted per position
  (GK 1.0/0.0, DEF 0.7/0.3, MID 0.3/0.7, FWD 0.0/1.0 on opponent attack/defence), decayed across
  the fixture run exactly like FDR, and blended at `MATCHUP_WEIGHT = 0.5` so FDR still anchors the
  estimate and continues to carry venue.
  - Opponent venue is read as the mirror of ours: facing a side away from home uses their *away*
    attack and defence, since teams attack and defend differently by venue.
  - Strengths are min-max normalised within the league, so the code is indifferent to whether FPL
    publishes a 1-5 or a 1000-1400 scale.
- **Currently dormant, deliberately.** `strength_attack_*` and `strength_defence_*` are 0 for every
  club pre-season and `strength` is null, so `_normalized_strengths` returns None and scoring falls
  back to FDR alone. That is why the squad and the 65.08 are unchanged. The layer starts
  contributing once FPL populates the fields after real matches are played. Verified against a
  simulated in-season dataset: Leeds' four positions then draw four different multipliers
  (GK 0.997, DEF 0.983, MID 0.963, FWD 0.949) off the same fixture run — the separation FDR cannot
  express. 13 new tests cover it, including the flat-field fallback.
- **Head-to-head history was considered and rejected.** The request that prompted this was whether
  past meetings between two clubs are accounted for. They are not, and shouldn't be:
  - The FPL API carries no history at all — `/fixtures/` is current-season only, 0 fixtures with
    scores. It would need an external source and a scraper to maintain.
  - Predictive value is weak and this season is a bad case for it: both Chelsea and Man City
    changed manager (Maresca left one for the other), Leeds have moved between divisions, and
    squads have turned over. Five meetings spread across years is mostly noise.
  - FDR is already an opponent-strength rating, so H2H would largely re-express it while adding
    variance. The position-aware matchup above targets the same instinct — "the opponent should
    matter more specifically" — using first-party data and without the double-count.

## Pre-season (favourite club priced, new-signing audit) — 2026-08-02

- **Decision:** No squad change, and **no club floor switched on**. Chelsea recorded as the
  favourite club in `config/settings.md` with loyalty mode `report`, per the user's choice to see
  the price before committing to a constraint.
- **Hit taken:** n/a — pre-season.
- **What forcing Chelsea players would cost** (`optimize.loyalty_cost`, live pool, £100.0m budget,
  measured in predicted points per gameweek against the unconstrained optimum of 60.10):
  - **1 player: 0.00** — João Pedro (FWD, £7.5m, 5.13) is already picked on merit, so the floor
    binds on nothing.
  - **2 players: 0.18** — adds Robert Sánchez (GK, £5.0m, 3.22), who sits on the bench.
  - **3 players: 0.38** — Chalobah (DEF, £5.5m, 4.03) and Emegha (FWD, £5.0m, 1.08) alongside
    João Pedro; only João Pedro starts.
  - Under a tenth of a point per forced player. The intuition that supporting your club is expensive
    is wrong on this pool, and the only way to know that was to measure it. Worth revisiting after
    GW1, when `form` goes live and the gaps between players widen.
- **Implementation note:** the floor is `optimize.min_from_team`, a hard constraint next to the
  quota/budget/3-per-club rules — deliberately *not* a bonus on `score`. Adding it to `score` would
  repeat the ownership mistake of 2026-07-29: inflating the predicted total until it no longer
  matches what the squad actually banks.
- **Bug found while adding it:** `recommend_transfers` raised on the first infeasible transfer
  count. A floor of 2 against a squad holding none of the club made k=0 and k=1 infeasible and
  killed the whole search, when the correct answer was "this takes 2 transfers". Infeasible counts
  are now skipped; only an all-infeasible search raises.

### New signings: are they in the recommendation? Audited, and the answer is no.

- 164 of the 564 players in the pool have zero Premier League minutes (new signings, returning
  loanees, players who missed last season). All 164 *are* scoreable — the price-implied baseline
  added on 2026-07-29 exists precisely so they aren't invisible — and all 164 are eligible for
  selection. None of them are chosen.
- The best-scoring new arrival is **Marcus Rashford (MUN, £7.0m) at 2.29, ranked #165** in the pool.
  Every player in the recommended 15 outranks him. The next best are Palestra (CHE, 2.11),
  V. Muñoz (LIV, 1.98), Tzolis (ARS, 1.97), N. Jackson (CHE, 1.83).
- **Cause, and it's structural, not a bug.** A player with no record is scored
  `baseline_ppg(price) × ease × UNKNOWN_RELIABILITY (0.55)`. The baseline regresses them onto the
  league's price/points line — average for their cost by construction, never exceptional — and the
  0.55 then removes 45% on top. The product cannot reach the ~5.0 the top of the squad scores.
  So no new signing can enter the squad at any price, on any fixture run.
- **Deliberately not retuned.** Per `CLAUDE.md`, weights change off measured error, not intuition,
  and there is zero measured data so far (GW1 is 2026-08-21). Raising `UNKNOWN_RELIABILITY` to make
  Rashford selectable today would be exactly the intuition-driven change the project rules forbid.
  Flagged as an open question for the first post-GW1 calibration, when real minutes for these
  players exist to measure against.
- **The honest mitigation is already specified and blocked on access:** `data/preseason.json`
  player-level friendly minutes. That's the one signal that legitimately separates a new signing the
  manager intends to start from one who won't play, and it's paywalled (FFS Chief Scout). Guessing
  the numbers is worse than leaving them null.

## GW1 pre-season re-run — 2026-08-02

- **Decision:** **Hold.** The optimizer rebuilds the identical 15 from scratch on today's pool —
  same XI (3-5-2), same captain and vice as the 2026-07-29 entry.
  No transfer is recommended and none is needed: pre-season, the squad can be changed freely until
  the deadline, so "hold" here means "the from-scratch optimum has not moved".
- **Hit taken:** n/a — unlimited changes until the GW1 deadline (2026-08-21 17:30 UTC).
- **Predicted GW1 total:** 65.081 (XI 57.890 + captain 7.191). Squad cost exactly £100.0m.
- **Captain: Bruno Fernandes (7.19), Vice: Gabriel Magalhães (6.59).**
  - The `fpl` MCP's captain tool disagreed, returning five Arsenal players and ranking Gabriel
    first on "great home fixture vs COV (diff 2)". Not adopted, and the reason is concrete: it is a
    fixture-only heuristic — every suggestion is one club, `form` is 0.0 for all of them so it is
    ranking on ppg and a single fixture. Man Utd's opener is Hull away at difficulty **2**, the same
    rating as Arsenal–Coventry, and the four-game run behind it is easier (2,2,3,4 vs 2,4,4,3),
    while Bruno's ppg is higher. The MCP's pick is already the vice, so the disagreement is narrow.
- **Club spread:** ARS 2, LEE 2, SUN 2, TOT 2, BRE/CHE/CRY/EVE/MUN/NEW/NFO 1 each. No club at the
  3-player limit.
- **Chelsea loyalty (mode `report`, floor OFF):** forcing 1 costs **0.00** (João Pedro already
  starts on merit), 2 costs **0.18** (adds Sánchez to the bench), 3 costs **0.38** (Chalobah +
  Emegha, neither starting). Reported, not applied, per `config/settings.md`.
- **Squad state:** all 15 flagged `status=a` with empty `news` in live bootstrap data, so the
  availability check is live data rather than missing data.
- **Recorded** to `records/predictions.jsonl` as the GW1 prediction, superseding the identical
  2026-07-29 line.
