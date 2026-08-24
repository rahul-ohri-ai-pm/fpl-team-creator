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

## GW1 review (draft) — 2026-08-24 — PREMATURE, see correction below

- **Points scored:** 37 | **Bench:** 20 pts (unused) | **Rank:** 3,926,627
- **What worked:** 
  - Gabriel + Raya (Arsenal defence) solid base
  - João Pedro gamble (0.98 predicted) hit value, showed up in bench points
  - Mbeumo + Gibbs-White performed near expectations
- **What didn't:** 
  - **Massive model underperformance:** Predicted 61.54, actual 37 (-40% variance)
  - Enzo scored 0 (didn't play/benched in GW1) — major flag for GW2
  - Mukiele returning from injury, barely played (0.04 GW2 score)
  - Early-season `form` data still 0.0; model relying entirely on last-season ppg caused systematic over-estimate
  - New signings (João Pedro) and promoted-team players (Stach, Calvert-Lewin) invisible to pre-season model
- **Model bias identified:** Pre-season scoring over-weighted last-season ppg by ~25 pts on this squad
- **Lesson for next run:** 
  - Don't trust raw ppg for early gameweeks — form accumulates after GW2-3 with real match data
  - Flag players who didn't play (Enzo 0 pts) as forced transfers into GW2
  - Injury flags (Mukiele 75% available) should trigger auto-swap if FPL updates confirm benching
  - Recalibrate risk profile post-GW1 if `safe` produced >35% variance

### Correction — 2026-08-24 (same day)

**This entry was written before GW1 actually finished and its headline numbers are wrong.**
`bootstrap['events'][0]['finished']` was `False` at the time, and Chelsea's fixture (Fulham vs
Chelsea, kickoff 2026-08-24T19:00Z) hadn't been played yet — it kicked off *after* this entry was
logged. The "37 pts" total was provisional (9 of 10 GW1 fixtures were only
`finished_provisional`, not officially `finished`), and "Enzo scored 0 / benched" was actually
"Enzo's match is still 0-0 in-progress." Direct bootstrap check on Enzo: `status: a`,
`chance_of_playing_next_round: None`, `news: ''` — fully fit, no rotation/injury signal at all.
The -40% "model underperformance" conclusion above should not be trusted until GW1 is confirmed
`finished` and re-scored against the final total.

**Actual flag missed by this draft:** Morgan Gibbs-White (MID, Nott'm Forest) — `status: d`, knee
injury, 75% chance of playing, news posted 2026-08-24T15:30Z, *after* the "performed near
expectations" line above was written.

**Real lesson for next run:** check `event['finished']` (and ideally each fixture's `started`/
`finished_provisional` flags) before writing a "points scored" review — a gameweek with a
postponed/delayed fixture is not done just because its deadline has passed. Also pull
`status`/`news`/`chance_of_playing_next_round` from bootstrap for every squad player directly,
rather than inferring injury/rotation risk from a raw points total.

