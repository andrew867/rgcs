"""Deterministic OpenSCAD export for the generated cone + coil sleeve.

The SCAD text is generated from the crystal-derived design values —
there is no import() or scale() of any reference mesh anywhere in the
output. Same input JSON -> byte-identical SCAD.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from rgcs_core.provenance import sha256_file

from rgcs_desktop.services.phryll_v2.cone_generator import ConeDesign


def _profile_points(profile) -> str:
    return ", ".join(f"[{p.r_mm:.4f}, {p.z_mm:.4f}]" for p in profile)


def _ring_dim(coupling: dict | None, key: str, default_expr: str) -> str:
    ring = (coupling or {}).get("pickup_ring") or {}
    if key in ring:
        return f"{float(ring[key]):.4f}"
    return default_expr


def render_scad(cone: ConeDesign, coil: dict | None = None,
                coupling: dict | None = None) -> str:
    dims = cone.generated_dimensions
    lines = [
        "// RGCS Phryll Generator Designer v2 — generated custom cone",
        f"// design {cone.design_id} for crystal {cone.crystal_id}",
        "// Crystal-first parametric output: every surface derives from",
        "// the entered crystal envelope plus clearance and wall.",
        "// No reference mesh is imported or scaled here.",
        "// Model output — an engineering plan, not a measurement.",
        "",
        "$fn = 96;",
        "",
        f"height_mm = {dims['height_mm']:.4f};",
        f"inner_top_d_mm = {dims['inner_top_diameter_mm']:.4f};",
        f"inner_base_d_mm = {dims['inner_base_diameter_mm']:.4f};",
        f"outer_top_d_mm = {dims['outer_top_diameter_mm']:.4f};",
        f"outer_base_d_mm = {dims['outer_base_diameter_mm']:.4f};",
        f"wall_mm = {dims['wall_thickness_mm']:.4f};",
        f"clearance_mm = {dims['clearance_mm']:.4f};",
        "",
        "// axial profiles as [r, z] polygons (rotate_extrude)",
        f"inner_profile = [{_profile_points(cone.inner_profile)}];",
        f"outer_profile = [{_profile_points(cone.outer_profile)}];",
        "",
        "module crystal_envelope_preview() {",
        "    // the crystal itself (inner profile minus clearance)",
        "    color(\"lightblue\", 0.35)",
        "    rotate_extrude()",
        "        polygon(concat([[0, 0]],",
        "            [for (p = inner_profile)"
        " [p[0] - clearance_mm, p[1]]],",
        "            [[0, height_mm]]));",
        "}",
        "",
        "module custom_inner_cone() {",
        "    rotate_extrude()",
        "        polygon(concat([[0, 0]], inner_profile,"
        " [[0, height_mm]]));",
        "}",
        "",
        "module custom_outer_cone() {",
        "    rotate_extrude()",
        "        polygon(concat([[0, 0]], outer_profile,"
        " [[0, height_mm]]));",
        "}",
        "",
        "module cone_shell() {",
        "    difference() {",
        "        custom_outer_cone();",
        "        translate([0, 0, -0.01]) scale([1, 1, 1.001])",
        "            custom_inner_cone();",
        "    }",
        "}",
    ]
    if coil is not None:
        spacing = coil["spacing"]
        paths = coil["paths"]
        eye = coil["eye_alignment"]
        lines += [
            "",
            f"wire_d_mm = {coil['wire']['wire_diameter_mm']:.4f};",
            f"groove_pitch_mm = {spacing['groove_pitch_mm']:.4f};",
            f"groove_depth_mm = {spacing['groove_depth_mm']:.4f};",
            f"z_eye_mm = {eye['z_eye_mm']:.4f};",
            f"band_bottom_mm = {paths['band_bottom_mm']:.4f};",
            f"band_top_mm = {paths['band_top_mm']:.4f};",
            f"coil_turns = {paths['copper']['turns']};",
            f"phase_cu_rad = {paths['copper']['phase_rad_at_z0']:.6f};",
            f"phase_ag_rad = {paths['silver']['phase_rad_at_z0']:.6f};",
            "",
            "function outer_r_at(z) = outer_profile[",
            "    min(len(outer_profile) - 1,",
            "        floor(z / height_mm * (len(outer_profile) - 1)))"
            "][0];",
            "",
            "band_h_mm = band_top_mm - band_bottom_mm;",
            "band_r_bottom_mm = outer_r_at(band_bottom_mm);",
            "band_r_top_mm = outer_r_at(band_top_mm);",
            "",
            "module groove_helix(phase_rad, handed) {",
            "    // CONTINUOUS helical slot: a wire-diameter circle at",
            "    // the outer surface, twist-extruded up the band. The",
            "    // linear_extrude scale factor tracks the cone taper,",
            "    // so the cutter hugs the outer wall the whole way.",
            "    twist_deg = -handed * 360 * band_h_mm / groove_pitch_mm;",
            "    start_deg = phase_rad * 180 / PI",
            "        + handed * 360 * band_bottom_mm / groove_pitch_mm;",
            "    translate([0, 0, band_bottom_mm])",
            "        linear_extrude(height = band_h_mm,",
            "                       twist = twist_deg,",
            "                       scale = band_r_top_mm"
            " / band_r_bottom_mm,",
            "                       slices = coil_turns * 90,"
            " convexity = 10)",
            "            rotate([0, 0, start_deg])",
            "                translate([band_r_bottom_mm"
            " - groove_depth_mm + wire_d_mm / 2, 0])",
            "                    circle(d = wire_d_mm + 0.1, $fn = 24);",
            "}",
            "",
            "module copper_groove_path() {",
            "    color(\"orange\") groove_helix(phase_cu_rad, 1);",
            "}",
            "",
            "module silver_groove_path() {",
            "    color(\"silver\") groove_helix(phase_ag_rad, -1);",
            "}",
            "",
            "module coil_sleeve() {",
            "    difference() {",
            "        cone_shell();",
            "        copper_groove_path();",
            "        silver_groove_path();",
            "    }",
            "}",
            "",
            "module eye_marker() {",
            "    color(\"red\")",
            "    translate([0, 0, z_eye_mm])",
            "        cylinder(h = 0.4,"
            " d = outer_base_d_mm + 4, center = true);",
            "}",
        ]
    lines += [
        "",
        "// The cone is OPEN below the crystal base aperture:",
        "// the crystal bottom is never overconstrained with solid",
        "// plastic; the bottom coupling path stays exposed.",
        "",
        "module base_adapter() {",
        "    // socket ring keyed to the outer base diameter",
        "    difference() {",
        "        cylinder(h = 8, d = outer_base_d_mm + 8);",
        "        translate([0, 0, 2])",
        "            cylinder(h = 6.1, d = outer_base_d_mm + 0.4);",
        "    }",
        "}",
        "",
        "module cap() {",
        "    // slip cap over the outer top diameter",
        "    difference() {",
        "        cylinder(h = 10, d = outer_top_d_mm + 4.4);",
        "        translate([0, 0, 2])",
        "            cylinder(h = 8.1, d = outer_top_d_mm + 0.4);",
        "    }",
        "}",
        "",
        "module led_holder() {",
        "    // 5 mm LED press-fit sleeve (style: porte led reference)",
        "    difference() {",
        "        cylinder(h = 12, d = 10);",
        "        translate([0, 0, 2]) cylinder(h = 10.1, d = 5.2);",
        "    }",
        "}",
        "",
        "module jack_holder() {",
        "    // 3.5 mm jack sleeve (style: jacks-holder reference)",
        "    difference() {",
        "        cube([14, 14, 12], center = true);",
        "        cylinder(h = 12.2, d = 6.2, center = true);",
        "    }",
        "}",
        "",
        "module annular_pickup_ring() {",
        "    // flat pickup surface + annular pickup ring below the",
        "    // open bottom gap (crystal-bottom coupling chain:",
        "    // crystal bottom -> gap -> flat pickup -> annular ring)",
        f"    ring_od = {_ring_dim(coupling, 'od_mm', 'inner_base_d_mm + 6')};",
        f"    ring_id = {_ring_dim(coupling, 'id_mm', 'inner_base_d_mm - 8')};",
        f"    ring_t = {_ring_dim(coupling, 'thickness_mm', '2')};",
        "    difference() {",
        "        cylinder(h = ring_t, d = ring_od);",
        "        translate([0, 0, -0.01])",
        "            cylinder(h = ring_t + 0.02, d = ring_id);",
        "    }",
        "}",
        "",
        "module locker() {",
        "    // quarter-turn locking lug for the base adapter",
        "    intersection() {",
        "        difference() {",
        "            cylinder(h = 4, d = outer_base_d_mm + 8);",
        "            cylinder(h = 4.2, d = outer_base_d_mm + 2);",
        "        }",
        "        cube([outer_base_d_mm + 10, 8, 8], center = true);",
        "    }",
        "}",
        "",
        "// default scene",
        ("coil_sleeve(); eye_marker();" if coil is not None
         else "cone_shell();"),
        "",
    ]
    return "\n".join(lines)


def write_scad(scad: str, out_path: str | Path) -> dict:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(scad, encoding="utf-8")
    return {"path": str(out_path), "sha256": sha256_file(str(out_path)),
            "kind": "scad"}


def export_stl_if_openscad(scad_path: str | Path,
                           stl_path: str | Path) -> dict:
    """Render via the external OpenSCAD CLI when installed; otherwise
    report unavailable (the mesh backend covers direct STL export)."""
    exe = shutil.which("openscad")
    scad_path, stl_path = Path(scad_path), Path(stl_path)
    if exe is None:
        return {"status": "unavailable",
                "reason": "OpenSCAD CLI not installed; use the built-in "
                          "mesh backend STL instead",
                "kind": "stl"}
    stl_path.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run([exe, "-o", str(stl_path), str(scad_path)],
                          capture_output=True, text=True, timeout=600)
    if proc.returncode != 0 or not stl_path.is_file():
        return {"status": "failed", "reason": proc.stderr[-2000:],
                "kind": "stl"}
    return {"status": "rendered", "path": str(stl_path),
            "sha256": sha256_file(str(stl_path)), "kind": "stl"}
