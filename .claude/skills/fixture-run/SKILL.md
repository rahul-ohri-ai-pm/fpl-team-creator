---
name: fixture-run
description: Analyze upcoming Premier League fixture difficulty for a team or squad over the next N gameweeks, including rotation risk from European/domestic cup competitions. Use for captain planning or spotting transfer windows around a fixture swing.
---

# Fixture Run

Loads `.claude/docs/SCORING.md` (for the ease_mult calculation) and `config/settings.md`. Run
from the repo root.

## Steps

1. **Get fixtures.** `engine/fetch.py`'s `get_fixtures()` for the full-season list; filter to the
   requested team(s) and next N gameweeks (default 4).

2. **Score the run.** Use `engine.score.fixture_ease(team_id, fixtures, next_event, n)` — same
   function `engine/score.py` uses internally, so this stays consistent with what the optimizer
   is already weighting. Present as a simple per-gameweek difficulty read (easy/medium/hard), not
   just the raw 0-1 ease score.

3. **Flag rotation risk from other competitions.** Check `.claude/docs/DATA_SOURCES.md`'s "Other
   competitions" section for which clubs are in Europe this season. If a team in the requested
   run is in the Champions League, Europa League, or Conference League, note that a midweek fixture
   3-4 days before a Premier League gameweek raises rotation risk for that GW — this isn't
   captured by `fixture_ease` at all (FPL's own fixture data is PL-only), so call it out
   separately rather than folding it into the ease score. FA Cup / EFL Cup rounds matter here too,
   especially from January onward — check via `WebSearch` if the run falls in that window and a
   cup round lands near a PL gameweek for that club.

4. **Report**: fixture difficulty per gameweek in the run, any rotation-risk flags from other
   competitions, and — only if asked — a captain recommendation for the easiest upcoming fixture
   among nailed, in-form squad players (cross-check with `/injury-check` before recommending a
   captain who has any doubt against their name).

## Constraints

- Advisory only — this doesn't touch the live FPL account or make transfers.
- Don't repeat the full fixture list back to the user; summarize the run (e.g., "easy GW3-5, hard
  GW6-7") rather than dumping every fixture's raw difficulty number.
