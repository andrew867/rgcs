"""Design Studio documentation guards (plan pack 10_TESTS)."""

from pathlib import Path

import re

REPO = Path(__file__).resolve().parents[2]

REQUIRED_DOCS = [
    "INSTALL.md",
    "docs/user/DESIGN_STUDIO.md",
    "docs/user/CRYSTAL_VALIDATOR.md",
    "docs/user/CERTIFICATION_SHEETS.md",
    "docs/user/PHYRLL_GENERATOR_DESIGNER.md",
    "docs/user/COIL_PULSE_DESIGNER.md",
    "docs/user/ANNULAR_RING_DESIGNER.md",
    "docs/user/FREQUENCY_KEYS.md",
    "docs/user/ADVANCED_MODE.md",
    "docs/developer/PACKAGING.md",
]


def test_design_studio_docs_exist():
    for rel in REQUIRED_DOCS:
        assert (REPO / rel).is_file(), rel


def test_readme_has_design_studio_start_by_task():
    text = (REPO / "README.md").read_text(encoding="utf-8")
    assert "## RGCS Design Studio" in text
    assert "### Start by task" in text
    assert "Crystal Validator" in text
    assert "rgcs-workbench" in text


def test_docs_index_has_design_studio_section():
    text = (REPO / "docs" / "README.md").read_text(encoding="utf-8")
    assert "## Start here — Design Studio" in text
    for rel in REQUIRED_DOCS:
        name = Path(rel).name
        assert name in text, f"docs index should link {name}"


def test_design_studio_doc_relative_links_resolve():
    for rel in REQUIRED_DOCS:
        doc = REPO / rel
        text = doc.read_text(encoding="utf-8")
        for target in re.findall(r"\]\(([^)#]+)(?:#[^)]*)?\)", text):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (doc.parent / target).resolve()
            assert resolved.exists(), f"{rel} links to missing {target}"


def test_design_studio_docs_carry_claim_boundaries():
    for rel in REQUIRED_DOCS:
        if rel in ("INSTALL.md", "docs/developer/PACKAGING.md", "docs/user/ADVANCED_MODE.md"):
            continue
        text = (REPO / rel).read_text(encoding="utf-8").lower()
        assert "claim boundary" in text or "claim-boundary" in text, rel
