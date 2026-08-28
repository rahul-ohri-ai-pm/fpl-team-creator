"""Parametrized weight-scheme backtesting against confirmed-finished gameweeks.

Generalizes engine/score.py's formula into a configurable "scheme" so any
combination of factor weights - the 4 named schemes documented in
.claude/docs/SCORING.md, or an arbitrary custom one - can be scored against
real gameweek results. This is the weight simulator: it never writes to
engine/score.py itself (see /score-calibrate for how a scheme becomes live).

Usage:
    python engine/backtest.py --gw 1 --scheme conservative
    python engine/backtest.py --gw 1 --custom '{"form_mult": 0.95, ...}'
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import requests

from engine.optimize import best_lineup

BASE = "https://fantasy.premierleague.com/api"
SNAPSHOT_DIR = os.path.join(os.path.dirname(__file__), "..", "records", "snapshots")

POSITION_BY_TYPE = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}
GAMES_REFERENCE = 38  # pre-season/early-season reference, matches engine/score.py

# The 3 real, previously-recorded test squads from records/scoring_backtest.md's
# GW1 backtest (Team A: actual GW1 squad, Team B: pre-season re-run draft,
# Team C: original pre-season draft) - by player id, resolved from bootstrap.
TEST_SQUADS = {
    "Team A": [1, 498, 4, 356, 427, 480, 236, 155, 106, 346, 165, 529, 533, 229, 335],
    "Team B": [1, 497, 4, 388, 533, 201, 204, 426, 397, 368, 452, 260, 165, 346, 527],
    "Team C": [529, 82, 4, 388, 533, 201, 112, 426, 368, 452, 260, 335, 165, 106, 346],
}

# The 4 named weight schemes - values as documented in .claude/docs/SCORING.md.
SCHEMES = {
    "baseline": {
        "form_mult": 1.0, "ease_min": 0.8, "ease_max": 1.2,
        "reliability_divisor_factor": 0.6, "injury_penalty_flat": 0.0,
        "ownership_weight": {"safe": 1.5, "balanced": 0.3, "differential": -1.5},
        "new_signing_downweight_factor": 1.0, "new_signing_minutes_threshold": 0,
    },
    "conservative": {
        "form_mult": 0.9, "ease_min": 0.8, "ease_max": 1.15,
        "reliability_divisor_factor": 0.5, "injury_penalty_flat": -0.1,
        "ownership_weight": {"safe": 2.0, "balanced": 0.5, "differential": -1.0},
        "new_signing_downweight_factor": 1.0, "new_signing_minutes_threshold": 0,
    },
    "aggressive": {
        "form_mult": 1.1, "ease_min": 0.75, "ease_max": 1.25,
        "reliability_divisor_factor": 0.75, "injury_penalty_flat": 0.0,
        "ownership_weight": {"safe": 1.0, "balanced": 0.0, "differential": -2.0},
        "new_signing_downweight_factor": 1.0, "new_signing_minutes_threshold": 0,
    },
    "new_signing_aware": {
        "form_mult": 1.0, "ease_min": 0.8, "ease_max": 1.2,
        "reliability_divisor_factor": 0.6, "injury_penalty_flat": 0.0,
        "ownership_weight": {"safe": 1.5, "balanced": 0.3, "differential": -1.5},
        "new_signing_downweight_factor": 0.85, "new_signing_minutes_threshold": 270,
    },
}

REQUIRED_SCHEME_KEYS = {
    "form_mult", "ease_min", "ease_max", "reliability_divisor_factor",
    "injury_penalty_flat", "ownership_weight", "new_signing_downweight_factor",
    "new_signing_minutes_threshold",
}


def check_gameweek_finished(gw: int) -> None:
    """Verification-loop guard: refuse to backtest a gameweek that hasn't
    actually finished, even if its deadline has passed."""
    r = requests.get(f"{BASE}/bootstrap-static/", timeout=15)
    r.raise_for_status()
    bootstrap = r.json()
    event = next((e for e in bootstrap["events"] if e["id"] == gw), None)
    if event is None:
        raise ValueError(f"No such gameweek: {gw}")
    if not event.get("finished"):
        raise ValueError(
            f"GW{gw} is not finished yet (finished={event.get('finished')}, "
            f"data_checked={event.get('data_checked')}) - a passed deadline does not mean "
            f"the gameweek is over. Refusing to backtest provisional data."
        )


def _snapshot_path(gw: int) -> str:
    return os.path.join(SNAPSHOT_DIR, f"gw{gw}_preseason_reconstruction.json")


def _fetch_prior_season_ppg_minutes(player_id: int, season_name: str) -> tuple[float, int]:
    r = requests.get(f"{BASE}/element-summary/{player_id}/", timeout=15)
    r.raise_for_status()
    history = r.json().get("history_past", [])
    season = next((h for h in history if h["season_name"] == season_name), None)
    if season is None:
        return 0.0, 0
    return season["total_points"] / 38.0, season["minutes"]


def build_snapshot(gw: int, player_ids: list[int], prior_season: str = "2025/26") -> dict:
    """Reconstructs the pre-gameweek inputs each scheme would have used:
    prior-season ppg/minutes (this season's form/minutes reset each GW and
    can't be un-reset retroactively), plus today's fixture-ease/ownership/
    chance-of-playing as a proxy for their pre-gameweek values. See the
    caveat in records/scoring_backtest.md - this is a close approximation,
    not a literal snapshot, unless one was saved before the deadline."""
    from engine.score import fixture_ease

    bootstrap_r = requests.get(f"{BASE}/bootstrap-static/", timeout=15)
    bootstrap_r.raise_for_status()
    bootstrap = bootstrap_r.json()
    fixtures_r = requests.get(f"{BASE}/fixtures/", timeout=15)
    fixtures_r.raise_for_status()
    fixtures = fixtures_r.json()

    elements_by_id = {e["id"]: e for e in bootstrap["elements"]}
    team_ease = {t["id"]: fixture_ease(t["id"], fixtures, gw) for t in bootstrap["teams"]}

    players = {}
    for pid in player_ids:
        e = elements_by_id[pid]
        ppg, minutes = _fetch_prior_season_ppg_minutes(pid, prior_season)
        players[str(pid)] = {
            "name": f"{e['first_name']} {e['second_name']}",
            "pos": POSITION_BY_TYPE[e["element_type"]],
            "team": e["team"],
            "cost": e["now_cost"],
            "ppg": ppg,
            "minutes": minutes,
            "ease_base": team_ease.get(e["team"], 0.5),
            "chance": e["chance_of_playing_next_round"],
            "ownership": float(e["selected_by_percent"] or 0),
        }

    live_r = requests.get(f"{BASE}/event/{gw}/live/", timeout=15)
    live_r.raise_for_status()
    live = live_r.json()
    actual_points = {
        str(el["id"]): el["stats"]["total_points"]
        for el in live["elements"] if el["id"] in player_ids
    }

    return {"gw": gw, "prior_season": prior_season, "players": players, "actual_points": actual_points}


def load_or_build_snapshot(gw: int, player_ids: list[int]) -> dict:
    path = _snapshot_path(gw)
    if os.path.exists(path):
        with open(path) as f:
            snapshot = json.load(f)
        missing = [pid for pid in player_ids if str(pid) not in snapshot["players"]]
        if not missing:
            return snapshot
    snapshot = build_snapshot(gw, player_ids)
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    with open(path, "w") as f:
        json.dump(snapshot, f, indent=2)
    return snapshot


def score_with_scheme(player: dict, scheme: dict, risk_profile: str = "safe") -> float:
    """player: one entry from a snapshot's "players" dict."""
    form = player["ppg"] * scheme["form_mult"]
    ease_mult = scheme["ease_min"] + player["ease_base"] * (scheme["ease_max"] - scheme["ease_min"])
    reliability = min(1.0, player["minutes"] / (GAMES_REFERENCE * 90 * scheme["reliability_divisor_factor"]))
    chance = player["chance"]
    injury_mult = max(0.0, (chance if chance is not None else 100) / 100 + scheme["injury_penalty_flat"])

    predicted = form * ease_mult * reliability * injury_mult
    if player["minutes"] < scheme["new_signing_minutes_threshold"]:
        predicted *= scheme["new_signing_downweight_factor"]

    ownership_weight = scheme["ownership_weight"].get(
        risk_profile, scheme["ownership_weight"].get("balanced", 0.0)
    )
    predicted += (player["ownership"] / 100) * ownership_weight
    return predicted


def _baseline_players_for_lineup(snapshot: dict, squad_ids: list[int]) -> dict:
    """Players dict shaped for engine.optimize.best_lineup, scored under Baseline -
    kept constant across schemes so squad-selection doesn't confound scoring accuracy."""
    out = {}
    for pid in squad_ids:
        p = snapshot["players"][str(pid)]
        out[pid] = {
            "score": score_with_scheme(p, SCHEMES["baseline"]),
            "pos": p["pos"], "team": p["team"], "cost": p["cost"],
        }
    return out


def backtest(scheme: dict, gw: int = 1, risk_profile: str = "safe",
             squads: dict[str, list[int]] | None = None) -> dict:
    """Runs `scheme` against `squads` (default TEST_SQUADS) for gameweek `gw`.
    Returns per-squad predicted/actual XI totals plus aggregate RMSE/MAE/bias."""
    check_gameweek_finished(gw)
    squads = squads or TEST_SQUADS
    all_ids = sorted({pid for ids in squads.values() for pid in ids})
    snapshot = load_or_build_snapshot(gw, all_ids)

    per_squad = {}
    errors = []
    for name, squad_ids in squads.items():
        baseline_players = _baseline_players_for_lineup(snapshot, squad_ids)
        lineup = best_lineup(squad_ids, baseline_players)
        starters = lineup["starters"]

        predicted = sum(score_with_scheme(snapshot["players"][str(pid)], scheme, risk_profile)
                         for pid in starters)
        actual = sum(snapshot["actual_points"].get(str(pid), 0) for pid in starters)
        per_squad[name] = {"predicted": round(predicted, 2), "actual": actual,
                            "diff": round(predicted - actual, 2)}
        errors.append(predicted - actual)

    n = len(errors)
    rmse = (sum(e ** 2 for e in errors) / n) ** 0.5
    mae = sum(abs(e) for e in errors) / n
    bias = sum(errors) / n
    return {"per_squad": per_squad, "rmse": round(rmse, 2), "mae": round(mae, 2), "bias": round(bias, 2)}


def _validate_custom_scheme(scheme: dict) -> dict:
    missing = REQUIRED_SCHEME_KEYS - scheme.keys()
    if missing:
        raise ValueError(f"Custom scheme missing required keys: {sorted(missing)}")
    if not isinstance(scheme["ownership_weight"], dict):
        raise ValueError('"ownership_weight" must be a dict, e.g. {"safe": 1.5, "balanced": 0.3, "differential": -1.5}')
    return scheme


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gw", type=int, required=True, help="Gameweek to backtest (must be finished)")
    parser.add_argument("--scheme", choices=sorted(SCHEMES), help="Named weight scheme")
    parser.add_argument("--custom", help="JSON weight scheme, overrides --scheme (the simulator)")
    parser.add_argument("--risk-profile", default="safe", choices=["safe", "balanced", "differential"])
    args = parser.parse_args()

    if args.custom:
        scheme = _validate_custom_scheme(json.loads(args.custom))
        label = "custom"
    elif args.scheme:
        scheme = SCHEMES[args.scheme]
        label = args.scheme
    else:
        parser.error("must pass --scheme or --custom")

    try:
        result = backtest(scheme, gw=args.gw, risk_profile=args.risk_profile)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"scheme: {label}")
    print(json.dumps(scheme, indent=2))
    print()
    for squad_name, r in result["per_squad"].items():
        print(f"{squad_name}: predicted={r['predicted']} actual={r['actual']} diff={r['diff']}")
    print()
    print(f"RMSE={result['rmse']} MAE={result['mae']} bias={result['bias']}")


if __name__ == "__main__":
    main()
