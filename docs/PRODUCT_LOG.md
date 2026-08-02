# Product Log

A running product-manager's view of FPL Team Creator: what problem it solves, how it's built, what
we got wrong, and what's still open. Written to be readable by someone who has never seen the code.

Append new entries at the bottom. Don't rewrite history — being able to see a bad decision and its
correction side by side is the point of this file.

---

## The problem

Fantasy Premier League asks a manager to do something people are measurably bad at: pick 15 players
under hard constraints, then repeat the decision every week for 38 weeks under time pressure.

Three distinct difficulties, only one of which is usually acknowledged:

1. **It's a real constrained optimisation.** £100.0m budget, exactly 2 GK / 5 DEF / 5 MID / 3 FWD,
   maximum 3 players per club, and a starting XI that must be a legal formation. Picking "the best
   players" doesn't work, because the binding constraint is nearly always budget allocation rather
   than player quality. Humans solve this by feel and leave points on the table.

2. **The information is scattered and perishable.** Prices, form, injury flags, fixture difficulty
   and ownership all live in different places and change daily. Most managers substitute a small
   number of loud signals — a pundit's tip, last week's hauls — for the full picture.

3. **There is no feedback loop.** This is the one nobody talks about, and it's the reason the other
   two never improve. A manager who takes a -4 hit and scores 60 has no idea whether the hit was
   correct; the outcome is dominated by variance. Without recording *what you predicted before you
   knew the answer*, every week's reasoning is unfalsifiable and next season's is no better.

**What this project is:** an advisory tool that makes a defensible weekly recommendation, writes
down its reasoning and its numeric prediction *before* the gameweek, and then measures itself.

**What it deliberately is not:** it never touches the live FPL account. Every recommendation is
advice; the user makes the move in-game. The MCP integration is read-only by design.

---

## The approach

Four layers, each replaceable without disturbing the others.

| Layer | Module | Responsibility |
|---|---|---|
| Data | `engine/fetch.py` | Pull live state from the public FPL API (no auth) |
| Judgement | `engine/score.py`, `engine/preseason.py` | Turn raw stats into predicted points per player |
| Decision | `engine/optimize.py` | MILP: best legal squad / best 0-2 transfers |
| Measurement | `engine/evaluate.py` | Record predictions, score them against reality |

Around them sit a Claude Code skill (`/fpl-weekly-review`) that runs the weekly process and applies
qualitative judgement the numbers can't, and an append-only `records/` directory that is the
project's durable memory.

### Why a solver rather than heuristics

The squad constraints are exactly the shape of an integer program, so `pulp`/CBC solves them to
proven optimality in under a second. This matters more than it sounds: it means when the
recommendation looks strange, the fault is *always* in the predicted points fed in, never in the
selection. That makes the scoring model the only thing to argue about, which is a much better
place to spend attention.

### Why the scoring model is deliberately simple

`score.py` is a transparent formula, not a learned model, because there is no training data yet.
Every term is one a person can argue with:

```
predicted = expected_points_per_game
          × fixture_multiplier      (opponent difficulty, position-aware, decayed over 4 games)
          × minutes_reliability     (will they actually play)
          × availability            (injury flags, fitness doubts, managerial upheaval)
```

Once `records/predictions.jsonl` holds real gameweeks, measured error becomes the justification for
changing any of these weights. Until then, changes are argued from first principles and logged.

### The one rule that shapes everything

**`score` is predicted points and nothing else.** Anything that isn't points — the risk-profile
preference for template players, for instance — lives in a separate field and is applied as a
tiebreak. We violated this early and it cost us; see Entry 3.

---

## The MCPs

Two MCP servers, with sharply different jobs.

### `fpl` (`uvx fpl-mcp-server`)

Used for **qualitative context the raw API doesn't shape well**: deadlines, injury/press-conference
news, rival and mini-league comparison, richer fixture-run views.

The important design decision is what it is *not* used for. All numeric inputs to the optimizer come
from `engine/fetch.py` calling the FPL API directly. The MCP is a second opinion and a news source,
never the source of truth for prices, form or fixtures.

