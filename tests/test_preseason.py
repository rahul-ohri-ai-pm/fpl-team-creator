"""Pre-season layer (engine.preseason) and its effect on scoring.

No network: synthetic bootstrap payloads throughout.
"""
import json

import pytest

from engine import preseason as ps
from engine.score import score_players


def element(pid=1, name="Player", ppg="5.0", minutes=3000, cost=70, etype=3,
            form="0.0", chance=None, own="10.0", team=1):
    return {
        "id": pid, "web_name": name, "first_name": "A", "second_name": name,
        "points_per_game": ppg, "minutes": minutes, "now_cost": cost,
        "element_type": etype, "form": form, "chance_of_playing_next_round": chance,
        "selected_by_percent": own, "team": team,
    }


def bootstrap(elements, finished=0):
    return {
        "elements": elements,
        "events": [{"id": i, "finished": i <= finished} for i in range(1, 39)],
        "teams": [{"id": 1}, {"id": 2}],
    }


NO_FIXTURES: list = []


def score_one(elements, preseason=None, pid=1):
    b = bootstrap(elements)
    return score_players(b, NO_FIXTURES, 1, "safe",
                         preseason=preseason or ps.Preseason())[pid]["score"]


# --- loading --------------------------------------------------------------

def test_missing_file_is_not_fatal(tmp_path):
    loaded = ps.load(str(tmp_path / "nope.json"))
    assert len(loaded) == 0
    assert loaded.minutes_share("Anyone") is None


