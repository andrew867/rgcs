"""P15/P17 — quadrature drive, six-pole schemes, and the polarity firewall.

The load-bearing tests are the ones that would fail if the maths were
wrong or the firewall were relaxed: the rotating field must actually be
constant-magnitude, the balanced drive must sum to *exactly* zero, the
three six-pole schemes must be *measurably* different (not asserted to
be), and reading four poles as four charge polarities must raise.

Every test names an input that makes it fail: change 90 to 91 in the
offsets and the rotation test fails; drop the 180-degree pairing and
the zero-sum fails; make alternating triads sinusoidal and the
distinguishing test fails.
"""

from __future__ import annotations

import math
from fractions import Fraction as F

import pytest

from r10 import polarity as P


# --- exact geometry: offsets are integer degrees -----------------------

def test_four_pole_offsets_are_exact_integers():
    assert P.phase_offsets_deg(4) == (0, 90, 180, 270)
    # exactly integers, not floats that happen to look right
    assert all(isinstance(o, int) for o in P.phase_offsets_deg(4))


def test_six_pole_offsets_are_exact_integers():
    assert P.phase_offsets_deg(6) == (0, 60, 120, 180, 240, 300)
    assert all(isinstance(o, int) for o in P.phase_offsets_deg(6))


def test_pole_count_that_does_not_divide_360_is_refused():
    # 7 poles cannot have an integer-degree spacing; refuse, do not round
    with pytest.raises(P.WaveformError):
        P.pole_angles_deg(7)
    with pytest.raises(P.WaveformError):
        P.pole_angles_deg(0)


# --- P15: the four waveform families all run and differ ----------------

@pytest.mark.parametrize("family", P.FOUR_POLE_FAMILIES)
def test_every_four_pole_family_produces_four_currents(family):
    cur = P.channel_currents(family, 0.7, amplitude=2.0)
    assert len(cur) == 4
    assert all(abs(c) <= 2.0 + 1e-12 for c in cur)   # bounded by amplitude


def test_unknown_family_is_refused():
    with pytest.raises(P.WaveformError):
        P.channel_currents("TRIANGLE_MADE_UP", 0.0)


def test_families_have_distinct_harmonic_content():
    # if two families collapsed to the same shape this would fail
    def thd(family):
        fx = [P.field_vector(
                  P.channel_currents(family, 2 * math.pi * s / 720),
                  P.FOUR_POLE_ANGLES_DEG)[0]
              for s in range(720)]
        return P.total_harmonic_distortion(fx)

    sinus = thd("SINUSOIDAL_QUADRATURE")
    overlap = thd("OVERLAP")
    stepped = thd("PULSE_STEPPED")
    assert sinus < 1e-6                    # pure fundamental
    assert overlap > sinus                 # corners add harmonics
    assert stepped > overlap               # a square wave adds more


def test_pwm_average_reconstructs_the_sinusoidal_reference():
    # PWM is bipolar +/-A instantaneously; its *duty cycle* carries the
    # sinusoid. Block-averaging one carrier period at a time must
    # recover a cosine. A DC or wrong-shape PWM would fail this.
    R = 21
    fine = R * 50
    vals = [P.channel_currents("PWM", 2 * math.pi * s / fine,
                              carrier_ratio=R)[0]
            for s in range(fine)]
    w = fine // R
    recon = [sum(vals[i:i + w]) / w for i in range(0, fine, w)]
    ref = [math.cos(2 * math.pi * (i + w / 2) / fine)
           for i in range(0, fine, w)]
    max_err = max(abs(a - b) for a, b in zip(recon, ref))
    assert max_err < 0.1


# --- P15 item 3: the rotating-field magnitude test ---------------------

def test_sinusoidal_quadrature_is_constant_magnitude_rotation():
    r = P.rotating_field_report(amplitude=1.0, samples=720)
    assert r["mean_magnitude"] == pytest.approx(2.0, abs=1e-9)
    assert r["is_constant_magnitude"]
    assert r["relative_ripple"] < 1e-9


def test_rotating_field_actually_rotates_through_every_angle():
    # the resultant should sweep a full turn, not sit still
    angles = P.FOUR_POLE_ANGLES_DEG
    dirs = set()
    for s in range(360):
        phase = 2 * math.pi * s / 360
        fx, fy = P.field_vector(
            P.channel_currents("SINUSOIDAL_QUADRATURE", phase), angles)
        dirs.add(round(math.atan2(fy, fx), 3))
    assert len(dirs) > 300           # a genuine continuous rotation


def test_rotation_amplitude_scales_with_drive():
    r = P.rotating_field_report(amplitude=3.0, samples=360)
    assert r["mean_magnitude"] == pytest.approx(6.0, abs=1e-9)


# --- P15 item 4: THE FIREWALL ------------------------------------------

def test_four_poles_are_not_four_charge_polarities():
    with pytest.raises(P.ChargePolarityConflation) as exc:
        P.refuse_four_charge_polarities()
    msg = str(exc.value).lower()
    assert "coil" in msg or "position" in msg
    assert "two signs" in msg or "geometry" in msg


def test_report_advertises_the_firewall():
    rep = P.polarity_report()
    assert "not four charge polarities" in rep["the_firewall"]
    assert rep["measured_here"] == "nothing"
    assert "DEFERRED" in rep["hardware_status"]


# --- P15 item 5: signed states and the EXACT zero-sum ------------------

