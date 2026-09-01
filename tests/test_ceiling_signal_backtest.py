"""Ceiling-signal correlation math (engine.ceiling_signal_backtest).

Synthetic rows only - no network. `collect()` itself hits the live API, so it's
not exercised here; these tests pin the pure math (`compare`, `big_haul_hit_rate`)
against hand-constructed data where the "right" answer is obvious by construction.
"""
import pytest

from engine.ceiling_signal_backtest import big_haul_hit_rate, compare


def row(pos, points, threat, bps, ict_index, next_points):
    return {"pos": pos, "points": points, "threat": threat, "bps": bps,
            "ict_index": ict_index, "next_points": next_points}


def test_compare_prefers_a_signal_that_actually_tracks_the_target():
    """threat rises in lockstep with next_points; points is pure noise (constant).
    threat's correlation must come out near 1.0, points' must come out as None
    (constant input has no variance - engine.backtest.correlation returns None)."""
    rows = [row("MID", points=5, threat=t, bps=10, ict_index=1.0, next_points=t)
            for t in range(1, 15)]
    result = compare(rows)
    assert result["MID"]["threat"] == pytest.approx(1.0, abs=0.01)
    assert result["MID"]["points"] is None  # constant "points" column, no variance


def test_compare_splits_by_position_independently():
    mids = [row("MID", 5, t, 10, 1.0, t) for t in range(1, 10)]
    defs = [row("DEF", 5, 10 - t, 10, 1.0, t) for t in range(1, 10)]  # inverse relation
    result = compare(mids + defs)
    assert result["MID"]["threat"] > 0.9
    assert result["DEF"]["threat"] < -0.9
    assert result["ALL"]["n"] == 18


def test_big_haul_hit_rate_identifies_the_true_top_decile():
    """10 players ranked 1..10 by `threat`; only the top one clears the big-haul
    threshold. The top-decile bucket (10% of 10 = 1 player) must be exactly that
    player, so the hit rate is 1.0, not diluted by the rest of the pool."""
    rows = [row("MID", 0, t, 0, 0, next_points=(20 if t == 10 else 2)) for t in range(1, 11)]
    hr = big_haul_hit_rate(rows, "threat", threshold=10, decile=10)
    assert hr["n"] == 1
    assert hr["hits"] == 1
    assert hr["rate"] == 1.0
    assert hr["baseline_rate"] == pytest.approx(0.1)


def test_big_haul_hit_rate_below_decile_size_returns_empty():
    rows = [row("MID", 0, i, 0, 0, 2) for i in range(3)]
    hr = big_haul_hit_rate(rows, "threat")
    assert hr["rate"] is None
