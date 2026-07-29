"""Free-transfer derivation (engine.fetch.free_transfers).

The public FPL API has no free-transfer balance, so the count is replayed from
transfer history. These cases pin the roll-over rule down; they use synthetic
histories so they run without network access.
"""
import pytest

from engine.fetch import UNLIMITED_TRANSFERS, free_transfers


def history(events, chips=None):
    return {
        "current": [{"event": e, "event_transfers": t} for e, t in events],
        "chips": [{"name": n, "event": e} for e, n in (chips or [])],
    }


@pytest.mark.parametrize("name,hist,expected", [
    ("pre-season, no history yet", history([]), UNLIMITED_TRANSFERS),
    ("GW1 changes are unlimited and don't roll over", history([(1, 9)]), 1),
    ("an unused free transfer rolls over", history([(1, 0), (2, 0)]), 2),
    ("using the free transfer leaves one for next week", history([(1, 0), (2, 1)]), 1),
    ("a -4 hit doesn't borrow against next week", history([(1, 0), (2, 2)]), 1),
    ("roll-over caps at 5", history([(i, 0) for i in range(1, 9)]), 5),
    ("banked transfers spend down", history([(1, 0), (2, 0), (3, 0), (4, 2)]), 2),
    ("wildcard week keeps saved transfers",
     history([(1, 0), (2, 0), (3, 0), (4, 11)], [(4, "wildcard")]), 4),
    ("free hit week keeps saved transfers",
     history([(1, 0), (2, 0), (3, 0), (4, 11)], [(4, "freehit")]), 4),
    ("events out of order are still replayed in order",
     history([(2, 1), (1, 0), (3, 0)]), 2),
])
def test_free_transfers(name, hist, expected):
    assert free_transfers(hist) == expected


def test_missing_transfer_count_is_treated_as_zero():
    assert free_transfers({"current": [{"event": 1}, {"event": 2}]}) == 2
