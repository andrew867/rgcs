"""P03 — pulse spectrum, matched-energy control, piezo model, null audit.

The spectral tests check the closed forms against values computed by
hand from the analytic expressions, not against the module's own output.
The frequency-audit tests check that the null is COMPUTED and reported
honestly; they deliberately do not assert a significant result.
"""

from __future__ import annotations

import math

import pytest

import r6
from r6 import pulse


# --- specification guards ------------------------------------------------

def test_rect_refuses_finite_edges():
    with pytest.raises(pulse.PulseModelError, match="TRAPEZOID"):
        pulse.PulseShape(rise_s=1e-6, width_s=1e-3, fall_s=0.0,
                         amplitude=1.0, shape="RECT")


def test_gaussian_refuses_edge_times():
    with pytest.raises(pulse.PulseModelError):
        pulse.PulseShape(0.0, 1e-3, 1e-6, 1.0, "GAUSSIAN")


def test_zero_width_refused():
    with pytest.raises(pulse.PulseModelError):
        pulse.PulseShape(0.0, 0.0, 0.0, 1.0, "RECT")


def test_unknown_shape_refused():
    with pytest.raises(pulse.PulseModelError, match="unknown pulse shape"):
        pulse.PulseShape(0.0, 1e-3, 0.0, 1.0, "SAWTOOTH")


# --- RECT closed form ----------------------------------------------------

RECT = pulse.PulseShape(0.0, 1e-3, 0.0, 2.0, "RECT")   # A=2, w=1 ms


def test_rect_dc_is_the_area():
    # |X(0)| = A*w = 2 * 1e-3
    assert pulse.spectrum(RECT, 0.0) == pytest.approx(2e-3, rel=1e-12)
    assert pulse.dc_magnitude(RECT) == pytest.approx(2e-3, rel=1e-12)


def test_rect_first_null_at_one_over_width():
    # sinc(pi f w) = 0 at f = 1/w = 1000 Hz
    assert pulse.spectrum(RECT, 1000.0) == pytest.approx(0.0, abs=1e-15)
    assert pulse.spectrum(RECT, 2000.0) == pytest.approx(0.0, abs=1e-15)


def test_rect_hand_computed_midband_value():
    # f = 500 Hz, w = 1e-3 -> pi f w = pi/2, sinc = sin(pi/2)/(pi/2) = 2/pi
    expected = 2.0 * 1e-3 * (2.0 / math.pi)
    assert pulse.spectrum(RECT, 500.0) == pytest.approx(expected, rel=1e-12)


def test_rect_energy_closed_form():
    # E = A^2 w = 4 * 1e-3
    assert pulse.total_energy(RECT) == pytest.approx(4e-3, rel=1e-12)


def test_rect_3db_bandwidth_matches_the_standard_0_4429_over_w():
    # The half-power point of sinc is at pi f w = 1.39156..., i.e.
    # f = 0.442946.../w. Standard result; checked to 4 decimals.
    b = pulse.bandwidth_3db(RECT)
    assert b * RECT.width_s == pytest.approx(0.4429, abs=1e-4)


# --- GAUSSIAN closed form ------------------------------------------------

GAUSS = pulse.PulseShape(0.0, 1e-3, 0.0, 1.0, "GAUSSIAN")  # FWHM 1 ms


def test_gaussian_sigma_from_fwhm():
    assert GAUSS.sigma_s == pytest.approx(
        1e-3 / 2.354820045030949, rel=1e-12)


def test_gaussian_dc_hand_computed():
    # |X(0)| = A sigma sqrt(2 pi)
    sigma = 1e-3 / (2.0 * math.sqrt(2.0 * math.log(2.0)))
    assert pulse.spectrum(GAUSS, 0.0) == pytest.approx(
        sigma * math.sqrt(2.0 * math.pi), rel=1e-12)


def test_gaussian_transform_is_a_gaussian_no_nulls():
    # Unlike the rectangle, there is no zero anywhere.
    for f in (100.0, 500.0, 1000.0, 2000.0, 5000.0):
        assert pulse.spectrum(GAUSS, f) > 0.0


def test_gaussian_hand_computed_value():
    sigma = GAUSS.sigma_s
    f = 300.0
    expected = sigma * math.sqrt(2 * math.pi) * math.exp(
        -2 * math.pi ** 2 * f ** 2 * sigma ** 2)
    assert pulse.spectrum(GAUSS, f) == pytest.approx(expected, rel=1e-12)


