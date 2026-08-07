"""PHRYLL_V2_COUPLING_UPDATE tests: bottom coupling model, O-ring
records, continuous groove slots, source-language entries, excitation
ordering, craft-skin doc separation."""
import json
import math
from pathlib import Path

import numpy as np
import pytest

from rgcs_desktop.services.phryll_v2.bottom_coupling import (
    CouplingError, design_bottom_coupling)
from rgcs_desktop.services.phryll_v2.coil_sleeve import \
    generate_crossed_coil_paths
from rgcs_desktop.services.phryll_v2.cone_generator import make_cone_design
from rgcs_desktop.services.phryll_v2.crystal_profile import \
    normalize_crystal_profile
from rgcs_desktop.services.phryll_v2.mesh_backend import (
    tessellate_coil_sleeve, tessellate_cone_shell)
from rgcs_desktop.services.phryll_v2.openscad_export import render_scad

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "phryll_v2"
REGISTRY = ROOT / "rgcs_desktop" / "data" / "phryll_v2_reference_registry.json"


@pytest.fixture()
def crystal():
    raw = json.loads((FIXTURES / "crystal_profile_example.json")
                     .read_text(encoding="utf-8"))
    return normalize_crystal_profile(raw)


# ------------------------------------------------- bottom coupling

def test_open_coupling_chain(crystal):
    coupling = design_bottom_coupling(crystal, {})
    assert coupling["coupling_chain"] == [
        "crystal bottom", "open or lightly coupled gap",
        "flat pickup surface", "annular pickup ring"]
    assert coupling["coupling_mode"] == "open"
    assert coupling["bottom_aperture_open"] is True
    assert coupling["gap_mm"] == 2.0
    ring = coupling["pickup_ring"]
    assert ring["id_mm"] < ring["od_mm"]


def test_solid_bottom_is_not_a_mode(crystal):
    with pytest.raises(CouplingError):
        design_bottom_coupling(crystal, {"coupling_mode": "solid"})
    with pytest.raises(CouplingError):
        design_bottom_coupling(crystal, {"gap_mm": 0.1})  # no real gap


def test_o_ring_record_required_and_bounded(crystal):
    good = design_bottom_coupling(crystal, {
        "coupling_mode": "o_ring_mounted", "gap_mm": 2.0,
        "o_ring": {"material": "nitrile", "cord_diameter_mm": 2.0,
                   "id_mm": 38.0, "compression_pct": 15.0,
                   "contact_height_mm": 4.0}})
    assert good["o_ring"]["material"] == "nitrile"
    with pytest.raises(CouplingError):        # record incomplete
        design_bottom_coupling(crystal, {
            "coupling_mode": "o_ring_mounted",
            "o_ring": {"material": "nitrile"}})
    with pytest.raises(CouplingError):        # hard damping
        design_bottom_coupling(crystal, {
            "coupling_mode": "o_ring_mounted",
            "o_ring": {"material": "nitrile", "cord_diameter_mm": 2.0,
                       "id_mm": 38.0, "compression_pct": 45.0,
                       "contact_height_mm": 4.0}})


def test_cone_bottom_is_open_in_mesh(crystal):
    """No solid plastic under the crystal: at z=0 the mesh only covers
    the wall annulus — nothing inside the inner aperture."""
    cone = make_cone_design(crystal)
    tris = tessellate_cone_shell(cone, segments=48)
    flat = tris.reshape(-1, 3)
    at_bottom = flat[np.abs(flat[:, 2]) < 1e-9]
    radii = np.hypot(at_bottom[:, 0], at_bottom[:, 1])
    inner_r = cone.generated_dimensions["inner_base_diameter_mm"] / 2
    assert radii.min() >= inner_r - 1e-6


# ------------------------------------------- continuous groove slots

def test_scad_groove_is_continuous_not_dotted(crystal):
    cone = make_cone_design(crystal)
    coil = generate_crossed_coil_paths(crystal, cone, {})
    scad = render_scad(cone, coil,
                       design_bottom_coupling(crystal, {}))
    assert "linear_extrude" in scad and "twist = twist_deg" in scad
    assert "sphere(d = wire_d_mm" not in scad     # old dotted cutter
    assert "module annular_pickup_ring(" in scad
    assert "OPEN below the crystal base aperture" in scad