This earned its keep immediately. **The `fpl` server disconnected mid-session during the first real
run.** Because the pipeline depends only on the direct API, the run continued on `fetch.py` and the
qualitative cross-checks were repeated when the server came back. A stale or broken MCP must never
block fetch → score → optimize, and now demonstrably doesn't.

Boundary worth keeping: the MCP is **read-only**. Nothing in this project is permitted to execute a
transfer against the live account.

### `github`

Used to read and write repository state. The `records/` files are the project's memory, and they're
only useful if they're durable and reviewable, so every weekly run commits and pushes. The log being
GitHub-visible is a feature, not incidental — a decision you can't review later may as well not have
been recorded.

### Where the human/agent boundary sits

The optimizer is deterministic and auditable. Claude's role is the part a solver can't do: reading a
press conference, noticing a manager changed, deciding a flagged risk is worth overriding — and
crucially, *stating the reason explicitly in the log when it overrides the optimizer*. An
unexplained override is indistinguishable from a bug.

---

## The evals

The measurement loop is the part that makes this more than a calculator.

### How it works

1. Every weekly run appends its recommendation to `records/predictions.jsonl` — the XI, the bench in
   auto-sub order, captain, vice, and `predicted_total` (which counts the captain twice, so it is
   directly comparable to a real FPL gameweek score).
2. The following week, `evaluate.py` replays that gameweek's actual per-player points from
   `/event/{gw}/live/` against the stored prediction.
3. The result — predicted vs actual, per-player error, MAE and signed bias — is reported *before*
   this week's recommendation is made, and written to `records/gameweek_reviews.md`.

### Two details that keep the measurement honest

- **Auto-substitutions are applied.** If a starter doesn't play, FPL brings on a bench player under
  specific rules (keepers only swap with keepers; the formation must stay legal). Scoring the
  blanked starter as a zero would report a worse result than the manager actually got, making the
  model look wrong in a way reality wouldn't support.
- **The vice-captain armband transfers.** If the captain doesn't play, the vice is doubled — again,
  matching what actually happens rather than what we predicted would.

Both are tested. It would have been easier to skip them and the numbers would have been quietly,
permanently pessimistic.

### The ordering rule

**Evaluate before recommending.** The skill enforces this as step 2, before data is even fetched for
the new gameweek. The temptation otherwise is to review last week *after* deciding this week, which
turns the review into a justification exercise.

### What it protects against

`calibration()` reports mean error across gameweeks and, importantly, mean *absolute* error
alongside it — a model that is +10 one week and -10 the next has a mean error of zero and is
useless. Persistent bias is the only evidence we'll accept for retuning `score.py`.

### Current status: nothing has been measured yet

The 2026/27 season has not kicked off. `predictions.jsonl` holds two GW1 predictions (the second
supersedes the first) and there is no actual to compare against. Every claim in this document about
model quality is therefore an argument from first principles, not a measured result. **The first
real evidence arrives after GW1.**

---

## Decision log

### Entry 1 — 2026-07-29 — Bench players were being bought with real money

**Symptom:** the optimizer maximised the summed predicted score of all 15 players.

**Why it's wrong:** only the starting XI banks points in a normal gameweek. Summing 15 equally spent
£22.0m of a £100.0m budget on players who score nothing, and left the XI ~1.3 pts/GW weaker. It also
corrupted transfer decisions — a bench upgrade counted at full weight toward justifying a -4 hit.

**Fix:** solve squad and lineup jointly, maximising `XI + 0.15 × bench`.

**Why not zero bench weight:** that swings to the opposite failure, buying four £4.0m players who
never take the pitch and losing points every time an auto-sub fires. 0.15 reflects that a bench
player pays out only via auto-subs or Bench Boost.

**Lesson:** the previous run had carefully sanity-checked player *scores* and never checked how they
were *aggregated*. The total looked healthy at 78.02 precisely because it was counting points that
didn't exist.

### Entry 2 — 2026-07-29 — 164 players were invisible

**Symptom:** 164 of 564 players had `points_per_game` 0 and scored ~0, so they could never be
selected — including Rashford (£7.0m), Kulusevski (£6.5m), N.Jackson (£6.5m).

