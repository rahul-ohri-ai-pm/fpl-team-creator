"""Position-aware opponent matchup (engine.score).

FDR gives a goalkeeper and a striker the same number for the same fixture. These
tests pin down that the matchup layer separates them, and that it disappears
cleanly when FPL hasn't populated the strength fields.
"""
import pytest

from engine import preseason as ps
from engine.score import (
    MATCHUP_WEIGHT,
    _normalized_strengths,
    opponent_matchup_ease,
    score_players,
)


def team(tid, name, att_h=1200, att_a=1150, def_h=1200, def_a=1150):
    return {"id": tid, "short_name": name,
            "strength_attack_home": att_h, "strength_attack_away": att_a,
            "strength_defence_home": def_h, "strength_defence_away": def_a}


# A great attack that cannot defend, and its mirror image.
ALL_ATTACK = team(2, "ATT", att_h=1400, att_a=1400, def_h=1000, def_a=1000)
ALL_DEFENCE = team(3, "DEF", att_h=1000, att_a=1000, def_h=1400, def_a=1400)
TEAMS = [team(1, "US"), ALL_ATTACK, ALL_DEFENCE]


def fixture(event, home, away, fdr=3):
    return {"event": event, "team_h": home, "team_a": away,
            "team_h_difficulty": fdr, "team_a_difficulty": fdr}


# --- normalisation --------------------------------------------------------

def test_flat_strength_fields_are_reported_as_unusable():
    """Pre-season every club sits at 0; a constant is not a signal."""
    flat = [team(1, "A", 0, 0, 0, 0), team(2, "B", 0, 0, 0, 0)]
    assert _normalized_strengths(flat) is None


def test_missing_strength_fields_are_unusable():
    assert _normalized_strengths([{"id": 1}, {"id": 2}]) is None


def test_normalisation_is_scale_free():
    """A 1-5 scale and a 1000-1400 scale must normalise identically."""
    small = [team(1, "A", 1, 1, 1, 1), team(2, "B", 5, 5, 5, 5)]
    large = [team(1, "A", 1000, 1000, 1000, 1000), team(2, "B", 1400, 1400, 1400, 1400)]
    assert _normalized_strengths(small) == _normalized_strengths(large)


# --- the matchup itself ---------------------------------------------------

def test_defenders_and_forwards_read_the_same_fixture_differently():
    """The whole point: one FDR integer cannot serve both."""
    s = _normalized_strengths(TEAMS)
    fx = [fixture(1, 1, 2)]  # us at home to the all-attack side
    d = opponent_matchup_ease("DEF", 1, fx, 1, s)
    f = opponent_matchup_ease("FWD", 1, fx, 1, s)
    assert d < f, "a lethal attack should worry a defender more than a forward"


def test_facing_a_leaky_defence_favours_forwards():
    s = _normalized_strengths(TEAMS)
    vs_leaky = opponent_matchup_ease("FWD", 1, [fixture(1, 1, 2)], 1, s)   # weak defence
    vs_solid = opponent_matchup_ease("FWD", 1, [fixture(1, 1, 3)], 1, s)   # strong defence
    assert vs_leaky > vs_solid


def test_facing_a_toothless_attack_favours_defenders():
    s = _normalized_strengths(TEAMS)
    vs_toothless = opponent_matchup_ease("DEF", 1, [fixture(1, 1, 3)], 1, s)
    vs_lethal = opponent_matchup_ease("DEF", 1, [fixture(1, 1, 2)], 1, s)
    assert vs_toothless > vs_lethal


def test_keeper_is_driven_entirely_by_the_opponent_attack():
    s = _normalized_strengths(TEAMS)
    gk = opponent_matchup_ease("GK", 1, [fixture(1, 1, 3)], 1, s)   # no attack, great defence
    assert gk == pytest.approx(1.0), "an opponent who cannot attack is the easiest possible"


def test_opponent_venue_is_the_mirror_of_ours():
    """Facing a side away means facing their away strength, not their home strength."""
    lopsided = [team(1, "US"),
                team(2, "OPP", att_h=1400, att_a=1000, def_h=1400, def_a=1000),
                team(3, "REF", att_h=1200, att_a=1200, def_h=1200, def_a=1200)]
    s = _normalized_strengths(lopsided)
    us_home = opponent_matchup_ease("DEF", 1, [fixture(1, 1, 2)], 1, s)  # they are away
    us_away = opponent_matchup_ease("DEF", 1, [fixture(1, 2, 1)], 1, s)  # they are home
    assert us_home > us_away


def test_matchup_respects_the_fixture_decay():
    s = _normalized_strengths(TEAMS)
    hard_now = opponent_matchup_ease("DEF", 1, [fixture(1, 1, 2), fixture(2, 1, 3)], 1, s)
    hard_later = opponent_matchup_ease("DEF", 1, [fixture(1, 1, 3), fixture(2, 1, 2)], 1, s)
    assert hard_later > hard_now


def test_no_strengths_or_no_fixtures_yields_none():
    s = _normalized_strengths(TEAMS)
    assert opponent_matchup_ease("DEF", 1, [fixture(1, 1, 2)], 1, None) is None
    assert opponent_matchup_ease("DEF", 1, [], 1, s) is None


# --- integration into scoring ---------------------------------------------

def element(pid, etype, team_id):
    return {"id": pid, "web_name": f"P{pid}", "first_name": "A", "second_name": f"P{pid}",
            "points_per_game": "5.0", "minutes": 3000, "now_cost": 60,
            "element_type": etype, "form": "0.0", "chance_of_playing_next_round": None,
            "selected_by_percent": "10.0", "team": team_id}


def bootstrap(teams):
    return {"elements": [element(1, 2, 1), element(2, 4, 1)],  # a DEF and a FWD, same club
            "events": [{"id": i, "finished": False} for i in range(1, 39)],
            "teams": teams}


def test_same_club_defender_and_forward_diverge_once_strengths_exist():
    fx = [fixture(1, 1, 2)]  # at home to the all-attack, no-defence side
    scored = score_players(bootstrap(TEAMS), fx, 1, "safe", preseason=ps.Preseason())
    assert scored[2]["score"] > scored[1]["score"], \
        "the forward faces a leaky defence; the defender faces a lethal attack"


def test_scoring_falls_back_to_fdr_when_strengths_are_flat():
    """Pre-season the fields are all 0 - identical inputs must give identical scores."""
    flat = [team(1, "US", 0, 0, 0, 0), team(2, "OPP", 0, 0, 0, 0)]
    fx = [fixture(1, 1, 2)]
    scored = score_players(bootstrap(flat), fx, 1, "safe", preseason=ps.Preseason())
    assert scored[1]["score"] == pytest.approx(scored[2]["score"])


def test_matchup_only_moves_the_estimate_by_its_configured_share():
    """FDR still anchors: the blend can't be dominated by the matchup term."""
    assert 0.0 < MATCHUP_WEIGHT <= 0.5
