"""RSCS-O.4 mode-coupling operator (anti-Hermitian, K = i*2*pi*g).

This is the keystone operator. It generalizes the frozen v2 coupled-mode
machinery (RGCS-M.23-28 frequency-domain eigenproblem; RGCS-M.46 time-domain
complex dynamics) and MUST preserve the QA-D-04 correction:

    the time-domain coupling is anti-Hermitian, K_nm = i * 2*pi * g_nm,

so a degenerate pair splits by 2g in FREQUENCY (peaks at f0 +/- g) with
purely oscillatory, non-growing amplitude. A real-symmetric K = pi*g (the
pre-QA-D-04 error) splits growth rates instead and is forbidden.

Two representations are returned together and kept consistent:
  * frequency-domain Hermitian matrix H (Hz): H = diag(f) + g_matrix; its
    real eigenvalues are the hybrid frequencies (reproduces RGCS-M.24/M.28);
  * time-domain anti-Hermitian coupling K (rad/s): K = i*2*pi*g_matrix, the
    off-diagonal generator entering RGCS-M.46.

Provenance: EP-01-01 (Sohn two-mode EoM), EP-04-01 (Wang anti-symmetric
coupling). Exclusions: no phonon-ATS / atomic-vapor physics imported.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .. import units as U
from ..coordinates import ModalState
from ..registry import rscs_classified

__all__ = ["frequency_matrix", "anti_hermitian_coupling", "couple_modes",
           "hybrid_frequencies", "apply_coupling",
           "overlap_integral", "mode_conversion",
           "state_dependent_susceptibility", "nonreciprocal_metrics"]


def _validate_g(g_matrix_hz: np.ndarray, n: int) -> np.ndarray:
    g = np.asarray(g_matrix_hz, dtype=float)
    if g.shape != (n, n):
        raise ValueError(f"g_matrix_hz must be {n}x{n}")
    if not np.all(np.isfinite(g)):
        raise ValueError("g_matrix_hz must be finite")
    if not np.allclose(g, g.T, atol=1e-9):
        raise ValueError("g_matrix_hz must be symmetric (g_nm = g_mn)")
    if not np.allclose(np.diag(g), 0.0, atol=1e-9):
        raise ValueError("g_matrix_hz must have zero diagonal (g_nn = 0)")
    return g


@rscs_classified("EST", registry=("RSCS-O.4",), provenance=("EP-01-01",),
                 units="Hz (matrix entries)",
                 note="frequency-domain Hermitian coupling matrix; "
                      "eigenvalues are hybrid frequencies (RGCS-M.24/M.28)")
def frequency_matrix(frequencies_hz: np.ndarray | list[float],
                     g_matrix_hz: np.ndarray | list[list[float]]) -> np.ndarray:
    """H = diag(f) + g_matrix (Hz), real symmetric (RGCS-M.23/M.28 form)."""
    f = np.asarray(frequencies_hz, dtype=float)
    if f.ndim != 1 or f.size < 1:
        raise ValueError("frequencies_hz must be a non-empty 1-D array")
    if np.any(~np.isfinite(f)) or np.any(f <= 0):
        raise ValueError("all frequencies must be positive and finite")
    g = _validate_g(g_matrix_hz, f.size)
    return np.diag(f) + g


@rscs_classified("DER", registry=("RSCS-O.4",),
                 provenance=("EP-01-01", "EP-04-01"),
                 units="rad/s (matrix entries)",
                 exclusions=("no phonon-ATS physics (SRC-3-01)",
                             "no atomic-vapor NLNR physics (SRC-3-04)"),
                 note="anti-Hermitian time-domain coupling K = i*2*pi*g "
                      "(QA-D-04, frozen); NOT real-symmetric pi*g")
def anti_hermitian_coupling(g_matrix_hz: np.ndarray | list[list[float]]
                            ) -> np.ndarray:
    """K = i * 2*pi * g_matrix (rad/s). Anti-Hermitian: K^dagger = -K."""
    g = np.asarray(g_matrix_hz, dtype=float)
    if g.ndim != 2 or g.shape[0] != g.shape[1]:
        raise ValueError("g_matrix_hz must be square")
    g = _validate_g(g, g.shape[0])
    return 1j * U.TWO_PI * g


@rscs_classified("EST", registry=("RSCS-O.4",), provenance=("EP-01-01",),
                 units="Hz", note="real eigenvalues of H (RGCS-M.24/M.28)")
def hybrid_frequencies(frequencies_hz: np.ndarray | list[float],
                       g_matrix_hz: np.ndarray | list[list[float]]
                       ) -> np.ndarray:
    """Sorted hybrid (dressed) frequencies: eigenvalues of H (Hz)."""
    h = frequency_matrix(frequencies_hz, g_matrix_hz)
    return np.linalg.eigvalsh(h)


@rscs_classified("EST", registry=("RSCS-O.4",),
                 provenance=("EP-01-01", "EP-04-01"), units="Hz + rad/s",
                 note="both representations with the frozen anti-Hermitian "
                      "convention; degenerate pair -> 2g Hz splitting")
def couple_modes(frequencies_hz: np.ndarray | list[float],
                 g_matrix_hz: np.ndarray | list[list[float]]) -> dict[str, Any]:
    """Full coupling result: Hermitian H (Hz), anti-Hermitian K (rad/s),
    hybrid frequencies, and the min splitting (2g for a degenerate pair)."""
    h = frequency_matrix(frequencies_hz, g_matrix_hz)
    k = anti_hermitian_coupling(g_matrix_hz)
    vals = np.linalg.eigvalsh(h)
    return {
        "frequency_matrix_hz": h,
        "coupling_k_rad_s": k,
        "hybrid_frequencies_hz": vals,
        "splitting_hz": float(vals[-1] - vals[0]),
        "is_anti_hermitian": bool(np.allclose(k.conj().T, -k, atol=1e-12)),
    }


@rscs_classified("EST", registry=("RSCS-O.4",), provenance=("EP-01-01",),
                 units="dimensionless (acts on ModalState)",
                 note="one explicit-Euler step of the coupling-only dynamics; "
                      "used to demonstrate 2g beating, not for production "
                      "integration (use rgcs_core.coupled_modes for that)")
def apply_coupling(state: ModalState,
                   g_matrix_hz: np.ndarray | list[list[float]],
                   dt_s: float) -> ModalState:
    """Advance a ModalState by dt under the coupling generator only:
    psi -> psi + K psi dt, K = i*2*pi*g. Small-step demonstrator."""
    if not (isinstance(dt_s, (int, float)) and np.isfinite(dt_s) and dt_s > 0):
        raise ValueError("dt_s must be positive and finite")
    k = anti_hermitian_coupling(g_matrix_hz)
    if k.shape[0] != state.n_modes:
        raise ValueError("coupling matrix size must match the modal state")
    return ModalState(state.amplitudes + (k @ state.amplitudes) * dt_s)


# --- Agent 06: photon-phonon mode conversion (RSCS-O.19) ---

@rscs_classified("EST", registry=("RSCS-O.19",), provenance=("EP-02-02",),
                 units="dimensionless (normalized inner product)",
                 note="normalized overlap <a|b>/(|a||b|); |overlap| <= 1 "
                      "(Cauchy-Schwarz); orthogonal profiles -> 0")
def overlap_integral(profile_a: np.ndarray, profile_b: np.ndarray,
                     weight: np.ndarray | None = None) -> complex:
    """Normalized overlap of two sampled mode profiles:

        overlap = sum(w a* b) / sqrt(sum(w |a|^2) sum(w |b|^2)).

    Discretized inner product on a shared sampling grid; ``weight`` is an
    optional positive quadrature/medium weight. |overlap| = 1 for identical
    shapes, 0 for orthogonal ones."""
    a = np.asarray(profile_a, dtype=complex).ravel()
    b = np.asarray(profile_b, dtype=complex).ravel()
    if a.size == 0 or a.shape != b.shape:
        raise ValueError("profiles must be non-empty and the same shape")
    if not (np.all(np.isfinite(a.real)) and np.all(np.isfinite(a.imag))
            and np.all(np.isfinite(b.real)) and np.all(np.isfinite(b.imag))):
        raise ValueError("profiles must be finite")
    if weight is None:
        w = np.ones(a.size)
    else:
        w = np.asarray(weight, dtype=float).ravel()
        if w.shape != a.shape or not np.all(np.isfinite(w)) or np.any(w < 0):
            raise ValueError("weight must be finite, non-negative, same shape")
    na = float(np.sum(w * np.abs(a) ** 2))
    nb = float(np.sum(w * np.abs(b) ** 2))
    if na == 0.0 or nb == 0.0:
        raise ValueError("profiles must have non-zero norm under the weight")
    return complex(np.sum(w * np.conj(a) * b) / np.sqrt(na * nb))


@rscs_classified("DER", registry=("RSCS-O.19",),
                 provenance=("EP-02-01", "EP-02-02"),
                 units="dimensionless (efficiency in [0, 1])",
                 exclusions=("no THz-bandwidth AO isolation import "
                             "(SRC-3-02); efficiency is a selection-rule "
                             "bookkeeping, not a quartz device prediction",),
                 note="all four selection rules: frequency (w_out = w_in + "
                      "Omega), momentum (sinc^2), parity flip, overlap")
def mode_conversion(omega_in_rad_s: float, omega_drive_rad_s: float,
                    omega_out_rad_s: float,
                    k_in_rad_mm: float, q_drive_rad_mm: float,
                    k_out_rad_mm: float,
                    parity_in: int, parity_out: int,
                    overlap: complex,
                    interaction_length_mm: float,
                    freq_tol_rad_s: float = 1e-6) -> dict[str, Any]:
    """Photon-phonon (or any two-mode) conversion selection rules (RSCS-O.19).

    Checks the four rules of EP-02-01/02:
      1. frequency:  w_out = w_in + Omega_drive (within freq_tol);
      2. momentum:   Delta_q = k_in + q - k_out; response ~ sinc^2(Dq L/2);
      3. parity:     the drive couples opposite-parity modes (must flip);
      4. overlap:    efficiency scales with |overlap|^2.

    Returns each rule's verdict, the phase mismatch, and the relative
    conversion efficiency eta = |overlap|^2 sinc^2(Dq L/2) * [rules]."""
    for name, v in (("omega_in_rad_s", omega_in_rad_s),
                    ("omega_drive_rad_s", omega_drive_rad_s),
                    ("omega_out_rad_s", omega_out_rad_s),
                    ("k_in_rad_mm", k_in_rad_mm),
                    ("q_drive_rad_mm", q_drive_rad_mm),
                    ("k_out_rad_mm", k_out_rad_mm)):
        if not np.isfinite(v):
            raise ValueError(f"{name} must be finite")
    if parity_in not in (-1, 1) or parity_out not in (-1, 1):
        raise ValueError("parity must be +1 (even) or -1 (odd)")
    if not (np.isfinite(interaction_length_mm)
            and interaction_length_mm > 0):
        raise ValueError("interaction_length_mm must be positive and finite")
    ov = complex(overlap)
    if abs(ov) > 1.0 + 1e-9:
        raise ValueError("|overlap| must be <= 1 (normalized; see "
                         "overlap_integral)")

    freq_matched = bool(abs(float(omega_in_rad_s) + float(omega_drive_rad_s)
                            - float(omega_out_rad_s)) <= freq_tol_rad_s)
    delta_q = (float(k_in_rad_mm) + float(q_drive_rad_mm)
               - float(k_out_rad_mm))
    parity_flips = parity_in != parity_out
    # sinc^2 momentum response (np.sinc is sin(pi x)/(pi x))
    momentum_response = float(
        np.sinc(delta_q * float(interaction_length_mm) / (2.0 * np.pi)) ** 2)
    efficiency = (abs(ov) ** 2 * momentum_response
                  if (freq_matched and parity_flips) else 0.0)
    return {
        "frequency_matched": freq_matched,
        "delta_q_rad_mm": delta_q,
        "momentum_response": momentum_response,
        "parity_allowed": parity_flips,
        "overlap_mag": abs(ov),
        "allowed": bool(freq_matched and parity_flips and abs(ov) > 0.0),
        "efficiency": efficiency,
    }


# --- Agent 06: state-dependent susceptibility + nonreciprocal metrics
#     (RSCS-O.22) ---

@rscs_classified("DER", registry=("RSCS-O.22",),
                 provenance=("EP-04-01", "EP-04-02"),
                 units="dimensionless (susceptibility)",
                 exclusions=("no atomic-vapor self-induced-nonreciprocity "
                             "physics import (SRC-3-04); chi_xy is a model "
                             "parameter, zero for unbiased quartz (D6-003)",),
                 note="chi_xy = chi1*bias + chi3*spin: bias term + "
                      "state-dependent term (EP-04-02 expansion)")
def state_dependent_susceptibility(chi1: complex, bias_b_z: float,
                                   chi3: complex, spin_s_z: float) -> complex:
    """Off-diagonal susceptibility chi_xy = chi1*B_z + chi3*s_z (EP-04-02):
    a bias-driven term plus a state-dependent term proportional to the
    drive-field spin s_z = (E x E*).e_z in [-1, 1]. Linear in both; both
    zero -> chi_xy = 0 (reciprocal null, D6-003)."""
    c1, c3 = complex(chi1), complex(chi3)
    for name, v in (("chi1", c1), ("chi3", c3)):
        if not (np.isfinite(v.real) and np.isfinite(v.imag)):
            raise ValueError(f"{name} must be finite")
    if not np.isfinite(bias_b_z):
        raise ValueError("bias_b_z must be finite")
    if not np.isfinite(spin_s_z) or not -1.0 <= spin_s_z <= 1.0:
        raise ValueError("spin_s_z must be finite and in [-1, 1]")
    return c1 * float(bias_b_z) + c3 * float(spin_s_z)


@rscs_classified("DER", registry=("RSCS-O.22",), provenance=("EP-04-03",),
                 units="dimensionless ratio + rad",
                 exclusions=("no atomic-vapor isolation performance import "
                             "(SRC-3-04)",),
                 note="T_ratio = exp(-4 k Im(chi_xy) L); phi_nr = "
                      "2 k Re(chi_xy) L; chi_xy = 0 -> ratio 1, phase 0")
def nonreciprocal_metrics(chi_xy: complex, k_rad_mm: float,
                          length_mm: float) -> dict[str, float]:
    """Directional metrics of a complex off-diagonal susceptibility
    (EP-04-03): counter-propagating transmittance ratio
    T_b/T_f = exp(-4 k Im(chi_xy) L) and nonreciprocal phase
    phi_nr = 2 k Re(chi_xy) L (rad). Both trivial (1, 0) when chi_xy = 0 --
    the reciprocity null of D6-003."""
    c = complex(chi_xy)
    if not (np.isfinite(c.real) and np.isfinite(c.imag)):
        raise ValueError("chi_xy must be finite")
    for name, v in (("k_rad_mm", k_rad_mm), ("length_mm", length_mm)):
        if not (np.isfinite(v) and v >= 0):
            raise ValueError(f"{name} must be finite and >= 0")
    kl = float(k_rad_mm) * float(length_mm)
    return {
        "transmittance_ratio": float(np.exp(-4.0 * kl * c.imag)),
        "nonreciprocal_phase_rad": 2.0 * kl * c.real,
        "reciprocal": bool(c == 0),
    }