**Cause:** new signings, returning loanees and players who missed the season injured have no
Premier League record. Scored literally, they rank below a third-choice keeper.

**Fix:** fall back to a price-implied baseline, fitted per run from the live pool (ppg ~ price by
position, correlation 0.73-0.83). FPL prices a signing by expected output, so price is the best free
proxy available. Fitted rather than hardcoded so it recalibrates as prices drift.

**Outcome:** none of the newly-visible players earned a squad place. The search widened without
degrading the pick — which is the right result, and worth stating because a fix that changes nothing
visible is easy to mistake for a fix that did nothing.

### Entry 3 — 2026-07-29 — The headline number was not points

**Symptom:** a user challenged the predicted total as too low, expecting ~72.

**What we found:** the opposite. The reported 69.21 was *inflated*. Ownership was being added
straight into `score` — up to +0.79 points per player — so the total was part points and part
preference. Honest expectation was ~63.8. Separately, a from-scratch optimisation on raw
points-per-game put the **theoretical ceiling for any £100.0m squad at 64.80**, so 72 was not merely
optimistic but unreachable.

**Worse than a cosmetic problem:** it changed picks. Szoboszlai (47.3% owned) outranked Stach while
predicting *fewer* points, 4.62 to 4.82. The squad was being chosen partly on popularity.

**Fix:** `score` is now points only; ownership moved to a `tiebreak` field applied at epsilon 0.02,
enough to separate near-identical players and nothing more. Predicted total became 64.50 — just
under the independently computed ceiling, which is where it should sit.

**Lesson, and the reason this file exists:** a number that looks like points, is summed like points,
and is compared against a -4 hit like points, *must be* points. This one wasn't, for weeks, and the
only reason it surfaced was a user finding the value implausible.

### Entry 4 — 2026-07-29 — The fixture being scored had 25% of the vote

**Symptom:** asked whether Leeds' and Chelsea's away openers were accounted for, we found Leeds
carrying a 1.025 multiplier — a net *boost* — going into an away trip.

**Cause:** `fixture_ease` took a flat mean of the next four fixtures, so the imminent game carried a
quarter of the weight and was outvoted by an easier GW2-4 run.

**Fix:** decay the weights at 0.5 (~53/27/13/7), so next gameweek dominates while keeping some
lookahead — justified because only about one free transfer a week is available to act on it.

**What we correctly did *not* do:** add a home/away term. FPL's FDR already rates the two sides of a
fixture differently (Leeds away at Forest is 3, Forest at home is 2). Venue was present all along;
it was being averaged onto the wrong gameweek. An explicit multiplier would have double-counted.

### Entry 5 — 2026-07-29 — Nothing represented a change of manager

**Symptom:** Man City appointed Enzo Maresca to replace Pep Guardiola, ending a decade under one
manager. The model had no way to express that last season's minutes had become a weak guide.

**Fix:** a `clubs` section in `data/preseason.json` applying a club-wide availability multiplier that
compounds with per-player flags and applies *even to players FPL rates fully fit* — a fitness rating
says nothing about whether a new manager picks someone.

**Explicitly a judgement call:** MCI is set to 0.90. That is not a measurement. It is sized to break
a tie against an equivalent player at a settled club without excluding a genuinely better one. It
was enough to drop both City players from the squad (Semenyo 5.54 → 4.98, Guéhi 5.13 → 4.62).

**Known incompleteness:** eight clubs changed manager in summer 2026 and only Man City is flagged,
because it is the one we were asked about. The others quietly benefit until added.

### Entry 6 — 2026-07-29 — One FDR integer for a keeper and a striker

**Symptom:** a request to model head-to-head records between clubs.

**What we built instead, and why:** H2H was rejected. The FPL API carries no history whatsoever
(`/fixtures/` is current-season only, zero results), so it needs an external scraper; and the
predictive value is weak and unusually confounded this season — both Chelsea and Man City changed
manager, Leeds have moved between divisions, and squads have turned over. FDR already encodes
opponent strength, so H2H would largely re-express it with added noise.

