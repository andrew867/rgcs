"""P06 — directional field-pair geometry, command compilation, force null."""

from __future__ import annotations

import math

import pytest

import r7
from r7 import vectorfield as VF


E_X = (1.0, 0.0)
E_Y = (0.0, 1.0)


# --- vector helpers ---------------------------------------------------

def test_helpers_agree_with_hand_arithmetic():
    assert VF.add((1.0, 2.0), (3.0, 4.0)) == (4.0, 6.0)
    assert VF.sub((1.0, 2.0), (3.0, 4.0)) == (-2.0, -2.0)
    assert VF.scale((1.0, 2.0), 3.0) == (3.0, 6.0)
    assert VF.dot((1.0, 2.0), (3.0, 4.0)) == 11.0
    assert VF.norm((3.0, 4.0)) == 5.0


def test_dimension_mismatch_rejected():
    with pytest.raises(ValueError):
        VF.add((1.0, 2.0), (1.0, 2.0, 3.0))


def test_cannot_normalize_zero():
    with pytest.raises(ValueError):
        VF.unit((0.0, 0.0))


def test_angle_between_is_clamped():
    """acos of 1.0000000002 would raise; the clamp is load-bearing."""
    assert VF.angle_between_deg(E_X, E_X) == pytest.approx(0.0)
    assert VF.angle_between_deg(E_X, (-1.0, 0.0)) == pytest.approx(180.0)


# --- 1. the rotating basis -------------------------------------------

def test_circular_requires_both_conditions():
    r = VF.rotation_state(1.0, 1.0, 90.0)
    assert r.state == "CIRCULAR"
    assert r.amplitudes_matched and r.quadrature


def test_circular_fails_on_amplitude_mismatch_alone():
    """Quadrature holds, amplitudes do not: an ellipse, not a circle."""
    r = VF.rotation_state(1.0, 1.1, 90.0)
    assert r.state == "ELLIPTICAL"
    assert r.quadrature
    assert not r.amplitudes_matched


def test_circular_fails_on_phase_error_alone():
    """Amplitudes match, quadrature does not: still an ellipse."""
    r = VF.rotation_state(1.0, 1.0, 45.0)
    assert r.state == "ELLIPTICAL"
    assert r.amplitudes_matched
    assert not r.quadrature


def test_minus_ninety_is_also_circular():
    assert VF.rotation_state(1.0, 1.0, -90.0).state == "CIRCULAR"
    assert VF.rotation_state(1.0, 1.0, 270.0).state == "CIRCULAR"


def test_zero_and_one_eighty_are_linear():
    assert VF.rotation_state(1.0, 2.0, 0.0).state == "LINEAR"
    assert VF.rotation_state(1.0, 2.0, 180.0).state == "LINEAR"


def test_dead_channel_is_degenerate():
    assert VF.rotation_state(1.0, 0.0, 90.0).state == "DEGENERATE"
    assert VF.rotation_state(0.0, 0.0, 90.0).state == "DEGENERATE"


def test_every_state_is_declared():
    for args in ((1.0, 1.0, 90.0), (1.0, 1.1, 90.0),
                 (1.0, 2.0, 0.0), (0.0, 0.0, 0.0)):
        assert VF.rotation_state(*args).state in VF.ROTATION_STATES


def test_tolerance_must_be_positive():
    with pytest.raises(ValueError):
        VF.rotation_state(1.0, 1.0, 90.0, tol=0.0)


def test_classification_is_exact_at_the_declared_tolerance():
    """Just inside passes, comfortably outside fails."""
    inside = VF.rotation_state(1.0, 1.0 + VF.TOL / 2, 90.0)
    outside = VF.rotation_state(1.0, 1.0 + VF.TOL * 100, 90.0)
    assert inside.state == "CIRCULAR"
    assert outside.state == "ELLIPTICAL"


def test_basis_sample_traces_a_circle():
    """A CIRCULAR basis has constant radius; the classifier is not
    lying about the geometry."""
    for i in range(16):
        t = i / 16.0
        x, y = VF.basis_sample(1.0, 1.0, 90.0, 2 * math.pi, t)
        assert math.hypot(x, y) == pytest.approx(1.0, abs=1e-12)


# --- 2. the symmetric pair -------------------------------------------

def test_forty_five_degree_pair_sums_to_sqrt2_along_d():
    p = VF.symmetric_pair(E_X, E_Y, 45.0)
    assert p.parallel_component == pytest.approx(math.sqrt(2.0))
    assert p.sum_vector[0] == pytest.approx(math.sqrt(2.0))


