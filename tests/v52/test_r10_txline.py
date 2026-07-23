"""P11 — transmission-line reflection/standing waves and a grounding
safety firewall that never yields to EMI mitigation."""

from __future__ import annotations

import math

import pytest

from r10 import txline as T


# --- reflection coefficient and SWR (POWER) -----------------------------

def test_matched_load_gives_zero_gamma_and_swr_one():
    g = T.reflection_coefficient(50, 50)
    assert g == 0
    assert T.swr_from_gamma(g) == pytest.approx(1.0)


def test_open_and_short_give_unit_gamma_and_infinite_swr():
    g_open = T.gamma_for_termination(50, T.Termination.OPEN)
    g_short = T.gamma_for_termination(50, T.Termination.SHORT)
    assert abs(g_open) == pytest.approx(1.0)
    assert abs(g_short) == pytest.approx(1.0)
    assert math.isinf(T.swr_from_gamma(g_open))
    assert math.isinf(T.swr_from_gamma(g_short))


def test_planted_load_gives_the_analytic_gamma_and_swr():
    """Z0 = 50, ZL = 100 -> Gamma = 50/150 = 1/3, SWR = 2."""
    g = T.reflection_coefficient(50, 100)
    assert g == pytest.approx(1.0 / 3.0)
    assert T.swr_from_gamma(g) == pytest.approx(2.0)


def test_complex_load_gives_the_analytic_complex_gamma():
    """Z0 = 50, ZL = 50 + 50j -> Gamma = 50j / (100 + 50j)."""
    z0, zl = 50, 50 + 50j
    g = T.reflection_coefficient(z0, zl)
    expected = (zl - z0) / (zl + z0)
    assert g == pytest.approx(expected)
    # |Gamma| = |50j| / |100+50j| = 50 / sqrt(12500)
    assert abs(g) == pytest.approx(50.0 / math.sqrt(12500.0))


def test_superunity_gamma_is_refused_as_unphysical():
    with pytest.raises(T.TxLineError):
        T.swr_from_gamma(1.5 + 0j)


def test_negative_of_z0_load_is_a_model_error():
    with pytest.raises(T.TxLineError):
        T.reflection_coefficient(50, -50)


# --- delay and quarter-wave resonance -----------------------------------

def test_delay_is_length_over_vf_times_c():
    # 1 m, vf = 0.66 -> 1 / (0.66 * c)
    d = T.one_way_delay(1.0, 0.66)
    assert d == pytest.approx(1.0 / (0.66 * T.C_M_PER_S))


def test_lowest_quarter_wave_frequency_for_a_planted_length():
    # L = 0.5 m, vf = 1.0 -> f = c / (4 * 0.5) = c / 2
    f = T.lowest_quarter_wave_frequency(0.5, 1.0)
    assert f == pytest.approx(T.C_M_PER_S / 2.0)


def test_quarter_wave_frequencies_are_odd_multiples():
    fs = T.quarter_wave_frequencies(0.5, 1.0, count=3)
    f0 = T.lowest_quarter_wave_frequency(0.5, 1.0)
    assert fs == pytest.approx([f0, 3 * f0, 5 * f0])


def test_bad_velocity_factor_is_refused():
    with pytest.raises(T.TxLineError):
        T.one_way_delay(1.0, 0.0)
    with pytest.raises(T.TxLineError):
        T.one_way_delay(1.0, 1.5)


# --- the line schema ----------------------------------------------------

def test_matched_line_constructs_with_swr_one():
    line = T.TransmissionLine(
        line_id="LN_MATCHED",
        geometry=T.Geometry.COAX,
        length=2.0,
        termination=T.Termination.MATCHED,
        source_impedance=50,
        load_impedance=50,
        velocity_factor=0.66,
    )
    assert line.is_matched
    assert line.SWR == pytest.approx(1.0)
    assert line.delay == pytest.approx(2.0 / (0.66 * T.C_M_PER_S))
    assert line.status == "TXLINE_MODEL_ONLY"


def test_open_line_constructs_with_infinite_swr_and_resonance():
    line = T.TransmissionLine(
        line_id="LN_OPEN",
        geometry=T.Geometry.COAX,
        length=0.5,
        termination=T.Termination.OPEN,
        source_impedance=50,
        load_impedance=None,
        velocity_factor=1.0,
    )
    assert math.isinf(line.SWR)
    assert line.lowest_quarter_wave_frequency() == pytest.approx(
        T.C_M_PER_S / 2.0)


# --- SAFETY FIREWALL (load-bearing) -------------------------------------

def test_refusing_to_defeat_protective_earth_raises():
    with pytest.raises(T.SafetyViolation):
        T.refuse_defeat_protective_earth("to kill 60 Hz hum")


def test_refusing_to_connect_a_body_to_earth_raises():
    with pytest.raises(T.SafetyViolation):
        T.refuse_body_to_earth("as a static drain")


def test_constructing_a_line_that_defeats_pe_is_refused():
    with pytest.raises(T.SafetyViolation):
        T.TransmissionLine(
            line_id="LN_UNSAFE",
            geometry=T.Geometry.COAX,
            length=1.0,
            termination=T.Termination.MATCHED,
            source_impedance=50,
            load_impedance=50,
            velocity_factor=0.66,
            safety_class=T.SafetyClass.DEFEATS_PROTECTIVE_EARTH,
        )


def test_safe_mitigations_are_offered_and_never_mention_defeating_earth():
    mits = T.safe_ground_loop_mitigations()
    assert len(mits) >= 3
    joined = " ".join(mits).lower()
    assert "single-point" in joined or "star" in joined
    assert "isolation" in joined
    # the safe list must never advise removing protective earth
    assert "defeat" not in joined
    assert "lift the earth" not in joined


# --- report -------------------------------------------------------------

def test_report_is_model_only_and_measures_nothing():
    r = T.txline_report()
    assert r["measured_here"] == "nothing"
    assert r["verdict"] == "TXLINE_MODEL_ONLY"
    assert r["evidence_class"] == "DERIVED_MATHEMATICS"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"


def test_report_says_it_does_not_endorse_defeating_earth():
    r = T.txline_report()
    w = r["what_this_does_not_say"].lower()
    assert "protective earth" in w
    assert "measured" in w
