"""Weight-scheme backtesting (engine.backtest).

No live network calls: the GW1 snapshot fixture below is a frozen copy of
records/snapshots/gw1_preseason_reconstruction.json (already verified against
the manually-computed figures in records/scoring_backtest.md), and
check_gameweek_finished/load_or_build_snapshot are monkeypatched so tests are
deterministic and offline.
"""
import json

import pytest

from engine.backtest import (
    SCHEMES,
    TEST_SQUADS,
    _validate_custom_scheme,
    backtest,
    check_gameweek_finished as real_check_gameweek_finished,
    score_with_scheme,
)

GW1_SNAPSHOT = {
    "gw": 1,
    "prior_season": "2025/26",
    "players": {
        "1": {"name": "Raya", "pos": "GK", "team": 1, "cost": 60, "ppg": 4.2631578947368425,
              "minutes": 3330, "ease_base": 0.4375, "chance": None, "ownership": 38.3},
        "4": {"name": "Gabriel", "pos": "DEF", "team": 1, "cost": 80, "ppg": 5.5,
              "minutes": 2750, "ease_base": 0.4375, "chance": None, "ownership": 29.2},
        "82": {"name": "Kelleher", "pos": "GK", "team": 4, "cost": 50, "ppg": 3.763157894736842,
               "minutes": 3330, "ease_base": 0.5625, "chance": None, "ownership": 6.5},
        "106": {"name": "Igor Thiago", "pos": "FWD", "team": 4, "cost": 80, "ppg": 4.7631578947368425,
                "minutes": 3282, "ease_base": 0.5625, "chance": None, "ownership": 16.7},
        "112": {"name": "van Hecke", "pos": "DEF", "team": 19, "cost": 50, "ppg": 3.8947368421052633,
                "minutes": 3210, "ease_base": 0.5625, "chance": None, "ownership": 9.7},
        "155": {"name": "Enzo", "pos": "MID", "team": 6, "cost": 70, "ppg": 4.131578947368421,
                "minutes": 3114, "ease_base": 0.5, "chance": None, "ownership": 4.6},
        "165": {"name": "João Pedro", "pos": "FWD", "team": 6, "cost": 76, "ppg": 4.657894736842105,
                "minutes": 2658, "ease_base": 0.5, "chance": None, "ownership": 67.7},
        "201": {"name": "Muñoz", "pos": "DEF", "team": 8, "cost": 55, "ppg": 3.5789473684210527,
                "minutes": 2400, "ease_base": 0.5, "chance": None, "ownership": 8.5},
        "204": {"name": "Mitchell", "pos": "DEF", "team": 8, "cost": 45, "ppg": 3.5526315789473686,
                "minutes": 3253, "ease_base": 0.5, "chance": None, "ownership": 5.6},
        "229": {"name": "Tarkowski", "pos": "DEF", "team": 9, "cost": 60, "ppg": 4.473684210526316,
                "minutes": 3330, "ease_base": 0.4375, "chance": None, "ownership": 8.8},
        "236": {"name": "Dewsbury-Hall", "pos": "MID", "team": 9, "cost": 65, "ppg": 3.973684210526316,
                "minutes": 2629, "ease_base": 0.4375, "chance": None, "ownership": 4.6},
        "260": {"name": "H.Wilson", "pos": "MID", "team": 13, "cost": 65, "ppg": 4.421052631578948,
                "minutes": 2674, "ease_base": 0.5625, "chance": None, "ownership": 5.7},
        "335": {"name": "Stach", "pos": "MID", "team": 13, "cost": 60, "ppg": 3.6052631578947367,
                "minutes": 2369, "ease_base": 0.5625, "chance": None, "ownership": 2.2},
        "346": {"name": "Calvert-Lewin", "pos": "FWD", "team": 13, "cost": 60, "ppg": 3.736842105263158,
                "minutes": 2721, "ease_base": 0.5625, "chance": None, "ownership": 28.8},
        "356": {"name": "van Dijk", "pos": "DEF", "team": 14, "cost": 65, "ppg": 4.605263157894737,
                "minutes": 3420, "ease_base": 0.625, "chance": None, "ownership": 19.6},
        "368": {"name": "Szoboszlai", "pos": "MID", "team": 14, "cost": 70, "ppg": 4.2105263157894735,
                "minutes": 3232, "ease_base": 0.625, "chance": None, "ownership": 43.1},
        "388": {"name": "Guéhi", "pos": "DEF", "team": 15, "cost": 60, "ppg": 4.7105263157894735,
                "minutes": 3150, "ease_base": 0.5, "chance": None, "ownership": 19.4},
        "397": {"name": "Semenyo", "pos": "MID", "team": 15, "cost": 85, "ppg": 5.315789473684211,
                "minutes": 3200, "ease_base": 0.5, "chance": None, "ownership": 24.3},
        "426": {"name": "B.Fernandes", "pos": "MID", "team": 16, "cost": 120, "ppg": 6.184210526315789,
                "minutes": 3065, "ease_base": 0.5625, "chance": None, "ownership": 48.5},
        "427": {"name": "Mbeumo", "pos": "MID", "team": 16, "cost": 80, "ppg": 3.8947368421052633,
                "minutes": 2611, "ease_base": 0.5625, "chance": None, "ownership": 36.0},
        "452": {"name": "Bruno G.", "pos": "MID", "team": 1, "cost": 69, "ppg": 4.052631578947368,
                "minutes": 2456, "ease_base": 0.4375, "chance": 75, "ownership": 2.9},
        "480": {"name": "Gibbs-White", "pos": "MID", "team": 18, "cost": 80, "ppg": 4.947368421052632,
                "minutes": 3101, "ease_base": 0.4375, "chance": 75, "ownership": 8.7},
        "497": {"name": "Dubravka", "pos": "GK", "team": 19, "cost": 40, "ppg": 2.526315789473684,
                "minutes": 3150, "ease_base": 0.5625, "chance": None, "ownership": 18.6},
        "498": {"name": "Senesi", "pos": "DEF", "team": 19, "cost": 60, "ppg": 4.605263157894737,
                "minutes": 3288, "ease_base": 0.5625, "chance": None, "ownership": 7.7},
        "527": {"name": "Richarlison", "pos": "FWD", "team": 19, "cost": 60, "ppg": 3.1315789473684212,
                "minutes": 1954, "ease_base": 0.5625, "chance": None, "ownership": 2.9},
        "529": {"name": "Roefs", "pos": "GK", "team": 20, "cost": 50, "ppg": 3.5789473684210527,
                "minutes": 3150, "ease_base": 0.5625, "chance": None, "ownership": 4.0},
        "533": {"name": "Mukiele", "pos": "DEF", "team": 20, "cost": 55, "ppg": 3.973684210526316,
                "minutes": 2784, "ease_base": 0.5625, "chance": 100, "ownership": 2.6},
    },
    "actual_points": {
        "1": 6, "4": 5, "82": 7, "106": 0, "112": 1, "155": 1, "165": 11, "201": 0, "204": 1,
        "229": 6, "236": 11, "260": 3, "335": 13, "346": 1, "356": 2, "368": 8, "388": 10,
        "397": 2, "426": 2, "427": 2, "452": 0, "480": 2, "497": 0, "498": 3, "527": 2,
        "529": 1, "533": 0,
    },
}


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Every test in this module runs against the frozen fixture, never the live API."""
    monkeypatch.setattr("engine.backtest.check_gameweek_finished", lambda gw: None)
    monkeypatch.setattr("engine.backtest.load_or_build_snapshot", lambda gw, ids: GW1_SNAPSHOT)


def test_score_with_scheme_matches_hand_computation():
    player = {"ppg": 5.0, "minutes": 1710, "ease_base": 0.5, "chance": 100, "ownership": 20.0}
    scheme = SCHEMES["baseline"]
    # form=5.0, ease_mult=0.8+0.5*0.4=1.0, reliability=min(1, 1710/(38*90*0.6))=0.833..,
    # injury_mult=1.0, ownership_add=(20/100)*1.5=0.3
    expected = 5.0 * 1.0 * (1710 / (38 * 90 * 0.6)) * 1.0 + 0.3
    assert score_with_scheme(player, scheme, "safe") == pytest.approx(expected)


def test_conservative_injury_penalty_is_flat_subtraction():
    player = {"ppg": 4.0, "minutes": 3420, "ease_base": 0.5, "chance": 50, "ownership": 0.0}
    scheme = SCHEMES["conservative"]
    injury_mult = max(0.0, 50 / 100 + scheme["injury_penalty_flat"])  # 0.5 - 0.1 = 0.4
    ease_mult = scheme["ease_min"] + 0.5 * (scheme["ease_max"] - scheme["ease_min"])
    reliability = min(1.0, 3420 / (38 * 90 * scheme["reliability_divisor_factor"]))
    expected = 4.0 * scheme["form_mult"] * ease_mult * reliability * injury_mult
    assert score_with_scheme(player, scheme, "safe") == pytest.approx(expected)


def test_new_signing_aware_downweights_low_minutes_player():
    low_minutes = {"ppg": 5.0, "minutes": 100, "ease_base": 0.5, "chance": None, "ownership": 0.0}
    baseline_score = score_with_scheme(low_minutes, SCHEMES["baseline"], "safe")
    nsa_score = score_with_scheme(low_minutes, SCHEMES["new_signing_aware"], "safe")
    assert nsa_score == pytest.approx(baseline_score * 0.85)


@pytest.mark.parametrize("scheme_name,expected_rmse,expected_bias", [
    ("baseline", 10.94, 10.15),
    ("conservative", 4.30, 0.97),
    ("aggressive", 14.41, 13.82),
    ("new_signing_aware", 10.94, 10.15),
])
def test_named_schemes_reproduce_recorded_gw1_numbers(scheme_name, expected_rmse, expected_bias):
    """Regression check against records/scoring_backtest.md's GW1 backtest table."""
    result = backtest(SCHEMES[scheme_name], gw=1)
    assert result["rmse"] == pytest.approx(expected_rmse, abs=0.01)
    assert result["bias"] == pytest.approx(expected_bias, abs=0.01)


