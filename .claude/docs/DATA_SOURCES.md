# Data Sources

## Premier League (Fantasy) data — authoritative, numeric

- **`engine/fetch.py`** — direct calls to the official public FPL API
  (`fantasy.premierleague.com/api`, no auth needed):
  - `get_bootstrap()` — full player pool, teams, gameweek (`events`) metadata
  - `get_fixtures()` — full-season fixture list with difficulty ratings
  - `get_entry(team_id)` / `get_entry_picks(team_id, event)` / `get_entry_history(team_id)` — a
    specific manager's squad, bank, value, transfer history
- **Use this for**: prices, form, fixture difficulty, entry/squad state, injury status fields
  (`status`, `news`, `chance_of_playing_next_round`), and whether a gameweek is actually
  finished (`bootstrap['events'][n]['finished']`). This is the ground truth — `engine/score.py`
  and `engine/optimize.py` both consume it directly.
- **Live per-gameweek points**: `/api/event/{n}/live/` — per-player actual points for a specific
  gameweek, once matches have been played. Use this (not `total_points`, which accumulates) when
  you need "what did player X score in gameweek N."
- **Last-season history**: `/api/element-summary/{player_id}/` → `history_past` — a player's
  totals from prior completed seasons. Useful for reconstructing what a pre-season prediction
  would have used, since `bootstrap`'s live `points_per_game`/`minutes` fields reset every season
  and can't be un-reset later (see `records/scoring_backtest.md`'s GW1 entry for why this matters
  and its "start snapshotting pre-GW data" action item).

## `fpl` MCP server — qualitative context only

- `.mcp.json` runs `uvx fpl-mcp-server`. Tools like `fpl_analyze_rival`, `fpl_get_captain_recommendations`,
  `fpl_compare_managers`, `fpl_find_fixture_opportunities` etc. are convenient for strategy
  framing and rival comparison.
- **Known gap**: MCP player-detail tools do **not** reliably surface `status`/`news`/
  `chance_of_playing_next_round` — always pull those three fields from bootstrap directly for any
  injury/rotation claim (see the verification loop in `CLAUDE.md`).
- **A stale or broken MCP should never block the core fetch → score → optimize pipeline** — it's
  a nice-to-have overlay, not a dependency.

## Other competitions (FA Cup, EFL Cup, Champions League, Europa League, Conference League)

**Not covered by the FPL API at all** — `bootstrap`/`fixtures` are Premier League only. Fantasy
points are never earned from cup or European matches, but those fixtures still matter as
**rotation-risk context**: a player carrying a midweek European or cup match 3-4 days before a
Premier League gameweek is more likely to be rested or subbed early.

There's no free no-auth API for this bundled into the project (unlike the FPL API). Until one is
integrated, treat this as an ad-hoc `WebSearch` check, not an automated pipeline step — pull it in
during `/fixture-run` or `/injury-check` only when a specific player's rotation risk is in
question, not as a blanket weekly fetch.

**2026/27 season European qualification (confirmed via web search, since this is beyond training
data)** — useful as a standing reference for which PL clubs carry extra midweek fixtures this
season:
- **Champions League**: Arsenal, Manchester City, Manchester United, Aston Villa, Liverpool
- **Europa League**: Bournemouth, Sunderland, Crystal Palace
- **Conference League**: Brighton
- Everyone else (including Chelsea, who missed out entirely) has no European football this
  season — lower rotation risk from that source specifically.
- **FA Cup / EFL Cup**: all PL clubs enter both competitions regardless of European status. Early
  rounds (EFL Cup) rarely cause much rotation for the biggest clubs' star players, but this
  should be re-checked deeper into the season (Jan-Apr) when cup replays and quarter/semi-finals
  start colliding with congested PL weeks.
- **Re-verify each season** — this list changes every year based on the previous season's
  finishing positions and cup winners. Don't assume it carries over; re-run the web search this
  note describes if working across a season boundary.

This project's squad (as of the GW1 review) has real exposure: Arsenal (Gabriel, Raya) and
Liverpool (van Dijk) are in the Champions League; Manchester United (Mbeumo) is also in the
Champions League; Sunderland (Mukiele, Roefs) is in the Europa League. Chelsea (Enzo Fernández,
João Pedro) has no European football this season, so no added rotation risk from that source.
