"""RSCS propagation operators:
  RSCS-O.6 transfer-matrix cascade (EP-02-02/03, EP-06-03),
  RSCS-O.7 phase-matching predicate (EP-02-01),
  RSCS-O.8 group-delay / dispersion balance (EP-02-03).

O.6 composes 2x2 transfer matrices and exposes the swap-on-reversal signature
that produces nonreciprocity (Chao eq. 10-13). O.7 evaluates the acousto-optic
phase-matching condition k+(w0)+q = k-(w0+Omega) and the mismatch Delta_q. O.8
reports and reduces the group-delay imbalance a coupler must null to widen its
reciprocity-breaking band. All are ADAPTED math; device conclusions excluded.
"""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np

from ..coordinates import GroupDelay
from ..registry import rscs_classified

__all__ = ["cascade", "is_unitary", "reverse_cascade", "phase_match",
           "group_delay_imbalance", "balance_group_delay"]


def _as_2x2(m: np.ndarray) -> np.ndarray:
    arr = np.asarray(m, dtype=complex)
    if arr.shape != (2, 2):
        raise ValueError("each transfer matrix must be 2x2")
    if not np.all(np.isfinite(arr)):
        raise ValueError("transfer matrix must be finite")
    return arr


@rscs_classified("EST", registry=("RSCS-O.6",),
                 provenance=("EP-02-02", "EP-02-03", "EP-06-03"),
                 units="dimensionless",
                 exclusions=("no CMOS-photonic / TMOKE device claims "
                             "(SRC-3-02, SRC-3-06)",),
                 note="ordered product T_n ... T_1 of 2x2 transfer matrices")
def cascade(matrices: Sequence[np.ndarray]) -> np.ndarray:
    """Cascade transfer matrices in propagation order: T = T_n ... T_1."""
    mats = [_as_2x2(m) for m in matrices]
    if not mats:
        raise ValueError("need at least one transfer matrix")
    out = np.eye(2, dtype=complex)
    for m in mats:
        out = m @ out
    return out


@rscs_classified("EST", registry=("RSCS-O.6",), provenance=("EP-06-03",),
                 units="dimensionless",
                 note="unitarity check for a lossless cascade")
def is_unitary(matrix: np.ndarray, atol: float = 1e-9) -> bool:
    """True iff the 2x2 matrix is unitary (lossless): T^dagger T = I."""
    m = _as_2x2(matrix)
    return bool(np.allclose(m.conj().T @ m, np.eye(2), atol=atol))


@rscs_classified("EST", registry=("RSCS-O.6",), provenance=("EP-06-03",),
                 units="dimensionless",
                 note="backward cascade with the even/odd rows swapped, the "
                      "algebraic signature of nonreciprocity (Chao eq.10-13)")
def reverse_cascade(matrices: Sequence[np.ndarray]) -> np.ndarray:
    """Backward-direction cascade: reverse order AND swap the parity rows/cols
    (X T X, X = [[0,1],[1,0]]) -- the nonreciprocal counterpart of cascade()."""
    swap = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
    mats = [swap @ _as_2x2(m) @ swap for m in reversed(matrices)]
    return cascade(mats)


@rscs_classified("EST", registry=("RSCS-O.7",), provenance=("EP-02-01",),
                 units="rad/mm",
                 note="phase-matching: Delta_q = k_plus + q - k_minus; matched "
                      "when |Delta_q| <= tol")
def phase_match(k_plus_rad_mm: float, q_rad_mm: float, k_minus_rad_mm: float,
                tol_rad_mm: float = 1e-9) -> dict[str, Any]:
    """Acousto-optic phase-matching predicate (EP-02-01):
    k+(w0) + q(Omega) = k-(w0+Omega). Returns the mismatch and a matched flag.
    The modulation response is proportional to sinc^2(Delta_q * L / 2)."""
    for name, v in (("k_plus", k_plus_rad_mm), ("q", q_rad_mm),
                    ("k_minus", k_minus_rad_mm)):
        if not np.isfinite(v):
            raise ValueError(f"{name} must be finite")
    if tol_rad_mm < 0:
        raise ValueError("tol must be >= 0")
    delta_q = float(k_plus_rad_mm) + float(q_rad_mm) - float(k_minus_rad_mm)
    return {"delta_q_rad_mm": delta_q, "matched": abs(delta_q) <= tol_rad_mm}


@rscs_classified("DER", registry=("RSCS-O.8",), provenance=("EP-02-03",),
                 units="s", note="max-min per-mode group delay (to be nulled)")
def group_delay_imbalance(tau: GroupDelay) -> float:
    """Group-delay imbalance (s): the quantity balance_group_delay() nulls."""
    if not isinstance(tau, GroupDelay):
        raise TypeError("tau must be a GroupDelay (RSCS-C.11)")
    return tau.imbalance_s


@rscs_classified("DER", registry=("RSCS-O.8",), provenance=("EP-02-03",),
                 units="s -> s",
                 note="subtract a common delay per mode so the mean is zero; "
                      "imbalance is invariant, phases re-reference (EP-02-03)")
def balance_group_delay(tau: GroupDelay) -> GroupDelay:
    """Re-reference group delays to zero mean (dispersion balancing);
    the imbalance is preserved, only the common offset is removed."""
    arr = np.asarray(tau.tau_g_s, dtype=float)
    return GroupDelay(arr - float(np.mean(arr)))
