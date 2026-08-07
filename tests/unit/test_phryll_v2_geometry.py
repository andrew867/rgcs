"""Phryll v2 geometry engine tests: crystal profile, cone generator,
coil spacing, eye alignment, source profiles (plan pack 09_TESTS)."""
import json
import math
from pathlib import Path

import pytest

from rgcs_desktop.services.phryll_v2.coil_sleeve import (
    CoilSleeveError, compute_coil_standoff, default_wire_spacing,
    generate_crossed_coil_paths)
from rgcs_desktop.services.phryll_v2.cone_generator import (
    check_fit, generate_inner_profile, generate_outer_profile,
    make_cone_design)
from rgcs_desktop.services.phryll_v2.crystal_profile import (
    ProfileError, interpolate_crystal_radius, normalize_crystal_profile,
    sample_crystal_envelope, validate_eye_coordinate)
from rgcs_desktop.services.phryll_v2.eye_alignment import (
    compute_eye_alignment, crossing_ladder, solve_helix_phase_for_eye)
from rgcs_desktop.services.phryll_v2.reference_assets import (
    load_reference_manifest, source_profile_by_id, source_profiles)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "phryll_v2"


def demo_crystal() -> dict:
    return json.loads((FIXTURES / "crystal_profile_example.json")
                      .read_text(encoding="utf-8"))


# ------------------------------------------------------ crystal profile

def test_normalize_demo_crystal():
    profile = normalize_crystal_profile(demo_crystal())
    assert profile.crystal_id == "CRY-DEMO-120"
    assert profile.length_mm == 120.0
    assert profile.z_eye_mm == 62.5


def test_profile_refusals():
    bad = demo_crystal()
    bad["top_diameter_mm"] = 50.0            # top > base: axis flipped
    with pytest.raises(ProfileError):
        normalize_crystal_profile(bad)
    bad2 = demo_crystal()
    bad2["z_eye_mm"] = 500.0                 # eye outside crystal
    with pytest.raises(ProfileError):
        normalize_crystal_profile(bad2)
    bad3 = demo_crystal()
    del bad3["uncertainty"]                  # schema violation
    with pytest.raises(ProfileError):
        normalize_crystal_profile(bad3)


def test_envelope_interpolation():
    profile = normalize_crystal_profile(demo_crystal())
    assert interpolate_crystal_radius(profile, 0.0) == 39.0 / 2
    assert interpolate_crystal_radius(profile, 120.0) == 26.0 / 2
    mid = interpolate_crystal_radius(profile, 60.0)
    assert 13.0 < mid < 19.5
    envelope = sample_crystal_envelope(profile, 96)
    assert len(envelope) == 96
    assert envelope[0].r_mm > envelope[-1].r_mm


# ----------------------------------------------------------------- cone

def test_custom_cone_dimensions():
    """Skeleton T001: inner = crystal + 2*clearance; outer = inner +
    2*wall (26/39 crystal, 0.66 clearance, 1.8 wall)."""
    profile = normalize_crystal_profile(demo_crystal())
    design = make_cone_design(profile, {"clearance_mm": 0.66,
                                        "wall_thickness_mm": 1.8})
    dims = design.generated_dimensions
    assert round(dims["inner_top_diameter_mm"], 3) == 27.32
    assert round(dims["inner_base_diameter_mm"], 3) == 40.32
    assert round(dims["outer_top_diameter_mm"], 3) == 30.92
    assert round(dims["outer_base_diameter_mm"], 3) == 43.92
    assert dims["generation"] == "crystal_envelope_plus_clearance"
    assert design.fit_report.ok
    assert design.fit_report.min_clearance_mm == pytest.approx(0.66)


def test_cone_fit_check_catches_interference():
    profile = normalize_crystal_profile(demo_crystal())
    inner = generate_inner_profile(profile, 0.66)
    shrunk = [type(p)(p.z_mm, p.r_mm - 0.6) for p in inner]
    report = check_fit(profile, shrunk)
    assert not report.ok
    assert report.failures


def test_cone_refusals():
    profile = normalize_crystal_profile(demo_crystal())
    with pytest.raises(ProfileError):
        generate_inner_profile(profile, 0.01)     # unusably tight
    with pytest.raises(ProfileError):
        generate_outer_profile(
            generate_inner_profile(profile, 0.66), 0.2)  # wall too thin


# ----------------------------------------------------------------- coil

def test_awg28_spacing_defaults():
    """Skeleton T003: 0.33 wire -> 0.66 clear gap -> 0.99 pitch."""
    spacing = default_wire_spacing(0.33)
    assert round(spacing.clear_gap_mm, 3) == 0.66
    assert round(spacing.groove_pitch_mm, 3) == 0.99


def test_coil_center_standoff():
    report = compute_coil_standoff(0.66, 1.8, 0.25, 0.33)
    assert round(report.coil_center_standoff_mm, 3) == 2.375
    assert round(report.nearest_conductor_standoff_mm, 3) == 2.21
    assert 7.0 <= report.standoff_in_wire_diameters <= 8.0
    with pytest.raises(CoilSleeveError):
        compute_coil_standoff(0.66, 1.8, 2.0, 0.33)   # groove > wall


