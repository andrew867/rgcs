"""Release-control tests for the local R10 public candidate."""

from __future__ import annotations

import json
from pathlib import Path

from tools import r10_public_release as release


REQUIRED_TERMS = (
    "crabwood",
    "ascii",
    "plaintext",
    "message decode",
    "decoded message",
    "glyph message",
    "private comms",
    "deuterium",
    "tritium",
    "heavy water",
    "neutron",
    "fusion",
    "transmutation",
    "helium generation",
    "reactor",
    "UHV gas fill",
)


def blob(path: str, content: str = "") -> release.BlobRecord:
    return release.BlobRecord(path, "test", content.encode("utf-8"))


def test_every_required_term_is_an_exclusion() -> None:
    for term in REQUIRED_TERMS:
        row = release.classify_blob(blob("docs/workbench/public.md", term))
        assert row["classification"] == release.CLASS_PRIVATE, term
        assert row["content_excluded_terms"], term


def test_exclusion_beats_explicit_public_inclusion() -> None:
    row = release.classify_blob(
        blob("rgcs_coordinate/codecs/public.py", "decoded message")
    )
    assert row["public_rule"]
    assert row["classification"] == release.CLASS_PRIVATE


def test_unmatched_goes_to_review() -> None:
    row = release.classify_blob(blob("misc/unmatched.bin", "ordinary data"))
    assert row["classification"] == release.CLASS_REVIEW


def test_archive_and_private_lane_prefixes_never_publish() -> None:
    assert (
        release.classify_blob(blob("archive/old/public-map.md"))["classification"]
        == release.CLASS_QUARANTINE
    )
    assert (
        release.classify_blob(blob("r1011/public-looking-codec.py"))["classification"]
        == release.CLASS_QUARANTINE
    )


def test_public_coordinate_file_requires_no_exclusion_hit() -> None:
    row = release.classify_blob(
        blob("rgcs_coordinate/codecs/public.py", "structural vector parser")
    )
    assert row["classification"] == release.CLASS_PUBLIC


def test_mixed_r1073_branch_is_quarantined() -> None:
    classification = release.classify_branch(
        "claude/rgcs-r10-62-terminal-vertex-4aca40",
        ahead=37,
        subject="R10.73",
    )
    assert classification.value == release.CLASS_QUARANTINE


def test_pinned_engineering_commits_are_the_only_default_overlays() -> None:
    assert release.SAFE_OVERLAY_COMMITS == (
        "35312e29c8db1b164975991b1df07a8c8653cd47",
        "4e762851d083c31238f582b4b29497943a1a0407",
        "a10a3bb11a1c05fd6f7676a97ac12b3417d877ec",
        "710e5947c80ea7a2299dc0a40fd63a4262891e39",
        "dfab636c4bf5e165103d7ebc72a693ef828b9987",
    )


def test_generated_report_has_no_public_exclusion_leak() -> None:
    path = Path("docs/release/r10_release_filter_report.json")
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["result"] == "PASS"
    assert report["counts"]["excluded_term_public_leaks"] == 0
