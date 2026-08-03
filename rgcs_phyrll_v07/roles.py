"""Coefficient Role Registry, v0.7.

Four lanes, five role classes, and one rule that everything else hangs
off: **only lane D (PHYSICAL_MEASUREMENT) may make a physical-performance
claim, and only when a measured value with an uncertainty exists.**

The headline correction is encoded here rather than prosed:

    SOURCE DISPLAY            67.3 N/W            (a rounded human figure)
    EXACT RECOVERED CALC      64672/961 N/W       (the arithmetic)
    RELATION                  rounds to the same one-decimal value
    NOT                       exact equality
    EXACT GAP                 673/10 - 64672/961 = 33/9610
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from fractions import Fraction as F

from . import ROLE_CLASSES

#: Lane grammar from the v0.7 correction.
LANES = {
    "A": "SOURCE_COEFFICIENTS",
    "B": "EXACT_CALCULATION_COEFFICIENTS",
    "C": "DESIGN_GEOMETRY_COEFFICIENTS",
    "D": "PHYSICAL_MEASUREMENT_COEFFICIENTS",
}


@dataclass(frozen=True)
class Coefficient:
    name: str
    lane: str                      # A / B / C / D
    role: str                      # one of ROLE_CLASSES
    exact: object = None           # Fraction where one exists
    decimal: float | None = None
    measured_value: float | None = None
    uncertainty: float | None = None
    note: str = ""
    relations: tuple = field(default_factory=tuple)

    def __post_init__(self):
        if self.role not in ROLE_CLASSES:
            raise ValueError(f"unknown role class {self.role!r}")
        if self.lane not in LANES:
            raise ValueError(f"unknown lane {self.lane!r}")

    @property
    def may_claim_performance(self) -> bool:
        """The gate. Everything outside lane D is arithmetic or design."""
        return (self.lane == "D" and self.role == "PHYSICAL_MEASUREMENT"
                and self.measured_value is not None
                and self.uncertainty is not None)

    def as_row(self) -> dict:
        return {"name": self.name, "lane": self.lane,
                "lane_meaning": LANES[self.lane], "role": self.role,
                "exact": None if self.exact is None else str(self.exact),
                "decimal": (self.decimal if self.decimal is not None
                            else (float(self.exact)
                                  if self.exact is not None else None)),
                "measured_value": self.measured_value,
                "uncertainty": self.uncertainty,
                "may_claim_performance": self.may_claim_performance,
                "note": self.note, "relations": list(self.relations)}


#: The mandated split, plus the exact gap as a first-class entry.
ETA_GAP = F(673, 10) - F(64672, 961)          # == 33/9610, asserted in tests

REGISTRY = (
    # ---- lane A: source numbers as supplied ----
    Coefficient("eta_F_display", "A", "SOURCE_DISPLAY", F(673, 10),
                note="67.3 N/W as written in the notes; a rounded "
                     "human-readable figure, NOT an identity",
                relations=("rounds_to_same_1dp_as:eta_F_exact_candidate",)),
    Coefficient("sigma_source", "A", "SOURCE_DISPLAY", F(47, 63)),
    Coefficient("q_source_spelling", "A", "SOURCE_DISPLAY", F(27, 93),
                note="source spelling; reduces to 9/31 in lane B"),
    Coefficient("cg_source", "A", "SOURCE_DISPLAY", F(631, 732)),
    Coefficient("geodesic_236805", "A", "SOURCE_DISPLAY", F(236805, 1),
                note="numerator of the RECORDED_POSTHOC_LEAD; see the "
                     "Bermuda lane"),
    # ---- lane B: exact recovered arithmetic ----
    Coefficient("eta_F_exact_candidate", "B", "EXACT_ARITHMETIC",
                F(64672, 961),
                note="47/63 * 9/31 * (311 - 9/31); the recovered exact "
                     "expression, units N/W_ring_coupled",
                relations=("differs_from_display_by:33/9610",)),
    Coefficient("q_reduced", "B", "EXACT_ARITHMETIC", F(9, 31)),
    Coefficient("eta_display_minus_exact", "B", "EXACT_ARITHMETIC",
                ETA_GAP, note="the gap itself, kept visible"),
    # ---- lane C: design geometry (the source locks) ----
    Coefficient("ring_family", "C", "GEOMETRY_DESIGN", F(37)),
    Coefficient("running_cells", "C", "GEOMETRY_DESIGN", F(35, 37),
                note="35/37 running"),
    Coefficient("steering_active", "C", "GEOMETRY_DESIGN", F(33)),
    Coefficient("carrier_ratio", "C", "GEOMETRY_DESIGN", F(411, 37),
                relations=("equals:11 + 4/37",)),
    Coefficient("aux_188_288", "C", "GEOMETRY_DESIGN", F(188, 288),
                relations=("reduces_to:47/72",)),
    # ---- lane D: physical measurements (all pending) ----
    Coefficient("eta_couple", "D", "BENCH_REQUIRED",
                note="wall-to-ring coupling efficiency; unmeasured"),
    Coefficient("eta_F_measured", "D", "BENCH_REQUIRED",
                note="the only object that could ever ground a force "
                     "claim; unmeasured"),
    Coefficient("L_eff", "D", "BENCH_REQUIRED"),
    Coefficient("C_eff", "D", "BENCH_REQUIRED"),
    Coefficient("Q_L", "D", "BENCH_REQUIRED"),
    Coefficient("R_loss", "D", "BENCH_REQUIRED"),
)


def registry_rows() -> list:
    return [c.as_row() for c in REGISTRY]


def registry_json() -> str:
    return json.dumps(registry_rows(), indent=2, sort_keys=False)


def display_vs_exact() -> dict:
    """The mandated status block, as data."""
    return {
        "source_display": "67.3 N/W",
        "exact_recovered_calculation": "64672/961 N/W_ring_coupled",
        "relation": "rounds to same one-decimal value",
        "not": "exact equality",
        "exact_gap": str(ETA_GAP),
        "gap_is_33_over_9610": ETA_GAP == F(33, 9610),
    }


def performance_claimants() -> list:
    """Who may currently claim physical performance. Expected: nobody."""
    return [c.name for c in REGISTRY if c.may_claim_performance]


__all__ = ["LANES", "Coefficient", "ETA_GAP", "REGISTRY", "registry_rows",
           "registry_json", "display_vs_exact", "performance_claimants"]
