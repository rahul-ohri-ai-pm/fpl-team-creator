"""Multi-gameweek transfer planner and chip calendar.

`optimize.recommend_transfers` answers "what is the best squad for next week, within
k transfers". That is the wrong question for a squad with one free transfer a week:
it will spend this week's transfer on a 0.3-point gain and leave an injured player
sitting for three more weeks, or take a -4 that a free transfer next week would have
covered. This module plans the transfers for the next N gameweeks *together* in one
MILP, with free-transfer rollover and hits modelled, so the order of moves is chosen
by the solver rather than week by week.

`chip_calendar` then prices each remaining chip in each planned week against the
payoff a chip typically returns in a double gameweek, and lists the blank/double
gameweeks actually on the schedule.

Nothing here is ever recorded to `records/predictions.jsonl`: later-week scores are
planning estimates, not the calibrated next-gameweek `score`.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import re
from collections import Counter

import pulp

from engine.optimize import (
    BENCH_WEIGHT, CLUB_LIMIT, FORMATION_LIMITS, POSITION_QUOTAS, optimal_squad,
)
from engine.score import _normalized_strengths, gameweek_ease, score_players

HIT_COST = 4
# Extra margin a hit must clear inside the solver (reported totals still use the real
# -4). The model misses by ~12 points a week, so a hit that only just beats 4 over a
# horizon is noise; the margin keeps the plan in line with config/settings.md's rule
# that a hit has to clearly pay for itself.
HIT_MARGIN = 2.0
MAX_FREE_TRANSFERS = 5
# Later weeks are less certain (injuries, rotation, form all drift), so they count
# for less. Hits are *not* discounted - a -4 is certain, the gain it buys isn't.
WEEK_DECAY = 0.9
# Candidates per position (on top of the current squad). Keeps the MILP small; a
# player outside the top 40 at his position over the horizon is never a buy.
POOL_PER_POSITION = 40

# What a chip has to beat to be worth using in a normal week: roughly what each one
# returns in a double gameweek (a DGW bench of 4 doubling players, a doubling premium
# captain, a Free Hit over a big blank). Below this, holding it is the better bet.
CHIP_THRESHOLDS = {"bboost": 15.0, "3xc": 10.0, "freehit": 15.0}
CHIP_NAMES = {"wildcard": "Wildcard", "freehit": "Free Hit",
              "bboost": "Bench Boost", "3xc": "Triple Captain"}
SECOND_HALF_START = 20  # wildcard #2 (CLAUDE.md: x2/season) opens at GW20

_RETURN_RE = re.compile(r"[Ee]xpected back (\d{1,2}) ([A-Z][a-z]{2})")


# --- per-gameweek scores --------------------------------------------------

def return_date(news: str, today: _dt.date) -> _dt.date | None:
    """Parse FPL's 'Expected back 1 Nov' into a date (the year is never given)."""
    m = _RETURN_RE.search(news or "")
    if not m:
        return None
    try:
        d = _dt.datetime.strptime(f"{m.group(1)} {m.group(2)} {today.year}", "%d %b %Y").date()
    except ValueError:
        return None
    # 'Expected back 5 Jan' read in December is next year.
    return d.replace(year=d.year + 1) if d < today - _dt.timedelta(days=60) else d


def gameweek_scores(bootstrap, fixtures, next_event: int, horizon: int = 5,
                    risk_profile: str = "safe", today: _dt.date | None = None) -> tuple[dict, dict]:
    """({gw: {pid: predicted points}}, {pid: player meta}) for the next `horizon` weeks.

    Week one is `score_players`' own `score` - the calibrated number. Later weeks
    re-apply that week's fixtures to `base`, the same way `horizon_scores` does, so
    a blank scores 0 and a double scores twice. A flagged player whose news gives a
    return date scores on `base_fit` from the first gameweek after it.
    """
    today = today or _dt.date.today()
    players = score_players(bootstrap, fixtures, next_event, risk_profile)
    strengths = _normalized_strengths(bootstrap["teams"])
    deadlines = {e["id"]: _dt.date.fromisoformat(e["deadline_time"][:10])
                 for e in bootstrap["events"] if e.get("deadline_time")}
    back = {}
    for el in bootstrap["elements"]:
        chance = el.get("chance_of_playing_next_round")
        if el["id"] in players and chance is not None and chance < 100:
            d = return_date(el.get("news", ""), today)
            if d:
                back[el["id"]] = d

    ease: dict = {}
    scores = {next_event: {pid: p["score"] for pid, p in players.items()}}
    for gw in range(next_event + 1, next_event + horizon):
        week = {}
        for pid, p in players.items():
            key = (p["team"], p["pos"])
            if (key, gw) not in ease:
                ease[(key, gw)] = gameweek_ease(p["pos"], p["team"], fixtures, gw, strengths)
            fit = pid in back and gw in deadlines and deadlines[gw] >= back[pid]
            base = p.get("base_fit", p["base"]) if fit else p["base"]
            week[pid] = round(sum(base * (0.8 + e * 0.4) for e in ease[(key, gw)]), 3)
        scores[gw] = week
    return scores, players


