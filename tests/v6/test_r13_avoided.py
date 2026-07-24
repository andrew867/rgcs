"""P11 — avoided crossings in a two-level system, analytic model."""

from __future__ import annotations

import math

import numpy as np
import pytest

from r13 import avoided as A


# --- the gap is 2|g| ------------------------------------------------------

def test_minimum_gap_over_the_sweep_equals_twice_the_coupling():
    """POWER: the swept minimum gap lands on 2*|g| exactly, at delta = 0."""
    g = 0.05
    sweep = A.avoided_crossing_sweep(lambda x: x, lambda x: -x, g,
                                     n_points=201, span=1.0, x0=0.0)
    assert sweep["minimum_matches_twice_the_coupling"] is True
    assert sweep["minimum_gap"] == pytest.approx(2.0 * abs(g), abs=1e-9)
    assert sweep["x_at_minimum"] == pytest.approx(0.0, abs=1e-12)
    assert sweep["gap_never_below_twice_the_coupling"] is True


def test_a_wrong_gap_would_fail():
    """The check is falsifiable: 2*|g| is not 4*|g|."""
    g = 0.05
    sweep = A.avoided_crossing_sweep(lambda x: x, lambda x: -x, g,
                                     n_points=51, span=1.0)
    assert sweep["minimum_gap"] != pytest.approx(4.0 * abs(g))


def test_avoided_gap_closed_form():
    assert A.avoided_gap(0.05) == pytest.approx(0.1)
    assert A.avoided_gap(3.0 + 4.0j) == pytest.approx(10.0)


def test_zero_coupling_gives_a_real_crossing():
    """g = 0: the branches touch (gap 0) at the degeneracy point."""
    sweep = A.avoided_crossing_sweep(lambda x: x, lambda x: -x, 0.0,
                                     n_points=101, span=1.0)
    assert A.avoided_gap(0.0) == 0.0
    assert sweep["minimum_gap"] == pytest.approx(0.0, abs=1e-12)
    assert sweep["branches_never_cross"] is False
    assert sweep["expected_minimum_gap"] == 0.0


def test_spectrum_gap_matches_closed_form_off_resonance():
    spec = A.two_level_spectrum(1.0, -1.0, 0.3)
    delta = 0.5 * (1.0 - (-1.0))
    assert spec.gap == pytest.approx(2.0 * math.hypot(delta, 0.3))


# --- eigenvector swap across x0 ------------------------------------------

def test_eigenvectors_swap_character_across_the_crossing():
    swap = A.diabatic_adiabatic_swap(lambda x: x, lambda x: -x, 0.05,
                                     x_low=-1.0, x_high=1.0)
    assert swap["far_side_upper_overlap"] < 0.1
    assert swap["characters_swap"] is True
    assert swap["adiabatic_labelling_is_continuous"] is True


def test_swap_requires_ordered_bounds():
    with pytest.raises(A.AvoidedError):
        A.diabatic_adiabatic_swap(lambda x: x, lambda x: -x, 0.05,
                                  x_low=1.0, x_high=-1.0)


# --- Landau-Zener limits --------------------------------------------------

def test_landau_zener_fast_sweep_is_diabatic():
    """P -> 1 as the sweep rate grows without bound (natural units)."""
    p_fast = A.landau_zener_probability(1.0, sweep_rate=1e6, hbar=1.0)
    assert p_fast == pytest.approx(1.0, abs=1e-4)


def test_landau_zener_slow_sweep_is_adiabatic():
    """P -> 0 as the sweep rate goes to zero (natural units)."""
    p_slow = A.landau_zener_probability(1.0, sweep_rate=1e-6, hbar=1.0)
    assert p_slow < 1e-6
    assert A.landau_zener_probability(1.0, sweep_rate=0.0, hbar=1.0) == 0.0


def test_landau_zener_is_monotone_in_rate():
    p_lo = A.landau_zener_probability(1.0, sweep_rate=0.5, hbar=1.0)
    p_hi = A.landau_zener_probability(1.0, sweep_rate=2.0, hbar=1.0)
    assert p_hi > p_lo
    assert 0.0 < p_lo < p_hi < 1.0


def test_landau_zener_limits_helper_reports_both_ends():
    limits = A.landau_zener_limits()
    assert limits["fast_is_diabatic"] is True
    assert limits["slow_is_adiabatic"] is True


def test_negative_rate_is_refused():
    with pytest.raises(A.AvoidedError):
        A.landau_zener_probability(0.05, sweep_rate=-1.0)


# --- the refusal ----------------------------------------------------------

def test_refuse_model_crossing_as_measured_raises():
    with pytest.raises(A.AvoidedError):
        A.refuse_model_crossing_as_measured(minimum_gap=0.1)


# --- structural refusals --------------------------------------------------

def test_non_finite_inputs_are_refused():
    with pytest.raises(A.AvoidedError):
        A.avoided_gap(float("inf"))
    with pytest.raises(A.AvoidedError):
        A.two_level_hamiltonian(float("nan"), 0.0, 0.1)


def test_even_n_points_is_refused():
    with pytest.raises(A.AvoidedError):
        A.avoided_crossing_sweep(lambda x: x, lambda x: -x, 0.05,
                                 n_points=200)


# --- report ---------------------------------------------------------------

def test_report_verdict_and_no_measurement():
    r = A.avoided_report()
    assert r["verdict"] == "AVOIDED_CROSSING_MODEL_ANALYTIC"
    assert r["claim_class"] == "ANALYTIC_MODEL"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert "what_this_does_not_say" in r
    assert r["the_sweep"]["minimum_matches_twice_the_coupling"] is True
