# Team History

Append-only log of squad snapshots. One entry per run of `/fpl-weekly-review`.

<!--
Template for each new entry:

## GW{N} — {YYYY-MM-DD}

- **Bank:** £{X.X}m | **Squad value:** £{X.X}m | **Free transfers:** {N} | **Chip active:** {none/wildcard/...}
- **Squad:** GK: ..., DEF: ..., MID: ..., FWD: ...
- **Starting XI ({formation}):** ...
- **Captain:** {name} | **Vice:** {name}
-->

## Pre-season — 2026-07-29

- **Season hasn't started yet** (GW1 deadline not passed) — no bank/value/free-transfers data from
  the API yet. Squad below is the optimizer's from-scratch recommendation using last season's
  points-per-game as the scoring base (this season's `form` is still 0 - see decisions_log).
- **Squad (£100.0m):** GK: Robin Roefs, Caoimhín Kelleher · DEF: Gabriel Magalhães, Marc Guéhi,
  Nordi Mukiele, Daniel Muñoz, Jan Paul van Hecke · MID: Bruno Fernandes, Dominik Szoboszlai,
  Bruno Guimarães, Harry Wilson, Anton Stach · FWD: João Pedro, Igor Thiago, Dominic Calvert-Lewin
- **Starting XI (4-4-2):** Roefs; Gabriel, Guéhi, Mukiele, Muñoz; Fernandes, Szoboszlai,
  Guimarães, Wilson; João Pedro, Igor Thiago (bench: Kelleher, van Hecke, Stach, Calvert-Lewin)
- **Captain:** Bruno Fernandes | **Vice:** Gabriel Magalhães

## Pre-season (re-run) — 2026-07-29

- **Bank:** n/a | **Squad value:** £100.0m | **Free transfers:** unlimited until the GW1 deadline
  (2026-08-21 17:30 UTC) | **Chip active:** none
- **Season still hasn't started**, so the API returns no bank/value/picks for the entry. Squad below
  is the optimizer's from-scratch draft after the objective fix logged in `decisions_log.md`;
  it supersedes the earlier 2026-07-29 snapshot above.
- **Squad (£100.0m):** GK: David Raya, Martin Dúbravka · DEF: Gabriel Magalhães, Marc Guéhi,
  Nordi Mukiele, Daniel Muñoz, Tyrick Mitchell · MID: Bruno Fernandes, Antoine Semenyo,
  Dominik Szoboszlai, Bruno Guimarães, Harry Wilson · FWD: João Pedro, Dominic Calvert-Lewin,
  Richarlison
- **Starting XI (4-5-1):** Raya; Gabriel, Guéhi, Mukiele, Muñoz; Fernandes, Semenyo, Szoboszlai,
  Guimarães, Wilson; João Pedro
- **Bench (auto-sub order):** Calvert-Lewin, Mitchell, Richarlison, Dúbravka
- **Captain:** Bruno Fernandes | **Vice:** Gabriel Magalhães
- All 15 flagged `status=a` (available) with no news at time of writing; 24 injured / 19 doubtful /
  3 suspended elsewhere in the pool, so the flags are live data, not missing data.

## GW2 Squad (Post-Transfer) — 2026-08-24

**Transfers made:** Enzo → Szoboszlai (1 free transfer used, 0 remaining)

**Squad (15 players):**
- GK: Raya (ARS, £6.0m), Roefs (SUN, £5.0m)
- DEF: Mukiele (SUN, £5.5m), Gabriel (ARS, £8.0m), Senesi (TOT, £6.0m), van Dijk (LIV, £6.5m), Tarkowski (EVE, £6.0m)
- MID: Szoboszlai (LIV, £7.0m), Mbeumo (BRE, £8.0m), Gibbs-White (NFO, £8.0m), Dewsbury-Hall (EVE, £6.5m), Stach (LEE, £6.0m)
- FWD: João Pedro (CHE, £7.5m), Calvert-Lewin (LEE, £6.0m), Thiago (BRE, £8.0m)

**Projected Starting XI (GW2):**
- GK: Raya (ARS)
- DEF: Gabriel (ARS), van Dijk (LIV), Senesi (TOT), Tarkowski (EVE), Mukiele (SUN)
- MID: Szoboszlai (LIV), Mbeumo (BRE), Gibbs-White (NFO), Dewsbury-Hall (EVE)
- FWD: João Pedro (CHE)

**Bench:** Roefs (GK), Stach (MID), Calvert-Lewin (FWD), Thiago (FWD)

**Captain:** Gabriel (ARS, 0.65 GW2 projected)
**Vice-Captain:** Szoboszlai (LIV, 1.00 GW2 projected)

**Financial:**
- Bank: £0.0m
- Squad value: £100.0m
- Free transfers remaining: 0
- Chips remaining: Wildcard x2, Free Hit, Bench Boost, Triple Captain

**Notes:**
- Formation: 5-4-1 (defensive-heavy due to budget constraints)
- Club distribution: Arsenal 2, Brentford 1, Chelsea 1, Everton 2, Leeds 2, Liverpool 2, Spurs 1, Sunderland 2 (at 3-club limit)
- Early-season model calibration ongoing — expect high variance week-to-week until GW3-4

