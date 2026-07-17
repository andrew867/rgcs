"""P02 orphan sweep tests: no idea may be silently dropped."""

import importlib.util
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "v4x_orphan_sweep", ROOT / "tools" / "v4x_orphan_sweep.py")
sweep_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sweep_mod)

LEGAL_DISPOSITIONS = {
    "translated_to_model", "translated_to_protocol",
    "translated_to_null", "quarantined_translation",
    "quarantined_private", "quarantined_source", "rejected",
    "preserved_distinct", "preserved_null",
    "preserved_contradiction",
}


@pytest.fixture(scope="module")
def report():
    return sweep_mod.sweep()


def test_every_orphan_has_a_disposition(report):
    """P02: an orphan may be translated, quarantined, or rejected —
    never deleted for sounding implausible."""
    assert not report["undisposed"]
    for row in report["rows"]:
        assert row["disposition"] in LEGAL_DISPOSITIONS, row
        assert row["note"] and len(row["note"]) > 40
        assert row["source"]
        assert row["documentation_path"].endswith(".md")


def test_orphan_ids_are_unique_and_stable(report):
    ids = [r["id"] for r in report["rows"]]
    assert len(ids) == len(set(ids))
    assert all(i.startswith("ORPHAN-") for i in ids)


def test_coverage_grew_beyond_the_fixed_248(report):
    """The fixed ledger was never a proof of completeness; the sweep
    is what tests it. 248 must not be preserved just because it was
    previously reported."""
    assert report["ledger_ids_fixed"] == 248
    assert report["orphans_found"] > 0
    assert report["total_coverage_after_sweep"] == \
        248 + report["orphans_found"]


def test_distinct_source_values_are_not_merged(report):
    """P02 boundary: do not silently merge distinct values. The two
    angle conventions differ by 0.0212 deg and must stay separate."""
    row = next(r for r in report["rows"] if r["id"] == "ORPHAN-011")
    assert row["disposition"] == "preserved_distinct"
    assert "51.843" in row["title"] and "51.8642" in row["title"]
    assert "0.0212" in row["note"]


def test_nulls_and_contradictions_preserved(report):
    """G48: a null result is not a failed project."""
    nul = next(r for r in report["rows"] if r["id"] == "ORPHAN-016")
    assert nul["disposition"] == "preserved_null"
    assert nul["status"] == "EXPERIMENTALLY_NULL"
    con = next(r for r in report["rows"] if r["id"] == "ORPHAN-017")
    assert con["disposition"] == "preserved_contradiction"
    assert con["status"] == "INCONCLUSIVE"


def test_private_myth_orphans_stay_private():
    """G38: portal/Atlantis/CERN motifs are retained, unendorsed, and
    routed to the private-myth policy — not to a physics document."""
    rep = sweep_mod.sweep()
    for oid in ("ORPHAN-006", "ORPHAN-007"):
        row = next(r for r in rep["rows"] if r["id"] == oid)
        assert row["disposition"] == "quarantined_private"
        assert "PHENOMENOLOGY" in row["documentation_path"]


def test_rejected_orphan_cites_evidence():
    """A rejection must cite a measurement, not a preference: the cusp
    'singularity' is rejected because the concentration is finite
    (10.576x), not because it sounds implausible."""
    rep = sweep_mod.sweep()
    row = next(r for r in rep["rows"] if r["id"] == "ORPHAN-009")
    assert row["status"] == "REJECTED_BY_EVIDENCE"
    assert "10.576" in row["note"] and "FINITE" in row["note"]


def test_missing_capability_is_not_nonexistence():
    """ORPHAN-004: phase conjugation is MECHANISM_NOT_IMPLEMENTED_FOR_
    MATERIAL, which is explicitly NOT a claim of nonexistence."""
    rep = sweep_mod.sweep()
    row = next(r for r in rep["rows"] if r["id"] == "ORPHAN-004")
    assert row["status"] == "MECHANISM_NOT_IMPLEMENTED_FOR_MATERIAL"
    assert "NOT a claim that" in row["note"]
