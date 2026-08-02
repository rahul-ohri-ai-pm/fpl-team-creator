# Architecture

How the pieces fit together and why the boundaries sit where they do. For the product reasoning
behind these choices see [PRODUCT_LOG.md](PRODUCT_LOG.md).

## Data flow

```
                    ┌────────────────────────────────────────────┐
                    │  fantasy.premierleague.com/api  (no auth)   │
                    └───────────────────┬────────────────────────┘
                                        │
                            engine/fetch.py
                    bootstrap-static · fixtures · entry
                    entry history · event/{gw}/live
                                        │
              ┌─────────────────────────┼──────────────────────────┐
              │                         │                          │
    data/preseason.json        engine/score.py            engine/evaluate.py
   friendlies · minutes  ────►  predicted points  ◄──── predicted vs actual
   fitness · club flags         per player                       ▲
              ▲                          │                        │
    engine/preseason.py                  ▼                records/predictions.jsonl
    price baseline for         engine/optimize.py                 │
    players with no record      MILP: squad + XI                  │
                                         │                        │
                                         ▼                        │
                              recommendation ──────────────────────┘
                                         │
                              records/*.md  (append-only)
```

The `fpl` MCP server sits alongside this, not inside it — see [MCP boundary](#mcp-boundary).

## Modules

| Module | Lines | Responsibility |
|---|---|---|
| `engine/fetch.py` | ~140 | Every call to the FPL API. Nothing else makes network requests. |
| `engine/score.py` | ~240 | Predicted points per player. The only place judgement about players lives. |
| `engine/preseason.py` | ~130 | Pre-season signal the API can't carry, plus the price-implied baseline. |
| `engine/optimize.py` | ~220 | MILP squad selection, lineup, and transfer search. No player judgement. |
| `engine/evaluate.py` | ~200 | Recording predictions and measuring them. Deliberately import-independent of the solver. |

### `fetch.py` — the only network boundary

Keeping every request in one module means the rest of the codebase is trivially testable offline.
All 90 tests run without network access.

One piece of real logic lives here: `free_transfers()`. The public API exposes no free-transfer
balance — that only exists on the authenticated `my-team` endpoint, which this project deliberately
never touches. So the count is replayed from the entry's transfer history under the roll-over rules
(one per week, capped at 5, with GW1 and chip weeks handled specially).

### `score.py` — predicted points, and nothing else

```
predicted = expected_ppg × ease_mult × reliability × availability
```

| Term | Source | Notes |
|---|---|---|
| `expected_ppg` | `form`, else `points_per_game`, else price baseline | `form` is 0.0 until GW1 |
| `ease_mult` | FDR blended with position-aware opponent strength | 0.8 – 1.2, decayed over 4 fixtures |
| `reliability` | Minutes played, blended with pre-season minutes | Falls back to 0.55 for unknowns |
| `availability` | FPL `chance_of_playing`, else pre-season flag, × club flag | FPL wins when it has an opinion |

`score` carries no non-points terms. The risk-profile ownership preference is returned separately as
`tiebreak` and applied by the optimizer at `OWNERSHIP_TIEBREAK_EPSILON` (0.02).

**Source precedence:** FPL's own data beats our editorial files. If FPL sets
`chance_of_playing_next_round`, a hand-written availability flag is ignored — it's the harder source.
Club-level flags are the exception and still apply, because a fitness rating says nothing about
whether a new manager picks someone.

### `optimize.py` — decisions, no judgement

Two MILPs via `pulp`/CBC:

- `optimal_squad` solves squad **and** starting XI together, maximising `XI + 0.15 × bench`. Solving
  them separately would misprice every bench slot, because you can't value a bench player without
  knowing who starts.
- `best_lineup` picks the legal XI, captain and vice from a fixed 15.

`recommend_transfers` searches 0–2 transfers and scores each option on the same quantity minus the
hit cost, so the comparison against -4 is in real points. A transfer count that can't satisfy the
constraints (a favourite-club floor, a tight bank) is skipped, not fatal — only a search where every
count is infeasible raises.

`loyalty_cost` re-solves the squad with a club floor of 1, 2 and 3 and reports the drop against the
unconstrained optimum, so a favourite-club preference can be priced in predicted points before it's
switched on.

Because the constraints are solved to proven optimality, **a strange recommendation is always a
scoring problem, never a selection problem.** That's the main reason to use a solver here.

### `evaluate.py` — measurement

Deliberately does not import `optimize.py`, so evaluation never depends on a solver being
installable. It re-declares the formation limits rather than share them; the duplication is worth
the isolation.

`records/predictions.jsonl` is append-only, one JSON object per line — a format that survives
concurrent appends and preserves every past prediction verbatim. Re-running a gameweek appends a
second line rather than overwriting; the reader takes the latest, and the superseded one stays
visible.

## MCP boundary

| Concern | Source |
|---|---|
| Prices, form, fixtures, squad state, actual points | `engine/fetch.py` — **always** |
| Deadlines, injury news, rival comparison, fixture-run views | `fpl` MCP |
| Repository state | `github` MCP |

The `fpl` MCP is a second opinion and a news source, never the source of truth for numbers. It
disconnected mid-session during the first real run and the pipeline continued uninterrupted, which
is the behaviour the boundary exists to guarantee.

**The MCP is read-only. Nothing in this project may execute a transfer against the live account.**

## Configuration

Tunables are named constants at the top of their module, not scattered literals:

| Constant | Module | Value | Meaning |
|---|---|---|---|
| `BENCH_WEIGHT` | `optimize` | 0.15 | Bench value relative to a starter |
| `OWNERSHIP_TIEBREAK_EPSILON` | `optimize` | 0.02 | Strength of the ownership lean |
| `FIXTURE_DECAY` | `score` | 0.5 | How fast fixture influence falls off |
| `MATCHUP_WEIGHT` | `score` | 0.5 | Position matchup vs FDR |
| `POSITION_MATCHUP` | `score` | table | Per-position weight on opponent attack/defence |
| `PRESEASON_MINUTES_WEIGHT` | `preseason` | 0.4 | Friendly minutes vs last season |
| `UNKNOWN_RELIABILITY` | `preseason` | 0.55 | Assumed reliability with no record |
| `CLUB_LIMIT` | `optimize` | 3 | FPL's cap on players from one club |

User-facing settings (team ID, risk profile, hit tolerance, favourite club and loyalty mode) live in
`config/settings.md`.

Two preferences that are *not* predicted points are deliberately kept out of `score`: the ownership
lean (applied as `tiebreak` at `OWNERSHIP_TIEBREAK_EPSILON`) and the favourite-club floor (applied
as `optimize.min_from_team`, a hard constraint). Both stay outside the score so squad totals remain
comparable with real FPL points. `optimize.loyalty_cost` prices the club floor in predicted points
before anyone decides to switch it on.

## Testing

90 tests, no network, no fixtures on disk — synthetic payloads throughout.

| File | Tests | Covers |
|---|---|---|
| `test_optimize.py` | 29 | Quotas, budget, club limits, formation legality, objective, transfers, fixture decay, favourite-club floor and its cost |
| `test_preseason.py` | 22 | File loading, price baseline, minutes blend, player and club flags |
| `test_evaluate.py` | 15 | Recording, auto-subs, armband, bench exclusion, calibration |
| `test_matchup.py` | 13 | Normalisation, position separation, venue mirroring, flat-field fallback |
| `test_free_transfers.py` | 11 | Roll-over rules, cap, chip weeks |

Many assert **directional** behaviour rather than fixed values — "a benched player must score less
than a nailed-on one" rather than "must equal 4.82". Those catch the class of bug where supplying
more information degrades an estimate, which is close to invisible in review. One such bug was
caught exactly this way; see Product Log entry 7.
