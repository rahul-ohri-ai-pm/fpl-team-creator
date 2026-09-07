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


# --- form shrinkage toward a price-implied prior -----------------------------
# records/gameweek_reviews.md's "GW3 review": a real backtest over 172 players
# found raw early-season form scores WORSE (RMSE 4.032) than each player's own
# price-implied baseline (3.266). FORM_SHRINKAGE_K blends the two, weighted by
# how many games `form` is actually built on. These need a priced pool (>=10
# same-position players) for `preseason.price_baselines` to fit at all - the
# single-element bootstrap above always leaves the prior unfitted (0), which is
# exactly why those tests above see raw form/ppg pass through unchanged.

def priced_pool(n=20, etype=1, cost_start=40, cost_step=5, ppg_per_pound=0.5):
    """ppg exactly proportional to price, so the fitted baseline is recoverable -
    mirrors tests/test_preseason.py's own make_priced_pool."""
    els = []
    for i in range(n):
        cost = cost_start + i * cost_step
        els.append(element(ppg=str(cost / 10 * ppg_per_pound), form="0.0"))
        els[-1]["id"] = i + 100
        els[-1]["now_cost"] = cost
        els[-1]["element_type"] = etype
    return els


def bootstrap_with_pool(target: dict, finished: int, pool_etype: int = 1) -> dict:
    return {
        "elements": priced_pool(etype=pool_etype) + [target],
        "events": [{"id": i, "finished": i <= finished} for i in range(1, 39)],
        "teams": [{"id": 1}],
    }


def test_form_shrinks_toward_the_price_implied_prior_early_season():
    """Target priced at £10.0m -> the pool's fit predicts ppg = 10.0*0.5 = 5.0.
    A raw form of 0.0 (a two-game cold streak) should pull toward that prior
    once real games have been played, not stay at the unshrunk 0.0."""
    target = element(ppg="0.0", form="0.0")
    target["now_cost"] = 100
    b = bootstrap_with_pool(target, finished=2)
    scored = score_players(b, NO_FIXTURES, next_event=3, risk_profile="safe")
    expected = (2 * 0.0 + 10 * 5.0) / (2 + 10)  # FORM_SHRINKAGE_K == 10
    assert scored[1]["score"] == pytest.approx(expected, abs=0.01)
    assert scored[1]["score"] > 0.0


def test_shrinkage_fades_as_more_games_accumulate():
    """The same raw-form/prior gap should matter less at a higher `finished` -
    the whole point of scaling the blend by games observed."""
    target = element(ppg="0.0", form="0.0")
    target["now_cost"] = 100
    early = score_players(bootstrap_with_pool(target, finished=2), NO_FIXTURES, 3, "safe")[1]["score"]
    later = score_players(bootstrap_with_pool(target, finished=20), NO_FIXTURES, 21, "safe")[1]["score"]
    assert early > later >= 0.0


def test_no_shrinkage_when_the_position_has_no_fitted_prior():
    """Pool is all GK (etype 1); target is a MID (etype 3) - no same-position
    pool to fit, so raw form must pass through unchanged, not toward 0."""
    target = element(ppg="6.0", form="6.0")
    target["element_type"] = 3
    b = bootstrap_with_pool(target, finished=2, pool_etype=1)
    scored = score_players(b, NO_FIXTURES, next_event=3, risk_profile="safe")
    assert scored[1]["score"] == pytest.approx(6.0, abs=0.01)
