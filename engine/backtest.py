"""Out-of-sample test: which of last season's numbers predicts next season?

The project rule is that scoring weights move on measured error, not intuition.
`evaluate.py` supplies that evidence *during* a season by replaying recorded
predictions against real points. Before a ball is kicked there is nothing to
replay, so this is the other half: a two-season backtest over the whole player
pool, which needs no recorded predictions at all.

The question it answers: for predicting a player's 2025/26 points per 90, is
last season's *realized* points per 90 the better input, or last season's
*underlying* expected goal involvements per 90? Realized points carry finishing
luck; xGI carries the chances a player actually got into. Which one survives a
summer is an empirical question, and the answer turns out to depend on position.

Run:
    python engine/backtest.py

Data note: `element-summary/{id}/history_past` is the only route to a prior
season - `history` (per-gameweek) is wiped at the rollover, which is also why
"how did he finish the season" cannot be answered from this API at all. Season
aggregates are all there is, so this measures a season, not a run-in.
"""
from __future__ import annotations

import concurrent.futures as cf

import requests

from engine.fetch import BASE, get_bootstrap

POSITION_BY_TYPE = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}

# A player needs a real season on both sides to be comparable. Below this, a
# points-per-90 is a handful of cameos amplified by the division.
MIN_MINUTES = 900


def correlation(xs: list[float], ys: list[float]) -> float | None:
    """Pearson r, or None when the sample is too small or has no spread."""
    n = len(xs)
    if n < 8:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sx = sum((x - mx) ** 2 for x in xs) ** 0.5
    sy = sum((y - my) ** 2 for y in ys) ** 0.5
    if sx == 0 or sy == 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy)


def _player_seasons(session, pid: int, element_type: int, prev: str, nxt: str) -> dict | None:
    try:
        data = session.get(f"{BASE}/element-summary/{pid}/", timeout=20).json()
    except Exception:
        return None
    past = {r["season_name"]: r for r in (data.get("history_past") or [])}
    a, c = past.get(prev), past.get(nxt)
    if not a or not c or a["minutes"] < MIN_MINUTES or c["minutes"] < MIN_MINUTES:
        return None
    return {
        "pos": POSITION_BY_TYPE[element_type],
        "prev_pts90": a["total_points"] / (a["minutes"] / 90),
        "prev_xgi90": float(a.get("expected_goal_involvements") or 0) / (a["minutes"] / 90),
        "next_pts90": c["total_points"] / (c["minutes"] / 90),
    }


def collect(bootstrap=None, prev: str = "2024/25", nxt: str = "2025/26",
            workers: int = 16) -> list[dict]:
    """One row per player with a full season on both sides of the summer."""
    bootstrap = bootstrap or get_bootstrap()
    cands = [p for p in bootstrap["elements"] if p["minutes"] > MIN_MINUTES]
    session = requests.Session()
    with cf.ThreadPoolExecutor(workers) as ex:
        rows = ex.map(lambda p: _player_seasons(session, p["id"], p["element_type"], prev, nxt),
                      cands)
        return [r for r in rows if r]


def compare(rows: list[dict]) -> dict:
    """Per position: how well each input predicts the following season."""
    out = {}
    for pos in ("GK", "DEF", "MID", "FWD", "ALL"):
        sub = rows if pos == "ALL" else [r for r in rows if r["pos"] == pos]
        y = [r["next_pts90"] for r in sub]
        out[pos] = {
            "n": len(sub),
            "points": correlation([r["prev_pts90"] for r in sub], y),
            "xgi": correlation([r["prev_xgi90"] for r in sub], y),
        }
    return out


def main():
    rows = collect()
    print(f"players with a full season on both sides: {len(rows)}\n")
    print(f"{'pos':5s} {'n':>4} {'prev pts/90':>12} {'prev xGI/90':>12}  better predictor")
    for pos, r in compare(rows).items():
        if r["points"] is None or r["xgi"] is None:
            print(f"{pos:5s} {r['n']:>4}  sample too small")
            continue
        better = "xGI" if r["xgi"] > r["points"] else "points"
        print(f"{pos:5s} {r['n']:>4} {r['points']:>12.3f} {r['xgi']:>12.3f}  {better}")


if __name__ == "__main__":
    main()
