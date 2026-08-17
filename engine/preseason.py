"""Pre-season signal, and a price-based baseline for players FPL has no history for.

Two gaps in the raw API that both bite hardest right before GW1:

1. No pre-season data at all. FPL ingests only competitive Premier League matches,
   so `form` is 0.0 for every player until GW1 is played and friendlies are absent
   entirely. `data/preseason.json` is the hand-maintained stand-in - see its
   _README for why it can't be fetched.

2. Players with no last-season Premier League record - new signings, returning
   loanees, players who missed the season injured - have points_per_game 0 and
   minutes 0. Scored literally they rank below a £4.0m third-choice keeper and can
   never be picked, no matter what FPL charges for them.
"""
from __future__ import annotations

import json
import os

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "data", "preseason.json")

# Weight on the pre-season minutes share when blending it with last season's
# reliability. Deliberately below half: a friendly programme is a handful of
# games against mixed opposition, so it informs the picture without overwriting
# a full season of evidence.
PRESEASON_MINUTES_WEIGHT = 0.4

# Reliability assumed for a player with no minutes on either side of the split -
# no last-season record and no pre-season minutes entered. Discounted well below
# a proven ever-present, but not zero, which would silently bar them from selection.
UNKNOWN_RELIABILITY = 0.55


class Preseason:
    """Per-player pre-season adjustments, keyed by FPL `web_name`.

    `web_name` is not unique. The live pool carries 14 collisions - three players
    answer to "Wilson", and "Munoz" and "Muñoz" are different footballers at
    different clubs in different positions. A mis-keyed entry doesn't fail, it
    silently moves the wrong player's score, which has already happened twice in
    this project's history. Two defences:

    - An entry may carry `element_id`, the FPL element id, which is unique and
      wins over `web_name` whenever present. Prefer it for any colliding name.
    - `validate(bootstrap)` reports entries that match no player or several, so a
      weekly run surfaces the problem instead of quietly scoring the wrong man.
    """

    def __init__(self, data: dict | None = None):
        data = data or {}
        self.updated = data.get("updated")
        self.friendlies = data.get("friendlies") or []
        self.context = data.get("context") or []
        entries = [p for p in (data.get("players") or []) if p.get("web_name")]
        self._entries = entries
        self._players = {p["web_name"]: p for p in entries}
        self._by_id = {int(p["element_id"]): p for p in entries if p.get("element_id")}
        self._clubs = {c["short_name"]: c for c in (data.get("clubs") or [])
                       if c.get("short_name")}

    def validate(self, bootstrap) -> list[str]:
        """Problems with this file against the live pool, worst first. Empty is good.

        Not raised - a stale name shouldn't take down the weekly run - but the
        caller is expected to show these, because a silent mis-key is the whole
        failure mode this exists to catch.
        """
        by_name: dict[str, list] = {}
        ids = set()
        for p in bootstrap["elements"]:
            by_name.setdefault(p["web_name"], []).append(p)
            ids.add(p["id"])

        by_id = {p["id"]: p for p in bootstrap["elements"]}

        problems = []
        for e in self._entries:
            name = e["web_name"]
            eid = e.get("element_id")
            if eid is not None:
                target = by_id.get(int(eid))
                if target is None:
                    problems.append(f"{name!r}: element_id {eid} is not in the current pool")
                elif target["web_name"] != name:
                    # Checking only that the id exists is not enough: a transposed or
                    # stale id points at a real player, just the wrong one, and then
                    # every flag on this entry silently lands on them instead. This
                    # has happened - a "Saka" entry carrying Merino's id meant Saka
                    # went unflagged while Merino took the haircut.
                    problems.append(
                        f"{name!r}: element_id {eid} belongs to "
                        f"{target['web_name']!r} ({target['first_name']} {target['second_name']}). "
                        f"Every flag on this entry is being applied to the wrong player.")
                continue
            matches = by_name.get(name, [])
            if not matches:
                problems.append(f"{name!r}: matches no player in the pool (renamed or departed?)")
            elif len(matches) > 1:
                where = ", ".join(f"id {m['id']} ({m['first_name']} {m['second_name']})"
                                  for m in matches)
                problems.append(
                    f"{name!r}: AMBIGUOUS - {len(matches)} players share this web_name "
                    f"[{where}]. Add element_id to disambiguate; scoring is currently "
                    f"applying this entry to whichever one loaded last.")
        return problems

    def club_override(self, web_name: str, element_id: int | None = None) -> str | None:
        """Club short_name a player has actually moved to, when FPL's pool still
        lists the old one. None if no override applies.

        FPL ingests a transfer some time after it completes, and during a window
        that lag is days. Until it catches up, every team-derived term is computed
        against the wrong club: fixture run, opponent matchup, any club-level flag,
        and - most dangerously - the three-per-club limit, which can silently
        produce an illegal squad. `moved_to` in a players[] entry fixes all of them
        at once by remapping the player's team before scoring.
        """
        p = self._entry(web_name, element_id)
        if not p:
            return None
        return p.get("moved_to") or None

    def _entry(self, web_name: str, element_id: int | None):
        """The entry for this player: by element_id when the file gives one, else
        by name."""
        if element_id is not None and element_id in self._by_id:
            return self._by_id[element_id]
        entry = self._players.get(web_name)
        # A name-keyed entry must not leak onto a different player who happens to
        # share the name and was pinned by id elsewhere in the file.
        if entry is not None and entry.get("element_id") is not None:
            return entry if element_id == int(entry["element_id"]) else None
        return entry

    def __len__(self):
        return len(self._players)

    def club_availability(self, short_name: str | None) -> float | None:
        """0..1 multiplier applying to every player at a club - a new manager, a
        tactical overhaul, anything that makes last season's minutes a weaker guide
        to this season's XI. None if the club isn't flagged."""
        c = self._clubs.get(short_name or "")
        if not c:
            return None
        a = c.get("availability")
        return None if a is None else max(0.0, min(1.0, float(a)))

    def club_note(self, short_name: str | None) -> str | None:
        c = self._clubs.get(short_name or "")
        return c.get("note") if c else None

    def minutes_share(self, web_name: str, element_id: int | None = None) -> float | None:
        """0..1 share of available pre-season minutes, or None if not recorded."""
        p = self._entry(web_name, element_id)
        if not p:
            return None
        played, possible = p.get("minutes"), p.get("possible_minutes")
        if played is None or not possible:
            return None
        return max(0.0, min(1.0, played / possible))

    def availability(self, web_name: str, element_id: int | None = None) -> float | None:
        """0..1 multiplier for a risk FPL hasn't flagged yet, or None."""
        p = self._entry(web_name, element_id)
        if not p:
            return None
        a = p.get("availability")
        return None if a is None else max(0.0, min(1.0, float(a)))

    def note(self, web_name: str, element_id: int | None = None) -> str | None:
        p = self._entry(web_name, element_id)
        return p.get("note") if p else None


