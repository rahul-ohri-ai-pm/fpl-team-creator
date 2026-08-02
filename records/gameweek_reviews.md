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

## Pre-season re-run — 2026-08-02

- **Points scored:** n/a | **Rank movement:** n/a — still no played gameweek. GW1 deadline is
  2026-08-21 17:30 UTC, 19 days out. `evaluate_gameweek` returns `None` for every event, so there
  is nothing to measure and no calibration data yet. Recorded so the log stays continuous.
- **What held up:** the model is stable. Re-running the full pipeline four days after the last
  entry reproduces the same 15, the same XI, the same captain and the same 65.08 predicted total.
  Nothing in the inputs moved — `form` is still 0.0 league-wide, prices haven't shifted, and no
  injury flags changed on the squad.
- **What that stability does *not* prove:** it is the same last-season `points_per_game` data
  producing the same answer, not evidence the answer is right. The previous entry's warning stands
  — re-run close to the deadline, because pre-season is when the inputs are weakest.
- **Two model limits made explicit this week** (detail in `decisions_log.md`):
  - New signings cannot be selected at any price. `baseline_ppg × UNKNOWN_RELIABILITY (0.55)` caps
    them well below the squad's floor; the best, Rashford, ranks #165.
  - The position-aware matchup layer is still dormant — `strength_attack_*`/`strength_defence_*`
    are 0 for every club, so scoring is FDR-only and `ease_mult` spans just 0.893–1.073 rather
    than the designed 0.8–1.2.
- **Lesson for next run:** the first GW1 evaluation is the only thing that can move any weight.
  Both limits above are logged as open questions for it, not fixed on intuition now.