def test_forty_five_degree_perpendicular_cancels():
    p = VF.symmetric_pair(E_X, E_Y, 45.0)
    assert abs(p.perpendicular_component) <= VF.TOL
    assert p.perpendicular_cancels
    assert p.sum_vector[1] == pytest.approx(0.0, abs=1e-15)


def test_pair_works_in_three_dimensions():
    d = (0.0, 0.0, 1.0)
    n = (0.0, 1.0, 0.0)
    p = VF.symmetric_pair(d, n, 45.0)
    assert p.parallel_component == pytest.approx(math.sqrt(2.0))
    assert p.perpendicular_cancels


def test_pair_requires_unit_orthogonal_axes():
    with pytest.raises(ValueError):
        VF.symmetric_pair((2.0, 0.0), E_Y)
    with pytest.raises(ValueError):
        VF.symmetric_pair(E_X, (0.0, 3.0))
    with pytest.raises(ValueError):
        VF.symmetric_pair(E_X, (1.0, 0.0))


def test_components_are_the_source_construction():
    p = VF.symmetric_pair(E_X, E_Y, 45.0)
    half = math.sqrt(2.0) / 2.0
    assert p.v_plus == pytest.approx((half, half))
    assert p.v_minus == pytest.approx((half, -half))


# --- 3. the honest framing -------------------------------------------

@pytest.mark.parametrize("theta", [0.0, 10.0, 15.0, 30.0, 45.0, 60.0,
                                   75.0, 89.0, 90.0])
def test_general_theta_gives_two_cos_theta(theta):
    """The whole point: 45 degrees is one entry in a smooth family."""
    p = VF.symmetric_pair(E_X, E_Y, theta)
    assert p.parallel_component == pytest.approx(
        2.0 * math.cos(math.radians(theta)))


@pytest.mark.parametrize("theta", [0.0, 10.0, 15.0, 30.0, 45.0, 60.0,
                                   75.0, 89.0, 90.0])
def test_perpendicular_cancels_at_every_angle(theta):
    """Cancellation is a property of the mirror construction, not of
    45 degrees and not of any field."""
    p = VF.symmetric_pair(E_X, E_Y, theta)
    assert p.perpendicular_cancels


def test_thirty_degrees_beats_forty_five():
    """sqrt(3) > sqrt(2): if the magnitude were evidence, 30 degrees
    would be better evidence."""
    a = VF.symmetric_pair(E_X, E_Y, 30.0).parallel_component
    b = VF.symmetric_pair(E_X, E_Y, 45.0).parallel_component
    assert a == pytest.approx(math.sqrt(3.0))
    assert a > b


def test_sixty_degrees_gives_exactly_one():
    assert VF.symmetric_pair(E_X, E_Y, 60.0).parallel_component == \
        pytest.approx(1.0)


def test_ninety_degrees_gives_zero():
    assert VF.symmetric_pair(E_X, E_Y, 90.0).parallel_component == \
        pytest.approx(0.0, abs=1e-15)


def test_significance_report_denies_that_45_is_special():
    rep = VF.vector_sum_significance()
    assert rep["is_45_degrees_special"] is False
    assert rep["value_at_45_deg"] == pytest.approx(math.sqrt(2.0))
    assert rep["value_at_30_deg"] > rep["value_at_45_deg"]
    assert rep["value_at_60_deg"] == pytest.approx(1.0)
    assert rep["value_at_90_deg"] == pytest.approx(0.0, abs=1e-15)


def test_significance_table_matches_closed_form_everywhere():
    rep = VF.vector_sum_significance()
    assert len(rep["table"]) == len(VF.SIGNIFICANCE_ANGLES)
    for row in rep["table"]:
        assert row["parallel_component"] == pytest.approx(
            row["closed_form_2cos_theta"])
        assert row["perpendicular_cancels"]


def test_significance_says_it_is_not_about_fields_or_force():
    rep = VF.vector_sum_significance()
    assert "not a discovery about fields" in rep["what_it_is_not"]
    assert "not a statement about force" in rep["what_it_is_not"]
    assert rep["collapse_refused"] == \
        r7.FORBIDDEN_COLLAPSES["VECTOR_SUM_IS_THRUST"]


def test_closed_form_is_stated_for_all_theta():
    assert "for all theta" in VF.vector_sum_significance()["closed_form"]


# --- 4. the command compiler -----------------------------------------

def test_command_normalizes_its_direction():
    c = VF.VectorCommand("east", (5.0, 0.0), 2.0)
    assert c.direction == pytest.approx((1.0, 0.0))
    assert c.contribution == pytest.approx((2.0, 0.0))


def test_requested_sum_is_the_weighted_superposition():
    cmds = [VF.VectorCommand("a", E_X, 3.0),
            VF.VectorCommand("b", E_Y, 4.0)]
    assert VF.requested_sum(cmds) == pytest.approx((3.0, 4.0))


