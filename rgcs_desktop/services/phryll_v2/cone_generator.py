"""Custom cone generator: inner/outer profiles from the crystal
envelope. Never a scaled stock mesh.

    r_inner(z) = r_crystal(z) + fit_clearance_mm
    r_outer(z) = r_inner(z) + wall_thickness_mm
"""
from __future__ import annotations

from dataclasses import dataclass, field

from rgcs_core.provenance import sha256_of_jsonable

from rgcs_desktop.services.phryll_v2.crystal_profile import (
    CrystalProfile, ProfileError, ProfilePoint, sample_crystal_envelope)
from rgcs_desktop.services.phryll_v2.schemas import validate

#: robust defaults (04_GEOMETRY_MATH/REFERENCE_RATIO_NOTES)
DEFAULT_CLEARANCE_MM = 0.66
DEFAULT_WALL_MM = 1.8
DEFAULT_PRINT_TOLERANCE_MM = 0.2
MIN_CLEARANCE_MM = 0.2
MAX_CLEARANCE_MM = 5.0


@dataclass
class FitReport:
    ok: bool
    min_clearance_mm: float
    max_clearance_mm: float
    stations_checked: int
    failures: list[str] = field(default_factory=list)


@dataclass
class ConeDesign:
    design_id: str
    crystal_id: str
    fit: dict
    inner_profile: list[ProfilePoint]
    outer_profile: list[ProfilePoint]
    generated_dimensions: dict
    fit_report: FitReport
    source_style_profile_id: str = "CUSTOM_GENERATED"
    bottom_coupling: dict = field(default_factory=dict)

    def to_json(self) -> dict:
        body = {
            "schema_version": "2.0.0",
            "design_id": self.design_id,
            "crystal_id": self.crystal_id,
            "source_style_profile_id": self.source_style_profile_id,
            "fit": dict(self.fit),
            "generated_dimensions": dict(self.generated_dimensions),
            "bottom_coupling": dict(self.bottom_coupling),
            "fit_report": {
                "ok": self.fit_report.ok,
                "min_clearance_mm": self.fit_report.min_clearance_mm,
                "max_clearance_mm": self.fit_report.max_clearance_mm,
                "stations_checked": self.fit_report.stations_checked,
                "failures": list(self.fit_report.failures),
            },
        }
        body["sha256"] = sha256_of_jsonable(body)
        return body


def generate_inner_profile(profile: CrystalProfile,
                           clearance_mm: float,
                           n: int = 96) -> list[ProfilePoint]:
    if not MIN_CLEARANCE_MM <= clearance_mm <= MAX_CLEARANCE_MM:
        raise ProfileError(
            f"clearance {clearance_mm} mm outside "
            f"[{MIN_CLEARANCE_MM}, {MAX_CLEARANCE_MM}] mm — refused "
            f"rather than generating an unusable holder")
    return [ProfilePoint(p.z_mm, p.r_mm + clearance_mm)
            for p in sample_crystal_envelope(profile, n)]


def generate_outer_profile(inner: list[ProfilePoint],
                           wall_mm: float) -> list[ProfilePoint]:
    if wall_mm <= 0.4:
        raise ProfileError(f"wall {wall_mm} mm too thin to print "
                           f"reliably (need > 0.4 mm)")
    return [ProfilePoint(p.z_mm, p.r_mm + wall_mm) for p in inner]


def check_fit(profile: CrystalProfile,
              inner_profile: list[ProfilePoint],
              fit_clearance_min_mm: float = MIN_CLEARANCE_MM) -> FitReport:
    """r_inner(z) - r_crystal(z) >= fit_clearance_min at every station."""
    from rgcs_desktop.services.phryll_v2.crystal_profile import \
        interpolate_crystal_radius
    failures = []
    gaps = []
    for point in inner_profile:
        gap = point.r_mm - interpolate_crystal_radius(profile, point.z_mm)
        gaps.append(gap)
        if gap < fit_clearance_min_mm - 1e-9:
            failures.append(
                f"z={point.z_mm:.2f} mm: clearance {gap:.3f} mm < "
                f"minimum {fit_clearance_min_mm} mm")
    return FitReport(ok=not failures,
                     min_clearance_mm=min(gaps),
                     max_clearance_mm=max(gaps),
                     stations_checked=len(inner_profile),
                     failures=failures[:10])


def make_cone_design(profile: CrystalProfile,
                     fit_settings: dict | None = None) -> ConeDesign:
    """The custom cone for this crystal. Diameter arithmetic:

        inner_d = crystal_d + 2*clearance
        outer_d = inner_d + 2*wall
    """
    settings = {
        "clearance_mm": DEFAULT_CLEARANCE_MM,
        "wall_thickness_mm": DEFAULT_WALL_MM,
        "print_tolerance_mm": DEFAULT_PRINT_TOLERANCE_MM,
        **(fit_settings or {}),
    }
    clearance = float(settings["clearance_mm"])
    wall = float(settings["wall_thickness_mm"])
    inner = generate_inner_profile(profile, clearance)
    outer = generate_outer_profile(inner, wall)
    fit_report = check_fit(profile, inner)

    inner_top_d = profile.top_diameter_mm + 2 * clearance
    inner_base_d = max(profile.base_diameter_mm,
                       profile.max_body_width_mm) + 2 * clearance
    dims = {
        "height_mm": profile.length_mm,
        "inner_top_diameter_mm": inner_top_d,
        "inner_base_diameter_mm": inner_base_d,
        "outer_top_diameter_mm": inner_top_d + 2 * wall,
        "outer_base_diameter_mm": inner_base_d + 2 * wall,
        "wall_thickness_mm": wall,
        "clearance_mm": clearance,
        "generation": "crystal_envelope_plus_clearance",
    }
    design = ConeDesign(
        design_id=f"PHV2-{profile.crystal_id}",
        crystal_id=profile.crystal_id,
        fit=settings,
        inner_profile=inner,
        outer_profile=outer,
        generated_dimensions=dims,
        fit_report=fit_report,
    )
    errors = validate("cone_design", design.to_json())
    if errors:
        raise ProfileError("generated cone failed its own schema: "
                           + "; ".join(errors))
    return design
