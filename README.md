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
   profile in `config/settings.md`. Before GW1 none of those inputs are live, so
   `engine/preseason.py` fills the gap: a price-implied baseline for players with no Premier
   League record, plus the hand-maintained `data/preseason.json` for friendly minutes and fitness
   doubts the API never carries.
3. **Optimization:** `engine/optimize.py` runs a MILP (via `pulp`) to find the best full squad or
   the best 0-2 transfers from the current squad, respecting budget/position/club-limit rules and
   weighing the -4pt hit cost. It can also hold a minimum number of places for a favourite club —
   and `loyalty_cost` prices that preference in predicted points first, so it's a choice made
   against a number rather than a feeling.
4. **Weekly review:** the `/fpl-weekly-review` skill (`.claude/skills/fpl-weekly-review/`) runs the
   above, cross-checks against the MCP's qualitative tools, and appends to `records/`.
5. **Measurement:** every run records its recommended XI and predicted points to
   `records/predictions.jsonl`. The next run replays that gameweek's real FPL points through
   `engine/evaluate.py` — applying auto-subs and the vice-captain armband — and reports predicted
   vs actual before recommending anything, so the scoring weights get tuned against measured error
   rather than intuition.

## Documentation

| Doc | What it covers |
|---|---|
| [docs/PRODUCT_LOG.md](docs/PRODUCT_LOG.md) | **Start here.** The problem being solved, the approach and why, the MCP servers and where the human/agent boundary sits, how the evals work, and a dated decision log of every change with its reasoning and what it cost. |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Data flow, module responsibilities, the network and MCP boundaries, configuration, and the testing approach. |
| [docs/EVALUATION.md](docs/EVALUATION.md) | How predictions are recorded and measured, how to read the error metrics, and the rule for what is allowed to change a scoring weight. |

## Repo map

```
config/settings.md          your team ID, risk profile, hit tolerance, favourite club
data/preseason.json         hand-maintained pre-season signal (friendlies, minutes, fitness)
engine/fetch.py              pulls FPL API data
engine/preseason.py           pre-season layer + price-implied baseline for unknown players
engine/score.py               predicted-points heuristic
engine/optimize.py            MILP squad/transfer optimizer
engine/evaluate.py            records predictions, measures them against real FPL points
records/team_history.md       squad snapshots over time
records/decisions_log.md      every transfer decision + reasoning
records/gameweek_reviews.md   how past decisions actually performed
records/predictions.jsonl     append-only predicted-vs-actual log (the calibration data)
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
