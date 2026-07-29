"""Prediction recording and measurement (engine.evaluate).

Synthetic live payloads - no network.
"""
import json

import pytest

from engine import evaluate as ev


def players(n=15, score=5.0):
    pos = ["GK"] + ["DEF"] * 5 + ["MID"] * 5 + ["FWD"] * 3 + ["GK"]
    return {i + 1: {"score": score, "name": f"P{i+1}", "pos": pos[i], "team": 1, "cost": 50}
            for i in range(n)}


def lineup(starters, bench, captain, vice):
    return {"starters": starters, "bench": bench, "captain": captain, "vice_captain": vice}


def standard():
    """1 GK, 4 DEF, 4 MID, 2 FWD starting; GK+DEF+MID+FWD on the bench."""
    p = players()
    starters = [1, 2, 3, 4, 5, 7, 8, 9, 10, 12, 13]
    bench = [15, 6, 11, 14]
    return p, lineup(starters, bench, 7, 2)


def live(points_by_id, minutes_by_id=None):
    minutes_by_id = minutes_by_id or {}
    return {"elements": [
        {"id": pid, "stats": {"total_points": pts,
                              "minutes": minutes_by_id.get(pid, 90)}}
        for pid, pts in points_by_id.items()]}


# --- recording ------------------------------------------------------------

def test_prediction_counts_the_captain_twice():
    p, lu = standard()
    entry = ev.build_prediction(1, lu, p)
    assert entry["predicted_xi"] == pytest.approx(55.0)
    assert entry["predicted_total"] == pytest.approx(60.0)


def test_record_appends_and_never_overwrites(tmp_path):
    path = str(tmp_path / "p.jsonl")
    p, lu = standard()
    ev.record_prediction(ev.build_prediction(1, lu, p), path)
    ev.record_prediction(ev.build_prediction(2, lu, p), path)
    assert [e["event"] for e in ev.load_predictions(path)] == [1, 2]
    assert len(open(path).read().strip().splitlines()) == 2


def test_rerunning_a_gameweek_keeps_both_and_reads_the_latest(tmp_path):
    path = str(tmp_path / "p.jsonl")
    p, lu = standard()
    ev.record_prediction(ev.build_prediction(1, lu, p), path)
    p2 = {k: {**v, "score": 9.0} for k, v in p.items()}
    ev.record_prediction(ev.build_prediction(1, lu, p2), path)
    assert len(ev.load_predictions(path)) == 2
    assert ev.prediction_for(1, path)["predicted_xi"] == pytest.approx(99.0)


def test_missing_and_corrupt_lines_do_not_break_the_run(tmp_path):
    path = tmp_path / "p.jsonl"
    assert ev.load_predictions(str(tmp_path / "absent.jsonl")) == []
    p, lu = standard()
    good = json.dumps(ev.build_prediction(1, lu, p))
    path.write_text(good + "\n{ broken\n\n")
    assert len(ev.load_predictions(str(path))) == 1


def test_prediction_for_unknown_gameweek_is_none(tmp_path):
    assert ev.prediction_for(9, str(tmp_path / "p.jsonl")) is None


# --- measuring ------------------------------------------------------------

def test_evaluate_returns_none_when_nothing_was_predicted(tmp_path):
    assert ev.evaluate_gameweek(1, live({1: 5}), str(tmp_path / "p.jsonl")) is None


def test_actual_total_doubles_the_captain(tmp_path):
    path = str(tmp_path / "p.jsonl")
    p, lu = standard()
    ev.record_prediction(ev.build_prediction(1, lu, p), path)
    pts = {pid: 3 for pid in range(1, 16)}
    pts[7] = 10  # captain
    result = ev.evaluate_gameweek(1, live(pts), path)
    # XI = 10 others on 3 (=30) + the captain on 10, then the captain again
    assert result["actual_total"] == 30 + 10 + 10
    assert result["captain"] == 7


