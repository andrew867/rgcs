"""Regression tests for the RSCS Conservative Extension Property (CEP) and the
anti-Hermitian coupling convention (QA-D-04).

CEP: O_RSCS(iota(x)) == iota(O_RGCS(x)) within tolerance over the frozen v2
domain. These tests pin that RSCS reproduces the frozen RGCS-M.* numbers and
that the coupling convention has not regressed to real-symmetric K = pi*g.
"""
from __future__ import annotations

import math

import numpy as np

from rgcs_core.coupled_modes.static import coupled_two_mode
from rscs_core import embedding as emb
from rscs_core import units as U
from rscs_core.coupling import (anti_hermitian_coupling, couple_modes,
                                frequency_matrix)


def _evolve_conservative(f_hz, g_matrix_hz, z0, fs_hz, n_samples):
    """Exact unitary evolution under the anti-Hermitian coupling generator.

    The time-domain generator is dz/dt = i*Omega z + K z with Omega = 2*pi*f
    and K = i*2*pi*g, i.e. dz/dt = i*2*pi*H z where H = diag(f) + g (Hz) is the
    Hermitian frequency matrix. Hence z(t) = exp(i*2*pi*H t) z0, computed by
    eigendecomposition of the real-symmetric H. Unitary => norm-preserving
    (no growth); eigenfrequencies are the hybrids f0 +/- g."""
    h = frequency_matrix(f_hz, g_matrix_hz)
    lam, vec = np.linalg.eigh(h)
    coeffs = vec.conj().T @ np.asarray(z0, dtype=complex)
    t = np.arange(n_samples) / fs_hz
    # z(t)_j = sum_k vec[j,k] exp(i 2pi lam_k t) coeffs[k]
    phases = np.exp(1j * U.TWO_PI * np.outer(t, lam))   # (n, M)
    return (phases * coeffs) @ vec.T                     # (n, M)


# --- Conservative Extension Property battery ---

def test_two_mode_cep():
    r = emb.check_two_mode_cep(1000.0, 1000.0, 10.0)
    assert r["ok"] and r["anti_hermitian"]


def test_two_mode_cep_detuned():
    r = emb.check_two_mode_cep(1000.0, 1040.0, 7.0)
    assert r["ok"]


def test_n_mode_cep():
    r = emb.check_n_mode_cep(
        [1000.0, 1005.0, 1010.0],
        [[0.0, 3.0, 0.0], [3.0, 0.0, 3.0], [0.0, 3.0, 0.0]])
    assert r["ok"]


def test_analytic_signal_cep():
    x = np.sin(np.linspace(0, 20 * np.pi, 512))
    assert emb.check_analytic_signal_cep(x)["ok"]


def test_coherence_cep():
    seg = np.exp(1j * np.linspace(0, 50, 400))
    assert emb.check_coherence_cep(seg)["ok"]


def test_uncertainty_cep():
    assert emb.check_uncertainty_cep(6310.0, 0.05, 2.0)["ok"]


def test_full_cep_battery():
    assert emb.run_all_cep()["all_ok"]


def test_cep_matches_v2_golden_G08():
    # Golden G-08: f_A = f_B = 1000 Hz, g = 10 Hz -> 990/1010 Hz.
    v2 = coupled_two_mode(1000.0, 1000.0, 10.0)
    rscs = couple_modes([1000.0, 1000.0], [[0.0, 10.0], [10.0, 0.0]])
    assert math.isclose(rscs["hybrid_frequencies_hz"][0], v2["lower_hybrid_hz"],
                        rel_tol=1e-9)
    assert math.isclose(rscs["hybrid_frequencies_hz"][-1], v2["upper_hybrid_hz"],
                        rel_tol=1e-9)


# --- anti-Hermitian coupling convention (QA-D-04) ---

def test_anti_hermitian_structure():
    k = anti_hermitian_coupling([[0.0, 10.0], [10.0, 0.0]])
    assert np.allclose(k.conj().T, -k)          # K^dagger = -K
    assert math.isclose(abs(k[0, 1]), 2 * math.pi * 10.0)  # |K| = 2*pi*g


