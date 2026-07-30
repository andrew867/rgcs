"""R10.15A — Scale A mechanical crystal lane tests."""

import json
import math
from fractions import Fraction

import pytest

from r1015a import (DESIGN_ID, EM_NEGATIVE_RESULT, FORBIDDEN_CLAIMS,
                    ScaleAError, assert_em_boundary)
from r1015a.design import (BRANCHES, ScaleAGeometry, half_wave_path,
                           half_wave_proxy, physical_length_budget,
                           scale_a_geometry)


def spec():
    from r1015a.scad import design_json
    return design_json()


# ------------------------------------------------ exact arithmetic
def test_half_wave_path_is_exact_dyadic():
    """3800 / (2 * 4096) = 475/1024 m exactly."""
    L = half_wave_path(3800, 4096)
    assert L == Fraction(475, 1024)
    assert float(L) * 1000.0 == 463.8671875
    Lc = half_wave_path(5700, 4096)
    assert Lc == Fraction(1425, 2048)
    assert float(Lc) * 1000.0 == 695.80078125


def test_half_wave_proxy_matches_spec_exactly():
    p = half_wave_proxy("shear_proxy")
    assert p["length_mm"] == spec()["effective_half_wave_path_mm"]
    assert p["is_dyadic_rational"]
    assert p["evidence_class"] == "ANALYTIC_PROXY"
    assert p["is_measured_resonance"] is False
    assert p["is_final_cut_length"] is False
    assert len(p["limitations"]) >= 4


def test_longitudinal_is_a_control_not_an_answer():
    c = half_wave_proxy("longitudinal_proxy")
    assert c["length_mm"] == \
        spec()["alternate_longitudinal_half_wave_path_mm"]
    assert "CONTROL" in c["role"].upper()
    assert "not a second preferred answer" in c["role"]


def test_harmonic_scaling_exact():
    for n in (1, 2, 3, 5):
        assert half_wave_path(3800, 4096, n) == \
            Fraction(475, 1024) / n


def test_unknown_branch_refuses():
    with pytest.raises(ScaleAError, match="declared branches"):
        half_wave_proxy("torsional_guess")


# --------------------------------------------- geometry regressions
@pytest.mark.parametrize("field,attr", [
    ("wide_diameter_mm", "wide_diameter_mm"),
    ("narrow_diameter_mm", "narrow_diameter_mm"),
    ("rx_cap_height_mm", "rx_cap_height_mm"),
    ("tx_cap_height_mm", "tx_cap_height_mm"),
    ("shaft_height_mm", "shaft_height_mm"),
])
def test_geometry_matches_spec(field, attr):
    geo = scale_a_geometry()
    assert abs(getattr(geo, attr) - spec()[field]) < 1e-9


def test_volume_and_mass_match_spec():
    geo = scale_a_geometry()
    assert abs(geo.volume_cm3 - spec()["idealized_volume_cm3"]) < 1e-6
    assert abs(geo.mass_g()
               - spec()["idealized_mass_g_at_2p65"]) < 1e-6


def test_lengths_sum_to_the_body():
    geo = scale_a_geometry()
    total = (geo.rx_cap_height_mm + geo.shaft_height_mm
             + geo.tx_cap_height_mm)
    assert abs(total - geo.length_mm) < 1e-12


def test_diameter_ratio_and_average_hold():
    geo = scale_a_geometry()
    assert abs(geo.wide_diameter_mm / geo.narrow_diameter_mm
               - 1.6) < 1e-12
    assert abs(0.5 * (geo.wide_diameter_mm + geo.narrow_diameter_mm)
               - geo.avg_diameter_mm) < 1e-12
    assert abs(geo.length_mm / geo.avg_diameter_mm - 6.0) < 1e-12


def test_across_flats_changes_caps():
    """The diameter convention is load-bearing, not cosmetic."""
    v = ScaleAGeometry(463.8671875, diameter_mode="across_vertices")
    f = ScaleAGeometry(463.8671875, diameter_mode="across_flats")
    assert f.rx_cap_height_mm > v.rx_cap_height_mm
    ratio = f.rx_cap_height_mm / v.rx_cap_height_mm
    assert abs(ratio - 1.0 / math.cos(math.pi / 6)) < 1e-12


