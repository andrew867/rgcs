"""Frequency-domain coupled-mode eigenproblems (RGCS-M.23..M.29).

Units: all matrix entries in Hz; angles in rad (mixing angle also deg).
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from ..provenance import classified, classification_string
from ..resonance import linewidth_fwhm_hz

__all__ = ["coupled_two_mode", "n_mode_eigenproblem",
           "avoided_crossing_sweep", "coupling_geometry_scaling",
           "coupling_rate_from_g_hz", "g_hz_from_coupling_rate",
           "coupling_consistency"]


def _positive(name: str, v: float) -> None:
    if not (math.isfinite(v) and v > 0):
        raise ValueError(f"{name} must be positive and finite; got {v!r}")


@classified("Established", registry=("RGCS-M.23", "RGCS-M.24", "RGCS-M.25",
                                     "RGCS-M.26", "RGCS-M.27"),
            sources=("RG-07",),
            note="standard avoided-crossing model; FWHM linewidth "
                 "convention stated (D-19c); strong-coupling criterion "
                 "citation required (D-19c)")
def coupled_two_mode(f_a_hz: float, f_b_hz: float, coupling_hz: float,
                     q_a: float = 1000.0, q_b: float = 1000.0
                     ) -> dict[str, Any]:
    """Two-mode avoided crossing (RGCS-M.23/M.24):
    f_pm = (f_A + f_B)/2 +- sqrt(((f_A - f_B)/2)^2 + g^2); mixing angle
    theta_mix = (1/2) atan2(2g, f_A - f_B) (RGCS-M.25); strong-coupling
    ratio R_g = 2g/(Gamma_A + Gamma_B) (RGCS-M.27).
    Golden: f_A = f_B = 1000 Hz, g = 10 Hz -> 990/1010 Hz (G-08)."""
    _positive("f_a_hz", f_a_hz)
    _positive("f_b_hz", f_b_hz)
    _positive("q_a", q_a)
    _positive("q_b", q_b)
    if coupling_hz < 0 or not math.isfinite(coupling_hz):
        raise ValueError("coupling_hz must be >= 0 and finite")
    mean = (f_a_hz + f_b_hz) / 2.0
    split = math.hypot((f_a_hz - f_b_hz) / 2.0, coupling_hz)
    gamma_a = linewidth_fwhm_hz(f_a_hz, q_a)
    gamma_b = linewidth_fwhm_hz(f_b_hz, q_b)
    mixing = 0.5 * math.atan2(2.0 * coupling_hz, f_a_hz - f_b_hz)
    return {
        "lower_hybrid_hz": mean - split,
        "upper_hybrid_hz": mean + split,
        "splitting_hz": 2.0 * split,
        "uncoupled_detuning_hz": f_a_hz - f_b_hz,
        "mixing_angle_rad": mixing,
        "mixing_angle_deg": math.degrees(mixing),
        "linewidth_a_hz": gamma_a,
        "linewidth_b_hz": gamma_b,
        "strong_coupling_ratio": 2.0 * coupling_hz / (gamma_a + gamma_b),
        "coupling_rate_s": coupling_rate_from_g_hz(coupling_hz),
        "classification": classification_string(coupled_two_mode),
    }


@classified("Established", registry=("RGCS-M.28",),
            note="linear algebra Established; fitted g_nm are Derived; "
                 "valid in the near-degenerate weak-coupling regime (A-04), "
                 "NOT a substitute for full elastodynamics")
def n_mode_eigenproblem(frequencies_hz: np.ndarray | list[float],
                        g_matrix_hz: np.ndarray | list[list[float]]
                        ) -> dict[str, Any]:
    """N-mode coupled eigenproblem (RGCS-M.28): H_nm = f_n delta_nm + g_nm
    with g symmetric, zero diagonal. Returns sorted real eigenvalues
    (hybrid frequencies) and orthonormal eigenvectors (numpy.linalg.eigh)."""
    f = np.asarray(frequencies_hz, dtype=float)
    g = np.asarray(g_matrix_hz, dtype=float)
    if f.ndim != 1 or f.size < 1:
        raise ValueError("frequencies_hz must be a non-empty 1-D array")
    if np.any(~np.isfinite(f)) or np.any(f <= 0):
        raise ValueError("all frequencies must be positive and finite")
    if g.shape != (f.size, f.size):
        raise ValueError("g_matrix_hz must be square, matching frequencies")
    if np.any(~np.isfinite(g)):
        raise ValueError("g_matrix_hz must be finite")
    if not np.allclose(g, g.T, atol=1e-9):
        raise ValueError("g_matrix_hz must be symmetric (g_nm = g_mn)")
    if not np.allclose(np.diag(g), 0.0, atol=1e-9):
        raise ValueError("g_matrix_hz must have zero diagonal (g_nn = 0)")
    h = np.diag(f) + g
    vals, vecs = np.linalg.eigh(h)
    return {
        "hybrid_frequencies_hz": vals,
        "mode_vectors": vecs,           # columns are orthonormal eigenvectors
        "matrix_hz": h,
        "classification": classification_string(n_mode_eigenproblem),
    }


@classified("Established", registry=("RGCS-M.24",),
            note="sweep of the two-mode hybrids for avoided-crossing plots")
def avoided_crossing_sweep(f_a_grid_hz: np.ndarray | list[float],
                           f_b_hz: float, coupling_hz: float
                           ) -> dict[str, Any]:
    """Hybrid branches f_pm(f_A) across a detuning sweep (RGCS-M.24).
    Minimum splitting is 2g at zero detuning."""
    fa = np.asarray(f_a_grid_hz, dtype=float)
    if fa.ndim != 1 or fa.size == 0 or np.any(fa <= 0):
        raise ValueError("f_a_grid_hz must be a 1-D array of positive values")
    _positive("f_b_hz", f_b_hz)
    if coupling_hz < 0:
        raise ValueError("coupling_hz must be >= 0")
    mean = (fa + f_b_hz) / 2.0
    split = np.sqrt(((fa - f_b_hz) / 2.0) ** 2 + coupling_hz ** 2)
    return {"f_a_hz": fa, "lower_hz": mean - split, "upper_hz": mean + split,
            "min_splitting_hz": float(np.min(2.0 * split)),
            "classification": classification_string(avoided_crossing_sweep)}


@classified("Hypothesis", registry=("RGCS-M.29",), sources=("LT-06",),
            note="H-05: g scales as (2 pi R_chi)^(-1/2) at fixed transducer "
                 "and mode pair; failure to scale kills the analogy row")
def coupling_geometry_scaling(g_ref_hz: float, r_ref_mm: float,
                              r_new_mm: float) -> float:
    """Predicted coupling after a compact-path change (RGCS-M.29):
    g_new = g_ref * sqrt(R_ref / R_new). Hypothesis H-05 (LT Eq. (6)
    analogue); testable and falsifiable."""
    _positive("g_ref_hz", g_ref_hz)
    _positive("r_ref_mm", r_ref_mm)
    _positive("r_new_mm", r_new_mm)
    return g_ref_hz * math.sqrt(r_ref_mm / r_new_mm)


@classified("Derived", registry=("RGCS-M.46",),
            note="|K_nm| = 2*pi*g_nm consistency map; the coupling is "
                 "anti-Hermitian, K_nm = i*2*pi*g_nm (2g Hz splitting)")
def coupling_rate_from_g_hz(g_hz: float) -> float:
    """Magnitude of the time-domain coupling rate |K| (rad/s) from the
    frequency-domain half-splitting g (Hz): |K| = 2*pi*g. The coupling
    entering RGCS-M.46 is anti-Hermitian, K_nm = i*2*pi*g_nm: at
    degeneracy the eigenvalues of [[i*omega, i*2*pi*g], [i*2*pi*g,
    i*omega]] are i*(omega +/- 2*pi*g), i.e. spectral peaks at f0 +/- g
    (a 2g Hz splitting) and an amplitude beat with node spacing 1/(4g).
    A real-symmetric K of the same magnitude instead splits *growth
    rates* (cosh growth, no frequency splitting) and is NOT the
    frequency-domain counterpart. Corrected 2026-07-14 (QA-D-04): the
    former map K = pi*g was wrong in structure and magnitude."""
    if g_hz < 0 or not math.isfinite(g_hz):
        raise ValueError("g_hz must be >= 0 and finite")
    return 2.0 * math.pi * g_hz


@classified("Derived", registry=("RGCS-M.46",))
def g_hz_from_coupling_rate(k_s: float) -> float:
    """Frequency-domain half-splitting g (Hz) from the time-domain
    coupling magnitude |K| (rad/s): g = |K| / (2*pi). See
    coupling_rate_from_g_hz for the anti-Hermitian structure."""
    if k_s < 0 or not math.isfinite(k_s):
        raise ValueError("k_s must be >= 0 and finite")
    return k_s / (2.0 * math.pi)


@classified("Derived", registry=("RGCS-M.46",),
            note="pre-registered warning flag: time- and frequency-domain "
                 "coupling estimates must agree (|K| = 2*pi*g)")
def coupling_consistency(k_fit_s: float, g_fit_hz: float,
                         rel_tol: float = 0.2) -> dict[str, Any]:
    """Check the |K_nm| = 2*pi*g_nm consistency between a time-domain fit
    (coupling magnitude |K|, rad/s) and a frequency-domain fit (g, Hz).
    Disagreement beyond rel_tol raises the pre-registered warning flag."""
    if g_fit_hz <= 0 or k_fit_s <= 0:
        raise ValueError("fitted K and g must be positive")
    expected = coupling_rate_from_g_hz(g_fit_hz)
    rel_dev = k_fit_s / expected - 1.0
    return {"k_fit_s": k_fit_s, "g_fit_hz": g_fit_hz,
            "k_expected_s": expected, "relative_deviation": rel_dev,
            "consistent": abs(rel_dev) <= rel_tol,
            "warning_flag": abs(rel_dev) > rel_tol,
            "classification": classification_string(coupling_consistency)}