def test_empty_command_set_rejected():
    with pytest.raises(ValueError):
        VF.requested_sum([])


def test_mixed_dimension_command_set_rejected():
    cmds = [VF.VectorCommand("a", E_X),
            VF.VectorCommand("b", (0.0, 1.0, 0.0))]
    with pytest.raises(ValueError):
        VF.requested_sum(cmds)


def test_requested_and_realized_differ_under_channel_error():
    """The headline of the compiler: a setting is not a measurement,
    and the realized field is not the requested one."""
    cmds = [VF.VectorCommand("a", E_X, 1.0),
            VF.VectorCommand("b", E_Y, 1.0)]
    out = VF.compile_commands(cmds)
    assert not out.exact
    assert out.realized != out.requested
    assert out.direction_error_deg > 0.0
    assert abs(out.magnitude_error_fraction) > 0.0


def test_direction_error_is_small_but_real():
    """A two percent gain error and 1.5 degrees of phase should steer
    the realized vector by roughly a degree, not by nothing and not by
    a lot."""
    cmds = [VF.VectorCommand("a", E_X, 1.0),
            VF.VectorCommand("b", E_Y, 1.0)]
    out = VF.compile_commands(cmds)
    assert 0.1 < out.direction_error_deg < 5.0


def test_ideal_chain_is_exact_and_is_labelled_an_idealization():
    cmds = [VF.VectorCommand("a", E_X, 1.0),
            VF.VectorCommand("b", E_Y, 1.0)]
    out = VF.compile_commands(cmds,
                              channel_error=VF.IDEAL_CHANNEL_ERROR)
    assert out.exact
    assert "no such chain exists" in VF.IDEAL_CHANNEL_ERROR.source


def test_default_channel_error_is_not_zero():
    """A silent default of zero error would let requested masquerade
    as realized."""
    assert VF.DEFAULT_CHANNEL_ERROR.amplitude_fraction > 0.0
    assert VF.DEFAULT_CHANNEL_ERROR.phase_deg > 0.0
    assert "not measured" in VF.DEFAULT_CHANNEL_ERROR.source


def test_channel_errors_do_not_cancel_between_channels():
    e = VF.DEFAULT_CHANNEL_ERROR
    assert e.channel_gain(0) > 1.0
    assert e.channel_gain(1) < 1.0
    assert e.channel_phase_factor(0) == 1.0
    assert e.channel_phase_factor(1) < 1.0


def test_larger_phase_error_steers_further():
    cmds = [VF.VectorCommand("a", E_X, 1.0),
            VF.VectorCommand("b", E_Y, 1.0)]
    small = VF.compile_commands(
        cmds, channel_error=VF.ChannelError(0.0, 1.0))
    large = VF.compile_commands(
        cmds, channel_error=VF.ChannelError(0.0, 20.0))
    assert large.direction_error_deg > small.direction_error_deg


def test_compiled_record_keeps_both_vectors():
    cmds = [VF.VectorCommand("a", E_X, 1.0),
            VF.VectorCommand("b", E_Y, 1.0)]
    rec = VF.compile_commands(cmds).as_record()
    assert "requested" in rec and "realized" in rec
    assert rec["requested"] != rec["realized"]
    assert "not a reading from" in rec["note"]


def test_null_command_set_reports_no_direction():
    cmds = [VF.VectorCommand("a", E_X, 1.0),
            VF.VectorCommand("b", E_X, -1.0)]
    out = VF.compile_commands(cmds)
    assert "no direction is defined" in out.note


# --- 5. the stationary state -----------------------------------------

def test_stationary_state_detects_balance():
    cmds = [VF.VectorCommand("a", E_X, 1.0),
            VF.VectorCommand("b", (-1.0, 0.0), 1.0)]
    s = VF.stationary_state(cmds)
    assert s.balanced
    assert s.residual_norm == pytest.approx(0.0, abs=VF.TOL)


def test_symmetric_pair_plus_its_reverse_is_stationary():
    """The core/06 condition, built from the source's own geometry."""
    p = VF.symmetric_pair(E_X, E_Y, 45.0)
    # VectorCommand normalizes, so the opposing command must carry the
    # sum's magnitude as its weight rather than -1.
    cmds = [VF.VectorCommand("plus", p.v_plus, 1.0),
            VF.VectorCommand("minus", p.v_minus, 1.0),
            VF.VectorCommand("back", p.sum_vector,
                             -VF.norm(p.sum_vector))]
    assert VF.stationary_state(cmds).balanced


