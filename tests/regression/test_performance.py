"""Non-gating performance benchmarks (marker: benchmark).

Limits are deliberately generous (~10x expected) so this never gates a
release on machine noise; timings are printed for the test report.
"""

from __future__ import annotations

import math
import time

import numpy as np
import pytest

from rgcs_core.coherence import coherence_series, spatial_phase_anisotropy, \
    instantaneous_phase
from rgcs_core.geometry import SpiralGeometry, spiral_metrics
from rgcs_core.coupled_modes import integrate_stuart_landau


@pytest.mark.benchmark
def test_benchmark_coherence_series():
    fs = 100_000.0
    t = np.arange(int(0.5 * fs)) / fs                 # 0.5 s record
    z = np.exp(1j * 2 * np.pi * 5000.0 * t)
    t0 = time.perf_counter()
    tc, c = coherence_series(z, fs)
    dt = time.perf_counter() - t0
    print(f"\ncoherence_series: {tc.size} windows over "
          f"{z.size} samples in {dt:.3f} s")
    assert dt < 30.0                                   # non-gating headroom


@pytest.mark.benchmark
def test_benchmark_spiral_convergence():
    t0 = time.perf_counter()
    m = spiral_metrics(SpiralGeometry())
    dt = time.perf_counter() - t0
    print(f"\nspiral_metrics (converged {m['path_length_samples']} "
          f"samples) in {dt:.3f} s")
    assert dt < 10.0


@pytest.mark.benchmark
def test_benchmark_stuart_landau():
    t0 = time.perf_counter()
    out = integrate_stuart_landau(
        [2 * math.pi * 1000.0, 2 * math.pi * 1080.0], [400.0, 400.0],
        [100.0, 100.0], [[1.0, 0.0], [0.0, 1.0]],
        [[0.0, 100.0], [100.0, 0.0]], [1.0 + 0j, 0.5 + 0j],
        100_000.0, 10_000, noise=1.0, seed=1)
    dt = time.perf_counter() - t0
    print(f"\nintegrate_stuart_landau: {out['z'].shape[0]} steps x 2 modes "
          f"in {dt:.3f} s")
    assert dt < 30.0


@pytest.mark.benchmark
def test_benchmark_anisotropy():
    fs = 100_000.0
    t = np.arange(int(0.05 * fs)) / fs
    phases = np.vstack([instantaneous_phase(
        np.exp(1j * 2 * np.pi * (5000.0 + d) * t)) for d in (-50, 0, 50)])
    t0 = time.perf_counter()
    spatial_phase_anisotropy(phases, fs)
    dt = time.perf_counter() - t0
    print(f"\nspatial_phase_anisotropy: 3 x {t.size} samples in {dt:.3f} s")
    assert dt < 20.0