def test_gaussian_energy_closed_form():
    # E = A^2 sigma sqrt(pi)
    assert pulse.total_energy(GAUSS) == pytest.approx(
        GAUSS.sigma_s * math.sqrt(math.pi), rel=1e-12)


def test_gaussian_3db_bandwidth_closed_form():
    # |X(B)| = |X(0)|/sqrt(2)  =>  exp(-2 pi^2 B^2 sigma^2) = 1/sqrt(2)
    # =>  B = sqrt(ln 2) / (2 pi sigma)
    expected = math.sqrt(math.log(2.0)) / (2 * math.pi * GAUSS.sigma_s)
    assert pulse.bandwidth_3db(GAUSS) == pytest.approx(expected, rel=1e-9)


def test_gaussian_is_less_broadband_than_a_rect_of_equal_duration():
    """The point of R6-C-005: 'the pulse' is not one thing."""
    rect = pulse.PulseShape(0.0, 1e-3, 0.0, 1.0, "RECT")
    gauss = pulse.PulseShape(0.0, 1e-3, 0.0, 1.0, "GAUSSIAN")
    hi = pulse.spectral_energy_fraction(rect, 5000.0, 50000.0)
    lo = pulse.spectral_energy_fraction(gauss, 5000.0, 50000.0)
    assert hi > lo


# --- TRAPEZOID closed form -----------------------------------------------

TRAP = pulse.PulseShape(rise_s=1e-4, width_s=1e-3, fall_s=1e-4,
                        amplitude=1.0, shape="TRAPEZOID")


def test_trapezoid_dc_is_the_trapezoid_area():
    # area = A (w + (r+g)/2) = 1e-3 + 1e-4
    assert pulse.spectrum(TRAP, 0.0) == pytest.approx(1.1e-3, rel=1e-12)


def test_trapezoid_symmetric_matches_the_two_sinc_product():
    """Symmetric trapezoid: |X| = A (w+r) sinc(pi f (w+r)) sinc(pi f r)."""
    r, w = TRAP.rise_s, TRAP.width_s
    for f in (37.0, 411.0, 1237.0, 9001.0):
        expected = abs((w + r)
                       * math.sin(math.pi * f * (w + r)) / (math.pi * f * (w + r))
                       * math.sin(math.pi * f * r) / (math.pi * f * r))
        assert pulse.spectrum(TRAP, f) == pytest.approx(expected, rel=1e-9)


def test_trapezoid_energy_closed_form():
    # E = A^2 (w + (r+g)/3)
    expected = 1e-3 + 2e-4 / 3.0
    assert pulse.total_energy(TRAP) == pytest.approx(expected, rel=1e-12)


def test_asymmetric_trapezoid_reduces_to_rect_when_edges_vanish():
    trap = pulse.PulseShape(0.0, 1e-3, 0.0, 2.0, "TRAPEZOID")
    for f in (0.0, 250.0, 500.0, 1500.0):
        assert pulse.spectrum(trap, f) == pytest.approx(
            pulse.spectrum(RECT, f), abs=1e-15)


def test_finite_edges_reduce_high_frequency_content():
    """Edge time, not 'pulseness', is what bounds real bandwidth."""
    sharp = pulse.PulseShape(1e-6, 1e-3, 1e-6, 1.0, "TRAPEZOID")
    soft = pulse.PulseShape(2e-4, 1e-3, 2e-4, 1.0, "TRAPEZOID")
    assert (pulse.spectral_energy_fraction(sharp, 2e4, 2e5)
            > pulse.spectral_energy_fraction(soft, 2e4, 2e5))


# --- Parseval / band fractions -------------------------------------------

def test_spectral_energy_fraction_over_a_wide_band_approaches_one():
    frac = pulse.spectral_energy_fraction(GAUSS, 0.0, 20000.0,
                                          n_points=20001)
    assert frac == pytest.approx(1.0, abs=1e-6)


def test_spectral_energy_fraction_is_zero_on_a_degenerate_band():
    assert pulse.spectral_energy_fraction(RECT, 100.0, 100.0) == 0.0


def test_spectral_energy_fraction_refuses_inverted_band():
    with pytest.raises(pulse.PulseModelError):
        pulse.spectral_energy_fraction(RECT, 500.0, 100.0)


# --- THE MANDATORY MATCHED-ENERGY CONTROL --------------------------------

