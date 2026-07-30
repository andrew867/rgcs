"""R10.19 — the SurfaceBridge, its evidence, and its limits."""

import pytest

from r1016.quarantine import QuarantineError
from r1019 import bridge as B


def test_header_stripped_affine_reproduces_both_pairs_exactly():
    r = B.verify_same_location_pairs()
    assert r["exact_reproductions"] == 2
    assert all(row["exact"] for row in r["rows"])
    assert r["parameters_fitted_in_this_run"] == 0


def test_constants_come_from_the_recorded_ledger_not_from_here():
    from r109.superseded import LEDGER
    model = LEDGER["HISTORICAL_R10_8_AFFINE_CANONICALIZATION"]["model"]
    assert str(B.MULTIPLIER) in model and str(B.OFFSET) in model


def test_whole_wire_application_does_not_reproduce_the_pairs():
    """The operand error that shelved this model at R10.9."""
    for wire, target in B.SAME_LOCATION_PAIRS.values():
        whole = (B.MULTIPLIER * wire + B.OFFSET) % B.MODULUS
        assert whole != target


def test_evidence_strength_is_family_membership_not_uniqueness():
    f = B.solution_family_size()
    assert f["solvable"] and f["family_size"] == 32
    assert f["recorded_multiplier_in_family"]
    assert f["recorded_multiplier_rank"] == 0
    assert f["probability_recorded_pair_lands_in_family_by_chance"] < 1e-16


def test_bridge_refuses_a_recorded_surface_word_as_input():
    """A SurfaceWord also starts with '16', so the lexical header alone
    cannot type it. Feeding an output back in is the R10.16C error."""
    for word in B.RECORDED_SURFACE_WORDS:
        assert word.startswith(B.TRANSPORT_HEADER)
        with pytest.raises(B.BridgeError, match="category error"):
            B.bridge(word)


def test_bridge_refuses_a_value_with_no_transport_header():
    with pytest.raises(B.BridgeError, match="carries no"):
        B.bridge(4789253)


def test_bridge_accepts_montreal_after_the_r1044_lift():
    """Quarantine lifted by operator instruction (R10.44)."""
    from r1016 import quarantine as q
    assert q.QUARANTINED == {}
    for v in ("165879243", "168500683", "168729543"):
        assert isinstance(B.bridge(v), int)
        assert v in q.RELEASED_BY_OPERATOR


def test_anchors_are_never_counted_as_confirmations():
    wires = [str(w) for w, _ in B.SAME_LOCATION_PAIRS.values()]
    r = B.generalization_report(wires)
    assert r["independent_rows"] == 0
    assert r["independent_hits"] == 0
    assert all(row["is_training_anchor"] for row in r["rows"])


def test_affine_is_refuted_by_the_third_labelled_pair():
    """R10.47C. Two points DEFINE an affine mod 2^30; they cannot test
    it. The third labelled pair is the first out-of-sample trial."""
    var, comp = B.REFUTING_PAIR["CYYT_StJohns"]
    got = B.bridge(var)
    assert got != comp
    assert abs(got - comp) > 4e8            # not a near miss
    assert B.STATUS["canonical_same_location_pairs"].startswith("REFUTED")
    assert B.STATUS["general_transport_bridge"].startswith("REFUTED")


def test_no_member_of_the_fitting_family_reproduces_the_third_pair():
    from math import gcd
    M = B.MODULUS
    (v1, c1), (v2, c2) = B.SAME_LOCATION_PAIRS.values()
    x1, x2 = B.strip_header(v1), B.strip_header(v2)
    v3, c3 = B.REFUTING_PAIR["CYYT_StJohns"]
    x3 = B.strip_header(v3)
    dx, dy = (x2 - x1) % M, (c2 - c1) % M
    g = gcd(dx, M)
    inv = pow(dx // g, -1, M // g)
    a0 = (dy // g * inv) % (M // g)
    fam = [((a0 + k * (M // g)) % M) for k in range(g)]
    assert len(fam) == 32
    assert not [a for a in fam if (a * x3 + (c1 - a * x1)) % M == c3]


def test_status_does_not_claim_avebury_is_refuted():
    """Avebury is a DIFFERENT family, not a failed affine.

    Its relation to Stonehenge is exact in payload-octal space
    (2173604 || 1). Recording it as 'refuted' would have buried a
    confirmed structural finding under a category error.
    """
    s = B.STATUS["right_append_child_relation"]
    assert not s.startswith("REFUTED")
    assert "PAYLOAD_OCTAL" in s
    from r1019.families import right_appends_stonehenge
    assert right_appends_stonehenge("1647012173") == (True, "1")
