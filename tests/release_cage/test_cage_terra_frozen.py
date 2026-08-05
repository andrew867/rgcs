"""Terra RC4 stays frozen -- metadata exact, promotion impossible.

MOD-002 cage tests (TERRA-001, TERRA-002 in the release matrix).
"""

from __future__ import annotations

import pathlib

import pytest

from rgcs_workbench.public_cage import terra_frozen as TF

ROOT = pathlib.Path(__file__).resolve().parents[2]
NOTES = ROOT / "docs" / "release" / "WORKBENCH_PUBLIC_RC1_CAGE_NOTES.md"


def test_terra_001_rc4_metadata_preserved_exactly():
    assert TF.TERRA_RC4_REPO == "andrew867/rgcs-terra"
    assert TF.TERRA_RC4_TAG == "v1.0.0-rc4"
    assert TF.TERRA_RC4_COMMIT == (
        "4fdee3e7fbdb416d8e4b32dcb422d0977e6f20af")
    assert TF.TERRA_RC4_VERDICT == (
        "GREEN_TERRA_ALIGNMENT_SOLVED_CALIBRATED_V1")


def test_blocker_split_matches_rc4_exactly():
    assert dict(TF.TERRA_RC4_BLOCKERS) == {
        "B01A": "CLOSED",
        "B02A": "CLOSED",
        "B01B": "VALIDATION_PENDING",
        "B02B": "PHYSICAL_VALIDATION_PENDING",
        "B10": "OPEN",
    }


def test_terra_002_no_physical_endpoint_validation_claimed():
    assert TF.PHYSICAL_ENDPOINT_VALIDATED is False
    assert TF.MANUAL_MAP_VERIFICATION is False
    with pytest.raises(TF.PhysicalValidationRefused):
        TF.promote_physical_validation()
    with pytest.raises(TF.PhysicalValidationRefused):
        TF.promote_physical_validation("GREEN", force=True)


@pytest.mark.parametrize("kind", TF.REFUSED_EVIDENCE_KINDS)
def test_map_screenshots_and_source_language_are_not_receipts(kind):
    with pytest.raises(TF.PhysicalValidationRefused):
        TF.accept_validation_evidence(kind)


def test_bench_evidence_enters_review_without_advancing_the_claim():
    row = TF.accept_validation_evidence("bench_receipt")
    assert row["status"] == "REVIEW_ONLY"
    assert row["physical_endpoint_validated"] is False


def test_frozen_profile_returns_a_copy():
    a = TF.frozen_profile()
    a["verdict"] = "TAMPERED"
    a["blockers"]["B10"] = "CLOSED"
    b = TF.frozen_profile()
    assert b["verdict"] == "GREEN_TERRA_ALIGNMENT_SOLVED_CALIBRATED_V1"
    assert b["blockers"]["B10"] == "OPEN"


def test_rc4_tag_and_commit_are_immutable_in_release_notes():
    text = NOTES.read_text(encoding="utf-8")
    assert "v1.0.0-rc4" in text
    assert "4fdee3e7fbdb416d8e4b32dcb422d0977e6f20af" in text
    assert "HOLDOUT_REQUIRED" in text
