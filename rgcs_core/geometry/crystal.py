"""Faceted crystal geometry and density inverse (RGCS-M.1..M.7).

Units: lengths and diameters in mm, areas in mm^2, volume in cm^3
(the mm^3 -> cm^3 conversion appears exactly once, in crystal_geometry),
mass in g, density in g/cm^3, angles in degrees. Coordinate frame for
node quantities: x from the female (wide) apex toward the male (narrow)
apex, 0 <= x <= L (NOTATION_AND_UNITS.md section 2.6).

The prototype's ``geometry_balance_node_mm`` (70.806 mm; no derivation)
is deliberately NOT implemented here and must never be reintroduced
(RGCS-M.39 resolution of D-01).
"""

from __future__ import annotations

import math
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..provenance import classified, classification_string

__all__ = ["CrystalGeometry", "polygon_area_mm2", "apothem_mm",
           "termination_height_mm", "crystal_geometry",
           "solve_diameter_scale_for_mass"]

DiameterMode = Literal["across_vertices", "across_flats"]
AngleMode = Literal["face_slope", "axis_to_face", "apex_included"]


class CrystalGeometry(BaseModel):
    """Static crystal geometry and material inputs (state component G).

    Default angle values 51.843/60 deg are Source claim (RG-16); the
    conventions themselves are Established (RGCS-M.4)."""

    model_config = ConfigDict(frozen=True)

    length_mm: float = Field(gt=0.0)
    wide_diameter_mm: float = Field(gt=0.0)
    narrow_diameter_mm: float = Field(gt=0.0)
    facets: int = Field(default=6, ge=3)
    female_angle_deg: float = Field(default=51.843, gt=0.0, lt=180.0)
    male_angle_deg: float = Field(default=60.0, gt=0.0, lt=180.0)
    density_g_cm3: float = Field(default=2.65, gt=0.0)
    diameter_mode: DiameterMode = "across_vertices"
    angle_mode: AngleMode = "face_slope"

    @model_validator(mode="after")
    def _check_taper(self) -> "CrystalGeometry":
        if self.wide_diameter_mm < self.narrow_diameter_mm:
            raise ValueError("wide_diameter_mm must be >= narrow_diameter_mm")
        for name in ("length_mm", "wide_diameter_mm", "narrow_diameter_mm",
                     "density_g_cm3"):
            if not math.isfinite(getattr(self, name)):
                raise ValueError(f"{name} must be finite")
        return self


@classified("Established", registry=("RGCS-M.1", "RGCS-M.2"), sources=("RG-04",))
def polygon_area_mm2(diameter_mm: float, facets: int,
                     mode: DiameterMode = "across_vertices") -> float:
    """Regular-polygon area (mm^2). RGCS-M.1 (across-vertices):
    A = (N_f/8) D^2 sin(2 pi/N_f); RGCS-M.2 (across-flats):
    A = N_f (D/2)^2 tan(pi/N_f). Established plane geometry."""
    if not (math.isfinite(diameter_mm) and diameter_mm > 0):
        raise ValueError(f"diameter_mm must be positive; got {diameter_mm!r}")
    if facets < 3:
        raise ValueError("facets must be >= 3")
    if mode == "across_vertices":
        return facets / 8.0 * diameter_mm ** 2 * math.sin(2.0 * math.pi / facets)
    if mode == "across_flats":
        return facets * (diameter_mm / 2.0) ** 2 * math.tan(math.pi / facets)
    raise ValueError(f"unsupported diameter mode: {mode!r}")


@classified("Established", registry=("RGCS-M.3",), sources=("RG-04",))
def apothem_mm(diameter_mm: float, facets: int,
               mode: DiameterMode = "across_vertices") -> float:
    """Apothem r_a (mm) of the regular polygonal section (RGCS-M.3)."""
    if not (math.isfinite(diameter_mm) and diameter_mm > 0):
        raise ValueError(f"diameter_mm must be positive; got {diameter_mm!r}")
    if facets < 3:
        raise ValueError("facets must be >= 3")
    if mode == "across_vertices":
        return diameter_mm / 2.0 * math.cos(math.pi / facets)
    if mode == "across_flats":
        return diameter_mm / 2.0
    raise ValueError(f"unsupported diameter mode: {mode!r}")


@classified("Established", registry=("RGCS-M.4",), sources=("RG-04", "RG-16"),
            note="conventions Established; default angle VALUES are Source claim")
def termination_height_mm(apothem: float, angle_deg: float,
                          mode: AngleMode = "face_slope") -> float:
    """Cap (termination) height h (mm) per declared angle convention
    (RGCS-M.4): face_slope h = r_a tan(a); axis_to_face h = r_a/tan(a);
    apex_included h = r_a/tan(a/2)."""
    if not (math.isfinite(apothem) and apothem > 0):
        raise ValueError(f"apothem must be positive; got {apothem!r}")
    angle = math.radians(angle_deg)
    if not 0.0 < angle < math.pi:
        raise ValueError("angle must lie strictly between 0 and 180 degrees")
    if mode == "face_slope":
        return apothem * math.tan(angle)
    if mode == "axis_to_face":
        return apothem / math.tan(angle)
    if mode == "apex_included":
        return apothem / math.tan(angle / 2.0)
    raise ValueError(f"unsupported angle mode: {mode!r}")


