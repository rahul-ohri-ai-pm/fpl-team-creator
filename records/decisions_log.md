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