# --- the plan -------------------------------------------------------------

def _pool(scores: dict, players: dict, current_squad: list[int], per_pos: int) -> list[int]:
    total = {pid: sum(week.get(pid, 0) for week in scores.values()) for pid in players}
    pool = set(pid for pid in current_squad if pid in players)
    for pos in POSITION_QUOTAS:
        ranked = sorted((pid for pid in players if players[pid]["pos"] == pos),
                        key=lambda pid: total[pid], reverse=True)
        pool.update(ranked[:per_pos])
    return sorted(pool)


def plan_transfers(scores: dict, players: dict, current_squad: list[int], bank: int,
                   free_transfers: int, max_per_week: int = 2,
                   bench_weight: float = BENCH_WEIGHT, decay: float = WEEK_DECAY,
                   pool_per_position: int = POOL_PER_POSITION,
                   hit_margin: float = HIT_MARGIN, allow_hits: bool = True) -> dict:
    """Plan transfers across every gameweek in `scores` at once.

    Free transfers roll over (+1 a week, capped at MAX_FREE_TRANSFERS); each transfer
    beyond those available costs HIT_COST. Squad value is held at current prices
    (FPL's sell-on price isn't public, same simplification as `optimize`).

    Returns {"weeks": [{event, in, out, hits, free_transfers, starters, bench,
    captain, predicted}], "total", "hold_total"} - `predicted` is that week's XI plus
    captain, undiscounted; `total`/`hold_total` are the undiscounted sums net of hits.
    """
    weeks = sorted(scores)
    pool = _pool(scores, players, current_squad, pool_per_position)
    squad0 = set(pid for pid in current_squad if pid in players)
    budget = sum(players[pid]["cost"] for pid in squad0) + bank

    prob = pulp.LpProblem("fpl_plan", pulp.LpMaximize)
    V = pulp.LpVariable
    x = {(p, t): V(f"x_{p}_{t}", cat="Binary") for p in pool for t in weeks}
    s = {(p, t): V(f"s_{p}_{t}", cat="Binary") for p in pool for t in weeks}
    c = {(p, t): V(f"c_{p}_{t}", cat="Binary") for p in pool for t in weeks}
    buy = {(p, t): V(f"b_{p}_{t}", cat="Binary") for p in pool for t in weeks}
    sell = {(p, t): V(f"o_{p}_{t}", cat="Binary") for p in pool for t in weeks}
    ft = {t: V(f"ft_{t}", lowBound=0, upBound=MAX_FREE_TRANSFERS, cat="Integer") for t in weeks}
    hit = {t: V(f"h_{t}", lowBound=0, cat="Integer") for t in weeks}
    # z_t = 1 when this week's transfers use up every free one. FPL spends free
    # transfers before charging hits, so hit = max(0, n - ft) exactly - without z the
    # solver could pay a -4 now to bank a free transfer for later.
    z = {t: V(f"z_{t}", cat="Binary") for t in weeks}
    big_m = max_per_week + MAX_FREE_TRANSFERS

    objective = []
    for i, t in enumerate(weeks):
        w = decay ** i
        for p in pool:
            pts = scores[t].get(p, 0.0)
            objective.append(w * pts * (bench_weight * x[p, t] + (1 - bench_weight) * s[p, t] + c[p, t]))
        objective.append(-(HIT_COST + hit_margin) * hit[t])
    prob += pulp.lpSum(objective)

    prob += ft[weeks[0]] == min(free_transfers, MAX_FREE_TRANSFERS)
    for i, t in enumerate(weeks):
        for p in pool:
            prev = (1 if p in squad0 else 0) if i == 0 else x[p, weeks[i - 1]]
            prob += x[p, t] == prev + buy[p, t] - sell[p, t]
            prob += s[p, t] <= x[p, t]
            prob += c[p, t] <= s[p, t]
        n = pulp.lpSum(buy[p, t] for p in pool)
        prob += n <= max_per_week
        prob += hit[t] >= n - ft[t]
        if not allow_hits:
            prob += hit[t] == 0
        prob += hit[t] <= n - ft[t] + big_m * (1 - z[t])
        prob += hit[t] <= big_m * z[t]
        prob += n - ft[t] <= big_m * z[t]
        if i + 1 < len(weeks):
            prob += ft[weeks[i + 1]] <= ft[t] - n + hit[t] + 1
        prob += pulp.lpSum(x[p, t] for p in pool) == 15
        prob += pulp.lpSum(s[p, t] for p in pool) == 11
        prob += pulp.lpSum(c[p, t] for p in pool) == 1
        for pos, count in POSITION_QUOTAS.items():
            prob += pulp.lpSum(x[p, t] for p in pool if players[p]["pos"] == pos) == count
            lo, hi = FORMATION_LIMITS[pos]
            started = pulp.lpSum(s[p, t] for p in pool if players[p]["pos"] == pos)
            prob += started >= lo
            prob += started <= hi
        for team in {players[p]["team"] for p in pool}:
            prob += pulp.lpSum(x[p, t] for p in pool if players[p]["team"] == team) <= CLUB_LIMIT
        prob += pulp.lpSum(players[p]["cost"] * x[p, t] for p in pool) <= budget

    prob.solve(pulp.PULP_CBC_CMD(msg=False, timeLimit=120))
    if pulp.LpStatus[prob.status] != "Optimal":
        raise RuntimeError(f"Planner did not find a feasible plan: {pulp.LpStatus[prob.status]}")

    on = lambda var: var.value() is not None and var.value() > 0.5
    # Free transfers are only upper-bounded in the model (more is never worse, so
    # the solver may leave slack), so replay the real rollover rule for reporting.
    out_weeks, prev, total = [], squad0, 0.0
    free = min(free_transfers, MAX_FREE_TRANSFERS)
    for t in weeks:
        squad = {p for p in pool if on(x[p, t])}
        starters = sorted(p for p in squad if on(s[p, t]))
        captain = next(p for p in squad if on(c[p, t]))
        n_in = len(squad - prev)
        hits = max(0, n_in - free)
        week_ft, free = free, min(MAX_FREE_TRANSFERS, free - (n_in - hits) + 1)
        predicted = sum(scores[t].get(p, 0) for p in starters) + scores[t].get(captain, 0)
        total += predicted - HIT_COST * hits
        out_weeks.append({
            "event": t, "in": sorted(squad - prev), "out": sorted(prev - squad),
            "free_transfers": week_ft, "hits": hits,
            "squad": sorted(squad), "starters": starters,
            "bench": sorted(squad - set(starters)), "captain": captain,
            "predicted": round(predicted, 2),
        })
        prev = squad
    return {"weeks": out_weeks, "total": round(total, 2),
            "hold_total": round(_hold_total(scores, players, sorted(squad0)), 2)}


