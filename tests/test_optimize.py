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
    loyalty_cost,
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


# --- fixture weighting ----------------------------------------------------

def fx(diffs):
    return [{"event": i + 1, "team_h": 1, "team_a": 2,
             "team_h_difficulty": d, "team_a_difficulty": 3}
            for i, d in enumerate(diffs)]


def test_when_the_hard_game_falls_changes_the_ease():
    """Same four fixtures, reordered. A flat mean can't tell these apart; the
    decay must, because only one of them is a hard game *this* week."""
    from engine.score import fixture_ease

    hard_now = fixture_ease(1, fx([5, 3, 3, 1]), 1)
    hard_later = fixture_ease(1, fx([1, 3, 3, 5]), 1)
    assert hard_later > hard_now

    flat_now = fixture_ease(1, fx([5, 3, 3, 1]), 1, decay=1.0)
    flat_later = fixture_ease(1, fx([1, 3, 3, 5]), 1, decay=1.0)
    assert flat_now == pytest.approx(flat_later), "the old flat mean was blind to this"


def test_next_fixture_outweighs_the_remaining_three_combined():
    from engine.score import fixture_ease
    # One easy game now against three hard ones later should still read as easier
    # than the reverse, or "next gameweek's points" isn't what's being scored.
    assert fixture_ease(1, fx([1, 5, 5, 5]), 1) > fixture_ease(1, fx([5, 1, 1, 1]), 1)


def test_a_hard_opener_scores_worse_than_the_flat_mean_would_suggest():
    from engine.score import fixture_ease
    diffs = [5, 1, 1, 1]
    assert fixture_ease(1, fx(diffs), 1) < fixture_ease(1, fx(diffs), 1, decay=1.0)


def test_fixture_ease_still_bounded_and_defaults_when_no_fixtures():
    from engine.score import fixture_ease
    assert fixture_ease(1, [], 1) == 0.5
    fx = [{"event": 1, "team_h": 1, "team_a": 2,
           "team_h_difficulty": 5, "team_a_difficulty": 1}]
    assert 0.0 <= fixture_ease(1, fx, 1) <= 1.0


# --- favourite-club floor -------------------------------------------------
# Wanting your own players in the squad is a preference, not a prediction, so it
# lives here as a constraint rather than in score.py. What these lock down is that
# it obeys FPL's rules, and that its price in predicted points is reported honestly.

def make_loyalty_pool():
    """Every club fields a full set, but club 1's players are the worst in the
    pool - so an unconstrained optimizer picks none of them and any floor has a
    measurable, strictly positive cost."""
    players, pid = {}, 1
    for club in range(1, 8):
        for pos in ("GK", "DEF", "MID", "FWD"):
            for i in range(3):
                players[pid] = {
                    "score": (1.0 if club == 1 else 5.0) + i * 0.1,
                    "pos": pos,
                    "team": club,
                    "cost": 45,
                    "name": f"c{club}{pos}{i}",
                }
                pid += 1
    return players


def test_club_floor_puts_the_required_number_in_the_squad():
    players = make_loyalty_pool()
    squad = optimal_squad(players, budget=1000, min_from_team=(1, 3))
    assert sum(1 for pid in squad if players[pid]["team"] == 1) == 3


def test_without_the_floor_the_weak_club_is_not_picked_at_all():
    players = make_loyalty_pool()
    squad = optimal_squad(players, budget=1000)
    assert not [pid for pid in squad if players[pid]["team"] == 1]


def test_club_floor_never_breaches_the_three_per_club_limit():
    players = make_loyalty_pool()
    with pytest.raises(ValueError):
        optimal_squad(players, budget=1000, min_from_team=(1, 4))


def test_club_floor_still_respects_quotas_and_budget():
    players = make_loyalty_pool()
    squad = optimal_squad(players, budget=1000, min_from_team=(1, 3))
    assert squad_positions(squad, players) == POSITION_QUOTAS
    assert sum(players[pid]["cost"] for pid in squad) <= 1000


def test_loyalty_cost_rises_with_each_extra_forced_player():
    players = make_loyalty_pool()
    report = loyalty_cost(players, budget=1000, team_id=1)
    costs = [report["levels"][n]["cost"] for n in (1, 2, 3)]
    assert costs[0] > 0, "forcing a strictly worse player must cost something"
    assert costs[0] < costs[1] < costs[2]


def test_loyalty_cost_is_zero_when_the_club_is_wanted_anyway():
    """A floor the optimizer would have satisfied on merit is free. Reporting a
    cost here would talk the user out of a preference that costs nothing."""
    players = make_loyalty_pool()
    for pid, p in players.items():
        if p["team"] == 1:
            p["score"] = 9.0  # now the best club in the pool
    report = loyalty_cost(players, budget=1000, team_id=1)
    assert report["levels"][3]["cost"] == pytest.approx(0.0)


def test_loyalty_cost_reports_infeasible_levels_without_losing_the_others():
    players = make_loyalty_pool()
    # Club 1 fields a single (expensive) player, so a floor of 2 cannot be met.
    players = {pid: p for pid, p in players.items()
               if p["team"] != 1 or p["name"] == "c1MID0"}
    report = loyalty_cost(players, budget=1000, team_id=1)
    assert report["levels"][1]["feasible"] is True
    assert report["levels"][2]["feasible"] is False
    assert "reason" in report["levels"][2]


def test_loyalty_report_scores_are_comparable_to_squad_score():
    players = make_loyalty_pool()
    report = loyalty_cost(players, budget=1000, team_id=1)
    forced = report["levels"][3]
    assert forced["score"] == pytest.approx(squad_score(forced["squad"], players), abs=1e-3)


def test_transfer_search_honours_the_club_floor():
    players = make_loyalty_pool()
    squad = optimal_squad(players, budget=1000)  # holds none of club 1
    rec = recommend_transfers(players, squad, bank=0, free_transfers=5,
                              min_from_team=(1, 2))
    assert sum(1 for pid in rec["squad"] if players[pid]["team"] == 1) >= 2


def test_transfer_search_errors_when_no_number_of_transfers_can_satisfy_the_floor():
    players = make_loyalty_pool()
    squad = optimal_squad(players, budget=1000)
    with pytest.raises(RuntimeError):
        recommend_transfers(players, squad, bank=0, free_transfers=5,
                            min_from_team=(1, 3), max_search=2)
