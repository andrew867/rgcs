"""Spatial phase anisotropy (COH-M13; RGCS-M.51..M.53) — exact port of
the normative reference in tools/generate_golden_coherence.py.

Units: phases in rad, phase rates in rad/s, anisotropy scalar in
rad^2/s^2; circular-variance tensor dimensionless in [0, 1].

The scalar adapts the GAN Eq. (2) FORM (GAN-05, Gan et al. 2025;
substitution map H_i -> h_i, per-axis phase rates) as a mathematical
analogy ONLY; no physical equivalence with cosmological shear or any
quantum system is claimed, and cosmology-specific coefficients are never
imported. Windowed slopes (not raw gradients) are NORMATIVE: raw
sample-to-sample gradients let additive-noise jitter swamp sustained
inter-channel disagreement and fail the golden tests.
"""

from __future__ import annotations

import math

import numpy as np

from ..provenance import classified, classification_string
from .metrics import DEFAULT_WINDOW_S, DEFAULT_HOP_S

__all__ = ["windowed_phase_rates", "spatial_phase_anisotropy",
           "phase_rate_shear_scalar", "circular_variance_tensor"]


@classified("Derived", registry=("RGCS-M.51",),
            note="COH-M13 helper; windowed least-squares slopes are "
                 "NORMATIVE (raw gradients fail the golden tests)")
def windowed_phase_rates(phases: np.ndarray, fs: float,
                         window_s: float = DEFAULT_WINDOW_S,
                         hop_s: float = DEFAULT_HOP_S) -> np.ndarray:
    """Per-channel windowed phase rates h_i(t_k) (rad/s): least-squares
    slope of the unwrapped phase within boxcar windows (length window_s,
    hop hop_s). Input shape (M, N); output shape (M, n_windows)."""
    ph = np.asarray(phases, float)
    if ph.ndim != 2 or ph.shape[0] < 1:
        raise ValueError("phases must have shape (M, N) with M >= 1")
    if not (math.isfinite(fs) and fs > 0):
        raise ValueError("fs must be positive")
    nwin = max(int(round(window_s * fs)), 2)
    nhop = max(int(round(hop_s * fs)), 1)
    if ph.shape[1] < nwin:
        raise ValueError("record shorter than one analysis window")
    starts = np.arange(0, ph.shape[1] - nwin + 1, nhop)
    tt = np.arange(nwin) / fs
    rates = np.empty((ph.shape[0], starts.size))
    for i in range(ph.shape[0]):
        for k, s in enumerate(starts):
            rates[i, k] = np.polyfit(tt, ph[i, s:s + nwin], 1)[0]
    return rates


@classified("Derived", registry=("RGCS-M.51", "RGCS-M.52"),
            sources=("GAN-04", "GAN-05"),
            note="COH-M13: mathematical analogy to the GAN-05 scalar FORM "
                 "only (substitution H_i -> h_i); a measured statistic of "
                 "directional data, nothing cosmological")
def spatial_phase_anisotropy(phases: np.ndarray, fs: float,
                             window_s: float = DEFAULT_WINDOW_S,
                             hop_s: float = DEFAULT_HOP_S) -> dict:
    """COH-M13. Spatial phase anisotropy for M spatial sensor channels.

    Input phases: shape (M, N) unwrapped instantaneous phases.
    h_i(t_k) = windowed phase rate (rad/s);
    hbar(t) = mean_i h_i(t)   (isotropic part, expansion-scalar analogue);
    Tensor  T_jk = < (h_j - hbar)(h_k - hbar) >_t      (M x M, rad^2/s^2);
    Scalar  sigma_phi^2 = < (1/M) sum_{i<j} (h_i - h_j)^2 >_t.
    For M = 3 the scalar reduces to the GAN Eq. (2) form
    ((h1-h2)^2 + (h2-h3)^2 + (h3-h1)^2)/3 applied to phase rates.
    Zero iff all channels share one phase rate in every window;
    permutation invariant; common-rate shifts leave it unchanged."""
    ph = np.asarray(phases, float)
    if ph.ndim != 2 or ph.shape[0] < 2:
        raise ValueError("phases must have shape (M, N) with M >= 2")
    m = ph.shape[0]
    h = windowed_phase_rates(ph, fs, window_s, hop_s)
    hbar = h.mean(axis=0)
    dev = h - hbar
    tensor = (dev @ dev.T) / dev.shape[1]
    pair = 0.0
    for i in range(m):
        for j in range(i + 1, m):
            pair += np.mean((h[i] - h[j]) ** 2)
    scalar = float(pair / m)
    return {"scalar_rad2_per_s2": scalar,
            "isotropic_mean_rate_rad_s": hbar.tolist(),
            "tensor": tensor.tolist(),
            "n_channels": m,
            "classification":
                classification_string(spatial_phase_anisotropy)}


