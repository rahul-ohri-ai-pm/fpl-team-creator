"""Season-stage gate on the `form == 0` fallback (engine.score.score_players).

No network: synthetic bootstrap payloads, mirrors tests/test_preseason.py's helpers.
Isolates the `form` input by holding every other multiplier at 1.0 - full-season
minutes (so `reliability` caps at 1.0 both pre- and in-season), no fixtures (so
`ease_mult` sits at its 0.5-ease default of 1.0), no injury flag, and a
goalkeeper (XGI_BLEND["GK"] == 0.0, so `ppg` is never xGI-blended) - so
`predicted score == form` exactly under these conditions, and any drift in the
fallback logic shows up directly in the asserted score.
"""
import pytest

from engine import preseason as ps
from engine.score import score_players


def element(ppg="5.0", form="0.0"):
    return {
        "id": 1, "web_name": "P", "first_name": "A", "second_name": "P",
        "points_per_game": ppg, "minutes": 3420, "now_cost": 50,
        "element_type": 1, "form": form, "chance_of_playing_next_round": None,
        "selected_by_percent": "10.0", "team": 1,
    }


def bootstrap(el, finished=0):
    return {
        "elements": [el],
        "events": [{"id": i, "finished": i <= finished} for i in range(1, 39)],
        "teams": [{"id": 1}],
    }


NO_FIXTURES: list = []


def score_of(el, finished):
    scored = score_players(bootstrap(el, finished), NO_FIXTURES, 1, "safe", preseason=ps.Preseason())
    return scored[1]["score"]


def test_zero_finished_events_falls_back_to_points_per_game():
    """Pre-season: form is legitimately 0 for everyone - use ppg instead."""
    assert score_of(element(ppg="5.0", form="0.0"), finished=0) == pytest.approx(5.0)


def test_finished_events_does_not_fall_back_even_when_form_is_zero():
    """Mid-season: a genuine scoring slump (form == 0) must not be papered over
    by a stale season-long ppg average - this is the bug being guarded against."""
    assert score_of(element(ppg="8.0", form="0.0"), finished=10) == pytest.approx(0.0)


def test_finished_events_uses_the_real_nonzero_form_not_ppg():
    """Regression guard: mid-season with a nonzero form must use form, not ppg,
    even when ppg is larger - catches any accidental revert to `form or ppg`."""
    assert score_of(element(ppg="8.0", form="2.0"), finished=10) == pytest.approx(2.0)
