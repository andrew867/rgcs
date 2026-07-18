"""v4.1.0 documentation closeout guards.

The build fails if current documentation reintroduces the retired
4 mm coincidence rule, presents the old verdict as current, claims
missing implementations prove physical nonexistence, or drifts from
the canonical v4.1.0 record (versions, numbers, links)."""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

#: current-facing documentation surfaces
CURRENT_DOCS = [
    "README.md", "CHANGELOG.md", "CITATION.cff",
    "docs/RELEASE_NOTES_V4_1.md", "docs/USER_GUIDE_V4.md",
    "docs/EYE_METHODOLOGY.md", "docs/CANONICAL_110MM_CASE_STUDY.md",
    "docs/RGCS_V4_TECHNICAL_MANUSCRIPT.md",
    "docs/ZENODO_METADATA_V4.md", "docs/V4_API_REFERENCE.md",
    "docs/V4_MODELLING_GUIDE.md",
    "docs/v4/RGCS_V4_1_COMPLETION_MANUSCRIPT.md",
    "docs/v4/WHAT_THIS_QUARTZ_MODEL_DOES_NOT_INCLUDE.md",
    "docs/v4/V4_WHAT_IS_NOT_MODELLED.md",
    "docs/v4/EYE_NODE_COINCIDENCE_CORRECTION.md",
]

#: markers that legitimize a mention of retired wording (correction /
#: history context)
HISTORY_MARKERS = ("V4C-D-001", "historical", "HISTORICAL",
                   "superseded", "retired", "removed", "frozen "
                   "history", "corrects defect", "old rule",
                   "pre-correction")


def _read(rel):
    return (REPO / rel).read_text(encoding="utf-8", errors="ignore")


def test_retired_verdict_and_threshold_only_in_history_context():
    """Any current doc that mentions the retired verdict strings or
    the 4 mm rule must carry an explicit correction/history marker."""
    retired = ("CONVENTIONAL_NODE_FOUND",
               "CONVENTIONAL_NODE_EXPLAINS_RESULT", "3.94 mm",
               "4 mm tolerance", "node_tol_mm = 4")
    for rel in CURRENT_DOCS:
        txt = _read(rel)
        for phrase in retired:
            if phrase in txt:
                assert any(m in txt for m in HISTORY_MARKERS), \
                    f"{rel} mentions retired '{phrase}' without a " \
                    "correction/history marker"


def test_canonical_record_numbers_where_quoted():
    """Docs quoting the canonical Eye record use the corrected
    numbers, and the flagship docs carry the corrected verdict."""
    for rel in ("README.md", "docs/RELEASE_NOTES_V4_1.md",
                "docs/CANONICAL_110MM_CASE_STUDY.md",
                "docs/EYE_METHODOLOGY.md", "docs/USER_GUIDE_V4.md"):
        txt = _read(rel)
        assert "UNCERTAINTY_OVERLAPS_CONVENTIONAL_NODE" in txt, rel
        assert "3.906" in txt, rel
    # the separation is never described as coincident-by-proximity
    for rel in CURRENT_DOCS:
        txt = _read(rel)
        assert not re.search(
            r"within\s+4\s*mm\s+of\s+an\s+ordinary", txt), \
            f"{rel} restores the proximity phrasing"


def test_no_physical_nonexistence_claims():
    """Missing implementation is never presented as proof of physical
    impossibility, and the typed status is named where the firewall is
    described."""
    banned = (r"physically impossible in (alpha )?quartz",
              r"proves? (the )?mechanism (is )?absent",
              r"proof of physical nonexistence\.")
    for rel in CURRENT_DOCS:
        txt = _read(rel)
        low = txt.lower()
        for pat in banned:
            for m in re.finditer(pat, low):
                ctx = low[max(0, m.start() - 120):m.end() + 120]
                assert ("never" in ctx or "not" in ctx
                        or "must not" in ctx), \
                    f"{rel}: affirmative nonexistence claim"
    for rel in ("README.md",
                "docs/v4/WHAT_THIS_QUARTZ_MODEL_DOES_NOT_INCLUDE.md"):
        assert "MECHANISM_NOT_IMPLEMENTED_FOR_MATERIAL" in _read(rel)


VERSION = "4.9.0"


def test_version_consistency():
    py = _read("pyproject.toml")
    assert f'version = "{VERSION}"' in py
    cff = _read("CITATION.cff")
    assert f"version: {VERSION}" in cff
    assert f"releases/tag/v{VERSION}" in cff
    ch = _read("CHANGELOG.md")
    for v in (VERSION, "4.1.1", "4.1.0"):
        assert f"[{v}]" in ch
    readme = _read("README.md")
    assert f"releases/tag/v{VERSION}" in readme
    assert "1840 tests" in readme or "1840 passed" in readme
    assert "115/115" in readme


def test_relative_links_resolve():
    """Markdown relative links in the flagship docs point at files
    that exist (case-exact)."""
    link_re = re.compile(r"\]\((?!https?://|#|mailto:)([^)\s]+)\)")
    for rel in ("README.md", "docs/RELEASE_NOTES_V4_1.md",
                "docs/USER_GUIDE_V4.md",
                "docs/CANONICAL_110MM_CASE_STUDY.md"):
        base = (REPO / rel).parent
        for target in link_re.findall(_read(rel)):
            target = target.split("#")[0]
            if not target:
                continue
            p = (base / target).resolve()
            assert p.exists(), f"{rel}: broken relative link {target}"


def test_reference_systems_not_described_as_quartz_physics():
    """Current docs never call the reduced-order reference systems
    implemented quartz mechanisms."""
    for rel in CURRENT_DOCS:
        txt = _read(rel).lower()
        assert "quartz now supports magnon" not in txt
        assert "quartz iome" not in txt
        assert not re.search(
            r"iome\s+(is\s+)?(now\s+)?implemented\s+(for|in)\s+"
            r"(alpha\s+)?quartz", txt), rel


def test_bundle_verdict_matches_docs():
    """The shipped bundle's machine verdict agrees with the docs."""
    import json
    v = json.loads((REPO / "proof_bundle_110mm/VERDICT.json"
                    ).read_text())
    assert v["verdict"] == "UNCERTAINTY_OVERLAPS_CONVENTIONAL_NODE"
    nc = json.loads((REPO / "proof_bundle_110mm/eye/"
                     "node_coincidence.json").read_text())[0]
    assert abs(nc["separation_mm"] - 3.906) < 5e-3
    assert abs(nc["candidate_mm"][2] - 102.240) < 5e-3
    assert abs(nc["nearest_comparator_mm"][2] - 106.018) < 5e-3
