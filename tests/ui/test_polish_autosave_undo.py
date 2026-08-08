"""v8.5.3 polish: autosave/crash recovery, undo/redo, shortcuts."""
from pathlib import Path

import pytest


@pytest.fixture()
def studio(main_window):
    panel = main_window.panels["Frequency Key Studio"]
    panel.dirty_prompt = lambda: "discard"
    return panel


def test_autosave_written_when_dirty(studio):
    studio.new_session.minutes.setValue(
        studio.new_session.minutes.value() + 1)
    assert studio.new_session.is_dirty
    studio.new_session._autosave_tick()
    candidates = studio.autosave_candidates()
    assert candidates
    sid = studio.new_session.current_session()["session_id"]
    assert candidates[0]["session"]["session_id"] == sid


def test_autosave_cleared_on_save(studio):
    studio.new_session.minutes.setValue(
        studio.new_session.minutes.value() + 1)
    studio.new_session._autosave_tick()
    assert studio.autosave_candidates()
    assert studio.save_session() is not None
    assert studio.autosave_candidates() == []


def test_recover_previous_session(studio):
    studio.new_session.set_title("Almost Lost")
    studio.new_session._autosave_tick()
    # simulate losing the editor state (forced close)
    studio.new_session.reset_identity()
    studio.new_session._dirty = False
    assert studio.recover_autosave()
    session = studio.new_session.current_session()
    assert session["title"] == "Almost Lost"
    assert studio.new_session.is_dirty     # recovered = unsaved


def test_teardown_autosaves_dirty_session(studio):
    studio.new_session.set_title("Teardown Capture")
    studio.new_session.teardown()
    titles = [c["session"]["title"]
              for c in studio.autosave_candidates()]
    assert "Teardown Capture" in titles


def test_undo_redo_value_edit(studio):
    page = studio.new_session
    before = page.minutes.value()
    page.minutes.setValue(before + 5)
    assert page.undo()
    assert page.minutes.value() == before
    assert page.redo()
    assert page.minutes.value() == before + 5


def test_undo_title_edit(studio):
    page = studio.new_session
    original = page.current_session()["title"]
    page.set_title("Renamed Session")
    assert page.current_session()["title"] == "Renamed Session"
    assert page.undo()
    assert page.current_session()["title"] == original


def test_undo_wobble_edit(studio):
    page = studio.new_session
    page.wobble.setCurrentIndex(1)      # first real wobble preset
    session = page.current_session()
    assert any("wobble" in layer for layer in session["layers"])
    assert page.undo()
    session = page.current_session()
    assert not any("wobble" in layer for layer in session["layers"])


def test_undo_floor_is_baseline(studio):
    page = studio.new_session
    # nothing to undo at a fresh baseline
    assert not page.undo()


def test_segment_edit_marks_dirty_for_undo(studio):
    editor = studio.timeline_editor
    editor.enabled.setChecked(True)
    assert studio.new_session.is_dirty


def test_shortcut_menu_entries_exist(main_window):
    file_actions = {a.text(): a.shortcut().toString()
                    for a in main_window.file_menu.actions()
                    if a.text()}
    assert file_actions.get("New Session") == "Ctrl+N"
    assert file_actions.get("Open Session…") == "Ctrl+O"
    assert file_actions.get("Save") == "Ctrl+S"
    assert file_actions.get("Save As…") == "Ctrl+Shift+S"
    assert file_actions.get("Close Session") == "Ctrl+W"
    assert file_actions.get("Export Selected Types") == "Ctrl+E"
    assert file_actions.get("Render Full + Export Set") == "Ctrl+R"
    assert file_actions.get("Quit") == "Ctrl+Q"
    edit_actions = {a.text(): a.shortcut().toString()
                    for a in main_window.edit_menu.actions()
                    if a.text()}
    assert edit_actions.get("Undo") == "Ctrl+Z"
    assert edit_actions.get("Redo") == "Ctrl+Y"


def test_quit_with_prompt_cancel_keeps_window(main_window, studio):
    studio.new_session._dirty = True
    studio.dirty_prompt = lambda: "cancel"
    main_window.quit_with_prompt()
    # cancel: still open (close() never called on a visible window)
    assert main_window.isVisible()
