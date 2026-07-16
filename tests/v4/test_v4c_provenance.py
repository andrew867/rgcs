"""Agent M1: provenance layer enforcement tests (gates B1-B5)."""
from __future__ import annotations

from pathlib import Path

import pytest

from rscs2_core import provenance_v4 as pv
from rscs2_core.provenance_v4 import ProvenanceError

REPO = Path(pv.__file__).resolve().parents[1]


def test_registry_loads_and_has_required_records():
    src = pv.load_sources()
    for sid in ("SRC-V4-00", "SRC-V4-01", "SRC-V4-02", "SRC-V4-03",
                "SRC-V4-04", "SRC-V4-18", "SRC-V4-19"):
        assert sid in src
    # News & Views is mandated preview-only (gate H10/B3)
    assert src["SRC-V4-02"].access_status == \
        "ACCESS_RESTRICTED_PREVIEW_ONLY"
    # no guessed hashes: every non-local record has null sha256 (B1
    # applies to LOCAL sources; absent files carry null, DV4C-003)
    for rec in src.values():
        if rec.raw.get("local_filename") is None:
            assert rec.raw.get("sha256") is None, rec.source_id


def test_equation_ledger_complete_and_linked():
    eqs = pv.load_equations()
    src = pv.load_sources()
    assert len(eqs) >= 15
    for eq in eqs.values():
        assert eq["source_id"] in src, eq["equation_id"]
        assert eq["units_check"]
        assert eq["classification"] in pv.CLASS_ORDER
        # ledger classification respects the source ceiling (B5)
        pv.check_classification(eq["source_id"], eq["classification"],
                                src)


def test_ceilings_block_laundering():
    """SRC/HYP sources can never yield CORE_VALIDATED (B5)."""
    with pytest.raises(ProvenanceError, match="laundering"):
        pv.check_classification("SRC-V4-18", "CORE_VALIDATED")
    with pytest.raises(ProvenanceError, match="laundering"):
        pv.check_classification("SRC-V4-19",
                                "REDUCED_ORDER_VALIDATED")
    with pytest.raises(ProvenanceError, match="laundering"):
        pv.check_classification("SRC-V4-02",
                                "REDUCED_ORDER_VALIDATED")
    # primary paper may ground REDUCED_ORDER_VALIDATED
    pv.check_classification("SRC-V4-01", "REDUCED_ORDER_VALIDATED")


def test_source_hierarchy_primary_outranks_commentary():
    assert pv.resolve_precedence(["SRC-V4-02", "SRC-V4-01"]) == \
        "SRC-V4-01"                                   # gate B4
    assert pv.resolve_precedence(["SRC-V4-19", "SRC-V4-18",
                                  "SRC-V4-03"]) == "SRC-V4-03"


def test_forbidden_transfers():
    with pytest.raises(ProvenanceError, match="forbidden"):
        pv.check_transfer("SRC-V4-01", "material.alpha_quartz")
    with pytest.raises(ProvenanceError, match="forbidden"):
        pv.check_transfer("SRC-V4-18", "default_solver.fem")
    with pytest.raises(ProvenanceError, match="forbidden"):
        pv.check_transfer("SRC-V4-05",
                          "proton_tunnelling_from_continuum")
    pv.check_transfer("SRC-V4-01", "material.linipo4")  # allowed


def test_quartz_mechanism_exclusions():
    for mech in ("magnetic_order", "magnon_modes",
                 "exciton_magnon_coupling", "ferrotoroidic_order",
                 "magnetoelectric_dynamic", "domain_writing",
                 "spacetime_torsion",
                 "quantum_statistical_response"):
        assert not pv.quartz_mechanism_allowed(mech), mech
    for mech in ("elasticity_anisotropic", "piezoelectric",
                 "photoelastic", "optical_birefringent"):
        assert pv.quartz_mechanism_allowed(mech), mech


def test_release_filter_blocks_restricted_pdfs(tmp_path):
    """A v3-registered restricted PDF placed in release staging is
    detected (B3)."""
    staged = tmp_path / "2104.04803v2.pdf"
    staged.write_bytes(b"not really the pdf")
    violations = pv.release_filter([staged])
    assert violations and "2104.04803v2.pdf" in violations[0]
    ok = tmp_path / "figure.pdf"
    ok.write_bytes(b"generated figure")
    assert pv.release_filter([ok]) == []


def test_linter_flags_unresolved_ids(tmp_path):
    good = tmp_path / "good.py"
    good.write_text("# uses SRC-V4-01 and RGCS-V4-EQ-002\n")
    bad = tmp_path / "bad.py"
    bad.write_text("# cites SRC-V4-99 which does not exist\n")
    assert pv.lint_provenance_ids([good]) == []
    out = pv.lint_provenance_ids([bad])
    assert out and "SRC-V4-99" in out[0]


def test_ingest_upgrades_and_diff_refuses_silent_replacement(tmp_path):
    import shutil
    reg = tmp_path / "reg.yaml"
    shutil.copy(pv.SRC_REGISTRY, reg)
    f = tmp_path / "toyoda.pdf"
    f.write_bytes(b"full text placeholder bytes")
    rec = pv.ingest_file("SRC-V4-01", f, registry_path=reg)
    assert rec["access_status"] == "FULL_TEXT_LOCAL"
    assert len(rec["sha256"]) == 64
    # same name, changed content -> refuse (source-diff tool)
    f.write_bytes(b"DIFFERENT content")
    with pytest.raises(ProvenanceError, match="content change"):
        pv.ingest_file("SRC-V4-01", f, registry_path=reg)


def test_no_restricted_source_in_current_release_assets():
    """Live audit: nothing under release/ or proof_bundle_110mm is a
    registered restricted source PDF."""
    staged = list((REPO / "proof_bundle_110mm").rglob("*.pdf")) + \
        list((REPO / "release").rglob("*.pdf")) if \
        (REPO / "release").exists() else \
        list((REPO / "proof_bundle_110mm").rglob("*.pdf"))
    assert pv.release_filter(staged) == []


def test_v3_registry_untouched():
    """M1 links, never edits, the frozen v3 registry (DV4C-006)."""
    import subprocess
    out = subprocess.run(
        ["git", "diff", "HEAD", "--", "references/"],
        capture_output=True, text=True, cwd=REPO)
    assert out.stdout.strip() == ""
