"""MILP squad optimization (pulp/CBC): full-squad build and incremental transfers.

Position quotas and club limits are the actual FPL rules, not heuristics -
the "best team possible" the optimizer returns is only as good as the
predicted `score` fed in from score.py.
"""
from __future__ import annotations

import pulp

POSITION_QUOTAS = {"GK": 2, "DEF": 5, "MID": 5, "FWD": 3}
FORMATION_LIMITS = {  # (min, max) starters per position, out of 11
    "GK": (1, 1), "DEF": (3, 5), "MID": (2, 5), "FWD": (1, 3),
}

# Only the starting XI scores in a normal gameweek, so the objective can't just
# sum all 15 - that spends real budget on bench players who bank nothing, and
# lets a bench upgrade look like it justifies a -4 hit. But a bench weight of 0
# swings the other way and buys four £4.0m players who never take the pitch,
# which loses points whenever an auto-sub fires. A bench player pays out only
# via auto-subs (a starter not playing) or Bench Boost, so weight it well below
# a starter but above nothing.
BENCH_WEIGHT = 0.15

# Strength of the risk-profile ownership preference from score.py. Player scores
# span roughly 0-8 predicted points and `tiebreak` spans -1..1, so at this size it
# can only decide between players within 0.02 points of each other - a genuine
# tiebreak. It is excluded from every reported total: `score` is predicted points,
# and the headline number has to stay comparable to what the squad actually scores.
OWNERSHIP_TIEBREAK_EPSILON = 0.02


def _objective_value(pid: int, players: dict) -> float:
    """Selection value: predicted points, nudged by the ownership tiebreak."""
    p = players[pid]
    return p["score"] + OWNERSHIP_TIEBREAK_EPSILON * p.get("tiebreak", 0.0)


def squad_score(squad_ids: list[int], players: dict, bench_weight: float = BENCH_WEIGHT) -> float:
    """Predicted points for a 15-man squad: full credit for the best legal XI,
    `bench_weight` credit for the rest. Same quantity `optimal_squad` maximizes,
    so transfer options can be compared against the -4 hit cost in real points."""
    lineup = best_lineup(squad_ids, players)
    starters = sum(players[pid]["score"] for pid in lineup["starters"])
    bench = sum(players[pid]["score"] for pid in lineup["bench"])
    return starters + bench_weight * bench


def optimal_squad(players: dict, budget: int, current_squad: list[int] | None = None,
                   max_transfers_out: int | None = None,
                   bench_weight: float = BENCH_WEIGHT) -> list[int]:
    """players: {pid: {"score", "pos", "team", "cost"}}. budget in tenths of a million.

    Maximizes the starting XI's predicted points plus `bench_weight` times the
    bench's, so squad selection and formation are solved together - picking the
    15 without knowing which 11 start would misprice every bench slot.

    If current_squad + max_transfers_out are given, constrains the result to
    differ from current_squad by at most that many dropped players - i.e. an
    incremental transfer search rather than a from-scratch draft.
    """
    prob = pulp.LpProblem("fpl_squad", pulp.LpMaximize)
    x = {pid: pulp.LpVariable(f"x_{pid}", cat="Binary") for pid in players}
    s = {pid: pulp.LpVariable(f"s_{pid}", cat="Binary") for pid in players}

    prob += pulp.lpSum(
        _objective_value(pid, players) * (bench_weight * x[pid] + (1 - bench_weight) * s[pid])
        for pid in players
    )

    prob += pulp.lpSum(x.values()) == 15
    prob += pulp.lpSum(s.values()) == 11
    for pid in players:
        prob += s[pid] <= x[pid]  # can only start someone who's in the squad

    for pos, count in POSITION_QUOTAS.items():
        prob += pulp.lpSum(x[pid] for pid in players if players[pid]["pos"] == pos) == count
    for pos, (lo, hi) in FORMATION_LIMITS.items():
        starting = pulp.lpSum(s[pid] for pid in players if players[pid]["pos"] == pos)
        prob += starting >= lo
        prob += starting <= hi

    teams = {players[pid]["team"] for pid in players}
    for team in teams:
        prob += pulp.lpSum(x[pid] for pid in players if players[pid]["team"] == team) <= 3

    prob += pulp.lpSum(players[pid]["cost"] * x[pid] for pid in players) <= budget

    if current_squad and max_transfers_out is not None:
        in_pool = [pid for pid in current_squad if pid in players]
        prob += pulp.lpSum(1 - x[pid] for pid in in_pool) <= max_transfers_out

    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    if pulp.LpStatus[prob.status] != "Optimal":
        raise RuntimeError(f"Optimizer did not find a feasible squad: {pulp.LpStatus[prob.status]}")

    return [pid for pid in players if x[pid].value() == 1]


def best_lineup(squad_ids: list[int], players: dict) -> dict:
    """Best valid starting XI + captain/vice from a 15-man squad."""
    prob = pulp.LpProblem("fpl_lineup", pulp.LpMaximize)
    x = {pid: pulp.LpVariable(f"s_{pid}", cat="Binary") for pid in squad_ids}

    prob += pulp.lpSum(_objective_value(pid, players) * x[pid] for pid in squad_ids)
    prob += pulp.lpSum(x.values()) == 11
    for pos, (lo, hi) in FORMATION_LIMITS.items():
        count = pulp.lpSum(x[pid] for pid in squad_ids if players[pid]["pos"] == pos)
        prob += count >= lo
        prob += count <= hi

    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    starters = [pid for pid in squad_ids if x[pid].value() == 1]
    bench = [pid for pid in squad_ids if pid not in starters]
    ranked = sorted(starters, key=lambda pid: _objective_value(pid, players), reverse=True)
    return {
        "starters": starters,
        "bench": bench,
        "captain": ranked[0],
        "vice_captain": ranked[1],
    }


def recommend_transfers(players: dict, current_squad: list[int], bank: int,
                         free_transfers: int, max_search: int = 2,
                         bench_weight: float = BENCH_WEIGHT) -> dict:
    """Tries 0..max_search transfers, picks the option with the best
    hit-adjusted predicted score (a -4pt penalty per transfer beyond the
    number of free transfers available)."""
    current_value = sum(players[pid]["cost"] for pid in current_squad if pid in players)
    budget = current_value + bank

    best = None
    for k in range(0, max_search + 1):
        squad = optimal_squad(players, budget, current_squad=current_squad,
                              max_transfers_out=k, bench_weight=bench_weight)
        raw_score = squad_score(squad, players, bench_weight)
        hit_cost = max(0, k - free_transfers) * 4
        net = raw_score - hit_cost
        if best is None or net > best["net_score"]:
            transfers_out = [pid for pid in current_squad if pid in players and pid not in squad]
            transfers_in = [pid for pid in squad if pid not in current_squad]
            best = {
                "transfers": k, "hit_cost": hit_cost, "net_score": net,
                "squad": squad, "out": transfers_out, "in": transfers_in,
            }
    return best
