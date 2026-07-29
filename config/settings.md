# Settings

Plain-text config read by `engine/fetch.py` and the `fpl-weekly-review` skill. Team IDs are public (not secret), safe to commit.

- **FPL team/entry ID:** `TODO_FILL_IN` — find yours at `https://fantasy.premierleague.com/entry/<ID>/history`, or ask the skill and it will look it up from your team name.
- **Risk profile:** `safe` — favor high-ownership, high-minutes, in-form players; avoid rotation/injury-risk picks even when upside looks good. Change to `balanced` or `differential` to shift `engine/score.py`'s weighting.
- **Budget:** standard FPL rules — £100.0m squad value, max 3 players per real club, 2 GK / 5 DEF / 5 MID / 3 FWD.
- **Transfer hit tolerance:** only take a -4 hit if the optimizer's predicted point gain over the next 3 gameweeks exceeds 4 points combined for the swap.
