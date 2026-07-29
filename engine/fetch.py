"""Pulls raw data from the official public FPL API (no auth required).

Usage:
    python engine/fetch.py                # bootstrap-static + fixtures summary
    python engine/fetch.py --team 123456   # also pulls that entry's current squad
"""
import argparse
import json
import sys

import requests

BASE = "https://fantasy.premierleague.com/api"

FREE_TRANSFER_CAP = 5
# Before the GW1 deadline you can make unlimited changes. There's no "infinity"
# to hand the optimizer, so use a number comfortably above any realistic search.
UNLIMITED_TRANSFERS = 15


def get_bootstrap():
    r = requests.get(f"{BASE}/bootstrap-static/", timeout=15)
    r.raise_for_status()
    return r.json()


def get_fixtures():
    r = requests.get(f"{BASE}/fixtures/", timeout=15)
    r.raise_for_status()
    return r.json()


def get_entry(team_id: int):
    r = requests.get(f"{BASE}/entry/{team_id}/", timeout=15)
    r.raise_for_status()
    return r.json()


def get_entry_picks(team_id: int, event: int):
    r = requests.get(f"{BASE}/entry/{team_id}/event/{event}/picks/", timeout=15)
    r.raise_for_status()
    return r.json()


def get_entry_history(team_id: int):
    r = requests.get(f"{BASE}/entry/{team_id}/history/", timeout=15)
    r.raise_for_status()
    return r.json()


def free_transfers(history) -> int:
    """Free transfers available for the *next* gameweek.

    The public no-auth API exposes no free-transfer balance - that only exists on
    the authenticated `my-team` endpoint, which this project deliberately doesn't
    touch. So replay the roll-over rule over the entry's transfer history: one
    free transfer per gameweek, unused ones roll over up to FREE_TRANSFER_CAP.

    Two weeks don't consume anything: GW1 (unlimited changes before the first
    deadline, and nothing rolls over from them) and any wildcard/free-hit week
    (transfers are free and saved free transfers are retained).
    """
    events = history.get("current") or []
    if not events:
        return UNLIMITED_TRANSFERS

    chip_events = {
        c.get("event") for c in history.get("chips") or []
        if c.get("name") in ("wildcard", "freehit")
    }

    available = 0
    for ev in sorted(events, key=lambda e: e["event"]):
        if ev["event"] == 1:
            leftover = 0
        elif ev["event"] in chip_events:
            leftover = available
        else:
            leftover = max(0, available - (ev.get("event_transfers") or 0))
        available = min(FREE_TRANSFER_CAP, leftover + 1)
    return available


def current_event(bootstrap) -> int:
    for e in bootstrap["events"]:
        if e["is_current"]:
            return e["id"]
    for e in bootstrap["events"]:
        if e["is_next"]:
            return e["id"] - 1
    raise RuntimeError("Could not determine current gameweek")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--team", type=int, help="FPL entry/team ID")
    parser.add_argument("--free-transfers", type=int, default=None,
                        help="Override the derived free-transfer count (see free_transfers())")
    args = parser.parse_args()

    bootstrap = get_bootstrap()
    gw = current_event(bootstrap)
    out = {
        "current_event": gw,
        "num_players": len(bootstrap["elements"]),
        "num_teams": len(bootstrap["teams"]),
    }

    if args.team:
        entry = get_entry(args.team)
        entry_out = {
            "team_name": entry.get("name"),
            "bank": entry.get("last_deadline_bank"),
            "value": entry.get("last_deadline_value"),
        }
        if gw >= 1:
            picks = get_entry_picks(args.team, gw)
            derived_ft = free_transfers(get_entry_history(args.team))
            entry_out["free_transfers"] = (
                args.free_transfers if args.free_transfers is not None else derived_ft
            )
            entry_out["free_transfers_derived"] = derived_ft
            entry_out["picks"] = [p["element"] for p in picks.get("picks", [])]
            entry_out["active_chip"] = picks.get("active_chip")
        else:
            entry_out["free_transfers"] = UNLIMITED_TRANSFERS
            entry_out["note"] = "Pre-season: no gameweek picks yet, unlimited changes until the GW1 deadline."
        out["entry"] = entry_out

    json.dump(out, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
