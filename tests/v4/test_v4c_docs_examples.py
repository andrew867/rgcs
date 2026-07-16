"""Agent D1: docs completeness, example execution, provenance-ID
resolution, claim-wording linters over the completion doc set."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
DOCS = REPO / "docs" / "v4"

REQUIRED_DOCS = [
    "V4C_DECISION_LOG.md", "V4_MULTIPHYSICS_MODEL.md",
    "V4_MATERIAL_CAPABILITY_MATRIX.md",
    "V4_TORSION_AND_CHIRALITY_TAXONOMY.md",
    "V4_SPIN_EXCITON_MAGNON_PHONON_MODELS.md",
    "V4_DYNAMIC_MAGNETOELECTRIC_MODEL.md",
    "V4_DYNAMIC_BOUNDARY_AND_SYMMETRY_MODELS.md",
    "V4_QUANTUM_STATISTICAL_METACRYSTAL_EXAMPLE.md",
    "V4_ADAPTIVE_CALIBRATION.md", "V4_FERROTOROIDIC_IOME_MODEL.md",
    "V4_FDT_SOURCE_HYPOTHESIS_ADAPTER.md",
    "V4_OPTICAL_CHANNEL_TAXONOMY.md", "V4_WHAT_IS_NOT_MODELLED.md",
    "WHAT_THIS_QUARTZ_MODEL_DOES_NOT_INCLUDE.md",
    "EYE_NODE_COINCIDENCE_CORRECTION.md",
    "baseline/V4_BASELINE_AUTHORITY_MAP.md",
    "provenance/NEW_ADAPTATION_MATRIX.md",
    "provenance/NEW_EXCLUSION_MATRIX.md",
]


def test_required_documents_exist_and_nonempty():
    for rel in REQUIRED_DOCS:
        p = DOCS / rel
        assert p.exists(), rel
        assert len(p.read_text(encoding="utf-8")) > 400, rel


def test_examples_execute():
    for ex in sorted((DOCS / "examples").glob("example_*.py")):
        r = subprocess.run([sys.executable, str(ex)],
                           capture_output=True, text=True, cwd=REPO,
                           timeout=300)
        assert r.returncode == 0, f"{ex.name}: {r.stderr[-800:]}"
        assert r.stdout.strip(), ex.name


def test_provenance_ids_resolve_across_docs_and_code():
    from rscs2_core.provenance_v4 import lint_provenance_ids
    paths = list(DOCS.rglob("*.md")) + \
        list((REPO / "rscs2_core").rglob("*.py"))
    paths = [p for p in paths if "M9-precorrection" not in str(p)]
    assert lint_provenance_ids(paths) == []


def test_no_fdt_or_lore_promotion_in_public_docs():
    from rscs2_core.source_hypotheses.fdt import conclusion_linter
    for p in DOCS.rglob("*.md"):
        hits = conclusion_linter(p.read_text(encoding="utf-8"))
        assert hits == [], f"{p}: {hits}"


def test_scope_statement_carries_the_binding_rules():
    txt = " ".join((DOCS / "WHAT_THIS_QUARTZ_MODEL_DOES_NOT_INCLUDE"
                    ".md").read_text(encoding="utf-8").split())
    for phrase in ("not be interpreted as proof",
                   "3.94 mm must be reported as 3.94 mm",
                   "must never be collapsed",
                   "CANDIDATE_NEW_COUPLING",
                   "MECHANISM_NOT_IMPLEMENTED_FOR_MATERIAL"):
        assert phrase in txt, phrase
