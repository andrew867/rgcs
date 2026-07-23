"""P10 — hybrid toothed rotor: exact tooth rate, quadrature, safety refusals."""

from __future__ import annotations

import math
from fractions import Fraction

import pytest

from r11 import rotor as R


# --- the exact tooth-rate identity --------------------------------------

def test_reference_case_is_exactly_4096_hz():
    rate = R.tooth_passage_rate_hz(192, 1280)
    assert rate == Fraction(4096)
    assert isinstance(rate, Fraction)
    assert rate.denominator == 1               # closes exactly, no residue
    assert rate.numerator == 4096


def test_the_intermediate_product_is_exact():
    # 192 * 1280 = 245760, and 245760/60 = 4096 with nothing left over
    assert 192 * 1280 == 245760
    assert Fraction(245760, 60) == Fraction(4096)
    assert R.tooth_passage_rate_hz(192, 1280) == Fraction(245760, 60)


def test_rpm_for_rate_inverts_the_reference_case_exactly():
    rpm = R.rpm_for_rate(192, 4096)
    assert rpm == Fraction(1280)
    assert isinstance(rpm, Fraction)
    assert rpm.denominator == 1


def test_the_identity_round_trips_for_other_tooth_counts():
    for teeth, rpm in ((96, 2560), (192, 1280), (384, 640), (60, 1)):
        rate = R.tooth_passage_rate_hz(teeth, rpm)
        assert R.rpm_for_rate(teeth, rate) == Fraction(rpm)


def test_a_non_closing_rate_stays_exact_rather_than_rounding():
    # 7 teeth at 1 rpm is 7/60 Hz -- kept as a rational, never 0.11666...
    rate = R.tooth_passage_rate_hz(7, 1)
    assert rate == Fraction(7, 60)
    assert rate.denominator == 60
    assert R.rpm_for_rate(7, rate) == Fraction(1)


def test_doubling_the_rpm_doubles_the_passage_rate():
    base = R.tooth_passage_rate_hz(192, 1280)
    doubled = R.tooth_passage_rate_hz(192, 2560)
    assert doubled == 2 * base
    assert doubled == Fraction(8192)
    # and it is linear in the tooth count too
    assert R.tooth_passage_rate_hz(384, 1280) == 2 * base


def test_a_float_rpm_is_refused_by_the_exact_arithmetic():
    with pytest.raises(R.RotorError):
        R.tooth_passage_rate_hz(192, 1280.0)


def test_a_zero_or_negative_tooth_count_is_refused():
    with pytest.raises(R.RotorError):
        R.tooth_passage_rate_hz(0, 1280)
    with pytest.raises(R.RotorError):
        R.rpm_for_rate(-192, 4096)


# --- refusing an approximate rate ---------------------------------------

def test_refuse_approximate_rate_refuses_a_float_restatement():
    with pytest.raises(R.RotorError):
        R.refuse_approximate_rate(4096.0)


def test_refuse_approximate_rate_refuses_a_rounded_value():
    with pytest.raises(R.RotorError):
        R.refuse_approximate_rate(Fraction(40961, 10))
    with pytest.raises(R.RotorError):
        R.refuse_approximate_rate(4100)


def test_refuse_approximate_rate_accepts_only_the_exact_value():
    assert R.refuse_approximate_rate(Fraction(4096)) == Fraction(4096)
    assert R.refuse_approximate_rate(4096) == Fraction(4096)


# --- quadrature geometry -------------------------------------------------

def test_tooth_pitch_is_exact():
    assert R.tooth_pitch_deg(192) == Fraction(360, 192)
    assert R.tooth_pitch_deg(192) == Fraction(15, 8)


def test_quadrature_offset_is_a_quarter_tooth_pitch():
    off = R.quadrature_offset_deg(192)
    assert off == Fraction(360, 768)
    assert off == Fraction(15, 32)
    assert off == R.tooth_pitch_deg(192) / 4