def test_stationary_state_detects_imbalance():
    cmds = [VF.VectorCommand("a", E_X, 1.0),
            VF.VectorCommand("b", (-1.0, 0.0), 0.5)]
    s = VF.stationary_state(cmds)
    assert not s.balanced
    assert s.relative_residual == pytest.approx(0.5)


def test_balance_is_relative_not_absolute():
    """Scaling every weight down must not turn imbalance into
    balance."""
    tiny = [VF.VectorCommand("a", E_X, 1e-12),
            VF.VectorCommand("b", (-1.0, 0.0), 0.5e-12)]
    assert not VF.stationary_state(tiny).balanced


def test_balanced_does_not_mean_inert():
    cmds = [VF.VectorCommand("a", E_X, 1.0),
            VF.VectorCommand("b", (-1.0, 0.0), 1.0)]
    note = VF.stationary_state(cmds).note
    assert "not thereby inert" in note
    assert "heating" in note


# --- 6. the refusal ---------------------------------------------------

def test_thrust_label_is_refused():
    with pytest.raises(VF.VectorFieldRefused) as e:
        VF.refuse_thrust_label(sum_vector=(1.0, 0.0))
    msg = str(e.value)
    assert "VECTOR_SUM_IS_THRUST" in msg
    assert r7.FORBIDDEN_COLLAPSES["VECTOR_SUM_IS_THRUST"] in msg


def test_refusal_names_force_measurement_as_the_requirement():
    with pytest.raises(VF.VectorFieldRefused) as e:
        VF.refuse_thrust_label()
    msg = str(e.value)
    assert "force or acceleration measurement" in msg
    assert "survives controls" in msg


def test_refusal_lists_the_required_controls():
    with pytest.raises(VF.VectorFieldRefused) as e:
        VF.refuse_thrust_label()
    msg = str(e.value).lower()
    for phrase in ("sham drive", "reversed geometry", "thermal",
                   "convection", "electrostatic", "magnetic",
                   "earth's field", "tether", "buoyancy"):
        assert phrase in msg, phrase


def test_confound_table_includes_thermal_and_electrostatic():
    assert "THERMAL_CONVECTION" in VF.THRUST_CONFOUNDS
    assert "ELECTROSTATIC_ATTRACTION" in VF.THRUST_CONFOUNDS
    for name, row in VF.THRUST_CONFOUNDS.items():
        assert row["control"], name
        assert row["why"], name


def test_thermal_and_electrostatic_confounds_are_microNewton_class():
    """The magnitudes are the argument: these are not small effects."""
    assert VF.THRUST_CONFOUNDS["THERMAL_CONVECTION"][
        "expected_magnitude_n"] >= 1e-7
    assert VF.THRUST_CONFOUNDS["ELECTROSTATIC_ATTRACTION"][
        "expected_magnitude_n"] >= 1e-7


def test_sham_and_reversal_are_controls_not_confounds():
    for k in ("SHAM_DRIVE", "REVERSED_GEOMETRY"):
        assert VF.THRUST_CONFOUNDS[k]["expected_magnitude_n"] is None


# --- 7. the force-null design ----------------------------------------

def test_force_null_design_is_a_design_not_a_result():
    d = VF.force_null_design()
    assert d["built"] is False
    assert d["measurements_taken"] == 0


def test_force_null_uses_a_torsion_balance():
    d = VF.force_null_design()
    assert "torsion balance" in d["apparatus"]
    assert "pendulum" in d["apparatus"]
    assert "torsion fibre" in d["why_torsion"]


def test_confound_budget_is_computed_not_asserted():
    d = VF.force_null_design()
    expected = math.sqrt(math.fsum(
        (v["expected_magnitude_n"] or 0.0) ** 2
        for v in VF.THRUST_CONFOUNDS.values()))
    assert d["quadrature_confound_floor_n"] == pytest.approx(expected)
    assert d["quadrature_confound_floor_n"] > 1e-6


def test_history_says_thermal_and_electrostatic_dominate():
    d = VF.force_null_design()
    note = d["historical_note"].lower()
    assert "thermal" in note
    assert "electrostatic" in note
    assert "every claimed anomalous-thrust result" in note


def test_acceptance_requires_all_four_criteria():
    d = VF.force_null_design()
    assert "Failing any one of the four" in d["acceptance"]


def test_expected_outcome_is_a_bounded_null():
    d = VF.force_null_design()
    assert "bounded null" in d["status_if_built"]


# --- 8. programme hygiene --------------------------------------------

def test_no_forbidden_state_strings_appear():
    """R7's forbidden states must not be reachable as literals."""
    import inspect
    src = inspect.getsource(VF)
    for s in r7.FORBIDDEN_STATES:
        assert s not in src, s
