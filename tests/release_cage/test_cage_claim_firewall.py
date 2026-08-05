"""Release-cage claim firewall -- banned claims stay out of public text.

Safety scan tests for the 2026-08-04 spec pack (CLAIM_SCAN_RULES).
These tests went in BEFORE any physical hypothesis module import, per
the cage ordering rule.
"""

from __future__ import annotations

import pathlib

import pytest

from rgcs_workbench.public_cage import claim_firewall as CF

ROOT = pathlib.Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("phrase", CF.BANNED_PHRASES)
def test_every_banned_phrase_is_detected_in_claim_text(phrase):
    findings = CF.scan_text(f"Our device {phrase} at bench scale.")
    assert findings, f"'{phrase}' escaped the firewall"
    assert findings[0]["phrase"] == phrase
    assert findings[0]["reason"]


def test_separator_variants_are_equivalent():
    assert CF.scan_text("achieves wall_power_thrust now")
    assert CF.scan_text("achieves wall power force output")
    assert CF.scan_text("N-W output validated on bench")


def test_refused_claim_list_under_heading_is_allowed():
    text = "## Refused claims\n\nthrust\nlift\nantigravity\nfree energy\n"
    assert CF.scan_text(text) == []


def test_does_not_claim_sentence_is_allowed():
    text = ("This module does measurement planning. It does not claim "
            "antigravity, free energy, or gravity control.")
    assert CF.scan_text(text) == []


def test_question_is_not_a_claim():
    assert CF.scan_text("Does this create free energy?") == []


def test_positive_claim_far_from_any_marker_is_blocked():
    filler = "line\n" * (CF.CONTEXT_WINDOW_BEFORE + 2)
    text = filler + "The ring produces thrust from wall power."
    findings = CF.scan_text(text)
    assert findings and findings[0]["phrase"] == "produces thrust"


def test_findings_carry_path_line_and_text():
    f = CF.scan_text("x\ny\nreal antigravity achieved", path="doc.md")
    assert f[0]["path"] == "doc.md"
    assert f[0]["line"] == 3
    assert "antigravity" in f[0]["text"]


def test_firewall_files_are_allowed_contexts_by_definition():
    """The spec's allowed-context list names the claim firewall itself."""
    assert CF.scan_text("antigravity", path="claim_firewall.py") == []
    assert CF.scan_text("antigravity", path="x/force_firewall.py") == []


def test_report_verdict_strings():
    assert CF.firewall_report([])["verdict"] == "RELEASE_FILTER_CLEAN"
    dirty = CF.firewall_report([{"phrase": "antigravity"}])
    assert dirty["verdict"] == "RELEASE_BLOCKED_BANNED_CLAIM"
    assert dirty["clean"] is False


def test_cage_public_surface_is_nonempty_and_scans_clean():
    """The live gate: cage files plus top-level public claim docs."""
    surface = CF.cage_public_surface(ROOT)
    assert any(p.name == "README.md" for p in surface)
    assert any(p.name == "module_registry.json" for p in surface)
    report = CF.firewall_report(CF.scan_paths(surface))
    assert report["clean"], report
