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

## Pre-season (fixture weighting + Man City managerial change) — 2026-07-29

- **Bank:** n/a | **Squad value:** £100.0m | **Free transfers:** unlimited until the GW1 deadline
  (2026-08-21 17:30 UTC) | **Chip active:** none
- **Predicted GW total:** 65.08 (XI 57.89 + captain 7.19)
- **Squad (£100.0m):** GK: David Raya, Martin Dúbravka · DEF: Gabriel Magalhães, Nordi Mukiele,
  Marcos Senesi, Daniel Ballard, Tyrick Mitchell · MID: Bruno Fernandes, Morgan Gibbs-White,
  Bruno Guimarães, Kiernan Dewsbury-Hall, Anton Stach · FWD: João Pedro, Igor Thiago,
  Dominic Calvert-Lewin
- **Starting XI (3-5-2):** Raya; Gabriel, Mukiele, Senesi; Fernandes, Gibbs-White, Guimarães,
  Dewsbury-Hall, Stach; João Pedro, Igor Thiago
- **Bench (auto-sub order):** Ballard, Calvert-Lewin, Mitchell, Dúbravka
- **Captain:** Bruno Fernandes | **Vice:** Gabriel Magalhães
- No Man City players remain after the managerial-change flag; club spread is now
  ARS 2, LEE 2, SUN 2, TOT 2, BRE/CHE/CRY/EVE/MUN/NEW/NFO 1 each.
- Recorded to `records/predictions.jsonl` (supersedes the earlier GW1 line from the same day).

## GW1 pre-season re-run (unchanged) — 2026-08-02

- **Bank:** n/a | **Squad value:** £100.0m | **Free transfers:** unlimited until the GW1 deadline
  (2026-08-21 17:30 UTC) | **Chip active:** none
- **Predicted GW1 total:** 65.081 (XI 57.890 + captain 7.191)
- **Squad (£100.0m):** GK: David Raya, Martin Dúbravka · DEF: Gabriel Magalhães, Nordi Mukiele,
  Marcos Senesi, Daniel Ballard, Tyrick Mitchell · MID: Bruno Fernandes, Morgan Gibbs-White,
  Bruno Guimarães, Kiernan Dewsbury-Hall, Anton Stach · FWD: João Pedro, Igor Thiago,
  Dominic Calvert-Lewin
- **Starting XI (3-5-2):** Raya; Gabriel, Mukiele, Senesi; Fernandes, Gibbs-White, Guimarães,
  Dewsbury-Hall, Stach; João Pedro, Igor Thiago
- **Bench (auto-sub order):** Ballard, Calvert-Lewin, Mitchell, Dúbravka
- **Captain:** Bruno Fernandes | **Vice:** Gabriel Magalhães
- Identical to the 2026-07-29 snapshot; recorded so the history stays continuous rather than
  implying the week went unreviewed. Chelsea loyalty floor available but off (forcing 3 would
  cost 0.38 predicted points).

## User's actual GW1 draft (as built in the FPL app) — 2026-08-02

Recorded because it is the first sight of the real entry: the app draft differs from the engine's
recommendation, and the gap is the more useful record. Not a recommendation — this is what the user
actually has.

- **Squad value:** £100.0m exactly | **Free transfers:** unlimited until the GW1 deadline
  (Fri 21 Aug 23:00 local = 17:30 UTC) | **Chips:** Bench Boost and Triple Captain available;
  Wildcard and Free Hit unavailable (normal — the first wildcard unlocks after GW1)
- **Squad:** GK: Raya (ARS), Petrović (BOU) · DEF: Pedro Porro (TOT), Tarkowski (EVE),
  Gabriel (ARS), Mukiele (SUN), Milenković (NFO) · MID: Mbeumo (MUN), Rogers (CHE), Cunha (MUN),
  Dewsbury-Hall (EVE), Rice (ARS) · FWD: João Pedro (CHE), Calvert-Lewin (LEE), Igor Thiago (BRE)
- **XI as picked (4-4-2):** Raya; Porro, Tarkowski, Gabriel, Mukiele; Mbeumo, Rogers, Cunha,
  Dewsbury-Hall; João Pedro, Calvert-Lewin. **Captain:** João Pedro | **Vice:** Raya
- **Legal:** 2/5/5/3 quotas correct, £100.0m on the nose, ARS at 3 (the limit, not over it).
- **Predicted GW1 as picked: 57.43** vs the engine's from-scratch squad at 65.08. 7 of the 15
  overlap (Raya, Gabriel, Mukiele, Dewsbury-Hall, João Pedro, Calvert-Lewin, Igor Thiago).

## GW1 revised — xGI blend applied to MID/FWD — 2026-08-02

- **Bank:** n/a | **Squad value:** £100.0m | **Free transfers:** unlimited until the GW1 deadline
  (2026-08-21 17:30 UTC) | **Chip active:** none
- **Predicted GW1 total:** 65.215 (XI 57.765 + captain 7.45). Level is deliberately unchanged from
  the previous 65.081 — the blend re-orders within a position, it does not re-level. See
  `gameweek_reviews.md`.
- **Squad (£100.0m):** GK: David Raya, Martin Dúbravka · DEF: Gabriel Magalhães, Nordi Mukiele,
  Marcos Senesi, Daniel Muñoz, Daniel Ballard · MID: Bruno Fernandes, Bryan Mbeumo,
  Morgan Gibbs-White, Bruno Guimarães, Enzo Fernández · FWD: João Pedro, Dominic Calvert-Lewin,
  Chido Obi
- **Starting XI (4-5-1):** Raya; Gabriel, Mukiele, Senesi, Muñoz; Fernandes, Mbeumo, Gibbs-White,
  Guimarães, Enzo Fernández; João Pedro
- **Bench (auto-sub order):** Ballard, Calvert-Lewin, Obi, Dúbravka
- **Captain:** Bruno Fernandes (7.45) | **Vice:** Gabriel Magalhães (6.59)
- **Changes from the previous snapshot:** IN Mbeumo, Muñoz, Enzo Fernández, Obi ·
  OUT Dewsbury-Hall, Stach, Igor Thiago, Mitchell. Club spread MUN 3 (at the limit),
  ARS/CHE/TOT/SUN 2, CRY/LEE/NEW/NFO 1.
- Bench cost £19.5m. Recorded to `records/predictions.jsonl`, superseding the 65.081 line.