def test_error_and_bias_are_signed_so_under_prediction_is_visible(tmp_path):
    path = str(tmp_path / "p.jsonl")
    p, lu = standard()
    ev.record_prediction(ev.build_prediction(1, lu, p), path)
    result = ev.evaluate_gameweek(1, live({pid: 8 for pid in range(1, 16)}), path)
    assert result["bias"] > 0          # predicted 5.0, actual 8 -> under-predicted
    assert result["error"] > 0
    assert result["mae"] == pytest.approx(3.0)


def test_a_blanked_starter_is_replaced_by_a_bench_player_who_played(tmp_path):
    path = str(tmp_path / "p.jsonl")
    p, lu = standard()
    ev.record_prediction(ev.build_prediction(1, lu, p), path)
    pts = {pid: 3 for pid in range(1, 16)}
    mins = {13: 0}  # a starting FWD didn't play
    result = ev.evaluate_gameweek(1, live(pts, mins), path)
    assert result["auto_subs"], "expected an auto-sub"
    out, came_in = result["auto_subs"][0]
    assert out == 13
    assert came_in in lu["bench"]


def test_auto_sub_keeps_the_formation_legal(tmp_path):
    """Blanking two defenders must not drop the XI below three."""
    path = str(tmp_path / "p.jsonl")
    p, lu = standard()
    ev.record_prediction(ev.build_prediction(1, lu, p), path)
    pts = {pid: 3 for pid in range(1, 16)}
    result = ev.evaluate_gameweek(1, live(pts, {2: 0, 3: 0}), path)
    positions = {int(k): v for k, v in ev.prediction_for(1, path)["positions"].items()}
    xi, _ = ev.apply_auto_subs(ev.prediction_for(1, path), {2: 0, 3: 0, **{i: 90 for i in range(1, 16) if i not in (2, 3)}})
    counts = {}
    for pid in xi:
        counts[positions[pid]] = counts.get(positions[pid], 0) + 1
    assert counts["GK"] == 1
    assert counts["DEF"] >= 3
    assert len(xi) == 11


def test_outfield_player_never_replaces_the_keeper(tmp_path):
    path = str(tmp_path / "p.jsonl")
    p, lu = standard()
    ev.record_prediction(ev.build_prediction(1, lu, p), path)
    pred = ev.prediction_for(1, path)
    mins = {i: 90 for i in range(1, 16)}
    mins[1] = 0   # starting GK blanks
    mins[15] = 0  # bench GK also didn't play
    xi, swaps = ev.apply_auto_subs(pred, mins)
    assert swaps == [], "no legal keeper replacement existed, so nobody should come on"


def test_armband_passes_to_the_vice_when_the_captain_does_not_play(tmp_path):
    path = str(tmp_path / "p.jsonl")
    p, lu = standard()
    ev.record_prediction(ev.build_prediction(1, lu, p), path)
    pts = {pid: 3 for pid in range(1, 16)}
    pts[2] = 12  # the vice
    result = ev.evaluate_gameweek(1, live(pts, {7: 0}), path)
    assert result["captain"] == 2
    assert result["captain_changed"] is True


def test_bench_points_do_not_count_unless_auto_subbed(tmp_path):
    path = str(tmp_path / "p.jsonl")
    p, lu = standard()
    ev.record_prediction(ev.build_prediction(1, lu, p), path)
    pts = {pid: 0 for pid in range(1, 16)}
    for b in lu["bench"]:
        pts[b] = 20  # a huge bench, all of it irrelevant
    result = ev.evaluate_gameweek(1, live(pts), path)
    assert result["actual_total"] == 0


# --- calibration ----------------------------------------------------------

def test_calibration_is_empty_before_any_gameweek_is_played():
    assert ev.calibration(evaluations=[])["gameweeks"] == 0


def test_calibration_averages_across_gameweeks():
    evals = [
        {"predicted_total": 60.0, "actual_total": 70, "error": 10.0},
        {"predicted_total": 60.0, "actual_total": 50, "error": -10.0},
    ]
    c = ev.calibration(evaluations=evals)
    assert c["gameweeks"] == 2
    assert c["mean_error"] == pytest.approx(0.0)
    assert c["mean_abs_error"] == pytest.approx(10.0)  # cancellation must not hide error
