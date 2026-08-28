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

## GW2 Decision (draft) — 2026-08-24 — SUPERSEDED, see correction below

**Transfers:** 1 free transfer (available: 1)
- **OUT:** Enzo Fernández (MID, Chelsea, £7.0m) — scored 0 in GW1, major red flag
- **IN:** Dominik Szoboszlai (MID, Liverpool, £7.0m) — nailed starter, 1.00 predicted GW2, Liverpool friendly GW2 run

**Reasoning:**
- Enzo's 0-point performance in GW1 is a forced transfer signal (either benched or injured)
- Same price swap (no budget impact) to a proven nailed player on better form
- Szoboszlai aligns with "safe" profile (high ownership, clear role in Liverpool's midfield hierarchy)
- Liverpool's GW2 run (Newcastle, Fulham, Brighton) is favorable

**Risk:** Early-season model still calibrating (form data = 0.0), so GW2 scores are heavily weighted to last-season ppg. Actual variance will likely be high.

**Other considerations (deferred to GW3):**
- Mukiele (0.04 GW2 score): Returning from injury, worth monitoring but risky to swap with £0 bank
- João Pedro (0.98): Gamble on new signing paying off; hold through GW2-3 for form data
- Bench depth (Roefs, Stach): Accept as necessary insurance given £0 bank constraint

**Squad value post-transfer:**
- Bank: £0.0m
- Squad value: £100.0m (unchanged)
- Starting XI estimated: ~37-40 pts (based on early-season variance)

## Correction — 2026-08-24 (same day)

**This draft was premature and is superseded.** Two things were wrong when it was written:

1. **GW1 was not finished.** `bootstrap['events'][0]['finished']` was `False` and Chelsea's
   fixture (Fulham vs Chelsea) had not kicked off yet at review time — it kicked off at
   2026-08-24T19:00Z, after this entry was drafted. The "37 pts, Enzo scored 0" read was
   provisional, not final. Enzo's 0 was "match not yet played," not a benching.
2. **Enzo has no injury/rotation flag.** Direct bootstrap check: `status: a`,
   `chance_of_playing_next_round: None`, `news: ''`. There was no fitness reason to transfer him
   out — the draft above treated a live-match zero as a red flag.

**No transfer has actually been made** — the user confirmed the free transfer is still unused,
which is the correct call. **Real flag found instead:** Morgan Gibbs-White (MID, Nott'm Forest) —
`status: d`, knee injury, 75% chance of playing, news posted 2026-08-24T15:30Z.

**Revised decision: HOLD.** GW2 deadline is 2026-08-28T17:30Z — 4 days out, no need to decide now.
- Do not transfer Enzo — he's fully fit; his GW1 zero will resolve once tonight's Chelsea match
  finishes.
- Watch Gibbs-White's status over the next few days; re-check nearer the deadline before deciding
  whether a -4 hit (0 free transfers would remain if used) is justified. Per `config/settings.md`
  hit tolerance, only take it if the swap's predicted gain over 3 GWs exceeds 4 points combined.
- Do not captain/vice Gibbs-White while he's doubtful.

**Lesson:** the weekly-review skill should check `event['finished']` and each live fixture's
`started`/`finished_provisional` status before treating a gameweek's points as final, and should
pull `status`/`news`/`chance_of_playing_next_round` from bootstrap directly for every squad player
rather than inferring injury/rotation risk from a raw points total.

## GW2 — 2026-08-28

**Decision:** Transferred Nordi Mukiele (DEF, Sunderland, £5.5m) → Maxim De Cuyper (DEF,
Brighton, £4.6m). Held the optimizer's suggested second transfer (Enzo Fernández → M.Sangaré).

**Hit taken:** 0 (1 free transfer used, 1 free transfer was available — no hit).

**Reasoning:**
- **Mukiele → De Cuyper (taken):** Mukiele played 0 minutes in GW1 for Sunderland — a genuine
  squad-role signal (dropped from the matchday XI), not just a form dip. De Cuyper played 77
  minutes and returned a goal + assist + clean sheet. Budget-neutral-ish (frees £0.9m). This
  transfer stands on non-form grounds alone.
- **Enzo → Sangaré (declined, overriding the optimizer):** `engine.optimize.recommend_transfers`
  picked this as part of a 2-transfer, -4 combo with a net score of 90.04 vs 81.36 for the
  1-transfer-only option — a +8.68 edge even after the hit. **Declined it anyway.** Both
  Sangaré (14 pts) and De Cuyper (17 pts) are one-game samples (75 and 77 minutes respectively) —
  exactly the small-sample overfitting risk documented in `records/scoring_backtest.md`'s GW1
  backtest (Baseline scheme: +43% bias, driven by the same fallback-to-raw-recent-output pattern).
  The `fpl` MCP's own transfer analysis called Sangaré "⚖️ Consider — close call," not a clear buy.
  Enzo carries no injury/rotation flag (`status: a`, fully fit, nailed) and just had a quiet
  personal game. Per `config/settings.md`'s hit tolerance ("only take a -4 hit if the predicted
  gain over the next 3 gameweeks exceeds 4 points combined"), `recommend_transfers` only optimizes
  a *single* gameweek's net score — it has no 3-gameweek projection to actually confirm that
  threshold, so the model's one-GW edge here isn't sufficient evidence to spend a hit on a
  one-game riser. Revisit Sangaré after 2-3 more gameweeks of sustained returns.
- **Gibbs-White:** re-checked bootstrap directly before this decision — unchanged since
  2026-08-24 (`status: d`, 75% chance, same knee-injury news). His score already reflects the 75%
  `injury_mult` discount; he remains a starter (best available MID score even discounted) but is
  **not** captain or vice.
- **Captain/Vice override:** `engine.optimize.best_lineup` auto-selected De Cuyper as captain
  purely on his (one-game-inflated) predicted score — declined for the same small-sample reason
  as the transfer above, and because it directly contradicts the `safe` risk profile's own
  preference for high-ownership picks (De Cuyper: 7.6% owned vs João Pedro: 67.7% owned). Set
  **Captain: João Pedro** (home vs Brighton, fixture difficulty 2, genuine goal involvement in
  GW1, nailed) and **Vice: Gabriel** (highly-owned, nailed, set-piece threat, despite a tougher
  fixture at Villa).

**Optimizer net score (post-hit):** 81.36 (1-transfer squad, 0 hit) — declined the higher raw
92.04/net-90.04 2-transfer option for the reasons above; this is a deliberate override, not a
model error.

## Model calibration — 2026-08-28

**Decision:** Applied 3 bug fixes surfaced by a `code-reviewer` subagent pass over the scoring/
transfer workflow, rather than a weight-scheme swap. All three were correctness bugs, not
calibration choices, so no `/score-calibrate` run was needed to justify them.

1. **`engine/fetch.py`'s `free_transfers()`** — the weekly `+1` roll-over was applying even on a
   Wildcard/Free Hit gameweek, inflating the derived free-transfer count by 1 every time a chip
   was played (and compounding forward through later weeks). Real FPL rule: a chip week leaves the
   count unchanged. Fixed; `tests/test_free_transfers.py`'s two chip-week cases (previously pinned
   to the buggy incremented value) now assert the correct kept value.
2. **`engine/score.py`'s `form == 0` fallback** — fired any time `form` was exactly 0, not just
   pre-season, so a genuine mid-season scoring slump got silently overridden by a stale season-long
   `points_per_game` average. Gated on `finished == 0` (season stage) instead. New
   `tests/test_score.py` added — this project had no dedicated scoring-formula test file before.
3. **`engine/score.py` + `engine/backtest.py`'s ownership term** — added after `injury_mult` had
   already been applied, so a confirmed-out player (`chance_of_playing_next_round == 0`) still
   carried a positive score from ownership alone. Now the whole prediction (including ownership) is
   scaled by `injury_mult`. See `records/scoring_backtest.md`'s "Formula correction" entry for the
   before/after GW1 backtest numbers — only Conservative's metrics moved (RMSE 4.30→4.24, bias
   +0.97→+0.40), recommendation unchanged.

**Not applied in this pass** (subagent attempts hit an environment issue — worktree isolation
branched from an unrelated `master` fork instead of this session's branch, so 3 of 5 planned fixes
were re-derived and applied directly instead of merged): two documentation fixes remain queued —
adding a verification-loop step to `.claude/skills/fpl-weekly-review/SKILL.md` and pointing
`.claude/skills/gw-backtest/SKILL.md` at `engine/backtest.py` instead of describing hand-computation.

**Test status:** `pytest tests/ -q` — 42 passed (was 38; +4 from the new `tests/test_score.py`).

