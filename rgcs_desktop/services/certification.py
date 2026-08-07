"""Certification sheet PDF for a validated crystal specimen.

Rules (plan pack 04_MODULE_SPECS/CERTIFICATION_SHEETS.md):
- no sheet without uncertainty fields
- no sheet without claim-boundary text (always embedded)
- absent image -> stated placeholder, never a crash
- unavailable estimates say "unavailable", never zero
- no NaN anywhere on the sheet
"""
from __future__ import annotations

from pathlib import Path

from rgcs_desktop.services import pdf_sheets
from rgcs_desktop.services.design_studio import claim_boundary
from rgcs_desktop.services.export_receipts import make_receipt


class CertificationError(ValueError):
    """Raised when a specimen cannot be certified (missing uncertainty)."""


def render_certification_pdf(specimen: dict, derived: dict,
                             out_path: Path) -> dict:
    """Render the certification sheet; returns the export receipt."""
    unc = specimen.get("uncertainty") or {}
    if unc.get("length_mm") is None:
        raise CertificationError(
            "no certification sheet without uncertainty fields "
            "(uncertainty.length_mm missing)")

    dims = specimen.get("dimensions", {})
    sid = specimen.get("specimen_id", "?")

    if specimen.get("photos") or specimen.get("diagram_files"):
        image_note = ("images on file: "
                      + ", ".join((specimen.get("photos") or [])
                                  + (specimen.get("diagram_files") or [])))
    else:
        image_note = ("diagram placeholder — no image supplied for this "
                      "specimen")

    measured_rows = [
        ("specimen ID", sid),
        ("material family", specimen.get("material_family")),
        ("length (mm)", dims.get("length_mm")),
        ("width (mm)", dims.get("width_mm")),
        ("diameter (mm)", dims.get("diameter_mm")),
        ("facet count", dims.get("facet_count")),
        ("termination angle (deg)", dims.get("termination_angle_deg")),
        ("mass (g)", specimen.get("mass_g")),
        ("measured nodes (mm)",
         ", ".join(f"{n:g}" for n in specimen.get("measured_nodes_mm") or [])
         or None),
    ]
    derived_rows = [
        ("aspect ratio", derived.get("aspect_ratio")),
        ("length/diameter ratio", derived.get("length_to_diameter_ratio")),
        ("termination angle status",
         derived.get("termination_angle_status")),
        ("volume estimate (cm^3)", derived.get("volume_estimate_cm3")),
        ("volume model", derived.get("volume_model")),
        ("density (g/cm^3)", derived.get("density_g_cm3")),
        ("density check", derived.get("density_check")),
    ]
    mode_rows = [
        ("axial half-wave (Hz)", derived.get("axial_half_wave_hz")),
        ("mode model", derived.get("mode_model")),
    ]
    uncertainty_rows = [
        ("length uncertainty (mm)", unc.get("length_mm")),
        ("width uncertainty (mm)", unc.get("width_mm")),
        ("angle uncertainty (deg)", unc.get("angle_deg")),
    ]
    prov = specimen.get("provenance", {})
    prov_rows = ([(k, v) for k, v in sorted(prov.items())]
                 + [("supplier", specimen.get("supplier")),
                    ("operator", specimen.get("operator"))])

    input_hash = pdf_sheets.sheet_input_hash(
        {"specimen": specimen, "derived": derived})
    sections = [
        ("Photograph / diagram", pdf_sheets.paragraph(image_note)),
        ("Entered measurements", pdf_sheets.rows_block(measured_rows)),
        ("Derived geometry", pdf_sheets.rows_block(derived_rows)),
        ("Mode estimates (model outputs)", pdf_sheets.rows_block(mode_rows)),
        ("Uncertainty", pdf_sheets.rows_block(uncertainty_rows)),
        ("Provenance", pdf_sheets.rows_block(prov_rows)),
    ]
    missing = [k for k in ("termination_angle_deg", "facet_count")
               if dims.get(k) is None]
    if specimen.get("mass_g") is None:
        missing.append("mass_g")
    if missing:
        sections.append(("Missing measurements", pdf_sheets.paragraph(
            "needs measurement: " + ", ".join(missing))))

    out_path = pdf_sheets.render_sheet_pdf(
        title="RGCS Crystal Certification Sheet",
        subtitle=f"Specimen {sid}",
        sections=sections,
        boundary=claim_boundary("certification"),
        out_path=Path(out_path),
        input_hash=input_hash)

    return make_receipt(
        inputs={"specimen": specimen, "derived": derived},
        outputs=[out_path],
        classification=str(specimen.get("classification", "MEASURED_INPUT")),
        object_id=f"CERT-{sid}",
        source_ids=[sid],
        boundary=claim_boundary("certification"))
