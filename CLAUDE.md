# FPL Team Creator

A stats-driven Fantasy Premier League squad/transfer advisor. See `README.md` for the project
overview and repo map.

## Rules this project must respect

- Squad: 15 players — 2 GK, 5 DEF, 5 MID, 3 FWD. Starting XI: 1 GK, 3-5 DEF, 2-5 MID, 1-3 FWD (11 total).
- Budget: £100.0m (stored as tenths of a million in the FPL API, e.g. `125` = £12.5m).
- Max 3 players per real-world club.
- Free transfers roll over (cap at 5); each extra transfer beyond available free transfers costs -4 points.
- Chips: Wildcard (x2/season), Free Hit, Bench Boost, Triple Captain.
- **This project never executes transfers against the live FPL account.** The MCP server used is
  read-only by design. All recommendations are advisory — the user makes the actual move in-game.

## User's settings

Read `config/settings.md` for the linked team ID, risk profile, and hit tolerance before any
analysis. Don't hardcode these values elsewhere — if the user's risk profile changes, only that
file and `engine/score.py`'s weighting table should need touching.

## Data sources

- `engine/fetch.py` — direct calls to the official public FPL API (`fantasy.premierleague.com/api`,
  no auth). Use this for the hard numeric data (prices, form, fixtures, entry/squad state) that
  `engine/optimize.py` needs.
- `fpl` MCP server (`.mcp.json`, `uvx fpl-mcp-server`) — used interactively for qualitative context
  the raw API doesn't shape well: strategy prompts, rival/manager comparison, richer fixture-run
  views. A stale or broken MCP should never block the core fetch → score → optimize pipeline.

## Weekly workflow

The `/fpl-weekly-review` skill (`.claude/skills/fpl-weekly-review/SKILL.md`) is the canonical
weekly process: confirm deadline → fetch → score → optimize → cross-check with MCP → log to
`records/` → short summary to the user. Don't duplicate that logic ad hoc; invoke the skill.

## Records

`records/team_history.md`, `records/decisions_log.md`, `records/gameweek_reviews.md` are
append-only and are the persistent, GitHub-visible memory of this project. Always append, never
rewrite past entries. Read `gameweek_reviews.md` before making a new recommendation — it's the
feedback loop for whether last week's reasoning actually held up.

## Token discipline

Weekly runs should end with a short summary (final squad changes, captain/vice, one-line reason
each) — not a full data dump of every player considered.
