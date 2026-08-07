"""Design Studio export integration: the golden path produces
JSON/PDF/SVG/SCAD artifacts with receipts, checksums, and claim
boundaries. PDF text is extracted with pypdf where available."""
import json
from pathlib import Path

import pytest

from rgcs_desktop.services.annular_ring import (
    render_engineering_pdf, render_ring_svg, write_active_mask_csv,
    write_phase_map_csv)
from rgcs_desktop.services.certification import (
    CertificationError, render_certification_pdf)
from rgcs_desktop.services.coil_pulse import render_coil_pulse_pdf
from rgcs_desktop.services.crystal_validator import (
    derive_crystal_geometry, export_specimen_json, make_crystal_diagram,
    validate_specimen)
from rgcs_desktop.services.export_receipts import (
    verify_manifest, write_manifest, write_receipt)
from rgcs_desktop.services.phyrll_generator import (
    derive_holder_geometry, export_scad, export_stl_if_available,
    render_build_sheet_pdf)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "design_studio"

pypdf = pytest.importorskip("pypdf", reason="pypdf needed for PDF text checks")


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def pdf_text(path: Path) -> str:
    reader = pypdf.PdfReader(str(path))
    raw = "\n".join(page.extract_text() or "" for page in reader.pages)
    # collapse line wraps so phrase assertions span wrapped lines
    return " ".join(raw.split())


@pytest.fixture()
def bundle(tmp_path):
    return tmp_path / "bundle"


def test_certification_pdf_from_fixture(bundle):
    spec = load("crystal_with_nodes.json")
    assert validate_specimen(spec).ok
    derived = derive_crystal_geometry(spec)
    receipt = render_certification_pdf(spec, derived,
                                       bundle / "pdf" / "cert.pdf")
    text = pdf_text(bundle / "pdf" / "cert.pdf")
    assert spec["specimen_id"] in text
    assert "Claim boundary" in text
    assert "does not by itself validate" in text
    assert receipt["input_sha256"][:16] in text     # receipt hash on sheet
    assert "NaN" not in text
    # full fixture: mode estimate is present, not "unavailable"
    assert "axial half-wave (Hz) 26000" in text
    assert "mode model f = v/(2L)" in text


def test_certification_missing_image_states_placeholder(bundle):
    spec = load("crystal_valid_minimal.json")
    derived = derive_crystal_geometry(spec)
    render_certification_pdf(spec, derived, bundle / "pdf" / "min.pdf")
    text = pdf_text(bundle / "pdf" / "min.pdf")
    assert "no image supplied" in text
    # minimal specimen: mode estimate must say unavailable, never zero
    assert "unavailable" in text
    assert "NaN" not in text


def test_certification_refused_without_uncertainty(bundle):
    spec = load("crystal_valid_minimal.json")
    spec["uncertainty"] = {}
    with pytest.raises(CertificationError):
        render_certification_pdf(spec, {}, bundle / "pdf" / "x.pdf")


def test_phyrll_build_sheet_includes_print_settings(bundle):
    spec = load("crystal_with_nodes.json")
    design = load("phryll_generator_basic.json")
    design["holder_geometry"] = derive_holder_geometry(
        spec, {"clearance_mm": design["clearance_mm"],
               "wall_thickness_mm": design["wall_thickness_mm"],
               "base_thickness_mm": design["base_thickness_mm"],
               "coil_channel": design["coil_channels"]})
    scad_receipt = export_scad(design, bundle / "geometry" / "holder.scad")
    design["exports"] = {"SCAD": "holder.scad"}
    receipt = render_build_sheet_pdf(design, bundle / "pdf" / "build.pdf")
    text = pdf_text(bundle / "pdf" / "build.pdf")
    assert "Print settings" in text
    assert "nozzle" in text
    assert "Measurements decide." in text           # build-sheet boundary
    assert design["design_id"] in text
    stl = export_stl_if_available(bundle / "geometry" / "holder.scad",
                                  bundle / "geometry" / "holder.stl")
    assert stl["status"] in ("rendered", "unavailable")
    assert scad_receipt["outputs"] and receipt["outputs"]


def test_coil_pulse_pdf_has_model_output_boundary(bundle):
    design = load("coil_pulse_925.json")
    render_coil_pulse_pdf(design, bundle / "pdf" / "coil.pdf")
    text = pdf_text(bundle / "pdf" / "coil.pdf")
    assert "3171" in text and "5021" in text        # 925 sidebands
    assert "model outputs" in text
    assert "Measurements decide." in text
    assert "NaN" not in text


def test_ring_engineering_sheet(bundle):
    design = load("annular_ring_37cell.json")
    render_ring_svg(design, bundle / "geometry" / "ring.svg")
    write_phase_map_csv(design, bundle / "ring" / "phase.csv")
    write_active_mask_csv(design, bundle / "ring" / "mask.csv")
    render_engineering_pdf(design, bundle / "pdf" / "ring.pdf")
    text = pdf_text(bundle / "pdf" / "ring.pdf")
    assert "37" in text
    assert "not evidence of physical performance" in text
    assert "3171" in text                           # sidebands from drive


def test_bundle_manifest_checksums(bundle):
    spec = load("crystal_with_nodes.json")
    derived = derive_crystal_geometry(spec)
    export_specimen_json(spec, derived, bundle / "specimen" / "s.json")
    make_crystal_diagram(spec, bundle / "geometry" / "s.svg")
    receipt = render_certification_pdf(spec, derived,
                                       bundle / "pdf" / "cert.pdf")
    write_receipt(receipt, bundle / "specimen" / "s.receipt.json")
    manifest_path = write_manifest(bundle, [receipt])
    assert manifest_path.name == "MANIFEST.json"

    check = verify_manifest(bundle)
    assert check["ok"], check
    assert check["n_members"] >= 4

    # recorded output hash matches the actual PDF hash in CHECKSUMS
    checks = json.loads((bundle / "CHECKSUMS.json").read_text())
    assert checks["pdf/cert.pdf"] == receipt["outputs"][0]["sha256"]

    # tamper -> verification fails
    (bundle / "specimen" / "s.json").write_text("{}", encoding="utf-8")
    assert not verify_manifest(bundle)["ok"]