@classified("Derived", registry=("RGCS-M.5", "RGCS-M.6", "RGCS-M.39"),
            sources=("RG-04",),
            note="Established solid geometry on declared inputs; node prior "
                 "x_g is a PRIOR only (RGCS-M.39)")
def crystal_geometry(g: CrystalGeometry) -> dict[str, Any]:
    """Full geometric summary: areas, cap heights, volume (RGCS-M.5),
    mass (RGCS-M.6), metric center (RGCS-M.38) and shaft-midpoint node
    prior x_g = (L + h_f - h_m)/2 in the female-apex frame (RGCS-M.39).

    The mm^3 -> cm^3 conversion happens exactly once, here."""
    aw = apothem_mm(g.wide_diameter_mm, g.facets, g.diameter_mode)
    an = apothem_mm(g.narrow_diameter_mm, g.facets, g.diameter_mode)
    hf = termination_height_mm(aw, g.female_angle_deg, g.angle_mode)
    hm = termination_height_mm(an, g.male_angle_deg, g.angle_mode)
    hs = g.length_mm - hf - hm
    if hs <= 0:
        raise ValueError("termination heights exceed total crystal length")

    area_w = polygon_area_mm2(g.wide_diameter_mm, g.facets, g.diameter_mode)
    area_n = polygon_area_mm2(g.narrow_diameter_mm, g.facets, g.diameter_mode)
    shaft_v = hs / 3.0 * (area_w + area_n + math.sqrt(area_w * area_n))
    volume_mm3 = shaft_v + area_w * hf / 3.0 + area_n * hm / 3.0
    volume_cm3 = volume_mm3 / 1000.0        # the single mm^3 -> cm^3 conversion
    mass_g = volume_cm3 * g.density_g_cm3
    davg = (g.wide_diameter_mm + g.narrow_diameter_mm) / 2.0
    node_prior = (g.length_mm + hf - hm) / 2.0   # RGCS-M.39, female frame

    return {
        "length_mm": g.length_mm,
        "average_diameter_mm": davg,
        "length_to_average_diameter": g.length_mm / davg,
        "taper_ratio": g.wide_diameter_mm / g.narrow_diameter_mm,
        "wide_apothem_mm": aw,
        "narrow_apothem_mm": an,
        "female_height_mm": hf,
        "male_height_mm": hm,
        "shaft_length_mm": hs,
        "wide_area_mm2": area_w,
        "narrow_area_mm2": area_n,
        "volume_cm3": volume_cm3,
        "mass_g": mass_g,
        "metric_center_mm": g.length_mm / 2.0,
        "node_prior_female_frame_mm": node_prior,
        "node_prior_male_frame_mm": g.length_mm - node_prior,
        "classification": classification_string(crystal_geometry),
    }


@classified("Derived", registry=("RGCS-M.7",),
            note="Newton iteration with bisection fallback; unique root "
                 "(V strictly increasing in the diameter scale)")
def solve_diameter_scale_for_mass(g: CrystalGeometry, measured_mass_g: float,
                                  tol_rel: float = 1e-10,
                                  max_iter: int = 200) -> dict[str, Any]:
    """Density inverse (RGCS-M.7): solve rho*V(s_D*D_w, s_D*D_n; L) = m*
    for the diameter scale s_D. Convergence |dm|/m* < tol_rel."""
    if not (math.isfinite(measured_mass_g) and measured_mass_g > 0):
        raise ValueError("measured_mass_g must be positive and finite")

    def mass_at(s: float) -> float:
        scaled = g.model_copy(update={
            "wide_diameter_mm": g.wide_diameter_mm * s,
            "narrow_diameter_mm": g.narrow_diameter_mm * s,
        })
        return float(crystal_geometry(scaled)["mass_g"])

    # Bracket the (unique) root: V is strictly increasing in s_D.
    lo, hi = 1e-3, 1.0
    while mass_at(hi) < measured_mass_g:
        hi *= 2.0
        if hi > 1e4:
            raise ValueError("cannot bracket diameter scale (mass too large "
                             "for any physical scale factor)")
    while mass_at(lo) > measured_mass_g:
        lo *= 0.5
        if lo < 1e-9:
            raise ValueError("cannot bracket diameter scale (mass too small)")

    s = 0.5 * (lo + hi)
    for iteration in range(max_iter):
        m = mass_at(s)
        err = (m - measured_mass_g) / measured_mass_g
        if abs(err) < tol_rel:
            break
        # Numerical Newton step, guarded by the bracket (bisection fallback).
        ds = max(s * 1e-6, 1e-9)
        dm_ds = (mass_at(s + ds) - m) / ds
        if m > measured_mass_g:
            hi = s
        else:
            lo = s
        step = s - (m - measured_mass_g) / dm_ds if dm_ds > 0 else None
        s = step if (step is not None and lo < step < hi) else 0.5 * (lo + hi)
    else:
        raise RuntimeError("density inverse did not converge")

    return {
        "diameter_scale": s,
        "wide_diameter_mm": g.wide_diameter_mm * s,
        "narrow_diameter_mm": g.narrow_diameter_mm * s,
        "predicted_mass_g": mass_at(s),
        "measured_mass_g": measured_mass_g,
        "iterations": iteration + 1,
        "classification": classification_string(solve_diameter_scale_for_mass),
    }
