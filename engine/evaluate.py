"""Prediction tracking: record what was recommended, then measure it.

The point of this module is that `engine/score.py` is a heuristic nobody has
checked against reality. Every weekly run appends its recommendation and its
predicted points to `records/predictions.jsonl`; the following week's run reads
the gameweek back, applies the real FPL points, and reports the error. Over a
season that turns the scoring weights from guesses into something calibrated.

`records/predictions.jsonl` is append-only, one JSON object per line - a format
that survives concurrent appends and keeps every past prediction verbatim, which
a rewritten summary file would not.
"""
from __future__ import annotations

import datetime as _dt
import json
import os

PREDICTIONS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "records", "predictions.jsonl")

# Legal starting XI bounds, repeated here rather than imported from optimize.py so
# that evaluation doesn't depend on the optimizer being importable (pulp, a solver).
FORMATION_LIMITS = {"GK": (1, 1), "DEF": (3, 5), "MID": (2, 5), "FWD": (1, 3)}


# --- recording ------------------------------------------------------------

def build_prediction(event: int, lineup: dict, players: dict, meta: dict | None = None) -> dict:
    """One gameweek's recommendation, with the points it is predicted to score.

    `predicted_total` counts the captain twice, matching how FPL actually scores,
    so it can be compared directly against the entry's real gameweek points.
    """
    starters, bench = lineup["starters"], lineup["bench"]
    captain, vice = lineup["captain"], lineup["vice_captain"]
    xi = sum(players[pid]["score"] for pid in starters)
    return {
        "event": event,
        "recorded_at": _dt.date.today().isoformat(),
        "starters": list(starters),
        "bench": list(bench),
        "captain": captain,
        "vice_captain": vice,
        "predicted_xi": round(xi, 3),
        "predicted_total": round(xi + players[captain]["score"], 3),
        "predicted": {str(pid): players[pid]["score"] for pid in starters + bench},
        "names": {str(pid): players[pid]["name"] for pid in starters + bench},
        "positions": {str(pid): players[pid]["pos"] for pid in starters + bench},
        "meta": meta or {},
    }


def record_prediction(entry: dict, path: str = PREDICTIONS_PATH) -> dict:
    """Append a prediction. Never rewrites or dedupes - a re-run of the same
    gameweek is itself information, and the reader takes the latest."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")
    return entry


def load_predictions(path: str = PREDICTIONS_PATH) -> list[dict]:
    """All recorded predictions, oldest first. Unparseable lines are skipped
    rather than killing the weekly run."""
    out = []
    try:
        with open(path) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except ValueError:
                    continue
    except OSError:
        return []
    return out


def prediction_for(event: int, path: str = PREDICTIONS_PATH) -> dict | None:
    """The most recent prediction recorded for a gameweek."""
    matches = [p for p in load_predictions(path) if p.get("event") == event]
    return matches[-1] if matches else None


# --- measuring ------------------------------------------------------------

def actual_points(live: dict) -> dict:
    """{player_id: points_scored} from the /event/{gw}/live/ payload."""
    return {e["id"]: (e.get("stats") or {}).get("total_points", 0)
            for e in live.get("elements", [])}


def actual_minutes(live: dict) -> dict:
    return {e["id"]: (e.get("stats") or {}).get("minutes", 0)
            for e in live.get("elements", [])}


def apply_auto_subs(prediction: dict, minutes: dict) -> tuple[list[int], list[tuple[int, int]]]:
    """FPL's auto-substitution: starters who didn't play are replaced from the bench.

    Returns the XI that actually counted, plus the (out, in) swaps. Without this a
    blanked starter is scored as a 0 that the real team never took, making the
    measured total look worse than the manager's actual result.
    """
    positions = {int(k): v for k, v in prediction["positions"].items()}
    starters = list(prediction["starters"])
    bench = [pid for pid in prediction["bench"] if minutes.get(pid, 0) > 0]
    swaps: list[tuple[int, int]] = []

    def counts(xi):
        c = dict.fromkeys(FORMATION_LIMITS, 0)
        for pid in xi:
            c[positions[pid]] += 1
        return c

    for pid in list(starters):
        if minutes.get(pid, 0) > 0:
            continue
        for cand in list(bench):
            trial = [p for p in starters if p != pid] + [cand]
            if positions[pid] == "GK" or positions[cand] == "GK":
                # Keepers only ever swap with the bench keeper.
                if positions[pid] != positions[cand]:
                    continue
            c = counts(trial)
            if all(lo <= c[pos] <= hi for pos, (lo, hi) in FORMATION_LIMITS.items()):
                starters = trial
                bench.remove(cand)
                swaps.append((pid, cand))
                break
    return starters, swaps


def evaluate_gameweek(event: int, live: dict, path: str = PREDICTIONS_PATH) -> dict | None:
    """Compare a recorded prediction against what actually happened.

    Returns None when nothing was recorded for that gameweek, so a first run (or a
    gameweek that was skipped) reports honestly instead of inventing a review.
    """
    pred = prediction_for(event, path)
    if pred is None:
        return None

    points, minutes = actual_points(live), actual_minutes(live)
    xi, swaps = apply_auto_subs(pred, minutes)

    captain = pred["captain"]
    # FPL passes the armband to the vice if the captain doesn't play.
    if minutes.get(captain, 0) == 0 and minutes.get(pred["vice_captain"], 0) > 0:
        captain = pred["vice_captain"]

    actual_xi = sum(points.get(pid, 0) for pid in xi)
    actual_total = actual_xi + points.get(captain, 0)

    per_player = []
    for pid in pred["starters"] + pred["bench"]:
        predicted = pred["predicted"].get(str(pid), 0.0)
        got = points.get(pid, 0)
        per_player.append({
            "id": pid,
            "name": pred["names"].get(str(pid), str(pid)),
            "started": pid in xi,
            "predicted": predicted,
            "actual": got,
            "error": round(got - predicted, 3),
            "minutes": minutes.get(pid, 0),
        })

    started = [p for p in per_player if p["started"]]
    errors = [p["error"] for p in started]
    mae = round(sum(abs(e) for e in errors) / len(errors), 3) if errors else 0.0
    bias = round(sum(errors) / len(errors), 3) if errors else 0.0

    return {
        "event": event,
        "predicted_total": pred["predicted_total"],
        "actual_total": actual_total,
        "error": round(actual_total - pred["predicted_total"], 3),
        "captain": captain,
        "captain_changed": captain != pred["captain"],
        "captain_points": points.get(captain, 0),
        "auto_subs": swaps,
        "mae": mae,
        "bias": bias,  # positive = the model under-predicts
        "per_player": sorted(per_player, key=lambda p: p["error"]),
    }


def calibration(path: str = PREDICTIONS_PATH, evaluations: list[dict] | None = None) -> dict:
    """Season-to-date accuracy across evaluated gameweeks - the number that should
    drive changes to score.py's weights."""
    evals = evaluations or []
    if not evals:
        return {"gameweeks": 0}
    errs = [e["error"] for e in evals]
    return {
        "gameweeks": len(evals),
        "mean_predicted": round(sum(e["predicted_total"] for e in evals) / len(evals), 2),
        "mean_actual": round(sum(e["actual_total"] for e in evals) / len(evals), 2),
        "mean_error": round(sum(errs) / len(errs), 2),
        "mean_abs_error": round(sum(abs(e) for e in errs) / len(errs), 2),
    }
