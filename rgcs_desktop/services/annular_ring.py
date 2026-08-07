"""Annular Ring Designer services: exact cell geometry, mask
validation, probe layout, SVG/SCAD/CSV exports, and the engineering
sheet PDF.

Cell angles are computed with exact rational arithmetic so N cells
always close the full ring with zero residual — the 37-cell default
fixture closes exactly by construction, and tests assert it.
"""
from __future__ import annotations

import csv
import math
from fractions import Fraction
from pathlib import Path

from rgcs_desktop.services import pdf_sheets
from rgcs_desktop.services.coil_pulse import sidebands
from rgcs_desktop.services.design_studio import MODEL_OUTPUT, claim_boundary
from rgcs_desktop.services.export_receipts import make_receipt


class RingError(ValueError):
    """A refused ring parameter combination (with the reason)."""


def derive_ring_cells(od_mm: float, id_mm: float,
                      cell_count: int) -> list[dict]:
    """Per-cell geometry. Angles carry exact Fraction spans (degrees)
    plus float renderings; the spans sum to exactly 360."""
    if od_mm <= 0 or id_mm <= 0:
        raise RingError("OD and ID must be > 0")
    if id_mm >= od_mm:
        raise RingError(f"ID {id_mm} mm must be smaller than OD {od_mm} mm")
    n = int(cell_count)
    if n < 3:
        raise RingError(f"cell count must be >= 3, got {cell_count}")

    span = Fraction(360, n)
    cells = []
    for i in range(n):
        start = span * i
        end = span * (i + 1)
        cells.append({
            "index": i,
            "start_deg_exact": start,
            "end_deg_exact": end,
            "span_deg_exact": span,
            "start_deg": float(start),
            "end_deg": float(end),
            "centroid_deg": float(start + span / 2),
        })
    assert sum(c["span_deg_exact"] for c in cells) == 360
    return cells


def validate_active_mask(mask: list[bool], cell_count: int) -> None:
    """Refuse masks that don't line up with the cell count."""
    if len(mask) != int(cell_count):
        raise RingError(
            f"active mask has {len(mask)} entries for {cell_count} cells; "
            f"the mask must name every cell exactly once")
    for i, v in enumerate(mask):
        if not isinstance(v, bool):
            raise RingError(f"mask entry {i} is {type(v).__name__}, "
                            f"expected bool")


def active_cells(design: dict) -> list[int]:
    """Cell indices that are active: masked true and not blanked."""
    mask = design["active_mask"]
    validate_active_mask(mask, design["cell_count"])
    blanked = set(design.get("blanked_cells") or [])
    return [i for i, on in enumerate(mask) if on and i not in blanked]


def _pol(cx: float, cy: float, r: float, deg: float) -> tuple[float, float]:
    rad = math.radians(deg - 90.0)  # 0° at 12 o'clock
    return cx + r * math.cos(rad), cy + r * math.sin(rad)


def render_ring_svg(design: dict, out_path: Path) -> dict:
    """Annulus diagram: labelled sectors, active/blanked fill, probe
    markers. Deterministic plain-XML SVG."""
    od = float(design["od_mm"])
    idm = float(design["id_mm"])
    n = int(design["cell_count"])
    cells = derive_ring_cells(od, idm, n)
    mask = design["active_mask"]
    validate_active_mask(mask, n)
    blanked = set(design.get("blanked_cells") or [])
    probes = (design.get("probe_plan") or {}).get("probes", [])

    scale = 640.0 / od
    r_out = od * scale / 2
    r_in = idm * scale / 2
    c = r_out + 60.0
    size = 2 * c

    p = ['<svg xmlns="http://www.w3.org/2000/svg" '
         f'width="{size:.0f}" height="{size:.0f}" '
         'font-family="sans-serif" font-size="11">',
         f'<title>annular ring {design["design_id"]}</title>']
    for cell in cells:
        i = cell["index"]
        a0, a1 = cell["start_deg"], cell["end_deg"]
        x0o, y0o = _pol(c, c, r_out, a0)
        x1o, y1o = _pol(c, c, r_out, a1)
        x1i, y1i = _pol(c, c, r_in, a1)
        x0i, y0i = _pol(c, c, r_in, a0)
        if i in blanked:
            fill = "#d0d0d0"
        elif mask[i]:
            fill = "#bcd7f0"
        else:
            fill = "#f6e3c1"
        p.append(
            f'<path d="M {x0o:.2f} {y0o:.2f} '
            f'A {r_out:.2f} {r_out:.2f} 0 0 1 {x1o:.2f} {y1o:.2f} '
            f'L {x1i:.2f} {y1i:.2f} '
            f'A {r_in:.2f} {r_in:.2f} 0 0 0 {x0i:.2f} {y0i:.2f} Z" '
            f'fill="{fill}" stroke="#333" stroke-width="1"/>')
        xm, ym = _pol(c, c, (r_out + r_in) / 2, cell["centroid_deg"])
        p.append(f'<text x="{xm:.1f}" y="{ym:.1f}" text-anchor="middle" '
                 f'dominant-baseline="middle">{i}</text>')
    for probe in probes:
        cell = cells[int(probe["cell"]) % n]
        xp, yp = _pol(c, c, r_out + 18, cell["centroid_deg"])
        p.append(f'<circle cx="{xp:.1f}" cy="{yp:.1f}" r="6" '
                 'fill="none" stroke="#b00020" stroke-width="2"/>')
        p.append(f'<text x="{xp:.1f}" y="{yp - 10:.1f}" '
                 f'text-anchor="middle" fill="#b00020">'
                 f'{probe.get("label", "?")}</text>')
    p.append(f'<text x="{c:.1f}" y="{c - 8:.1f}" text-anchor="middle" '
             f'font-size="14" font-weight="bold">'
             f'{design["design_id"]}</text>')
    p.append(f'<text x="{c:.1f}" y="{c + 12:.1f}" text-anchor="middle">'
             f'OD {od:g} mm · ID {idm:g} mm · {n} cells</text>')
    p.append('</svg>')

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(p), encoding="utf-8")
    return make_receipt(inputs=design, outputs=[out_path],
                        classification=MODEL_OUTPUT,
                        object_id=design["design_id"],
                        boundary=claim_boundary("ring_design"))


