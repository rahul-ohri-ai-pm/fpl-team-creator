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

## Pre-season (unchanged, pre-season data layer applied) — 2026-07-29

- **Bank:** n/a | **Squad value:** £100.0m | **Free transfers:** unlimited until the GW1 deadline
  (2026-08-21 17:30 UTC) | **Chip active:** none
- **No change** to the 15 in the entry above; re-confirmed after adding the pre-season layer
  (`data/preseason.json`, `engine/preseason.py`). Recorded here so the snapshot history stays
  continuous rather than implying the squad went unreviewed.
- **Starting XI (4-5-1):** Raya; Gabriel, Guéhi, Mukiele, Muñoz; Fernandes, Semenyo, Szoboszlai,
  Guimarães, Wilson; João Pedro
- **Bench (auto-sub order):** Calvert-Lewin, Mitchell, Richarlison, Dúbravka
- **Captain:** Bruno Fernandes | **Vice:** Gabriel Magalhães
- 0 of the 15 have zero Premier League minutes, i.e. no unproven players entered the squad once
  the price baseline made 164 of them selectable.

## Pre-season (post ownership-tiebreak fix) — 2026-07-29

- **Bank:** n/a | **Squad value:** £100.0m | **Free transfers:** unlimited until the GW1 deadline
  (2026-08-21 17:30 UTC) | **Chip active:** none
- **Predicted GW total:** 64.50 (XI 57.64 + captain 6.87). This is now pure predicted points —
  earlier entries' higher totals included an ownership term that was never points.
- **Squad (£100.0m):** GK: David Raya, Bart Verbruggen · DEF: Gabriel Magalhães, Marc Guéhi,
  Marcos Senesi, Nordi Mukiele, Tyrick Mitchell · MID: Bruno Fernandes, Antoine Semenyo,
  Bruno Guimarães, Harry Wilson, Anton Stach · FWD: João Pedro, Dominic Calvert-Lewin, Richarlison
- **Starting XI (4-5-1):** Raya; Gabriel, Guéhi, Senesi, Mukiele; Fernandes, Semenyo, Guimarães,
  Wilson, Stach; João Pedro
- **Bench (auto-sub order):** Calvert-Lewin, Richarlison, Mitchell, Verbruggen
- **Captain:** Bruno Fernandes | **Vice:** Gabriel Magalhães
- Recorded to `records/predictions.jsonl` as the GW1 prediction for measurement after the gameweek.
