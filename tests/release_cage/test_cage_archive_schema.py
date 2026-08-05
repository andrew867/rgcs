"""MOD-007 archive schema -- the six spec tests."""

from __future__ import annotations

import pytest

from rgcs_workbench.public_cage import archive_schema as AS


def _record(**overrides):
    record = {
        "record_id": "ARC-0001",
        "source_type": "PUBLIC_WEB",
        "original_url": "https://example.org/page",
        "access_datetime": "2026-08-01T12:00:00Z",
        "local_datetime": "2026-08-01T08:00:00-04:00",
        "title": "Example page",
        "author_or_channel": "example author",
        "capture_method": "single-file page capture",
        "raw_file_hash": "f" * 64,
        "rendered_file_hash": "e" * 64,
        "transcript_hash": "NOT_APPLICABLE",
        "operator_note_hash": "d" * 64,
        "repost_status": "ORIGINAL",
        "redirect_status": "NO_REDIRECT",
        "copyright_status_note": "publicly posted; fair-dealing archive",
        "claim_boundary": "archived statement, not a validated claim",
    }
    record.update(overrides)
    return record


def test_1_no_record_lacks_a_source_type():
    assert AS.validate_record(_record()) == []
    problems = AS.validate_record(_record(source_type=""))
    assert any("source_type" in p for p in problems)
    problems = AS.validate_record(_record(source_type="MADE_UP"))
    assert any("unknown source_type" in p for p in problems)


def test_2_no_mirrored_file_lacks_a_hash():
    problems = AS.validate_record(_record(
        source_type="MIRRORED_PUBLIC_WEB", raw_file_hash="NONE"))
    assert any("mirrored" in p for p in problems)
    assert AS.validate_record(_record(
        source_type="MIRRORED_PUBLIC_WEB")) == []


def test_3_community_submissions_start_unverified():
    entry = AS.community_intake({"record_id": "ARC-0002",
                                 "source_type": "PUBLIC_WEB",
                                 "verified": True})
    assert entry["source_type"] == "COMMUNITY_SUBMISSION_UNVERIFIED"
    assert entry["verified"] is False
    assert entry["promotion_steps_completed"] == []


def test_3b_promotion_requires_all_four_steps():
    entry = AS.community_intake({"record_id": "ARC-0003"})
    with pytest.raises(AS.PromotionRefused, match="technical_claim"):
        AS.promote_community_submission(
            entry, ["original_source_recovery", "timestamp_capture",
                    "duplicate_check"])
    promoted = AS.promote_community_submission(
        entry, list(AS.PROMOTION_STEPS))
    assert promoted["verified"] is True


def test_4_redirects_and_dead_links_are_explicit():
    problems = AS.validate_record(_record(redirect_status=""))
    assert any("redirect_status" in p for p in problems)
    assert AS.validate_record(_record(redirect_status="DEAD_LINK")) == []


def test_5_reposts_are_not_merged_into_originals():
    problems = AS.validate_record(_record(source_type="THIRD_PARTY_REPOST"))
    assert any("reference the original" in p for p in problems)
    assert AS.validate_record(_record(
        source_type="THIRD_PARTY_REPOST",
        repost_of_record_id="ARC-0001")) == []


def test_6_interpretation_stays_separate_from_extraction():
    """claim_boundary is a required field: every archived record must
    state that archiving is not validation."""
    problems = AS.validate_record(_record(claim_boundary=""))
    assert any("claim_boundary" in p for p in problems)
