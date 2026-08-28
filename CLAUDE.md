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

Read `config/settings.md` for the linked team ID, risk profile, and hit tolerance before any
analysis — don't hardcode these values elsewhere.

## Verification loop (non-negotiable)

Apply this before treating any conclusion as final — whether inside a skill run or in an ad-hoc
question:

1. **Draft** the conclusion (a "points scored" total, an injury/rotation flag, a transfer
   rationale) from the data fetched so far.
2. **Verify each claim against the raw source** before repeating it:
   - A gameweek is only final when `bootstrap['events'][n]['finished']` is `True` — a passed
     deadline does not mean the gameweek is over.
   - A player's injury/rotation status comes from `status`, `news`, and
     `chance_of_playing_next_round` on that player's `bootstrap` element — not from a raw points
     total, and not from the `fpl` MCP's player-detail tools alone.
   - A transfer is only "made" if the user has explicitly said they executed it in the live FPL
     app. Never log one as done based on a recommendation alone.
3. **If a check fails, revise the conclusion and re-verify** — repeat until every claim is
   confirmed against source data, not assumed.

This loop caught two real mistakes on 2026-08-24 (see `records/decisions_log.md` and
`records/gameweek_reviews.md` correction entries from that date) — don't skip it to save a step.

## Quick reference

- **`.claude/docs/DATA_SOURCES.md`** — FPL API vs. `fpl` MCP vs. other-competition context (FA
  Cup / EFL Cup / European qualification), and when to use each.
- **`.claude/docs/SCORING.md`** — the scoring formula, its 4 weight schemes, known biases, and
  the backtest methodology.
- **`.claude/docs/WEEKLY_WORKFLOW.md`** — the full `/fpl-weekly-review` step-by-step.
- **`.claude/docs/RECORDS.md`** — the four append-only logs, their templates, and the append-only
  rule.
- **`.claude/docs/AGENTS.md`** — which agent type fits which task in this project.

## Skills

`/fpl-weekly-review` is the canonical weekly process (fetch → score → optimize → cross-check →
log). Narrower skills for sub-tasks: `/gw-backtest` (scoring-scheme backtest), `/score-calibrate`
(apply a calibration), `/injury-check` (fast squad status audit), `/fixture-run` (fixture-run and
rotation-risk analysis). Don't duplicate their logic ad hoc — invoke the skill.

## Token discipline

Weekly runs should end with a short summary (final squad changes, captain/vice, one-line reason
each) — not a full data dump of every player considered.
