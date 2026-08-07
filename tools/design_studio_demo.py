#!/usr/bin/env python3
"""Generate the Design Studio demo artifact set (release checklist).

Writes to docs/assets/design-studio/demo/ by default:
    crystal_certificate_demo.pdf
    crystal_geometry_demo.svg
    phyrll_generator_demo.scad
    phyrll_generator_build_sheet_demo.pdf
    coil_pulse_build_sheet_demo.pdf
    annular_ring_demo.svg
    annular_ring_engineering_sheet_demo.pdf
    export_bundle_demo.zip   (bundle dir + MANIFEST + CHECKSUMS zipped)

Everything is produced by the same services the app uses; every sheet
carries its claim boundary. Run: python tools/design_studio_demo.py
"""
from __future__ import annotations

import json
import shutil
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from rgcs_desktop.services.annular_ring import (            # noqa: E402
    render_engineering_pdf, render_ring_scad, render_ring_svg,
    write_active_mask_csv, write_phase_map_csv)
from rgcs_desktop.services.certification import (           # noqa: E402
    render_certification_pdf)
from rgcs_desktop.services.coil_pulse import (              # noqa: E402
    render_coil_pulse_pdf)
from rgcs_desktop.services.crystal_validator import (       # noqa: E402
    derive_crystal_geometry, export_specimen_json, make_crystal_diagram,
    validate_specimen)
from rgcs_desktop.services.export_receipts import (         # noqa: E402
    write_manifest, write_receipt)
from rgcs_desktop.services.phyrll_generator import (        # noqa: E402
    derive_holder_geometry, export_scad, render_build_sheet_pdf)

FIXTURES = REPO / "tests" / "fixtures" / "design_studio"


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def main(out_dir: Path | None = None) -> int:
    out = out_dir or (REPO / "docs" / "assets" / "design-studio" / "demo")
    out.mkdir(parents=True, exist_ok=True)
    bundle = out / "_bundle"
    if bundle.exists():
        shutil.rmtree(bundle)
    for sub in ("specimen", "designs", "pulse", "ring", "pdf", "geometry"):
        (bundle / sub).mkdir(parents=True, exist_ok=True)
    receipts = []

    def keep(src: Path, sub: str) -> None:
        shutil.copy(src, bundle / sub / src.name)

    # 1. crystal certification
    spec = load("crystal_with_nodes.json")
    result = validate_specimen(spec)
    assert result.ok, result.errors
    derived = derive_crystal_geometry(spec)
    export_specimen_json(spec, derived,
                         bundle / "specimen" / "specimen_demo.json")
    make_crystal_diagram(spec, out / "crystal_geometry_demo.svg")
    keep(out / "crystal_geometry_demo.svg", "geometry")
    receipt = render_certification_pdf(
        spec, derived, out / "crystal_certificate_demo.pdf")
    keep(out / "crystal_certificate_demo.pdf", "pdf")
    write_receipt(receipt,
                  bundle / "specimen" / "specimen_demo.receipt.json")
    receipts.append(receipt)
    print("certification sheet:", out / "crystal_certificate_demo.pdf")

    # 2. phyrll generator holder
    design = load("phryll_generator_basic.json")
    design["holder_geometry"] = derive_holder_geometry(
        spec, {"clearance_mm": design["clearance_mm"],
               "wall_thickness_mm": design["wall_thickness_mm"],
               "base_thickness_mm": design["base_thickness_mm"],
               "coil_channel": design["coil_channels"]})
    scad_receipt = export_scad(design, out / "phyrll_generator_demo.scad")
    keep(out / "phyrll_generator_demo.scad", "designs")
    design["exports"] = {"SCAD": "phyrll_generator_demo.scad"}
    build_receipt = render_build_sheet_pdf(
        design, out / "phyrll_generator_build_sheet_demo.pdf")
    keep(out / "phyrll_generator_build_sheet_demo.pdf", "pdf")
    receipts += [scad_receipt, build_receipt]
    print("phyrll SCAD + build sheet:", out / "phyrll_generator_demo.scad")

    # 3. coil / pulse
    cp = load("coil_pulse_925.json")
    cp_receipt = render_coil_pulse_pdf(
        cp, out / "coil_pulse_build_sheet_demo.pdf")
    keep(out / "coil_pulse_build_sheet_demo.pdf", "pulse")
    receipts.append(cp_receipt)
    print("coil/pulse build sheet:",
          out / "coil_pulse_build_sheet_demo.pdf")

    # 4. annular ring
    ring = load("annular_ring_37cell.json")
    ring_svg_receipt = render_ring_svg(ring, out / "annular_ring_demo.svg")
    keep(out / "annular_ring_demo.svg", "ring")
    (bundle / "ring" / "annular_ring_demo.scad").write_text(
        render_ring_scad(ring), encoding="utf-8")
    write_phase_map_csv(ring, bundle / "ring" / "phase_map_demo.csv")
    write_active_mask_csv(ring, bundle / "ring" / "active_mask_demo.csv")
    ring_receipt = render_engineering_pdf(
        ring, out / "annular_ring_engineering_sheet_demo.pdf")
    keep(out / "annular_ring_engineering_sheet_demo.pdf", "pdf")
    receipts += [ring_svg_receipt, ring_receipt]
    print("ring pack:", out / "annular_ring_engineering_sheet_demo.pdf")

    # 5. bundle manifest + zip
    write_manifest(bundle, receipts)
    zip_path = out / "export_bundle_demo.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(bundle.rglob("*")):
            if p.is_file():
                zf.write(p, p.relative_to(bundle).as_posix())
    shutil.rmtree(bundle)
    print("export bundle:", zip_path)
    print("done:", len(list(out.iterdir())), "demo artifacts in", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
