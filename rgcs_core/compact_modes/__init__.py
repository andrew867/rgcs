"""rgcs_core.compact_modes — compact phase-coordinate mode spectrum,
parity families, and the identifiable spectral slope
(RGCS-M.13..M.17; adapted from LT Eqs. (9)-(10) and Table I with the
substitution map m -> f, m_B -> f_b, 1/R -> v_chi/(2 pi R_chi); LT-08/09,
Lee & Tsai 2026).

Units: frequencies in Hz, R_chi in mm (converted mm -> m exactly once,
inside kappa_chi), speeds in m/s. The compact coordinate chi is a closed
wave path — a modeling construct, NOT a spatial extra dimension.

Identifiability (RGCS-M.14): only kappa_chi = v_chi/(2 pi R_chi) enters
the spectrum; v_chi and R_chi are NOT separately identifiable from mode
spacing alone. Fits report kappa_chi.
"""

from __future__ import annotations

import math
from typing import Any, Literal

from ..provenance import classified, classification_string
from ..uncertainty import UncertainValue, default_wave_speed

__all__ = ["Parity", "parity_index_set", "kappa_chi_hz",
           "compact_mode_spectrum"]

Parity = Literal["odd", "even", "all"]


@classified("Established", registry=("RGCS-M.16", "RGCS-M.17"),
            sources=("LT-02", "LT-03", "LT-04"),
            note="index-set definitions Established; physical relevance is "
                 "Hypothesis H-03. Odd family NEVER contains n = 0; the "
                 "even family's n = 0 is controlled by include_zero_mode "
                 "(False reproduces the strict LT zero-flux template)")
def parity_index_set(parity: Parity, n_max: int,
                     include_zero_mode: bool = True) -> list[int]:
    """Mode index sets per parity family (RGCS-M.16/M.17):
    odd  (P-): {1, 3, 5, ...}   — antisymmetric, sin(n chi/2); no n = 0.
    even (P+): {0, 2, 4, ...}   — symmetric, cos(n chi/2); n = 0 present
    only when include_zero_mode is True.
    all: union of both."""
    if n_max < 0:
        raise ValueError("n_max must be >= 0")
    if parity == "odd":
        return list(range(1, n_max + 1, 2))
    if parity == "even":
        start = 0 if include_zero_mode else 2
        return list(range(start, n_max + 1, 2))
    if parity == "all":
        return sorted(set(parity_index_set("odd", n_max))
                      | set(parity_index_set("even", n_max,
                                             include_zero_mode)))
    raise ValueError(f"unknown parity {parity!r}; expected odd/even/all")


@classified("Derived", registry=("RGCS-M.14",),
            note="the ONLY combination identifiable from mode spacing alone; "
                 "report kappa_chi, never (v_chi, R_chi) separately")
def kappa_chi_hz(v_chi: UncertainValue | float | None = None,
                 compact_radius_mm: float = 100.0) -> UncertainValue:
    """Compact spectral slope kappa_chi = v_chi/(2 pi R_chi) in Hz
    (RGCS-M.14). R_chi is converted mm -> m exactly once here.
    NOTE (D-21): the 100 mm default is an arbitrary placeholder, unrelated
    to the spiral-derived priors of rgcs_core.geometry.spiral."""
    if not (math.isfinite(compact_radius_mm) and compact_radius_mm > 0):
        raise ValueError("compact_radius_mm must be positive")
    if v_chi is None:
        v = default_wave_speed()
    elif isinstance(v_chi, UncertainValue):
        v = v_chi
    else:
        v = UncertainValue(float(v_chi), 0.0)
    if v.mean <= 0:
        raise ValueError("v_chi must be positive")
    radius_m = compact_radius_mm / 1000.0    # the single mm -> m conversion
    return UncertainValue(v.mean / (2.0 * math.pi * radius_m), v.u_rel)


