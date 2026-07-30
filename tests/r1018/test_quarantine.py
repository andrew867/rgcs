"""R10.44 — the Montreal quarantine, LIFTED by operator instruction.

The R10.18C quarantine was an operator decision and so is lifting it
(2026-07-29). These tests now pin the RELEASE, and — more importantly —
pin the technical note the quarantine was flagging, so lifting the gate
does not quietly lose the reason it existed.
"""

import pytest

from r1016 import quarantine as q
from r1028.varcodec36 import decode

MONTREAL = ("165879243", "168500683", "168729543")


def test_quarantine_is_lifted():
    assert q.QUARANTINED == {}
    assert q.QUARANTINED_FAMILIES == ()


@pytest.mark.parametrize("value", MONTREAL)
def test_assert_clean_now_passes_on_montreal(value):
    q.assert_clean(["165876523", value], where="R10.44 scoring")
    assert q.is_quarantined(value) is False


@pytest.mark.parametrize("value", MONTREAL)
def test_every_released_value_carries_its_note(value):
    """Lifting the gate must not lose WHY it was raised."""
    assert value in q.RELEASED_BY_OPERATOR
    assert q.RELEASED_BY_OPERATOR[value].strip()


def test_the_band_conflict_that_prompted_the_quarantine_still_exists():
    """Montreal is in North America. The DIRECT wire says Britain."""
    direct = decode(165879243)
    canonical = decode(168500683)
    assert direct["S8_surface"] >> 3 == 15      # Britain macroband
    assert canonical["S8_surface"] >> 3 == 16   # North America
    # the local cell and state are preserved across the correction
    assert direct["P12_path"] == canonical["P12_path"] == 3191
    assert (165879243 & 63) == (168500683 & 63) == 11


def test_superseded_transcription_is_a_different_cell():
    d = decode(168729543)
    assert d["P12_path"] == 2671 != 3191


def test_bridge_now_accepts_montreal():
    from r1019.bridge import bridge
    assert isinstance(bridge("165879243"), int)
