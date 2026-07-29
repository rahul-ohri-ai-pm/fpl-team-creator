"""Predicted-points heuristic per player, v1.

FPL's own `form` stat (avg points/match, last 30 days) is already a solid
expected-points proxy. We adjust it for upcoming fixture ease, minutes
reliability, injury doubt, and a risk-profile-driven ownership nudge.

Before GW1 none of that is live: `form` is 0.0 for every player and `minutes`
still describes last season. See engine/preseason.py for the two fallbacks that
keep the pre-season run honest - a price-implied baseline for players with no
Premier League record, and the hand-maintained pre-season file.
"""
from __future__ import annotations

from engine import preseason as preseason_mod

POSITION_BY_TYPE = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}


def _finished_events(bootstrap) -> int:
    """Games played so far this season. 0 pre-season/early season - callers must
    not divide by this directly (minutes would then look artificially reliable)."""
    return sum(1 for e in bootstrap["events"] if e["finished"])


# How fast a fixture's influence decays with each gameweek further out. `score` is
# next gameweek's predicted points, so the imminent fixture has to dominate - a flat
# average over four gave it only 25% of the weight and let an easy run three weeks
# out cancel a hard opener. Some lookahead is still right, because a squad can only
# absorb about one free transfer a week. At 0.5 over four fixtures the weights come
# out at roughly 53% / 27% / 13% / 7%, so the next fixture outweighs the rest combined
# without the later ones dropping out of sight.
FIXTURE_DECAY = 0.5


def fixture_ease(team_id: int, fixtures: list, next_event: int, n: int = 4,
                 decay: float = FIXTURE_DECAY) -> float:
    """0 (very hard run) .. 1 (very easy run) over the next n fixtures, weighted
    towards the imminent one.

    Home/away is already carried by FDR: FPL rates the two sides of a fixture
    separately (an away trip to a mid-table side scores harder than hosting them),
    so venue needs no separate term here - it needs the imminent fixture to actually
    count, which is what the decay fixes.
    """
    upcoming = [f for f in fixtures if f["event"] and f["event"] >= next_event
                and (f["team_h"] == team_id or f["team_a"] == team_id)]
    upcoming.sort(key=lambda f: f["event"])
    upcoming = upcoming[:n]
    if not upcoming:
        return 0.5
    diffs = [f["team_h_difficulty"] if f["team_h"] == team_id else f["team_a_difficulty"]
             for f in upcoming]
    weights = [decay ** i for i in range(len(diffs))]
    avg_fdr = sum(d * w for d, w in zip(diffs, weights)) / sum(weights)  # 1 easy .. 5 hard
    return max(0.0, min(1.0, (5 - avg_fdr) / 4))


# How much of a player's fixture adjustment comes from the position-aware opponent
# matchup rather than FDR. FDR compresses an opponent into one integer that is
# identical for a goalkeeper and a striker, which is wrong in an obvious way: a
# clean sheet depends on how well the opponent attacks, an attacking return on how
# badly they defend. Held at half so FDR - which also carries venue and FPL's own
# composite judgement - still anchors the estimate.
MATCHUP_WEIGHT = 0.5

# Weight on (opponent's attack, opponent's defence) by position. Defenders and
# keepers live off clean sheets, so a dangerous opponent attack hurts them most;
# forwards only care how leaky the opponent is. Defenders and midfielders get a
# share of both because both score attacking returns too.
POSITION_MATCHUP = {
    "GK": (1.0, 0.0),
    "DEF": (0.7, 0.3),
    "MID": (0.3, 0.7),
    "FWD": (0.0, 1.0),
}


def _normalized_strengths(teams: list) -> dict | None:
    """Team attack/defence strength rescaled to 0 (weakest) .. 1 (strongest).

    Min-max normalised within the league so this works whatever absolute scale FPL
    uses. Returns None when the fields are flat or absent - they sit at 0 for every
    club pre-season, and a constant carries no information, so callers fall back to
    FDR rather than pretending a signal exists.
    """
    fields = ("strength_attack_home", "strength_attack_away",
              "strength_defence_home", "strength_defence_away")
    out: dict = {}
    for field in fields:
        values = {t["id"]: (t.get(field) or 0) for t in teams}
        lo, hi = min(values.values()), max(values.values())
        if hi <= lo:
            return None
        out[field] = {tid: (v - lo) / (hi - lo) for tid, v in values.items()}
    return out


def opponent_matchup_ease(pos: str, team_id: int, fixtures: list, next_event: int,
                          strengths: dict | None, n: int = 4,
                          decay: float = FIXTURE_DECAY) -> float | None:
    """0 (brutal matchups) .. 1 (kind matchups) for this position specifically.

    None when strength data isn't usable, so the caller keeps FDR alone.
    """
    if not strengths:
        return None
    w_att, w_def = POSITION_MATCHUP.get(pos, (0.5, 0.5))

    upcoming = [f for f in fixtures if f["event"] and f["event"] >= next_event
                and (f["team_h"] == team_id or f["team_a"] == team_id)]
    upcoming.sort(key=lambda f: f["event"])
    upcoming = upcoming[:n]
    if not upcoming:
        return None

    hardness, weights = [], []
    for i, f in enumerate(upcoming):
        at_home = f["team_h"] == team_id
        opponent = f["team_a"] if at_home else f["team_h"]
        # The opponent's own venue is the mirror of ours, and a side attacks and
        # defends differently home and away.
        suffix = "away" if at_home else "home"
        att = strengths[f"strength_attack_{suffix}"].get(opponent, 0.5)
        dfn = strengths[f"strength_defence_{suffix}"].get(opponent, 0.5)
        hardness.append(w_att * att + w_def * dfn)
        weights.append(decay ** i)

    weighted = sum(h * w for h, w in zip(hardness, weights)) / sum(weights)
    return max(0.0, min(1.0, 1.0 - weighted))