def test_anti_hermitian_2g_splitting():
    # A degenerate anti-Hermitian pair produces spectral peaks at f0 +/- g,
    # i.e. a 2g Hz frequency splitting. Read the spectrum of the exact
    # unitary evolution z(t) = exp(i 2*pi H t) z0.
    f0, g = 200.0, 8.0
    fs, n = 4000.0, 16000
    z = _evolve_conservative([f0, f0], [[0.0, g], [g, 0.0]],
                             [1 + 0j, 0 + 0j], fs, n)[:, 0]
    spec = np.abs(np.fft.fft(z * np.hanning(n)))
    freqs = np.fft.fftfreq(n, d=1.0 / fs)
    band = (freqs > f0 - 4 * g) & (freqs < f0 + 4 * g)
    fb, sb = freqs[band], spec[band]
    order = np.argsort(sb)[::-1]
    top = sorted(fb[order[:2]])
    assert math.isclose(top[1] - top[0], 2 * g, abs_tol=fs / n * 3), \
        f"expected 2g={2*g} Hz splitting, got {top[1]-top[0]:.3f}"


def test_no_growth_degenerate_pair():
    # Conservative (anti-Hermitian, no gain/damping) evolution is UNITARY and
    # must preserve total occupancy. A real-symmetric K = pi*g would instead
    # give exponential (cosh) growth of the norm -- the QA-D-04 failure mode.
    f0, g = 200.0, 8.0
    fs, n = 4000.0, 16000
    z = _evolve_conservative([f0, f0], [[0.0, g], [g, 0.0]],
                             [1 + 0j, 0 + 0j], fs, n)
    total = np.abs(z[:, 0]) ** 2 + np.abs(z[:, 1]) ** 2
    assert np.isfinite(total).all()
    # norm preserved to machine precision (started at 1)
    assert np.allclose(total, 1.0, atol=1e-9)


def test_anisotropy_reproduces_scalar_vL():
    # RSCS-O.17 (anisotropic Christoffel) generalizes the frozen scalar v_L
    # (RGCS-M.10, default 6310 m/s +/- 5%). Along the Z optic axis the
    # quasi-longitudinal speed must fall inside v2's declared uncertainty band
    # -- the conservative extension of the scalar model.
    from rgcs_core.anisotropy import axis_speeds
    from rgcs_core.uncertainty import default_wave_speed
    v2 = default_wave_speed()                 # mean 6310, u_rel 0.05
    lo, hi = v2.interval(k=1.0)               # +/- 1 sigma band
    z_ql = axis_speeds()["Z"]["v_quasi_long_m_s"]
    assert lo <= z_ql <= hi, f"Z quasi-long {z_ql} outside v2 band [{lo},{hi}]"


def test_real_symmetric_coupling_would_grow():
    # Guard the QA-D-04 correction: the WRONG real-symmetric generator
    # (K_real = pi*g, applied as a real coupling in the exponent) produces
    # norm GROWTH, which is exactly why it is forbidden. This test documents
    # the contrast; it does NOT use the RSCS operator (which is anti-Hermitian).
    f0, g = 200.0, 8.0
    fs, n = 4000.0, 4000
    # generator with a REAL symmetric off-diagonal (growth/decay of amplitude)
    gen = np.array([[1j * U.hz_to_rad_s(f0), math.pi * g],
                    [math.pi * g, 1j * U.hz_to_rad_s(f0)]], dtype=complex)
    lam, vec = np.linalg.eig(gen)
    z0 = np.array([1 + 0j, 0 + 0j])
    coeffs = np.linalg.solve(vec, z0)
    t = np.arange(n) / fs
    z = (np.exp(np.outer(t, lam)) * coeffs) @ vec.T
    total = np.abs(z[:, 0]) ** 2 + np.abs(z[:, 1]) ** 2
    # the forbidden real-symmetric coupling grows without bound
    assert np.max(total) > 10.0
