"""Phyrll Generator Designer service tests (plan pack 04_MODULE_SPECS)."""
import json
from pathlib import Path

import pytest

from rgcs_desktop.services.phyrll_generator import (
    DesignError, derive_holder_geometry, export_scad, render_scad)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "design_studio"


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def make_design(**overrides):
    spec = load("crystal_with_nodes.json")
    params = {"clearance_mm": 0.4, "wall_thickness_mm": 3.0,
              "base_thickness_mm": 4.0,
              "coil_channel": {"enabled": True, "width_mm": 2.0,
                               "depth_mm": 1.5}}
    params.update(overrides)
    design = load("phryll_generator_basic.json")
    design["clearance_mm"] = params["clearance_mm"]
    design["holder_geometry"] = derive_holder_geometry(spec, params)
    return spec, design


def test_dimensions_inherit_from_specimen():
    spec, design = make_design()
    g = design["holder_geometry"]
    assert g["cavity_length_mm"] == spec["dimensions"]["length_mm"] + 0.8
    assert g["cavity_width_mm"] == spec["dimensions"]["diameter_mm"] + 0.8


def test_clearance_changes_cavity():
    _, tight = make_design(clearance_mm=0.2)
    _, loose = make_design(clearance_mm=1.0)
    assert (loose["holder_geometry"]["cavity_length_mm"]
            - tight["holder_geometry"]["cavity_length_mm"]) == pytest.approx(1.6)


def test_invalid_clearance_refused():
    spec = load("crystal_with_nodes.json")
    with pytest.raises(DesignError):
        derive_holder_geometry(spec, {"clearance_mm": -0.5})
    with pytest.raises(DesignError):
        derive_holder_geometry(spec, {"clearance_mm": float("nan")})
    with pytest.raises(DesignError):
        derive_holder_geometry(spec, {})
    with pytest.raises(DesignError):
        derive_holder_geometry(spec, {"clearance_mm": 100.0})


def test_coil_channel_must_fit_wall():
    spec = load("crystal_with_nodes.json")
    with pytest.raises(DesignError):
        derive_holder_geometry(spec, {
            "clearance_mm": 0.4, "wall_thickness_mm": 2.0,
            "coil_channel": {"enabled": True, "width_mm": 2.0,
                             "depth_mm": 2.5}})


def test_scad_deterministic(tmp_path):
    _, design = make_design()
    assert render_scad(design) == render_scad(json.loads(json.dumps(design)))
    a = tmp_path / "a.scad"
    receipt = export_scad(design, a)
    assert receipt["outputs"][0]["sha256"]
    receipt2 = export_scad(design, tmp_path / "b.scad")
    assert receipt["outputs"][0]["sha256"] == receipt2["outputs"][0]["sha256"]
    assert receipt["input_sha256"] == receipt2["input_sha256"]


def test_scad_contains_geometry_and_boundary_comment():
    _, design = make_design()
    scad = render_scad(design)
    assert "cavity_l = 110.800;" in scad
    assert "not a measurement" in scad
    assert design["design_id"] in scad