def test_malformed_file_is_not_fatal(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    assert len(ps.load(str(bad))) == 0


def test_the_checked_in_file_parses_and_matches_its_schema():
    loaded = ps.load()
    assert loaded.updated
    assert loaded.friendlies
    for entry in loaded.friendlies:
        assert {"date", "home", "away", "score"} <= set(entry)


def test_minutes_share_needs_both_halves():
    p = ps.Preseason({"players": [
        {"web_name": "Full", "minutes": 180, "possible_minutes": 360},
        {"web_name": "NoTotal", "minutes": 180},
        {"web_name": "NoMinutes", "possible_minutes": 360},
    ]})
    assert p.minutes_share("Full") == pytest.approx(0.5)
    assert p.minutes_share("NoTotal") is None
    assert p.minutes_share("NoMinutes") is None
    assert p.minutes_share("Absent") is None


def test_shares_and_availability_are_clamped():
    p = ps.Preseason({"players": [
        {"web_name": "Over", "minutes": 500, "possible_minutes": 360, "availability": 1.4},
        {"web_name": "Under", "minutes": -10, "possible_minutes": 360, "availability": -1},
    ]})
    assert p.minutes_share("Over") == 1.0
    assert p.availability("Over") == 1.0
    assert p.minutes_share("Under") == 0.0
    assert p.availability("Under") == 0.0


# --- price baseline -------------------------------------------------------

def make_priced_pool():
    """A pool where ppg is exactly 0.5 * price, so the fit is recoverable."""
    els = []
    for i in range(20):
        cost = 40 + i * 5
        els.append(element(pid=i + 1, name=f"P{i}", ppg=str(cost / 10 * 0.5),
                           minutes=3000, cost=cost, etype=3))
    return els


def test_price_baseline_recovers_a_linear_relationship():
    models = ps.price_baselines(bootstrap(make_priced_pool()))
    assert ps.baseline_ppg(models, 3, 100) == pytest.approx(5.0, abs=0.01)


def test_price_baseline_ignores_players_without_a_real_sample():
    pool = make_priced_pool()
    # Cameo appearances at silly prices must not drag the fit.
    pool.append(element(pid=99, name="Cameo", ppg="12.0", minutes=90, cost=40, etype=3))
    models = ps.price_baselines(bootstrap(pool))
    assert ps.baseline_ppg(models, 3, 100) == pytest.approx(5.0, abs=0.01)


def test_baseline_is_zero_for_an_unfittable_position():
    assert ps.baseline_ppg({}, 3, 100) == 0.0


def test_baseline_never_goes_negative():
    models = ps.price_baselines(bootstrap(make_priced_pool()))
    assert ps.baseline_ppg(models, 3, 1) >= 0.0


def test_player_with_no_history_is_scored_from_price_not_zero():
    pool = make_priced_pool()
    newcomer = element(pid=99, name="Newcomer", ppg="0.0", minutes=0, cost=90, etype=3)
    pool.append(newcomer)
    scores = score_players(bootstrap(pool), NO_FIXTURES, 1, "safe", preseason=ps.Preseason())
    assert scores[99]["score"] > 0


# --- pre-season minutes ---------------------------------------------------

def test_pre_season_minutes_raise_reliability_for_an_unproven_player():
    els = [element(pid=1, name="Rookie", ppg="5.0", minutes=0)]
    without = score_one(els)
    nailed = score_one(els, ps.Preseason({"players": [
        {"web_name": "Rookie", "minutes": 360, "possible_minutes": 360}]}))
    assert nailed > without


def test_pre_season_benching_lowers_a_proven_players_score():
    els = [element(pid=1, name="Star", ppg="6.0", minutes=3400)]
    without = score_one(els)
    benched = score_one(els, ps.Preseason({"players": [
        {"web_name": "Star", "minutes": 0, "possible_minutes": 360}]}))
    assert benched < without


def test_pre_season_minutes_only_partly_outweigh_last_season():
    """A blend, not a replacement - one benched friendly run shouldn't erase a season."""
    els = [element(pid=1, name="Star", ppg="6.0", minutes=3400)]
    benched = score_one(els, ps.Preseason({"players": [
        {"web_name": "Star", "minutes": 0, "possible_minutes": 360}]}))
    assert benched > 0
    assert benched == pytest.approx(score_one(els) * (1 - ps.PRESEASON_MINUTES_WEIGHT), rel=0.05)


# --- availability ---------------------------------------------------------

def test_pre_season_availability_discounts_an_unflagged_player():
    els = [element(pid=1, name="Doubt", chance=None)]
    full = score_one(els)
    doubted = score_one(els, ps.Preseason({"players": [
        {"web_name": "Doubt", "availability": 0.5}]}))
    assert doubted == pytest.approx(full * 0.5, rel=0.05)


def test_fpl_chance_of_playing_beats_the_pre_season_file():
    """FPL flagging a player is the harder source; our editorial guess must yield."""
    els = [element(pid=1, name="Flagged", chance=100)]
    with_file = score_one(els, ps.Preseason({"players": [
        {"web_name": "Flagged", "availability": 0.25}]}))
    assert with_file == pytest.approx(score_one(els))


def test_scoring_runs_unchanged_with_an_empty_preseason():
    els = [element(pid=1, name="Solo")]
    assert score_one(els, ps.Preseason()) == score_one(els, ps.Preseason({}))


# --- club-level flags -----------------------------------------------------

def test_unflagged_club_returns_none():
    assert ps.Preseason({}).club_availability("MCI") is None
    assert ps.Preseason({}).club_availability(None) is None


def test_club_availability_is_clamped():
    p = ps.Preseason({"clubs": [{"short_name": "A", "availability": 3},
                                {"short_name": "B", "availability": -2}]})
    assert p.club_availability("A") == 1.0
    assert p.club_availability("B") == 0.0


def test_club_flag_discounts_every_player_at_that_club():
    els = [element(pid=1, name="CityPlayer", team=1),
           element(pid=2, name="OtherPlayer", team=2)]
    b = bootstrap(els)
    b["teams"] = [{"id": 1, "short_name": "MCI"}, {"id": 2, "short_name": "ARS"}]
    plain = score_players(b, NO_FIXTURES, 1, "safe", preseason=ps.Preseason())
    flagged = score_players(b, NO_FIXTURES, 1, "safe",
                            preseason=ps.Preseason({"clubs": [
                                {"short_name": "MCI", "availability": 0.9}]}))
    assert flagged[1]["score"] == pytest.approx(plain[1]["score"] * 0.9, rel=0.02)
    assert flagged[2]["score"] == pytest.approx(plain[2]["score"])


def test_club_flag_applies_even_when_fpl_says_the_player_is_fit():
    """A settled fitness rating says nothing about whether a new manager picks them."""
    els = [element(pid=1, name="Fit", team=1, chance=100)]
    b = bootstrap(els)
    b["teams"] = [{"id": 1, "short_name": "MCI"}]
    plain = score_players(b, NO_FIXTURES, 1, "safe", preseason=ps.Preseason())
    flagged = score_players(b, NO_FIXTURES, 1, "safe",
                            preseason=ps.Preseason({"clubs": [
                                {"short_name": "MCI", "availability": 0.5}]}))
    assert flagged[1]["score"] == pytest.approx(plain[1]["score"] * 0.5, rel=0.02)


def test_club_and_player_flags_compound():
    els = [element(pid=1, name="Both", team=1)]
    b = bootstrap(els)
    b["teams"] = [{"id": 1, "short_name": "MCI"}]
    plain = score_players(b, NO_FIXTURES, 1, "safe", preseason=ps.Preseason())
    both = score_players(b, NO_FIXTURES, 1, "safe", preseason=ps.Preseason({
        "clubs": [{"short_name": "MCI", "availability": 0.5}],
        "players": [{"web_name": "Both", "availability": 0.5}]}))
    assert both[1]["score"] == pytest.approx(plain[1]["score"] * 0.25, rel=0.02)


def test_checked_in_file_club_entries_are_well_formed():
    loaded = ps.load()
    assert loaded.club_availability("MCI") is not None
    assert loaded.club_note("MCI")


# --- web_name collisions --------------------------------------------------
# `web_name` is not unique: the live pool carries 14 collisions, and "Munoz" /
# "Muñoz" are different footballers at different clubs. A mis-keyed entry does not
# fail, it silently scores the wrong player - which has now happened twice here.

def _pool_with_collision():
    def el(pid, web, first, second, team):
        return {"id": pid, "web_name": web, "first_name": first, "second_name": second,
                "element_type": 3, "team": team, "now_cost": 60,
                "points_per_game": "5.0", "form": "0.0", "minutes": 3000,
                "chance_of_playing_next_round": None, "selected_by_percent": "5.0"}
    return {"elements": [
        el(201, "Munoz", "Daniel", "Munoz Mejia", 1),
        el(377, "Munoz", "Victor", "Munoz", 2),
        el(426, "B.Fernandes", "Bruno", "Fernandes", 3),
    ]}


def test_validate_flags_an_ambiguous_web_name():
    pre = ps.Preseason({"players": [{"web_name": "Munoz", "availability": 0.7}]})
    problems = pre.validate(_pool_with_collision())
    assert len(problems) == 1
    assert "AMBIGUOUS" in problems[0]
    assert "201" in problems[0] and "377" in problems[0]


def test_validate_accepts_an_entry_pinned_by_element_id():
    pre = ps.Preseason({"players": [{"web_name": "Munoz", "element_id": 201, "availability": 0.7}]})
    assert pre.validate(_pool_with_collision()) == []


def test_validate_flags_a_name_that_matches_nobody():
    pre = ps.Preseason({"players": [{"web_name": "Ghost", "availability": 0.5}]})
    problems = pre.validate(_pool_with_collision())
    assert len(problems) == 1 and "matches no player" in problems[0]


def test_validate_flags_a_stale_element_id():
    pre = ps.Preseason({"players": [{"web_name": "Munoz", "element_id": 99999}]})
    problems = pre.validate(_pool_with_collision())
    assert len(problems) == 1 and "not in the current pool" in problems[0]


def test_a_pinned_entry_reaches_only_its_own_player():
    """The actual bug: an availability flag meant for Daniel Munoz (CRY) landed on
    Victor Munoz (LIV), a different player at a different club."""
    pre = ps.Preseason({"players": [{"web_name": "Munoz", "element_id": 201, "availability": 0.7}]})
    assert pre.availability("Munoz", 201) == 0.7
    assert pre.availability("Munoz", 377) is None


def test_an_unpinned_entry_still_works_for_a_unique_name():
    """Pinning must stay optional - most names don't collide and the file should
    not need an id for every one of them."""
    pre = ps.Preseason({"players": [{"web_name": "B.Fernandes", "availability": 0.7}]})
    assert pre.availability("B.Fernandes", 426) == 0.7
    assert pre.validate(_pool_with_collision()) == []


def test_a_clean_file_reports_no_problems():
    assert ps.Preseason({}).validate(_pool_with_collision()) == []


# --- club overrides for transfers FPL hasn't ingested ---------------------

def test_no_override_by_default():
    assert ps.Preseason({}).club_override("Anyone") is None
    assert ps.Preseason({"players": [{"web_name": "X"}]}).club_override("X") is None


def test_club_override_is_read_by_element_id_not_just_name():
    p = ps.Preseason({"players": [
        {"web_name": "Dup", "element_id": 7, "moved_to": "ARS"}]})
    assert p.club_override("Dup", 7) == "ARS"
    assert p.club_override("Dup", 99) is None, "must not leak onto a same-named player"


def test_moved_player_is_scored_on_the_new_clubs_fixtures():
    """The whole point: the wrong club means the wrong fixture run."""
    els = [element(pid=1, name="Mover", team=1)]
    b = bootstrap(els)
    b["teams"] = [{"id": 1, "short_name": "OLD"}, {"id": 2, "short_name": "NEW"}]
    # club 1 has a brutal opener, club 2 an easy one
    fx = [{"event": 1, "team_h": 1, "team_a": 3, "team_h_difficulty": 5, "team_a_difficulty": 3},
          {"event": 1, "team_h": 2, "team_a": 4, "team_h_difficulty": 1, "team_a_difficulty": 3}]
    stay = score_players(b, fx, 1, "safe", preseason=ps.Preseason())[1]
    moved = score_players(b, fx, 1, "safe", preseason=ps.Preseason(
        {"players": [{"web_name": "Mover", "element_id": 1, "moved_to": "NEW"}]}))[1]
    assert moved["team"] == 2, "the scored team must be the new club"
    assert moved["score"] > stay["score"], "an easier opener must show up in the score"


def test_moved_player_counts_against_the_new_clubs_limit():
    """A stale club silently permits an illegal squad - four from one real club."""
    els = [element(pid=i, name=f"P{i}", team=1) for i in range(1, 5)]
    b = bootstrap(els)
    b["teams"] = [{"id": 1, "short_name": "OLD"}, {"id": 2, "short_name": "NEW"}]
    scored = score_players(b, [], 1, "safe", preseason=ps.Preseason(
        {"players": [{"web_name": "P4", "element_id": 4, "moved_to": "NEW"}]}))
    assert scored[4]["team"] == 2
    assert [scored[i]["team"] for i in (1, 2, 3)] == [1, 1, 1]


def test_unknown_club_code_is_ignored_rather_than_crashing():
    els = [element(pid=1, name="Mover", team=1)]
    b = bootstrap(els)
    b["teams"] = [{"id": 1, "short_name": "OLD"}]
    scored = score_players(b, [], 1, "safe", preseason=ps.Preseason(
        {"players": [{"web_name": "Mover", "element_id": 1, "moved_to": "NOPE"}]}))
    assert scored[1]["team"] == 1


def test_any_move_recorded_in_the_checked_in_file_names_a_real_club():
    """Overrides are transient - they exist only until FPL ingests the transfer, so
    pinning one player here would fail the moment the file is correctly cleaned up
    (as happened when FPL caught up with Bruno Guimaraes). Assert the invariant
    instead: whatever moves are on file must name clubs that actually exist, or
    scoring silently ignores them."""
    loaded = ps.load()
    valid = {"ARS", "AVL", "BOU", "BRE", "BHA", "CHE", "COV", "CRY", "EVE", "FUL",
             "HUL", "IPS", "LEE", "LIV", "MCI", "MUN", "NEW", "NFO", "SUN", "TOT"}
    for entry in loaded._entries:
        moved = entry.get("moved_to")
        if moved is not None:
            assert moved in valid, f"{entry['web_name']}: moved_to {moved!r} is not a club code"
