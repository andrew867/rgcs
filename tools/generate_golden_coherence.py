#!/usr/bin/env python3
"""
generate_golden_coherence.py — RGCS v2 golden synthetic coherence datasets.

Owner: Sub-Agent 03 (Dynamic Coherence and Phase-Evolution Model).

Deterministic, seeded, numpy-only (matplotlib used only for optional plots).
Python 3.11 compatible. Run from anywhere:

    python3 tools/generate_golden_coherence.py [--no-plots]

Outputs (relative to repo root):
    experiments/sample_data/golden_coherence/*.csv
    experiments/sample_data/golden_coherence/manifest.json
    experiments/sample_data/golden_coherence/plots/*.png

CLASSIFICATION (per docs/SCIENTIFIC_CLASSIFICATION_POLICY.md):
  - Every signal-processing definition here is **Established** (standard DSP /
    circular statistics; coherence metric adapted from KOS-07, Koster et al.
    2026, Methods equation — cited in docs/COHERENCE_METRICS.md).
  - Every synthetic dataset is **Derived** (project-generated from stated
    parameters and seeds; reproducible bit-for-bit).
  - The Stuart-Landau dynamical model as a description of RGCS crystals is a
    **Hypothesis**; here it is used only as a synthetic-data generator.
  - No dataset represents a measurement. No physical equivalence with
    magnon-BEC systems (KOS) or cosmological shear (GAN) is claimed.

REFERENCE IMPLEMENTATIONS
-------------------------
The functions in the "reference metric implementations" section are the
normative reference for Agent 04's port into rgcs_core/coherence/.  They are
pure numpy, stateless, and documented with the exact formulas from
docs/COHERENCE_METRICS.md (section numbers cited in each docstring).
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from typing import Sequence

import numpy as np

# ---------------------------------------------------------------------------
# Global generation constants (Derived; arbitrary bench-plausible values.
# Deliberately NOT Koster operating values — see KOS-15 / policy §3.5).
# ---------------------------------------------------------------------------
MASTER_SEED = 20260714          # date-derived; fixed forever for goldens
FS_HZ = 100_000.0               # sample rate of synthetic I/Q records
F0_HZ = 5_000.0                 # nominal carrier of synthetic "mode"
WINDOW_S = 2.0e-3               # coherence boxcar window w (Koster used 100 ns
                                # at GHz carriers; same ~10 carrier-cycle-per-
                                # window compromise, scaled to audio-band f0)
HOP_S = 0.5e-3                  # hop between window centres

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUTDIR = os.path.join(REPO, "experiments", "sample_data", "golden_coherence")
PLOTDIR = os.path.join(OUTDIR, "plots")


# ===========================================================================
# Reference metric implementations  (port targets for rgcs_core/coherence/)
# Formula references: docs/COHERENCE_METRICS.md (COH-M1 .. COH-M13)
# ===========================================================================

def analytic_signal(x: np.ndarray) -> np.ndarray:
    """COH-M1b. Analytic signal z(t) of a real record x via FFT Hilbert
    transform: Z(f) = X(f) * h(f), h = [1, 2...2, 1(only if N even), 0...0].
    Established (standard). Returns complex array, same length as x."""
    x = np.asarray(x, dtype=float)
    n = x.size
    X = np.fft.fft(x)
    h = np.zeros(n)
    if n % 2 == 0:
        h[0] = h[n // 2] = 1.0
        h[1:n // 2] = 2.0
    else:
        h[0] = 1.0
        h[1:(n + 1) // 2] = 2.0
    return np.fft.ifft(X * h)


def instantaneous_phase(z: np.ndarray) -> np.ndarray:
    """COH-M2. Unwrapped instantaneous phase phi(t) = unwrap(arg z(t)). rad."""
    return np.unwrap(np.angle(z))


def instantaneous_frequency(z: np.ndarray, fs: float) -> np.ndarray:
    """COH-M2. Instantaneous frequency f_inst = (1/2pi) dphi/dt via central
    differences (np.gradient). Hz. Length preserved."""
    return np.gradient(instantaneous_phase(z)) * fs / (2.0 * np.pi)


def circular_mean(phases: np.ndarray) -> float:
    """COH-M3. Circular mean angle: arg( mean exp(i*phi) ). rad in (-pi,pi]."""
    return float(np.angle(np.mean(np.exp(1j * np.asarray(phases)))))


def circular_resultant(phases: np.ndarray) -> float:
    """COH-M3. Mean resultant length Rbar = |mean exp(i*phi)| in [0,1]."""
    return float(np.abs(np.mean(np.exp(1j * np.asarray(phases)))))


def circular_variance(phases: np.ndarray) -> float:
    """COH-M3. Circular variance V = 1 - Rbar in [0,1]."""
    return 1.0 - circular_resultant(phases)


def rayleigh_test(phases: np.ndarray) -> dict:
    """COH-M4. Rayleigh test of uniformity for n phases.
    Z = n*Rbar^2 ; p ~= exp(-Z) * (1 + (2Z - Z^2)/(4n)
                                   - (24Z - 132Z^2 + 76Z^3 - 9Z^4)/(288 n^2))
    (Established: standard small-sample corrected Rayleigh p, e.g. Mardia &
    Jupp 2000). Small p => reject uniformity (phase is externally imprinted);
    large p is CONSISTENT with uniform (spontaneous-phase pattern, KOS-06)."""
    ph = np.asarray(phases, dtype=float)
    n = ph.size
    rbar = circular_resultant(ph)
    z = n * rbar * rbar
    p = math.exp(-z) * (1.0 + (2.0 * z - z * z) / (4.0 * n)
                        - (24.0 * z - 132.0 * z ** 2 + 76.0 * z ** 3
                           - 9.0 * z ** 4) / (288.0 * n * n))
    return {"n": n, "Rbar": rbar, "Z": z, "p": float(min(max(p, 0.0), 1.0))}


def coherence_window(seg: np.ndarray) -> float:
    """COH-M5 (adapted from KOS-07, Koster et al. 2026 Methods, Established
    as a signal-processing definition). Normalized autocorrelation coherence
    of one complex window segment:

        C = sum_tau |ACF_z(tau)|  /  sum_tau |ACF_tone(tau)|

    where ACF_z(tau) = sum_n z[n+tau] conj(z[n]) over the window, and the
    normaliser is the same quantity for a perfect tone with the SAME power
    (sum_tau (N-|tau|) * mean|z|^2 * ... ) which equals N * sum_n |z[n]|^2.
    Properties: pure tone -> 1 exactly; white noise -> small positive
    baseline ~ (2*sqrt(pi)/3)/sqrt(N); amplitude scale cancels."""
    seg = np.asarray(seg, dtype=complex)
    n = seg.size
    power = float(np.sum(np.abs(seg) ** 2))
    if power <= 0.0 or n < 2:
        return 0.0
    acf = np.correlate(seg, seg, mode="full")   # lags -(n-1)..(n-1)
    return float(np.sum(np.abs(acf)) / (n * power))


def coherence_series(z: np.ndarray, fs: float, window_s: float = WINDOW_S,
                     hop_s: float = HOP_S) -> tuple[np.ndarray, np.ndarray]:
    """COH-M5. Sliding-window coherence trace C_w(t): coherence_window applied
    to boxcar segments of length w centred at t, hop hop_s.
    Returns (t_centres, C)."""
    z = np.asarray(z, dtype=complex)
    nwin = max(int(round(window_s * fs)), 2)
    nhop = max(int(round(hop_s * fs)), 1)
    starts = np.arange(0, z.size - nwin + 1, nhop)
    tc = (starts + nwin / 2.0) / fs
    C = np.array([coherence_window(z[s:s + nwin]) for s in starts])
    return tc, C


def phase_linearity(z: np.ndarray) -> float:
    """COH-M6. Phase-linearity score in [0,1]:
        PL = | mean_n exp(i * (phi_n - (a*n + b))) |
    with (a,b) the least-squares line through the unwrapped phase.
    1 = perfectly linear phase (single stable tone); ~0 = phase diffusion."""
    phi = instantaneous_phase(np.asarray(z, dtype=complex))
    n = np.arange(phi.size, dtype=float)
    a, b = np.polyfit(n, phi, 1)
    resid = phi - (a * n + b)
    return float(np.abs(np.mean(np.exp(1j * resid))))


def amplitude_normalized_coherence(z: np.ndarray, fs: float,
                                   window_s: float = WINDOW_S,
                                   hop_s: float = HOP_S,
                                   floor: float = 1e-12
                                   ) -> tuple[np.ndarray, np.ndarray]:
    """COH-M7. Amplitude-independent coherence tracking: coherence_series of
    the unit-magnitude signal u(t) = z(t)/max(|z(t)|, floor). Separates phase
    order from amplitude (KOS-03/KOS-10 lesson: high amplitude != coherence,
    and coherence can outlive amplitude)."""
    z = np.asarray(z, dtype=complex)
    u = z / np.maximum(np.abs(z), floor)
    return coherence_series(u, fs, window_s, hop_s)


def band_power_fraction(z: np.ndarray, fs: float, f0: float,
                        bw: float) -> float:
    """COH-M8. Mode occupancy proxy: fraction of one-record power spectral
    density within [f0-bw/2, f0+bw/2], over total in [0, fs/2) (analytic
    signal is single-sided). In [0,1]. A *proxy* only — labelled Derived;
    it is not a quasiparticle occupation number."""
    z = np.asarray(z, dtype=complex)
    spec = np.abs(np.fft.fft(z)) ** 2
    freqs = np.fft.fftfreq(z.size, d=1.0 / fs)
    pos = freqs >= 0.0
    band = pos & (np.abs(freqs - f0) <= bw / 2.0)
    tot = float(np.sum(spec[pos]))
    return float(np.sum(spec[band]) / tot) if tot > 0 else 0.0


def coherence_onset_time(tc: np.ndarray, C: np.ndarray, threshold: float,
                         hold: int = 3) -> float:
    """COH-M9. Onset time: earliest window centre where C >= threshold and
    stays >= threshold for `hold` consecutive windows. NaN if never."""
    C = np.asarray(C)
    for i in range(C.size - hold + 1):
        if np.all(C[i:i + hold] >= threshold):
            return float(tc[i])
    return float("nan")


def fit_exponential_decay(t: np.ndarray, y: np.ndarray) -> dict:
    """COH-M10. Log-linear least-squares fit y ~= A exp(-t/tau) on samples
    with y > 0. Returns A, tau_s, and RMS residual in log space."""
    t = np.asarray(t, float)
    y = np.asarray(y, float)
    m = y > 0
    slope, intercept = np.polyfit(t[m], np.log(y[m]), 1)
    tau = -1.0 / slope if slope < 0 else float("inf")
    resid = np.log(y[m]) - (slope * t[m] + intercept)
    return {"A": float(np.exp(intercept)), "tau_s": float(tau),
            "log_rms": float(np.sqrt(np.mean(resid ** 2)))}


def coherence_decay_time(tc: np.ndarray, C: np.ndarray,
                         baseline: float) -> float:
    """COH-M10. Coherence decay time: exponential-fit tau of (C - baseline)
    over the falling segment from the global max of C to the first window
    where C <= baseline + 0.05 (or the end)."""
    tc = np.asarray(tc)
    C = np.asarray(C)
    i0 = int(np.argmax(C))
    below = np.where(C[i0:] <= baseline + 0.05)[0]
    i1 = i0 + int(below[0]) if below.size else C.size
    seg_t, seg_c = tc[i0:i1], C[i0:i1] - baseline
    if seg_t.size < 3:
        return float("nan")
    return fit_exponential_decay(seg_t, np.maximum(seg_c, 1e-9))["tau_s"]


def phase_locking_value(phi_a: np.ndarray, phi_b: np.ndarray) -> float:
    """COH-M11. Pairwise phase-locking value:
    PLV = | mean_t exp(i (phi_a - phi_b)) | in [0,1]. Established."""
    return float(np.abs(np.mean(np.exp(1j * (np.asarray(phi_a)
                                             - np.asarray(phi_b))))))


def threshold_detect_bootstrap(x: np.ndarray, y_runs: np.ndarray,
                               n_boot: int = 500,
                               seed: int = 0) -> dict:
    """COH-M12. Threshold (change-point) detection with bootstrap CI.
    x: control-parameter grid (K values or drive levels), shape (nx,).
    y_runs: order-parameter samples, shape (nx, nruns).
    Estimator: x* where the run-mean crosses the midpoint between its
    low-plateau (min) and high-plateau (max), linearly interpolated.
    Bootstrap: resample runs per x with replacement, n_boot times; report
    the percentile 2.5/97.5 CI. Established resampling methodology."""
    rng = np.random.default_rng(seed)
    x = np.asarray(x, float)
    y = np.asarray(y_runs, float)

    def crossing(mean_curve: np.ndarray) -> float:
        lo, hi = float(mean_curve.min()), float(mean_curve.max())
        mid = 0.5 * (lo + hi)
        above = np.where(mean_curve >= mid)[0]
        if not above.size or above[0] == 0:
            return float(x[0])
        i = above[0]
        y0, y1 = mean_curve[i - 1], mean_curve[i]
        frac = (mid - y0) / (y1 - y0) if y1 != y0 else 0.5
        return float(x[i - 1] + frac * (x[i] - x[i - 1]))

    est = crossing(y.mean(axis=1))
    boots = np.empty(n_boot)
    nruns = y.shape[1]
    for b in range(n_boot):
        idx = rng.integers(0, nruns, size=nruns)
        boots[b] = crossing(y[:, idx].mean(axis=1))
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {"threshold": est, "ci_lo": float(lo), "ci_hi": float(hi),
            "n_boot": n_boot}


def windowed_phase_rates(phases: np.ndarray, fs: float,
                         window_s: float = WINDOW_S,
                         hop_s: float = HOP_S) -> np.ndarray:
    """COH-M13 helper. Per-channel windowed phase rates h_i(t_k) (rad/s):
    least-squares slope of the unwrapped phase within boxcar windows of
    length window_s, hop hop_s. Windowed slopes (not raw sample-to-sample
    gradients) so that additive-noise phase jitter is suppressed and the
    anisotropy statistic reflects sustained inter-channel disagreement."""
    ph = np.asarray(phases, float)
    nwin = max(int(round(window_s * fs)), 2)
    nhop = max(int(round(hop_s * fs)), 1)
    starts = np.arange(0, ph.shape[1] - nwin + 1, nhop)
    tt = np.arange(nwin) / fs
    rates = np.empty((ph.shape[0], starts.size))
    for i in range(ph.shape[0]):
        for k, s in enumerate(starts):
            rates[i, k] = np.polyfit(tt, ph[i, s:s + nwin], 1)[0]
    return rates


def spatial_phase_anisotropy(phases: np.ndarray, fs: float) -> dict:
    """COH-M13. Spatial phase anisotropy for M spatial sensor channels.
    (NEVER 'quantum shear' — mathematical analogy to GAN-04/05 only; no
    physical equivalence with cosmological shear is claimed.)

    Input phases: shape (M, N) unwrapped instantaneous phases.
    h_i(t_k) = windowed phase rate (see windowed_phase_rates), rad/s
    hbar(t) = mean_i h_i(t)   (isotropic part; analogue of expansion theta)
    Tensor  T_jk = < (h_j - hbar)(h_k - hbar) >_t          (M x M, rad^2/s^2)
    Scalar  sigma_phi^2 = < (1/M) sum_{i<j} (h_i - h_j)^2 >_t
    For M=3 this reduces to GAN Eq. (2)'s form ((h1-h2)^2 + (h2-h3)^2 +
    (h3-h1)^2)/3 applied to phase rates. Zero iff all channels' phase rates
    are identical in every window."""
    ph = np.asarray(phases, float)
    m = ph.shape[0]
    h = windowed_phase_rates(ph, fs)
    hbar = h.mean(axis=0)
    dev = h - hbar
    tensor = (dev @ dev.T) / dev.shape[1]
    pair = 0.0
    for i in range(m):
        for j in range(i + 1, m):
            pair += np.mean((h[i] - h[j]) ** 2)
    scalar = float(pair / m)
    return {"scalar_rad2_per_s2": scalar, "tensor": tensor.tolist(),
            "n_channels": m}


def model_comparison(t: np.ndarray, y: np.ndarray) -> dict:
    """COH-M14. AIC/BIC comparison of decay-law models fit to (t, y>0):
        exponential:        y = A exp(-t/tau)                    (k=2)
        power law:          y = A (1 + t/t0)^(-p)                (k=3)
        damped oscillatory: y = A exp(-t/tau) |cos(2 pi f t)|+c  (k=4, grid f)
        no change:          y = c                                (k=1)
    Gaussian residual likelihood: AIC = n ln(SSR/n) + 2k;
    BIC = n ln(SSR/n) + k ln n. Established (standard model selection).
    Fits are deliberately simple (log-linear / coarse grid) so the reference
    is reproducible without scipy."""
    t = np.asarray(t, float)
    y = np.asarray(y, float)
    m = y > 0
    t, y = t[m], y[m]
    n = t.size
    out = {}

    def score(ssr: float, k: int) -> tuple[float, float]:
        ssr = max(ssr, 1e-300)
        return (n * math.log(ssr / n) + 2 * k,
                n * math.log(ssr / n) + k * math.log(n))

    # exponential (log-linear)
    fe = fit_exponential_decay(t, y)
    pred = fe["A"] * np.exp(-t / fe["tau_s"]) if math.isfinite(fe["tau_s"]) \
        else np.full_like(t, fe["A"])
    a, b = score(float(np.sum((y - pred) ** 2)), 2)
    out["exponential"] = {"AIC": a, "BIC": b, "params": fe}

    # power law: grid over t0, log-linear in p
    best = None
    for t0 in np.geomspace(max(t[1] - t[0], 1e-6), max(t[-1], 1e-3), 25):
        lx = np.log1p(t / t0)
        sl, ic = np.polyfit(lx, np.log(y), 1)
        pred = np.exp(ic) * np.exp(sl * lx)
        ssr = float(np.sum((y - pred) ** 2))
        if best is None or ssr < best[0]:
            best = (ssr, t0, -sl, math.exp(ic))
    a, b = score(best[0], 3)
    out["power_law"] = {"AIC": a, "BIC": b,
                        "params": {"t0_s": best[1], "p": best[2],
                                   "A": best[3]}}

    # damped oscillatory: coarse grid over f, exp fit on residual envelope
    best = None
    for f in np.geomspace(0.5 / (t[-1] - t[0] + 1e-12),
                          0.25 * n / (t[-1] - t[0] + 1e-12), 40):
        osc = np.abs(np.cos(2 * np.pi * f * t))
        env = fe["A"] * np.exp(-t / fe["tau_s"]) if math.isfinite(
            fe["tau_s"]) else np.full_like(t, fe["A"])
        base = env * osc
        denom = float(np.sum(base ** 2))
        g = float(np.sum(base * y) / denom) if denom > 0 else 0.0
        c = float(np.mean(y - g * base))
        pred = g * base + c
        ssr = float(np.sum((y - pred) ** 2))
        if best is None or ssr < best[0]:
            best = (ssr, f, g, c)
    a, b = score(best[0], 4)
    out["damped_oscillatory"] = {"AIC": a, "BIC": b,
                                 "params": {"f_hz": best[1], "gain": best[2],
                                            "offset": best[3]}}

    # no change
    c = float(np.mean(y))
    a, b = score(float(np.sum((y - c) ** 2)), 1)
    out["no_change"] = {"AIC": a, "BIC": b, "params": {"c": c}}

    out["best_by_AIC"] = min((k for k in out if k != "best_by_AIC"),
                             key=lambda k: out[k]["AIC"])
    return out


# ===========================================================================
# Synthetic-signal generators (Derived; Stuart-Landau model = Hypothesis as
# a physical description, Derived as a data generator)
# ===========================================================================

def gen_white_noise(rng, n: int, sigma: float = 1.0) -> np.ndarray:
    """Complex circular white Gaussian noise."""
    return sigma * (rng.standard_normal(n) + 1j * rng.standard_normal(n)) \
        / math.sqrt(2.0)


def gen_tone(n: int, fs: float, f0: float, amp: float = 1.0,
             phase0: float = 0.0) -> np.ndarray:
    t = np.arange(n) / fs
    return amp * np.exp(1j * (2 * np.pi * f0 * t + phase0))


def stuart_landau_pair(rng, n: int, fs: float, f1: float, f2: float,
                       mu: float, coupling_k: float, noise: float,
                       a0: complex, b0: complex) -> tuple[np.ndarray,
                                                          np.ndarray]:
    """Two diffusively coupled Stuart-Landau oscillators (Euler-Maruyama):

        da/dt = (mu + i 2pi f1) a - |a|^2 a + K (b - a) + noise * xi_a(t)
        db/dt = (mu + i 2pi f2) b - |b|^2 b + K (a - b) + noise * xi_b(t)

    HYPOTHESIS as an RGCS physical model (docs/DYNAMIC_COHERENCE_SPEC.md
    DC-H2); Derived as a synthetic-data generator. In the phase reduction
    the pair locks when 2K >= |2pi(f1-f2)|, i.e. K_c = pi |f1 - f2|."""
    dt = 1.0 / fs
    a = np.empty(n, complex)
    b = np.empty(n, complex)
    a[0], b[0] = a0, b0
    sq = math.sqrt(dt)
    for i in range(1, n):
        xa = (rng.standard_normal() + 1j * rng.standard_normal()) / math.sqrt(2)
        xb = (rng.standard_normal() + 1j * rng.standard_normal()) / math.sqrt(2)
        ap, bp = a[i - 1], b[i - 1]
        da = ((mu + 1j * 2 * np.pi * f1) * ap - (abs(ap) ** 2) * ap
              + coupling_k * (bp - ap))
        db = ((mu + 1j * 2 * np.pi * f2) * bp - (abs(bp) ** 2) * bp
              + coupling_k * (ap - bp))
        a[i] = ap + da * dt + noise * sq * xa
        b[i] = bp + db * dt + noise * sq * xb
    return a, b


# ===========================================================================
# CSV / manifest helpers
# ===========================================================================

def write_csv(path: str, header: Sequence[str], rows) -> None:
    with open(path, "w", newline="") as fh:
        wcsv = csv.writer(fh)
        wcsv.writerow(header)
        wcsv.writerows(rows)


def fmt(x: float) -> str:
    return f"{x:.9g}"


# ===========================================================================
# Dataset builders (cases a..g)
# ===========================================================================

def case_a_white_noise(manifest: dict) -> dict:
    seed = MASTER_SEED + 1
    rng = np.random.default_rng(seed)
    n = int(0.02 * FS_HZ)                      # 20 ms
    z = gen_white_noise(rng, n)
    t = np.arange(n) / FS_HZ
    path = os.path.join(OUTDIR, "case_a_white_noise.csv")
    write_csv(path, ["t_s", "I", "Q"],
              ((fmt(tt), fmt(zi.real), fmt(zi.imag)) for tt, zi in zip(t, z)))

    tc, C = coherence_series(z, FS_HZ)
    occ = band_power_fraction(z, FS_HZ, F0_HZ, 500.0)
    nwin = int(round(WINDOW_S * FS_HZ))
    baseline_theory = (2.0 * math.sqrt(math.pi) / 3.0) / math.sqrt(nwin)
    entry = {
        "file": os.path.basename(path),
        "description": "Complex circular white Gaussian noise, 20 ms. "
                       "Coherence must sit at the small positive window "
                       "baseline, far from 1 (KOS-07 baseline concept).",
        "classification": "Derived (synthetic; Established statistics)",
        "seed": seed,
        "params": {"fs_hz": FS_HZ, "n_samples": n, "sigma": 1.0},
        "expected": {
            "coherence_mean": {"value": float(np.mean(C)), "atol": 0.03},
            "coherence_max": {"value": float(np.max(C)), "atol": 0.05},
            "baseline_theory": {"value": baseline_theory, "atol": 0.03,
                                "note": "(2 sqrt(pi)/3)/sqrt(N_window)"},
            "mode_occupancy_5kHz_500Hz": {"value": occ, "atol": 0.01},
            "phase_linearity": {"value": phase_linearity(z), "atol": 0.15},
        },
    }
    manifest["datasets"]["case_a_white_noise"] = entry
    return {"z": z, "tc": tc, "C": C}


def case_b_pure_sinusoid(manifest: dict) -> dict:
    seed = MASTER_SEED + 2
    n = int(0.02 * FS_HZ)
    z = gen_tone(n, FS_HZ, F0_HZ, amp=1.0, phase0=0.7)
    t = np.arange(n) / FS_HZ
    path = os.path.join(OUTDIR, "case_b_pure_sinusoid.csv")
    write_csv(path, ["t_s", "I", "Q"],
              ((fmt(tt), fmt(zi.real), fmt(zi.imag)) for tt, zi in zip(t, z)))

    tc, C = coherence_series(z, FS_HZ)
    finst = instantaneous_frequency(z, FS_HZ)
    entry = {
        "file": os.path.basename(path),
        "description": "Noise-free complex tone at f0=5 kHz, amp 1, "
                       "phase0=0.7 rad. Coherence must be ~1 in every window.",
        "classification": "Derived (synthetic; Established)",
        "seed": seed,
        "params": {"fs_hz": FS_HZ, "f0_hz": F0_HZ, "amp": 1.0,
                   "phase0_rad": 0.7, "n_samples": n},
        "expected": {
            "coherence_min": {"value": float(np.min(C)), "atol": 1e-6,
                              "note": "exactly 1 to numerical precision"},
            "phase_linearity": {"value": phase_linearity(z), "atol": 1e-6},
            "inst_freq_mean_hz": {"value": float(np.mean(finst[10:-10])),
                                  "atol": 1.0},
            "mode_occupancy_5kHz_500Hz": {
                "value": band_power_fraction(z, FS_HZ, F0_HZ, 500.0),
                "atol": 1e-3},
        },
    }
    manifest["datasets"]["case_b_pure_sinusoid"] = entry
    return {"z": z, "tc": tc, "C": C}


def case_c_decaying_sinusoid(manifest: dict) -> dict:
    seed = MASTER_SEED + 3
    rng = np.random.default_rng(seed)
    dur = 0.05                        # 50 ms
    n = int(dur * FS_HZ)
    t = np.arange(n) / FS_HZ
    t_on = 0.005                      # signal starts at 5 ms (onset metric)
    tau_amp = 0.008                   # amplitude decay constant 8 ms
    amp0, sigma_n = 3.0, 0.05
    env = np.where(t >= t_on, amp0 * np.exp(-(t - t_on) / tau_amp), 0.0)
    z = env * np.exp(1j * (2 * np.pi * F0_HZ * t + 1.1)) \
        + gen_white_noise(rng, n, sigma_n)
    path = os.path.join(OUTDIR, "case_c_decaying_sinusoid.csv")
    write_csv(path, ["t_s", "I", "Q"],
              ((fmt(tt), fmt(zi.real), fmt(zi.imag)) for tt, zi in zip(t, z)))

    tc, C = coherence_series(z, FS_HZ)
    tcn, Cn = amplitude_normalized_coherence(z, FS_HZ)
    onset = coherence_onset_time(tc, C, threshold=0.5)
    nwin = int(round(WINDOW_S * FS_HZ))
    baseline = (2.0 * math.sqrt(math.pi) / 3.0) / math.sqrt(nwin)
    tdec = coherence_decay_time(tc, C, baseline)
    # coherence-below-amplitude-floor check (KOS-10 property): window where
    # envelope < noise sigma but coherence still > 3x baseline
    idx = np.where(env[(tc * FS_HZ).astype(int)] < sigma_n)[0]
    c_after_floor = float(np.max(C[idx])) if idx.size else float("nan")
    # model comparison on the noise-floor-corrected amplitude envelope:
    # E|noise| = sigma*sqrt(pi)/2 for circular complex Gaussian; fit only
    # where the corrected envelope clearly exceeds the noise (> 3 sigma).
    amp_est = np.array([float(np.mean(np.abs(
        z[int((x - WINDOW_S / 2) * FS_HZ):int((x + WINDOW_S / 2) * FS_HZ)])))
        for x in tc])
    amp_corr = amp_est - sigma_n * math.sqrt(math.pi) / 2.0
    sel = (tc >= t_on + WINDOW_S) & (amp_corr > 3.0 * sigma_n)
    mc = model_comparison(tc[sel] - (t_on + WINDOW_S), amp_corr[sel])
    entry = {
        "file": os.path.basename(path),
        "description": "Tone at 5 kHz starting at t=5 ms with exponential "
                       "amplitude decay tau=8 ms in weak noise. Coherence "
                       "must stay high while amplitude falls and persist "
                       "below the amplitude noise floor (KOS-10 analogue).",
        "classification": "Derived (synthetic; Established)",
        "seed": seed,
        "params": {"fs_hz": FS_HZ, "f0_hz": F0_HZ, "amp0": amp0,
                   "tau_amp_s": tau_amp, "t_on_s": t_on,
                   "noise_sigma": sigma_n, "n_samples": n},
        "expected": {
            "coherence_max": {"value": float(np.max(C)), "atol": 0.02},
            "coherence_at_10ms": {
                "value": float(C[np.argmin(np.abs(tc - 0.010))],),
                "atol": 0.05,
                "note": "amplitude already down ~2x; coherence still high"},
            "onset_time_s": {"value": onset, "atol": 2 * HOP_S,
                             "note": "true signal start 0.005 s"},
            "coherence_decay_tau_s": {"value": tdec, "rtol": 0.5,
                                      "note": "order-of-magnitude check; "
                                              "coherence decays later and "
                                              "faster than amplitude"},
            "coherence_below_amp_floor": {
                "value": c_after_floor, "atol": 0.15,
                "note": "max C in windows where envelope < noise sigma; "
                        "must exceed 3x white-noise baseline"},
            "envelope_best_model": {"value": mc["best_by_AIC"],
                                    "exact": True},
            "aic_exp_minus_power": {
                "value": mc["exponential"]["AIC"] - mc["power_law"]["AIC"],
                "max": 0.0, "note": "exponential must beat power law"},
            "aic_exp_minus_nochange": {
                "value": mc["exponential"]["AIC"] - mc["no_change"]["AIC"],
                "max": -10.0, "note": "exponential must crush no-change"},
            "envelope_fit_tau_s": {
                "value": mc["exponential"]["params"]["tau_s"],
                "rtol": 0.15, "note": "true tau_amp 0.008 s"},
        },
    }
    manifest["datasets"]["case_c_decaying_sinusoid"] = entry
    return {"z": z, "t": t, "env": env, "tc": tc, "C": C, "Cn": Cn,
            "tcn": tcn, "amp_est": amp_est, "mc": mc}


def case_d_random_phase_runs(manifest: dict) -> dict:
    seed = MASTER_SEED + 4
    rng = np.random.default_rng(seed)
    nruns, n = 100, int(0.01 * FS_HZ)          # 100 runs x 10 ms
    t = np.arange(n) / FS_HZ
    phases0 = rng.uniform(-np.pi, np.pi, nruns)
    rows = []
    per_run_pl, per_run_C, init_phase_meas = [], [], []
    for r in range(nruns):
        z = gen_tone(n, FS_HZ, F0_HZ, amp=1.0, phase0=phases0[r]) \
            + gen_white_noise(rng, n, 0.1)
        for tt, zi in zip(t, z):
            rows.append((r, fmt(tt), fmt(zi.real), fmt(zi.imag)))
        per_run_pl.append(phase_linearity(z))
        _, C = coherence_series(z, FS_HZ)
        per_run_C.append(float(np.mean(C)))
        # measured initial phase: demodulate first window at f0
        w0 = z[:int(WINDOW_S * FS_HZ)]
        ref = gen_tone(w0.size, FS_HZ, F0_HZ)
        init_phase_meas.append(float(np.angle(np.sum(w0 * np.conj(ref)))))
    path = os.path.join(OUTDIR, "case_d_random_phase_runs.csv")
    write_csv(path, ["run", "t_s", "I", "Q"], rows)

    ray = rayleigh_test(np.array(init_phase_meas))
    entry = {
        "file": os.path.basename(path),
        "description": "100 independent runs of the same tone with "
                       "per-run random initial phase (uniform) in weak "
                       "noise. Per-run coherence high; ensemble initial "
                       "phase uniform (Rayleigh must NOT reject). This is "
                       "the KOS-06 spontaneous-order signature.",
        "classification": "Derived (synthetic; Established statistics)",
        "seed": seed,
        "params": {"fs_hz": FS_HZ, "f0_hz": F0_HZ, "n_runs": nruns,
                   "n_samples_per_run": n, "noise_sigma": 0.1},
        "expected": {
            "per_run_coherence_mean": {"value": float(np.mean(per_run_C)),
                                       "atol": 0.03},
            "per_run_phase_linearity_min": {
                "value": float(np.min(per_run_pl)), "atol": 0.1},
            "ensemble_Rbar": {"value": ray["Rbar"], "atol": 0.1,
                              "note": "near 0 for uniform phases"},
            "rayleigh_p": {"value": ray["p"], "min": 0.05,
                           "note": "must NOT reject uniformity"},
            "circular_variance": {
                "value": circular_variance(np.array(init_phase_meas)),
                "atol": 0.1, "note": "near 1 for uniform"},
        },
    }
    manifest["datasets"]["case_d_random_phase_runs"] = entry
    return {"init_phase": np.array(init_phase_meas),
            "per_run_C": np.array(per_run_C)}


def case_e_coupled_oscillators(manifest: dict) -> dict:
    seed = MASTER_SEED + 5
    rng = np.random.default_rng(seed)
    f1, f2 = 5000.0, 5080.0            # 80 Hz detuning
    k_c_true = math.pi * abs(f1 - f2)  # phase-reduction critical coupling
    K_grid = np.array([0.0, 50.0, 100.0, 150.0, 200.0, 250.0, 300.0,
                       400.0, 600.0, 1000.0])
    nruns_per_k = 8
    n = int(0.05 * FS_HZ)              # 50 ms
    t = np.arange(n) / FS_HZ
    mu, noise = 400.0, 8.0
    rows = []
    plv = np.zeros((K_grid.size, nruns_per_k))
    for ik, K in enumerate(K_grid):
        for r in range(nruns_per_k):
            pa = rng.uniform(-np.pi, np.pi)
            pb = rng.uniform(-np.pi, np.pi)
            amp = math.sqrt(mu)
            a, b = stuart_landau_pair(rng, n, FS_HZ, f1, f2, mu, K, noise,
                                      amp * np.exp(1j * pa),
                                      amp * np.exp(1j * pb))
            # discard first 10 ms transient for PLV
            i0 = int(0.01 * FS_HZ)
            plv[ik, r] = phase_locking_value(instantaneous_phase(a[i0:]),
                                             instantaneous_phase(b[i0:]))
            if r == 0:  # store one full run per K to keep the CSV small
                for tt, ai, bi in zip(t, a, b):
                    rows.append((fmt(K), fmt(tt), fmt(ai.real), fmt(ai.imag),
                                 fmt(bi.real), fmt(bi.imag)))
    path = os.path.join(OUTDIR, "case_e_coupled_oscillators.csv")
    write_csv(path, ["K", "t_s", "I1", "Q1", "I2", "Q2"], rows)
    # PLV summary table (all runs) — this is what tests recompute against
    path2 = os.path.join(OUTDIR, "case_e_plv_summary.csv")
    write_csv(path2, ["K"] + [f"plv_run{r}" for r in range(nruns_per_k)],
              [[fmt(K_grid[ik])] + [fmt(v) for v in plv[ik]]
               for ik in range(K_grid.size)])

    thr = threshold_detect_bootstrap(K_grid, plv, n_boot=500,
                                     seed=MASTER_SEED + 55)
    entry = {
        "file": os.path.basename(path),
        "summary_file": os.path.basename(path2),
        "description": "Two coupled Stuart-Landau oscillators (5000 vs 5080 "
                       "Hz, mu=400, noise=8), coupling K swept over 10 "
                       "values x 8 runs. PLV low below and high above the "
                       "phase-reduction critical coupling K_c = pi*|f1-f2| "
                       "~= 251.3 s^-1. Model as RGCS physics = Hypothesis "
                       "(DC-H2); dataset = Derived.",
        "classification": "Derived (generator); Hypothesis (as RGCS model)",
        "seed": seed,
        "params": {"fs_hz": FS_HZ, "f1_hz": f1, "f2_hz": f2, "mu": mu,
                   "noise": noise, "K_grid": K_grid.tolist(),
                   "n_runs_per_K": nruns_per_k, "n_samples": n,
                   "K_c_theory": k_c_true},
        "expected": {
            "plv_at_K0_mean": {"value": float(plv[0].mean()), "atol": 0.15,
                               "note": "unlocked: low PLV"},
            "plv_at_Kmax_mean": {"value": float(plv[-1].mean()),
                                 "atol": 0.05, "note": "locked: PLV ~ 1"},
            "threshold_K": {"value": thr["threshold"], "atol": 60.0,
                            "note": "K_c theory ~251.3; midpoint-crossing "
                                    "estimator on noisy PLV"},
            "threshold_ci": {"value": [thr["ci_lo"], thr["ci_hi"]],
                             "note": "95% bootstrap CI, n_boot=500, "
                                     "seed MASTER_SEED+55"},
            "plv_monotone_spearman_min": {
                "value": 0.9, "min": 0.9,
                "note": "mean PLV must increase with K (rank corr > 0.9)"},
        },
    }
    manifest["datasets"]["case_e_coupled_oscillators"] = entry
    return {"K_grid": K_grid, "plv": plv, "thr": thr, "k_c_true": k_c_true}


def case_f_pump_leakage(manifest: dict) -> dict:
    seed = MASTER_SEED + 6
    rng = np.random.default_rng(seed)
    nruns, n = 100, int(0.01 * FS_HZ)
    t = np.arange(n) / FS_HZ
    pump_phase = 0.4                      # FIXED across runs = the tell
    leak_amp, sigma_n = 0.6, 0.3
    rows = []
    stats = {"sample": {"C": [], "ph": []}, "control": {"C": [], "ph": []}}
    for cond in ("sample", "control"):
        for r in range(nruns):
            # both conditions contain ONLY pump leakage + noise: there is no
            # genuine sample signal. The false coherence is identical.
            z = gen_tone(n, FS_HZ, F0_HZ, amp=leak_amp, phase0=pump_phase) \
                + gen_white_noise(rng, n, sigma_n)
            for tt, zi in zip(t, z):
                rows.append((cond, r, fmt(tt), fmt(zi.real), fmt(zi.imag)))
            _, C = coherence_series(z, FS_HZ)
            stats[cond]["C"].append(float(np.mean(C)))
            w0 = z[:int(WINDOW_S * FS_HZ)]
            ref = gen_tone(w0.size, FS_HZ, F0_HZ)
            stats[cond]["ph"].append(
                float(np.angle(np.sum(w0 * np.conj(ref)))))
    path = os.path.join(OUTDIR, "case_f_pump_leakage.csv")
    write_csv(path, ["condition", "run", "t_s", "I", "Q"], rows)

    ray_s = rayleigh_test(np.array(stats["sample"]["ph"]))
    cs = float(np.mean(stats["sample"]["C"]))
    cc = float(np.mean(stats["control"]["C"]))
    entry = {
        "file": os.path.basename(path),
        "description": "False-coherence trap: fixed-phase pump leakage in "
                       "noise for 100 'sample' and 100 'control' (no-"
                       "crystal) runs. Coherence alone is HIGH and "
                       "identical in both. Controls that must catch it: "
                       "(1) Rayleigh test REJECTS ensemble-phase "
                       "uniformity (phase imprinted by pump, contra "
                       "KOS-06/KOS-13); (2) control-subtracted coherence "
                       "~ 0.",
        "classification": "Derived (synthetic)",
        "seed": seed,
        "params": {"fs_hz": FS_HZ, "f0_hz": F0_HZ, "n_runs_per_cond": nruns,
                   "leak_amp": leak_amp, "noise_sigma": sigma_n,
                   "pump_phase_rad": pump_phase, "n_samples": n},
        "expected": {
            "sample_coherence_mean": {"value": cs, "atol": 0.05,
                                      "note": "high — the trap"},
            "control_coherence_mean": {"value": cc, "atol": 0.05},
            "coherence_excess_sample_minus_control": {
                "value": cs - cc, "atol": 0.02,
                "note": "~0: no genuine effect"},
            "rayleigh_p_sample": {"value": ray_s["p"], "max": 1e-6,
                                  "note": "MUST reject uniformity"},
            "ensemble_Rbar_sample": {"value": ray_s["Rbar"], "atol": 0.1,
                                     "note": "near 1: pump-imprinted phase"},
            "ensemble_phase_vs_pump_rad": {
                "value": circular_mean(np.array(stats["sample"]["ph"])),
                "atol": 0.1, "note": "clusters at pump phase 0.4 rad"},
        },
    }
    manifest["datasets"]["case_f_pump_leakage"] = entry
    return {"stats": stats, "ray_s": ray_s}


def case_g_sensor_geometry(manifest: dict) -> dict:
    seed = MASTER_SEED + 7
    rng = np.random.default_rng(seed)
    n = int(0.02 * FS_HZ)
    t = np.arange(n) / FS_HZ
    length_mm = 150.0
    sensor_x_mm = np.array([35.0, 75.0, 115.0])        # 3 point sensors,
    # chosen OFF the nodes of both test modes: |sin(kx)| = 1 for the 20-mm
    # mode at all three positions; 0.67/1.0/0.67 for the 300-mm mode.
    aperture_mm = 60.0        # wide sensor span = 3 x lambda_short exactly,
    # so the aperture integral of the short mode vanishes identically.
    sigma_n = 0.15
    conds = {
        # (mode wavelength mm, amplitude)
        "coherent_long": {"lambda_mm": 300.0, "amp": 1.0},   # >> aperture
        "coherent_short": {"lambda_mm": 20.0, "amp": 1.0},   # << aperture
        "detuned_channels": None,   # channels at 4950/5000/5050 Hz: growing
        # directional disagreement (GAN-analogy contrast condition)
    }
    rows = []
    results = {}
    for cond, spec in conds.items():
        chans = []
        if spec is None:
            for i, fi in enumerate((4950.0, 5000.0, 5050.0)):
                chans.append(gen_tone(n, FS_HZ, fi, 1.0,
                                      rng.uniform(-np.pi, np.pi))
                             + gen_white_noise(rng, n, sigma_n))
            wide = gen_white_noise(rng, n, sigma_n)
        else:
            k = 2 * np.pi / spec["lambda_mm"]
            carrier = gen_tone(n, FS_HZ, F0_HZ, 1.0, 0.9)
            for x in sensor_x_mm:
                chans.append(spec["amp"] * math.sin(k * x) * carrier
                             + gen_white_noise(rng, n, sigma_n))
            # wide sensor: mean of field over aperture centred at L/2
            xc = length_mm / 2.0
            # integral of sin(kx) over aperture / aperture
            g = (math.cos(k * (xc - aperture_mm / 2))
                 - math.cos(k * (xc + aperture_mm / 2))) / (k * aperture_mm)
            wide = spec["amp"] * g * carrier + gen_white_noise(rng, n,
                                                               sigma_n)
        for i, tt in enumerate(t):
            rows.append((cond, fmt(tt),
                         fmt(chans[0][i].real), fmt(chans[0][i].imag),
                         fmt(chans[1][i].real), fmt(chans[1][i].imag),
                         fmt(chans[2][i].real), fmt(chans[2][i].imag),
                         fmt(wide[i].real), fmt(wide[i].imag)))
        _, Cw = coherence_series(wide, FS_HZ)
        Cp = [float(np.mean(coherence_series(c, FS_HZ)[1])) for c in chans]
        phases = np.vstack([instantaneous_phase(c) for c in chans])
        aniso = spatial_phase_anisotropy(phases, FS_HZ)
        results[cond] = {"C_wide_mean": float(np.mean(Cw)),
                         "C_point_mean": float(np.mean(Cp)),
                         "aniso_scalar": aniso["scalar_rad2_per_s2"]}
    path = os.path.join(OUTDIR, "case_g_sensor_geometry.csv")
    write_csv(path, ["condition", "t_s", "p1_I", "p1_Q", "p2_I", "p2_Q",
                     "p3_I", "p3_Q", "wide_I", "wide_Q"], rows)

    r = results
    entry = {
        "file": os.path.basename(path),
        "description": "Spatial-filtering analogue of KOS-11: three point "
                       "sensors at 30/75/120 mm and one 60-mm-aperture "
                       "'wide' sensor on a 150 mm 1-D standing-wave field. "
                       "Long-wavelength mode (300 mm) survives aperture "
                       "averaging; short-wavelength mode (20 mm) is "
                       "averaged out (aperture = 3 lambda exactly), so the "
                       "wide sensor's coherence falls to the noise "
                       "baseline while point sensors still see it. "
                       "'Spatial phase anisotropy' scalar (GAN-05 "
                       "mathematical analogy ONLY — never 'quantum shear') "
                       "is small for the common coherent mode and large "
                       "for mutually detuned channels.",
        "classification": "Derived (synthetic)",
        "seed": seed,
        "params": {"fs_hz": FS_HZ, "f0_hz": F0_HZ,
                   "sensor_x_mm": sensor_x_mm.tolist(),
                   "aperture_mm": aperture_mm, "length_mm": length_mm,
                   "noise_sigma": sigma_n,
                   "lambda_long_mm": 300.0, "lambda_short_mm": 20.0,
                   "n_samples": n},
        "expected": {
            "long_point_coherence": {"value": r["coherent_long"]
                                     ["C_point_mean"], "atol": 0.05},
            "long_wide_coherence": {"value": r["coherent_long"]
                                    ["C_wide_mean"], "atol": 0.05,
                                    "note": "aperture passes long lambda"},
            "short_point_coherence": {"value": r["coherent_short"]
                                      ["C_point_mean"], "atol": 0.05,
                                      "note": "point sensors still coherent"},
            "short_wide_coherence": {"value": r["coherent_short"]
                                     ["C_wide_mean"], "atol": 0.08,
                                     "note": "aperture-averaged toward "
                                             "noise baseline"},
            "aniso_scalar_coherent_long": {
                "value": r["coherent_long"]["aniso_scalar"], "rtol": 0.5,
                "note": "small: common phase rate across channels"},
            "aniso_scalar_detuned": {
                "value": r["detuned_channels"]["aniso_scalar"], "rtol": 0.2,
                "note": "theory ~ ((2pi*50)^2 + (2pi*100)^2 + (2pi*50)^2)/3"
                        " = 1.97e5 rad^2/s^2"},
            "aniso_ratio_detuned_over_long": {
                "value": r["detuned_channels"]["aniso_scalar"]
                / r["coherent_long"]["aniso_scalar"],
                "min": 10.0,
                "note": "detuned/long anisotropy ratio must exceed 10"},
        },
    }
    manifest["datasets"]["case_g_sensor_geometry"] = entry
    return {"results": results}


# ===========================================================================
# Plots
# ===========================================================================

def make_plots(res: dict) -> list[str]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    os.makedirs(PLOTDIR, exist_ok=True)
    made = []

    def save(fig, name):
        p = os.path.join(PLOTDIR, name)
        fig.tight_layout()
        fig.savefig(p, dpi=120)
        plt.close(fig)
        made.append(p)

    # a + b: coherence traces
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(res["a"]["tc"] * 1e3, res["a"]["C"], label="white noise (a)")
    ax.plot(res["b"]["tc"] * 1e3, res["b"]["C"], label="pure sinusoid (b)")
    nwin = int(round(WINDOW_S * FS_HZ))
    ax.axhline((2 * math.sqrt(math.pi) / 3) / math.sqrt(nwin), ls="--",
               c="gray", label="theoretical noise baseline")
    ax.set(xlabel="t (ms)", ylabel="coherence C_w(t)", ylim=(0, 1.05),
           title="Cases a/b: coherence bounds (KOS-07-style metric)")
    ax.legend()
    save(fig, "case_ab_coherence_bounds.png")

    # c: amplitude vs coherence
    c = res["c"]
    fig, ax1 = plt.subplots(figsize=(7, 4))
    ax1.plot(c["t"] * 1e3, np.abs(c["z"]), c="0.8", lw=0.5,
             label="|z(t)| raw")
    ax1.plot(c["t"] * 1e3, c["env"], c="C0", label="true envelope")
    ax1.axhline(0.05, ls=":", c="C0", label="noise sigma")
    ax1.set(xlabel="t (ms)", ylabel="amplitude")
    ax2 = ax1.twinx()
    ax2.plot(c["tc"] * 1e3, c["C"], c="C3", label="coherence C_w(t)")
    ax2.plot(c["tcn"] * 1e3, c["Cn"], c="C2", ls="--",
             label="amplitude-normalized C")
    ax2.set(ylabel="coherence", ylim=(0, 1.05))
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper right", fontsize=8)
    ax1.set_title("Case c: coherence persists while amplitude decays "
                  "(KOS-10 analogue)")
    save(fig, "case_c_decaying_sinusoid.png")

    # d: ensemble phase histogram
    d = res["d"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 4))
    ax1.hist(d["init_phase"], bins=18, range=(-np.pi, np.pi), color="C0")
    ax1.set(xlabel="initial phase (rad)", ylabel="runs",
            title="Case d: uniform ensemble phase\n(Rayleigh does not "
                  "reject)")
    ax2.hist(d["per_run_C"], bins=20, color="C3")
    ax2.set(xlabel="per-run mean coherence", ylabel="runs",
            title="per-run coherence: high in every run")
    save(fig, "case_d_random_phase_runs.png")

    # e: PLV vs K with threshold
    e = res["e"]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.errorbar(e["K_grid"], e["plv"].mean(axis=1),
                yerr=e["plv"].std(axis=1), fmt="o-", capsize=3,
                label="PLV mean +/- sd (8 runs)")
    ax.axvline(e["k_c_true"], ls="--", c="gray",
               label=f"K_c theory = {e['k_c_true']:.2f}")
    ax.axvspan(e["thr"]["ci_lo"], e["thr"]["ci_hi"], color="C1", alpha=0.2,
               label="bootstrap 95% CI of detected threshold")
    ax.set(xlabel="coupling K (1/s)", ylabel="phase-locking value",
           title="Case e: parameter-dependent locking of coupled "
                 "Stuart-Landau oscillators")
    ax.legend()
    save(fig, "case_e_locking_threshold.png")

    # f: false coherence + phase clustering
    f = res["f"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 4))
    ax1.hist(f["stats"]["sample"]["C"], bins=20, alpha=0.6,
             label="sample runs")
    ax1.hist(f["stats"]["control"]["C"], bins=20, alpha=0.6,
             label="control (no-crystal) runs")
    ax1.set(xlabel="per-run mean coherence", ylabel="runs",
            title="Case f: identical 'coherence' in sample and control")
    ax1.legend()
    ax2.hist(f["stats"]["sample"]["ph"], bins=18, range=(-np.pi, np.pi))
    ax2.axvline(0.4, ls="--", c="r", label="pump phase 0.4 rad")
    ax2.set(xlabel="ensemble initial phase (rad)", ylabel="runs",
            title="phase locked to pump:\nRayleigh REJECTS uniformity")
    ax2.legend()
    save(fig, "case_f_pump_leakage_controls.png")

    # g: sensor geometry
    g = res["g"]["results"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 4))
    conds = ["coherent_long", "coherent_short"]
    x = np.arange(len(conds))
    ax1.bar(x - 0.18, [g[c]["C_point_mean"] for c in conds], 0.36,
            label="point sensors")
    ax1.bar(x + 0.18, [g[c]["C_wide_mean"] for c in conds], 0.36,
            label="wide (60 mm) sensor")
    ax1.set_xticks(x, ["lambda=300 mm", "lambda=20 mm"])
    ax1.set(ylabel="mean coherence",
            title="Case g: aperture averaging suppresses\nshort-wavelength "
                  "coherence (KOS-11 analogue)")
    ax1.legend()
    names = ["coherent_long", "coherent_short", "detuned_channels"]
    ax2.bar(range(3), [g[c]["aniso_scalar"] for c in names], color="C4")
    ax2.set_yscale("log")
    ax2.set_xticks(range(3), ["long", "short", "detuned\nchannels"],
                   fontsize=8)
    ax2.set(ylabel="spatial phase anisotropy (rad$^2$/s$^2$)",
            title="anisotropy scalar (GAN-05 analogy,\nnot 'quantum shear')")
    save(fig, "case_g_sensor_geometry.png")

    return made


# ===========================================================================
# Main
# ===========================================================================

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-plots", action="store_true")
    args = ap.parse_args()

    os.makedirs(OUTDIR, exist_ok=True)
    manifest = {
        "name": "RGCS v2 golden coherence datasets",
        "generator": "tools/generate_golden_coherence.py",
        "master_seed": MASTER_SEED,
        "fs_hz": FS_HZ,
        "f0_hz": F0_HZ,
        "coherence_window_s": WINDOW_S,
        "coherence_hop_s": HOP_S,
        "classification_policy": "docs/SCIENTIFIC_CLASSIFICATION_POLICY.md",
        "metric_spec": "docs/COHERENCE_METRICS.md",
        "test_matrix": "docs/COHERENCE_TEST_MATRIX.md",
        "notes": [
            "All datasets are Derived synthetic records; none are "
            "measurements.",
            "Coherence metric adapted from KOS-07 (Koster et al. 2026, "
            "Methods) as an Established signal-processing definition.",
            "'Spatial phase anisotropy' adapts the GAN-05 shear-scalar "
            "FORM as a mathematical analogy only; no physical equivalence "
            "with cosmological shear (or magnon BEC) is claimed.",
            "Tolerance semantics: atol = |got - value| <= atol; rtol = "
            "|got - value| <= rtol*|value|; min/max = one-sided bound; "
            "exact = string equality.",
        ],
        "datasets": {},
    }

    res = {}
    res["a"] = case_a_white_noise(manifest)
    res["b"] = case_b_pure_sinusoid(manifest)
    res["c"] = case_c_decaying_sinusoid(manifest)
    res["d"] = case_d_random_phase_runs(manifest)
    res["e"] = case_e_coupled_oscillators(manifest)
    res["f"] = case_f_pump_leakage(manifest)
    res["g"] = case_g_sensor_geometry(manifest)

    if not args.no_plots:
        manifest["plots"] = [os.path.relpath(p, OUTDIR)
                             for p in make_plots(res)]

    mpath = os.path.join(OUTDIR, "manifest.json")
    with open(mpath, "w") as fh:
        json.dump(manifest, fh, indent=2)
    print(f"wrote {mpath}")
    for name, entry in manifest["datasets"].items():
        print(f"  {name}: {entry['file']}")
        for k, v in entry["expected"].items():
            print(f"    {k}: {v.get('value')}")


if __name__ == "__main__":
    main()