def test_the_quadrature_offset_is_90_electrical_degrees_for_any_tooth_count():
    for teeth in (1, 2, 24, 60, 192, 1024):
        assert R.quadrature_offset_electrical_deg(teeth) == Fraction(90)
    # and one full tooth pitch is one full electrical cycle
    assert R.electrical_deg(R.tooth_pitch_deg(192), 192) == Fraction(360)


# --- the direction sign rule --------------------------------------------

def _quadrature_samples(step_deg: float, n: int = 5):
    """Ideal signed pair a = cos(phi), b = sin(phi), advancing by step."""
    phis = [math.radians(step_deg * k) for k in range(n)]
    return [math.cos(p) for p in phis], [math.sin(p) for p in phis]


def test_direction_is_forward_and_flips_when_the_channels_swap():
    a, b = _quadrature_samples(30.0)
    assert R.direction_from_quadrature(a, b) is R.Direction.FORWARD
    assert R.direction_from_quadrature(b, a) is R.Direction.REVERSE
    assert R.Direction.FORWARD.sign == -R.Direction.REVERSE.sign


def test_a_reversed_phase_advance_reads_as_reverse():
    a, b = _quadrature_samples(-30.0)
    assert R.direction_from_quadrature(a, b) is R.Direction.REVERSE


def test_two_identical_channels_give_no_direction():
    a, _ = _quadrature_samples(30.0)
    assert R.direction_from_quadrature(a, a) is R.Direction.INDETERMINATE


def test_direction_needs_two_samples_of_each_channel():
    with pytest.raises(R.RotorError):
        R.direction_from_quadrature(1.0, 0.0)          # scalars
    with pytest.raises(R.RotorError):
        R.direction_from_quadrature([1.0], [0.0])      # one sample each
    with pytest.raises(R.RotorError):
        R.direction_from_quadrature([1.0, 0.0], [0.0, 1.0, 0.0])


def test_direction_from_a_single_channel_is_refused():
    with pytest.raises(R.RotorError):
        R.refuse_direction_from_single_channel("A", samples=100_000)


def test_an_unsigned_or_lone_channel_pair_cannot_carry_direction():
    pair = R.quadrature_channel_pair(192)
    assert len(pair) == 2
    assert all(c.signed for c in pair)
    assert R.refuse_unsigned_direction_pair(pair) is None
    with pytest.raises(R.RotorError):
        R.refuse_unsigned_direction_pair(pair[:1])
    unsigned = (pair[0], R.PickupChannel(
        "B", pair[1].transduction, pair[1].offset_deg, signed=False))
    with pytest.raises(R.RotorError):
        R.refuse_unsigned_direction_pair(unsigned)


def test_the_quadrature_pair_sits_a_quarter_pitch_apart():
    a, b = R.quadrature_channel_pair(192)
    assert b.offset_deg - a.offset_deg == R.quadrature_offset_deg(192)


# --- the two transduction paths -----------------------------------------

def test_conductive_tabs_and_ferromagnetic_inserts_are_distinct_types():
    tabs = R.place_conductive_tabs(4)
    inserts = R.place_ferromagnetic_inserts(2)
    assert all(isinstance(t, R.ConductiveTab) for t in tabs)
    assert all(isinstance(i, R.FerromagneticInsert) for i in inserts)
    assert not any(isinstance(t, R.FerromagneticInsert) for t in tabs)
    assert tabs[0].transduction is R.Transduction.EDDY_CURRENT_CAPACITIVE
    assert inserts[0].transduction is R.Transduction.VARIABLE_RELUCTANCE
    assert tabs[0].transduction is not inserts[0].transduction


def test_a_feature_cannot_be_relabelled_onto_the_other_path():
    with pytest.raises(R.RotorError):
        R.ConductiveTab(0, Fraction(0),
                        transduction=R.Transduction.VARIABLE_RELUCTANCE)
    with pytest.raises(R.RotorError):
        R.FerromagneticInsert(
            0, Fraction(0),
            transduction=R.Transduction.EDDY_CURRENT_CAPACITIVE)


