"""Phryll v2 CAD export tests: SCAD determinism + no stock scaling,
mesh backend (STL/3MF), flat templates, reference measurement tools."""
import json
import struct
import zipfile
from pathlib import Path

import pytest

from rgcs_desktop.services.phryll_v2.coil_sleeve import \
    generate_crossed_coil_paths
from rgcs_desktop.services.phryll_v2.cone_generator import make_cone_design
from rgcs_desktop.services.phryll_v2.crystal_profile import \
    normalize_crystal_profile
from rgcs_desktop.services.phryll_v2.flat_templates import (
    axial_section_svg, top_template_svg, winding_template_dxf)
from rgcs_desktop.services.phryll_v2.mesh_backend import (
    mesh_stats, tessellate_cone_shell, write_3mf, write_binary_stl)
from rgcs_desktop.services.phryll_v2.openscad_export import (
    export_stl_if_openscad, render_scad, write_scad)
from rgcs_desktop.services.phryll_v2.reference_assets import (
    measure_cone_profile, measure_stl_bounds)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "phryll_v2"


@pytest.fixture()
def design():
    raw = json.loads((FIXTURES / "crystal_profile_example.json")
                     .read_text(encoding="utf-8"))
    profile = normalize_crystal_profile(raw)
    cone = make_cone_design(profile)
    coil = generate_crossed_coil_paths(profile, cone, {})
    return profile, cone, coil


# ----------------------------------------------------------------- scad

def test_scad_deterministic_and_crystal_first(design):
    profile, cone, coil = design
    a = render_scad(cone, coil)
    b = render_scad(cone, coil)
    assert a == b                                  # byte-stable
    # crystal-derived numbers present
    assert "inner_top_d_mm = 27.3200;" in a
    assert "inner_base_d_mm = 40.3200;" in a
    assert "z_eye_mm = 62.5000;" in a
    # T005: no stock STL scaling — generated, never imported
    assert "import(" not in a
    assert ".stl" not in a.lower()
    # required module vocabulary
    for module in ("custom_inner_cone", "custom_outer_cone",
                   "coil_sleeve", "copper_groove_path",
                   "silver_groove_path", "eye_marker", "base_adapter",
                   "cap", "led_holder", "jack_holder", "locker",
                   "crystal_envelope_preview"):
        assert f"module {module}(" in a, module


def test_scad_write_and_optional_openscad(tmp_path, design, monkeypatch):
    _, cone, coil = design
    receipt = write_scad(render_scad(cone, coil), tmp_path / "d.scad")
    assert len(receipt["sha256"]) == 64
    # unit tests never launch the heavy lattice render: force the
    # not-found path and assert the stated absence
    from rgcs_desktop.services.phryll_v2 import openscad_export as oe
    monkeypatch.setattr(oe, "find_openscad", lambda: None)
    stl = oe.export_stl_if_openscad(tmp_path / "d.scad",
                                    tmp_path / "d.stl")
    assert stl["status"] == "unavailable"
    assert "mesh backend" in stl["reason"]


def test_openscad_real_render_smoke(tmp_path):
    """When OpenSCAD is installed, prove the real CLI path with a
    trivial model (fast); skipped cleanly when absent."""
    import pytest as _pytest

    from rgcs_desktop.services.phryll_v2.openscad_export import (
        export_stl_if_openscad, find_openscad)
    if find_openscad() is None:
        _pytest.skip("OpenSCAD not installed")
    scad = tmp_path / "cube.scad"
    scad.write_text("cube([5, 5, 5]);", encoding="utf-8")
    result = export_stl_if_openscad(scad, tmp_path / "cube.stl",
                                    timeout_s=60)
    assert result["status"] == "rendered", result
    assert (tmp_path / "cube.stl").stat().st_size > 80


# ----------------------------------------------------------- mesh/stl

def test_mesh_backend_stl_roundtrip(tmp_path, design):
    _, cone, _ = design
    triangles = tessellate_cone_shell(cone, segments=48)
    stats = mesh_stats(triangles)
    dims = cone.generated_dimensions
    assert stats["height_mm"] == pytest.approx(dims["height_mm"])
    assert stats["max_diameter_mm"] == pytest.approx(
        dims["outer_base_diameter_mm"], rel=0.01)

    stl = write_binary_stl(triangles, tmp_path / "cone.stl")
    data = stl.read_bytes()
    n = struct.unpack("<I", data[80:84])[0]
    assert n == len(triangles)
    assert len(data) == 84 + n * 50

    # our own reference measurement tools read it back
    bounds = measure_stl_bounds(stl)
    assert bounds.n_triangles == n
    assert bounds.size_mm[2] == pytest.approx(dims["height_mm"],
                                              abs=0.01)
    stations = measure_cone_profile(stl)
    assert stations[0]["outer_r_mm"] > stations[-1]["outer_r_mm"]


def test_mesh_backend_3mf(tmp_path, design):
    _, cone, _ = design
    triangles = tessellate_cone_shell(cone, segments=32)
    path = write_3mf(triangles, tmp_path / "cone.3mf")
    with zipfile.ZipFile(path) as zf:
        names = set(zf.namelist())
        assert "3D/3dmodel.model" in names
        assert "[Content_Types].xml" in names
        model = zf.read("3D/3dmodel.model").decode()
    assert "<vertices>" in model and "<triangle " in model
    assert 'unit="millimeter"' in model


# ------------------------------------------------------ flat templates

def test_axial_section_svg(tmp_path, design):
    profile, cone, _ = design
    receipt = axial_section_svg(cone, profile.z_eye_mm,
                                tmp_path / "axial.svg")
    svg = Path(receipt["path"]).read_text(encoding="utf-8")
    assert "Eye 62.5 mm" in svg
    assert "not a scaled" in svg
    assert cone.design_id in svg


def test_top_template_svg(tmp_path, design):
    profile, cone, _ = design
    receipt = top_template_svg(cone, profile.facet_count,
                               tmp_path / "top.svg")
    svg = Path(receipt["path"]).read_text(encoding="utf-8")
    assert "6 facets" in svg


def test_winding_template_dxf(tmp_path, design):
    _, cone, coil = design
    receipt = winding_template_dxf(coil, cone, tmp_path / "wind.dxf")
    dxf = Path(receipt["path"]).read_text(encoding="utf-8")
    assert "EYE_PLANE" in dxf
    assert "COPPER_CW" in dxf
    assert "SILVER_CCW" in dxf
    assert dxf.strip().endswith("EOF")
    assert receipt["developed_mean_radius_mm"] > 0


def test_find_openscad_env_override(tmp_path, monkeypatch):
    """Detection order: PATH, then RGCS_OPENSCAD, then standard install
    locations — the Windows installer does not add OpenSCAD to PATH."""
    from rgcs_desktop.services.phryll_v2 import openscad_export as oe
    fake = tmp_path / "openscad.exe"
    fake.write_bytes(b"stub")
    monkeypatch.setattr(oe.shutil, "which", lambda _name: None)
    monkeypatch.setenv("RGCS_OPENSCAD", str(fake))
    assert oe.find_openscad() == str(fake)
    monkeypatch.delenv("RGCS_OPENSCAD")
    monkeypatch.setattr(oe, "_OPENSCAD_CANDIDATES", (str(fake),))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "nowhere"))
    assert oe.find_openscad() == str(fake)
    monkeypatch.setattr(oe, "_OPENSCAD_CANDIDATES", ())
    assert oe.find_openscad() is None
