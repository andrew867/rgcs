"""Phryll v2 PDF sheets: crystal compatibility sheet and build sheet
(shared dependency-free PDF writer)."""
from __future__ import annotations

from pathlib import Path

from rgcs_core.provenance import sha256_file, sha256_of_jsonable

from rgcs_desktop.services import pdf_sheets
from rgcs_desktop.services.phryll_v2.cone_generator import ConeDesign
from rgcs_desktop.services.phryll_v2.crystal_profile import CrystalProfile
from rgcs_desktop.services.phryll_v2.reference_assets import (
    compare_reference_to_custom, source_profiles)

COMPAT_BOUNDARY = ("This sheet documents crystal fit geometry and "
                   "generated CAD dimensions. It does not assert "
                   "physical output.")
BUILD_BOUNDARY = ("This build sheet is an engineering plan and "
                  "reproducibility record. Source-language pulse notes "
                  "are recorded, not validated. Predictions are model "
                  "outputs. Measurements decide.")


def export_compatibility_sheet(crystal: CrystalProfile,
                               cone: ConeDesign,
                               out_path: str | Path) -> dict:
    dims = cone.generated_dimensions
    fit = cone.fit_report
    crystal_rows = [
        ("crystal ID", crystal.crystal_id),
        ("length (mm)", crystal.length_mm),
        ("top diameter (mm)", crystal.top_diameter_mm),
        ("base diameter (mm)", crystal.base_diameter_mm),
        ("max body width (mm)", crystal.max_body_width_mm),
        ("facet count", crystal.facet_count),
        ("top angle (deg)", crystal.top_angle_deg),
        ("base angle (deg)", crystal.base_angle_deg),
        ("mass (g)", crystal.mass_g),
        ("Eye z (mm)", crystal.z_eye_mm),
        ("Eye source", crystal.eye_source or None),
    ]
    generated_rows = [
        ("inner top / base diameter (mm)",
         f"{dims['inner_top_diameter_mm']:g} / "
         f"{dims['inner_base_diameter_mm']:g}"),
        ("outer top / base diameter (mm)",
         f"{dims['outer_top_diameter_mm']:g} / "
         f"{dims['outer_base_diameter_mm']:g}"),
        ("height (mm)", dims["height_mm"]),
        ("wall (mm)", dims["wall_thickness_mm"]),
        ("clearance (mm)", dims["clearance_mm"]),
    ]
    clearance_rows = [
        ("fit pass", "PASS" if fit.ok else "FAIL"),
        ("min clearance (mm)", round(fit.min_clearance_mm, 3)),
        ("max clearance (mm)", round(fit.max_clearance_mm, 3)),
        ("stations checked", fit.stations_checked),
    ]
    ref_rows = []
    for ref in source_profiles():
        if ref["kind"] in ("compatibility_text", "mesh_decode"):
            cmp_result = compare_reference_to_custom(
                ref["profile_id"], crystal, dims["clearance_mm"])
            ref_rows.append([
                ref["profile_id"], ref["kind"],
                "fits" if cmp_result.get("fits") else "does not fit",
                cmp_result.get("min_margin_mm"),
            ])
    input_hash = sha256_of_jsonable(
        {"crystal": crystal.raw, "cone": cone.to_json()})
    out_path = pdf_sheets.render_sheet_pdf(
        title="RGCS Phryll v2 — Crystal Compatibility Sheet",
        subtitle=f"Crystal {crystal.crystal_id} · design "
                 f"{cone.design_id}",
        sections=[
            ("Entered dimensions", pdf_sheets.rows_block(crystal_rows)),
            ("Generated custom cone (crystal envelope + clearance)",
             pdf_sheets.rows_block(generated_rows)),
            ("Clearance table", pdf_sheets.rows_block(clearance_rows)),
            ("Source profile comparison (advisory; M2 text and mesh "
             "profiles kept separate)",
             pdf_sheets.table_block(
                 ["profile", "kind", "advisory fit", "min margin (mm)"],
                 ref_rows)),
        ],
        boundary=COMPAT_BOUNDARY,
        out_path=Path(out_path),
        input_hash=input_hash)
    return {"path": str(out_path), "sha256": sha256_file(str(out_path)),
            "kind": "pdf", "input_sha256": input_hash}


