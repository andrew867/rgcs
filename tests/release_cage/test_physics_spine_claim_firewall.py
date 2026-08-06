"""Group A: the RC2 physics-spine forbidden claims are firewall-live.

Safety scan tests. The phrases below are banned in public claim text
outside refused-claim contexts; this file's name keeps it an allowed
context for its own literals.
"""

from __future__ import annotations

import pathlib

import pytest

from rgcs_workbench.public_cage import claim_firewall as CF

ROOT = pathlib.Path(__file__).resolve().parents[2]

RC2_FORBIDDEN = (
    "validated thrust",
    "external source proven",
    "non-human source authenticated",
    "crop circle authorship proven",
    "positron bench device",
    "DCE power source",
    "CIA has the magic file",
)


@pytest.mark.parametrize("phrase", RC2_FORBIDDEN)
def test_every_rc2_phrase_is_banned(phrase):
    assert phrase in CF.BANNED_PHRASES
    findings = CF.scan_text(f"The device achieved {phrase} today.")
    assert phrase in {f["phrase"] for f in findings}


def test_rc2_phrases_allowed_only_in_refused_contexts():
    text = ("## Forbidden public claims\n\n"
            "validated thrust\nDCE power source\n"
            "positron bench device\n")
    assert CF.scan_text(text) == []
    naked = ("progress\n" * (CF.CONTEXT_WINDOW_BEFORE + 2)
             + "we now have validated thrust")
    assert CF.scan_text(naked)


def test_research_docs_scan_clean():
    docs = sorted((ROOT / "docs" / "research").glob("*.md"))
    assert len(docs) >= 5
    report = CF.firewall_report(CF.scan_paths(docs))
    assert report["clean"], report


def test_full_tree_still_clean_with_extended_list():
    report = CF.firewall_report(CF.scan_tracked_markdown(ROOT))
    assert report["verdict"] == "RELEASE_FILTER_CLEAN", report


def test_cage_surface_includes_ledgers_and_scans_clean():
    surface = CF.cage_public_surface(ROOT)
    names = {p.name for p in surface}
    assert "patent_paper_ledger.json" in names
    assert "patent_paper_ledger.csv" in names
    assert "physics_spine_entries.json" in names
    report = CF.firewall_report(CF.scan_paths(surface))
    assert report["clean"], report
