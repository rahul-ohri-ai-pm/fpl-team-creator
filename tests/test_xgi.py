"""Underlying-numbers blend (engine.score.XGI_BLEND and friends).

The weights here came from engine/backtest.py, not from taste: last season's xGI/90
predicts the following season better than last season's points do, but only for
midfielders and forwards. These tests pin the *shape* of that decision - where the
blend applies, where it must not, and that it degrades safely.
"""
import pytest

from engine.score import (
    XGI_BLEND,
    XGI_MIN_MINUTES,
    blended_ppg,
    score_players,
    xgi_models,
)


def element(pid, element_type=3, ppg="5.0", xgi90="0.50", minutes=3000, cost=70, team=1):
    return {"id": pid, "web_name": f"P{pid}", "first_name": "F", "second_name": f"L{pid}",
            "element_type": element_type, "team": team, "now_cost": cost,
            "points_per_game": ppg, "form": "0.0", "minutes": minutes,
            "expected_goal_involvements_per_90": xgi90,
            "chance_of_playing_next_round": None, "selected_by_percent": "5.0"}


def pool(n=40, element_type=3):
    """A pool where ppg rises with xGI/90, so the fit has a real slope."""
    els = []
    for i in range(n):
        xgi = 0.10 + i * 0.02
        els.append(element(i + 1, element_type=element_type,
                           ppg=f"{2.0 + xgi * 6:.2f}", xgi90=f"{xgi:.2f}"))
    return els


def bootstrap(elements):
    return {
        "events": [{"id": i, "finished": False, "is_current": False, "is_next": i == 1}
                   for i in range(1, 9)],
        "teams": [{"id": i, "short_name": f"T{i}", "strength": None,
                   "strength_attack_home": 0, "strength_attack_away": 0,
                   "strength_defence_home": 0, "strength_defence_away": 0}
                  for i in range(1, 5)],
        "elements": elements,
    }


def fixtures():
    return [{"event": g, "team_h": 1, "team_a": 2,
             "team_h_difficulty": 3, "team_a_difficulty": 3} for g in range(1, 9)]


# --- where the blend applies ---------------------------------------------

def test_the_backtest_result_is_encoded_by_position():
    """GK and DEF lost the backtest, so they must carry no blend at all."""
    assert XGI_BLEND["GK"] == 0.0
    assert XGI_BLEND["DEF"] == 0.0
    assert XGI_BLEND["MID"] > 0
    assert XGI_BLEND["FWD"] > 0


def test_keepers_and_defenders_keep_their_realized_points_untouched():
    models = xgi_models(bootstrap(pool(element_type=2)))
    for et, pos in ((1, "GK"), (2, "DEF")):
        assert blended_ppg(models, et, pos, ppg=4.0, xgi90=0.9, minutes=3000) == 4.0


def test_a_midfielder_outperforming_his_chances_is_marked_down():
    """The Mbeumo case in reverse: banked points well above what the chances imply
    is exactly the finishing luck the backtest says does not survive a summer."""
    els = pool()
    models = xgi_models(bootstrap(els))
    lucky = blended_ppg(models, 3, "MID", ppg=8.0, xgi90=0.10, minutes=3000)
    assert lucky < 8.0


def test_a_midfielder_underperforming_his_chances_is_marked_up():
    els = pool()
    models = xgi_models(bootstrap(els))
    unlucky = blended_ppg(models, 3, "MID", ppg=3.0, xgi90=0.90, minutes=3000)
    assert unlucky > 3.0


def test_the_blend_preserves_the_positions_mean_and_spread():
    """The whole safety property. A raw blend shrinks toward the fitted line, and
    the squad is picked from the top tail where everyone sits above it - so an
    unrescaled blend re-levels midfielders against defenders and biases every
    recorded predicted_total low. Level and spread must come back unchanged; only
    the ordering may move."""
    els = pool()
    models = xgi_models(bootstrap(els))
    before, after = [], []
    for e in els:
        ppg = float(e["points_per_game"])
        before.append(ppg)
        after.append(blended_ppg(models, 3, "MID", ppg=ppg,
                                 xgi90=float(e["expected_goal_involvements_per_90"]),
                                 minutes=e["minutes"]))
    n = len(before)
    mean_b, mean_a = sum(before)/n, sum(after)/n
    sd = lambda v, m: (sum((x-m)**2 for x in v)/n) ** 0.5
    assert mean_a == pytest.approx(mean_b, abs=1e-6)
    assert sd(after, mean_a) == pytest.approx(sd(before, mean_b), abs=1e-6)


def test_an_exceptional_midfielder_is_not_dragged_toward_the_pack():
    """The bug this guards: blending pulled the best midfielder down 1.25 points
    while leaving an equally exceptional defender alone, which moved the armband."""
    els = pool()
    els.append(element(900, ppg="9.0", xgi90="0.95"))
    models = xgi_models(bootstrap(els))
    got = blended_ppg(models, 3, "MID", ppg=9.0, xgi90=0.95, minutes=3000)
    assert got > 8.0


# --- where it must not apply ---------------------------------------------

def test_a_player_without_a_full_season_is_left_alone():
    """Below the minutes floor an xGI/90 is a few cameos amplified by the division."""
    els = pool()
    models = xgi_models(bootstrap(els))
    assert blended_ppg(models, 3, "MID", ppg=5.0, xgi90=1.5,
                       minutes=XGI_MIN_MINUTES - 1) == 5.0


def test_a_player_with_no_recorded_chances_is_left_alone():
    els = pool()
    models = xgi_models(bootstrap(els))
    assert blended_ppg(models, 3, "MID", ppg=5.0, xgi90=0.0, minutes=3000) == 5.0


def test_an_unfittable_pool_falls_back_to_realized_points():
    """Fewer than 10 usable players, or no spread, means no model - and no blend,
    rather than a fit invented from three points."""
    thin = bootstrap([element(i, xgi90="0.4") for i in range(1, 4)])
    assert xgi_models(thin) == {}
    assert blended_ppg({}, 3, "MID", ppg=5.0, xgi90=0.9, minutes=3000) == 5.0


def test_missing_xgi_fields_do_not_break_scoring():
    """Older payloads and edge cases: absent field must degrade, not raise."""
    els = pool()
    for e in els:
        e.pop("expected_goal_involvements_per_90")
    scored = score_players(bootstrap(els), fixtures(), 1)
    assert len(scored) == len(els)
    assert all(s["score"] > 0 for s in scored.values())


def test_scoring_still_ranks_the_better_underlying_midfielder_higher():
    els = pool()
    # Two identical-ppg midfielders, different chance volume.
    els.append(element(900, ppg="5.0", xgi90="0.15"))
    els.append(element(901, ppg="5.0", xgi90="0.85"))
    scored = score_players(bootstrap(els), fixtures(), 1)
    assert scored[901]["score"] > scored[900]["score"]
