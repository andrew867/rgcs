"""Phryll v2 end-to-end pipeline: crystal dict in, full export bundle
out. Shared by the UI panel, the demo tool, and integration tests."""
from __future__ import annotations

from pathlib import Path

from rgcs_desktop.services.phryll_v2.bundle_export import (export_bundle,
                                                           verify_bundle)
from rgcs_desktop.services.phryll_v2.coil_sleeve import \
    generate_crossed_coil_paths
from rgcs_desktop.services.phryll_v2.cone_generator import make_cone_design
from rgcs_desktop.services.phryll_v2.crystal_profile import (
    normalize_crystal_profile, validate_eye_coordinate)
from rgcs_desktop.services.phryll_v2.flat_templates import (
    axial_section_svg, top_template_svg, winding_template_dxf)
from rgcs_desktop.services.phryll_v2.mesh_backend import (mesh_stats,
                                                          tessellate_cone_shell,
                                                          write_3mf,
                                                          write_binary_stl)
from rgcs_desktop.services.phryll_v2.openscad_export import (
    export_stl_if_openscad, render_scad, write_scad)
from rgcs_desktop.services.phryll_v2.pdf_exports import (
    export_build_sheet, export_compatibility_sheet)


def generate_full_design(raw_crystal: dict, out_root: str | Path,
                         fit_settings: dict | None = None,
                         coil_settings: dict | None = None) -> dict:
    """Generate cone + coil sleeve + all exports + verified bundle.

    Returns a summary dict: bundle path, verification, key numbers
    (eye residual, standoff, pitch), and per-export receipts.
    """
    out_root = Path(out_root)
    work = out_root / "_work"
    work.mkdir(parents=True, exist_ok=True)

    crystal = normalize_crystal_profile(raw_crystal)
    eye_check = validate_eye_coordinate(crystal)
    cone = make_cone_design(crystal, fit_settings)
    coil = generate_crossed_coil_paths(crystal, cone,
                                       coil_settings or {})

    # CAD
    scad_text = render_scad(cone, coil)
    scad_receipt = write_scad(scad_text, work / "coil_sleeve.scad")
    cone_only_receipt = write_scad(render_scad(cone),
                                   work / "custom_cone.scad")
    triangles = tessellate_cone_shell(cone)
    stl_path = write_binary_stl(triangles, work / "custom_cone.stl")
    mf_path = write_3mf(triangles, work / "custom_cone.3mf")
    stats = mesh_stats(triangles)
    openscad_stl = export_stl_if_openscad(work / "coil_sleeve.scad",
                                          work / "coil_sleeve.stl")

    # flat templates
    axial = axial_section_svg(cone, crystal.z_eye_mm,
                              work / "axial_section.svg")
    top = top_template_svg(cone, crystal.facet_count,
                           work / "top_template.svg")
    winding = winding_template_dxf(coil, cone,
                                   work / "winding_template.dxf")

    # PDFs
    compat = export_compatibility_sheet(crystal, cone,
                                        work / "compatibility_sheet.pdf")
    build = export_build_sheet(crystal, cone, coil,
                               work / "build_sheet.pdf")

    backend_notes = [
        f"mesh backend: built-in tessellation "
        f"({stats['n_triangles']} triangles, watertight shell)",
        f"openscad CLI: {openscad_stl.get('status', 'n/a')} — "
        f"{openscad_stl.get('reason', openscad_stl.get('path', ''))}",
        "3mf: built-in minimal writer",
    ]
    cad_files = {"custom_cone.scad": cone_only_receipt["path"],
                 "coil_sleeve.scad": scad_receipt["path"],
                 "custom_cone.stl": str(stl_path),
                 "custom_cone.3mf": str(mf_path)}
    if openscad_stl.get("status") == "rendered":
        cad_files["coil_sleeve.stl"] = openscad_stl["path"]

    bundle = export_bundle(
        design_id=cone.design_id,
        bundle_root=out_root,
        inputs={"crystal_profile": crystal.raw,
                "coil_settings": coil_settings or {},
                "fit_settings": cone.fit},
        cad=cad_files,
        flat={"axial_section.svg": axial["path"],
              "top_template.svg": top["path"],
              "winding_template.dxf": winding["path"]},
        pdf={"compatibility_sheet.pdf": compat["path"],
             "build_sheet.pdf": build["path"]},
        receipts={"design_receipt": cone.to_json(),
                  "coil_sleeve_receipt": coil,
                  "eye_alignment_receipt": coil["eye_alignment"],
                  "fit_receipt": {
                      "ok": cone.fit_report.ok,
                      "min_clearance_mm":
                          cone.fit_report.min_clearance_mm,
                      "max_clearance_mm":
                          cone.fit_report.max_clearance_mm,
                      "stations_checked":
                          cone.fit_report.stations_checked,
                      "eye_validation_notes": eye_check.reasons}},
        backend_notes=backend_notes)
    check = verify_bundle(bundle)

    return {
        "bundle": bundle,
        "verification": check,
        "cone": cone,
        "coil": coil,
        "mesh_stats": stats,
        "eye_alignment_residual_mm":
            coil["eye_alignment"]["alignment_error_mm"],
        "coil_center_standoff_mm":
            coil["spacing"]["coil_center_standoff_mm"],
        "nearest_conductor_standoff_mm":
            coil["spacing"]["nearest_conductor_standoff_mm"],
        "groove_pitch_mm": coil["spacing"]["groove_pitch_mm"],
        "openscad_status": openscad_stl.get("status"),
    }
