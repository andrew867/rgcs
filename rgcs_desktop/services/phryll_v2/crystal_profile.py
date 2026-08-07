"""Crystal profile service: normalized measured profiles, axial radius
envelope, and Eye-coordinate validation.

Frame convention (04_GEOMETRY_MATH): the crystal axis is z; z = 0 is
the base / 52-degree end reference plane; z = length_mm is the top /
60-degree tip reference plane; z_eye_mm is the Eye coordinate along
the axis.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from rgcs_desktop.services.phryll_v2.schemas import validate


class ProfileError(ValueError):
    """A refused crystal profile (with the reason)."""


@dataclass(frozen=True)
class ProfilePoint:
    z_mm: float
    r_mm: float


@dataclass
class CrystalProfile:
    crystal_id: str
    length_mm: float
    top_diameter_mm: float
    base_diameter_mm: float
    max_body_width_mm: float
    facet_count: int
    top_angle_deg: float | None = None
    base_angle_deg: float | None = None
    mass_g: float | None = None
    z_eye_mm: float | None = None
    eye_source: str = ""
    eye_uncertainty_mm: float = 0.0
    uncertainty: dict = field(default_factory=dict)
    provenance: dict = field(default_factory=dict)
    raw: dict = field(default_factory=dict)


@dataclass
class EyeValidation:
    ok: bool
    z_eye_mm: float | None
    tolerance_mm: float | None
    reasons: list[str]


def normalize_crystal_profile(raw: dict) -> CrystalProfile:
    """Schema-validate and normalize a measured crystal profile dict."""
    errors = validate("crystal_profile", raw)
    if errors:
        raise ProfileError("crystal profile invalid: " + "; ".join(errors))
    profile = CrystalProfile(
        crystal_id=raw["crystal_id"],
        length_mm=float(raw["length_mm"]),
        top_diameter_mm=float(raw["top_diameter_mm"]),
        base_diameter_mm=float(raw["base_diameter_mm"]),
        max_body_width_mm=float(raw["max_body_width_mm"]),
        facet_count=int(raw["facet_count"]),
        top_angle_deg=raw.get("top_angle_deg"),
        base_angle_deg=raw.get("base_angle_deg"),
        mass_g=raw.get("mass_g"),
        z_eye_mm=raw.get("z_eye_mm"),
        eye_source=raw.get("eye_source", ""),
        eye_uncertainty_mm=float(raw.get("eye_uncertainty_mm", 0.0)),
        uncertainty=dict(raw.get("uncertainty", {})),
        provenance=dict(raw.get("provenance", {})),
        raw=dict(raw),
    )
    if profile.top_diameter_mm > profile.base_diameter_mm:
        raise ProfileError(
            f"top diameter {profile.top_diameter_mm} mm exceeds base "
            f"diameter {profile.base_diameter_mm} mm — check the axis "
            f"convention (z=0 is the base / 52-degree end)")
    if profile.max_body_width_mm < profile.base_diameter_mm:
        raise ProfileError(
            f"max body width {profile.max_body_width_mm} mm is smaller "
            f"than the base diameter {profile.base_diameter_mm} mm")
    if profile.z_eye_mm is not None and \
            not 0 <= profile.z_eye_mm <= profile.length_mm:
        raise ProfileError(
            f"z_eye {profile.z_eye_mm} mm is outside the crystal "
            f"[0, {profile.length_mm}] mm")
    return profile


def interpolate_crystal_radius(profile: CrystalProfile,
                               z_mm: float) -> float:
    """Radius envelope at axial station z (linear base->top taper; the
    body maximum governs at the base station)."""
    if not 0 <= z_mm <= profile.length_mm:
        raise ProfileError(f"z {z_mm} mm outside [0, {profile.length_mm}]")
    r_base = max(profile.base_diameter_mm,
                 profile.max_body_width_mm) / 2.0
    r_top = profile.top_diameter_mm / 2.0
    frac = z_mm / profile.length_mm
    return r_base + (r_top - r_base) * frac


def sample_crystal_envelope(profile: CrystalProfile,
                            n: int = 96) -> list[ProfilePoint]:
    if n < 2:
        raise ProfileError("need at least 2 envelope samples")
    step = profile.length_mm / (n - 1)
    return [ProfilePoint(z_mm=i * step,
                         r_mm=interpolate_crystal_radius(profile,
                                                         i * step))
            for i in range(n)]


def validate_eye_coordinate(profile: CrystalProfile) -> EyeValidation:
    """Eye coordinate check. The Eye is user-entered, calculated, or
    imported — it is NOT any midpoint unless the numbers coincide."""
    reasons = []
    if profile.z_eye_mm is None:
        return EyeValidation(ok=False, z_eye_mm=None, tolerance_mm=None,
                             reasons=["z_eye_mm missing — enter, "
                                      "calculate, or import the Eye "
                                      "coordinate"])
    tolerance = max(0.25, 2.0 * profile.eye_uncertainty_mm)
    midpoint = profile.length_mm / 2.0
    if abs(profile.z_eye_mm - midpoint) < 1e-9 and \
            profile.eye_source not in ("calculated", "measured"):
        reasons.append(
            f"z_eye equals the crystal midpoint ({midpoint:g} mm) with "
            f"source {profile.eye_source or 'unspecified'!r} — confirm "
            f"this is the Eye, not a midpoint default")
    return EyeValidation(ok=True, z_eye_mm=profile.z_eye_mm,
                         tolerance_mm=tolerance, reasons=reasons)
