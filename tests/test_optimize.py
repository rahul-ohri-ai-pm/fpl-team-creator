"""Squad optimizer (engine.optimize).

Synthetic player pools only - these must run without network access. The pools
are built so the "right" answer is obvious by construction, which is what makes
a wrong objective visible.
"""
import pytest

from engine.optimize import (
    BENCH_WEIGHT,
    POSITION_QUOTAS,
    best_lineup,
    optimal_squad,
    recommend_transfers,
    squad_score,
)


def make_pool(n_per_pos=8, n_clubs=10):
    """A pool where score rises with cost, so budget allocation actually matters."""
    players, pid = {}, 1
    for pos in ("GK", "DEF", "MID", "FWD"):
        for i in range(n_per_pos):
            players[pid] = {
                "score": 1.0 + i * 0.5,
                "pos": pos,
                "team": pid % n_clubs,
                "cost": 40 + i * 5,
                "name": f"{pos}{i}",
            }
            pid += 1
    return players


def squad_positions(squad, players):
    counts = dict.fromkeys(POSITION_QUOTAS, 0)
    for pid in squad:
        counts[players[pid]["pos"]] += 1
    return counts


def test_squad_respects_position_quotas_and_size():
    players = make_pool()
    squad = optimal_squad(players, budget=1000)
    assert len(squad) == 15
    assert squad_positions(squad, players) == POSITION_QUOTAS


def test_squad_respects_budget():
    players = make_pool()
    budget = 850
    squad = optimal_squad(players, budget)
    assert sum(players[pid]["cost"] for pid in squad) <= budget


def test_squad_respects_three_per_club_limit():
    players = make_pool(n_per_pos=10, n_clubs=6)
    squad = optimal_squad(players, budget=1000)
    counts = {}
    for pid in squad:
        counts[players[pid]["team"]] = counts.get(players[pid]["team"], 0) + 1
    assert max(counts.values()) <= 3


def test_infeasible_squad_raises():
    players = make_pool()
    with pytest.raises(RuntimeError):
        optimal_squad(players, budget=100)  # nowhere near enough for 15 players


# --- the objective itself -------------------------------------------------
# Only the XI banks points in a normal gameweek. Summing all 15 equally (the
# old objective, == bench_weight 1.0) spends budget on players who never play.

def test_lower_bench_weight_buys_a_stronger_starting_xi():
    players = make_pool()

    def xi_score(bench_weight):
        squad = optimal_squad(players, budget=800, bench_weight=bench_weight)
        lineup = best_lineup(squad, players)
        return sum(players[pid]["score"] for pid in lineup["starters"])

    assert xi_score(0.15) > xi_score(1.0)


def test_bench_weight_zero_leaves_a_cheaper_bench_than_full_weight():
    players = make_pool()

    def bench_cost(bench_weight):
        squad = optimal_squad(players, budget=800, bench_weight=bench_weight)
        lineup = best_lineup(squad, players)
        return sum(players[pid]["cost"] for pid in lineup["bench"])

    assert bench_cost(0.0) < bench_cost(1.0)


def test_squad_score_credits_bench_at_the_bench_weight():
    players = make_pool()
    squad = optimal_squad(players, budget=800)
    lineup = best_lineup(squad, players)
    starters = sum(players[pid]["score"] for pid in lineup["starters"])
    bench = sum(players[pid]["score"] for pid in lineup["bench"])
    assert squad_score(squad, players) == pytest.approx(starters + BENCH_WEIGHT * bench)


def test_squad_score_at_full_bench_weight_is_the_plain_15_man_sum():
    players = make_pool()
    squad = optimal_squad(players, budget=800)
    total = sum(players[pid]["score"] for pid in squad)
    assert squad_score(squad, players, bench_weight=1.0) == pytest.approx(total)


# --- lineup ---------------------------------------------------------------

def test_best_lineup_is_a_legal_formation():
    players = make_pool()
    squad = optimal_squad(players, budget=1000)
    lineup = best_lineup(squad, players)
    assert len(lineup["starters"]) == 11
    assert len(lineup["bench"]) == 4
    counts = squad_positions(lineup["starters"], players)
    assert counts["GK"] == 1
    assert 3 <= counts["DEF"] <= 5
    assert 2 <= counts["MID"] <= 5
    assert 1 <= counts["FWD"] <= 3


