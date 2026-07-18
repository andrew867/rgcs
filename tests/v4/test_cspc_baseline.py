"""A00 (v4.6 CSCP): baseline, doctrine constants, and the source-hash
line-ending regression.

Positive tests cover the public behaviour introduced; negative tests
cover the claim boundaries (software may never emit a physical
evidence class).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "docs" / "v4" / "cspc" / "BASELINE_V4_6.json"


# --- doctrine constants -------------------------------------------------

def test_evidence_ladder_and_firewalls_present():
    import cspc
    assert cspc.EVIDENCE_CLASSES[0] == "LORE"
    for needed in ("SOURCE_CLAIM", "DERIVED_ARITHMETIC",
                   "BENCH_MEASUREMENT", "UNSUPPORTED"):
        assert needed in cspc.EVIDENCE_CLASSES
    # all eight mandatory transfer firewalls (core/04)
    assert len(cspc.TRANSFER_FIREWALLS) == 8
    for key in ("ARITHMETIC_TO_SPECTRUM", "TEMPORAL_ORDER_TO_TRAVEL",
                "CLOCK_SHIFT_TO_METRIC_CONTROL",
                "SOURCE_PRECISION_TO_MEASUREMENT_PRECISION"):
        assert key in cspc.TRANSFER_FIREWALLS
        assert cspc.TRANSFER_FIREWALLS[key].strip()


def test_excluded_claims_cover_the_charter_prohibitions():
    import cspc
    joined = " | ".join(cspc.EXCLUDED_CLAIMS).lower()
    for phrase in ("time travel", "superluminal", "wormhole",
                   "negative-energy", "metric engineering",
                   "consciousness transfer"):
        assert phrase in joined


def test_validate_evidence_class_accepts_legal_and_rejects_junk():
    import cspc
    assert cspc.validate_evidence_class("DERIVED_ARITHMETIC") == \
        "DERIVED_ARITHMETIC"
    with pytest.raises(cspc.ClaimBoundaryError):
        cspc.validate_evidence_class("PROVEN")


# --- negative / refusal tests (claim boundary) --------------------------

@pytest.mark.parametrize("cls", ["BENCH_MEASUREMENT",
                                 "REPLICATED_MEASUREMENT"])
def test_software_may_not_emit_a_physical_evidence_class(cls):
    """The load-bearing refusal: a green software lane is not a
    measurement."""
    import cspc
    with pytest.raises(cspc.ClaimBoundaryError):
        cspc.require_non_physical(cls, context="unit test")


def test_require_non_physical_allows_modelling_classes():
    import cspc
    for cls in ("DERIVED_ARITHMETIC", "ANALYTIC_MODEL",
                "NUMERICAL_SIMULATION", "SYNTHETIC_RUN"):
        assert cspc.require_non_physical(cls) == cls


# --- source-hash regression (line endings) ------------------------------

def test_source_hash_is_line_ending_invariant(tmp_path):
    """Regression: git checkouts on Windows (core.autocrlf=true)
    re-materialise .py files with CRLF. A raw-byte hash then reports a
    spurious mismatch for identical source, which would fail
    --build-info verification for a genuinely fresh binary."""
    from rgcs_desktop.build_meta import compute_source_hash
    body = "x = 1\ny = 2\n"
    for name, text in (("lf", body), ("crlf", body.replace("\n", "\r\n"))):
        repo = tmp_path / name
        (repo / "cspc").mkdir(parents=True)
        (repo / "cspc" / "m.py").write_bytes(text.encode())
        (repo / "cspc" / "__init__.py").write_bytes(text.encode())
    assert compute_source_hash(tmp_path / "lf") == \
        compute_source_hash(tmp_path / "crlf")


def test_source_hash_still_changes_on_real_edit(tmp_path):
    """Fail-safe preserved: normalising line endings must not blind the
    hash to an actual source change."""
    from rgcs_desktop.build_meta import compute_source_hash
    repo = tmp_path / "r"
    (repo / "cspc").mkdir(parents=True)
    f = repo / "cspc" / "__init__.py"
    f.write_text("x = 1\n")
    first = compute_source_hash(repo)
    f.write_text("x = 2\n")
    assert compute_source_hash(repo) != first


def test_cspc_is_a_tracked_source_root():
    """A change to the v4.6 package must invalidate a frozen binary."""
    from rgcs_desktop.build_meta import SOURCE_ROOTS
    assert "cspc" in SOURCE_ROOTS


# --- baseline artifact --------------------------------------------------

def test_baseline_exists_and_is_honest():
    assert BASELINE.exists(), "run tools/cspc_baseline.py"
    b = json.loads(BASELINE.read_text(encoding="utf-8"))
    assert b["programme"] == "RGCS-V4.6-CSCP"
    assert b["evidence_class"] == "RELEASE_EVIDENCE"
    assert b["physical_status"] == "UNTESTED"
    assert b["binary_freshness"]["state"] in {"FRESH", "STALE", "ABSENT"}
    assert len(b["source_hash"]) == 64
    assert b["test_command"].startswith("python -m pytest")


def test_baseline_claims_nothing_physical():
    text = BASELINE.read_text(encoding="utf-8").lower()
    for word in ("proves", "portal", "warp", "activation"):
        assert word not in text