def test_one_transduction_path_does_not_imply_the_other():
    with pytest.raises(R.RotorError):
        R.refuse_transduction_equivalence(
            R.Transduction.EDDY_CURRENT_CAPACITIVE,
            R.Transduction.VARIABLE_RELUCTANCE)
    with pytest.raises(R.RotorError):
        R.refuse_transduction_equivalence(
            R.Transduction.VARIABLE_RELUCTANCE,
            R.Transduction.EDDY_CURRENT_CAPACITIVE)


def test_placements_are_exact_and_evenly_spaced():
    tabs = R.place_conductive_tabs(4)
    assert [t.angle_deg for t in tabs] == [Fraction(0), Fraction(90),
                                           Fraction(180), Fraction(270)]
    assert all(isinstance(t.angle_deg, Fraction) for t in tabs)
    assert R.place_conductive_tabs(0) == ()


def test_a_hybrid_rotor_declares_both_paths_separately():
    spec = R.reference_rotor()
    assert spec.n_conductive_tabs == 4
    assert spec.n_ferromagnetic_inserts == 2
    assert spec.transduction_paths() == (
        R.Transduction.EDDY_CURRENT_CAPACITIVE,
        R.Transduction.VARIABLE_RELUCTANCE)
    assert len(set(spec.transduction_paths())) == 2


# --- balance -------------------------------------------------------------

def test_unbalance_force_scales_as_the_square_of_speed():
    f1 = R.residual_unbalance_force_N(0.25, 1e-4, 1280)
    f2 = R.residual_unbalance_force_N(0.25, 1e-4, 2560)
    assert f2 == pytest.approx(4.0 * f1, rel=1e-12)
    f3 = R.residual_unbalance_force_N(0.25, 1e-4, 3840)
    assert f3 == pytest.approx(9.0 * f1, rel=1e-12)


def test_unbalance_force_matches_m_e_omega_squared():
    omega = 2.0 * math.pi * 1280 / 60.0
    assert R.angular_velocity_rad_per_s(1280) == pytest.approx(omega)
    assert R.residual_unbalance_force_N(0.25, 1e-4, 1280) == pytest.approx(
        0.25 * 1e-4 * omega * omega, rel=1e-12)


def test_a_balance_grade_tightens_as_speed_rises():
    e_slow = R.permissible_eccentricity_m(6.3, 640)
    e_fast = R.permissible_eccentricity_m(6.3, 1280)
    assert e_fast == pytest.approx(e_slow / 2.0, rel=1e-12)
    assert R.balance_ok(6.3, 1280, e_fast * 0.5)
    assert not R.balance_ok(6.3, 1280, e_fast * 2.0)


def test_an_out_of_grade_rotor_is_a_safety_violation():
    spec = R.reference_rotor(containment_class="ENCLOSURE_MODEL")
    good = R.permissible_eccentricity_m(spec.balance_grade, spec.rpm) * 0.5
    ok = R.refuse_unbalanced_operation(spec, 0.25, good)
    assert ok["residual_unbalance_force_N"] > 0.0
    with pytest.raises(R.SafetyViolation):
        R.refuse_unbalanced_operation(spec, 0.25, good * 10.0)
    ungraded = R.RotorSpec(balance_grade=None)
    with pytest.raises(R.SafetyViolation):
        R.refuse_unbalanced_operation(ungraded, 0.25, 1e-6)


# --- containment ---------------------------------------------------------

def test_rim_speed_grows_with_diameter_and_with_speed():
    v = R.rim_speed_m_per_s(120.0, 1280)
    assert v == pytest.approx(math.pi * 0.120 * 1280 / 60.0, rel=1e-12)
    assert R.rim_speed_m_per_s(240.0, 1280) == pytest.approx(2.0 * v)
    assert R.rim_speed_m_per_s(120.0, 2560) == pytest.approx(2.0 * v)
    assert R.rim_speed_m_per_s(60.0, 1280) < v


def test_a_printed_polymer_rotor_has_a_low_declared_rim_speed_limit():
    printed = R.material_rim_speed_limit("printed polymer")
    assert printed < R.material_rim_speed_limit("aluminium")
    with pytest.raises(R.RotorError):
        R.material_rim_speed_limit("unobtainium")