def test_canonical_sign_patterns_are_four_and_balanced():
    pats = P.canonical_sign_patterns()
    assert len(pats) == 4
    for p in pats:
        # exact: net current is a Fraction equal to integer zero
        assert isinstance(p["net_current"], F)
        assert p["net_current"] == 0
        assert p["sums_to_zero"]
        assert p["pairing_holds"]
        # each pattern has two positive and two negative signs
        assert sorted(p["signs"]) == [-1, -1, 1, 1]


def test_sign_patterns_are_all_distinct():
    signs = [p["signs"] for p in P.canonical_sign_patterns()]
    assert len(set(signs)) == 4


def test_cardinal_states_sum_to_exactly_zero():
    for st in P.cardinal_current_states(F(5)):
        assert isinstance(st["net_current"], F)
        assert st["net_current"] == 0           # exact, not approx
    # and the phases are the four cardinals
    assert [s["phase_deg"] for s in P.cardinal_current_states()] == \
        [0, 90, 180, 270]


def test_zero_sum_would_fail_if_pairing_broke():
    # sanity: an *unbalanced* quad does not sum to zero, so the test
    # above is not vacuous
    bad = (F(2), F(1), F(-2), F(0))
    assert sum(bad) != 0


# --- P17: six-pole schemes, and the real distinction between them ------

def test_all_three_six_pole_schemes_run():
    for scheme in P.SIX_POLE_SCHEMES:
        cur = P.six_pole_currents(scheme, 0.4, amplitude=1.0)
        assert len(cur) == 6


def test_unknown_scheme_is_refused():
    with pytest.raises(P.WaveformError):
        P.six_pole_currents("NINE_PHASE_IMAGINARY", 0.0)


def test_six_phase_and_dual_three_phase_agree_everywhere():
    # the two sinusoidal schemes must trace the SAME locus
    angles = P.SIX_POLE_ANGLES_DEG
    for s in range(500):
        phase = 2 * math.pi * s / 500
        f6 = P.field_vector(
            P.six_pole_currents("TRUE_SIX_PHASE", phase), angles)
        fd = P.field_vector(
            P.six_pole_currents("DUAL_THREE_PHASE", phase), angles)
        assert f6[0] == pytest.approx(fd[0], abs=1e-9)
        assert f6[1] == pytest.approx(fd[1], abs=1e-9)


def test_dual_three_phase_currents_match_six_phase():
    # stronger: the assembled two-set currents equal the six-phase ones
    for s in range(50):
        phase = 2 * math.pi * s / 50
        a = P.true_six_phase_currents(phase)
        b = P.dual_three_phase_currents(phase)
        assert a == pytest.approx(b, abs=1e-9)


def test_alternating_triads_is_measurably_different():
    c = P.compare_six_pole_schemes(samples=720)
    six = c["schemes"]["TRUE_SIX_PHASE"]
    dual = c["schemes"]["DUAL_THREE_PHASE"]
    alt = c["schemes"]["ALTERNATING_TRIADS"]

    # the two sinusoidal schemes: no harmonics, a full continuous sweep
    assert six["thd_fx"] < 1e-6
    assert dual["thd_fx"] < 1e-6
    assert six["distinct_field_directions"] > 500
    assert dual["distinct_field_directions"] > 500

    # alternating triads: real harmonic content and only a few directions
    assert alt["thd_fx"] > 0.1
    assert alt["distinct_field_directions"] <= 12
    assert alt["relative_magnitude_ripple"] > 0.05


def test_agreement_gaps_confirm_the_comparison():
    c = P.compare_six_pole_schemes(samples=360)
    ag = c["agreement"]
    # six-phase and dual coincide; alternating is far off
    assert ag["six_phase_vs_dual_max_field_gap"] < 1e-9
    assert ag["six_phase_vs_alternating_max_field_gap"] > 1.0


def test_six_phase_field_magnitude_is_three_amplitudes():
    # F = 3A rotating for a balanced six-phase sinusoid
    mags = P.compare_six_pole_schemes(amplitude=2.0,
                                      samples=360)["schemes"]
    assert mags["TRUE_SIX_PHASE"]["mean_magnitude"] == \
        pytest.approx(6.0, abs=1e-9)
    assert mags["TRUE_SIX_PHASE"]["relative_magnitude_ripple"] < 1e-9


# --- harmonic analysis sanity ------------------------------------------

def test_thd_of_pure_cosine_is_zero():
    n = 512
    cos = [math.cos(2 * math.pi * k / n) for k in range(n)]
    assert P.total_harmonic_distortion(cos) < 1e-9


def test_thd_of_square_wave_is_positive_and_known():
    n = 512
    sq = [1.0 if k < n // 2 else -1.0 for k in range(n)]
    # an ideal square wave has THD ~ 0.483
    assert P.total_harmonic_distortion(sq) == pytest.approx(0.483, abs=0.02)


# --- driver limits are parameters, not measurements --------------------

def test_driver_limits_are_parameters_not_measurements():
    d = P.DriverLimits(max_current_a=2.0, supply_voltage_v=12.0,
                       energy_budget_j=0.5)
    assert d.calibration_id == "UNCALIBRATED_NO_HARDWARE"
    with pytest.raises(ValueError):
        P.DriverLimits(max_current_a=-1.0, supply_voltage_v=12.0,
                       energy_budget_j=0.5)


def test_report_makes_no_physical_claim():
    rep = P.polarity_report()
    assert rep["evidence_class"] == "DERIVED_MATHEMATICS"
    low = rep["what_this_is_not"].lower()
    assert "gateway" in low and "propulsion" in low
