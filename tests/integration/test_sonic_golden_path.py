"""Frequency Key Studio golden path (plan pack 10_TESTS/TEST_PLAN.md):
seed recipe -> short WAV -> recipe JSON -> session PDF -> bundle ->
checksums -> PDF text contains carrier, beat, duration, receipt hash."""
import json
import zipfile
from pathlib import Path

import pytest

from rgcs_desktop.services.schemas import validate_instance
from rgcs_desktop.services.sonic_audio import read_wav_info
from rgcs_desktop.services.sonic_exports import (
    export_bundle, export_recipe_json, export_session_pdf,
    export_youtube_metadata_sheet, render_session_wav, verify_bundle)
from rgcs_desktop.services.sonic_recipes import (recipe_by_id,
                                                 recipe_to_session)

pypdf = pytest.importorskip("pypdf", reason="pypdf needed for PDF checks")


def pdf_text(path: Path) -> str:
    reader = pypdf.PdfReader(str(path))
    return " ".join(" ".join((page.extract_text() or "").split())
                    for page in reader.pages)


def test_golden_path(tmp_path):
    recipe = recipe_by_id("RGCS-SCH-0001")
    session = recipe_to_session(recipe, duration_s=10.0)

    # 1. render short WAV
    wav = tmp_path / "session.wav"
    receipt = render_session_wav(session, wav)
    info = read_wav_info(wav)
    assert info["channels"] == 2
    assert info["sample_rate"] == 48000
    assert info["duration_s"] == pytest.approx(10.0, abs=0.01)
    assert receipt["peak"] <= 0.95 + 1e-6
    assert validate_instance(receipt, "render_receipt.schema.json") == []

    # 2. recipe JSON validates
    recipe_json = export_recipe_json(session, tmp_path / "recipe.json")
    body = json.loads(recipe_json.read_text(encoding="utf-8"))
    body_no_hash = {k: v for k, v in body.items() if k != "sha256"}
    assert validate_instance(body_no_hash,
                             "frequency_session.schema.json") == []

    # 3. session PDF contains carrier, beat, duration, receipt hash
    pdf = export_session_pdf(session, receipt, tmp_path / "sheet.pdf")
    text = pdf_text(pdf)
    assert "925" in text
    assert "7.83" in text
    assert "10" in text
    assert receipt["input_sha256"][:16] in text
    assert receipt["output_sha256"][:16] in text
    assert "comfortable volume" in text
    assert "NaN" not in text

    # 4. YouTube sheet + bundle + checksum verification
    meta = export_youtube_metadata_sheet(session, tmp_path / "yt.txt")
    bundle = export_bundle(session, [wav, recipe_json, pdf, meta],
                           tmp_path / "bundle.zip")
    check = verify_bundle(bundle)
    assert check["ok"] and check["n_members"] == 4

    # 5. tampering is detected
    with zipfile.ZipFile(bundle) as zf:
        names = zf.namelist()
    assert "MANIFEST.json" in names
    tampered = tmp_path / "tampered.zip"
    with zipfile.ZipFile(bundle) as src, \
            zipfile.ZipFile(tampered, "w") as dst:
        for name in names:
            data = src.read(name)
            if name == "recipe.json":
                data = data.replace(b"925", b"999", 1)
            dst.writestr(name, data)
    assert not verify_bundle(tampered)["ok"]
