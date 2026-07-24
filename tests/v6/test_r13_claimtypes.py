"""P04 — typed claim semantics and the seven forbidden promotions."""

from __future__ import annotations

import pytest

from r13 import claimtypes as C


def test_the_ladder_is_ordered_and_measurement_is_the_top():
    assert C.ClaimClass.EXACT_IDENTITY.value < C.ClaimClass.BENCH_MEASUREMENT.value
    assert C.MAX_SOFTWARE_CLASS is C.ClaimClass.REPOSITORY_COMPUTATIONAL_RESULT
    assert C.ClaimClass.BENCH_MEASUREMENT in C.MEASUREMENT_CLASSES
    assert C.MAX_SOFTWARE_CLASS not in C.MEASUREMENT_CLASSES


def test_a_state_variable_needs_name_unit_and_domain():
    with pytest.raises(C.ClaimError):
        C.StateVariable("", "Hz", "electrical")
    C.StateVariable("f_s", "Hz", "electrical")   # ok


def test_unit_or_domain_mismatch_is_refused():
    hz = C.StateVariable("f", "Hz", "electrical")
    us = C.StateVariable("t", "us", "acoustic")
    with pytest.raises(C.ClaimError):
        C.refuse_unit_mismatch(hz, us)
    C.refuse_unit_mismatch(hz, C.StateVariable("f2", "Hz", "electrical"))


def test_a_claim_needs_a_justification():
    with pytest.raises(C.ClaimError):
        C.Claim("x", C.ClaimClass.ANALYTIC_MODEL, "")


def test_promotion_to_a_measurement_class_is_refused():
    c = C.Claim("a modelled transfer", C.ClaimClass.NUMERICAL_SIMULATION,
                "solved the model")
    with pytest.raises(C.ClaimError):
        C.refuse_promotion(c, C.ClaimClass.BENCH_MEASUREMENT)
    with pytest.raises(C.ClaimError):
        C.refuse_promotion(c, C.ClaimClass.REPOSITORY_COMPUTATIONAL_RESULT)


def test_a_lower_or_equal_class_is_not_a_promotion():
    c = C.Claim("x", C.ClaimClass.ENGINEERING_CANDIDATE, "declared")
    C.refuse_promotion(c, C.ClaimClass.ANALYTIC_MODEL)   # downward: fine
    C.refuse_promotion(c, C.ClaimClass.ENGINEERING_CANDIDATE)


@pytest.mark.parametrize("name", [
    "similarity_to_equivalence", "simulation_to_measurement",
    "match_to_authentication", "unclosed_to_new_energy",
    "planar_to_isotropic", "alias_to_destination", "paper_to_carrier",
])
def test_every_forbidden_promotion_raises(name):
    with pytest.raises(C.ClaimError):
        C.FORBIDDEN_PROMOTIONS[name]()


def test_there_are_exactly_seven_forbidden_promotions():
    assert len(C.FORBIDDEN_PROMOTIONS) == 7


def test_report_claims_no_measurement():
    r = C.claimtypes_report()
    assert r["measured_here"] == "nothing"
    assert r["max_software_class"] == "REPOSITORY_COMPUTATIONAL_RESULT"
    assert len(r["forbidden_promotions"]) == 7
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
