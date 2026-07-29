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

## Working agreements

- **Work directly on `master`.** Don't develop on a feature branch and don't open a PR unless
  asked — commit and push straight to `master` so nothing needs merging afterwards. Some sessions
  start with a generated `claude/*` branch configured; ignore it and use `master`.
- **Always present the final 15 as a table**, never as prose. One row per player, split into
  starting XI and bench, with position, club, price and predicted score. Captain and vice marked.

## Data sources

- `engine/fetch.py` — direct calls to the official public FPL API (`fantasy.premierleague.com/api`,
  no auth). Use this for the hard numeric data (prices, form, fixtures, entry/squad state) that
  `engine/optimize.py` needs.
- `fpl` MCP server (`.mcp.json`, `uvx fpl-mcp-server`) — used interactively for qualitative context
  the raw API doesn't shape well: strategy prompts, rival/manager comparison, richer fixture-run
  views. A stale or broken MCP should never block the core fetch → score → optimize pipeline.
- `data/preseason.json` — pre-season signal, which the FPL API does **not** carry at all. FPL
  ingests only competitive league matches: `/fixtures/` returns exactly 380 games starting at the
  GW1 date, `form` is `0.0` for every player until GW1 is played, and no element field references
  friendlies. So this file is maintained by hand, loaded by `engine/preseason.py`, and consumed by
  `engine/score.py`. Refresh it during a pre-season weekly run.
  - Team-level friendly results are published free (premierleague.com). Player-level **minutes** —
    the part that actually predicts anything — sit behind Fantasy Football Scout's Chief Scout
    paywall. Leave `minutes` null rather than guessing: null is handled, an invented number
    silently corrupts every score downstream.
  - Score friendly **minutes**, not friendly goals. Pre-season output is a weak predictor (weak
    opposition, trialists, experimental XIs); minutes reveal who the manager intends to start.

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
