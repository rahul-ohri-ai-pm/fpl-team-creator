"""Scoring formula (engine.score.score_players).

Synthetic bootstrap/fixtures only - no network access, mirrors the style of
tests/test_optimize.py and tests/test_backtest.py.
"""
import pytest

from engine.score import score_players


def make_bootstrap(n_finished_events: int, players: list[dict]) -> dict:
    events = [{"finished": i < n_finished_events} for i in range(38)]
    teams = [{"id": 1}]
    elements = []
    for i, p in enumerate(players):
        elements.append({
            "id": i + 1,
            "first_name": "P", "second_name": str(i + 1),
            "element_type": 3,  # MID
            "team": 1,
            "now_cost": 60,
            "form": p.get("form", 0),
            "points_per_game": p.get("points_per_game", 0),
            "minutes": p.get("minutes", 2500),
            "chance_of_playing_next_round": p.get("chance", None),
            "selected_by_percent": p.get("ownership", 0),
        })
    return {"events": events, "teams": teams, "elements": elements}


FIXTURES: list = []  # no upcoming fixtures -> fixture_ease() falls back to 0.5 for every team


def test_zero_finished_events_falls_back_to_points_per_game():
    """Pre-season: form is legitimately 0 for everyone - use last known ppg instead."""
    bootstrap = make_bootstrap(0, [{"form": 0, "points_per_game": 5.0}])
    scored = score_players(bootstrap, FIXTURES, next_event=1)
    # ease_mult = 1.0 (fixture_ease default 0.5 -> 0.8+0.5*0.4), reliability = min(1, 2500/(38*90*0.6))
    ease_mult = 0.8 + 0.5 * 0.4
    reliability = min(1.0, 2500 / (38 * 90 * 0.6))
    expected = 5.0 * ease_mult * reliability
    assert scored[1]["score"] == pytest.approx(expected, abs=0.001)


def test_finished_events_does_not_fall_back_even_when_form_is_zero():
    """Mid-season: a genuine scoring slump (form == 0) must not be papered over by
    a stale season-long points_per_game average - this is the bug being fixed."""
    bootstrap = make_bootstrap(10, [{"form": 0, "points_per_game": 8.0}])
    scored = score_players(bootstrap, FIXTURES, next_event=11)
    assert scored[1]["score"] == 0.0


def test_finished_events_uses_the_real_nonzero_form_not_ppg():
    """Regression guard: mid-season with a nonzero form must use form, not ppg,
    even when ppg is larger - catches any accidental revert to `form or ppg`."""
    bootstrap = make_bootstrap(10, [{"form": 2.0, "points_per_game": 8.0}])
    scored = score_players(bootstrap, FIXTURES, next_event=11)
    ease_mult = 0.8 + 0.5 * 0.4
    reliability = min(1.0, 2500 / (10 * 90 * 0.6))
    expected = 2.0 * ease_mult * reliability
    assert scored[1]["score"] == pytest.approx(expected, abs=0.001)


def test_confirmed_out_player_scores_zero_despite_high_ownership():
    """A player ruled out (chance_of_playing_next_round == 0) must not still carry
    a positive score from the ownership nudge alone."""
    bootstrap = make_bootstrap(10, [{"form": 6.0, "chance": 0, "ownership": 40.0}])
    scored = score_players(bootstrap, FIXTURES, next_event=11, risk_profile="safe")
    assert scored[1]["score"] == 0.0
