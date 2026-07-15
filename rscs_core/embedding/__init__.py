"""RGCS -> RSCS embedding (iota) and the Conservative Extension Property.

The embedding iota: X_RGCS -> X_RSCS maps a frozen v2 quantity into the RSCS
coordinate/operator layer WITHOUT changing its value. The Conservative
Extension Property (CEP) is the binding contract of Agent 03:

    O_RSCS(iota(x)) == iota(O_RGCS(x))

within CONSERVATIVE_EXTENSION_RTOL/ATOL over the frozen v2 test domain. RSCS
never replaces v2 mathematics; where an RSCS operator generalizes an RGCS-M.*
equation it must reproduce it exactly on the v2 domain. The check functions
below return structured evidence used by the regression tests.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from rgcs_core.coherence.metrics import (analytic_signal as _v2_analytic_signal,
                                         coherence_window as _v2_coherence_window)
from rgcs_core.coupled_modes.static import coupled_two_mode as _v2_two_mode
from rgcs_core.coupled_modes.static import n_mode_eigenproblem as _v2_n_mode
from rgcs_core.uncertainty import UncertainValue

from .. import units as U
from ..coordinates import AngularFrequency, ModalState, Uncertainty
from ..coupling import couple_modes, hybrid_frequencies
from ..observation import coherence as rscs_coherence
from ..transforms import time_to_frequency
from ..uncertainty import scale as rscs_scale

__all__ = [
    "iota_frequency", "iota_uncertainty", "iota_record",
    "check_two_mode_cep", "check_n_mode_cep", "check_analytic_signal_cep",
    "check_coherence_cep", "check_uncertainty_cep", "run_all_cep",
]


# --- iota: embed v2 quantities into RSCS coordinates (value-preserving) ---

def iota_frequency(f_hz: float) -> AngularFrequency:
    """Embed a v2 Hz frequency as an RSCS AngularFrequency (RSCS-C.4)."""
    return AngularFrequency.from_hz(f_hz)


def iota_uncertainty(uv: UncertainValue) -> Uncertainty:
    """Embed a v2 UncertainValue as an RSCS Uncertainty (RSCS-C.12)."""
    return Uncertainty(uv.mean, uv.u_rel)


def iota_record(x: np.ndarray) -> np.ndarray:
    """Embed a real time record (identity; RSCS reuses the v2 array)."""
    return np.asarray(x, dtype=float)


def _close(a: Any, b: Any) -> bool:
    return bool(np.allclose(np.asarray(a), np.asarray(b),
                            rtol=U.CONSERVATIVE_EXTENSION_RTOL,
                            atol=U.CONSERVATIVE_EXTENSION_ATOL))


# --- Conservative Extension Property checks ---

def check_two_mode_cep(f_a_hz: float, f_b_hz: float, g_hz: float) -> dict[str, Any]:
    """CEP for the two-mode coupling operator (RSCS-O.4 vs RGCS-M.24).

    The RSCS hybrid frequencies must equal the v2 coupled_two_mode hybrids,
    and the RSCS splitting must equal the v2 splitting (2g at degeneracy)."""
    v2 = _v2_two_mode(f_a_hz, f_b_hz, g_hz)
    g_matrix = [[0.0, g_hz], [g_hz, 0.0]]
    r = couple_modes([f_a_hz, f_b_hz], g_matrix)
    v2_hybrids = sorted((v2["lower_hybrid_hz"], v2["upper_hybrid_hz"]))
    ok_hybrids = _close(r["hybrid_frequencies_hz"], v2_hybrids)
    ok_split = _close(r["splitting_hz"], v2["splitting_hz"])
    return {"property": "two_mode", "ok": ok_hybrids and ok_split,
            "ok_hybrids": ok_hybrids, "ok_splitting": ok_split,
            "rscs_splitting_hz": r["splitting_hz"],
            "v2_splitting_hz": v2["splitting_hz"],
            "anti_hermitian": r["is_anti_hermitian"]}


def check_n_mode_cep(frequencies_hz, g_matrix_hz) -> dict[str, Any]:
    """CEP for the N-mode eigenproblem (RSCS-O.4 vs RGCS-M.28)."""
    v2 = _v2_n_mode(frequencies_hz, g_matrix_hz)
    rscs = hybrid_frequencies(frequencies_hz, g_matrix_hz)
    ok = _close(rscs, v2["hybrid_frequencies_hz"])
    return {"property": "n_mode", "ok": ok, "n": len(list(frequencies_hz))}


def check_analytic_signal_cep(record: np.ndarray) -> dict[str, Any]:
    """CEP for the time->frequency map (RSCS-O.2 vs RGCS-M.55).

    RSCS delegates to v2, so equality is exact (rtol/atol trivially met)."""
    v2 = _v2_analytic_signal(record)
    rscs = time_to_frequency(record)
    return {"property": "analytic_signal", "ok": _close(rscs, v2)}


def check_coherence_cep(segment: np.ndarray) -> dict[str, Any]:
    """CEP for the observation coherence (RSCS-O.10 vs RGCS-M.56)."""
    v2 = _v2_coherence_window(segment)
    rscs = rscs_coherence(segment)
    return {"property": "coherence", "ok": _close(rscs, v2),
            "value": float(rscs)}


def check_uncertainty_cep(mean: float, u_rel: float,
                          factor: float) -> dict[str, Any]:
    """CEP for uncertainty scaling (RSCS-O.11 vs RGCS-M.11).

    Scaling then embedding == embedding then scaling."""
    uv = UncertainValue(mean, u_rel)
    left = iota_uncertainty(uv.scale(factor))                 # iota(O_RGCS(x))
    right = rscs_scale(iota_uncertainty(uv), factor)          # O_RSCS(iota(x))
    ok = _close(left.value, right.value) and _close(left.u_rel, right.u_rel)
    return {"property": "uncertainty", "ok": ok}


def run_all_cep() -> dict[str, Any]:
    """Run the standard CEP battery over representative v2-domain inputs and
    return a summary. Used by the regression suite and the handoff report."""
    rng = np.random.default_rng(0)
    checks = [
        check_two_mode_cep(1000.0, 1000.0, 10.0),   # golden G-08: 990/1010 Hz
        check_two_mode_cep(1000.0, 1040.0, 7.0),    # detuned
        check_n_mode_cep([1000.0, 1005.0, 1010.0],
                         [[0.0, 3.0, 0.0], [3.0, 0.0, 3.0], [0.0, 3.0, 0.0]]),
        check_analytic_signal_cep(np.sin(np.linspace(0, 20 * np.pi, 512))),
        check_coherence_cep(np.exp(1j * np.linspace(0, 50, 400))),
        check_uncertainty_cep(6310.0, 0.05, 2.0),
    ]
    return {"all_ok": all(c["ok"] for c in checks), "checks": checks}
