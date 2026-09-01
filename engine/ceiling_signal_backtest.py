"""Does a per-gameweek 'ceiling' signal (threat/bps/ict_index) predict the
*next* gameweek's points better than the player's own actual points did?

Motivated by a gap surfaced in research on this project's scoring model: `score.py`'s
`form` is backward-looking box-score points, with nothing capturing a player's
underlying attacking involvement separately from what they've already banked - so
two players with an identical recent scoreline can carry very different ceilings,
and the model can't tell them apart. This measures whether that gap is real, using
actual per-gameweek FPL data.

Why per-gameweek and not last-season, like engine/backtest.py's xGI study: FPL wipes
per-gameweek history at each season's rollover (see that module's docstring) - only
season aggregates survive for a prior season. Per-gameweek granularity only exists
for the *current* season's finished gameweeks, via /event/{n}/live/. That means this
backtest is necessarily thin early in a season (each run adds one more GW-to-GW
transition) - see the caveat in its CLI output and treat a single-transition result
as a first data point, not a verdict, exactly like this project treats every other
early-season backtest.

Run:
    python engine/ceiling_signal_backtest.py --from 1 --to 2
"""
from __future__ import annotations

import argparse
import json

from engine.backtest import correlation
from engine.fetch import get_bootstrap, get_event_live

POSITION_BY_TYPE = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}
MIN_MINUTES = 60  # a real game, not a substitute cameo
BIG_HAUL = 10  # FPL's own "green arrow" territory - a double-digit haul


def _finished(bootstrap, gw: int) -> bool:
    event = next((e for e in bootstrap["events"] if e["id"] == gw), None)
    return bool(event and event.get("finished"))


def collect(gw_from: int, gw_to: int, min_minutes: int = MIN_MINUTES) -> list[dict]:
    """One row per player who played >= min_minutes in gw_from and also has data
    for gw_to: gw_from's actual points/threat/bps/ict_index (the candidate signals)
    against gw_to's actual points (the target)."""
    bootstrap = get_bootstrap()
    pos_of = {e["id"]: POSITION_BY_TYPE[e["element_type"]] for e in bootstrap["elements"]}
    s_from = {e["id"]: e["stats"] for e in get_event_live(gw_from)["elements"]}
    s_to = {e["id"]: e["stats"] for e in get_event_live(gw_to)["elements"]}

    rows = []
    for pid, st in s_from.items():
        nxt = s_to.get(pid)
        if not nxt or st["minutes"] < min_minutes:
            continue
        rows.append({
            "id": pid,
            "pos": pos_of.get(pid, "?"),
            "points": st["total_points"],
            "threat": float(st["threat"]),
            "bps": st["bps"],
            "ict_index": float(st["ict_index"]),
            "next_points": nxt["total_points"],
        })
    return rows


SIGNALS = ("points", "threat", "bps", "ict_index")


def compare(rows: list[dict]) -> dict:
    """Per position (and overall): correlation of each candidate signal against
    next-gameweek points. `points` is the baseline - the question this answers is
    whether the others beat it, not just whether they're nonzero."""
    out = {}
    for pos in ("GK", "DEF", "MID", "FWD", "ALL"):
        sub = rows if pos == "ALL" else [r for r in rows if r["pos"] == pos]
        y = [r["next_points"] for r in sub]
        out[pos] = {"n": len(sub), **{s: correlation([r[s] for r in sub], y) for s in SIGNALS}}
    return out


def big_haul_hit_rate(rows: list[dict], key: str, threshold: int = BIG_HAUL, decile: int = 10) -> dict:
    """Among the top decile ranked by `key`, what fraction had a big-haul next
    gameweek, vs the whole pool's baseline rate."""
    if len(rows) < decile:
        return {"n": 0, "hits": 0, "rate": None, "baseline_rate": None}
    ranked = sorted(rows, key=lambda r: -r[key])
    n = max(1, len(ranked) // decile)
    top = ranked[:n]
    hits = sum(1 for r in top if r["next_points"] >= threshold)
    baseline = sum(1 for r in rows if r["next_points"] >= threshold) / len(rows)
    return {"n": n, "hits": hits, "rate": round(hits / n, 3), "baseline_rate": round(baseline, 3)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--from", dest="gw_from", type=int, required=True)
    parser.add_argument("--to", dest="gw_to", type=int, required=True)
    args = parser.parse_args()

    bootstrap = get_bootstrap()
    for gw in (args.gw_from, args.gw_to):
        if not _finished(bootstrap, gw):
            print(f"warning: GW{gw} is not marked finished yet in bootstrap - "
                  f"treating its posted points as provisional, not final.")

    rows = collect(args.gw_from, args.gw_to)
    print(f"GW{args.gw_from} -> GW{args.gw_to}: {len(rows)} players with >= {MIN_MINUTES} min in GW{args.gw_from}")
    print()
    print(json.dumps(compare(rows), indent=2))
    print()
    for key in SIGNALS:
        hr = big_haul_hit_rate(rows, key)
        print(f"{key}: top-decile big-haul(>={BIG_HAUL}) rate {hr['rate']} vs pool baseline {hr['baseline_rate']} (n={hr['n']})")


if __name__ == "__main__":
    main()