def _xi_total(squad: list[int], week: dict, players: dict) -> tuple[float, list[int], int]:
    """Best legal XI + captain for one week's scores. Greedy is exact here: fill the
    formation minimums with each position's best, then the best of the rest."""
    by_pos = {pos: sorted((p for p in squad if players[p]["pos"] == pos),
                          key=lambda p: week.get(p, 0), reverse=True) for pos in POSITION_QUOTAS}
    xi = [p for pos, (lo, _) in FORMATION_LIMITS.items() for p in by_pos[pos][:lo]]
    rest = sorted((p for pos, (lo, hi) in FORMATION_LIMITS.items() for p in by_pos[pos][lo:hi]),
                  key=lambda p: week.get(p, 0), reverse=True)
    xi += rest[:11 - len(xi)]
    captain = max(xi, key=lambda p: week.get(p, 0))
    return sum(week.get(p, 0) for p in xi) + week.get(captain, 0), xi, captain


def _hold_total(scores: dict, players: dict, squad: list[int]) -> float:
    return sum(_xi_total(squad, scores[t], players)[0] for t in scores)


# --- chips ----------------------------------------------------------------

def chips_available(history: dict, next_event: int) -> list[str]:
    """Chips still playable, from the entry history. Per CLAUDE.md: two wildcards
    (one per half of the season), one each of the others."""
    used = Counter()
    for chip in history.get("chips", []):
        half = 1 if chip["event"] < SECOND_HALF_START else 2
        used[(chip["name"], half if chip["name"] == "wildcard" else 0)] += 1
    half = 1 if next_event < SECOND_HALF_START else 2
    out = []
    if not used[("wildcard", half)]:
        out.append("wildcard")
    if half == 1:
        out.append("wildcard (GW20+)")
    out += [c for c in ("freehit", "bboost", "3xc") if not used[(c, 0)]]
    return out


def fixture_structure(fixtures: list, from_event: int, n_teams: int = 20) -> dict:
    """{gw: {"doubles": [team ids], "blanks": [team ids]}} for every gameweek that
    has either, plus "unscheduled": fixtures with no gameweek yet (future doubles)."""
    count = Counter()
    for f in fixtures:
        if f.get("event") and f["event"] >= from_event:
            count[(f["event"], f["team_h"])] += 1
            count[(f["event"], f["team_a"])] += 1
    teams = range(1, n_teams + 1)
    out = {}
    for gw in range(from_event, 39):
        doubles = [t for t in teams if count[(gw, t)] > 1]
        blanks = [t for t in teams if count[(gw, t)] == 0]
        if doubles or blanks:
            out[gw] = {"doubles": doubles, "blanks": blanks}
    out["unscheduled"] = sum(1 for f in fixtures if not f.get("event") and not f.get("finished"))
    return out


