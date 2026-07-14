"""Regression test for QA-D-04: the K_nm <-> g_nm consistency map.

The corrected map is anti-Hermitian, K_nm = i*2*pi*g_nm (rad/s), so that
a degenerate pair coupled at g (Hz) shows spectral peaks at f0 +/- g
(splitting 2g Hz) and an amplitude beat |z1| = |cos(2*pi*g*t)|.

The former (wrong) map K = pi*g with real-symmetric coupling produces a
growth-rate splitting (cosh growth) and NO frequency splitting; the
second test pins that failure mode so it cannot silently return.
"""

import math

import numpy as np
import pytest

from rgcs_core.coupled_modes import (integrate_stuart_landau,
                                     coupling_rate_from_g_hz,
                                     g_hz_from_coupling_rate,
                                     coupling_consistency)

F0 = 100.0     # Hz, degenerate pair
G = 2.0        # Hz, frequency-domain half-splitting
FS = 50000.0   # Hz (fine step: the Euler-Maruyama coupling term has
               # O(omega*K*dt^2) amplitude drift at coarse steps)
N = 100000     # 2 s -> FFT resolution 0.5 Hz


def _integrate(k_matrix):
    return integrate_stuart_landau(
        omega_rad_s=[2 * math.pi * F0, 2 * math.pi * F0],
        gain_s=[0.0, 0.0], damping_s=[0.0, 0.0],
        beta=[[0.0, 0.0], [0.0, 0.0]],
        coupling_k_s=k_matrix,
        z0=[1.0 + 0.0j, 0.0 + 0.0j],
        fs_hz=FS, n_samples=N)


def _spectral_peaks(z):
    spec = np.abs(np.fft.fft(z))
    freqs = np.fft.fftfreq(z.size, d=1.0 / FS)
    pos = freqs > 0
    spec, freqs = spec[pos], freqs[pos]
    # the two strongest positive-frequency components
    order = np.argsort(spec)[::-1]
    return sorted(freqs[order[:2]])


def test_anti_hermitian_coupling_reproduces_2g_frequency_splitting():
    kmag = coupling_rate_from_g_hz(G)
    assert kmag == pytest.approx(2 * math.pi * G)
    k = [[0.0, 1j * kmag], [1j * kmag, 0.0]]
    res = _integrate(k)
    z1 = res["z"][:, 0]
    # bounded (no exponential runaway; small integrator drift allowed)
    assert np.max(np.abs(z1)) < 1.6
    # spectral peaks at f0 +/- g -> splitting 2g
    lo, hi = _spectral_peaks(z1)
    assert lo == pytest.approx(F0 - G, abs=0.5)
    assert hi == pytest.approx(F0 + G, abs=0.5)
    assert hi - lo == pytest.approx(2 * G, abs=1.0)
    # amplitude beat |cos(2 pi g t)|: first node near t = 1/(4g)
    t = res["t_s"]
    i_node = int(np.argmin(np.abs(z1[: int(FS / (2 * G))])))
    assert t[i_node] == pytest.approx(1.0 / (4 * G), abs=2.0 / FS)
    # round trip and consistency gate
    assert g_hz_from_coupling_rate(kmag) == pytest.approx(G)
    assert coupling_consistency(kmag, G)["consistent"]


def test_real_symmetric_coupling_splits_growth_not_frequency():
    # The pre-correction (wrong) structure: real symmetric K of the old
    # magnitude pi*g. Degenerate eigenvalues i*w +/- K -> cosh growth of
    # |z1| with NO frequency splitting. This is why K = pi*g was wrong.
    kmag = math.pi * G
    res = _integrate([[0.0, kmag], [kmag, 0.0]])
    z1 = res["z"][:, 0]
    # monotone-ish exponential growth, no beat node
    assert np.abs(z1[-1]) > np.cosh(kmag * (N - 1) / FS) * 0.5
    assert np.min(np.abs(z1)) >= 1.0 - 1e-6
    # single spectral line at f0 (both top components within FFT
    # resolution of f0, not split by 2g)
    lo, hi = _spectral_peaks(z1)
    assert hi - lo <= 1.0  # << 2g = 4 Hz


def test_old_pi_g_map_now_flags_inconsistent():
    # A pair fitted correctly in both domains under the OLD map
    # (K = pi*g) must now trip the pre-registered warning flag.
    res = coupling_consistency(math.pi * G, G)
    assert res["warning_flag"] and not res["consistent"]
