"""Multi-gameweek planning scores (engine.score.horizon_scores).

`score` answers "what does this player bank next week". These cover the separate
question the transfer budget actually poses: only one free transfer arrives per
week, so a squad has to survive its opening run, not just win the first fixture.
"""
import pytest

from engine.score import gameweek_ease, horizon_scores, score_players


def bootstrap(n_teams=4):
    return {
        "events": [{"id": i, "finished": False, "is_current": False, "is_next": i == 1}
                   for i in range(1, 9)],
        "teams": [{"id": i, "short_name": f"T{i}", "strength": None,
                   "strength_attack_home": 0, "strength_attack_away": 0,
                   "strength_defence_home": 0, "strength_defence_away": 0}
                  for i in range(1, n_teams + 1)],
        "elements": [],
    }


def player(pid, team, element_type=3, cost=60, ppg="5.0", minutes=3000):
    return {"id": pid, "web_name": f"P{pid}", "first_name": "F", "second_name": f"L{pid}",
            "element_type": element_type, "team": team, "now_cost": cost,
            "points_per_game": ppg, "form": "0.0", "minutes": minutes,
            "chance_of_playing_next_round": None, "selected_by_percent": "5.0"}


def fixture(event, home, away, hd=3, ad=3):
    return {"event": event, "team_h": home, "team_a": away,
            "team_h_difficulty": hd, "team_a_difficulty": ad}


# --- gameweek_ease: the thing a decayed average throws away ----------------

def test_a_blank_gameweek_yields_no_fixtures():
    fx = [fixture(1, 1, 2), fixture(3, 1, 2)]  # nothing in GW2
    assert gameweek_ease("MID", 1, fx, 2, None) == []


def test_a_double_gameweek_yields_two_fixtures():
    fx = [fixture(1, 1, 2), fixture(1, 3, 1)]
    assert len(gameweek_ease("MID", 1, fx, 1, None)) == 2


def test_easier_fdr_reads_as_a_higher_ease():
    easy = gameweek_ease("MID", 1, [fixture(1, 1, 2, hd=1)], 1, None)
    hard = gameweek_ease("MID", 1, [fixture(1, 1, 2, hd=5)], 1, None)
    assert easy[0] > hard[0]


# --- horizon_scores -------------------------------------------------------

def test_a_blank_gameweek_costs_a_whole_week_of_points():
    """The point of the horizon view: a club that doesn't play banks nothing that
    week, which a fixture-run average silently hides by borrowing the next game."""
    b = bootstrap()
    b["elements"] = [player(1, team=1), player(2, team=3)]
    fx = [fixture(g, 1, 2) for g in range(1, 5)] + \
         [fixture(g, 3, 4) for g in (1, 2, 4)]  # team 3 blanks in GW3
    hz = horizon_scores(b, fx, 1, horizon=4)
    assert hz[1]["score"] > hz[2]["score"]


def test_a_double_gameweek_pays_out_twice():
    b = bootstrap()
    b["elements"] = [player(1, team=1), player(2, team=3)]
    fx = [fixture(g, 1, 2) for g in range(1, 4)] + \
         [fixture(g, 3, 4) for g in range(1, 4)] + [fixture(2, 4, 3)]
    hz = horizon_scores(b, fx, 1, horizon=3)
    assert hz[2]["score"] > hz[1]["score"]


def test_horizon_grows_with_the_number_of_gameweeks():
    b = bootstrap()
    b["elements"] = [player(1, team=1)]
    fx = [fixture(g, 1, 2) for g in range(1, 9)]
    short = horizon_scores(b, fx, 1, horizon=2)[1]["score"]
    long = horizon_scores(b, fx, 1, horizon=6)[1]["score"]
    assert long > short


def test_horizon_is_order_blind_where_the_single_gameweek_score_is_not():
    """Same six fixtures, reversed. Next week's score must move (the decay exists
    to make it move); the six-week total must not, because you play them all."""
    b = bootstrap()
    b["elements"] = [player(1, team=1)]
    diffs = [1, 2, 3, 4, 5, 5]
    fwd = [fixture(g, 1, 2, hd=d) for g, d in enumerate(diffs, 1)]
    rev = [fixture(g, 1, 2, hd=d) for g, d in enumerate(reversed(diffs), 1)]

    assert score_players(b, fwd, 1)[1]["score"] != pytest.approx(
        score_players(b, rev, 1)[1]["score"])
    assert horizon_scores(b, fwd, 1, horizon=6)[1]["score"] == pytest.approx(
        horizon_scores(b, rev, 1, horizon=6)[1]["score"])


def test_horizon_prefers_the_better_run_between_equal_players():
    b = bootstrap()
    b["elements"] = [player(1, team=1), player(2, team=3)]
    fx = [fixture(g, 1, 2, hd=2) for g in range(1, 7)] + \
         [fixture(g, 3, 4, hd=5) for g in range(1, 7)]
    hz = horizon_scores(b, fx, 1, horizon=6)
    assert hz[1]["score"] > hz[2]["score"]


def test_the_single_gameweek_score_is_carried_through_untouched():
    """The optimizer reads `score`, so horizon_scores has to overwrite it - but the
    recorded, measurable next-gameweek number must survive alongside it."""
    b = bootstrap()
    b["elements"] = [player(1, team=1)]
    fx = [fixture(g, 1, 2) for g in range(1, 7)]
    gw = score_players(b, fx, 1)
    hz = horizon_scores(b, fx, 1, horizon=6)
    assert hz[1]["gw_score"] == gw[1]["score"]
    assert hz[1]["score"] != gw[1]["score"]
    assert hz[1]["cost"] == gw[1]["cost"] and hz[1]["pos"] == gw[1]["pos"]


def test_base_times_ease_reconstructs_the_single_gameweek_score():
    """horizon_scores re-applies ease onto `base`, so `base` must be exactly the
    pre-fixture half of `score` or the two views drift apart silently."""
    b = bootstrap()
    b["elements"] = [player(1, team=1)]
    fx = [fixture(1, 1, 2, hd=2)]
    gw = score_players(b, fx, 1)[1]
    ease = gameweek_ease("MID", 1, fx, 1, None)[0]
    assert gw["base"] * (0.8 + ease * 0.4) == pytest.approx(gw["score"], abs=1e-3)