def test_backtest_per_squad_predicted_matches_recorded_values():
    result = backtest(SCHEMES["conservative"], gw=1)
    assert result["per_squad"]["Team A"]["predicted"] == pytest.approx(43.87, abs=0.01)
    assert result["per_squad"]["Team B"]["predicted"] == pytest.approx(46.55, abs=0.01)
    assert result["per_squad"]["Team C"]["predicted"] == pytest.approx(45.50, abs=0.01)


def test_unfinished_gameweek_is_refused(monkeypatch):
    import engine.backtest as bt

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"events": [{"id": 2, "finished": False, "data_checked": False}]}

    monkeypatch.setattr(bt.requests, "get", lambda *a, **k: FakeResponse())

    with pytest.raises(ValueError, match="not finished yet"):
        real_check_gameweek_finished(2)


def test_custom_scheme_requires_all_keys():
    with pytest.raises(ValueError, match="missing required keys"):
        _validate_custom_scheme({"form_mult": 1.0})


def test_custom_scheme_ownership_weight_must_be_dict():
    scheme = dict(SCHEMES["baseline"])
    scheme["ownership_weight"] = 1.5
    with pytest.raises(ValueError, match="must be a dict"):
        _validate_custom_scheme(scheme)


def test_test_squads_are_15_players_each():
    for name, ids in TEST_SQUADS.items():
        assert len(ids) == 15, name
        assert len(set(ids)) == 15, f"{name} has duplicate player ids"
