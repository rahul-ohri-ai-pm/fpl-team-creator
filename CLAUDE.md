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

## Verification loop

Apply this before treating any conclusion as final — whether inside `/fpl-weekly-review` or in an
ad-hoc question — not just at the end of a formal run:

1. **Draft** the conclusion (a "points scored" total, an injury/rotation flag, a transfer
   rationale) from the data fetched so far.
2. **Verify each claim against the raw source** before repeating it:
   - A gameweek is only final when `bootstrap['events'][n]['finished']` is `True` — a passed
     deadline does not mean the gameweek is over. Check individual fixtures' `started` /
     `finished_provisional` flags too if the total matters (e.g. a postponed/delayed match).
   - A player's injury/rotation status comes from `status`, `news`, and
     `chance_of_playing_next_round` on that player's `bootstrap` element — not from a raw points
     total, and not from the `fpl` MCP's player-detail tools alone (they don't surface these
     fields).
   - A transfer is only "made" if the user has explicitly said they executed it in the live FPL
     app. Never log one to `records/team_history.md` as done based on a recommendation alone.
3. **If a check fails, revise the conclusion and re-verify** — repeat until every claim is
   confirmed against source data, not assumed. Don't report or log a claim you haven't checked
   this way.

This loop is what catches "the deadline passed so the gameweek must be over" or "zero points means
benched" — both wrong, and both bit this project on 2026-08-24 (see `records/decisions_log.md` and
`records/gameweek_reviews.md` correction entries from that date).

## Token discipline

Weekly runs should end with a short summary (final squad changes, captain/vice, one-line reason
each) — not a full data dump of every player considered.
