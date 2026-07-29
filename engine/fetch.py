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
            entry_out["free_transfers"] = picks.get("entry_history", {}).get("event_transfers_cost")
            entry_out["picks"] = [p["element"] for p in picks.get("picks", [])]
            entry_out["active_chip"] = picks.get("active_chip")
        else:
            entry_out["note"] = "Pre-season: no gameweek picks yet."
        out["entry"] = entry_out

    json.dump(out, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
