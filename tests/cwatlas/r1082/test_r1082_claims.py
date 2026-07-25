"""R10.8.2 governance core: evidence/result taxonomy and locked-root refusals."""

from __future__ import annotations

import pytest

from cwatlas.r1082 import claims as C


def test_seven_evidence_and_seven_result_classes():
    assert len(list(C.EvidenceClass)) == 7
    assert len(list(C.ResultClass)) == 7
    assert C.EvidenceClass.MEASURED in C.MEASUREMENT_EVIDENCE
    assert C.MAX_CANDIDATE_EVIDENCE not in C.MEASUREMENT_EVIDENCE


def test_candidate_ceiling_is_calibrated_candidate():
    assert C.MAX_CANDIDATE_EVIDENCE is C.EvidenceClass.CALIBRATED_CANDIDATE


def test_candidate_is_not_measured():
    with pytest.raises(C.R1082ClaimError):
        C.refuse_candidate_as_measured(C.ResultClass.CANDIDATE_CALIBRATED_POINT)


def test_post_freeze_retune_is_refused():
    with pytest.raises(C.R1082ClaimError):
        C.refuse_post_output_retuning("handedness", frozen=True)
    # before a freeze, adjusting is allowed (no raise)
    C.refuse_post_output_retuning("handedness", frozen=False)


def test_shell_supplies_altitude():
    with pytest.raises(C.R1082ClaimError):
        C.refuse_altitude_missing_when_shell_present(shell_state=3)
    C.refuse_altitude_missing_when_shell_present(shell_state=None)  # ok


@pytest.mark.parametrize("name", [
    "candidate_as_measured", "source_origin_validated", "nonhuman_origin",
    "physical_effect", "post_output_retuning",
    "altitude_missing_when_shell_present", "source_as_geographic",
])
def test_every_forbidden_promotion_raises(name):
    with pytest.raises(Exception):
        C.FORBIDDEN_PROMOTIONS[name]()


def test_report_seals_origin_and_effects():
    r = C.claims_report()
    assert r["source_origin"] == "SOURCE_ORIGIN_NOT_VALIDATED"
    assert r["physical_effects"] == "PHYSICAL_EFFECTS_NOT_CLAIMED"
    assert r["measured_here"] == "nothing"
    assert r["max_candidate_evidence"] == "CALIBRATED_CANDIDATE"
    assert len(C.FROZEN_PARAMETERS) == 7
