"""Crystal Validator service tests (plan pack 04_MODULE_SPECS)."""
import json
from pathlib import Path

from rgcs_desktop.services.crystal_validator import (
    derive_crystal_geometry, export_specimen_json, make_crystal_diagram,
    specimen_receipt_json, validate_specimen)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "design_studio"


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_minimal_valid_specimen_passes():
    result = validate_specimen(load("crystal_valid_minimal.json"))
    assert result.ok, result.errors
    # optional measurements are reported as missing, not as errors
    assert "mass_g" in result.missing_optional


def test_missing_dimensions_fail():
    spec = load("crystal_valid_minimal.json")
    del spec["dimensions"]["diameter_mm"]
    result = validate_specimen(spec)
    assert not result.ok


def test_uncertainty_required():
    spec = load("crystal_valid_minimal.json")
    spec["uncertainty"].pop("length_mm")
    result = validate_specimen(spec)
    assert not result.ok


def test_node_outside_length_refused():
    spec = load("crystal_with_nodes.json")
    spec["measured_nodes_mm"].append(500.0)
    result = validate_specimen(spec)
    assert not result.ok


def test_derived_geometry():
    spec = load("crystal_with_nodes.json")
    derived = derive_crystal_geometry(spec)
    assert derived["aspect_ratio"] == 110.0 / 32.0
    assert derived["length_to_diameter_ratio"] == 110.0 / 32.0
    assert "51.7" in derived["termination_angle_status"]
    assert derived["volume_estimate_cm3"] > 0
    assert derived["density_g_cm3"] is not None
    assert "consistent" in derived["density_check"]
    assert derived["axial_half_wave_hz"] == 5720.0 / (2 * 0.110)
    assert derived["classification"] == "MODEL_OUTPUT"


def test_unavailable_estimates_are_none_not_zero():
    spec = load("crystal_valid_minimal.json")
    spec["material_family"] = "unobtainium"
    derived = derive_crystal_geometry(spec)
    assert derived["axial_half_wave_hz"] is None
    assert derived["density_g_cm3"] is None
    assert "unavailable" in derived["density_check"]


def test_json_receipt_deterministic(tmp_path):
    spec = load("crystal_with_nodes.json")
    derived = derive_crystal_geometry(spec)
    a = specimen_receipt_json(spec, derived)
    b = specimen_receipt_json(json.loads(json.dumps(spec)),
                              derive_crystal_geometry(spec))
    assert a == b
    body = json.loads(a)
    assert len(body["sha256"]) == 64
    out = export_specimen_json(spec, derived, tmp_path / "s.json")
    assert out.read_text(encoding="utf-8") == a


def test_svg_contains_length_label(tmp_path):
    spec = load("crystal_with_nodes.json")
    out = make_crystal_diagram(spec, tmp_path / "s.svg")
    svg = out.read_text(encoding="utf-8")
    assert "length 110 mm" in svg
    assert "diameter 32 mm" in svg
    assert spec["specimen_id"] in svg
    # node markers present
    assert "27.5" in svg
