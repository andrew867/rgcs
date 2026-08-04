"""Terra public-release filter -- exclusion wins, archives are respected."""

from __future__ import annotations

import pytest

from rgcs_terra_release import release_filter as RF


REQUIRED_RC_TERMS = (
    "crabwood", "cnt", "carbon nanotube", "ascii", "plaintext", "message decode",
    "message decoding", "decoded message", "glyph message",
    "private comms", "deuterium", "tritium", "heavy water", "neutron",
    "fusion", "transmutation", "helium generation", "reactor",
    "UHV gas fill",
)


@pytest.mark.parametrize("bad", [
    "docs/Crabwood_message.md", "notes/ascii_dump.txt",
    "x/plaintext_read.md", "y/message_decode_run.py",
    "z/message-decoding-notes.md", "g/glyph_message_table.csv",
    "p/private_comms_log.md",
])
def test_every_declared_exclusion_term_excludes(bad):
    assert RF.classify(bad)["class"] == RF.CLASS_EXCLUDED


@pytest.mark.parametrize("term", REQUIRED_RC_TERMS)
def test_every_rc_term_excludes_from_file_content(term):
    row = RF.classify("docs/coordinate_public.md", content=f"prefix {term} suffix")
    assert row["class"] == RF.CLASS_EXCLUDED
    assert row["excluded_term"]


def test_space_underscore_and_hyphen_variants_are_equivalent():
    assert RF.classify("docs/vector.md", content="heavy_water")["class"] == RF.CLASS_EXCLUDED
    assert RF.classify("docs/vector.md", content="glyph-message")["class"] == RF.CLASS_EXCLUDED


@pytest.mark.parametrize("good", [
    "docs/V1_COORDINATE_SYSTEM.md", "r1053/projector.py",
    "docs/VARIABLE_LENGTH_CODEC.md", "cwatlas/vector_map.json",
])
def test_coordinate_and_codec_material_is_allowed(good):
    assert RF.classify(good)["class"] == RF.CLASS_PUBLIC


def test_exclusion_beats_inclusion_on_conflict():
    """A coordinate doc mentioning Crabwood must NOT be released."""
    r = RF.classify("docs/coordinate_crabwood_comparison.md")
    assert r["class"] == RF.CLASS_EXCLUDED


def test_private_archives_are_reported_not_re_excluded():
    r = RF.classify("internal-docs/plans-v7/crabwood_notes.md")
    assert r["class"] == RF.CLASS_ARCHIVED


def test_tags_participate_in_classification():
    r = RF.classify("docs/innocuous_title.md", tags=("ASCII", "decode"))
    assert r["class"] == RF.CLASS_EXCLUDED


def test_unmatched_paths_go_to_review_not_to_release():
    assert RF.classify("misc/randomfile.bin")["class"] == RF.CLASS_REVIEW


def test_case_insensitivity():
    assert RF.classify("docs/CRABWOOD.md")["class"] == RF.CLASS_EXCLUDED


def test_manifest_is_deterministic_and_report_is_clean():
    paths = ["docs/coordinate_a.md", "docs/Crabwood.md", "misc/blob.bin",
             "internal-docs/x/ascii.md"]
    rows1, rows2 = RF.filter_manifest(paths), RF.filter_manifest(paths)
    assert rows1 == rows2
    rep = RF.release_report(rows1)
    assert rep["total"] == 4
    assert rep["no_excluded_term_released"] is True


def test_real_repo_scan_releases_no_excluded_term():
    """End to end on the live tree: nothing matching an exclusion term is
    classified as releasable."""
    rows = RF.scan_repo_tree(".", subdirs=("docs",))
    assert rows, "docs tree should not be empty"
    rep = RF.release_report(rows)
    assert rep["no_excluded_term_released"] is True