def test_captain_and_vice_are_the_two_best_starters():
    players = make_pool()
    squad = optimal_squad(players, budget=1000)
    lineup = best_lineup(squad, players)
    ranked = sorted(lineup["starters"], key=lambda pid: players[pid]["score"], reverse=True)
    assert lineup["captain"] == ranked[0]
    assert lineup["vice_captain"] == ranked[1]
    assert lineup["captain"] != lineup["vice_captain"]


# --- transfers ------------------------------------------------------------

def test_holds_when_the_current_squad_is_already_optimal():
    players = make_pool()
    squad = optimal_squad(players, budget=800)
    rec = recommend_transfers(players, squad, bank=0, free_transfers=1)
    assert rec["transfers"] == 0
    assert rec["in"] == [] and rec["out"] == []


def test_free_transfer_is_used_when_it_improves_the_xi():
    players = make_pool()
    squad = optimal_squad(players, budget=800)

    # Downgrade the squad by one player: swap a starter for a strictly worse,
    # strictly cheaper player of the same position from outside it. The freed
    # cash goes to the bank, so undoing the swap is affordable and free.
    lineup = best_lineup(squad, players)
    swap = next(
        (pid, other)
        for pid in sorted(lineup["starters"], key=lambda i: -players[i]["score"])
        for other, p in sorted(players.items(), key=lambda kv: kv[1]["score"])
        if other not in squad
        and p["pos"] == players[pid]["pos"]
        and p["score"] < players[pid]["score"]
        and p["cost"] < players[pid]["cost"]
    )
    dropped, replacement = swap
    downgraded = [pid for pid in squad if pid != dropped] + [replacement]
    bank = players[dropped]["cost"] - players[replacement]["cost"]

    rec = recommend_transfers(players, downgraded, bank=bank, free_transfers=1)
    assert rec["transfers"] == 1
    assert rec["hit_cost"] == 0
    assert rec["out"] == [replacement]


def test_hit_is_declined_when_the_gain_is_smaller_than_four_points():
    # One clearly-worse starter, upgradeable by only ~1 point. Not worth -4.
    players = make_pool()
    squad = optimal_squad(players, budget=800)
    rec = recommend_transfers(players, squad, bank=0, free_transfers=0)
    assert rec["transfers"] == 0
    assert rec["hit_cost"] == 0


def test_hit_is_taken_when_the_gain_clearly_beats_the_four_point_cost():
    players = make_pool()
    squad = optimal_squad(players, budget=800)
    lineup = best_lineup(squad, players)
    weakest = min(lineup["starters"], key=lambda pid: players[pid]["score"])

    # A free superstar of the same position, sitting outside the squad: worth
    # far more than the 4-point hit even with no free transfers.
    star = max(players) + 1
    players[star] = {
        "score": players[weakest]["score"] + 40,
        "pos": players[weakest]["pos"],
        "team": 999,
        "cost": players[weakest]["cost"],
        "name": "star",
    }
    rec = recommend_transfers(players, squad, bank=0, free_transfers=0)
    assert star in rec["in"]
    assert rec["transfers"] == 1
    assert rec["hit_cost"] == 4


def test_hit_cost_is_charged_only_beyond_the_free_transfers_available():
    players = make_pool()
    squad = optimal_squad(players, budget=800)
    weakest_two = sorted(squad, key=lambda pid: players[pid]["score"])[:2]
    stars = []
    for n, out in enumerate(weakest_two):
        star = max(players) + 1
        players[star] = {
            "score": players[out]["score"] + 40,
            "pos": players[out]["pos"],
            "team": 900 + n,
            "cost": players[out]["cost"],
            "name": f"star{n}",
        }
        stars.append(star)

    rec = recommend_transfers(players, squad, bank=0, free_transfers=1)
    assert rec["transfers"] == 2
    assert rec["hit_cost"] == 4  # 2 transfers, 1 free -> a single -4
