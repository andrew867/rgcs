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
from rgcs_desktop.services.phryll_v2.mesh_backend import (
    mesh_stats, tessellate_coil_sleeve, tessellate_cone_shell, write_3mf,
    write_binary_stl)
from rgcs_desktop.services.phryll_v2.openscad_export import (
    export_stl_if_openscad, render_scad, write_scad)
from rgcs_desktop.services.phryll_v2.pdf_exports import (
    export_build_sheet, export_compatibility_sheet)


def _design_stack(raw_crystal: dict,
                  fit_settings: dict | None,
                  coil_settings: dict | None,
                  coupling_settings: dict | None):
    """Shared normalize -> cone -> coupling -> coil prefix."""
    crystal = normalize_crystal_profile(raw_crystal)
    eye_check = validate_eye_coordinate(crystal)
    cone = make_cone_design(crystal, fit_settings)
    from rgcs_desktop.services.phryll_v2.bottom_coupling import \
        design_bottom_coupling
    coupling = design_bottom_coupling(crystal, coupling_settings)
    cone.bottom_coupling = coupling
    coil = generate_crossed_coil_paths(crystal, cone,
                                       coil_settings or {})
    return crystal, eye_check, cone, coupling, coil


def generate_full_design(raw_crystal: dict, out_root: str | Path,
                         fit_settings: dict | None = None,
                         coil_settings: dict | None = None,
                         coupling_settings: dict | None = None,
                         openscad_timeout_s: float = 120.0) -> dict:
    """Generate cone + coil sleeve + all exports + verified bundle.

    Returns a summary dict: bundle path, verification, key numbers
    (eye residual, standoff, pitch), and per-export receipts.
    """
    out_root = Path(out_root)
    work = out_root / "_work"
    work.mkdir(parents=True, exist_ok=True)

    crystal, eye_check, cone, coupling, coil = _design_stack(
        raw_crystal, fit_settings, coil_settings, coupling_settings)

    # CAD
    scad_text = render_scad(cone, coil, coupling)
    scad_receipt = write_scad(scad_text, work / "coil_sleeve.scad")
    cone_only_receipt = write_scad(render_scad(cone),
                                   work / "custom_cone.scad")
    triangles = tessellate_cone_shell(cone)
    stl_path = write_binary_stl(triangles, work / "custom_cone.stl")
    mf_path = write_3mf(triangles, work / "custom_cone.3mf")
    stats = mesh_stats(triangles)
    # grooved coil sleeve: continuous helical wire slots, built-in
    sleeve_tris = tessellate_coil_sleeve(cone, coil)
    sleeve_stl = write_binary_stl(sleeve_tris,
                                  work / "coil_sleeve.stl")
    sleeve_3mf = write_3mf(sleeve_tris, work / "coil_sleeve.3mf")
    sleeve_stats = mesh_stats(sleeve_tris)
    openscad_stl = export_stl_if_openscad(
        work / "coil_sleeve.scad", work / "coil_sleeve_openscad.stl",
        timeout_s=openscad_timeout_s)

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
                               work / "build_sheet.pdf",
                               coupling=coupling)

    backend_notes = [
        f"mesh backend: built-in tessellation "
        f"({stats['n_triangles']} triangles cone shell; "
        f"{sleeve_stats['n_triangles']} triangles grooved coil sleeve "
        f"with continuous helical wire slots)",
        f"openscad CLI: {openscad_stl.get('status', 'n/a')} — "
        f"{openscad_stl.get('reason', openscad_stl.get('path', ''))}",
        "3mf: built-in minimal writer",
    ]
    cad_files = {"custom_cone.scad": cone_only_receipt["path"],
                 "coil_sleeve.scad": scad_receipt["path"],
                 "custom_cone.stl": str(stl_path),
                 "custom_cone.3mf": str(mf_path),
                 "coil_sleeve.stl": str(sleeve_stl),
                 "coil_sleeve.3mf": str(sleeve_3mf)}
    if openscad_stl.get("status") == "rendered":
        cad_files["coil_sleeve_openscad.stl"] = openscad_stl["path"]

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
                  "bottom_coupling_receipt": coupling,
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
        "sleeve_mesh_stats": sleeve_stats,
        "eye_alignment_residual_mm":
            coil["eye_alignment"]["alignment_error_mm"],
        "coil_center_standoff_mm":
            coil["spacing"]["coil_center_standoff_mm"],
        "nearest_conductor_standoff_mm":
            coil["spacing"]["nearest_conductor_standoff_mm"],
        "groove_pitch_mm": coil["spacing"]["groove_pitch_mm"],
        "openscad_status": openscad_stl.get("status"),
    }