@classified("Hypothesis", registry=("RGCS-M.13", "RGCS-M.15", "RGCS-M.16",
                                    "RGCS-M.17"),
            sources=("RG-05", "LT-08", "LT-09"),
            note="H-01: adapted from LT Eqs. (9)-(10) as mathematical "
                 "template only (substitution m -> f, 1/R -> v_chi/(2 pi "
                 "R_chi)); must beat simpler modal models on held-out modes "
                 "(RG-19). No dark-sector physics is analogized.")
def compact_mode_spectrum(base_frequency_hz: float = 0.0,
                          kappa: UncertainValue | None = None,
                          v_chi: UncertainValue | float | None = None,
                          compact_radius_mm: float | None = None,
                          n_max: int = 12,
                          parity: Parity = "all",
                          include_zero_mode: bool = True,
                          u_base_frequency_hz: float = 0.0
                          ) -> dict[str, Any]:
    """Compact-coordinate spectrum f_n^2 = f_b^2 + (n kappa_chi)^2
    (RGCS-M.13) with first-order uncertainty propagation (RGCS-M.15).

    Provide EITHER ``kappa`` (preferred: the identifiable parameter,
    RGCS-M.14) OR the pair (``v_chi``, ``compact_radius_mm``), from which
    kappa_chi is computed; the output always reports kappa_chi.

    Zero-mode rule (RGCS-M.17): the odd family never contains n = 0; the
    even family lists n = 0 (f = f_b) only when ``include_zero_mode`` is
    True AND f_b > 0; when f_b = 0 the n = 0 member is excluded
    unconditionally (a DC/rigid-body pattern, not a vibratory mode).

    Golden: n = 1, f_b = 0, v = 6310 m/s, R_chi = 100 mm ->
    10042.6769091 Hz (G-06)."""
    if base_frequency_hz < 0 or not math.isfinite(base_frequency_hz):
        raise ValueError("base_frequency_hz must be >= 0 and finite")
    if u_base_frequency_hz < 0:
        raise ValueError("u_base_frequency_hz must be >= 0")
    if n_max < 1:
        raise ValueError("n_max must be >= 1")
    if kappa is not None and (v_chi is not None
                              or compact_radius_mm is not None):
        raise ValueError("provide kappa OR (v_chi, compact_radius_mm), "
                         "not both (RGCS-M.14 identifiability)")
    if kappa is None:
        kappa = kappa_chi_hz(v_chi, 100.0 if compact_radius_mm is None
                             else compact_radius_mm)
    fb = base_frequency_hz
    indices = parity_index_set(parity, n_max, include_zero_mode)
    if fb == 0.0:
        indices = [n for n in indices if n != 0]   # RGCS-M.17 rule 3

    rows: list[dict[str, Any]] = []
    for n in indices:
        compact_term = n * kappa.mean
        f_n = math.hypot(fb, compact_term)
        if f_n > 0.0:
            # RGCS-M.15 first-order propagation.
            u_f = math.sqrt((fb / f_n) ** 2 * u_base_frequency_hz ** 2
                            + (compact_term / f_n) ** 2
                            * (compact_term * kappa.u_rel) ** 2)
            u_rel = u_f / f_n
        else:
            u_rel = 0.0
        rows.append({
            "n": n,
            "parity": "even" if n % 2 == 0 else "odd",
            "compact_term_hz": compact_term,
            "frequency": UncertainValue(f_n, u_rel).to_dict(),
        })
    return {
        "base_frequency_hz": fb,
        "kappa_chi_hz": kappa.to_dict(),
        "parity": parity,
        "include_zero_mode": include_zero_mode,
        "zero_mode_present": any(r["n"] == 0 for r in rows),
        "modes": rows,
        "identifiability_note": "only kappa_chi is identifiable from mode "
                                "spacing (RGCS-M.14); R_chi quoted only "
                                "when v_chi is independently fixed",
        "classification": classification_string(compact_mode_spectrum),
    }
