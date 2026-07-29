# FPL Team Creator

A Fantasy Premier League squad/transfer advisor: a small deterministic optimizer picks the
statistically best squad under real FPL constraints (budget, position quotas, club limits), a
Claude Code skill layers judgment on top (injury news, fixture nuance) and writes a durable,
GitHub-tracked record of every decision, and a weekly schedule keeps it running before each
gameweek deadline.

## How it works

1. **Data:** `engine/fetch.py` pulls live data from the official public FPL API. The `fpl` MCP
   server (configured in `.mcp.json`, see [nguyenanhducs/fpl-mcp-server](https://github.com/nguyenanhducs/fpl-mcp-server))
   supplements this with qualitative tools/prompts during a Claude session.
2. **Scoring:** `engine/score.py` turns raw stats (form, fixture difficulty, minutes reliability,
   injury doubt, ownership) into a predicted-points estimate per player, weighted by the risk
   profile in `config/settings.md`.
3. **Optimization:** `engine/optimize.py` runs a MILP (via `pulp`) to find the best full squad or
   the best 0-2 transfers from the current squad, respecting budget/position/club-limit rules and
   weighing the -4pt hit cost.
4. **Weekly review:** the `/fpl-weekly-review` skill (`.claude/skills/fpl-weekly-review/`) runs the
   above, cross-checks against the MCP's qualitative tools, and appends to `records/`.

## Repo map

```
config/settings.md          your team ID, risk profile, hit tolerance
engine/fetch.py              pulls FPL API data
engine/score.py               predicted-points heuristic
engine/optimize.py            MILP squad/transfer optimizer
records/team_history.md       squad snapshots over time
records/decisions_log.md      every transfer decision + reasoning
records/gameweek_reviews.md   how past decisions actually performed
.claude/skills/fpl-weekly-review/   the weekly Claude Code workflow
```

## Manual run

```
pip install -e .
python engine/fetch.py --team <your-team-id>
```

Or in Claude Code, run `/fpl-weekly-review` directly at any time - it doesn't require the schedule.

## Setup

1. `pip install uv` (provides `uvx`, used to run the `fpl` MCP server).
2. Fill in your FPL team ID in `config/settings.md`.
3. `claude mcp list` to confirm the `fpl` server is healthy.
