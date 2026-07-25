"""R15 governance core: claim taxonomy, evidence ladder, forbidden promotions."""

from __future__ import annotations

import pytest

from r15 import claims as C


def test_taxonomy_has_the_fifteen_classes():
    assert len(list(C.ClaimClass)) == 15
    assert C.ClaimClass.UNEXPLAINED_INSTRUMENT_RESIDUAL in C.ClaimClass
    # there is no PHRYLL_DETECTED anywhere in the taxonomy
    assert not any("PHRYLL" in c.value for c in C.ClaimClass)


def test_measurement_classes_are_not_software_reachable():
    assert C.MAX_SOFTWARE_CLASS not in C.MEASUREMENT_CLASSES
    assert C.ClaimClass.PHYSICAL_MEASUREMENT in C.MEASUREMENT_CLASSES
    for m in C.MEASUREMENT_CLASSES:
        assert m not in C.SOFTWARE_CLASSES


def test_evidence_caps_below_physical_without_bindings():
    empty = C.EvidenceBindings()
    assert C.evidence_cap(empty, C.EvidenceLevel.E7) is C.MAX_SOFTWARE_EVIDENCE
    assert C.evidence_cap(empty, C.EvidenceLevel.E7).value < C.EvidenceLevel.E4.value


def test_full_bindings_permit_physical_evidence():
    full = C.EvidenceBindings(instrument=True, calibration=True, specimen=True,
                              fixture=True, protocol=True, clock=True,
                              environment=True, raw_artifact=True,
                              uncertainty=True)
    assert full.complete_for_physical()
    assert C.evidence_cap(full, C.EvidenceLevel.E4) is C.EvidenceLevel.E4


def test_missing_bindings_are_named():
    b = C.EvidenceBindings(instrument=True)
    assert "calibration" in b.missing()
    assert "instrument" not in b.missing()


def test_a_claim_needs_a_justification():
    with pytest.raises(C.ClaimError):
        C.Claim("x", C.ClaimClass.MODEL_PREDICTION, "")


def test_promotion_to_measurement_is_refused():
    c = C.Claim("a simulated reading", C.ClaimClass.PHYSICAL_MEASUREMENT,
                "declared", C.EvidenceLevel.E2)
    with pytest.raises(C.ClaimError):
        C.refuse_promotion_to_measurement(c)


def test_measurement_class_caps_to_software_ceiling():
    assert C.cap_claim_to_software(C.ClaimClass.PHYSICAL_MEASUREMENT) is \
        C.MAX_SOFTWARE_CLASS
    assert C.cap_claim_to_software(C.ClaimClass.MODEL_PREDICTION) is \
        C.ClaimClass.MODEL_PREDICTION


@pytest.mark.parametrize("name", [
    "synthetic_to_physical", "source_to_measurement", "model_to_measurement",
    "noise_to_resonance", "residual_to_new_physics", "phryll_detected",
])
def test_every_forbidden_promotion_raises(name):
    with pytest.raises(C.ClaimError):
        C.FORBIDDEN_PROMOTIONS[name]()


def test_there_are_six_forbidden_promotions():
    assert len(C.FORBIDDEN_PROMOTIONS) == 6


def test_report_claims_nothing_and_has_no_phryll_state():
    r = C.claims_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["has_phryll_detected_state"] is False
    assert r["residual_ceiling"] == "UNEXPLAINED_INSTRUMENT_RESIDUAL"
    assert r["max_software_class"] == "MODEL_PREDICTION"
