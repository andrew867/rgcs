"""Design Studio schema contracts (plan pack 05_DATA_CONTRACTS)."""
import json
from pathlib import Path

import pytest

from rgcs_desktop.services.schemas import validate_instance

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "design_studio"


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize("fixture,schema", [
    ("crystal_valid_minimal.json", "crystal_specimen.schema.json"),
    ("crystal_with_nodes.json", "crystal_specimen.schema.json"),
    ("phryll_generator_basic.json", "phyrll_generator_design.schema.json"),
    ("coil_pulse_925.json", "coil_pulse_design.schema.json"),
    ("annular_ring_37cell.json", "annular_ring_design.schema.json"),
])
def test_fixtures_validate(fixture, schema):
    assert validate_instance(load(fixture), schema) == []


def test_missing_dimensions_fail():
    spec = load("crystal_valid_minimal.json")
    del spec["dimensions"]["length_mm"]
    assert validate_instance(spec, "crystal_specimen.schema.json")


def test_width_or_diameter_required():
    spec = load("crystal_valid_minimal.json")
    del spec["dimensions"]["diameter_mm"]
    assert validate_instance(spec, "crystal_specimen.schema.json")


def test_uncertainty_required():
    spec = load("crystal_valid_minimal.json")
    del spec["uncertainty"]
    assert validate_instance(spec, "crystal_specimen.schema.json")
    spec2 = load("crystal_valid_minimal.json")
    del spec2["uncertainty"]["length_mm"]
    assert validate_instance(spec2, "crystal_specimen.schema.json")


def test_unknown_schema_major_refused():
    spec = load("crystal_valid_minimal.json")
    spec["schema_version"] = "2.0.0"
    errors = validate_instance(spec, "crystal_specimen.schema.json")
    assert errors and "major" in errors[0]


def test_pulse_mode_enum_enforced():
    design = load("coil_pulse_925.json")
    design["pulse"]["mode"] = "freeform"
    assert validate_instance(design, "coil_pulse_design.schema.json")


def test_ring_mask_type_enforced():
    design = load("annular_ring_37cell.json")
    design["active_mask"][0] = "yes"
    assert validate_instance(design, "annular_ring_design.schema.json")
