# Ceiling-Signal Backtest Log

Tests whether a per-gameweek "ceiling" signal (`threat`, `bps`, `ict_index`) predicts the
**next** gameweek's points better than a player's own actual points did — the gap surfaced by
research into why our GW1/GW2 scores looked ordinary next to a rival's chip-fuelled 161-point
week (see `records/decisions_log.md`'s GW3 entry and the deep-research finding it cites).
`engine/score.py`'s `form` is backward-looking box-score points; it carries no signal that could
separate "consistent 5-pointer" from "capable of a 20-point haul" independent of whether that
haul already happened. Methodology and code: `engine/ceiling_signal_backtest.py`.

**Data constraint**: FPL wipes per-gameweek granularity at each season's rollover — only season
aggregates survive for a *prior* season (see `engine/backtest.py`'s docstring, which hit the same
wall for its xGI study). Per-gameweek data only exists for the *current* season's finished
gameweeks, via `/event/{n}/live/`. That means this backtest necessarily starts thin (one GW-to-GW
transition per run right now) and gains a transition every week — re-run it each week and this
log accumulates real, compounding evidence rather than resetting.

<!--
Template for each new entry:

## GW{N}→GW{N+1} — {YYYY-MM-DD}

- **Data:** ...
- **Results:** ...
- **Recommendation:** ...
-->

## GW1→GW2 — 2026-09-01

**Data:** `python engine/ceiling_signal_backtest.py --from 1 --to 2` — 210 players with ≥60
minutes in GW1, matched against their GW2 actual points. **Caveat:** GW2 is not yet marked
`finished` in bootstrap (`data_checked: False`) even though its points have posted and match play
finished days ago — treated as reliable per the same reasoning already applied elsewhere this
session (GW2's official entry-history points and the GW3 weekly review both used this data), but
flagged here per the verification loop rather than silently assumed.

**Results (correlation of GW1 signal vs GW2 actual points, by position):**

| Position | n | `points` (baseline) | `threat` | `bps` | `ict_index` |
|---|---|---|---|---|---|
| GK | 20 | 0.385 | n/a (no variance) | **0.451** | 0.242 |
| DEF | 85 | 0.108 | -0.041 | 0.109 | -0.029 |
| MID | 86 | **-0.004** | **0.277** | 0.082 | **0.285** |
| FWD | 19 | 0.031 | **0.430** | -0.055 | 0.253 |
| ALL | 210 | 0.075 | 0.219 | 0.116 | 0.207 |

**Top-decile "big haul" (≥10 pts) hit rate next gameweek, vs the pool's 6.2% baseline:** `points`
14.3%, `threat` 14.3%, `bps` 9.5%, `ict_index` 9.5% (n=21 per decile).

**Finding:** for **MID and FWD**, a player's own recent actual points are essentially useless for
predicting next week's points (correlation ≈0 — GW1 output tells you almost nothing about GW2
output for an attacker). `threat` and `ict_index`, by contrast, carry real signal (0.25–0.43) that
`form` never sees. This is exactly the gap the research finding described, now backed by a real
number instead of a general claim. For **DEF**, none of the four signals predict anything
(clean-sheet-driven scoring is a team-defensive outcome these individual attacking metrics can't
capture — consistent with why `score.py` already leans on fixture ease/opponent matchup for
defenders rather than a player-level attacking stat). For **GK**, `bps` modestly beats raw points
(saves-driven bonus is a real, if small-sample, signal); not currently acted on given n=20.

**Recommendation: not enough evidence to change `engine/score.py` yet.** This is one GW-to-GW
transition — real and reasonably powered cross-sectionally (n=86 MID, n=19 FWD is thinner), but a
single week can be shaped by that week's own fixture particulars rather than a stable pattern.
Per this project's own established practice (declining the Sangaré/De Cuyper swap in GW2 for
identical reasoning, and the GW1 weight-scheme backtest's explicit "re-run after GW2/GW3" caveat),
**do not treat a single transition as a verdict.** Re-run
`python engine/ceiling_signal_backtest.py --from 2 --to 3` once GW3 finishes and append a new
entry here. If the MID/FWD pattern (threat/ict beating raw points, DEF signal-free) holds across
2–3 more transitions, that's real grounds for a `/score-calibrate`-logged change — most plausibly
blending `threat`/`ict_index` into the MID/FWD `form` term the same way `XGI_BLEND` already blends
season-level xGI into `ppg`, not replacing `form` outright.
