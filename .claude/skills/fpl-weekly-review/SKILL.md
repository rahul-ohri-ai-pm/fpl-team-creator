---
name: fpl-weekly-review
description: Weekly FPL squad check-in - fetches live data, scores players, runs the transfer optimizer, cross-checks qualitative context via the fpl MCP server, and logs the decision to records/. Use before a gameweek deadline, or whenever asked to check, update, or review the FPL team.
---

# FPL Weekly Review

Run this from the repo root. Read `config/settings.md` first for the team ID, risk profile, hit
tolerance, and favourite club / loyalty mode - don't hardcode any of these.

## Steps

1. **Confirm the deadline.** Use the `fpl` MCP server's gameweek/deadline tool or resource to get
   the next gameweek's real deadline. If running within ~2 hours of it, warn the user up front -
   don't silently proceed as if there's plenty of time.

2. **Evaluate last gameweek before deciding anything.** This runs *first*, so the week's
   recommendation is made in light of how the last one actually did - not after the fact.
   ```python
   from engine.fetch import get_event_live
   from engine.evaluate import evaluate_gameweek, load_predictions, calibration
   result = evaluate_gameweek(last_gw, get_event_live(last_gw))
   ```
   `evaluate_gameweek` returns `None` if nothing was recorded for that gameweek (a first run, or
   one that was skipped) - say so plainly rather than inventing a review. Otherwise report
   `predicted_total` vs `actual_total`, the signed `error`, and the two or three players in
   `per_player` with the largest errors. `bias > 0` means the model is under-predicting.
   Re-run `calibration(...)` over all evaluated gameweeks to see whether the error is systematic;
   if it is, that's evidence for changing `engine/score.py`'s weights, and the reasoning goes in
   `records/gameweek_reviews.md`.

3. **Refresh the pre-season file (pre-season runs only).** If `data/preseason.json`'s `updated` is
   more than a few days old and GW1 hasn't been played, refresh it before scoring - late-July and
   August friendlies are the most informative of the whole calendar. Team results and manager
   quotes are free (premierleague.com, Sky Sports, Fantasy Football Scout's free articles);
   player-level friendly **minutes** are paywalled, so leave `minutes` null rather than guessing.
   Record fitness/lay-off notes as `availability`, always with a `source`.
   **Always validate afterwards** - a mis-keyed entry silently scores the wrong player:
   ```python
   from engine.preseason import load
   print(load().validate(bootstrap))   # [] means clean
   ```
   `web_name` is not unique (14 collisions in the pool). Pin any colliding name with `element_id`.

4. **Fetch data.**
   ```
   python engine/fetch.py --team <team_id from config/settings.md>
   ```
   This returns the current gameweek, and the entry's bank/value/free-transfers/current picks.
   Also fetch bootstrap-static and fixtures (fetch.py's `get_bootstrap()` / `get_fixtures()`) for
   the full player pool - import and call these directly in a short script if you need the raw
   JSON rather than just the summarized CLI output.

5. **Score and optimize.** Using `engine.score.score_players(bootstrap, fixtures, next_event,
   risk_profile)` and `engine.optimize.recommend_transfers(players, current_squad, bank,
   free_transfers)`, get the recommended 0-2 transfers (or "hold"). Then run
   `engine.optimize.best_lineup(...)` on the resulting squad for the starting XI, formation,
   captain, and vice-captain.

6. **Price the favourite-club preference.** Read the favourite club and club loyalty mode from
   `config/settings.md`.
   ```python
   from engine.optimize import loyalty_cost
   report = loyalty_cost(players, budget, team_id=<favourite club's FPL team id>,
                         current_squad=squad, max_transfers_out=<transfers being recommended>)
   ```
   - Mode `report` (the default): don't constrain anything. Add one line to the summary giving the
     cost in predicted points of forcing 1 / 2 / 3 of that club's players, and who they'd be. A
     level costing ~0 means the preference is free and worth taking — say so.
   - Mode `1`/`2`/`3`: pass `min_from_team=(team_id, n)` to `recommend_transfers` so the floor is a
     real constraint, and report what it cost against the unconstrained optimum.
   - Mode `off`: skip this step.
   Never fold club loyalty into `score` — it isn't predicted points, and `predictions.jsonl` has to
   stay comparable to what the squad actually banks.

7. **Cross-check with the `fpl` MCP.** Before finalizing, check its injury/news tools and any
   rival/mini-league comparison for context the raw stats wouldn't catch (e.g. a press-conference
   knock, a fixture postponement). Adjust the recommendation only if there's a concrete reason to
   override the optimizer - state that reason explicitly if you do.

8. **Read the narrative history.** Read the most recent entry in `records/gameweek_reviews.md`
   before finalizing this week's call - step 2 gives the numbers, this gives the reasoning behind
   them and whether it held up.

9. **Record this week's prediction.** Do this every run, including holds - an unrecorded week is a
   permanent hole in the calibration data.
   ```python
   from engine.evaluate import build_prediction, record_prediction
   record_prediction(build_prediction(next_event, lineup, players,
                                      meta={"decision": "hold"}))
   ```
   `predicted_total` counts the captain twice, so it is directly comparable to the entry's real
   gameweek points.

10. **Log to records/** (append, never rewrite past entries):
   - `records/gameweek_reviews.md` - how the *previous* gameweek's held squad actually scored,
     using the step 2 numbers (predicted vs actual, biggest misses, what it implies for scoring).
   - `records/decisions_log.md` - this week's decision (hold, or the specific transfer(s)) with
     the reasoning and the optimizer's net (hit-adjusted) score.
   - `records/team_history.md` - the new squad snapshot: bank, value, free transfers, chip status,
     full squad, starting XI/formation, captain/vice.

11. **Report back concisely.** Lead with last gameweek's predicted vs actual, then the final squad
   changes (if any), captain/vice, and a one-line reason each. **Always present the final 15 as a
   table** - one row per player, starting XI and bench separated, with position, club, price and
   predicted score, captain and vice marked. Do not dump the full player pool or raw stats table
   into the chat - that defeats the point of running this as a lean weekly check-in.

## Constraints

- Never attempt to execute a transfer against the live FPL account - this is advisory only.
- If the optimizer errors (e.g. infeasible squad), report the error plainly rather than
  improvising a squad by hand.
