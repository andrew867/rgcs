"""RSCS observation operators: O.10 (coherence + dB metrics),
O.20 Autler-Townes split lineshape, O.21 critical coupling (Agent 06).

Maps a modal/time-series state to observables: coherence (delegating to the
frozen v2 RGCS-M.56 autocorrelation coherence) and log-ratio isolation /
insertion-loss metrics (EP-01-03, EP-04-03, EP-05-02). The coherence path is a
thin wrapper over v2 so the Conservative Extension Property is exact; the dB
metrics are standard definitions with the source-domain performance claims
excluded.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from rgcs_core.coherence.metrics import coherence_window as _v2_coherence_window

from ..registry import rscs_classified

__all__ = ["coherence", "insertion_loss_db", "isolation_db",
           "nonreciprocal_contrast_db", "autler_townes_response",
           "is_strong_coupling", "critical_coupling_transmission",
           "is_critically_coupled"]


@rscs_classified("EST", registry=("RSCS-O.10",), provenance=("EP-05-02",),
                 units="dimensionless [0, ~1]",
                 note="autocorrelation coherence; delegates to frozen v2 "
                      "RGCS-M.56 coherence_window (byte-identical)")
def coherence(segment: np.ndarray) -> float:
    """Normalized autocorrelation coherence of one complex window.
    Thin RSCS wrapper over the frozen v2 RGCS-M.56 implementation."""
    return _v2_coherence_window(segment)


def _require_transmission(name: str, t: float) -> float:
    if not (isinstance(t, (int, float)) and math.isfinite(t) and t > 0):
        raise ValueError(f"{name} must be a positive finite transmission")
    return float(t)


@rscs_classified("EST", registry=("RSCS-O.10",), provenance=("EP-05-02",),
                 units="dB",
                 exclusions=("no device IL performance import (SRC-3-05)",),
                 note="insertion loss IL = -10 log10(T_forward)")
def insertion_loss_db(t_forward: float) -> float:
    """Insertion loss (dB) from a forward power transmission: -10 log10(T)."""
    return -10.0 * math.log10(_require_transmission("t_forward", t_forward))


@rscs_classified("EST", registry=("RSCS-O.10",),
                 provenance=("EP-04-03", "EP-05-02"), units="dB",
                 exclusions=("no device isolation import (SRC-3-04, SRC-3-05)",),
                 note="isolation = -10 log10(T_backward)")
def isolation_db(t_backward: float) -> float:
    """Isolation (dB) from a backward power transmission: -10 log10(T)."""
    return -10.0 * math.log10(_require_transmission("t_backward", t_backward))


@rscs_classified("EST", registry=("RSCS-O.10",), provenance=("EP-04-03",),
                 units="dB",
                 note="directional contrast = 10 log10(T_forward / T_backward)")
def nonreciprocal_contrast_db(t_forward: float, t_backward: float) -> float:
    """Directional contrast (dB): 10 log10(T_forward / T_backward)."""
    tf = _require_transmission("t_forward", t_forward)
    tb = _require_transmission("t_backward", t_backward)
    return 10.0 * math.log10(tf / tb)


# --- Agent 06: Autler-Townes split lineshape (RSCS-O.20) ---

def _require_positive(name: str, v: float) -> float:
    if not (isinstance(v, (int, float)) and math.isfinite(v) and v > 0):
        raise ValueError(f"{name} must be positive and finite")
    return float(v)


@rscs_classified("EST", registry=("RSCS-O.20",), provenance=("EP-01-02",),
                 units="dimensionless (normalized |response|^2)",
                 exclusions=("no acousto-optic ATS device physics import "
                             "(SRC-3-01); this is the two-Lorentzian "
                             "lineshape algebra only",),
                 note="two-Lorentzian dressed response, peaks split by G "
                      "(EP-01-02 eq. S4); parallels the RGCS-M.24 2g split")
def autler_townes_response(detuning_rad_s: np.ndarray | float,
                           kappa_rad_s: float,
                           g_split_rad_s: float) -> np.ndarray:
    """Autler-Townes (dressed-state) magnitude-squared response:

        |chi(D)|^2, chi = 1/2 [ 1/(k/2 - i(D + G/2)) + 1/(k/2 - i(D - G/2)) ]

    (EP-01-02 eq. S4, matched-loss degenerate limit). For G >> kappa the
    response has two peaks separated by G. In the RGCS mapping the dressed
    splitting G corresponds to the 2g hybrid-frequency splitting of the
    frozen coupled-mode model (RGCS-M.24): G = 2*pi*(2g) rad/s."""
    kappa = _require_positive("kappa_rad_s", kappa_rad_s)
    if not (isinstance(g_split_rad_s, (int, float))
            and math.isfinite(g_split_rad_s) and g_split_rad_s >= 0):
        raise ValueError("g_split_rad_s must be finite and >= 0")
    d = np.asarray(detuning_rad_s, dtype=float)
    if not np.all(np.isfinite(d)):
        raise ValueError("detuning must be finite")
    half_g = float(g_split_rad_s) / 2.0
    chi = 0.5 * (1.0 / (kappa / 2.0 - 1j * (d + half_g))
                 + 1.0 / (kappa / 2.0 - 1j * (d - half_g)))
    return np.abs(chi) ** 2


@rscs_classified("EST", registry=("RSCS-O.20",), provenance=("EP-01-02",),
                 units="dimensionless (predicate)",
                 note="strong-coupling threshold G > sqrt(kappa1*kappa2) "
                      "(EP-01-02 main text); parallels RGCS-M.27 R_g")
def is_strong_coupling(g_split_rad_s: float, kappa1_rad_s: float,
                       kappa2_rad_s: float) -> bool:
    """True iff the splitting exceeds the loss geometric mean:
    G > sqrt(kappa1 * kappa2) -- the resolvable-splitting threshold."""
    k1 = _require_positive("kappa1_rad_s", kappa1_rad_s)
    k2 = _require_positive("kappa2_rad_s", kappa2_rad_s)
    if not (isinstance(g_split_rad_s, (int, float))
            and math.isfinite(g_split_rad_s) and g_split_rad_s >= 0):
        raise ValueError("g_split_rad_s must be finite and >= 0")
    return float(g_split_rad_s) > math.sqrt(k1 * k2)


# --- Agent 06: critical coupling (RSCS-O.21) ---

@rscs_classified("EST", registry=("RSCS-O.21",), provenance=("EP-01-03",),
                 units="dimensionless (power transmission in [0, 1])",
                 exclusions=("no device insertion-loss/contrast import "
                             "(SRC-3-01)",),
                 note="t = 1 - kex/(k_tot/2 - iD), k_tot = k_int + k_ex; "
                      "T(0) = 0 iff k_int = k_ex (EP-01-03 eq. S6)")
def critical_coupling_transmission(kappa_int_rad_s: float,
                                   kappa_ext_rad_s: float,
                                   detuning_rad_s: float = 0.0) -> float:
    """Power transmission past a side-coupled resonator:

        T(D) = |1 - kappa_ext / ((kappa_int + kappa_ext)/2 - i D)|^2.

    At resonance (D = 0) this vanishes exactly when kappa_int = kappa_ext:
    the critical-coupling condition (intrinsic loss = external coupling)."""
    ki = _require_positive("kappa_int_rad_s", kappa_int_rad_s)
    ke = _require_positive("kappa_ext_rad_s", kappa_ext_rad_s)
    if not (isinstance(detuning_rad_s, (int, float))
            and math.isfinite(detuning_rad_s)):
        raise ValueError("detuning_rad_s must be finite")
    t_amp = 1.0 - ke / ((ki + ke) / 2.0 - 1j * float(detuning_rad_s))
    return float(abs(t_amp) ** 2)


@rscs_classified("EST", registry=("RSCS-O.21",), provenance=("EP-01-03",),
                 units="dimensionless (predicate)",
                 note="critical coupling: kappa_int == kappa_ext within rtol")
def is_critically_coupled(kappa_int_rad_s: float, kappa_ext_rad_s: float,
                          rtol: float = 1e-6) -> bool:
    """True iff intrinsic loss equals external coupling within rtol."""
    ki = _require_positive("kappa_int_rad_s", kappa_int_rad_s)
    ke = _require_positive("kappa_ext_rad_s", kappa_ext_rad_s)
    return bool(math.isclose(ki, ke, rel_tol=rtol))
