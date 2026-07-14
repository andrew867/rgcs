"""rgcs_core.resonance — dimensionless resonance offset, Q-derived
resonance classes, detuning, linewidth, and the signed correction ledger
(RGCS-M.18..M.22, M.26; closes D-06).

Units: frequencies in Hz; epsilon and detunings dimensionless (signed);
linewidths in Hz (FWHM convention, stated per D-19c).

Sign convention of the offset is identical to LT Eq. (13) (LT-15,
Lee & Tsai 2026), substitution map m -> f; LT's invisible/visible
interpretation has NO RGCS analogue. Resonance classes derive from
measured quality factors via eps_Q = 1/Q_eff (RGCS-M.20), replacing the
retired borrowed 1e-4/0.01/0.1 bins. eps = 1.25 is retained only as the
convention for a deliberately non-resonant control configuration (LT-20).
"""

from __future__ import annotations

import math
from typing import Any

from ..provenance import classified, classification_string

__all__ = ["resonance_offset", "linear_detuning", "linewidth_fwhm_hz",
           "effective_q", "epsilon_q", "classify_resonance",
           "sweep_span_hz", "corrected_resonance_offset",
           "NONRESONANT_CONTROL_EPSILON"]

#: Convention for a deliberately non-resonant control configuration
#: (Source-claim context, LT-20; never a physics threshold).
NONRESONANT_CONTROL_EPSILON = 1.25


def _positive(name: str, v: float) -> None:
    if not (math.isfinite(v) and v > 0):
        raise ValueError(f"{name} must be positive and finite; got {v!r}")


@classified("Derived", registry=("RGCS-M.18",), sources=("RG-06", "LT-15"),
            note="definition Derived (sign convention = LT Eq. (13)); "
                 "enhancement near zero is Hypothesis H-02")
def resonance_offset(f_m_hz: float, f_x_hz: float,
                     pair_multiple: float = 2.0) -> float:
    """Signed dimensionless resonance offset (RGCS-M.18):
    eps_R^(f) = [f_m^2 - (p f_x)^2] / (p f_x)^2. Golden:
    eps(40960, 20480, p=2) = 0 exactly (G-07)."""
    _positive("f_m_hz", f_m_hz)
    _positive("f_x_hz", f_x_hz)
    _positive("pair_multiple", pair_multiple)
    ref = pair_multiple * f_x_hz
    return (f_m_hz ** 2 - ref ** 2) / ref ** 2


@classified("Established", registry=("RGCS-M.19",))
def linear_detuning(f_m_hz: float, f_x_hz: float,
                    pair_multiple: float = 2.0) -> float:
    """Linear fractional detuning d_lin = f_m/(p f_x) - 1 (RGCS-M.19);
    eps_R^(f) = (1 + d_lin)^2 - 1."""
    _positive("f_m_hz", f_m_hz)
    _positive("f_x_hz", f_x_hz)
    _positive("pair_multiple", pair_multiple)
    return f_m_hz / (pair_multiple * f_x_hz) - 1.0


@classified("Established", registry=("RGCS-M.26",),
            note="FWHM convention, stated (D-19c)")
def linewidth_fwhm_hz(f_hz: float, q: float) -> float:
    """FWHM linewidth Gamma = f/Q (RGCS-M.26)."""
    _positive("f_hz", f_hz)
    _positive("q", q)
    return f_hz / q


@classified("Derived", note="harmonic-mean effective Q; declared modeling "
                            "choice (D-19d)")
def effective_q(q_a: float, q_b: float) -> float:
    """Harmonic-mean effective quality factor Q_eff = 2/(1/Q_a + 1/Q_b)."""
    _positive("q_a", q_a)
    _positive("q_b", q_b)
    return 2.0 / (1.0 / q_a + 1.0 / q_b)


@classified("Derived", registry=("RGCS-M.20",),
            note="Q-derived epsilon scale; replaces retired borrowed bins "
                 "(D-06)")
def epsilon_q(q_m: float, q_x: float) -> float:
    """Q-derived epsilon scale eps_Q = 1/Q_eff (RGCS-M.20)."""
    return 1.0 / effective_q(q_m, q_x)


@classified("Derived", registry=("RGCS-M.20",),
            note="engineering heuristic - not evidence; a class string "
                 "without u(eps_R) is non-compliant (policy 3.4)")
