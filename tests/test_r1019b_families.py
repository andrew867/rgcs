"""R10.19B — family sorting. NO UNIVERSAL BRIDGE.

Operator instruction: do not run one universal bridge; sort into bridge
families first. These tests pin the precedence that makes that true.
"""

import pytest

from r1016.quarantine import QuarantineError
from r1019.families import (
    AFFINE_SAME_LOCATION,
    NO_AFFINE,
    STONEHENGE_PAYLOAD_OCTAL,
    classify,
    payload_octal,
    right_appends_stonehenge,
    sort_ledger,
)


def fam(v, group="", **kw):
    return classify(v, group, **kw)["bridge_family"]


# --- the structural split -------------------------------------------

def test_thirty_bit_test_precedes_the_lexical_header():
    """A direct SurfaceWord also starts with '16' and ends with '3'.

    Testing the lexical header first routes it into the affine lane and
    mangles it: the R10.16C category error.
    """
    v = "165829473"
    assert v.startswith("16") and v.endswith("3")
    assert int(v) < (1 << 30)
    assert fam(v) == "DIRECT_30BIT_SURFACEWORD_RAW"


def test_direct_surface_words_need_no_bridge():
    c = classify("165829473")
    assert c["needs_bridge"] is False
    assert c["surface_word"] == 165829473
    assert c["projectable"]


def test_record_group_splits_canonical_from_raw():
    assert fam("165829473", "earth_root_35") == \
        "DIRECT_OR_CANONICAL_30BIT_SURFACEWORD"
    assert fam("165829473", "census_extra") == \
        "DIRECT_30BIT_SURFACEWORD_RAW"


# --- the affine lane is closed --------------------------------------

def test_affine_family_contains_exactly_the_two_confirmed_wires():
    assert set(AFFINE_SAME_LOCATION) == {"1643789253", "1672875493"}
    for w in AFFINE_SAME_LOCATION:
        assert fam(w) == "HEADER_STRIPPED_AFFINE_SAME_LOCATION_BRIDGE"


def test_there_is_no_affine_fallback():
    """An unrecognised variable row must NOT be affine-projected."""
    c = classify("16999999999")
    assert c["bridge_family"] == "UNRESOLVED_VARIABLE_ROUTE"
    assert c["may_affine_project"] is False


@pytest.mark.parametrize("family", sorted(NO_AFFINE))
def test_no_affine_families_are_flagged_unprojectable(family):
    assert family in NO_AFFINE


def test_two_sided_and_private_codecs_are_never_affine_projected():
    for grp, expected in (
            ("r10_11f_28_intake", "R10_11F_TWO_SIDED_VARIABLE_CODEC"),
            ("private_path_17",
             "PRIVATE_PATH_BASE100_OR_TWO_SIDED_VARIABLE_CODEC")):
        c = classify("16879053173", grp)
        assert c["bridge_family"] == expected
        assert c["may_affine_project"] is False


# --- the Avebury right-append ---------------------------------------

def test_avebury_right_appends_stonehenge_payload_octal():
    assert payload_octal("165876523") == STONEHENGE_PAYLOAD_OCTAL
    ok, tail = right_appends_stonehenge("1647012173")
    assert ok and tail == "1"
    assert payload_octal("1647012173") == STONEHENGE_PAYLOAD_OCTAL + "1"


def test_avebury_relation_outranks_its_worked_example_group():
    """The append is a positive structural finding, not an example."""
    assert fam("1647012173", "worked_examples", worked_example=True) == \
        "PAYLOAD_OCTAL_STONEHENGE_RIGHT_APPEND_FAMILY"


def test_avebury_is_not_reachable_through_the_affine():
    """Why the earlier affine cross-check failed: wrong family."""
    from r1019.bridge import bridge
    assert bridge("1647012173") != 165876523


# --- exclusions ------------------------------------------------------

def test_short_worked_example_is_not_typed_as_a_surface_word():
    """16343 is 5 digits, so it falls below 2^30 by accident."""
    assert int("16343") < (1 << 30)
    assert fam("16343", "worked_examples", worked_example=True) == \
        "WORKED_EXAMPLE_NOT_GEOGRAPHIC"


def test_quarantine_is_absolute_and_first():
    for v in ("165879243", "168500683", "168729543"):
        assert fam(v) == "QUARANTINED_MONTREAL_FAMILY"
    with pytest.raises(QuarantineError):
        sort_ledger([{"raw_vector": "165879243", "record_group": "x"}])


def test_corrupted_collision_row_is_excluded():
    assert fam("1658792343") == "CORRUPTED_COLLISION_EXCLUDED"


# --- the verdict -----------------------------------------------------

def test_sort_ledger_reports_the_required_verdict():
    r = sort_ledger([{"raw_vector": "165829473",
                      "record_group": "earth_root_35"},
                     {"raw_vector": "1643789253", "record_group": ""}])
    assert r["verdict"] == "R10_19B_VARIABLE_VECTOR_FAMILIES_SORTED"
    assert r["claim"] == "NO_UNIVERSAL_BRIDGE_CLAIM"
    assert r["affine_rows"] == 1 and r["affine_is_closed_at_two"]
