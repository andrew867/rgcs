"""Flat 2-D templates: SVG axial section, SVG top template, and a
minimal R12 ASCII DXF winding template."""
from __future__ import annotations

import math
from pathlib import Path

from rgcs_core.provenance import sha256_file

from rgcs_desktop.services.phryll_v2.cone_generator import ConeDesign


def axial_section_svg(cone: ConeDesign, z_eye_mm: float | None,
                      out_path: str | Path) -> dict:
    """Axial cross-section: crystal-side inner profile, outer profile,
    and the Eye plane, dimension-labelled. 4 px per mm."""
    scale = 4.0
    height = cone.generated_dimensions["height_mm"]
    r_max = cone.generated_dimensions["outer_base_diameter_mm"] / 2
    x0 = r_max * scale + 60
    y0 = 40.0
    h_px = height * scale

    def x(r: float) -> tuple[float, float]:
        return x0 - r * scale, x0 + r * scale

    def y(z: float) -> float:
        return y0 + (height - z) * scale   # z up

    p = ['<svg xmlns="http://www.w3.org/2000/svg" '
         f'width="{2 * x0:.0f}" height="{h_px + 110:.0f}" '
         'font-family="sans-serif" font-size="12">',
         f'<title>{cone.design_id} axial section</title>']
    for profile, color in ((cone.inner_profile, "#1258a8"),
                           (cone.outer_profile, "#111111")):
        for side in (0, 1):
            points = " ".join(
                f"{x(pt.r_mm)[side]:.1f},{y(pt.z_mm):.1f}"
                for pt in profile)
            p.append(f'<polyline points="{points}" fill="none" '
                     f'stroke="{color}" stroke-width="1.5"/>')
    if z_eye_mm is not None:
        ye = y(z_eye_mm)
        p.append(f'<line x1="{x0 - r_max * scale - 20:.1f}" '
                 f'y1="{ye:.1f}" x2="{x0 + r_max * scale + 20:.1f}" '
                 f'y2="{ye:.1f}" stroke="#b00020" '
                 'stroke-dasharray="6 4" stroke-width="1.5"/>')
        p.append(f'<text x="{x0 + r_max * scale + 24:.1f}" '
                 f'y="{ye + 4:.1f}" fill="#b00020">Eye '
                 f'{z_eye_mm:g} mm</text>')
    dims = cone.generated_dimensions
    p.append(f'<text x="{x0:.1f}" y="{y0 - 16:.1f}" '
             f'text-anchor="middle" font-weight="bold">'
             f'{cone.design_id} — height {dims["height_mm"]:g} mm · '
             f'inner {dims["inner_base_diameter_mm"]:g} → '
             f'{dims["inner_top_diameter_mm"]:g} mm · wall '
             f'{dims["wall_thickness_mm"]:g} mm</text>')
    p.append(f'<text x="{x0:.1f}" y="{h_px + 100:.1f}" '
             'text-anchor="middle">generated from crystal '
             f'{cone.crystal_id} (envelope + clearance; not a scaled '
             'reference mesh)</text>')
    p.append("</svg>")
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(p), encoding="utf-8")
    return {"path": str(out_path), "sha256": sha256_file(str(out_path)),
            "kind": "svg"}


