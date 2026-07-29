"""R10.18C — the Montreal quarantine is a hard gate, not a convention.

Operator instruction: Montreal is not confirmed. If any Montreal
raw/canonical/superseded value reaches a scoring table, the run is
INVALID. These tests prove the gate fires and that no live structure
still carries the values.
"""

import pytest

from r1016 import inventory, project
from r1016.quarantine import QUARANTINED, QuarantineError, assert_clean


MONTREAL = ("165879243", "168500683", "168729543")


def test_all_three_montreal_values_are_quarantined():
    assert set(MONTREAL) <= set(QUARANTINED)


@pytest.mark.parametrize("value", MONTREAL)
def test_assert_clean_raises_on_each_montreal_value(value):
    with pytest.raises(QuarantineError, match="INVALID RUN"):
        assert_clean(["165876523", value], where="scoring table")


def test_assert_clean_passes_on_the_surviving_anchors():
    assert_clean(project.STRICT_ANCHORS, where="scoring table") is None


def test_montreal_is_absent_from_every_live_anchor_structure():
    from r1016.surface_word import ANCHOR_RECORDS
    live = set(project.STRICT_ANCHORS) | set(project.RAW_TRANSPORT_ANCHORS)
    live |= set(inventory.SOURCE_NOTES)
    for rec in ANCHOR_RECORDS.values():
        live |= {str(rec["raw_vector"]),
                 str(rec["canonical_packet_or_candidate"])}
    assert not (live & set(MONTREAL))


def test_strict_anchor_count_is_three_not_twenty_two():
    """Hard independent anchors: 3. The 17 projection-derived rows are
    internal-consistency only and are never validation."""
    assert len(project.STRICT_ANCHORS) == 3


def test_the_bridge_refuses_quarantined_input():
    from r1019.bridge import bridge
    for v in MONTREAL:
        with pytest.raises(QuarantineError):
            bridge(v)
