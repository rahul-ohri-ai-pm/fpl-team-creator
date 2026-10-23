"""Multi-gameweek planner and chip calendar (engine.planner).

Synthetic pools only - no network. As in test_optimize, the right answer is
obvious by construction so a wrong constraint shows up as a wrong plan.
"""
import datetime as dt

from engine.optimize import optimal_squad
from engine.planner import (
    chip_calendar, chips_available, fixture_structure, plan_transfers, return_date,
)


def make_pool(n_per_pos=8, n_clubs=20):
    players, pid = {}, 1
    for pos in ("GK", "DEF", "MID", "FWD"):
        for i in range(n_per_pos):
            players[pid] = {"score": 1.0 + i * 0.5, "pos": pos, "team": pid % n_clubs,
                            "cost": 40 + i * 5, "name": f"{pos} {i}"}
            pid += 1
    return players


def setup(weeks=3):
    players = make_pool()
    squad = optimal_squad(players, budget=800)
    budget = sum(players[p]["cost"] for p in squad)
    scores = {t: {p: v["score"] for p, v in players.items()} for t in range(1, weeks + 1)}
    return players, squad, budget, scores


def starters_by_score(squad, players):
    return sorted(squad, key=lambda p: players[p]["score"], reverse=True)


def test_holds_and_rolls_free_transfers_when_nothing_is_better():
    players, squad, _, scores = setup()
    plan = plan_transfers(scores, players, squad, bank=0, free_transfers=1)
    assert all(not wk["in"] for wk in plan["weeks"])
    assert [wk["free_transfers"] for wk in plan["weeks"]] == [1, 2, 3]
    assert plan["total"] == plan["hold_total"]


def test_an_injured_starter_is_replaced_with_the_free_transfer_not_a_hit():
    players, squad, _, scores = setup()
    out = starters_by_score(squad, players)[0]
    for week in scores.values():
        week[out] = 0.0
    plan = plan_transfers(scores, players, squad, bank=0, free_transfers=1)
    first = plan["weeks"][0]
    assert first["out"] == [out] and len(first["in"]) == 1
    assert sum(wk["hits"] for wk in plan["weeks"]) == 0


def test_hits_are_charged_only_beyond_the_free_transfers():
    """Two big losses, one free transfer: two moves in week one cost exactly one hit,
    and the solver can't pay an extra -4 to bank a free transfer for later."""
    players, squad, _, scores = setup()
    a, b = starters_by_score(squad, players)[:2]
    for week in scores.values():
        week[a] = week[b] = 0.0
    plan = plan_transfers(scores, players, squad, bank=0, free_transfers=1, hit_margin=0)
    first = plan["weeks"][0]
    assert set(first["out"]) == {a, b}
    assert first["hits"] == 1
    assert plan["weeks"][1]["free_transfers"] == 1


def test_no_hits_mode_never_charges():
    players, squad, _, scores = setup()
    for p in starters_by_score(squad, players)[:3]:
        for week in scores.values():
            week[p] = 0.0
    plan = plan_transfers(scores, players, squad, bank=0, free_transfers=1, allow_hits=False)
    assert all(wk["hits"] == 0 for wk in plan["weeks"])


def test_plan_respects_squad_rules_every_week():
    players, squad, budget, scores = setup()
    for week in scores.values():
        week[starters_by_score(squad, players)[0]] = 0.0
    for wk in plan_transfers(scores, players, squad, bank=0, free_transfers=2)["weeks"]:
        assert len(wk["squad"]) == 15 and len(wk["starters"]) == 11
        assert sum(players[p]["cost"] for p in wk["squad"]) <= budget


def test_return_date_parses_and_rolls_the_year():
    today = dt.date(2026, 10, 23)
    assert return_date("Hamstring injury - Expected back 1 Nov", today) == dt.date(2026, 11, 1)
    assert return_date("Expected back 5 Jan", dt.date(2026, 12, 20)) == dt.date(2027, 1, 5)
    assert return_date("Thigh injury - Unknown return date", today) is None


def test_fixture_structure_finds_doubles_and_blanks():
    fx = [{"event": 9, "team_h": 1, "team_a": 2}, {"event": 9, "team_h": 1, "team_a": 3},
          {"event": None, "team_h": 4, "team_a": 5, "finished": False}]
    s = fixture_structure(fx, 9, n_teams=4)
    assert s[9]["doubles"] == [1] and s[9]["blanks"] == [4]
    assert s["unscheduled"] == 1


def test_chips_available_tracks_wildcard_halves():
    hist = {"chips": [{"name": "wildcard", "event": 4}, {"name": "bboost", "event": 6}]}
    assert chips_available(hist, 8) == ["wildcard (GW20+)", "freehit", "3xc"]
    assert chips_available(hist, 21) == ["wildcard", "freehit", "3xc"]


def test_chip_calendar_holds_chips_in_a_flat_week():
    players, squad, budget, scores = setup(weeks=1)
    plan = plan_transfers(scores, players, squad, bank=0, free_transfers=1)
    rows = chip_calendar(plan, scores, players, budget, ["bboost", "3xc", "freehit"])
    assert {r["chip"] for r in rows} == {"bboost", "3xc", "freehit"}
    assert not any(r["use"] for r in rows)