def top_template_svg(cone: ConeDesign, facet_count: int,
                     out_path: str | Path) -> dict:
    """Top-view template: outer/inner circles + facet polygon."""
    scale = 4.0
    r_out = cone.generated_dimensions["outer_base_diameter_mm"] / 2
    r_in = cone.generated_dimensions["inner_base_diameter_mm"] / 2
    c = r_out * scale + 40
    p = ['<svg xmlns="http://www.w3.org/2000/svg" '
         f'width="{2 * c:.0f}" height="{2 * c + 30:.0f}" '
         'font-family="sans-serif" font-size="12">',
         f'<title>{cone.design_id} top template</title>',
         f'<circle cx="{c}" cy="{c}" r="{r_out * scale:.1f}" '
         'fill="none" stroke="#111" stroke-width="1.5"/>',
         f'<circle cx="{c}" cy="{c}" r="{r_in * scale:.1f}" '
         'fill="none" stroke="#1258a8" stroke-width="1.5"/>']
    pts = []
    for i in range(facet_count):
        ang = 2 * math.pi * i / facet_count - math.pi / 2
        pts.append(f"{c + r_in * scale * math.cos(ang):.1f},"
                   f"{c + r_in * scale * math.sin(ang):.1f}")
    p.append(f'<polygon points="{" ".join(pts)}" fill="none" '
             'stroke="#b26a00" stroke-dasharray="4 3"/>')
    p.append(f'<text x="{c}" y="{2 * c + 20:.1f}" '
             f'text-anchor="middle">outer {2 * r_out:g} mm · inner '
             f'{2 * r_in:g} mm · {facet_count} facets</text>')
    p.append("</svg>")
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(p), encoding="utf-8")
    return {"path": str(out_path), "sha256": sha256_file(str(out_path)),
            "kind": "svg"}


def _dxf_lines(entities: list[str]) -> str:
    return "\n".join(["0", "SECTION", "2", "ENTITIES"] + entities
                     + ["0", "ENDSEC", "0", "EOF"]) + "\n"


def winding_template_dxf(coil: dict, cone: ConeDesign,
                         out_path: str | Path) -> dict:
    """Unrolled winding template (R12 ASCII DXF): the outer surface
    developed flat, with copper/silver groove lines and the Eye plane.

    Development approximation uses the mean outer radius across the
    winding band (stated on the drawing via layer names).
    """
    paths = coil["paths"]
    pitch = float(coil["spacing"]["groove_pitch_mm"])
    band_bottom = float(paths["band_bottom_mm"])
    band_top = float(paths["band_top_mm"])
    z_eye = float(coil["eye_alignment"]["z_eye_mm"])
    radii = [p.r_mm for p in cone.outer_profile
             if band_bottom <= p.z_mm <= band_top]
    mean_r = sum(radii) / len(radii)
    circumference = 2 * math.pi * mean_r

    def line(x1, y1, x2, y2, layer):
        return ["0", "LINE", "8", layer,
                "10", f"{x1:.4f}", "20", f"{y1:.4f}",
                "11", f"{x2:.4f}", "21", f"{y2:.4f}"]

    entities: list[str] = []
    # band frame
    entities += line(0, band_bottom, circumference, band_bottom, "FRAME")
    entities += line(0, band_top, circumference, band_top, "FRAME")
    entities += line(0, band_bottom, 0, band_top, "FRAME")
    entities += line(circumference, band_bottom, circumference,
                     band_top, "FRAME")
    # eye plane
    entities += line(0, z_eye, circumference, z_eye, "EYE_PLANE")
    # crossed ±45° multi-start lattice, developed flat: two families
    # of parallel diagonal strands (slope ±tan(helix angle)), spaced
    # one axial strand spacing apart, anchored so a strand of each
    # family passes (x=0, z_eye)
    slope = math.tan(math.radians(
        float(paths.get("helix_angle_deg", 45.0))))
    axial = float(coil["spacing"].get("axial_strand_spacing_mm",
                                      pitch))
    for layer, s in (("COPPER_CW", 1.0), ("SILVER_CCW", -1.0)):
        span = circumference * slope
        c = z_eye
        while c > band_bottom - span - axial:
            c -= axial
        while c < band_top + span:
            # y(x) = c + s*slope*x, clipped to the band rectangle
            xs = []
            for y_edge in (band_bottom, band_top):
                x_at = (y_edge - c) / (s * slope)
                xs.append(x_at)
            x_lo = max(0.0, min(xs))
            x_hi = min(circumference, max(xs))
            if x_hi > x_lo:
                y_lo = c + s * slope * x_lo
                y_hi = c + s * slope * x_hi
                entities += line(x_lo, y_lo, x_hi, y_hi, layer)
            c += axial
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(_dxf_lines(entities), encoding="utf-8")
    return {"path": str(out_path), "sha256": sha256_file(str(out_path)),
            "kind": "dxf",
            "developed_mean_radius_mm": mean_r}