def chip_calendar(plan: dict, scores: dict, players: dict, budget: int,
                  available: list[str]) -> list[dict]:
    """Each chip's predicted gain in each planned week, on the planned squad.

    Bench Boost gains the bench's points, Triple Captain the captain's points once
    more, Free Hit the best unconstrained XI minus the planned one. `use` is True
    only where the gain clears CHIP_THRESHOLDS - i.e. beats what the chip would
    typically return in a double gameweek.
    """
    rows = []
    for wk in plan["weeks"]:
        t = wk["event"]
        week = scores[t]
        planned, _, captain = _xi_total(wk["squad"], week, players)
        gains = {}
        if "bboost" in available:
            gains["bboost"] = sum(week.get(p, 0) for p in wk["squad"]) - (planned - week.get(captain, 0))
        if "3xc" in available:
            gains["3xc"] = week.get(captain, 0)
        if "freehit" in available:
            one_week = {p: dict(players[p], score=week.get(p, 0)) for p in players}
            fh = optimal_squad(one_week, budget, bench_weight=0.0)
            gains["freehit"] = _xi_total(fh, week, players)[0] - planned
        for chip, g in gains.items():
            rows.append({"event": t, "chip": chip, "gain": round(g, 2),
                         "use": g >= CHIP_THRESHOLDS[chip]})
    return rows


# --- CLI ------------------------------------------------------------------

def main():
    from engine.fetch import (current_event, free_transfers, get_bootstrap, get_entry_history,
                              get_entry_picks, get_fixtures)
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--team", type=int, required=True)
    ap.add_argument("--horizon", type=int, default=5)
    ap.add_argument("--risk", default="safe")
    ap.add_argument("--free-transfers", type=int, default=None)
    args = ap.parse_args()

    b, f = get_bootstrap(), get_fixtures()
    gw = current_event(b)
    nxt = gw + 1
    picks = get_entry_picks(args.team, gw)
    history = get_entry_history(args.team)
    squad = [p["element"] for p in picks["picks"]]
    bank = picks["entry_history"]["bank"]
    ft = args.free_transfers if args.free_transfers is not None else free_transfers(history)
    horizon = min(args.horizon, 39 - nxt)

    scores, players = gameweek_scores(b, f, nxt, horizon, args.risk)
    plan = plan_transfers(scores, players, squad, bank, ft)
    short = {t["id"]: t["short_name"] for t in b["teams"]}
    name = lambda p: f"{players[p]['name'].split()[-1]} ({short[players[p]['team']]})"

    print(f"Plan GW{nxt}-{nxt + horizon - 1} from {ft} FT, bank £{bank / 10:.1f}m")
    for wk in plan["weeks"]:
        moves = ", ".join(f"{name(o)} -> {name(i)}" for o, i in zip(wk["out"], wk["in"])) or "hold"
        print(f"  GW{wk['event']}: {moves} | FT {wk['free_transfers']}, hits {wk['hits']} | "
              f"C {name(wk['captain'])} | pred {wk['predicted']}")
    print(f"  Total {plan['total']} vs hold {plan['hold_total']} (+{plan['total'] - plan['hold_total']:.1f})")
    if any(wk["hits"] for wk in plan["weeks"]):
        free = plan_transfers(scores, players, squad, bank, ft, allow_hits=False)
        print(f"  Hits buy {plan['total'] - free['total']:+.1f} over the horizon vs the best no-hit plan "
              f"({free['total']}): GW{nxt} no-hit move: "
              + (", ".join(f"{name(o)} -> {name(i)}" for o, i in zip(free['weeks'][0]['out'], free['weeks'][0]['in'])) or "hold"))

    available = chips_available(history, nxt)
    budget = sum(players[p]["cost"] for p in squad if p in players) + bank
    print(f"\nChips available: {', '.join(available)}")
    for row in chip_calendar(plan, scores, players, budget, available):
        flag = "USE" if row["use"] else "hold"
        print(f"  GW{row['event']} {CHIP_NAMES[row['chip']]:<15} +{row['gain']:.1f}  {flag}")
    structure = fixture_structure(f, nxt)
    unscheduled = structure.pop("unscheduled")
    if structure:
        for g, d in structure.items():
            print(f"  GW{g}: doubles {[short[t] for t in d['doubles']]} blanks {[short[t] for t in d['blanks']]}")
    else:
        print("  No blank or double gameweeks on the schedule yet"
              + (f" ({unscheduled} fixtures still unscheduled)" if unscheduled else "")
              + " - hold Bench Boost / Triple Captain / Free Hit for when they appear.")


if __name__ == "__main__":
    main()