The instinct behind the request was right, though: the opponent *should* matter more specifically.
FDR compresses an opponent into one integer identical for a goalkeeper and a striker, when a clean
sheet depends on how well the opponent attacks and an attacking return on how badly they defend.

**Fix:** a position-aware matchup from FPL's own `strength_attack_*` / `strength_defence_*` fields,
weighted per position, decayed like FDR, and blended at half weight so FDR still anchors the
estimate. First-party data, no scraper, no double-count.

**Currently dormant:** those fields are 0 for every club pre-season, so the code detects a flat
signal and falls back to FDR rather than inventing information from a constant. It activates once
real matches populate them.

### Entry 7 — 2026-07-29 — Recording good data made a player look worse

**Symptom:** caught by a test, not by inspection. A player with a *perfect* pre-season minutes record
scored 2.15, while an identical player with no data at all scored 2.90.

**Cause:** the pre-season minutes blend was applied before the fallback for players with no Premier
League record, so the blend averaged against a raw zero.

**Fix:** reorder so the fallback lands first.

**Lesson:** this class of bug — where supplying more information degrades an estimate — is nearly
invisible to code review and trivial for a property-based test. It's the strongest argument in this
project for tests that assert *directional* behaviour rather than fixed values.

### Entry 8 — 2026-08-02 — Supporting your own club, priced rather than argued

**Symptom:** the user asked to record a favourite club and whether the squad should hold the maximum
allowed from it. Nothing in the model represented fandom, and the obvious implementation — a bonus
on those players' `score` — is exactly the mistake Entry 3 fixed for ownership.

**Fix:** a `min_from_team` floor in `engine/optimize.py`, a hard constraint alongside the quota,
budget and 3-per-club rules. It never touches `score`, so the predicted total stays comparable to
what the squad actually banks and `predictions.jsonl` stays honest.

**The more useful half is `loyalty_cost`.** It solves the squad unconstrained, then once per level,
and reports the drop in predicted points from forcing 1 / 2 / 3 of the club's players. The user
chose to run in that reporting mode rather than switching the floor on — decide with the number
visible, not from a feeling. Measured for Chelsea on the current pre-season pool: **1 costs 0.00
(João Pedro is picked on merit anyway), 2 costs 0.18, 3 costs 0.38 predicted points per gameweek.**
Under a tenth of a point per player — the "supporting my team is expensive" intuition was wrong
here, and only measuring it could have shown that.

**A bug the constraint exposed:** `recommend_transfers` raised on the first infeasible transfer
count, so a floor of 2 against a squad holding none of the club failed the whole search instead of
reporting that it takes 2 transfers to satisfy. Infeasible counts are now skipped; only an entirely
infeasible search errors.

---

## Open risks

| Risk | Impact | Status |
|---|---|---|
| **Nothing has been measured yet** | Every quality claim is theoretical | Resolves after GW1 |
| Player-level pre-season minutes are paywalled (FFS Chief Scout) | The best "who is actually starting" signal is missing; slot left null rather than guessed | Needs a subscription or a different source |
| 7 of 8 new managers unflagged | Those clubs are quietly advantaged | Add as pre-season XIs become readable |
| `MCI: 0.90` is a judgement, not a measurement | Could be over- or under-stated | Revisit once real minutes data exists |
| `form` is 0.0 until GW1 | Everything rests on last season's ppg | Self-resolving |
| Ownership tiebreak may now be too weak | The `safe` risk profile has much less pull than it did | Decide once calibration data exists |

## Principles worth keeping

1. **`score` is points.** Anything else goes in a separate field.
2. **Evaluate before recommending.** Otherwise the review becomes a justification.
3. **Null over a guess.** A missing value is handled; an invented one silently corrupts everything
   downstream and is untraceable later.
4. **Detect flat signals.** A constant is not information. Fall back rather than pretend.
5. **Log the reasoning, not just the decision.** A recommendation you can't audit next month is
   indistinguishable from a coin flip.
6. **The MCP is a second opinion, never the source of truth** for numbers — and never a write path.
