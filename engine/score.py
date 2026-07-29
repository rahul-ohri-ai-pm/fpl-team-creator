"""Predicted-points heuristic per player, v1.

FPL's own `form` stat (avg points/match, last 30 days) is already a solid
expected-points proxy. We adjust it for upcoming fixture ease, minutes
reliability, injury doubt, and a risk-profile-driven ownership nudge.
"""
from __future__ import annotations

POSITION_BY_TYPE = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}


def _finished_events(bootstrap) -> int:
    return sum(1 for e in bootstrap["events"] if e["finished"]) or 1


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


def score_players(bootstrap, fixtures, next_event: int, risk_profile: str = "safe") -> dict:
    """Returns {player_id: {"score": float, "pos": str, "team": int, "cost": int, "name": str}}"""
    finished = _finished_events(bootstrap)
    team_ease = {t["id"]: fixture_ease(t["id"], fixtures, next_event) for t in bootstrap["teams"]}

    ownership_weight = {"safe": 1.5, "balanced": 0.3, "differential": -1.5}.get(risk_profile, 0.3)

    out = {}
    for p in bootstrap["elements"]:
        form = float(p["form"] or 0)
        minutes = p["minutes"]
        reliability = min(1.0, minutes / max(1, finished * 90 * 0.6))
        chance = p["chance_of_playing_next_round"]
        injury_mult = (chance if chance is not None else 100) / 100
        ease = team_ease.get(p["team"], 0.5)
        ease_mult = 0.8 + ease * 0.4  # 0.8 .. 1.2
        ownership = float(p["selected_by_percent"] or 0)

        predicted = form * ease_mult * reliability * injury_mult
        predicted += (ownership / 100) * ownership_weight

        out[p["id"]] = {
            "score": round(predicted, 3),
            "pos": POSITION_BY_TYPE[p["element_type"]],
            "team": p["team"],
            "cost": p["now_cost"],
            "name": f"{p['first_name']} {p['second_name']}",
        }
    return out
