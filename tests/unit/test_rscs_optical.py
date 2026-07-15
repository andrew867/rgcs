"""Unit tests for the Agent 06 optical/nonreciprocal layer:
RSCS-C.16/C.17 coordinates, RSCS-O.18..O.23 operators, and the Jones<->Stokes
extension of RSCS-C.9.
"""
from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from rscs_core.coordinates import (DirectionalPropagation, OpticalCarrier,
                                   PolarizationState, SPEED_OF_LIGHT_M_S)
from rscs_core.coupling import (mode_conversion, nonreciprocal_metrics,
                                overlap_integral,
                                state_dependent_susceptibility)
from rscs_core.observation import (autler_townes_response,
                                   critical_coupling_transmission,
                                   is_critically_coupled, is_strong_coupling)
from rscs_core.propagation import (beating_length_mm, directional_betas,
                                   dispersion_group_delay, dispersion_phase)

REPO = Path(__file__).resolve().parents[2]


# --- coordinates ---

def test_optical_carrier():
    c = OpticalCarrier(632.8, 1e6)
    assert math.isclose(c.frequency_hz, SPEED_OF_LIGHT_M_S / 632.8e-9)
    assert math.isclose(c.omega0_rad_s, 2 * math.pi * c.frequency_hz)
    with pytest.raises(ValueError):
        OpticalCarrier(0.0)
    with pytest.raises(ValueError):
        OpticalCarrier(632.8, -1.0)
    with pytest.raises(ValueError):
        OpticalCarrier(float("nan"))


def test_directional_propagation():
    dp = DirectionalPropagation(10.0, 0.25)
    assert dp.forward_rad_mm == 10.25
    assert dp.backward_rad_mm == 9.75
    assert math.isclose(dp.nonreciprocal_split_rad_mm, 0.5)
    assert not dp.is_reciprocal
    assert DirectionalPropagation(10.0, 0.0).is_reciprocal
    with pytest.raises(ValueError):
        DirectionalPropagation(float("inf"), 0.0)


def test_jones_stokes_roundtrip():
    # right circular (1, i)/sqrt(2) -> sigma_plus
    s = PolarizationState.from_jones(1.0, 1j)
    assert math.isclose(s.helicity, 1.0, abs_tol=1e-12)
    # horizontal linear
    h = PolarizationState.from_jones(1.0, 0.0)
    assert np.allclose(h.stokes, (1.0, 0.0, 0.0))
    # round-trip through the representative Jones vector
    for st in [(1, 0, 0), (0, 1, 0), (0, 0, 1), (0, 0, -1),
               (0.6, 0.0, 0.8), (-0.36, 0.48, 0.8)]:
        p = PolarizationState(st)
        back = PolarizationState.from_jones(*p.jones)
        assert np.allclose(back.stokes, p.stokes, atol=1e-12)
    with pytest.raises(ValueError):
        PolarizationState.from_jones(0.0, 0.0)


# --- RSCS-O.18 dispersion phase ---

def test_dispersion_phase_at_carrier():
    # at omega = omega0 the expansion reduces to Delta_Phi0
    assert dispersion_phase(0.7, 1e-9, 1e-24, 5.0e14, 5.0e14) == 0.7


def test_dispersion_group_delay_is_derivative():
    dtau, db2, w0 = 2e-9, 3e-20, 1.0e15
    w = w0 + 1.0e9
    eps = 1.0
    num = (dispersion_phase(0.0, dtau, db2, w + eps, w0)
           - dispersion_phase(0.0, dtau, db2, w - eps, w0)) / (2 * eps)
    assert math.isclose(num, dispersion_group_delay(dtau, db2, w, w0),
                        rel_tol=1e-6)


# --- RSCS-O.19 mode conversion selection rules ---

def test_overlap_integral():
    a = np.array([1.0, 0.0])
    b = np.array([0.0, 1.0])
    assert overlap_integral(a, a) == pytest.approx(1.0)
    assert overlap_integral(a, b) == pytest.approx(0.0)
    # Cauchy-Schwarz bound with an arbitrary complex pair
    rng = np.random.default_rng(6)
    x = rng.normal(size=32) + 1j * rng.normal(size=32)
    y = rng.normal(size=32) + 1j * rng.normal(size=32)
    assert abs(overlap_integral(x, y)) <= 1.0 + 1e-12
    with pytest.raises(ValueError):
        overlap_integral(a, np.array([1.0, 2.0, 3.0]))
    with pytest.raises(ValueError):
        overlap_integral(np.zeros(4), np.ones(4))