def classify_resonance(eps: float, q_m: float, q_x: float,
                       u_eps: float) -> dict[str, Any]:
    """Q-derived resonance classes (RGCS-M.20):
    WITHIN_LINEWIDTH |eps| <= eps_Q; NEAR <= 5 eps_Q; MODERATE <= 50 eps_Q;
    FAR otherwise. u_eps is REQUIRED: a resonance-class string without its
    uncertainty is non-compliant (policy section 3.4)."""
    if not math.isfinite(eps):
        raise ValueError("eps must be finite")
    if not (math.isfinite(u_eps) and u_eps >= 0):
        raise ValueError("u_eps must be >= 0 and finite (mandatory)")
    eq = epsilon_q(q_m, q_x)
    mag = abs(eps)
    if mag <= eq:
        cls = "WITHIN_LINEWIDTH"
    elif mag <= 5.0 * eq:
        cls = "NEAR"
    elif mag <= 50.0 * eq:
        cls = "MODERATE"
    else:
        cls = "FAR"
    return {"epsilon": eps, "u_epsilon": u_eps, "epsilon_q": eq,
            "resonance_class": cls,
            "class_uncertain": u_eps > 0 and (mag - u_eps <= eq <= mag + u_eps
                                              or mag - u_eps <= 5 * eq
                                              <= mag + u_eps
                                              or mag - u_eps <= 50 * eq
                                              <= mag + u_eps),
            "note": "engineering heuristic - not evidence",
            "classification": classification_string(classify_resonance)}


@classified("Derived", registry=("RGCS-M.21",),
            note="engineering heuristic - not evidence; 6-linewidth floor "
                 "resolves the lineshape at small detuning")
def sweep_span_hz(f_m_hz: float, f_x_hz: float, q_m: float, q_x: float,
                  pair_multiple: float = 2.0) -> float:
    """Sweep-span heuristic (RGCS-M.21):
    span = max(10 Hz, 4 |f_m - p f_x|, 6 max(Gamma_m, Gamma_x))."""
    gm = linewidth_fwhm_hz(f_m_hz, q_m)
    gx = linewidth_fwhm_hz(f_x_hz, q_x)
    return max(10.0, 4.0 * abs(f_m_hz - pair_multiple * f_x_hz),
               6.0 * max(gm, gx))


@classified("Derived", registry=("RGCS-M.22", "RGCS-M.45"),
            sources=("LT-13", "LT-14", "LT-15"),
            note="corrections are SIGNED and can move eps through zero "
                 "(LT-Delta2); additive ledger is first-order only (A-10)")
def corrected_resonance_offset(f_m0_hz: float, f_x0_hz: float,
                               deltas_m: dict[str, float] | None = None,
                               deltas_x: dict[str, float] | None = None,
                               u_f_m_hz: float = 0.0, u_f_x_hz: float = 0.0,
                               pair_multiple: float = 2.0) -> dict[str, Any]:
    """Corrected, uncertainty-carrying resonance offset (RGCS-M.22):
    f_corr = f_0 (1 + sum_k delta_k) with SIGNED delta_k, then eps of the
    corrected pair, with first-order u(eps_R). Warns when |sum delta| > 0.02
    (assumption A-10: additive form is first-order only)."""
    _positive("f_m0_hz", f_m0_hz)
    _positive("f_x0_hz", f_x0_hz)
    if u_f_m_hz < 0 or u_f_x_hz < 0:
        raise ValueError("frequency uncertainties must be >= 0")
    dm = deltas_m or {}
    dx = deltas_x or {}
    sum_m, sum_x = sum(dm.values()), sum(dx.values())
    f_m = f_m0_hz * (1.0 + sum_m)
    f_x = f_x0_hz * (1.0 + sum_x)
    _positive("corrected f_m", f_m)
    _positive("corrected f_x", f_x)
    eps = resonance_offset(f_m, f_x, pair_multiple)
    ref = pair_multiple * f_x
    # Exact first-order propagation of eps = f_m^2/ref^2 - 1.
    d_eps_dfm = 2.0 * f_m / ref ** 2
    d_eps_dfx = -2.0 * f_m ** 2 / (pair_multiple ** 2 * f_x ** 3)
    u_eps = math.hypot(d_eps_dfm * u_f_m_hz, d_eps_dfx * u_f_x_hz)
    return {
        "f_m_corrected_hz": f_m,
        "f_x_corrected_hz": f_x,
        "delta_sum_m": sum_m,
        "delta_sum_x": sum_x,
        "epsilon_corrected": eps,
        "u_epsilon": u_eps,
        "linear_detuning": linear_detuning(f_m, f_x, pair_multiple),
        "first_order_valid": max(abs(sum_m), abs(sum_x)) <= 0.02,
        "classification":
            classification_string(corrected_resonance_offset),
    }
