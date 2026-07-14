"""Hypothesis property tests for rgcs_core invariants."""

from __future__ import annotations

import math

import numpy as np
import pytest
from hypothesis import given, settings, strategies as st

from rgcs_core.uncertainty import UncertainValue
from rgcs_core.geometry import (CrystalGeometry, crystal_geometry,
                                polygon_area_mm2,
                                solve_diameter_scale_for_mass,
                                female_to_male_frame_mm, node_prior_mm)
from rgcs_core.harmonics import axial_half_wave, ladder_length_mm
from rgcs_core.compact_modes import compact_mode_spectrum, parity_index_set
from rgcs_core.resonance import resonance_offset, linear_detuning
from rgcs_core.coupled_modes import coupled_two_mode, n_mode_eigenproblem
from rgcs_core.coherence import (coherence_window, circular_variance,
                                 phase_linearity, phase_locking_value,
                                 phase_rate_shear_scalar)

finite = st.floats(allow_nan=False, allow_infinity=False)
pos_freq = st.floats(min_value=10.0, max_value=1e6)
pos_len = st.floats(min_value=1.0, max_value=1e4)


# ------------------------------------------------------------- spectra

@given(fb=st.floats(min_value=0.0, max_value=1e4),
       kappa=st.floats(min_value=1.0, max_value=1e5))
def test_compact_spectrum_monotone_in_n(fb, kappa):
    s = compact_mode_spectrum(fb, kappa=UncertainValue(kappa, 0.02),
                              n_max=10, parity="all")
    freqs = [r["frequency"]["mean"] for r in s["modes"]]
    assert all(b > a for a, b in zip(freqs, freqs[1:]))


@given(n_max=st.integers(min_value=0, max_value=50),
       flag=st.booleans())
def test_parity_families_partition(n_max, flag):
    odd = parity_index_set("odd", n_max)
    even = parity_index_set("even", n_max, include_zero_mode=flag)
    both = parity_index_set("all", n_max, include_zero_mode=flag)
    assert 0 not in odd
    assert set(odd).isdisjoint(even)
    assert sorted(set(odd) | set(even)) == both


# -------------------------------------------------------- eigenproblems

@given(fa=pos_freq, fb=pos_freq,
       g=st.floats(min_value=0.0, max_value=1e4))
def test_two_mode_eigenvalue_bracketing(fa, fb, g):
    r = coupled_two_mode(fa, fb, g)
    lo, hi = r["lower_hybrid_hz"], r["upper_hybrid_hz"]
    assert lo <= min(fa, fb) + 1e-9
    assert hi >= max(fa, fb) - 1e-9
    assert r["splitting_hz"] >= abs(fa - fb) - 1e-9
    if g == 0.0:
        assert r["splitting_hz"] == pytest.approx(abs(fa - fb), abs=1e-9)


@settings(max_examples=40)
@given(st.integers(min_value=2, max_value=6), st.integers(0, 2 ** 31 - 1))
def test_n_mode_eigenvalue_interlacing(n, seed):
    """Cauchy interlacing: eigenvalues of the leading (n-1) principal
    submatrix interlace those of the full symmetric matrix."""
    rng = np.random.default_rng(seed)
    f = np.sort(1000.0 + 500.0 * rng.random(n))
    g = rng.normal(0.0, 5.0, (n, n))
    g = 0.5 * (g + g.T)
    np.fill_diagonal(g, 0.0)
    full = n_mode_eigenproblem(f, g)["hybrid_frequencies_hz"]
    sub = np.linalg.eigvalsh(np.diag(f[:n - 1]) + g[:n - 1, :n - 1])
    for k in range(n - 1):
        assert full[k] <= sub[k] + 1e-9
        assert sub[k] <= full[k + 1] + 1e-9


# ------------------------------------------------------------ resonance

@given(fm=pos_freq, fx=pos_freq,
       p=st.floats(min_value=0.5, max_value=4.0))
def test_offset_detuning_identity_property(fm, fx, p):
    eps = resonance_offset(fm, fx, p)
    d = linear_detuning(fm, fx, p)
    assert eps == pytest.approx((1 + d) ** 2 - 1, rel=1e-9, abs=1e-12)
    assert eps > -1.0


# ------------------------------------------------------------- geometry

@given(d=st.floats(min_value=0.1, max_value=1e3),
       n=st.integers(min_value=3, max_value=64),
       s=st.floats(min_value=0.1, max_value=10.0))
def test_polygon_area_scales_quadratically(d, n, s):
    a1 = polygon_area_mm2(d, n)
    a2 = polygon_area_mm2(d * s, n)
    assert a2 == pytest.approx(a1 * s * s, rel=1e-9)