def load(path: str = DEFAULT_PATH) -> Preseason:
    """Load the pre-season file. A missing or unreadable file is not fatal - the
    core fetch/score/optimize pipeline must still run without it."""
    try:
        with open(path) as fh:
            return Preseason(json.load(fh))
    except (OSError, ValueError):
        return Preseason()


def price_baselines(bootstrap) -> dict:
    """Fit ppg ~ price per position, on players who actually have a record.

    FPL prices a new signing by what it expects them to produce, so price is the
    best free proxy available for someone with no Premier League history. Fitted
    from the live pool each run rather than hardcoded, so it recalibrates itself
    as prices and scoring rules drift between seasons.
    """
    by_pos: dict[int, list[tuple[float, float]]] = {}
    for p in bootstrap["elements"]:
        ppg = float(p["points_per_game"] or 0)
        if ppg > 0 and p["minutes"] > 900:  # a real sample, not a handful of cameos
            by_pos.setdefault(p["element_type"], []).append((p["now_cost"] / 10, ppg))

    models = {}
    for pos_type, pts in by_pos.items():
        if len(pts) < 10:
            continue
        n = len(pts)
        mx = sum(x for x, _ in pts) / n
        my = sum(y for _, y in pts) / n
        sxx = sum((x - mx) ** 2 for x, _ in pts)
        if sxx == 0:
            continue
        slope = sum((x - mx) * (y - my) for x, y in pts) / sxx
        models[pos_type] = (slope, my - slope * mx)
    return models


def baseline_ppg(models: dict, element_type: int, now_cost: int) -> float:
    """Expected ppg implied by price. 0 if the position couldn't be fitted."""
    if element_type not in models:
        return 0.0
    slope, intercept = models[element_type]
    return max(0.0, slope * (now_cost / 10) + intercept)
