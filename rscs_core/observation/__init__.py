"""RSCS-O.10 observation / projection operator.

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
           "nonreciprocal_contrast_db"]


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
