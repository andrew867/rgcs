"""P19 — calibration freeze and cryptographic receipt.

Schema conformance, the seven frozen parameters, anchor hashes, determinism,
freeze-before-holdout ordering, post-freeze retuning refusal, and the decoder's
receipt requirement.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cwatlas.r1082 import calibration_fit, calibration_freeze as F, claims

SCHEMA_DIR = (Path(__file__).resolve().parents[3]
              / "cwatlas" / "r1082" / "schemas")


@pytest.fixture(scope="module")
def receipt_validator():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(
        (SCHEMA_DIR / "calibration_receipt.schema.json").read_text("utf-8"))
    return jsonschema.Draft202012Validator(schema)


@pytest.fixture(scope="module")
def frozen():
    return F.freeze_calibration(calibration_fit.fit_all())


def test_receipt_conforms_to_schema(frozen, receipt_validator):
    receipt_validator.validate(frozen.receipt())
    r = frozen.receipt()
    assert r["root_profile"] == "EARTH_ROOT_D_V1"
    assert r["retuning_forbidden"] is True
    assert r["freeze_hash"].startswith("sha256:")


def test_receipt_seals_seven_frozen_parameters(frozen):
    fp = frozen.receipt()["parameters"]["frozen"]
    for key in claims.FROZEN_PARAMETERS:
        assert key in fp
    assert len(fp) == len(claims.FROZEN_PARAMETERS) == 7
    # The locked values are the operator-selected ADR values.
    assert fp["grid_rotation"] == "SOUTH_UP"
    assert fp["handedness"] == "CLOCKWISE_FROM_ABOVE_ANTARCTICA"
    assert fp["root_feature"] == "ICOSAHEDRAL_FACE_CENTER"
    assert fp["topology"] == "SPHERICAL_ICOSAHEDRON_20_FACES"
    assert fp["tokenization"] == "FIVE_TOKEN_BASE_100"


def test_receipt_carries_two_training_anchor_hashes(frozen):
    anchors = frozen.receipt()["training_anchors"]
    assert len(anchors) == 2
    names = {a["anchor"] for a in anchors}
    assert "WILKES_FIXED_ROOT" in names
    assert "STONEHENGE_PRIVATE_001" in names
    for a in anchors:
        assert a["hash"]


def test_freeze_hash_deterministic_and_verifies(frozen):
    other = F.freeze_calibration(calibration_fit.fit_all())
    assert frozen.freeze_hash == other.freeze_hash
    assert frozen.receipt_id == other.receipt_id
    assert frozen.verify() is True


def test_freeze_hash_changes_if_a_parameter_changes(frozen):
    # Tampering with a frozen parameter breaks the recomputed hash.
    import dataclasses
    tampered = dataclasses.replace(
        frozen, frozen_parameters={**frozen.frozen_parameters,
                                   "epoch_choice": 9999.0})
    assert tampered.verify() is False


# -- ordering: freeze precedes holdout scoring ------------------------------

def test_negative_holdout_before_freeze_refused():
    session = F.CalibrationSession(calibration_fit.fit_all())
    assert session.is_frozen is False
    with pytest.raises(F.CalibrationOrderError):
        session.score_holdout((1, 2, 3, 4, 5), "F4_ROTATED_DIRECT_LE")


def test_scoring_allowed_after_freeze():
    session = F.CalibrationSession(calibration_fit.fit_all())
    session.freeze()
    assert session.is_frozen is True
    scored = session.score_holdout((1, 2, 3, 4, 5), "F4_ROTATED_DIRECT_LE")
    assert scored["scored_after_freeze"] is True
    assert scored["result_class"] == "CANDIDATE_CALIBRATED_POINT"


# -- no result shopping -----------------------------------------------------

def test_negative_post_freeze_retune_refused(frozen):
    with pytest.raises(claims.R1082ClaimError):
        frozen.refuse_retune("grid_rotation")
    session = F.CalibrationSession(calibration_fit.fit_all())
    # Retuning while still fitting (unfrozen) is permitted (no raise).
    session.retune("grid_rotation")
    session.freeze()
    # After the freeze it is refused.
    with pytest.raises(claims.R1082ClaimError):
        session.retune("grid_rotation")


# -- decoder requires a valid receipt ---------------------------------------

def test_decoder_requires_valid_receipt(frozen):
    F.require_valid_receipt(frozen.receipt())     # valid: no raise
    with pytest.raises(F.CalibrationFreezeError):
        F.require_valid_receipt({})
    with pytest.raises(F.CalibrationFreezeError):
        F.require_valid_receipt({"root_profile": "WRONG",
                                 "retuning_forbidden": True,
                                 "freeze_hash": "x"})
    with pytest.raises(F.CalibrationFreezeError):
        F.require_valid_receipt({"root_profile": "EARTH_ROOT_D_V1",
                                 "retuning_forbidden": False,
                                 "freeze_hash": "x"})


def test_report_seals_claims():
    r = F.calibration_freeze_report()
    assert r["phase_id"] == "P19"
    assert r["retuning_forbidden"] is True
    assert r["freeze_precedes_holdout"] is True
    assert r["post_freeze_retuning"] == "REFUSED"
    assert r["decoder_requires_receipt"] is True
    assert r["receipt_verifies"] is True
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["physical_effects"] == "PHYSICAL_EFFECTS_NOT_CLAIMED"
    assert r["source_origin"] == "SOURCE_ORIGIN_NOT_VALIDATED"