@settings(max_examples=20, deadline=None)
@given(scale=st.floats(min_value=0.5, max_value=2.0))
def test_density_inverse_recovers_scale(scale):
    g = CrystalGeometry(length_mm=154.0, wide_diameter_mm=31.6,
                        narrow_diameter_mm=26.9)
    scaled = g.model_copy(update={
        "wide_diameter_mm": g.wide_diameter_mm * scale,
        "narrow_diameter_mm": g.narrow_diameter_mm * scale})
    mass = crystal_geometry(scaled)["mass_g"]
    sol = solve_diameter_scale_for_mass(g, mass)
    assert sol["diameter_scale"] == pytest.approx(scale, rel=1e-6)


@given(length=pos_len, frac=st.floats(min_value=0.0, max_value=1.0))
def test_frame_round_trip(length, frac):
    x = frac * length
    assert female_to_male_frame_mm(
        female_to_male_frame_mm(x, length), length) == pytest.approx(
        x, abs=1e-9)


@given(length=st.floats(min_value=10.0, max_value=1e3),
       f1=st.floats(min_value=0.01, max_value=0.4),
       f2=st.floats(min_value=0.01, max_value=0.4))
def test_node_prior_inside_shaft(length, f1, f2):
    hf, hm = f1 * length, f2 * length
    xg = node_prior_mm(length, hf, hm)
    assert hf <= xg <= length - hm     # shaft midpoint lies in the shaft


# ---------------------------------------------------- unit round trips

@given(length=pos_len)
def test_ladder_frequency_length_round_trip(length):
    """mm -> Hz -> mm round trip through the half-wave pair (unit test of
    the single-conversion rule)."""
    f = axial_half_wave(length, wave_speed=6310.0)
    # L = v/(2 f), back in mm.
    back = 6310.0 / (2.0 * f.mean) * 1000.0
    assert back == pytest.approx(length, rel=1e-12)


@given(n=st.integers(min_value=1, max_value=64))
def test_ladder_length_reproduces_base_frequency(n):
    ln = ladder_length_mm(n, wave_speed=6310.0)
    f = axial_half_wave(ln.mean, wave_speed=6310.0)
    assert f.mean == pytest.approx(n * 4096.0, rel=1e-12)


# ------------------------------------------------------------ coherence

@settings(max_examples=30)
@given(st.integers(0, 2 ** 31 - 1), st.integers(min_value=8, max_value=256))
def test_coherence_window_in_unit_interval(seed, n):
    rng = np.random.default_rng(seed)
    z = rng.standard_normal(n) + 1j * rng.standard_normal(n)
    c = coherence_window(z)
    assert 0.0 <= c <= 1.0 + 1e-9


@settings(max_examples=30)
@given(st.integers(0, 2 ** 31 - 1), st.integers(min_value=4, max_value=200))
def test_circular_variance_in_unit_interval(seed, n):
    rng = np.random.default_rng(seed)
    v = circular_variance(rng.uniform(-np.pi, np.pi, n))
    assert 0.0 <= v <= 1.0


@settings(max_examples=20)
@given(st.floats(min_value=100.0, max_value=20_000.0),
       st.floats(min_value=-3.0, max_value=3.0))
def test_phase_linearity_one_for_any_tone(f0, phase0):
    t = np.arange(512) / 100_000.0
    z = np.exp(1j * (2 * np.pi * f0 * t + phase0))
    assert phase_linearity(z) == pytest.approx(1.0, abs=1e-9)


@settings(max_examples=30)
@given(st.integers(0, 2 ** 31 - 1))
def test_plv_bounds_and_self_locking(seed):
    rng = np.random.default_rng(seed)
    a = np.cumsum(rng.standard_normal(300))
    b = np.cumsum(rng.standard_normal(300))
    plv = phase_locking_value(a, b)
    assert 0.0 <= plv <= 1.0 + 1e-12
    assert phase_locking_value(a, a + 1.234) == pytest.approx(1.0)


@given(h1=st.floats(-1e3, 1e3), h2=st.floats(-1e3, 1e3),
       h3=st.floats(-1e3, 1e3), c=st.floats(-1e3, 1e3))
def test_shear_scalar_invariances(h1, h2, h3, c):
    s = phase_rate_shear_scalar(h1, h2, h3)["sigma_phi2_s2"]
    assert s >= 0.0
    s_perm = phase_rate_shear_scalar(h3, h1, h2)["sigma_phi2_s2"]
    s_shift = phase_rate_shear_scalar(h1 + c, h2 + c, h3 + c)["sigma_phi2_s2"]
    assert s_perm == pytest.approx(s, rel=1e-9, abs=1e-6)
    assert s_shift == pytest.approx(s, rel=1e-9, abs=1e-6)


@given(m=st.floats(min_value=0.1, max_value=1e5),
       u=st.floats(min_value=0.0, max_value=0.5),
       k=st.floats(min_value=0.1, max_value=100.0))
def test_uncertain_value_scale_invariant(m, u, k):
    v = UncertainValue(m, u)
    assert v.scale(k).u_rel == v.u_rel
    assert v.scale(k).mean == pytest.approx(m * k)
    lo, hi = v.interval()
    assert lo <= m <= hi
