"""Tests for the RSCS2 analytic reference formulas (RSCS2-V.*). These are
closed-form truths, correct and testable independently of the FEM solver.
"""
from __future__ import annotations

import math

import pytest

from rscs2_core import reference as ref

# Steel bar used across the benchmarks.
E, NU, RHO = 210e9, 0.3, 7850.0
L, W, T = 0.1, 0.01, 0.01


def test_rod_longitudinal():
    # f1 = c/(2L), c = sqrt(E/rho)
    c = math.sqrt(E / RHO)
    assert ref.rod_longitudinal_free_free_hz(E, RHO, L, 1) == pytest.approx(
        c / (2 * L))
    # harmonics scale linearly
    assert ref.rod_longitudinal_free_free_hz(E, RHO, L, 3) == pytest.approx(
        3 * ref.rod_longitudinal_free_free_hz(E, RHO, L, 1))
    # fixed-free is a quarter-wave: f1 = c/(4L)
    assert ref.rod_longitudinal_fixed_free_hz(E, RHO, L, 1) == pytest.approx(
        c / (4 * L))


def test_cantilever_eb():
    # known value for this steel bar: ~835.5 Hz (first flexural)
    f1 = ref.euler_bernoulli_cantilever_hz(E, RHO, L, W, T, 1)
    assert f1 == pytest.approx(835.5, rel=1e-3)
    # mode ratios follow (beta_n L)^2
    f2 = ref.euler_bernoulli_cantilever_hz(E, RHO, L, W, T, 2)
    ratio = (ref.CANTILEVER_BETA_L[1] / ref.CANTILEVER_BETA_L[0]) ** 2
    assert f2 / f1 == pytest.approx(ratio, rel=1e-6)
    # frequency scales as thickness / length^2
    f_thick = ref.euler_bernoulli_cantilever_hz(E, RHO, L, W, 2 * T, 1)
    assert f_thick / f1 == pytest.approx(2.0, rel=1e-9)
    f_long = ref.euler_bernoulli_cantilever_hz(E, RHO, 2 * L, W, T, 1)
    assert f_long / f1 == pytest.approx(0.25, rel=1e-9)


def test_timoshenko_reduces_to_eb():
    G = ref.lame_from_e_nu(E, NU)[1]
    # very slender -> Timoshenko ~ EB
    slender = ref.timoshenko_cantilever_hz(E, G, RHO, 1.0, W, T, n=1)
    eb_slender = ref.euler_bernoulli_cantilever_hz(E, RHO, 1.0, W, T, 1)
    assert slender == pytest.approx(eb_slender, rel=1e-3)
    # thick beam -> Timoshenko strictly below EB (shear + rotary inertia)
    thick_t = ref.timoshenko_cantilever_hz(E, G, RHO, 0.05, W, 0.02, n=1)
    thick_eb = ref.euler_bernoulli_cantilever_hz(E, RHO, 0.05, W, 0.02, 1)
    assert thick_t < thick_eb


def test_lame_identity():
    lam, mu = ref.lame_from_e_nu(E, NU)
    # back out E, nu
    e_back = mu * (3 * lam + 2 * mu) / (lam + mu)
    nu_back = lam / (2 * (lam + mu))
    assert e_back == pytest.approx(E, rel=1e-9)
    assert nu_back == pytest.approx(NU, rel=1e-9)