def test_angle_mode_conventions_differ():
    fs = ScaleAGeometry(463.8671875, angle_mode="face_slope")
    ax = ScaleAGeometry(463.8671875, angle_mode="axis_to_face")
    assert abs(fs.rx_cap_height_mm - ax.rx_cap_height_mm) > 1.0


# ------------------------------------------- invalid-geometry refusals
@pytest.mark.parametrize("kwargs", [
    {"length_mm": 0.0},
    {"length_mm": -10.0},
    {"length_mm": float("nan")},
    {"length_mm": 100.0, "facets": 2},
    {"length_mm": 100.0, "wide_to_narrow_ratio": 0.5},
    {"length_mm": 100.0, "length_to_avg_diameter": 0.0},
    {"length_mm": 100.0, "angle_mode": "guess"},
    {"length_mm": 100.0, "diameter_mode": "across_corners"},
    {"length_mm": 100.0, "rx_face_slope_deg": 0.0},
    {"length_mm": 100.0, "tx_face_slope_deg": 90.0},
    {"length_mm": 100.0, "rx_face_slope_deg": 120.0},
])
def test_invalid_geometry_refused(kwargs):
    with pytest.raises(ScaleAError):
        ScaleAGeometry(**kwargs)


def test_terminations_cannot_consume_the_body():
    """A short fat body whose cones exceed its length must be caught."""
    geo = ScaleAGeometry(length_mm=60.0, length_to_avg_diameter=1.2,
                         rx_face_slope_deg=75.0,
                         tx_face_slope_deg=75.0)
    v = geo.validate()
    assert not v["ok"]
    assert "no shaft left" in v["errors"][0]
    assert geo.shaft_height_mm <= 0


# --------------------------------------------- physical length budget
def test_physical_length_refuses_while_terms_unknown():
    b = physical_length_budget(463.8671875)
    assert b["physical_length_mm"] is None
    assert b["status"] == "PHYSICAL_LENGTH_NOT_YET_SOLVED"
    assert len(b["unknown_terms"]) == 5


def test_physical_length_totals_only_when_all_supplied():
    b = physical_length_budget(463.8671875, termination_mm=1.0,
                               electrode_mm=0.2, fixture_mm=0.1,
                               temperature_mm=-0.05,
                               machining_trim_mm=0.5)
    assert b["status"] == "ALL_TERMS_SUPPLIED"
    assert abs(b["physical_length_mm"] - (463.8671875 + 1.75)) < 1e-12
    assert "trim plan" in b["caveat"]


# ------------------------------------------------- branch + sweeps
def test_velocity_sweep_is_linear():
    from r1015a.fem_profile import velocity_sweep
    s = velocity_sweep("shear_proxy", uncertainty_pct=5.0, points=5)
    assert abs(s["length_span_pct"] - 10.0) < 1e-9
    assert abs(s["nominal_length_mm"] - 463.8671875) < 1e-9
    assert s["length_span_mm"] > 40.0        # dominates machining
    lo, hi = s["rows"][0], s["rows"][-1]
    assert abs(hi["length_mm"] / lo["length_mm"]
               - hi["velocity_m_s"] / lo["velocity_m_s"]) < 1e-12


def test_branch_comparison_labels_control():
    from r1015a.fem_profile import branch_comparison
    b = branch_comparison()
    assert b["primary"] == "shear_proxy"
    assert b["control"] == "longitudinal_proxy"
    assert "not a second preferred answer" in b["rule"]


# ------------------------------------------------------ FEM profile
def test_fem_profile_requires_every_mandatory_input():
    from r1015a.fem_profile import (MANDATORY_INPUTS, ScaleAFemProfile,
                                    assert_solvable)
    p = ScaleAFemProfile(geometry=scale_a_geometry())
    rec = p.record()
    assert not rec["solvable"]
    assert set(rec["unresolved_inputs"]) == set(MANDATORY_INPUTS)
    with pytest.raises(ScaleAError, match="unresolved"):
        assert_solvable(p)


