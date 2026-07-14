"""rgcs_core.loading — mass/stiffness/damping corrections
(RGCS-M.42..M.45; closes D-10).

Units: frequencies in Hz, lengths in mm, masses in g; correction terms
delta_k dimensionless (signed).

k_H (measured frequency ratio, RGCS-M.42) and k~_H (length-shortfall
proxy, RGCS-M.44) are DISTINCT quantities with distinct functions; the
proxy equals the loading factor only under Hypothesis H-08b.
"""

from __future__ import annotations

import math
from typing import Any

from ..provenance import classified, classification_string

__all__ = ["loading_factor", "added_modal_mass_g", "length_shortfall_ratio",
           "loading_from_length", "apply_correction_ledger"]


def _positive(name: str, v: float) -> None:
    if not (math.isfinite(v) and v > 0):
        raise ValueError(f"{name} must be positive and finite; got {v!r}")


@classified("Established", registry=("RGCS-M.42",), sources=("RG-10",),
            note="a measured ratio")
def loading_factor(f_loaded_hz: float, f_free_hz: float) -> float:
    """Loading factor k_H = f_loaded / f_free (RGCS-M.42, measured)."""
    _positive("f_loaded_hz", f_loaded_hz)
    _positive("f_free_hz", f_free_hz)
    return f_loaded_hz / f_free_hz


@classified("Derived", registry=("RGCS-M.43",), sources=("RG-10",),
            note="Established SDOF algebra CONDITIONED on Hypothesis H-08 "
                 "(loading is pure added modal mass with fraction eta; "
                 "eta = 0.5 is asserted, unmeasured); (eta, dM) degenerate "
                 "in a single loading measurement")
def added_modal_mass_g(k_h: float, crystal_mass_g: float,
                       modal_mass_fraction: float = 0.5) -> dict[str, Any]:
    """First-order added modal mass (RGCS-M.43):
    dM_H = M_eff (1/k_H^2 - 1), M_eff = eta m. Golden: k_H = 0.9866751189,
    m = 154 g, eta = 0.5 -> dM_H = 2.0937873 g (G-09)."""
    _positive("k_h", k_h)
    _positive("crystal_mass_g", crystal_mass_g)
    if not (0.0 < modal_mass_fraction <= 1.0):
        raise ValueError("modal_mass_fraction must lie in (0, 1]")
    m_eff = modal_mass_fraction * crystal_mass_g
    dm = m_eff * (1.0 / (k_h * k_h) - 1.0)
    return {
        "loading_factor_k_h": k_h,
        "effective_modal_mass_g": m_eff,
        "added_modal_mass_g": dm,
        "conditioning": "Hypothesis H-08: pure added modal mass, "
                        f"eta = {modal_mass_fraction} asserted",
        "classification": classification_string(added_modal_mass_g),
    }


@classified("Hypothesis", registry=("RGCS-M.44",), sources=("RG-10",),
            note="H-08b: length-shortfall proxy k~_H, NOT the same quantity "
                 "as k_H (closes D-10); equals k_H only if f ~ 1/L exactly "
                 "and loading targets the design frequency")
def length_shortfall_ratio(actual_length_mm: float,
                           target_length_mm: float) -> float:
    """Length-shortfall proxy k~_H = L_actual / L_target (RGCS-M.44).
    A DISTINCT symbol and function from the measured loading factor k_H."""
    _positive("actual_length_mm", actual_length_mm)
    _positive("target_length_mm", target_length_mm)
    return actual_length_mm / target_length_mm


@classified("Hypothesis", registry=("RGCS-M.43", "RGCS-M.44"),
            sources=("RG-10",),
            note="k~_H route; every output states the conditioning")
def loading_from_length(actual_length_mm: float, target_length_mm: float,
                        crystal_mass_g: float,
                        modal_mass_fraction: float = 0.5) -> dict[str, Any]:
    """Loading estimate via the length-shortfall proxy (RGCS-M.44 feeding
    RGCS-M.43). The result is CONDITIONED on Hypotheses H-08 and H-08b;
    the compatibility string states the conditioning explicitly."""
    k_tilde = length_shortfall_ratio(actual_length_mm, target_length_mm)
    mass = added_modal_mass_g(k_tilde, crystal_mass_g, modal_mass_fraction)
    compatible = (
        "compatible IF H-08b holds (f ~ 1/L exactly and loading targets "
        "the design frequency)" if k_tilde <= 1.0 else
        "requires stiffness/mode correction; k~_H > 1 is outside the "
        "added-mass picture (H-08/H-08b conditioning)")
    return {
        "length_shortfall_ratio_k_tilde_h": k_tilde,
        "proxy_note": "k~_H is a length ratio, NOT the measured loading "
                      "factor k_H (RGCS-M.42 vs M.44, D-10)",
        "effective_modal_mass_g": mass["effective_modal_mass_g"],
        "added_modal_mass_g": mass["added_modal_mass_g"],
        "length_correction_fraction": k_tilde - 1.0,
        "mass_loading_compatible": compatible,
        "classification": classification_string(loading_from_length),
    }


@classified("Derived", registry=("RGCS-M.45",), sources=("LT-13", "LT-14"),
            note="signed correction ledger; corrections can flip eps_R "
                 "through zero (LT-Delta2); additive form first-order only "
                 "(A-10)")
def apply_correction_ledger(f_predicted_hz: float,
                            deltas: dict[str, float],
                            u_deltas: dict[str, float] | None = None
                            ) -> dict[str, Any]:
    """Signed correction ledger (RGCS-M.45):
    f = f_pred (1 + sum_k delta_k), delta_k in {geometry, anisotropy,
    loading, T, fixture, drive} (extra keys allowed, all signed). Each
    delta_k may carry its own uncertainty u(delta_k); the ledger reports
    the combined u(f). Warns when |sum delta| > 0.02 (A-10)."""
    _positive("f_predicted_hz", f_predicted_hz)
    if not deltas:
        raise ValueError("deltas must contain at least one signed term")
    for k, v in deltas.items():
        if not math.isfinite(v):
            raise ValueError(f"delta {k!r} must be finite")
    u = u_deltas or {}
    total = sum(deltas.values())
    u_total = math.sqrt(sum(uv * uv for uv in u.values()))
    return {
        "f_predicted_hz": f_predicted_hz,
        "deltas": dict(deltas),
        "delta_sum": total,
        "f_corrected_hz": f_predicted_hz * (1.0 + total),
        "u_f_corrected_hz": f_predicted_hz * u_total,
        "first_order_valid": abs(total) <= 0.02,
        "note": "supersede with nonlinear/Bayesian treatment when "
                "|sum delta| > 0.02 (A-10)",
        "classification": classification_string(apply_correction_ledger),
    }