def test_clear_gap_source_rule_enforced():
    profile = normalize_crystal_profile(demo_crystal())
    cone = make_cone_design(profile)
    with pytest.raises(CoilSleeveError):
        generate_crossed_coil_paths(profile, cone,
                                    {"wire_diameter_mm": 0.33,
                                     "clear_gap_mm": 0.4})


# ------------------------------------------------------------------ eye

def test_eye_alignment_exact():
    report = compute_eye_alignment(62.5, 62.5, 0.25)
    assert report.alignment_error_mm == 0.0
    assert report.ok


def test_eye_alignment_rejects_midpoint_when_wrong():
    """Skeleton: crystal midpoint (60.0) is NOT the Eye (62.5)."""
    report = compute_eye_alignment(62.5, 120.0 / 2, 0.25)
    assert report.alignment_error_mm == pytest.approx(2.5)
    assert not report.ok


def test_helix_phase_places_crossing_on_eye():
    pitch = 0.99
    z_eye = 62.5
    phase_cu = solve_helix_phase_for_eye(z_eye, pitch, "clockwise")
    phase_ag = solve_helix_phase_for_eye(z_eye, pitch,
                                         "counter_clockwise")
    # both helices reach angular position 0 (mod 2*pi) at z_eye
    theta_cu = (2 * math.pi * z_eye / pitch + phase_cu) % (2 * math.pi)
    theta_ag = (-2 * math.pi * z_eye / pitch + phase_ag) % (2 * math.pi)
    assert theta_cu == pytest.approx(0.0, abs=1e-9) or \
        theta_cu == pytest.approx(2 * math.pi, abs=1e-9)
    assert theta_ag == pytest.approx(0.0, abs=1e-9) or \
        theta_ag == pytest.approx(2 * math.pi, abs=1e-9)


def test_crossing_ladder_contains_eye_exactly():
    ladder = crossing_ladder(62.5, 0.99, 120.0)
    assert 62.5 in ladder
    spacings = {round(b - a, 6) for a, b in zip(ladder, ladder[1:])}
    assert spacings == {round(0.99 / 2, 6)}


def test_generated_coil_aligns_to_eye_not_midpoint():
    profile = normalize_crystal_profile(demo_crystal())
    cone = make_cone_design(profile)
    coil = generate_crossed_coil_paths(profile, cone, {})
    eye = coil["eye_alignment"]
    assert eye["z_cross_mm"] == 62.5          # the Eye, not 60.0
    assert eye["alignment_error_mm"] == 0.0
    assert eye["pass"] is True
    assert 62.5 in coil["paths"]["crossing_ladder_mm"]
    assert coil["paths"]["no_electrical_contact"] is True


def test_coil_requires_eye():
    raw = demo_crystal()
    del raw["z_eye_mm"]
    profile = normalize_crystal_profile(raw)
    cone = make_cone_design(profile)
    with pytest.raises(CoilSleeveError):
        generate_crossed_coil_paths(profile, cone, {})
    check = validate_eye_coordinate(profile)
    assert not check.ok


# ---------------------------------------------------- source profiles

def test_m2_profiles_are_not_silently_merged():
    """Skeleton T002: M2_TEXT and M2_MESH stored separately."""
    text = source_profile_by_id("M2_TEXT")
    mesh = source_profile_by_id("M2_MESH")
    assert text["top_inner_d_mm"] == 29.0
    assert text["base_inner_d_mm"] == 39.0
    assert text["height_mm"] == 120.0
    assert mesh["top_inner_d_mm"] == 30.244
    assert mesh["base_inner_d_mm"] == 44.911
    assert mesh["height_mm"] == 103.712
    assert text["top_inner_d_mm"] != mesh["top_inner_d_mm"]
    assert text["base_inner_d_mm"] != mesh["base_inner_d_mm"]


def test_reference_registry_ids_and_licenses():
    """Skeleton T006: every asset has an ID and license metadata."""
    assets = load_reference_manifest()
    assert len(assets) == 12
    for asset in assets:
        assert asset["asset_id"].startswith("REF-")
        assert asset["license_status"] == "CC-SA supplied"
        assert asset["file_name"]
        assert asset["role"]


def test_annular_craft_locks_not_in_cone_defaults():
    """Skeleton T009: 35/37, 47/72, 288/188, 1683456 are never cone
    sizing inputs — scan the generator sources."""
    import inspect

    from rgcs_desktop.services.phryll_v2 import (coil_sleeve,
                                                 cone_generator,
                                                 crystal_profile)
    for module in (cone_generator, coil_sleeve, crystal_profile):
        source = inspect.getsource(module)
        for lock in ("1683456", "1_683_456", "47/72", "35/37",
                     "288", "188"):
            assert lock not in source, (module.__name__, lock)
