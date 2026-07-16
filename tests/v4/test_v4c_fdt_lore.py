"""Agents M13/M10: FDT quarantine + source-lore translation tests
(gates H8-H10, B5)."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from rscs2_core.source_hypotheses import fdt, lore

REPO = Path(fdt.__file__).resolve().parents[2]

#: default-physics modules that must NEVER import source_hypotheses
DEFAULT_MODULES = [
    "rscs2_core/fem.py", "rscs2_core/quartz.py",
    "rscs2_core/piezo.py", "rscs2_core/projections.py",
    "rscs2_core/eye.py", "rscs2_core/refsystems.py",
    "rscs2_core/crystal110.py", "rscs2_core/accel.py",
    "rscs2_core/proofbundle.py", "rscs2_core/calibration.py",
    "rscs2_core/dynamic_boundary.py",
    "rscs2_core/multiphysics/capabilities.py",
    "rscs2_core/multiphysics/coupling.py",
    "rscs2_core/multiphysics/materials.py",
    "rscs2_core/refmodels/exciton_magnon.py",
    "rscs2_core/refmodels/avoided_crossing.py",
    "rscs2_core/refmodels/iome_linipo4.py",
    "rscs2_core/refmodels/nonlinear_spin.py",
    "rscs2_core/refmodels/metacrystal.py",
    "rscs2_core/refmodels/dynamic_me.py",
]


def test_import_firewall_no_core_module_imports_fdt():
    """Gate H8: dependency scan — no default module imports the
    quarantined namespace."""
    for rel in DEFAULT_MODULES:
        tree = ast.parse((REPO / rel).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            for n in names:
                assert "source_hypotheses" not in n, \
                    f"{rel} imports quarantined namespace"


def test_classification_ceiling_everywhere():
    """Gate H8: every FDT output is SOURCE_HYPOTHESIS + SRC/HYP."""
    out = fdt.force_relation(0.5, 0.5)
    assert out["classification"] == "SOURCE_HYPOTHESIS"
    assert set(out["evidence_tags"]) == {"SRC", "HYP"}
    assert fdt.dimensional_audit()["classification"] == \
        "SOURCE_HYPOTHESIS"
    for p in fdt.prediction_registry():
        assert p["classification"] == "SOURCE_HYPOTHESIS"
    # the M1 ceiling blocks envelope-level laundering too
    from rscs2_core.provenance_v4 import (ProvenanceError,
                                          check_classification)
    with pytest.raises(ProvenanceError):
        check_classification("SRC-V4-18", "REDUCED_ORDER_VALIDATED")


def test_dimensional_audit_and_coefficient():
    aud = fdt.dimensional_audit()
    out = fdt.force_relation(1.0, 1.0)
    assert out["coefficient_newton"] == pytest.approx(
        299792458.0 ** 4 / (4 * 6.67430e-11), rel=1e-12)
    assert out["coefficient_newton"] == pytest.approx(3.026e43,
                                                      rel=1e-3)
    assert aud["force_relation"]["gaps"]          # gaps recorded
    assert "unspecified" in " ".join(
        aud["alpha_r_map"]["gaps"])


def test_alpha_r_invertibility_adds_no_evidence():
    """Gate H8/H9: alpha_R is a bijection of n; the audit says so
    explicitly."""
    for n in (1.0, 1.5443, 2.5):
        assert fdt.alpha_r_inverse(fdt.alpha_r(n)) == \
            pytest.approx(n, rel=1e-12)
    assert 0.0 <= fdt.alpha_r(1.5443) < 1.0
    aud = fdt.algebraic_audit()
    assert aud["alpha_r_is_invertible_bijection"]
    assert "ADDS NO EVIDENCE" in aud["consequence"]
    with pytest.raises(ValueError):
        fdt.alpha_r(0.5)


def test_empirical_audit_and_no_toyoda_confirmation():
    """Gates H9/H10: every claim has a conventional comparator; the
    Toyoda source cannot be used as FDT confirmation."""
    aud = fdt.empirical_audit()
    for claim, rec in aud["claims"].items():
        assert rec["conventional_comparator"], claim
        assert rec["status"] in ("PREDICTION_PENDING", "NO_LOCAL_DATA",
                                 "UNDERDETERMINED")
    assert "may not be cited as confirmation" in aud["toyoda_usage"]


def test_prediction_registry_preregistered_interpretations():
    preds = fdt.prediction_registry()
    assert len(preds) == 6
    for p in preds:
        assert p["if_positive"] and p["if_null"] \
            and p["if_opposite_sign"]
        assert "no exclusive confirmation" in p["if_positive"].lower()


def test_conclusion_linters():
    assert fdt.conclusion_linter(
        "This result PROVES the FDT universal force law") != []
    assert fdt.conclusion_linter(
        "the FDT variant remains a source hypothesis") == []
    hits = lore.conclusion_linter(
        "our derived spectrum confirms the Atlantis machinery")
    assert hits
    ok = lore.conclusion_linter(
        'the source states "the portal opened" (SRC quote) — '
        "we translate this motif only")
    assert ok == []


def test_lore_registry_structure_and_honest_no_analogue():
    rep = lore.registry_report()
    assert rep["n_motifs"] == 9
    assert len(rep["with_analogue"]) == 8
    assert rep["no_useful_analogue"] == ["LORE-09"]   # literal claims
    for m in lore.MOTIFS.values():
        assert m.source_id == "SRC-V4-19"
        assert m.source_locator
        assert m.literal_meaning != m.computational_analogue
        if m.computational_analogue:
            assert m.falsification_condition
    with pytest.raises(ValueError, match="falsification"):
        lore.MotifTranslation("X", "SRC-V4-19", "loc", "x", "lit",
                              "analogue-without-falsifier", None,
                              None, None, None)