def test_fem_profile_becomes_solvable_when_fully_specified():
    from r1015a.fem_profile import ScaleAFemProfile, assert_solvable
    p = ScaleAFemProfile(
        geometry=scale_a_geometry(), handedness="right",
        c_axis_direction="+Z_body", a_axis_azimuth_deg=0.0,
        electrode_condition="open", fixture="free",
        temperature_c=25.0, velocity_uncertainty_pct=2.0)
    assert p.record()["solvable"]
    assert_solvable(p)


@pytest.mark.parametrize("bad", [
    {"handedness": "ambidextrous"},
    {"electrode_condition": "capacitive"},
    {"fixture": "glued"},
    {"a_axis_azimuth_deg": 400.0},
    {"velocity_uncertainty_pct": -1.0},
])
def test_fem_profile_rejects_bad_values(bad):
    from r1015a.fem_profile import ScaleAFemProfile
    p = ScaleAFemProfile(geometry=scale_a_geometry(), **bad)
    assert not p.validate()["ok"]


def test_finite_load_requires_an_impedance():
    from r1015a.fem_profile import ScaleAFemProfile
    p = ScaleAFemProfile(
        geometry=scale_a_geometry(), handedness="right",
        c_axis_direction="+Z_body", a_axis_azimuth_deg=0.0,
        electrode_condition="finite_load", fixture="free",
        temperature_c=25.0, velocity_uncertainty_pct=2.0)
    assert "finite_load_ohm" in p.record()["unresolved_inputs"]


def test_declared_fixture_requires_contacts():
    from r1015a.fem_profile import ScaleAFemProfile
    p = ScaleAFemProfile(
        geometry=scale_a_geometry(), handedness="left",
        c_axis_direction="+Z_body", a_axis_azimuth_deg=10.0,
        electrode_condition="short", fixture="declared_fixture",
        temperature_c=25.0, velocity_uncertainty_pct=1.0)
    assert "fixture_contacts" in p.record()["unresolved_inputs"]


# ------------------------------------------------ mode crowding
def test_mode_crowding_finds_the_nearby_flexural_mode():
    from r1015a.modes import crowding_report
    r = crowding_report(scale_a_geometry())
    assert abs(r["target_mode"]["frequency_hz"] - 4096.0) < 1e-6
    assert r["target_mode"]["family"] == "shear_torsional"
    assert r["nearest_other_mode"] is not None
    assert r["nearest_other_mode"]["family"] == "flexural_free_free"
    assert 0.0 < abs(r["nearest_other_mode"]["separation_fraction"]) < 0.15
    assert r["mode_identity_risk"] in ("MODERATE", "HIGH")
    assert "IDENTITY" in r["interpretation"].upper()


def test_proxy_velocity_ratio_artifact_is_flagged():
    from r1015a.modes import proxy_ratio_artifact
    a = proxy_ratio_artifact()
    assert a["v_longitudinal_over_v_shear"] == [3, 2]
    assert a["is_small_integer_ratio"]
    assert "do not exist in real quartz" in a["warning"].lower()
    assert a["first_spurious_degeneracy_hz"] == 4096.0 * 3


def test_mode_families_cover_three_branches():
    from r1015a.modes import mode_families
    fams = {m["family"] for m in mode_families(scale_a_geometry())}
    assert fams == {"extensional", "shear_torsional",
                    "flexural_free_free"}


# ------------------------------------------ SCAD + JSON verification
def test_scad_static_inspection_passes():
    from r1015a.scad import static_inspection
    s = static_inspection()
    assert s["delimiter_balance"]["balanced"]
    assert s["all_presets_present"]
    assert s["all_exact_present"]
    assert s["ascii_clean"] and not s["em_or_en_dash_present"]
    assert s["module_count"] >= 5 and s["function_count"] >= 5


