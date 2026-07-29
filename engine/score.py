"""Predicted-points heuristic per player, v1.

FPL's own `form` stat (avg points/match, last 30 days) is already a solid
expected-points proxy. We adjust it for upcoming fixture ease, minutes
reliability, injury doubt, and a risk-profile-driven ownership nudge.

Before GW1 none of that is live: `form` is 0.0 for every player and `minutes`
still describes last season. See engine/preseason.py for the two fallbacks that
keep the pre-season run honest - a price-implied baseline for players with no
Premier League record, and the hand-maintained pre-season file.
"""
from __future__ import annotations

from engine import preseason as preseason_mod

POSITION_BY_TYPE = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}


def _finished_events(bootstrap) -> int:
    """Games played so far this season. 0 pre-season/early season - callers must
    not divide by this directly (minutes would then look artificially reliable)."""
    return sum(1 for e in bootstrap["events"] if e["finished"])


def fixture_ease(team_id: int, fixtures: list, next_event: int, n: int = 4) -> float:
    """0 (very hard run) .. 1 (very easy run) over the next n fixtures."""
    upcoming = [f for f in fixtures if f["event"] and f["event"] >= next_event
                and (f["team_h"] == team_id or f["team_a"] == team_id)]
    upcoming.sort(key=lambda f: f["event"])
    upcoming = upcoming[:n]
    if not upcoming:
        return 0.5
    diffs = [f["team_h_difficulty"] if f["team_h"] == team_id else f["team_a_difficulty"]
             for f in upcoming]
    avg_fdr = sum(diffs) / len(diffs)  # 1 (easy) .. 5 (hard)
    return max(0.0, min(1.0, (5 - avg_fdr) / 4))


def score_players(bootstrap, fixtures, next_event: int, risk_profile: str = "safe",
                  preseason=None) -> dict:
    """Returns {player_id: {"score": float, "pos": str, "team": int, "cost": int, "name": str}}

    `preseason` is an engine.preseason.Preseason; loaded from disk when omitted.
    Pass Preseason() to score on FPL data alone.
    """
    finished = _finished_events(bootstrap)
    team_ease = {t["id"]: fixture_ease(t["id"], fixtures, next_event) for t in bootstrap["teams"]}

    # Direction and strength of the ownership preference, as a *tiebreak* only.
    # Positive = prefer template/high-ownership cover, negative = prefer differentials.
    # This deliberately never enters `score`: ownership isn't predicted points, and
    # adding it there inflated squad totals into looking like a points forecast they
    # weren't. The optimizer applies it at OWNERSHIP_TIEBREAK_EPSILON strength, so it
    # can only separate players who are otherwise near-identical.
    ownership_weight = {"safe": 1.0, "balanced": 0.2, "differential": -1.0}.get(risk_profile, 0.2)

    ps = preseason_mod.load() if preseason is None else preseason
    baselines = preseason_mod.price_baselines(bootstrap)

    out = {}
    for p in bootstrap["elements"]:
        web_name = p["web_name"]
        # `form` is a rolling last-30-days average - it's legitimately 0 pre-season
        # and early in a new season (no matches played recently), not a signal that
        # the player is bad. Fall back to last known points-per-game in that case,
        # and to a price-implied baseline for anyone with no Premier League record
        # at all (new signing, returning loanee, season missed injured) - scoring
        # those at a literal 0 makes them permanently unpickable.
        ppg = float(p["points_per_game"] or 0)
        if ppg == 0:
            ppg = preseason_mod.baseline_ppg(baselines, p["element_type"], p["now_cost"])
        form = float(p["form"] or 0) or ppg

        minutes = p["minutes"]
        # Pre-season/early season, `minutes` is still last season's total and there's
        # no `finished` games this season to normalize against - use a full season
        # (38 games) as the reference so low-minutes players are still discounted.
        games_reference = finished if finished > 0 else 38
        reliability = min(1.0, minutes / (games_reference * 90 * 0.6))
        if minutes == 0:
            # No Premier League record to measure. Assume a discounted starter
            # rather than 0, which would be indistinguishable from "definitely
            # won't play". Applied before the blend below so that a player with
            # pre-season minutes on file is never scored worse than an identical
            # player with none - recording data must not penalise anyone.
            reliability = preseason_mod.UNKNOWN_RELIABILITY

        # Pre-season minutes are the one thing friendlies are genuinely good for:
        # they show who the manager actually intends to start. Blend rather than
        # replace - a few friendlies shouldn't outvote a full season.
        share = ps.minutes_share(web_name)
        if share is not None:
            w = preseason_mod.PRESEASON_MINUTES_WEIGHT
            reliability = (1 - w) * reliability + w * share

        chance = p["chance_of_playing_next_round"]
        injury_mult = (chance if chance is not None else 100) / 100
        if chance is None:
            # FPL hasn't flagged this player. Fall back to any pre-season fitness
            # doubt on file; once FPL sets a real percentage it wins, being the
            # harder source.
            ps_avail = ps.availability(web_name)
            if ps_avail is not None:
                injury_mult = ps_avail

        ease = team_ease.get(p["team"], 0.5)
        ease_mult = 0.8 + ease * 0.4  # 0.8 .. 1.2
        ownership = float(p["selected_by_percent"] or 0)

        predicted = form * ease_mult * reliability * injury_mult

        out[p["id"]] = {
            # Predicted points, and nothing else. Summing these across an XI gives a
            # number that can be compared against what the squad actually scores.
            "score": round(predicted, 3),
            # Signed -1..1 ownership preference, applied only as a tiebreak.
            "tiebreak": round((ownership / 100) * ownership_weight, 4),
            "pos": POSITION_BY_TYPE[p["element_type"]],
            "team": p["team"],
            "cost": p["now_cost"],
            "name": f"{p['first_name']} {p['second_name']}",
        }
    return out
