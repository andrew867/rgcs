"""Crystal Validator services: schema + semantic validation, derived
geometry, and the labelled SVG diagram.

Everything here is Qt-free and deterministic. Derived values are
labelled derived; model estimates are labelled model estimates and are
"unavailable" (never zero) when the geometry does not support them.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

from rgcs_core.provenance import json_dumps, sha256_of_jsonable

from rgcs_desktop.services.design_studio import MODEL_OUTPUT
from rgcs_desktop.services.schemas import validate_instance

SCHEMA_NAME = "crystal_specimen.schema.json"

#: Reference densities (g/cm^3) for the coarse consistency check.
#: These are published handbook values, used only to flag gross
#: measurement inconsistencies — never to certify material identity.
MATERIAL_DENSITY_G_CM3 = {
    "quartz": 2.65,
    "amethyst": 2.65,
    "calcite": 2.71,
    "fluorite": 3.18,
    "obsidian": 2.40,
    "glass": 2.50,
}

#: Longitudinal sound speeds (m/s) for the axial half-wave model
#: estimate. Model input, declared per material family.
MATERIAL_SOUND_SPEED_M_S = {
    "quartz": 5720.0,
    "amethyst": 5720.0,
    "glass": 5300.0,
}

#: Optional measurements that improve a specimen record when present.
OPTIONAL_MEASUREMENTS = ("termination_angle_deg", "facet_count", "mass_g",
                         "measured_nodes_mm")


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    missing_optional: list[str] = field(default_factory=list)

    def summary(self) -> str:
        if self.ok:
            note = f" ({len(self.warnings)} warning(s))" if self.warnings else ""
            return f"valid{note}"
        return f"invalid: {'; '.join(self.errors)}"


def validate_specimen(specimen: dict) -> ValidationResult:
    """Schema validation plus semantic checks. Geometric/schema
    validation of measurements only — never a physical-effect claim."""
    errors = validate_instance(specimen, SCHEMA_NAME)
    warnings: list[str] = []
    missing = []

    dims = specimen.get("dimensions", {})
    unc = specimen.get("uncertainty", {})
    if not errors:
        if "width_mm" not in dims and "diameter_mm" not in dims:
            errors.append("width_mm or diameter_mm is required")
        if unc.get("length_mm", None) is None:
            errors.append("uncertainty.length_mm is required")
        cross = dims.get("diameter_mm", dims.get("width_mm", 0.0))
        if cross and dims.get("length_mm", 0.0) < cross:
            warnings.append(
                "length is smaller than width/diameter — check axis "
                "convention")
        for key in OPTIONAL_MEASUREMENTS:
            if key not in dims and key not in specimen:
                missing.append(key)
        nodes = specimen.get("measured_nodes_mm") or []
        length = dims.get("length_mm", 0.0)
        for n in nodes:
            if not 0 <= n <= length:
                errors.append(f"measured node {n} mm outside specimen "
                              f"length {length} mm")
    return ValidationResult(ok=not errors, errors=errors,
                            warnings=warnings, missing_optional=missing)


def derive_crystal_geometry(specimen: dict) -> dict:
    """Deterministic derived geometry + declared model estimates.

    Unsupported values are None (rendered as "unavailable"), never zero.
    """
    dims = specimen["dimensions"]
    length = float(dims["length_mm"])
    diameter = dims.get("diameter_mm")
    width = dims.get("width_mm")
    cross = float(diameter if diameter is not None else width)
    material = str(specimen.get("material_family", "")).lower()

    derived: dict = {
        "cross_section_mm": cross,
        "cross_section_kind": "diameter" if diameter is not None else "width",
        "aspect_ratio": length / cross if cross else None,
        "length_to_diameter_ratio": (length / diameter
                                     if diameter else None),
    }

    angle = dims.get("termination_angle_deg")
    if angle is None:
        derived["termination_angle_status"] = "not measured"
    else:
        # natural quartz termination faces cluster near 51.7 deg
        derived["termination_angle_status"] = (
            "within 5 deg of the 51.7 deg reference"
            if abs(float(angle) - 51.7) <= 5.0
            else f"{float(angle):.1f} deg (outside the 51.7 deg ± 5 deg "
                 f"reference band)")

    # volume estimate — only where the geometry supports it
    if diameter is not None:
        r_cm = float(diameter) / 20.0
        volume_cm3 = math.pi * r_cm * r_cm * (length / 10.0)
        derived["volume_estimate_cm3"] = volume_cm3
        derived["volume_model"] = "right circular cylinder (model estimate)"
    elif width is not None and dims.get("side_count") in (None, 4):
        w_cm = float(width) / 10.0
        volume_cm3 = w_cm * w_cm * (length / 10.0)
        derived["volume_estimate_cm3"] = volume_cm3
        derived["volume_model"] = "square prism (model estimate)"
    else:
        derived["volume_estimate_cm3"] = None
        derived["volume_model"] = "unavailable for this geometry"

    # density consistency — only when mass and volume both exist
    mass = specimen.get("mass_g")
    ref = MATERIAL_DENSITY_G_CM3.get(material)
    vol = derived["volume_estimate_cm3"]
    if mass is not None and vol:
        rho = float(mass) / vol
        derived["density_g_cm3"] = rho
        if ref is None:
            derived["density_check"] = (
                f"computed {rho:.2f} g/cm3; no reference density for "
                f"'{material}'")
        elif abs(rho - ref) / ref <= 0.25:
            derived["density_check"] = (
                f"computed {rho:.2f} g/cm3 vs reference {ref:.2f} — "
                f"consistent within 25%")
        else:
            derived["density_check"] = (
                f"computed {rho:.2f} g/cm3 vs reference {ref:.2f} — "
                f"inconsistent; check mass/dimensions")
    else:
        derived["density_g_cm3"] = None
        derived["density_check"] = "unavailable (needs mass and volume)"

    # axial half-wave model estimate where a sound speed is declared
    speed = MATERIAL_SOUND_SPEED_M_S.get(material)
    if speed:
        derived["axial_half_wave_hz"] = speed / (2.0 * (length / 1000.0))
        derived["mode_model"] = (
            f"f = v/(2L) with v={speed:.0f} m/s ({material}); model "
            f"estimate, not a measurement")
    else:
        derived["axial_half_wave_hz"] = None
        derived["mode_model"] = "unavailable (no declared sound speed)"

    derived["classification"] = MODEL_OUTPUT
    return derived


def specimen_receipt_json(specimen: dict, derived: dict) -> str:
    """Canonical, deterministic JSON receipt for a specimen: the
    specimen, its derived geometry, and the sha256 of that content."""
    content = {"specimen": specimen, "derived": derived}
    body = dict(content)
    body["sha256"] = sha256_of_jsonable(content)
    return json_dumps(body, indent=2, sort_keys=True)


def export_specimen_json(specimen: dict, derived: dict,
                         out_path: Path) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(specimen_receipt_json(specimen, derived),
                        encoding="utf-8")
    return out_path


def make_crystal_diagram(specimen: dict, out_path: Path) -> Path:
    """Labelled 2-D SVG diagram: outline, termination angle, node
    markers, measurement labels. Deterministic plain-XML output."""
    dims = specimen["dimensions"]
    length = float(dims["length_mm"])
    cross = float(dims.get("diameter_mm", dims.get("width_mm")))
    angle = dims.get("termination_angle_deg")
    nodes = specimen.get("measured_nodes_mm") or []

    # drawing box: specimen laid horizontally, 4 px per mm capped scale
    scale = min(4.0, 640.0 / max(length, 1.0))
    x0, y0 = 60.0, 60.0
    body_l = length * scale
    body_w = max(cross * scale, 12.0)
    tip = min(body_w, 0.35 * body_l)  # termination wedge

    p = []
    p.append('<svg xmlns="http://www.w3.org/2000/svg" '
             f'width="{x0 * 2 + body_l + tip:.0f}" '
             f'height="{y0 * 2 + body_w:.0f}" '
             'font-family="sans-serif" font-size="12">')
    p.append(f'<title>specimen {specimen["specimen_id"]}</title>')
    # body
    p.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{body_l:.1f}" '
             f'height="{body_w:.1f}" fill="none" stroke="#111" '
             'stroke-width="1.5"/>')
    # termination wedge
    p.append(f'<path d="M {x0 + body_l:.1f} {y0:.1f} '
             f'L {x0 + body_l + tip:.1f} {y0 + body_w / 2:.1f} '
             f'L {x0 + body_l:.1f} {y0 + body_w:.1f}" '
             'fill="none" stroke="#111" stroke-width="1.5"/>')
    # length dimension
    yd = y0 + body_w + 24
    p.append(f'<line x1="{x0:.1f}" y1="{yd:.1f}" x2="{x0 + body_l:.1f}" '
             f'y2="{yd:.1f}" stroke="#555"/>')
    p.append(f'<text x="{x0 + body_l / 2:.1f}" y="{yd - 5:.1f}" '
             f'text-anchor="middle">length {length:g} mm</text>')
    # cross-section dimension
    kind = "diameter" if "diameter_mm" in dims else "width"
    p.append(f'<text x="{x0 - 10:.1f}" y="{y0 + body_w / 2:.1f}" '
             f'text-anchor="end">{kind} {cross:g} mm</text>')
    # termination angle label
    if angle is not None:
        p.append(f'<text x="{x0 + body_l + tip:.1f}" y="{y0 - 8:.1f}" '
                 f'text-anchor="end">termination {float(angle):g}°</text>')
    # node markers
    for n in nodes:
        xn = x0 + float(n) * scale
        p.append(f'<line x1="{xn:.1f}" y1="{y0 - 6:.1f}" x2="{xn:.1f}" '
                 f'y2="{y0 + body_w + 6:.1f}" stroke="#b26a00" '
                 'stroke-dasharray="4 3"/>')
        p.append(f'<text x="{xn:.1f}" y="{y0 - 10:.1f}" '
                 f'text-anchor="middle" fill="#b26a00">{n:g}</text>')
    p.append(f'<text x="{x0:.1f}" y="{y0 - 28:.1f}" font-size="14" '
             f'font-weight="bold">specimen '
             f'{specimen["specimen_id"]}</text>')
    p.append("</svg>")

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(p), encoding="utf-8")
    return out_path
