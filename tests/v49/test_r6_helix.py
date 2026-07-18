"""P02 — dual-helical coil digital twin: geometry, field solver, claims."""

from __future__ import annotations

import math

import pytest

import r6
from r6 import helix
from r6.helix import (
    DualHelix,
    GeometryError,
    HelixGeometry,
    SingularEvaluationError,
)


# --------------------------------------------------------------------
# Geometry: positive cases
# --------------------------------------------------------------------

def test_geometry_derived_quantities():
    g = HelixGeometry(radius_m=0.01, pitch_m=0.002, turns=100,
                      wire_diameter_m=1e-3)
    assert g.length_m == pytest.approx(0.2)
    assert g.turns_per_m == pytest.approx(500.0)
    assert g.sense == 1
    # wire length is longer than the bare circumference stack
    assert g.wire_length_m > 100 * 2 * math.pi * 0.01


def test_points_count_and_closure():
    g = HelixGeometry(0.01, 0.002, 3, wire_diameter_m=1e-3)
    pts = g.points(n_per_turn=12)
    assert len(pts) == 3 * 12 + 1
    # every sample sits on the cylinder
    for x, y, _ in pts:
        assert math.hypot(x, y) == pytest.approx(0.01)
    # one full turn advances exactly one pitch
    assert pts[12][2] == pytest.approx(0.002)


def test_handedness_flips_the_sign_of_the_azimuthal_advance():
    r = HelixGeometry(0.01, 0.002, 2, "RIGHT", 0.0, 1e-3)
    l = HelixGeometry(0.01, 0.002, 2, "LEFT", 0.0, 1e-3)
    assert r.sense == 1 and l.sense == -1
    pr = r.points(16)
    pl = l.points(16)
    # mirror pair: x and z shared, y negated
    for (xr, yr, zr), (xl, yl, zl) in zip(pr, pl):
        assert xl == pytest.approx(xr)
        assert zl == pytest.approx(zr)
        assert yl == pytest.approx(-yr)
    # and the y advance genuinely has opposite sign just after the start
    assert pr[1][1] > 0.0 > pl[1][1]


def test_handedness_flips_the_sign_of_the_axial_field():
    r = HelixGeometry(0.005, 0.002, 40, "RIGHT", 0.0, 1e-3)
    l = HelixGeometry(0.005, 0.002, 40, "LEFT", 0.0, 1e-3)
    p = (0.0, 0.0, r.length_m / 2.0)
    bz_r = helix.helix_field(r, 1.0, p, 24)[2]
    bz_l = helix.helix_field(l, 1.0, p, 24)[2]
    assert bz_r > 0.0
    assert bz_l < 0.0
    assert bz_l == pytest.approx(-bz_r, rel=1e-9)


# --------------------------------------------------------------------
# Geometry: refusals
# --------------------------------------------------------------------

@pytest.mark.parametrize("kwargs", [
    dict(radius_m=0.0, pitch_m=0.002, turns=10),
    dict(radius_m=-0.01, pitch_m=0.002, turns=10),
    dict(radius_m=0.01, pitch_m=0.0, turns=10),
    dict(radius_m=0.01, pitch_m=0.002, turns=0),
    dict(radius_m=0.01, pitch_m=0.002, turns=-5),
    dict(radius_m=0.01, pitch_m=0.002, turns=float("nan")),
])
def test_bad_geometry_is_refused(kwargs):
    kwargs.setdefault("wire_diameter_m", 1e-4)
    with pytest.raises(GeometryError):
        HelixGeometry(**kwargs)


def test_zero_turns_refused_with_a_reason():
    with pytest.raises(GeometryError, match="turns must be > 0"):
        HelixGeometry(0.01, 0.002, 0, wire_diameter_m=1e-4)


def test_unknown_handedness_refused():
    with pytest.raises(GeometryError, match="handedness"):
        HelixGeometry(0.01, 0.002, 10, "WIDDERSHINS", 0.0, 1e-4)


def test_overlapping_turns_refused():
    with pytest.raises(GeometryError, match="cannot be wound"):
        HelixGeometry(0.01, pitch_m=1e-4, turns=10, wire_diameter_m=1e-3)


def test_too_few_samples_per_turn_refused():
    g = HelixGeometry(0.01, 0.002, 5, wire_diameter_m=1e-4)
    with pytest.raises(GeometryError, match="n_per_turn"):
        g.points(2)


# --------------------------------------------------------------------
# Crossing angle / dual helix
# --------------------------------------------------------------------

def test_pitch_for_crossing_angle_round_trips():
    for target_deg in (15.0, 30.0, 45.0, 60.0, 90.0):
        d = helix.dual_helix_at_crossing_angle(
            radius_m=0.01, turns=20, crossing_angle_deg=target_deg)
        assert d.crossing_angle_deg == pytest.approx(target_deg, abs=1e-9)