@pytest.mark.parametrize("shape", ["RECT", "GAUSSIAN", "TRAPEZOID"])
@pytest.mark.parametrize("f_hz", [587.0, 644.0, 1496.0, 10000.0])
def test_matched_energy_sinusoid_really_matches_the_energy(shape, f_hz):
    """The control is worthless if the energies are not actually equal."""
    if shape == "TRAPEZOID":
        p = pulse.PulseShape(1e-4, 1e-3, 1e-4, 3.0, shape)
    else:
        p = pulse.PulseShape(0.0, 1e-3, 0.0, 3.0, shape)
    ctrl = pulse.matched_energy_sinusoid(p, f_hz)
    assert ctrl.energy == pytest.approx(pulse.total_energy(p), rel=1e-12)
    # And the sinusoid's own parameters reproduce that energy.
    assert ctrl.energy_check() == pytest.approx(
        pulse.total_energy(p), rel=1e-12)


def test_matched_energy_sinusoid_uses_whole_half_cycles():
    p = pulse.PulseShape(0.0, 1e-3, 0.0, 1.0, "RECT")
    ctrl = pulse.matched_energy_sinusoid(p, 1496.0)
    n_half = ctrl.duration_s / (0.5 / 1496.0)
    assert n_half == pytest.approx(round(n_half), abs=1e-9)
    assert ctrl.duration_s >= p.duration_s


def test_matched_energy_sinusoid_states_what_it_does_not_control():
    ctrl = pulse.matched_energy_sinusoid(RECT, 644.0)
    for missing in ("peak", "slew", "phase"):
        assert missing in ctrl.note.lower()


def test_matched_energy_sinusoid_refuses_nonpositive_frequency():
    with pytest.raises(pulse.PulseModelError):
        pulse.matched_energy_sinusoid(RECT, 0.0)


# --- piezoelectric model -------------------------------------------------

def test_literature_piezo_constants_are_the_published_alpha_quartz_values():
    assert pulse.D11_QUARTZ_C_PER_N == 2.31e-12
    assert pulse.D14_QUARTZ_C_PER_N == 0.727e-12
    assert pulse.EPS11_REL_QUARTZ == 4.52


def test_piezo_charge_is_d_times_force():
    q = pulse.piezo_charge(1e6, 1e-4, pulse.D11_QUARTZ_C_PER_N)
    assert q == pytest.approx(2.31e-12 * 1e6 * 1e-4, rel=1e-12)


def test_piezo_charge_scales_linearly_in_stress_and_area():
    base = pulse.piezo_charge(1e6, 1e-4)
    assert pulse.piezo_charge(2e6, 1e-4) == pytest.approx(2 * base)
    assert pulse.piezo_charge(1e6, 2e-4) == pytest.approx(2 * base)


def test_d14_gives_a_smaller_response_than_d11():
    assert (pulse.piezo_charge(1e6, 1e-4, pulse.D14_QUARTZ_C_PER_N)
            < pulse.piezo_charge(1e6, 1e-4, pulse.D11_QUARTZ_C_PER_N))


def test_piezo_capacitance_parallel_plate():
    c = pulse.piezo_capacitance(1e-4, 1e-3)
    assert c == pytest.approx(
        pulse.EPS0_F_PER_M * 4.52 * 1e-4 / 1e-3, rel=1e-12)


def test_piezo_voltage_is_area_independent():
    """V = d T t / (eps0 eps_r): the electrode area cancels."""
    v1 = pulse.piezo_voltage(1e6, 1e-4, 1e-3)
    v2 = pulse.piezo_voltage(1e6, 5e-4, 1e-3)
    assert v1 == pytest.approx(v2, rel=1e-12)
    expected = 2.31e-12 * 1e6 * 1e-3 / (pulse.EPS0_F_PER_M * 4.52)
    assert v1 == pytest.approx(expected, rel=1e-12)


def test_piezo_rejects_nonphysical_geometry():
    with pytest.raises(pulse.PulseModelError):
        pulse.piezo_charge(1e6, 0.0)
    with pytest.raises(pulse.PulseModelError):
        pulse.piezo_capacitance(1e-4, 0.0)


# --- modal spectrum ------------------------------------------------------

def test_modal_frequencies_are_the_free_free_harmonic_series():
    modes = pulse.modal_frequencies(0.1, 5720.0, 5)
    assert modes[0] == pytest.approx(5720.0 / 0.2, rel=1e-12)
    for n, f in enumerate(modes, start=1):
        assert f == pytest.approx(n * modes[0], rel=1e-12)


