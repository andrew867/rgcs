"""P28 — prospective bidirectional challenge.

The challenge is sealed before reveal, is bidirectional (vector→place and
place→vector), grades the four outcomes, and — critically — CAN FAIL cleanly: a
deliberately-wrong prediction fails the criterion, and a swapped actual is
refused at reveal.
"""

from __future__ import annotations

import pytest

from cwatlas.r1082 import claims, prospective_challenge as C
from cwatlas.r1082.prospective_challenge import ChallengeDirection, ChallengeOutcome


# -- vector -> place --------------------------------------------------------

def test_vector_to_place_self_consistent_passes():
    from cwatlas.r1082.geocode_forward import geocode, single_family_stub
    stub = single_family_stub()
    fg = geocode("246813579", stub, shell=3, body="EARTH")
    actual = (fg.candidates[0].latitude_deg, fg.candidates[0].longitude_deg)
    spec = C.build_vector_to_place_challenge("V2P", "246813579", actual)
    result = C.run_challenge(spec, actual)
    assert result.outcome is ChallengeOutcome.SUCCESS
    assert result.passed is True
    assert result.primary_error_km == pytest.approx(0.0, abs=1e-6)


def test_vector_to_place_wrong_actual_fails_cleanly():
    from cwatlas.r1082.geocode_forward import geocode, single_family_stub
    stub = single_family_stub()
    fg = geocode("246813579", stub, shell=3, body="EARTH")
    true = (fg.candidates[0].latitude_deg, fg.candidates[0].longitude_deg)
    # Antipode: guaranteed far beyond any sane tolerance.
    wrong = (-true[0], ((true[1] + 360.0) % 360.0) - 180.0)
    spec = C.build_vector_to_place_challenge("V2P_FAIL", "246813579", wrong,
                                             tolerance_km=50.0)
    result = C.run_challenge(spec, wrong)
    assert result.outcome is ChallengeOutcome.FAILURE
    assert result.passed is False
    assert result.primary_error_km > spec.tolerance_km


# -- place -> vector --------------------------------------------------------

def test_place_to_vector_self_consistent_passes():
    from cwatlas.r1082.geocode_forward import single_family_stub
    from cwatlas.r1082.geocode_inverse import inverse_geocode
    stub = single_family_stub()
    ig = inverse_geocode(12.5, -34.0, 3, stub, body="EARTH")
    spec = C.build_place_to_vector_challenge("P2V", (12.5, -34.0),
                                             ig.source_vector)
    result = C.run_challenge(spec, ig.source_vector)
    assert result.outcome is ChallengeOutcome.SUCCESS
    assert result.passed is True


def test_place_to_vector_wrong_vector_fails_cleanly():
    from cwatlas.r1082.geocode_forward import single_family_stub
    from cwatlas.r1082.geocode_inverse import inverse_geocode
    stub = single_family_stub()
    ig = inverse_geocode(12.5, -34.0, 3, stub, body="EARTH")
    wrong = "0000000001" if ig.source_vector != "0000000001" else "9999999998"
    spec = C.build_place_to_vector_challenge("P2V_FAIL", (12.5, -34.0), wrong)
    result = C.run_challenge(spec, wrong)
    assert result.outcome is ChallengeOutcome.FAILURE
    assert result.passed is False


# -- reveal discipline ------------------------------------------------------

def test_swapped_actual_after_seal_is_refused():
    spec = C.build_vector_to_place_challenge("V2P", "246813579", (10.0, 20.0))
    # Revealing a different actual than the sealed one is refused.
    with pytest.raises(C.ChallengeError):
        C.run_challenge(spec, (10.0, 21.0))


def test_seal_commitment_is_direction_specific():
    h_place = C.seal_actual(ChallengeDirection.VECTOR_TO_PLACE, (1.0, 2.0))
    h_place2 = C.seal_actual(ChallengeDirection.VECTOR_TO_PLACE, (1.0, 2.0))
    assert h_place == h_place2
    assert h_place != C.seal_actual(
        ChallengeDirection.VECTOR_TO_PLACE, (1.0, 3.0))


# -- bundles ----------------------------------------------------------------

def test_signed_bundle_round_trips_and_detects_tamper():
    spec = C.build_place_to_vector_challenge("P2V", (12.5, -34.0), "246813579")
    bundle = C.challenge_bundle(spec)
    assert C.verify_bundle(bundle) is True
    bundle["spec"]["tolerance_km"] = 999999.0  # tamper
    assert C.verify_bundle(bundle) is False


# -- synthetic held-back suite: proves falsifiability -----------------------

def test_synthetic_suite_has_both_pass_and_failure():
    results = C.run_synthetic_suite()
    outcomes = {r["challenge_id"]: r["outcome"] for r in results}
    assert outcomes["CHALLENGE_SYN_V2P_PASS"] == "SUCCESS"
    assert outcomes["CHALLENGE_SYN_V2P_FAIL"] == "FAILURE"
    assert outcomes["CHALLENGE_SYN_P2V_PASS"] == "SUCCESS"
    assert outcomes["CHALLENGE_SYN_P2V_FAIL"] == "FAILURE"
    assert any(r["passed"] for r in results)
    assert any(r["outcome"] == "FAILURE" for r in results)


def test_suite_deterministic():
    a = C.run_synthetic_suite()
    b = C.run_synthetic_suite()
    assert [r["outcome"] for r in a] == [r["outcome"] for r in b]


def test_candidate_not_measured_raises():
    spec = C.build_vector_to_place_challenge("V2P", "246813579", (10.0, 20.0))
    result = C.run_challenge(spec, (10.0, 20.0))
    with pytest.raises(claims.R1082ClaimError):
        result.assert_not_measured()


def test_report_governance_fields():
    r = C.prospective_challenge_report()
    assert r["phase_id"] == "P28"
    assert r["tranche"] == "T07"
    assert r["falsifiable"] is True
    assert r["sealed_before_reveal"] is True
    assert r["swapped_actual_refused"] is True
    assert r["synthetic_suite_has_pass"] is True
    assert r["synthetic_suite_has_failure"] is True
    assert r["famous_place_proximity_rewarded"] is False
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["physical_effects"] == "PHYSICAL_EFFECTS_NOT_CLAIMED"
    assert r["source_origin"] == "SOURCE_ORIGIN_NOT_VALIDATED"
    assert r["verdict"]