def test_source_45_degree_configuration():
    d = helix.dual_helix_at_crossing_angle(0.01, 20, 45.0)
    assert d.crossing_angle_deg == pytest.approx(45.0)
    assert not d.co_handed
    # 45 deg crossing means 22.5 deg pitch angle on each winding
    assert math.degrees(d.a.pitch_angle_rad) == pytest.approx(22.5)


def test_co_handed_crossing_angle_request_is_refused():
    with pytest.raises(GeometryError, match="opposite handedness"):
        helix.pitch_for_crossing_angle(0.01, 45.0, opposed_handedness=False)


def test_co_handed_equal_pitch_helices_have_zero_crossing_angle():
    a = HelixGeometry(0.01, 0.005, 10, "RIGHT", 0.0, 1e-3)
    b = HelixGeometry(0.01, 0.005, 10, "RIGHT", 0.0, 1e-3)
    d = DualHelix(a, b, angular_offset_rad=math.pi / 3)
    assert d.crossing_angle_rad == pytest.approx(0.0, abs=1e-12)


def test_angular_offset_is_applied_to_the_second_winding():
    a = HelixGeometry(0.01, 0.005, 4, "RIGHT", 0.0, 1e-3)
    b = HelixGeometry(0.01, 0.005, 4, "LEFT", 0.0, 1e-3)
    d = DualHelix(a, b, angular_offset_rad=math.pi)
    assert d.b_offset.start_phase_rad == pytest.approx(math.pi)
    x, y, z = d.b_offset.points(8)[0]
    assert x == pytest.approx(-0.01)
    assert y == pytest.approx(0.0, abs=1e-12)


def test_non_helix_windings_refused():
    a = HelixGeometry(0.01, 0.005, 4, wire_diameter_m=1e-3)
    with pytest.raises(GeometryError):
        DualHelix(a, "not a helix")


# --------------------------------------------------------------------
# THE CORRECTNESS ANCHOR
# --------------------------------------------------------------------

def test_biot_savart_matches_the_infinite_solenoid_limit():
    """The numeric solver must reproduce mu0*n*I to better than 2%."""
    res = helix.validate_against_solenoid()
    assert res["aspect_ratio"] > 100.0
    assert res["relative_error_infinite"] < 0.02, res
    assert res["relative_error_finite"] < 0.02, res
    # on axis the transverse components must be negligible
    assert abs(res["transverse_bx_t"]) < 1e-3 * abs(res["numeric_bz_t"])
    assert abs(res["transverse_by_t"]) < 1e-3 * abs(res["numeric_bz_t"])


def test_solenoid_validation_improves_with_discretisation():
    coarse = helix.validate_against_solenoid(n_per_turn=6)
    fine = helix.validate_against_solenoid(n_per_turn=36)
    assert fine["relative_error_finite"] < coarse["relative_error_finite"]


def test_left_handed_validation_also_passes():
    res = helix.validate_against_solenoid(handedness="LEFT")
    assert res["numeric_bz_t"] < 0.0
    assert res["relative_error_finite"] < 0.02, res


def test_axial_field_analytic_value():
    assert helix.axial_field_analytic(0.01, 1000.0, 2.0) == pytest.approx(
        helix.MU0 * 1000.0 * 2.0)


def test_axial_field_analytic_refuses_bad_inputs():
    with pytest.raises(GeometryError):
        helix.axial_field_analytic(0.0, 1000.0, 1.0)
    with pytest.raises(GeometryError):
        helix.axial_field_analytic(0.01, -1.0, 1.0)


def test_finite_solenoid_is_below_the_infinite_limit():
    inf = helix.axial_field_analytic(0.01, 500.0, 1.0)
    fin = helix.axial_field_finite_solenoid(0.01, 0.2, 500.0, 1.0)
    assert 0.0 < fin < inf


# --------------------------------------------------------------------
# Field solver behaviour
# --------------------------------------------------------------------

def _small_dual():
    return helix.dual_helix_at_crossing_angle(
        radius_m=0.01, turns=6, crossing_angle_deg=45.0,
        wire_diameter_m=5e-4)


def test_field_scales_linearly_with_current():
    d = _small_dual()
    p = (0.0, 0.0, d.a.length_m / 2.0)
    b1 = helix.biot_savart_field(d, 1.0, p, n_per_turn=12)
    b3 = helix.biot_savart_field(d, 3.0, p, n_per_turn=12)
    for c1, c3 in zip(b1, b3):
        assert c3 == pytest.approx(3.0 * c1, rel=1e-9)


