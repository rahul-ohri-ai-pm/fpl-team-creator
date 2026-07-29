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


def optimal_squad(players: dict, budget: int, current_squad: list[int] | None = None,
                   max_transfers_out: int | None = None) -> list[int]:
    """players: {pid: {"score", "pos", "team", "cost"}}. budget in tenths of a million.

    If current_squad + max_transfers_out are given, constrains the result to
    differ from current_squad by at most that many dropped players - i.e. an
    incremental transfer search rather than a from-scratch draft.
    """
    prob = pulp.LpProblem("fpl_squad", pulp.LpMaximize)
    x = {pid: pulp.LpVariable(f"x_{pid}", cat="Binary") for pid in players}

    prob += pulp.lpSum(players[pid]["score"] * x[pid] for pid in players)

    prob += pulp.lpSum(x.values()) == 15
    for pos, count in POSITION_QUOTAS.items():
        prob += pulp.lpSum(x[pid] for pid in players if players[pid]["pos"] == pos) == count

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

    prob += pulp.lpSum(players[pid]["score"] * x[pid] for pid in squad_ids)
    prob += pulp.lpSum(x.values()) == 11
    for pos, (lo, hi) in FORMATION_LIMITS.items():
        count = pulp.lpSum(x[pid] for pid in squad_ids if players[pid]["pos"] == pos)
        prob += count >= lo
        prob += count <= hi

    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    starters = [pid for pid in squad_ids if x[pid].value() == 1]
    bench = [pid for pid in squad_ids if pid not in starters]
    ranked = sorted(starters, key=lambda pid: players[pid]["score"], reverse=True)
    return {
        "starters": starters,
        "bench": bench,
        "captain": ranked[0],
        "vice_captain": ranked[1],
    }


def recommend_transfers(players: dict, current_squad: list[int], bank: int,
                         free_transfers: int, max_search: int = 2) -> dict:
    """Tries 0..max_search transfers, picks the option with the best
    hit-adjusted predicted score (a -4pt penalty per transfer beyond the
    number of free transfers available)."""
    current_value = sum(players[pid]["cost"] for pid in current_squad if pid in players)
    budget = current_value + bank

    best = None
    for k in range(0, max_search + 1):
        squad = optimal_squad(players, budget, current_squad=current_squad, max_transfers_out=k)
        raw_score = sum(players[pid]["score"] for pid in squad)
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
