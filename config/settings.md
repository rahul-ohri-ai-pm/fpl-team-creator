# Settings

Plain-text config read by `engine/fetch.py` and the `fpl-weekly-review` skill. Team IDs are public (not secret), safe to commit.

- **FPL team/entry ID:** `1669770` (ScorpionFC, managed by Rahul Ohri).
- **Risk profile:** `differential` — favor upside/low-ownership picks over template safety; the user
  is chasing a top-5 mini-league finish from 20th of 22 (90 pts back, ~24.6 pts/GW off top-5 pace
  as of GW4), a gap `safe`'s high-ownership floor cannot close. Changed from `safe` on 2026-09-16 —
  see `records/decisions_log.md`'s GW5 entry for the full reasoning. Change back to `safe` or
  `balanced` to shift `engine/score.py`'s weighting.
- **Budget:** standard FPL rules — £100.0m squad value, max 3 players per real club, 2 GK / 5 DEF / 5 MID / 3 FWD.
- **Transfer hit tolerance:** only take a -4 hit if the optimizer's predicted point gain over the next 3 gameweeks exceeds 4 points combined for the swap.
- **Favourite club:** `Chelsea` (FPL team id `6`). Supporting your own team is a preference, not a
  prediction, so it is never added to a player's `score` — it is a floor on how many squad places
  the club gets, applied by `engine/optimize.py`'s `min_from_team`.
- **Club loyalty mode:** `report` — the floor is **off**, and every weekly run instead reports what
  forcing 1, 2 and 3 Chelsea players *would* cost in predicted points (`optimize.loyalty_cost`), so
  the call is made against a number. Change to `1`, `2` or `3` to make it a standing constraint,
  or `off` to stop reporting it. `3` is the FPL maximum per club.
- **Mini-league:** `FPL@Parkway`, league id `218260` (`fpl` MCP's `fpl_get_league_standings` /
  `fpl_compare_managers`). Manager name in this league: `Rahul Ohri`. Used for the top-5 pace gap
  and the weekly squad-vs-league-leader comparison (captain, common players, differentials).