# Single-artifact export: one file per call, never a bundle.
SINGLE_ARTIFACT_KINDS = (
    "cone_stl", "cone_3mf", "cone_scad",
    "sleeve_stl", "sleeve_3mf", "sleeve_scad",
    "axial_section_svg", "top_template_svg", "winding_template_dxf",
    "build_pdf", "compatibility_pdf", "receipt_json",
)

_ARTIFACT_FILENAMES = {
    "cone_stl": "custom_cone.stl",
    "cone_3mf": "custom_cone.3mf",
    "cone_scad": "custom_cone.scad",
    "sleeve_stl": "coil_sleeve.stl",
    "sleeve_3mf": "coil_sleeve.3mf",
    "sleeve_scad": "coil_sleeve.scad",
    "axial_section_svg": "axial_section.svg",
    "top_template_svg": "top_template.svg",
    "winding_template_dxf": "winding_template.dxf",
    "build_pdf": "build_sheet.pdf",
    "compatibility_pdf": "compatibility_sheet.pdf",
    "receipt_json": "design_receipt.json",
}


def export_single_artifact(raw_crystal: dict, out_dir: str | Path,
                           kind: str,
                           fit_settings: dict | None = None,
                           coil_settings: dict | None = None,
                           coupling_settings: dict | None = None) -> dict:
    """Export exactly one artifact for the design.

    Runs the same normalize -> cone -> coupling -> coil stack as the
    full pipeline, then writes only the requested file into ``out_dir``.
    Returns {"kind", "path", "sha256", "design_id"}.
    """
    if kind not in SINGLE_ARTIFACT_KINDS:
        raise ValueError(
            f"unknown artifact kind {kind!r}; "
            f"expected one of {', '.join(SINGLE_ARTIFACT_KINDS)}")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    crystal, eye_check, cone, coupling, coil = _design_stack(
        raw_crystal, fit_settings, coil_settings, coupling_settings)
    name = _ARTIFACT_FILENAMES[kind]
    target = out_dir / f"{cone.design_id}_{name}"

    if kind in ("cone_stl", "cone_3mf"):
        triangles = tessellate_cone_shell(cone)
        path = (write_binary_stl(triangles, target) if kind == "cone_stl"
                else write_3mf(triangles, target))
    elif kind in ("sleeve_stl", "sleeve_3mf"):
        triangles = tessellate_coil_sleeve(cone, coil)
        path = (write_binary_stl(triangles, target)
                if kind == "sleeve_stl" else write_3mf(triangles, target))
    elif kind == "cone_scad":
        path = Path(write_scad(render_scad(cone), target)["path"])
    elif kind == "sleeve_scad":
        path = Path(write_scad(render_scad(cone, coil, coupling),
                               target)["path"])
    elif kind == "axial_section_svg":
        path = Path(axial_section_svg(cone, crystal.z_eye_mm,
                                      target)["path"])
    elif kind == "top_template_svg":
        path = Path(top_template_svg(cone, crystal.facet_count,
                                     target)["path"])
    elif kind == "winding_template_dxf":
        path = Path(winding_template_dxf(coil, cone, target)["path"])
    elif kind == "build_pdf":
        path = Path(export_build_sheet(crystal, cone, coil, target,
                                       coupling=coupling)["path"])
    elif kind == "compatibility_pdf":
        path = Path(export_compatibility_sheet(crystal, cone,
                                               target)["path"])
    else:  # receipt_json
        import json
        receipt = {
            "design": cone.to_json(),
            "coil_sleeve": coil,
            "bottom_coupling": coupling,
            "eye_alignment": coil["eye_alignment"],
            "fit": {"ok": cone.fit_report.ok,
                    "min_clearance_mm": cone.fit_report.min_clearance_mm,
                    "max_clearance_mm": cone.fit_report.max_clearance_mm,
                    "stations_checked": cone.fit_report.stations_checked,
                    "eye_validation_notes": eye_check.reasons},
        }
        target.write_text(json.dumps(receipt, indent=2, sort_keys=True,
                                     default=str), encoding="utf-8")
        path = target

    import hashlib
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"kind": kind, "path": str(path), "sha256": digest,
            "design_id": cone.design_id}
