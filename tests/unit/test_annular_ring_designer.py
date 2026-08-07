"""Annular Ring Designer service tests (plan pack 04_MODULE_SPECS)."""
import json
from fractions import Fraction
from pathlib import Path

import pytest

from rgcs_desktop.services.annular_ring import (
    RingError, active_cells, derive_ring_cells, render_ring_scad,
    render_ring_svg, validate_active_mask, write_active_mask_csv,
    write_phase_map_csv)
from rgcs_desktop.services.coil_pulse import sidebands

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "design_studio"


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_37_cells_close_exactly():
    cells = derive_ring_cells(288.0, 188.0, 37)
    assert len(cells) == 37
    total = sum(c["span_deg_exact"] for c in cells)
    assert total == Fraction(360)              # exact, zero residual
    assert cells[0]["start_deg_exact"] == 0
    assert cells[-1]["end_deg_exact"] == 360


def test_invalid_geometry_refused():
    with pytest.raises(RingError):
        derive_ring_cells(188.0, 288.0, 37)    # ID > OD
    with pytest.raises(RingError):
        derive_ring_cells(288.0, 188.0, 2)     # too few cells


def test_active_mask_length_must_match():
    validate_active_mask([True] * 37, 37)
    with pytest.raises(RingError):
        validate_active_mask([True] * 36, 37)
    with pytest.raises(RingError):
        validate_active_mask([True] * 36 + ["yes"], 37)


def test_blanked_cells_excluded():
    design = load("annular_ring_37cell.json")
    act = active_cells(design)
    assert len(act) == 33
    assert set(act).isdisjoint(design["blanked_cells"])


def test_fixture_matches_default_rgcs_ring():
    design = load("annular_ring_37cell.json")
    assert design["od_mm"] == 288.0
    assert design["id_mm"] == 188.0
    assert design["cell_count"] == 37
    assert sum(design["active_mask"]) == 33
    assert len(design["blanked_cells"]) == 4


def test_sideband_table_from_drive():
    design = load("annular_ring_37cell.json")
    table = sidebands(design["drive"]["base_hz"],
                      design["drive"]["modulation_key_hz"])
    assert table[0]["lower_hz"] == 3171.0
    assert table[0]["upper_hz"] == 5021.0


def test_ring_svg_labels_sectors(tmp_path):
    design = load("annular_ring_37cell.json")
    receipt = render_ring_svg(design, tmp_path / "ring.svg")
    svg = (tmp_path / "ring.svg").read_text(encoding="utf-8")
    assert design["design_id"] in svg
    assert "37 cells" in svg
    assert ">36<" in svg                       # every sector labelled
    assert "P1" in svg                         # probe markers
    assert receipt["outputs"][0]["sha256"]


def test_ring_scad_deterministic():
    design = load("annular_ring_37cell.json")
    assert render_ring_scad(design) == render_ring_scad(
        json.loads(json.dumps(design)))
    scad = render_ring_scad(design)
    assert "od = 288.000;" in scad
    assert "not a measurement" in scad


def test_csv_exports(tmp_path):
    design = load("annular_ring_37cell.json")
    phase = write_phase_map_csv(design, tmp_path / "phase.csv")
    mask = write_active_mask_csv(design, tmp_path / "mask.csv")
    phase_lines = phase.read_text(encoding="utf-8").strip().splitlines()
    mask_lines = mask.read_text(encoding="utf-8").strip().splitlines()
    assert len(phase_lines) == 38              # header + 37 cells
    assert len(mask_lines) == 38
    assert phase_lines[0] == "cell,centroid_deg,state,phase_deg"
    # blanked cells carry no phase
    assert ",blanked," in "\n".join(phase_lines)
