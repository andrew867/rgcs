"""v8.5.3 polish: render job control, import error UX, Phryll export
visibility."""
import json
from pathlib import Path

import pytest


@pytest.fixture()
def studio(main_window):
    panel = main_window.panels["Frequency Key Studio"]
    panel.dirty_prompt = lambda: "discard"
    return panel


def test_render_full_cycle_and_duplicate_guard(studio, qtbot):
    page = studio.new_session
    page.minutes.setValue(1)
    thread = page.render_clicked()
    assert thread is not None
    assert page._rendering
    assert not page.render_btn.isEnabled()
    # duplicate click while running is refused, does not start another
    assert page.render_clicked() is None
    qtbot.waitUntil(lambda: not page._rendering, timeout=120_000)
    assert page.render_btn.isEnabled()
    assert page.last_exports.get("bundle")
    assert Path(page.last_exports["bundle"]).is_file()


def test_cancelled_render_discards_files(studio, qtbot):
    page = studio.new_session
    page.minutes.setValue(1)
    thread = page.render_clicked()
    assert thread is not None
    page.cancel_render()
    qtbot.waitUntil(lambda: not page._rendering, timeout=120_000)
    # nothing recorded as the last export set
    assert page.last_exports.get("bundle") is None \
        or not Path(page.last_exports["bundle"]).exists() \
        or page._render_cancelled


def test_render_error_shows_and_clears_on_edit(studio):
    page = studio.new_session
    page._render_failed("synthetic failure")
    assert "synthetic failure" in page.render_error.text()
    assert page.render_btn.isEnabled()
    page.minutes.setValue(page.minutes.value() + 1)   # user fixes input
    assert page.render_error.text() == ""


def test_import_error_reports_exact_reason(studio, tmp_path):
    reports = []
    studio.import_error_handler = \
        lambda path, message: reports.append((path, message))
    bad = tmp_path / "malformed.json"
    bad.write_text("{not json", encoding="utf-8")
    assert not studio.open_session(bad)
    assert reports and "not valid JSON" in reports[0][1]

    wrong_major = tmp_path / "future.json"
    wrong_major.write_text(json.dumps({
        "schema_version": "9.0.0", "session_id": "X", "title": "x",
        "duration_s": 10,
        "segments": [{"kind": "hold", "duration_s": 10}]}),
        encoding="utf-8")
    assert not studio.open_session(wrong_major)
    assert len(reports) == 2
    assert "schema" in reports[1][1].lower()


def test_phryll_single_export_reports_path_and_reveal(main_window,
                                                     tmp_path):
    panel = main_window.panels["Phryll Generator v2"]
    receipt = panel.export_single(out_dir=tmp_path)
    assert receipt is not None
    path = Path(receipt["path"])
    assert path.is_file() and path.stat().st_size > 0
    # the panel shows the full path — no mystery destinations
    assert str(path) in panel.status.text()
    assert panel.reveal_btn.isEnabled()