def test_mode_conversion_selection_rules():
    w_in, omega, k_in, q = 1.0e15, 2 * math.pi * 40e6, 100.0, 0.5
    ok = mode_conversion(w_in, omega, w_in + omega, k_in, q, k_in + q,
                         parity_in=+1, parity_out=-1, overlap=1.0,
                         interaction_length_mm=10.0)
    assert ok["allowed"] and ok["frequency_matched"] and ok["parity_allowed"]
    assert ok["efficiency"] == pytest.approx(1.0)  # sinc(0)^2 * |1|^2
    # parity violation blocks conversion
    blocked = mode_conversion(w_in, omega, w_in + omega, k_in, q, k_in + q,
                              parity_in=+1, parity_out=+1, overlap=1.0,
                              interaction_length_mm=10.0)
    assert not blocked["allowed"] and blocked["efficiency"] == 0.0
    # momentum mismatch suppresses via sinc^2
    mism = mode_conversion(w_in, omega, w_in + omega, k_in, q,
                           k_in + q + 2.0, parity_in=+1, parity_out=-1,
                           overlap=1.0, interaction_length_mm=10.0)
    assert mism["efficiency"] < 0.05
    with pytest.raises(ValueError):
        mode_conversion(w_in, omega, w_in + omega, k_in, q, k_in + q,
                        parity_in=0, parity_out=-1, overlap=1.0,
                        interaction_length_mm=10.0)
    with pytest.raises(ValueError):
        mode_conversion(w_in, omega, w_in + omega, k_in, q, k_in + q,
                        parity_in=1, parity_out=-1, overlap=1.5,
                        interaction_length_mm=10.0)


# --- RSCS-O.20 Autler-Townes ---

def test_ats_peak_separation():
    kappa, g = 2 * math.pi * 1.0e3, 2 * math.pi * 50.0e3   # G >> kappa
    d = np.linspace(-2 * g, 2 * g, 40001)
    r = autler_townes_response(d, kappa, g)
    # find the two local maxima
    peaks = d[1:-1][(r[1:-1] > r[:-2]) & (r[1:-1] > r[2:])]
    assert len(peaks) == 2
    assert math.isclose(peaks[1] - peaks[0], g, rel_tol=1e-3)


def test_ats_single_peak_when_weak():
    kappa, g = 2 * math.pi * 10.0e3, 2 * math.pi * 100.0  # G << kappa
    d = np.linspace(-5 * kappa, 5 * kappa, 20001)
    r = autler_townes_response(d, kappa, g)
    peaks = d[1:-1][(r[1:-1] > r[:-2]) & (r[1:-1] > r[2:])]
    assert len(peaks) == 1
    assert not is_strong_coupling(g, kappa, kappa)
    assert is_strong_coupling(2 * kappa, kappa, kappa)


# --- RSCS-O.21 critical coupling ---

def test_critical_coupling_zero():
    # T(0) = 0 exactly at kappa_int == kappa_ext
    assert critical_coupling_transmission(1e6, 1e6, 0.0) == pytest.approx(0.0)
    assert is_critically_coupled(1e6, 1e6)
    # under/over-coupled transmit
    assert critical_coupling_transmission(2e6, 1e6, 0.0) > 0.05
    assert critical_coupling_transmission(1e6, 3e6, 0.0) > 0.05
    assert not is_critically_coupled(2e6, 1e6)
    # far off resonance -> full transmission
    assert critical_coupling_transmission(1e6, 1e6, 1e12) == pytest.approx(
        1.0, abs=1e-9)


# --- RSCS-O.22 state-dependent susceptibility + metrics ---

def test_state_dependent_susceptibility_linear():
    c = state_dependent_susceptibility(2.0 + 0j, 0.5, 4.0 + 0j, 0.25)
    assert c == pytest.approx(2.0)
    # both drivers zero -> zero coupling (reciprocal null)
    assert state_dependent_susceptibility(2.0, 0.0, 4.0, 0.0) == 0
    with pytest.raises(ValueError):
        state_dependent_susceptibility(2.0, 0.0, 4.0, 1.5)


def test_reciprocal_null():
    m = nonreciprocal_metrics(0.0, 9.93, 154.0)
    assert m["reciprocal"]
    assert m["transmittance_ratio"] == pytest.approx(1.0)
    assert m["nonreciprocal_phase_rad"] == pytest.approx(0.0)
    # imaginary part -> amplitude asymmetry; real part -> pure phase
    lossy = nonreciprocal_metrics(1e-6j, 1e4, 100.0)
    assert lossy["transmittance_ratio"] < 1.0
    assert lossy["nonreciprocal_phase_rad"] == pytest.approx(0.0)


# --- RSCS-O.23 directional betas / beating ---

def test_beating_length():
    assert beating_length_mm(10.0, 10.0 + math.pi) == pytest.approx(2.0)
    dp = DirectionalPropagation(12.0, 0.5)
    d = directional_betas(dp)
    assert d["split_rad_mm"] == pytest.approx(1.0)
    assert not d["reciprocal"]
    with pytest.raises(ValueError):
        beating_length_mm(7.0, 7.0)


# --- generated comparison table stays in sync ---

def test_comparison_table_up_to_date():
    r = subprocess.run(
        [sys.executable, str(REPO / "tools" / "generate_optical_comparison.py"),
         "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