def test_sleeve_mesh_has_real_slots(crystal):
    """The shipped sleeve STL carries the slots: on a groove centerline
    the surface radius dips by ~groove depth; off-groove it does not."""
    cone = make_cone_design(crystal)
    coil = generate_crossed_coil_paths(crystal, cone, {})
    tris = tessellate_coil_sleeve(cone, coil, segments=48,
                                  band_z_step_mm=0.05)
    flat = tris.reshape(-1, 3)
    paths = coil["paths"]
    pitch = coil["spacing"]["groove_pitch_mm"]
    depth = coil["spacing"]["groove_depth_mm"]
    phi = paths["copper"]["phase_rad_at_z0"]
    z_eye = coil["eye_alignment"]["z_eye_mm"]

    def outer_r_at(z):
        zs = [p.z_mm for p in cone.outer_profile]
        rs = [p.r_mm for p in cone.outer_profile]
        return float(np.interp(z, zs, rs))

    # copper groove centerline passes theta=0 at z_eye (phased there)
    near_eye = flat[(np.abs(flat[:, 2] - z_eye) < 0.02)
                    & (np.abs(np.arctan2(flat[:, 1], flat[:, 0]))
                       < 0.05)]
    assert len(near_eye), "no vertices sampled on the groove line"
    groove_r = np.hypot(near_eye[:, 0], near_eye[:, 1]).min()
    assert groove_r <= outer_r_at(z_eye) - 0.8 * depth

    # halfway between grooves (quarter pitch off), the wall is smooth
    z_off = z_eye + pitch / 4
    off = flat[(np.abs(flat[:, 2] - z_off) < 0.01)
               & (np.abs(np.arctan2(flat[:, 1], flat[:, 0])) < 0.05)]
    if len(off):
        off_r = np.hypot(off[:, 0], off[:, 1]).max()
        assert off_r >= outer_r_at(z_off) - 1e-3


# --------------------------------- source language + craft separation

def test_source_language_entries_registered():
    body = json.loads(REGISTRY.read_text(encoding="utf-8"))
    entries = {e["entry_id"]: e for e in body["source_language_entries"]}
    for eid in ("SRC-AG-BIRDWING", "SRC-L-1520", "SRC-L-1526",
                "SRC-L-1527", "SRC-INTENTION-ONLY"):
        assert eid in entries
        assert entries[eid]["status"] == "source-language"


def test_excitation_paths_hardware_first():
    body = json.loads(REGISTRY.read_text(encoding="utf-8"))
    paths = body["excitation_paths"]["implemented_first"]
    assert paths == ["photonic / laser",
                     "magneto-acoustic / pulsed coils",
                     "mechanical / acoustic",
                     "electrical / coil"]
    assert "source-language" in body["excitation_paths"]["note"]


def test_craft_skin_doc_exists_and_stays_out_of_generator():
    doc = ROOT / "docs" / "research" / "circular_aerofoil_craft_skin.md"
    text = doc.read_text(encoding="utf-8")
    assert "pressure-differential analogy" in text
    assert "source-language" in text
    assert "Refused claims" in text
    # craft-docs only: the phryll generator code never references it
    import inspect

    from rgcs_desktop.services.phryll_v2 import (cone_generator,
                                                 coil_sleeve, pipeline)
    for module in (cone_generator, coil_sleeve, pipeline):
        source = inspect.getsource(module)
        assert "aerofoil" not in source.lower()


def test_lattice_is_45_degrees_multi_start(crystal):
    """Reference geometry: ±45° crossed multi-start lattice, not
    near-horizontal rings — rise per turn equals one circumference at
    the mean band radius, and the perpendicular wire gap keeps the
    source rule."""
    cone = make_cone_design(crystal)
    coil = generate_crossed_coil_paths(crystal, cone, {})
    paths = coil["paths"]
    spacing = coil["spacing"]
    assert paths["helix_angle_deg"] == 45.0
    r_mean = paths["mean_band_radius_mm"]
    assert paths["rise_per_turn_mm"] == pytest.approx(
        2 * math.pi * r_mean, rel=1e-9)
    # steep lattice: far more than one circumference per band-height
    # of rise (the old bug had rise = 0.99 mm per turn)
    assert paths["rise_per_turn_mm"] > 50.0
    band = paths["band_top_mm"] - paths["band_bottom_mm"]
    assert paths["turns_per_strand"] == pytest.approx(
        band / paths["rise_per_turn_mm"])
    assert 0.3 < paths["turns_per_strand"] < 1.5   # partial diagonal wrap
    # multi-start family fills the circumference
    assert paths["n_starts_per_coil"] >= 50
    assert paths["n_starts_per_coil"] == int(
        paths["rise_per_turn_mm"] / spacing["axial_strand_spacing_mm"])
    # perpendicular spacing keeps the >= 2 wire-diameter clear gap
    wire_d = coil["wire"]["wire_diameter_mm"]
    perp = spacing["axial_strand_spacing_mm"] * math.cos(
        math.radians(45.0))
    assert perp == pytest.approx(spacing["perpendicular_pitch_mm"])
    assert perp - wire_d >= 2 * wire_d - 1e-9
    # lattice crossing centered on the Eye
    assert coil["eye_alignment"]["z_cross_mm"] == 62.5
    assert coil["eye_alignment"]["alignment_error_mm"] == 0.0