def test_counter_wound_equal_currents_cancel_the_axial_field():
    """Counter-wound windings at equal current are pure common mode in
    the drive sense, but their axial fields oppose and cancel."""
    d = _small_dual()
    p = (0.0, 0.0, d.a.length_m / 2.0)
    bz = helix.biot_savart_field(d, (1.0, 1.0), p, n_per_turn=24)[2]
    bz_single = helix.biot_savart_field(d, (1.0, 0.0), p, n_per_turn=24)[2]
    assert abs(bz) < 1e-6 * abs(bz_single)


def test_separate_currents_superpose():
    d = _small_dual()
    p = (0.002, 0.001, d.a.length_m / 2.0)
    ba = helix.biot_savart_field(d, (2.0, 0.0), p, n_per_turn=12)
    bb = helix.biot_savart_field(d, (0.0, 3.0), p, n_per_turn=12)
    both = helix.biot_savart_field(d, (2.0, 3.0), p, n_per_turn=12)
    for x, y, z in zip(ba, bb, both):
        assert z == pytest.approx(x + y, rel=1e-9, abs=1e-18)


def test_singular_evaluation_point_is_refused():
    """A point on the conductor gets a refusal, never an infinity."""
    d = _small_dual()
    on_wire = d.a.points(24)[5]
    with pytest.raises(SingularEvaluationError):
        helix.biot_savart_field(d, 1.0, on_wire, n_per_turn=24)


def test_singular_refusal_survives_zero_current():
    d = _small_dual()
    on_wire = d.a.points(24)[5]
    with pytest.raises(SingularEvaluationError):
        helix.biot_savart_field(d, 0.0, on_wire, n_per_turn=24)


def test_point_just_outside_the_wire_is_allowed():
    d = _small_dual()
    x, y, z = d.a.points(24)[5]
    r = math.hypot(x, y)
    out = ((x / r) * (r + 0.002), (y / r) * (r + 0.002), z)
    b = helix.biot_savart_field(d, 1.0, out, n_per_turn=24)
    assert all(math.isfinite(c) for c in b)


def test_field_solver_refuses_bad_arguments():
    d = _small_dual()
    with pytest.raises(ValueError):
        helix.biot_savart_field(d, (1.0, 2.0, 3.0), (0.1, 0.0, 0.0))
    with pytest.raises(ValueError):
        helix.biot_savart_field(d, float("inf"), (0.1, 0.0, 0.0))
    with pytest.raises(ValueError):
        helix.biot_savart_field(d, 1.0, (0.1, 0.0))
    with pytest.raises(ValueError):
        helix.biot_savart_field(d, 1.0, (0.1, 0.0, 0.0),
                                min_distance_m=0.0)


# --------------------------------------------------------------------
# Claim R6-C-002: common / differential decomposition
# --------------------------------------------------------------------

def test_common_differential_decomposition_basic():
    d = helix.common_differential_decomposition(3.0, 1.0)
    assert d["common_mode_a"] == pytest.approx(2.0)
    assert d["differential_mode_a"] == pytest.approx(1.0)
    assert d["units"]["common_mode_a"] == "A"
    assert d["evidence_class"] == "SYNTHETIC_MODEL"


def test_equal_currents_are_pure_common_mode():
    d = helix.common_differential_decomposition(2.0, 2.0)
    assert d["differential_mode_a"] == 0.0
    assert d["purely_common"] is True
    assert d["purely_differential"] is False


def test_opposite_currents_are_pure_differential_mode():
    d = helix.common_differential_decomposition(2.0, -2.0)
    assert d["common_mode_a"] == 0.0
    assert d["purely_differential"] is True


def test_decomposition_refuses_non_finite_currents():
    with pytest.raises(ValueError):
        helix.common_differential_decomposition(float("nan"), 1.0)


def test_source_pulse_trains_unipolar_are_not_purely_differential():
    """The honest result: 1-0-1-0 / 0-1-0-1 at 0 A and A carries an
    equal common-mode component in every active slot."""
    d = helix.decompose_pulse_trains(helix.SOURCE_TRAIN_COPPER,
                                     helix.SOURCE_TRAIN_SILVER,
                                     amplitude_a=5.0)
    assert d["n_slots"] == 6
    assert d["antiphase_fraction"] == 1.0
    assert d["purely_differential_fraction"] == 0.0
    assert d["mean_common_mode_a"] == pytest.approx(2.5)
    assert d["mean_abs_differential_a"] == pytest.approx(2.5)
    for k, s in enumerate(d["slots"]):
        assert s["slot"] == k
        assert abs(s["common_mode_a"]) == pytest.approx(2.5)
    assert d["claim"] == "R6-C-002"