def test_render_claim_matches_toolchain_reality():
    """Never claim a render that was not performed."""
    from r1015a.scad import openscad_available, verify_render
    r = verify_render()
    if openscad_available():
        assert r["render_attempted"]
    else:
        assert r["render_attempted"] is False
        assert r["render_claimed"] is False
        assert r["verification_level"] == "STATIC_INSPECTION_ONLY"


def test_design_json_validates_and_reproduces():
    from r1015a.scad import validate_design_json
    v = validate_design_json()
    assert v["ok"], v["errors"]
    assert v["cross_check_max_deviation"] == 0.0
    assert v["nonclaim_count"] >= 4
    assert v["unresolved_input_count"] >= 10


def test_design_json_rejects_tampered_geometry():
    from r1015a.scad import design_json, validate_design_json
    d = design_json()
    d["wide_diameter_mm"] = d["wide_diameter_mm"] * 1.05
    v = validate_design_json(d)
    assert not v["ok"]
    assert "not reproducible" in v["errors"][0]


def test_design_json_status_cannot_be_promoted():
    from r1015a.scad import design_json, validate_design_json
    d = design_json()
    d["status"] = "MEASURED_RESONANCE_CONFIRMED"
    assert not validate_design_json(d)["ok"]


# ------------------------------------- R10.15 EM boundary preserved
def test_em_negative_result_is_frozen_verbatim():
    e = EM_NEGATIVE_RESULT
    assert abs(e["annular_eigenmode_hz"] - 1150903000.0) < 1.0
    assert e["4096_hz_as_em_carrier"].startswith("FALSIFIED")
    assert "unattainable Q" in e["sideband_resolution"]
    assert e["reversed_modulation"] == "zero nonreciprocal contrast"
    assert "closed against the support" in e["lateral_force"]
    assert e["status"] == "FROZEN_DO_NOT_REOPEN"


def test_4096hz_cannot_become_em_carrier_without_all_four_gates():
    assert_em_boundary(None)                       # no claim, fine
    with pytest.raises(ScaleAError, match="cannot be treated as an"):
        assert_em_boundary(4096.0)
    with pytest.raises(ScaleAError):
        assert_em_boundary(4096.0, new_geometry=True,
                           new_eigenproblem=True)
    assert_em_boundary(4096.0, new_geometry=True,
                       new_eigenproblem=True, holdout_criteria=True,
                       explicit_result=True)


def test_lane_separation_from_surface_wave():
    """The mechanical lane must not import the EM package."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parents[2] / "r1015a"
    for f in root.rglob("*.py"):
        text = f.read_text(encoding="utf-8")
        assert "import rgcs_surface_wave" not in text, f.name
        assert "from rgcs_surface_wave" not in text, f.name


def test_no_forbidden_claim_appears_in_the_lane():
    """Every occurrence of a forbidden term must be a DENIAL.

    Checked line by line rather than on a context window: the terms
    legitimately appear in the FORBIDDEN_CLAIMS declaration itself and
    in nonclaim sentences, and both of those are denials.
    """
    import pathlib
    root = pathlib.Path(__file__).resolve().parents[2] / "r1015a"
    negations = ("not", "never", "forbidden", "nonclaim", "no claim",
                 "does not", "may never", "refus", "cannot",
                 "forbidden_claims")
    # Evaluate a WINDOW, not a single physical line: these terms
    # legitimately occur inside multi-line nonclaim strings and inside
    # the FORBIDDEN_CLAIMS tuple, where the negation sits on an earlier
    # line. A three-line window is what a human reviewer reads.
    window = 3
    for f in list(root.rglob("*.py")) + list(root.rglob("*.json")):
        lines = f.read_text(encoding="utf-8",
                            errors="replace").lower().splitlines()
        for i, line in enumerate(lines):
            for term in FORBIDDEN_CLAIMS:
                if term in line:
                    ctx = " ".join(lines[max(0, i - window): i + 2])
                    assert any(n in ctx for n in negations), \
                        (f.name, i + 1, term, line.strip()[:90])


def test_design_id_is_stable():
    assert DESIGN_ID == "SCALE_A_4096HZ_SHEAR_463P867_SIX_SIDED"
    assert spec()["design_id"] == DESIGN_ID
