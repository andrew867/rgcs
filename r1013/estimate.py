"""R10.13 Phase 13 — quick estimate engine.

Quarter-wave, half-wave, and declared closed-path screening estimates.
Every output states formula, path, speed, harmonic, boundary
assumption, uncertainty, and evidence class. These are screening
tools: no taper, terminations, anisotropy detail, or fixture.

The axial speed defaults to the frozen v2 longitudinal reference
v_L = 6310 m/s (RGCS-M.10); with a known orientation the exact
Christoffel qL speed along the body axis is used instead and the
choice is recorded.
"""

from __future__ import annotations

import math

from r1013.errors import UserError
from r1013.specimen import require_valid

#: Frozen v2 default longitudinal speed along the c-axis (m/s).
V_L_DEFAULT_M_S = 6310.0

MODELS = ("axial-quarter", "axial-half", "closed-path")


def _axial_speed(rec: dict) -> tuple[float, str]:
    ori = rec.get("orientation") or {}
    if ori.get("status") in ("known", "estimated") and \
            ori.get("euler_zxz_deg") is not None:
        from r1013.christoffel_api import body_axis_speed
        v = body_axis_speed(tuple(ori["euler_zxz_deg"]))
        return v, ("Christoffel qL speed along the body axis for the "
                   f"recorded orientation ({v:.1f} m/s)")
    return V_L_DEFAULT_M_S, ("frozen v2 default longitudinal speed "
                             "6310 m/s (orientation not measured)")


def quick_estimate(rec: dict, models=("axial-quarter", "axial-half"),
                   harmonics: int = 3) -> dict:
    """Screening estimates for a specimen record."""
    require_valid(rec)
    L_mm = rec["geometry"].get("length_mm")
    if not isinstance(L_mm, (int, float)) or L_mm <= 0:
        raise UserError("RGCS-E008", "A quick estimate needs "
                        "geometry.length_mm.")
    for m in models:
        if m not in MODELS:
            raise UserError("RGCS-E006",
                            f"'{m}' is not an estimate model. Choose "
                            f"from: {', '.join(MODELS)}.")
    L = L_mm / 1000.0
    v, speed_basis = _axial_speed(rec)
    unc = rec.get("measurements", {}) or {}
    dL = unc.get("length_uncertainty_mm")
    rel_L = (dL / L_mm) if isinstance(dL, (int, float)) else 0.01
    # declared screening-model uncertainty: geometry idealization
    # dominates; +-10 percent envelope plus measured length error
    rel_total = math.hypot(0.10, rel_L)

    results = []
    for model in models:
        for n in range(1, harmonics + 1):
            if model == "axial-quarter":
                f = (2 * n - 1) * v / (4 * L)
                formula = "f_n = (2n-1) v / (4 L_eff)"
                boundary = "one end effectively fixed, one free"
            elif model == "axial-half":
                f = n * v / (2 * L)
                formula = "f_n = n v / (2 L_eff)"
                boundary = "both ends alike (free-free or fixed-fixed)"
            else:                        # closed-path
                f = n * v / (2 * L)
                formula = ("f_n = n v / P with declared closed path "
                           "P = 2 L (out and back)")
                boundary = "declared closed axial path"
            results.append({
                "model": model, "harmonic": n,
                "frequency_hz": f,
                "uncertainty_hz": f * rel_total,
                "formula": formula,
                "path_m": (2 * L) if model != "axial-quarter" else 4 * L,
                "path_note": "L_eff = recorded length; taper and "
                             "terminations not included",
                "speed_m_s": v, "speed_basis": speed_basis,
                "boundary_assumption": boundary,
                "evidence_class": "ESTIMATE",
            })
    return {"specimen_id": rec["specimen_id"],
            "length_mm": L_mm, "speed_m_s": v,
            "relative_uncertainty": rel_total,
            "estimates": results,
            "evidence_class": "ESTIMATE",
            "note": "screening estimates only; a computed frequency "
                    "is not a measured resonance"}
