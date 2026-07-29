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
    """Per-player pre-season adjustments, keyed by FPL `web_name`."""

    def __init__(self, data: dict | None = None):
        data = data or {}
        self.updated = data.get("updated")
        self.friendlies = data.get("friendlies") or []
        self.context = data.get("context") or []
        self._players = {p["web_name"]: p for p in (data.get("players") or [])
                         if p.get("web_name")}

    def __len__(self):
        return len(self._players)

    def minutes_share(self, web_name: str) -> float | None:
        """0..1 share of available pre-season minutes, or None if not recorded."""
        p = self._players.get(web_name)
        if not p:
            return None
        played, possible = p.get("minutes"), p.get("possible_minutes")
        if played is None or not possible:
            return None
        return max(0.0, min(1.0, played / possible))

    def availability(self, web_name: str) -> float | None:
        """0..1 multiplier for a risk FPL hasn't flagged yet, or None."""
        p = self._players.get(web_name)
        if not p:
            return None
        a = p.get("availability")
        return None if a is None else max(0.0, min(1.0, float(a)))

    def note(self, web_name: str) -> str | None:
        p = self._players.get(web_name)
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