@classified("Established", registry=("RGCS-M.52",), sources=("GAN-05",),
            note="definition Established (exact adaptation of GAN Eq. (2) "
                 "FORM, substitution H_i -> Omega_j); a measured statistic")
def phase_rate_shear_scalar(omega_1: float, omega_2: float,
                            omega_3: float) -> dict:
    """Phase-rate shear scalar for three instantaneous rates (RGCS-M.52):
    sigma_phi^2 = ((O1-O2)^2 + (O2-O3)^2 + (O3-O1)^2)/3, with the
    isotropic mean rate Theta_phi = (O1+O2+O3)/3 reported alongside
    (GAN-04 decomposition lesson). Golden identities (G-15): zero for
    equal rates; permutation invariant; common-rate shift invariant."""
    for name, v in (("omega_1", omega_1), ("omega_2", omega_2),
                    ("omega_3", omega_3)):
        if not math.isfinite(v):
            raise ValueError(f"{name} must be finite")
    sigma2 = ((omega_1 - omega_2) ** 2 + (omega_2 - omega_3) ** 2
              + (omega_3 - omega_1) ** 2) / 3.0
    theta = (omega_1 + omega_2 + omega_3) / 3.0
    denom = theta * theta
    if denom > 0.0 and math.isfinite(sigma2 / denom):
        dimensionless = sigma2 / denom
    else:
        dimensionless = 0.0 if sigma2 == 0.0 else float("inf")
    return {"sigma_phi2_s2": sigma2,
            "mean_rate_theta_phi_s": theta,
            "dimensionless_anisotropy": dimensionless,
            "classification":
                classification_string(phase_rate_shear_scalar)}


@classified("Derived", registry=("RGCS-M.53",),
            note="Established circular statistics; entries in [0, 1]: 0 = "
                 "locked relative phase over the window, 1 = uniformly "
                 "random relative phase")
def circular_variance_tensor(phases: np.ndarray) -> dict:
    """Circular-variance phase-anisotropy tensor (RGCS-M.53):
    Sigma_jk = 1 - |< exp(i(phi_j - phi_k)) >_window|, j != k; zero
    diagonal. Input shape (M, N) over one analysis window. Also reports
    the scalar reduction (mean of off-diagonal upper triangle) and the
    per-channel circular variance V_j = 1 - Rbar_j (needed for the
    Rayleigh spontaneity test, RGCS-M.61)."""
    ph = np.asarray(phases, float)
    if ph.ndim != 2 or ph.shape[0] < 2 or ph.shape[1] < 1:
        raise ValueError("phases must have shape (M, N), M >= 2, N >= 1")
    m = ph.shape[0]
    sig = np.zeros((m, m))
    pairs = []
    for j in range(m):
        for k in range(j + 1, m):
            v = 1.0 - float(np.abs(np.mean(np.exp(1j * (ph[j] - ph[k])))))
            sig[j, k] = sig[k, j] = v
            pairs.append(v)
    per_channel_v = [1.0 - float(np.abs(np.mean(np.exp(1j * ph[j]))))
                     for j in range(m)]
    return {"tensor": sig.tolist(),
            "scalar_mean_offdiag": float(np.mean(pairs)),
            "per_channel_circular_variance": per_channel_v,
            "n_channels": m,
            "classification":
                classification_string(circular_variance_tensor)}
