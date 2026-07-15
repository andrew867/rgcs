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
           "hybrid_frequencies", "apply_coupling"]


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
