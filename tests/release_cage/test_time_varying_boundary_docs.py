"""Groups D and E: boundary-accounting docs and bench-plan sanity."""

from __future__ import annotations

import pathlib

from rgcs_workbench.public_cage import physics_spine as PS

ROOT = pathlib.Path(__file__).resolve().parents[2]
RESEARCH = ROOT / "docs" / "research"

DOCS = (
    "physics_spine.md",
    "time_varying_boundaries.md",
    "angular_momentum_biased_rings.md",
    "phonon_boundary_engine.md",
    "contractor_control_research_map.md",
)

REQUIRED_SECTIONS = ("Purpose", "External anchors", "RGCS operator",
                     "Bench observables", "Claim boundary", "Next tests")


def _read(name: str) -> str:
    return (RESEARCH / name).read_text(encoding="utf-8")


def test_all_five_research_docs_exist_with_required_sections():
    for name in DOCS:
        text = _read(name)
        for section in REQUIRED_SECTIONS:
            assert f"## {section}" in text, f"{name} lacks {section}"


def test_boundary_docs_carry_energy_and_momentum_accounting():
    for name in ("time_varying_boundaries.md",
                 "phonon_boundary_engine.md"):
        text = _read(name).lower()
        assert "switching work supplies or removes energy" in text, name
        assert "sideband" in text, name
        assert "momentum ledger" in text, name
        assert "dce is an analogy, not a power claim" in text, name


def test_no_doc_offers_lift_or_propulsion_as_first_validation():
    for name in DOCS:
        text = _read(name).lower()
        assert "first validation is lift" not in text
        assert "first validation is thrust" not in text
        for line in text.splitlines():
            if "first" in line and "validation" in line:
                assert "lift" not in line and "thrust" not in line \
                    or "not" in line, (name, line)


def test_first_stage_observables_match_the_approved_list():
    approved = set(PS.load_spine()["approved_observables"])
    for entry in PS.load_spine()["entries"]:
        for obs in entry["observables"]:
            assert obs in approved, (entry["id"], obs)


def test_docs_never_use_em_or_en_dashes():
    em_dash, en_dash = "—", "–"
    for name in DOCS:
        text = _read(name)
        assert em_dash not in text and en_dash not in text, name


def test_terra_rc4_reference_remains_frozen():
    from rgcs_workbench.public_cage import terra_frozen as TF
    assert TF.TERRA_RC4_COMMIT == (
        "4fdee3e7fbdb416d8e4b32dcb422d0977e6f20af")
    assert TF.PHYSICAL_ENDPOINT_VALIDATED is False