def test_operation_without_a_declared_containment_class_is_refused():
    spec = R.reference_rotor()                      # containment undeclared
    assert spec.containment_class is None
    with pytest.raises(R.SafetyViolation):
        R.refuse_uncontained_operation(spec)


def test_operation_above_the_declared_rim_speed_limit_is_refused():
    fast = R.RotorSpec(teeth=192, rpm=5000, diameter_mm=120.0,
                       containment_class="ENCLOSURE_MODEL")
    assert fast.rim_speed_m_per_s > R.material_rim_speed_limit(fast.material)
    assert fast.burst_margin() < 1.0
    with pytest.raises(R.SafetyViolation):
        R.refuse_uncontained_operation(fast)


def test_a_declared_containment_within_limit_returns_margins_only():
    spec = R.reference_rotor(containment_class="ENCLOSURE_MODEL")
    margins = R.refuse_uncontained_operation(spec)
    assert margins["burst_margin"] > 1.0
    assert margins["declared_limit_m_per_s"] == R.material_rim_speed_limit(
        spec.material)
    assert "not authorisation to spin" in margins["note"]


# --- nothing may be spun -------------------------------------------------

def test_spin_authorization_always_raises():
    with pytest.raises(R.SafetyViolation):
        R.refuse_spin_authorization()
    spec = R.reference_rotor(containment_class="ENCLOSURE_MODEL")
    # every argument supplied, every margin satisfied -- still refused
    with pytest.raises(R.SafetyViolation):
        R.refuse_spin_authorization(spec, requested_rpm=1,
                                    operator="declared",
                                    containment_class="ENCLOSURE_MODEL")
    with pytest.raises(R.SafetyViolation):
        R.refuse_spin_authorization(R.RotorSpec(rpm=0), requested_rpm=0)


def test_a_safety_violation_is_not_an_arithmetic_refusal():
    assert not issubclass(R.SafetyViolation, R.RotorError)
    assert not issubclass(R.RotorError, R.SafetyViolation)
    with pytest.raises(R.SafetyViolation):
        R.refuse_spin_authorization()


# --- the spec is unbuilt -------------------------------------------------

def test_the_spec_is_pinned_to_model_only():
    spec = R.reference_rotor()
    assert spec.status == "MODEL_ONLY"
    assert spec.material == "printed polymer"
    assert spec.tooth_rate_hz == Fraction(4096)
    assert spec.quadrature_offset_deg == Fraction(15, 32)
    with pytest.raises(R.RotorError):
        R.RotorSpec(status="BUILT")


# --- the report ----------------------------------------------------------

def test_report_declares_the_verdict_and_measures_nothing():
    rep = R.rotor_report()
    assert rep["verdict"] == "HYBRID_ROTOR_MODEL_IMPLEMENTED"
    assert rep["measured_here"] == "nothing"
    assert rep["evidence_class"] == "ANALYTIC_MODEL"
    assert rep["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert rep["what_this_does_not_say"]
    assert rep["status"] == "MODEL_ONLY"


def test_report_carries_the_exact_reference_arithmetic():
    ref = R.rotor_report()["reference_case"]
    assert ref["teeth"] == 192
    assert ref["rpm"] == "1280"
    assert ref["tooth_passage_rate_hz_exact"] == "4096"
    assert ref["is_exact_integer"] is True
    assert ref["inverts_exactly"] is True


def test_report_keeps_the_two_transduction_paths_apart():
    paths = R.rotor_report()["transduction_paths"]
    assert paths["conductive_tabs"]["path"] == "eddy_current_capacitive"
    assert paths["ferromagnetic_inserts"]["path"] == "variable_reluctance"
    assert paths["conductive_tabs"]["path"] != \
        paths["ferromagnetic_inserts"]["path"]
    assert paths["paths_are_distinct"] is True
    assert R.rotor_report()["quadrature"]["two_signed_channels_required"] \
        is True
