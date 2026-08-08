"""Phryll v2 golden path: demo crystal -> full export bundle with
verified checksums and PDF content checks (plan pack 09_TESTS)."""
import json
from pathlib import Path

import pytest

from rgcs_desktop.services.phryll_v2.bundle_export import verify_bundle
from rgcs_desktop.services.phryll_v2.pipeline import generate_full_design

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "phryll_v2"

pypdf = pytest.importorskip("pypdf", reason="pypdf needed for PDF checks")


def pdf_text(path: Path) -> str:
    reader = pypdf.PdfReader(str(path))
    return " ".join(" ".join((page.extract_text() or "").split())
                    for page in reader.pages)


@pytest.fixture(scope="module")
def result(tmp_path_factory):
    raw = json.loads((FIXTURES / "crystal_profile_example.json")
                     .read_text(encoding="utf-8"))
    out = tmp_path_factory.mktemp("phv2")
    return generate_full_design(
        raw, out,
        fit_settings={"clearance_mm": 0.66, "wall_thickness_mm": 1.8},
        coil_settings={"wire_gauge": "AWG28"})


def test_bundle_layout_and_checksums(result):
    bundle = result["bundle"]
    for sub in ("inputs", "cad", "flat", "pdf", "receipts", "logs"):
        assert (bundle / sub).is_dir()
    assert (bundle / "MANIFEST.json").is_file()
    assert (bundle / "CHECKSUMS.sha256").is_file()
    assert result["verification"]["ok"]
    assert result["verification"]["n_members"] >= 13

    # tamper detection
    (bundle / "inputs" / "crystal_profile.json").write_text(
        "{}", encoding="utf-8")
    assert not verify_bundle(bundle)["ok"]


def test_cad_exports_present(result):
    cad = result["bundle"] / "cad"
    assert (cad / "custom_cone.scad").is_file()
    assert (cad / "coil_sleeve.scad").is_file()
    assert (cad / "custom_cone.stl").stat().st_size > 5000
    assert (cad / "custom_cone.3mf").stat().st_size > 1000


def test_flat_templates_present(result):
    flat = result["bundle"] / "flat"
    for name in ("axial_section.svg", "top_template.svg",
                 "winding_template.dxf"):
        assert (flat / name).is_file(), name


def test_key_numbers(result):
    assert result["eye_alignment_residual_mm"] == 0.0
    assert result["coil_center_standoff_mm"] == pytest.approx(2.375)
    assert result["groove_pitch_mm"] == pytest.approx(0.99)
    assert result["openscad_status"] in ("rendered", "unavailable",
                                         "failed", "timeout")


def test_build_sheet_content(result):
    """Skeleton T007: crystal inputs, clearances, wire pitch, Eye
    alignment on the build sheet."""
    text = pdf_text(result["bundle"] / "pdf" / "build_sheet.pdf")
    assert "CRY-DEMO-120" in text
    assert "0.99" in text                       # groove pitch
    assert "2.375" in text                      # coil center standoff
    assert "62.5" in text                       # Eye
    assert "alignment residual (mm) 0" in text
    assert "Measurements decide." in text
    assert "4096" in text                       # pulse metadata recorded
    assert "NaN" not in text


def test_compatibility_sheet_content(result):
    text = pdf_text(result["bundle"] / "pdf"
                    / "compatibility_sheet.pdf")
    assert "CRY-DEMO-120" in text
    assert "27.32" in text and "40.32" in text  # generated inner dims
    assert "M2_TEXT" in text and "M2_MESH" in text  # kept separate
    assert "does not assert physical output" in text


def test_receipts_schema_and_eye(result):
    receipts = result["bundle"] / "receipts"
    design = json.loads((receipts / "design_receipt.json")
                        .read_text(encoding="utf-8"))
    assert design["schema_version"].startswith("2.")
    assert design["generated_dimensions"]["generation"] == \
        "crystal_envelope_plus_clearance"
    eye = json.loads((receipts / "eye_alignment_receipt.json")
                     .read_text(encoding="utf-8"))
    assert eye["z_cross_mm"] == eye["z_eye_mm"] == 62.5
    assert eye["pass"] is True
