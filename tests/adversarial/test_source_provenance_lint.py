"""Machine lint for Agent 02 source/provenance deliverables.

Enforces the integrity rules that must hold before Agents 03-08 build on
the frozen notation (Quality Gates 2-4): every source has a real sha256 and
a forbidden-transfer boundary; every provenance equation names a known
source, a location, and both an allowed adaptation and a forbidden
transfer; the reference PDFs still hash to the recorded values.
"""
from __future__ import annotations

import hashlib
import pathlib

import pytest
import yaml

REPO = pathlib.Path(__file__).resolve().parents[2]
REFS = REPO / "references"
PDF_DIR = REPO / "internal-docs" / "plans-v3" / "reference_documents"

VALID_CLASSES = {"EST", "DER", "HYP", "SRC", "ENG"}


def _load(name):
    with open(REFS / name, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@pytest.fixture(scope="module")
def sources():
    return _load("source_registry.yaml")["sources"]


@pytest.fixture(scope="module")
def equations():
    return _load("equation_provenance.yaml")["equations"]


def test_source_ids_unique_and_complete(sources):
    ids = [s["source_id"] for s in sources]
    assert len(ids) == len(set(ids)), "duplicate source_id"
    for s in sources:
        assert s["title"] and s["authors"], s["source_id"]
        assert len(s["sha256"]) == 64, f"{s['source_id']} sha256 malformed"
        assert s["forbidden_transfer"], f"{s['source_id']} needs a boundary"


def test_no_fabricated_and_et_al(sources):
    # QA-D-01/02 rule: author lists are explicit, never "and et al."
    for s in sources:
        for a in s["authors"]:
            assert "et al" not in a.lower(), f"{s['source_id']}: {a!r}"


def test_reference_pdf_hashes_match(sources):
    if not PDF_DIR.exists():
        pytest.skip("reference PDFs not present (packaged separately)")
    for s in sources:
        pdf = REPO / s["file"]
        if not pdf.exists():
            pytest.skip(f"missing {s['file']}")
        got = hashlib.sha256(pdf.read_bytes()).hexdigest()
        assert got == s["sha256"], f"{s['source_id']} hash drift"


def test_every_equation_has_full_provenance(equations, sources):
    known = {s["source_id"] for s in sources}
    seen = set()
    for e in equations:
        pid = e["prov_id"]
        assert pid not in seen, f"duplicate prov_id {pid}"
        seen.add(pid)
        assert e["source_id"] in known, f"{pid} unknown source"
        assert e["location"].get("page"), f"{pid} needs a page"
        assert e["allowed_adaptation"], f"{pid} needs allowed_adaptation"
        assert e["forbidden_transfer"], f"{pid} needs forbidden_transfer"
        assert e["target_rscs"], f"{pid} needs a target_rscs reservation"


def test_all_substantive_sources_have_equations(equations):
    covered = {e["source_id"] for e in equations}
    # SRC-3-09 is a slide deck (context only); the other eight must appear.
    required = {f"SRC-3-0{i}" for i in range(1, 9)}
    assert required <= covered, f"missing provenance for {required - covered}"


def test_notation_ledger_present_and_frozen():
    led = REPO / "docs" / "RSCS_NOTATION_LEDGER.md"
    text = led.read_text(encoding="utf-8")
    assert "GATE FOR AGENTS 03" in text or "GATE: OPEN" in text
    assert "K = i·2πg" in text, "frozen coupling convention must be stated"