def render_ring_scad(design: dict) -> str:
    """Deterministic OpenSCAD source: annulus plate with blanked-cell
    sector cutouts marked as shallow recesses."""
    od = float(design["od_mm"])
    idm = float(design["id_mm"])
    n = int(design["cell_count"])
    blanked = sorted(set(design.get("blanked_cells") or []))
    lines = [
        f"// RGCS annular ring — design {design['design_id']}",
        "// generated by rgcs_desktop.services.annular_ring "
        "(deterministic)",
        "// model output — an engineering plan, not a measurement",
        "",
        f"od = {od:.3f};",
        f"id = {idm:.3f};",
        "thickness = 3.0;",
        f"cells = {n};",
        "",
        "difference() {",
        "    cylinder(h = thickness, d = od, $fn = 360);",
        "    translate([0, 0, -0.01])",
        "        cylinder(h = thickness + 0.02, d = id, $fn = 360);",
    ]
    for b in blanked:
        angle = 360.0 * b / n
        lines += [
            f"    // blanked cell {b}: shallow marker recess",
            f"    rotate([0, 0, {angle:.4f}])",
            f"        translate([id / 2 + (od - id) / 4, 0, "
            f"thickness - 0.6])",
            f"            cylinder(h = 0.7, d = 4, $fn = 32);",
        ]
    lines.append("}")
    return "\n".join(lines) + "\n"


def write_phase_map_csv(design: dict, out_path: Path) -> Path:
    """Per-cell phase map: centroid angle and the phase offset assigned
    by even distribution of the modulation key across active cells."""
    cells = derive_ring_cells(design["od_mm"], design["id_mm"],
                              design["cell_count"])
    act = active_cells(design)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["cell", "centroid_deg", "state", "phase_deg"])
        for cell in cells:
            i = cell["index"]
            if i in act:
                state = "active"
                phase = 360.0 * act.index(i) / len(act)
            elif i in set(design.get("blanked_cells") or []):
                state, phase = "blanked", ""
            else:
                state, phase = "inactive", ""
            w.writerow([i, f"{cell['centroid_deg']:.6f}", state,
                        f"{phase:.6f}" if phase != "" else ""])
    return out_path


def write_active_mask_csv(design: dict, out_path: Path) -> Path:
    validate_active_mask(design["active_mask"], design["cell_count"])
    blanked = set(design.get("blanked_cells") or [])
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["cell", "active", "blanked"])
        for i, on in enumerate(design["active_mask"]):
            w.writerow([i, int(on), int(i in blanked)])
    return out_path


def render_engineering_pdf(design: dict, out_path: Path) -> dict:
    """Engineering sheet: geometry, masks, probe plan, sideband table,
    claim boundary, hashes."""
    n = int(design["cell_count"])
    act = active_cells(design)
    blanked = sorted(set(design.get("blanked_cells") or []))
    drive = design.get("drive") or {}

    geo_rows = [
        ("design ID", design["design_id"]),
        ("outer diameter (mm)", design["od_mm"]),
        ("inner diameter (mm)", design["id_mm"]),
        ("annulus width (mm)",
         (float(design["od_mm"]) - float(design["id_mm"])) / 2.0),
        ("cell count", n),
        ("cell span (deg)", 360.0 / n),
        ("active cells", len(act)),
        ("blanked cells", ", ".join(str(b) for b in blanked) or "none"),
        ("material", design.get("material")),
    ]
    probe_rows = [[pr.get("label", "?"), pr.get("cell")]
                  for pr in (design.get("probe_plan") or {})
                  .get("probes", [])]
    sections = [
        ("Ring geometry (derived, closes exactly)",
         pdf_sheets.rows_block(geo_rows)),
        ("Probe plan",
         pdf_sheets.table_block(["probe", "cell"], probe_rows)
         if probe_rows else pdf_sheets.paragraph("no probes planned")),
    ]
    base = drive.get("base_hz")
    key = drive.get("modulation_key_hz")
    if base and key is not None:
        sb_rows = [[r["order"], r["lower_hz"], r["upper_hz"]]
                   for r in sidebands(base, key)]
        sections.append(
            (f"Sideband table (base {base:g} Hz ± n · {key:g} Hz)",
             pdf_sheets.table_block(["order", "lower (Hz)", "upper (Hz)"],
                                   sb_rows)))

    input_hash = pdf_sheets.sheet_input_hash(design)
    out_path = pdf_sheets.render_sheet_pdf(
        title="RGCS Engineering Sheet — Annular Ring Prototype",
        subtitle=f"Design {design['design_id']} · {n} cells",
        sections=sections,
        boundary=claim_boundary("ring_design"),
        out_path=Path(out_path),
        input_hash=input_hash)
    return make_receipt(
        inputs=design, outputs=[out_path], classification=MODEL_OUTPUT,
        object_id=design["design_id"],
        boundary=claim_boundary("ring_design"))