def test_default_velocity_is_the_documented_quartz_x_axis_value():
    assert pulse.QUARTZ_LONGITUDINAL_VELOCITY_X_MS == 5720.0


def test_modal_frequencies_refuse_nonphysical_inputs():
    with pytest.raises(pulse.PulseModelError):
        pulse.modal_frequencies(0.0)
    with pytest.raises(pulse.PulseModelError):
        pulse.modal_frequencies(0.1, 0.0)
    with pytest.raises(pulse.PulseModelError):
        pulse.modal_frequencies(0.1, 5720.0, 0)


# --- THE NULL: source frequency audit ------------------------------------

AUDIT = pulse.source_frequency_audit(0.1, n_draws=2000)


def test_audit_p_value_is_actually_computed_and_a_probability():
    """Not asserted significant. Asserted COMPUTED and in [0, 1]."""
    p = AUDIT["p_value"]
    assert isinstance(p, float)
    assert 0.0 <= p <= 1.0
    assert p >= 1.0 / (1 + AUDIT["null_draws"])   # add-one estimator floor
    assert AUDIT["null_at_least_as_good"] <= AUDIT["null_draws"]


def test_audit_never_claims_significance_at_or_above_alpha():
    """The binding honesty guard: no branch may report a finding at p>=alpha."""
    assert AUDIT["significant"] == (AUDIT["p_value"] < AUDIT["alpha"])
    if not AUDIT["significant"]:
        assert "NOT SIGNIFICANT" in AUDIT["verdict"]
        assert "no demonstrated relationship" in AUDIT["verdict"]


def test_audit_verdict_and_flag_cannot_disagree():
    claims_a_fit = "fits the computed modal spectrum better" in AUDIT["verdict"]
    assert claims_a_fit == AUDIT["significant"]


def test_audit_null_is_granularity_matched_not_a_continuum():
    """The v4.6 lesson, asserted on the record itself."""
    assert "integers in Hz" in AUDIT["null_granularity"]
    assert AUDIT["null_band_hz"] == pulse.NULL_BAND_HZ
    lo, hi = AUDIT["null_band_hz"]
    assert all(lo <= f <= hi for f in AUDIT["frequencies_hz"])


def test_audit_is_deterministic_under_its_documented_seed():
    a = pulse.source_frequency_audit(0.1, n_draws=500, seed=pulse.NULL_SEED)
    b = pulse.source_frequency_audit(0.1, n_draws=500, seed=pulse.NULL_SEED)
    assert a["p_value"] == b["p_value"]
    assert a["null_seed"] == pulse.NULL_SEED == 20260718


def test_audit_reports_when_every_source_frequency_is_below_the_fundamental():
    """A 10 cm quartz bar has a ~28.6 kHz fundamental. 1496/644/587 Hz
    are all far below it, so there is no mode to assign them to at all."""
    assert AUDIT["fundamental_hz"] == pytest.approx(28600.0, rel=1e-9)
    assert AUDIT["all_below_fundamental"] is True
    assert all(pf["below_fundamental"] for pf in AUDIT["per_frequency"])


def test_audit_covers_the_three_source_frequencies_verbatim():
    assert AUDIT["frequencies_hz"] == (1496, 644, 587)
    assert pulse.SOURCE_FREQUENCIES_HZ == (1496, 644, 587)
    assert AUDIT["claim_id"] == "R6-C-006"


def test_audit_declares_itself_not_bench_data():
    assert AUDIT["not_bench_data"] is True
    assert "is a measurement of any specimen" in AUDIT["ceiling"].lower()


def test_audit_refuses_a_band_too_narrow_for_the_candidate_set():
    with pytest.raises(pulse.PulseModelError):
        pulse.source_frequency_audit(0.1, band_hz=(100, 101), n_draws=10)


# --- claim-language guards ----------------------------------------------

def test_module_names_no_forbidden_state():
    import pathlib
    text = pathlib.Path(pulse.__file__).read_text(encoding="utf-8")
    for state in r6.FORBIDDEN_STATES:
        assert state not in text, f"{state} must never appear in R6"


def test_module_declares_it_holds_no_bench_data():
    assert "NOTHING IN THIS MODULE IS BENCH DATA" in pulse.__doc__
