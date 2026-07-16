"""Quantum-statistical metacrystal reference (Agent M7;
RGCS-V4-EQ-010; material reference.metacrystal).

A transparent, bounded reduced-order coherence-transfer rule: geometry
maps input g2(0) toward a registered allowed band. Explicitly NOT a
microscopic plasmonic simulation and NOT bulk quartz (capability
firewall + tests)."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from ..multiphysics import applicability, get_material, make_result
from ..multiphysics import not_applicable_result

MODULE_ID = "rscs2.refmodels.metacrystal"

#: canonical photon-statistics fixtures (independently constructed;
#: source figure values unavailable locally, DV4C-003)
FIXTURES = {"coherent": 1.0, "thermal": 2.0,
            "subthermal": 1.4, "superthermal": 2.6}


@dataclass(frozen=True)
class MetaAtomGeometry:
    size_nm: float
    count: int
    orientation_deg: float
    arrangement: str            # 'ring' | 'lattice'
    coupling: float             # bounded transfer parameter in [0, 1]

    def __post_init__(self):
        if not (0.0 <= self.coupling <= 1.0):
            raise ValueError("coupling must be in [0, 1]")
        if self.arrangement not in ("ring", "lattice"):
            raise ValueError("arrangement must be ring|lattice")
        if self.size_nm <= 0 or self.count < 1:
            raise ValueError("positive size and count required")

    @property
    def band(self) -> tuple:
        """Registered allowed g2 band for this geometry class
        (transparent reduced rule; declared validity, not physics)."""
        lo = 1.0 - 0.5 * self.coupling
        hi = 2.0 + 1.0 * self.coupling
        return (lo, hi)


def transfer_g2(material_id: str, g2_in: float,
                geometry: MetaAtomGeometry,
                sigma_g2: float = 0.0) -> dict:
    """Bounded transfer map (EQ-010): identity at coupling 0;
    otherwise a sigmoid pull toward the geometry's allowed band.
    Deterministic; uncertainty propagated to first order."""
    if not (g2_in >= 0.0 and math.isfinite(g2_in)):
        raise ValueError("g2 must be finite and >= 0")
    if sigma_g2 < 0:
        raise ValueError("sigma must be >= 0")
    mat = get_material(material_id)
    app = applicability(mat, "quantum_statistical_response")
    if app["applicability"] == "NOT_APPLICABLE":
        return not_applicable_result(MODULE_ID, material_id,
                                     app["reason_code"], app["reason"])
    lo, hi = geometry.band
    c = geometry.coupling
    if c == 0.0:
        g2_out = g2_in                      # identity limit
        deriv = 1.0
    else:
        w = 2.0 * c
        s = 1.0 / (1.0 + math.exp(-w * (g2_in - 1.0)))
        g2_out = (1 - c) * g2_in + c * (lo + (hi - lo) * s)
        ds = w * s * (1 - s)
        deriv = (1 - c) + c * (hi - lo) * ds
    # declared bound: the output lies BETWEEN the input and the band
    # (a partial pull, never an overshoot past the far band edge)
    lo_b = min(g2_in, lo)
    hi_b = max(g2_in, hi)
    assert lo_b - 1e-9 <= g2_out <= hi_b + 1e-9
    return make_result(
        MODULE_ID, material_id, "REDUCED_ORDER_VALIDATED",
        ["DER", "ENG"],
        {"g2_in": g2_in, "g2_out": g2_out,
         "band": [lo, hi],
         "in_band": bool(lo <= g2_out <= hi),
         "pull_bound": "between input and band (partial pull rule)"},
        {"g2": "dimensionless (second-order coherence at zero delay)"},
        uncertainty={"sigma_g2_out": abs(deriv) * sigma_g2},
        source_ids=["SRC-V4-09"], equation_ids=["RGCS-V4-EQ-010"],
        assumptions=["transparent bounded transfer rule (ENG); no "
                     "microscopic plasmonic simulation; separate "
                     "reference system, NOT bulk quartz"])


def inverse_query(material_id: str, g2_target: float,
                  g2_in: float, n_grid: int = 101) -> dict:
    """Geometry candidates achieving g2_target from g2_in: scans the
    coupling axis; returns ALL matches with a nonuniqueness flag."""
    mat = get_material(material_id)
    app = applicability(mat, "quantum_statistical_response")
    if app["applicability"] == "NOT_APPLICABLE":
        return not_applicable_result(MODULE_ID + ".inverse",
                                     material_id, app["reason_code"],
                                     app["reason"])
    cands = []
    for c in np.linspace(0.0, 1.0, n_grid):
        g = MetaAtomGeometry(100.0, 16, 0.0, "ring", float(c))
        out = transfer_g2(material_id, g2_in, g)
        if abs(out["value"]["g2_out"] - g2_target) < 0.02:
            cands.append({"coupling": float(c),
                          "g2_out": out["value"]["g2_out"]})
    return {"candidates": cands,
            "nonunique": len(cands) > 1,
            "note": "inverse design is generally nonunique; every "
                    "match on the scanned axis is reported"}