def score_players(bootstrap, fixtures, next_event: int, risk_profile: str = "safe",
                  preseason=None) -> dict:
    """Returns {player_id: {"score": float, "pos": str, "team": int, "cost": int, "name": str}}

    `preseason` is an engine.preseason.Preseason; loaded from disk when omitted.
    Pass Preseason() to score on FPL data alone.
    """
    finished = _finished_events(bootstrap)
    team_ease = {t["id"]: fixture_ease(t["id"], fixtures, next_event) for t in bootstrap["teams"]}

    # Position-aware opponent matchup, blended over FDR where the data supports it.
    # Cached per (team, position) rather than per player - it's the same fixture run
    # for every defender at a club.
    strengths = _normalized_strengths(bootstrap["teams"])
    matchup_ease: dict = {}
    for t in bootstrap["teams"]:
        for pos in POSITION_MATCHUP:
            m = opponent_matchup_ease(pos, t["id"], fixtures, next_event, strengths)
            if m is not None:
                matchup_ease[(t["id"], pos)] = m

    # Direction and strength of the ownership preference, as a *tiebreak* only.
    # Positive = prefer template/high-ownership cover, negative = prefer differentials.
    # This deliberately never enters `score`: ownership isn't predicted points, and
    # adding it there inflated squad totals into looking like a points forecast they
    # weren't. The optimizer applies it at OWNERSHIP_TIEBREAK_EPSILON strength, so it
    # can only separate players who are otherwise near-identical.
    ownership_weight = {"safe": 1.0, "balanced": 0.2, "differential": -1.0}.get(risk_profile, 0.2)

    ps = preseason_mod.load() if preseason is None else preseason
    baselines = preseason_mod.price_baselines(bootstrap)
    club_short = {t["id"]: t.get("short_name") for t in bootstrap["teams"]}

    out = {}
    for p in bootstrap["elements"]:
        web_name = p["web_name"]
        # `form` is a rolling last-30-days average - it's legitimately 0 pre-season
        # and early in a new season (no matches played recently), not a signal that
        # the player is bad. Fall back to last known points-per-game in that case,
        # and to a price-implied baseline for anyone with no Premier League record
        # at all (new signing, returning loanee, season missed injured) - scoring
        # those at a literal 0 makes them permanently unpickable.
        ppg = float(p["points_per_game"] or 0)
        if ppg == 0:
            ppg = preseason_mod.baseline_ppg(baselines, p["element_type"], p["now_cost"])
        form = float(p["form"] or 0) or ppg

        minutes = p["minutes"]
        # Pre-season/early season, `minutes` is still last season's total and there's
        # no `finished` games this season to normalize against - use a full season
        # (38 games) as the reference so low-minutes players are still discounted.
        games_reference = finished if finished > 0 else 38
        reliability = min(1.0, minutes / (games_reference * 90 * 0.6))
        if minutes == 0:
            # No Premier League record to measure. Assume a discounted starter
            # rather than 0, which would be indistinguishable from "definitely
            # won't play". Applied before the blend below so that a player with
            # pre-season minutes on file is never scored worse than an identical
            # player with none - recording data must not penalise anyone.
            reliability = preseason_mod.UNKNOWN_RELIABILITY

        # Pre-season minutes are the one thing friendlies are genuinely good for:
        # they show who the manager actually intends to start. Blend rather than
        # replace - a few friendlies shouldn't outvote a full season.
        share = ps.minutes_share(web_name)
        if share is not None:
            w = preseason_mod.PRESEASON_MINUTES_WEIGHT
            reliability = (1 - w) * reliability + w * share

        chance = p["chance_of_playing_next_round"]
        injury_mult = (chance if chance is not None else 100) / 100
        if chance is None:
            # FPL hasn't flagged this player. Fall back to any pre-season fitness
            # doubt on file; once FPL sets a real percentage it wins, being the
            # harder source.
            ps_avail = ps.availability(web_name)
            if ps_avail is not None:
                injury_mult = ps_avail

        # Club-level uncertainty (a new manager, say) compounds with the player's own:
        # it makes last season's minutes a weaker guide to this season's XI for
        # everyone at the club, including players FPL has flagged fit.
        club_avail = ps.club_availability(club_short.get(p["team"]))
        if club_avail is not None:
            injury_mult *= club_avail

        pos = POSITION_BY_TYPE[p["element_type"]]
        ease = team_ease.get(p["team"], 0.5)
        m = matchup_ease.get((p["team"], pos))
        if m is not None:
            ease = (1 - MATCHUP_WEIGHT) * ease + MATCHUP_WEIGHT * m
        ease_mult = 0.8 + ease * 0.4  # 0.8 .. 1.2
        ownership = float(p["selected_by_percent"] or 0)

        predicted = form * ease_mult * reliability * injury_mult

        out[p["id"]] = {
            # Predicted points, and nothing else. Summing these across an XI gives a
            # number that can be compared against what the squad actually scores.
            "score": round(predicted, 3),
            # Signed -1..1 ownership preference, applied only as a tiebreak.
            "tiebreak": round((ownership / 100) * ownership_weight, 4),
            "pos": pos,
            "team": p["team"],
            "cost": p["now_cost"],
            "name": f"{p['first_name']} {p['second_name']}",
        }
    return out
