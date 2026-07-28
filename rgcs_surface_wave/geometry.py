"""R10.15 Phase B07 — typed annular geometry.

All lengths in metres, angles in radians internally (degrees at the
schema boundary). The candidate constants (35 cells, 33 active,
29/89 area ratio, the bench-scale radii) are PREREGISTERED RESEARCH
CANDIDATES, not established optima, and every one of them must be
compared against the null library in ``masks.py``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from rgcs_surface_wave.evidence import ClaimClass

EPS0 = 8.8541878128e-12
MU0 = 4.0e-7 * math.pi
C0 = 299792458.0

#: Preregistered candidate constants (Phase A04 freeze).
CANDIDATE = {
    "cells": 35,
    "active": 33,
    "omitted": 2,
    "duty_fraction": [33, 35],
    "pitch_deg": 360.0 / 35.0,
    "five_pitch_deg": 5 * 360.0 / 35.0,      # = 360/7
    "area_ratio_inner_outer": [29, 89],
    "inner_radius_mm": 82.261610772,
    "outer_radius_mm": 144.109699835,
    "modulation_hz": 16.0,
    "carrier_hz": 4096.0,
    "carrier_phase_states": 125,
    "timing_step_us": 1.953125,
    "phase_step_deg": 2.88,
    "claim_class": ClaimClass.SOURCE_PROVENANCE.value,
    "note": "candidate inputs from the source record; no physical "
            "warrant, compared against controls in every study",
}


class GeometryError(ValueError):
    pass


@dataclass(frozen=True)
class DielectricSlab:
    """Loading slab above the annulus."""
    gap_m: float                 # slab-to-conductor separation
    thickness_m: float
    epsilon_r: float
    loss_tangent: float = 0.0

    def __post_init__(self):
        for name, v in (("gap_m", self.gap_m),
                        ("thickness_m", self.thickness_m)):
            if not (math.isfinite(v) and v > 0):
                raise GeometryError(f"{name} must be positive, got {v!r}")
        if self.epsilon_r < 1.0:
            raise GeometryError(
                f"epsilon_r must be >= 1 for a passive dielectric, got "
                f"{self.epsilon_r!r}")
        if not (0.0 <= self.loss_tangent < 1.0):
            raise GeometryError("loss_tangent must lie in [0, 1)")

    @property
    def epsilon_complex(self) -> complex:
        """exp(+j omega t) convention: passive loss is NEGATIVE
        imaginary part."""
        return self.epsilon_r * (1.0 - 1j * self.loss_tangent)


@dataclass(frozen=True)
class Conductor:
    """Annulus conductor (finite conductivity and thickness)."""
    conductivity_s_per_m: float = 5.8e7      # copper
    thickness_m: float = 35e-6               # 1 oz copper

    def skin_depth_m(self, frequency_hz: float) -> float:
        if frequency_hz <= 0:
            raise GeometryError("frequency must be positive")
        return math.sqrt(1.0 / (math.pi * frequency_hz * MU0
                                * self.conductivity_s_per_m))

    def surface_resistance_ohm(self, frequency_hz: float) -> float:
        return 1.0 / (self.conductivity_s_per_m
                      * self.skin_depth_m(frequency_hz))


@dataclass(frozen=True)
class Support:
    """A mechanical support: its reaction force must appear in the
    momentum ledger, never be silently dropped."""
    name: str
    position_m: tuple
    stiffness_n_per_m: float | None = None


@dataclass(frozen=True)
class AnnularGeometry:
    """Phase B07 typed geometry."""
    inner_radius_m: float
    outer_radius_m: float
    thickness_m: float
    cells: int = 35
    omitted_cells: tuple = ()
    dielectric: DielectricSlab | None = None
    conductor: Conductor = field(default_factory=Conductor)
    supports: tuple = ()

    def __post_init__(self):
        if not (0 < self.inner_radius_m < self.outer_radius_m):
            raise GeometryError(
                f"require 0 < inner < outer; got inner="
                f"{self.inner_radius_m!r}, outer={self.outer_radius_m!r}")
        if not (math.isfinite(self.thickness_m) and self.thickness_m > 0):
            raise GeometryError("thickness_m must be positive")
        if self.cells < 3:
            raise GeometryError("cells must be >= 3")
        for g in self.omitted_cells:
            if not isinstance(g, int) or isinstance(g, bool) \
                    or not (0 <= g < self.cells):
                raise GeometryError(
                    f"omitted cell index {g!r} outside 0..{self.cells - 1}")
        if len(set(self.omitted_cells)) != len(self.omitted_cells):
            raise GeometryError("omitted cell indices must be distinct")

    # ------------------------------------------------------ derived
    @property
    def active_cells(self) -> tuple:
        return tuple(j for j in range(self.cells)
                     if j not in set(self.omitted_cells))

    @property
    def pitch_rad(self) -> float:
        return 2.0 * math.pi / self.cells

    def cell_angle_rad(self, j: int) -> float:
        return 2.0 * math.pi * j / self.cells

    @property
    def area_ratio(self) -> float:
        return (self.inner_radius_m / self.outer_radius_m) ** 2

    @property
    def annulus_area_m2(self) -> float:
        return math.pi * (self.outer_radius_m ** 2
                          - self.inner_radius_m ** 2)

    @property
    def mean_radius_m(self) -> float:
        return 0.5 * (self.inner_radius_m + self.outer_radius_m)

    def has_diametric_pair(self) -> bool:
        """An exactly diametric omitted pair requires an even cell
        count; for the candidate N=35 it does not exist."""
        return self.cells % 2 == 0

    def record(self) -> dict:
        return {
            "schema": "rgcs.r1015.geometry.v1",
            "inner_radius_m": self.inner_radius_m,
            "outer_radius_m": self.outer_radius_m,
            "thickness_m": self.thickness_m,
            "cells": self.cells,
            "active_count": len(self.active_cells),
            "omitted_cells": list(self.omitted_cells),
            "pitch_deg": math.degrees(self.pitch_rad),
            "area_ratio": self.area_ratio,
            "annulus_area_m2": self.annulus_area_m2,
            "mean_radius_m": self.mean_radius_m,
            "exact_diametric_pair_possible": self.has_diametric_pair(),
            "dielectric": (None if self.dielectric is None else {
                "gap_m": self.dielectric.gap_m,
                "thickness_m": self.dielectric.thickness_m,
                "epsilon_r": self.dielectric.epsilon_r,
                "loss_tangent": self.dielectric.loss_tangent}),
            "conductor": {
                "conductivity_s_per_m":
                    self.conductor.conductivity_s_per_m,
                "thickness_m": self.conductor.thickness_m},
            "supports": [s.name for s in self.supports],
            "claim_class": ClaimClass.DERIVED.value,
        }


def candidate_geometry(with_dielectric: bool = True) -> AnnularGeometry:
    """The preregistered bench-scale candidate. Gap indices are NOT
    fixed by any source authority: the default here is the adjacent
    pair (0, 1), and every study must sweep the null library."""
    return AnnularGeometry(
        inner_radius_m=CANDIDATE["inner_radius_mm"] * 1e-3,
        outer_radius_m=CANDIDATE["outer_radius_mm"] * 1e-3,
        thickness_m=1.6e-3,
        cells=35, omitted_cells=(0, 1),
        dielectric=(DielectricSlab(gap_m=1.0e-3, thickness_m=3.0e-3,
                                   epsilon_r=4.4, loss_tangent=0.02)
                    if with_dielectric else None),
        supports=(Support("support_a", (0.0, 0.0, -0.01)),
                  Support("support_b", (0.0, 0.0, -0.01))))


def validate(geo: AnnularGeometry) -> dict:
    """Phase B07 validation with plain-language findings."""
    warnings, notes = [], []
    if geo.cells % 2:
        notes.append(
            f"cells={geo.cells} is odd, so no exactly diametric omitted "
            "pair exists; 'diametric' controls use the nearest "
            "separation and are labelled NEAREST_DIAMETRIC")
    ar = geo.area_ratio
    target = 29.0 / 89.0
    if abs(ar - target) < 5e-4:
        notes.append(f"area ratio {ar:.6f} matches the candidate 29/89 "
                     f"({target:.6f}) to {abs(ar - target):.2e}")
    if geo.dielectric and geo.dielectric.loss_tangent == 0:
        warnings.append("lossless dielectric: Q will be limited only by "
                        "conductor loss and radiation; do not read the "
                        "resulting Q as physical")
    if not geo.supports:
        warnings.append("no supports declared: the momentum ledger "
                        "cannot attribute a reaction force and will "
                        "refuse to close")
    return {"ok": True, "warnings": warnings, "notes": notes,
            "record": geo.record()}
