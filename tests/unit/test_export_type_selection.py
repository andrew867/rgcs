"""Export file-type selection (v8.5.2 plan pack 07_TESTS:
test_export_type_selection, service half)."""
import zipfile
from pathlib import Path

import pytest

from rgcs_desktop.services.sonic_export_selection import (
    EXPORT_KINDS, ExportSelectionError, expected_export_files,
    export_selected)
from rgcs_desktop.services.sonic_recipes import (load_recipes,
                                                 recipe_to_session)


@pytest.fixture()
def session() -> dict:
    return recipe_to_session(load_recipes()[0], duration_s=12.0)


def _files(out: Path) -> set[str]:
    return {p.name for p in out.iterdir() if p.is_file()}


def test_json_only_export_has_one_json(session, tmp_path):
    written = export_selected(session, ["session_json"], tmp_path)
    path = written["session_json"]
    assert path.suffix == ".json"
    assert _files(tmp_path) == {path.name}


def test_wav_preview_only_export_has_one_wav(session, tmp_path):
    written = export_selected(session, ["wav_preview"], tmp_path)
    assert _files(tmp_path) == {written["wav_preview"].name}
    assert written["receipt"]["duration_s"] == pytest.approx(12.0)


def test_pdf_only_export_has_one_pdf_with_real_stats(session, tmp_path):
    written = export_selected(session, ["session_pdf"], tmp_path)
    assert _files(tmp_path) == {written["session_pdf"].name}
    # the render happened (stats exist) but no WAV was kept
    assert written["receipt"]["output_sha256"]


def test_expected_files_match_what_export_writes(session, tmp_path):
    kinds = ["recipe_json", "wav_full", "youtube_txt"]
    names = expected_export_files(session, kinds)
    written = export_selected(session, kinds, tmp_path)
    produced = {p.name for k, p in written.items() if k != "receipt"}
    assert set(names) == produced == _files(tmp_path)


def test_bundle_zip_includes_member_files(session, tmp_path):
    written = export_selected(session, ["bundle_zip"], tmp_path)
    with zipfile.ZipFile(written["bundle_zip"]) as zf:
        members = set(zf.namelist())
    assert any(m.endswith(".wav") for m in members)
    assert "MANIFEST.json" in members


def test_unknown_kind_refused(session, tmp_path):
    with pytest.raises(ExportSelectionError, match="unknown export"):
        export_selected(session, ["everything"], tmp_path)
    with pytest.raises(ExportSelectionError, match="at least one"):
        export_selected(session, [], tmp_path)


def test_all_kinds_are_exportable(session, tmp_path):
    written = export_selected(session, list(EXPORT_KINDS), tmp_path)
    assert set(EXPORT_KINDS) <= set(written)