def export_build_sheet(crystal: CrystalProfile, cone: ConeDesign,
                       coil: dict, out_path: str | Path,
                       coupling: dict | None = None) -> dict:
    dims = cone.generated_dimensions
    spacing = coil["spacing"]
    eye = coil["eye_alignment"]
    wire = coil["wire"]
    paths = coil["paths"]
    input_hash = sha256_of_jsonable(
        {"crystal": crystal.raw, "cone": cone.to_json(), "coil": coil})
    sections = [
        ("Crystal profile", pdf_sheets.rows_block([
            ("crystal ID", crystal.crystal_id),
            ("length (mm)", crystal.length_mm),
            ("top / base diameter (mm)",
             f"{crystal.top_diameter_mm:g} / "
             f"{crystal.base_diameter_mm:g}"),
            ("Eye z (mm)", crystal.z_eye_mm),
        ])),
        ("Generated parts", pdf_sheets.paragraph(
            "custom cone shell, coil sleeve with grooves, base adapter, "
            "cap, LED holder, jack holder, locker — all generated from "
            "the crystal envelope; no stock mesh scaled")),
        ("Print settings", pdf_sheets.rows_block([
            ("wall (mm)", dims["wall_thickness_mm"]),
            ("clearance (mm)", dims["clearance_mm"]),
            ("print tolerance (mm)",
             cone.fit.get("print_tolerance_mm")),
            ("suggested material", "PLA / PETG"),
        ])),
        ("Coil settings (crossed ±45° multi-start lattice)",
         pdf_sheets.rows_block([
            ("wire", f"{wire.get('wire_gauge', '?')} "
                     f"({wire['wire_diameter_mm']:g} mm)"),
            ("copper", f"{wire.get('copper_material')} — "
                       f"{paths['copper']['handedness']} at "
                       f"+{paths['helix_angle_deg']:g}°"),
            ("silver", f"{wire.get('silver_material')} — "
                       f"{paths['silver']['handedness']} at "
                       f"-{paths['helix_angle_deg']:g}°"),
            ("starts per coil", paths["n_starts_per_coil"]),
            ("rise per turn (mm)", paths["rise_per_turn_mm"]),
            ("turns per strand across band",
             round(paths["turns_per_strand"], 3)),
            ("winding band (mm)",
             f"{paths['band_bottom_mm']:g} – {paths['band_top_mm']:g}"),
            ("lattice crossing", "X centered on the Eye plane"),
            ("electrical contact", "none permitted between coils"),
        ])),
        ("Wire spacing", pdf_sheets.rows_block([
            ("clear gap, perpendicular (mm)", spacing["clear_gap_mm"]),
            ("strand pitch, perpendicular (mm)",
             spacing["groove_pitch_mm"]),
            ("axial strand spacing (mm)",
             spacing["axial_strand_spacing_mm"]),
            ("groove depth (mm)", spacing["groove_depth_mm"]),
        ])),
        ("Coil-to-crystal standoff", pdf_sheets.rows_block([
            ("nearest conductor (mm)",
             spacing["nearest_conductor_standoff_mm"]),
            ("coil centerline (mm)",
             spacing["coil_center_standoff_mm"]),
        ])),
        ("Eye alignment", pdf_sheets.rows_block([
            ("Eye z (mm)", eye["z_eye_mm"]),
            ("crossing plane z (mm)", eye["z_cross_mm"]),
            ("alignment residual (mm)", eye["alignment_error_mm"]),
            ("tolerance (mm)", eye["tolerance_mm"]),
            ("aligned", "PASS" if eye["pass"] else "FAIL"),
        ])),
        ("Crystal-bottom coupling (crystal bottom -> gap -> flat "
         "pickup -> annular ring; bottom stays open)",
         pdf_sheets.rows_block([
             ("coupling mode", (coupling or {}).get("coupling_mode")),
             ("gap (mm)", (coupling or {}).get("gap_mm")),
             ("pickup ring OD / ID (mm)",
              (f"{coupling['pickup_ring']['od_mm']:g} / "
               f"{coupling['pickup_ring']['id_mm']:g}")
              if coupling else None),
             ("O-ring",
              (f"{coupling['o_ring']['material']}, cord "
               f"{coupling['o_ring']['cord_diameter_mm']:g} mm, ID "
               f"{coupling['o_ring']['id_mm']:g} mm, "
               f"{coupling['o_ring']['compression_pct']:g}% at "
               f"{coupling['o_ring']['contact_height_mm']:g} mm")
              if coupling and coupling.get("o_ring")
              else "none (open coupling)"),
             ("bottom aperture", "open — no solid plastic under the "
                                 "crystal base"),
         ])),
        ("Excitation paths (hardware first)", pdf_sheets.rows_block([
            ("1", "photonic / laser"),
            ("2", "magneto-acoustic / pulsed coils"),
            ("3", "mechanical / acoustic"),
            ("4", "electrical / coil"),
            ("intention/focus-only",
             "source-language only — not an implemented mode"),
        ])),
        ("Pulse metadata (source-language, recorded not validated)",
         pdf_sheets.rows_block([
             ("drive", "two coils pulsed alternately at 4096 Hz"),
             ("listed starting voltage",
              "20 V (source-reported; user limits govern)"),
             ("crossing", "copper/silver crossed, no contact"),
         ])),
        ("Assembly notes", pdf_sheets.paragraph(
            "Wind copper clockwise and silver counter-clockwise in "
            "their grooves; verify the crossing plane against the Eye "
            "mark before fixing; check no electrical contact between "
            "coils with a continuity meter.")),
    ]
    out_path = pdf_sheets.render_sheet_pdf(
        title="RGCS Phryll v2 — Build Sheet",
        subtitle=f"Design {cone.design_id} · crystal "
                 f"{crystal.crystal_id}",
        sections=sections,
        boundary=BUILD_BOUNDARY,
        out_path=Path(out_path),
        input_hash=input_hash)
    return {"path": str(out_path), "sha256": sha256_file(str(out_path)),
            "kind": "pdf", "input_sha256": input_hash}