def test_source_pulse_trains_bipolar_are_purely_differential():
    d = helix.decompose_pulse_trains(helix.SOURCE_TRAIN_COPPER,
                                     helix.SOURCE_TRAIN_SILVER,
                                     amplitude_a=5.0, bipolar=True)
    assert d["purely_differential_fraction"] == 1.0
    assert d["mean_common_mode_a"] == pytest.approx(0.0)
    assert d["mean_abs_differential_a"] == pytest.approx(5.0)


def test_in_phase_trains_have_no_differential_component():
    d = helix.decompose_pulse_trains((1, 0, 1), (1, 0, 1),
                                     amplitude_a=2.0)
    assert d["antiphase_fraction"] == 0.0
    assert d["mean_abs_differential_a"] == 0.0


@pytest.mark.parametrize("t1,t2", [
    ((1, 0, 1), (0, 1)),
    ((), ()),
    ((1, 2), (0, 1)),
    ((1, 0), (0, -1)),
])
def test_bad_pulse_trains_are_refused(t1, t2):
    with pytest.raises(ValueError):
        helix.decompose_pulse_trains(t1, t2)


def test_pulse_train_amplitude_must_be_positive():
    with pytest.raises(ValueError):
        helix.decompose_pulse_trains((1, 0), (0, 1), amplitude_a=0.0)


# --------------------------------------------------------------------
# Coupling
# --------------------------------------------------------------------

def test_mutual_inductance_states_its_approximation_and_validity():
    d = helix.dual_helix_at_crossing_angle(0.005, 200, 45.0)
    m = helix.mutual_inductance_estimate(d)
    assert m["approximation"]
    assert m["validity_range"]
    assert m["units"]["mutual_inductance_h"] == "H"
    assert m["evidence_class"] == "SYNTHETIC_MODEL"


def test_counter_wound_mutual_inductance_is_negative():
    d = helix.dual_helix_at_crossing_angle(0.005, 200, 45.0)
    m = helix.mutual_inductance_estimate(d)
    assert not d.co_handed
    assert m["mutual_inductance_h"] < 0.0
    assert "oppose" in m["sign_reason"]


def test_co_handed_mutual_inductance_is_positive_and_k_near_one():
    g = HelixGeometry(0.005, 0.002, 200, "RIGHT", 0.0, 1e-3)
    d = DualHelix(g, g, angular_offset_rad=0.0)
    m = helix.mutual_inductance_estimate(d)
    assert m["mutual_inductance_h"] > 0.0
    assert m["coupling_coefficient"] == pytest.approx(1.0)


def test_short_fat_coil_is_flagged_invalid():
    g = HelixGeometry(0.05, 0.005, 4, "RIGHT", 0.0, 1e-3)
    d = DualHelix(g, g, 0.0)
    m = helix.mutual_inductance_estimate(d)
    assert m["valid"] is False
    assert "NOT VALID" in m["validity_note"]


def test_mutual_inductance_is_offset_independent_as_documented():
    """The stated limitation is tested, not merely asserted in prose."""
    g1 = HelixGeometry(0.005, 0.002, 200, "RIGHT", 0.0, 1e-3)
    g2 = HelixGeometry(0.005, 0.002, 200, "RIGHT", 0.0, 1e-3)
    a = helix.mutual_inductance_estimate(DualHelix(g1, g2, 0.0))
    b = helix.mutual_inductance_estimate(DualHelix(g1, g2, math.pi / 2))
    assert a["mutual_inductance_h"] == pytest.approx(
        b["mutual_inductance_h"])
    assert "cannot test" in a["validity_range"]


def test_excessive_overlap_is_refused():
    d = helix.dual_helix_at_crossing_angle(0.005, 20, 45.0)
    with pytest.raises(GeometryError, match="exceeds"):
        helix.mutual_inductance_estimate(d, overlap_length_m=1e6)


# --------------------------------------------------------------------
# Claim-language guards
# --------------------------------------------------------------------

def test_module_declares_no_coil_has_been_wound():
    assert "no coil has been wound" in helix.__doc__.lower()


def test_module_uses_no_forbidden_state():
    import pathlib
    src = pathlib.Path(helix.__file__).read_text(encoding="utf-8")
    for state in r6.FORBIDDEN_STATES:
        assert state not in src, f"{state} appears in r6/helix.py"


def test_records_carry_units_and_evidence_class():
    d = helix.dual_helix_at_crossing_angle(0.005, 20, 45.0)
    rec = d.as_record()
    assert rec["evidence_class"] == "SYNTHETIC_MODEL"
    assert rec["a"]["units"]["radius_m"] == "m"
    assert "no coil has been wound" in rec["note"]
