---
name: injury-check
description: Fast audit of a squad's injury/rotation status straight from the FPL bootstrap API. Use mid-week before a gameweek deadline, or whenever asked to check if anyone is injured, doubtful, or a rotation risk.
---

# Injury Check

Loads only `config/settings.md` — no other project docs needed. Fetches bootstrap directly; no
`fpl` MCP call (MCP player-detail tools don't reliably surface these fields anyway — see
`.claude/docs/DATA_SOURCES.md`).

## Steps

1. **Get the squad.** Either the team ID's current picks (`engine/fetch.py`'s
   `get_entry_picks`), or a squad list passed in directly.

2. **Pull bootstrap fresh** and, for each squad player, read `status`, `news`, and
   `chance_of_playing_next_round` directly off their `bootstrap['elements']` entry. Don't infer
   status from points totals or from any cached/previous read — always re-fetch.

3. **Flag anything non-clean**:
   - `status != 'a'` (doubtful/injured/suspended/unavailable)
   - `chance_of_playing_next_round` set and < 100
   - Non-empty `news`, even if `status == 'a'` (sometimes news posts before the status flag updates)

4. **Cross-check rotation risk from other competitions** if the deadline is close to a midweek
   European or cup fixture for any squad player's club — see `.claude/docs/DATA_SOURCES.md`'s
   "Other competitions" section for this season's European qualifiers. This isn't in the FPL API,
   so use judgment (or a quick web search) rather than automating it.

5. **Report**: a short per-player line only for flagged players (clean players don't need
   individual callouts — just confirm "the rest are clean, no news" as one line). End with a
   one-line captain/vice recommendation implication if a flagged player is currently armbanded.

## Constraints

- Never report an injury/rotation conclusion without having read `status`/`news`/
  `chance_of_playing_next_round` from bootstrap in *this* run — a cached read from an earlier
  turn in the conversation isn't good enough if any time has passed, per the verification loop.
- This skill doesn't recommend transfers — it's a status check. Route any resulting transfer
  question to `/fpl-weekly-review` or `/score-calibrate` as appropriate.
