"""Frequency Studio session CRUD from the UI (v8.5.2 plan pack
07_TESTS: test_frequency_studio_crud)."""
from pathlib import Path

import pytest


@pytest.fixture()
def studio(main_window):
    return main_window.panels["Frequency Key Studio"]


def test_new_session_creates_dirty_editable_session(studio):
    assert studio.new_session_action()
    assert studio.new_session.is_dirty
    session = studio.new_session.current_session()
    assert session is not None
    assert session["session_id"]


def test_save_clears_dirty_flag(studio):
    studio.dirty_prompt = lambda: "discard"
    studio.new_session_action()
    path = studio.save_session()
    assert path is not None and path.is_file()
    assert not studio.new_session.is_dirty
    # editing marks dirty again
    studio.new_session.minutes.setValue(
        studio.new_session.minutes.value() + 1)
    assert studio.new_session.is_dirty


def test_save_keeps_stable_session_id(studio):
    studio.dirty_prompt = lambda: "discard"
    studio.new_session_action()
    sid = studio.new_session.current_session()["session_id"]
    studio.new_session.preview()
    assert studio.new_session.current_session()["session_id"] == sid
    path = studio.save_session()
    import json
    assert json.loads(path.read_text(
        encoding="utf-8"))["session_id"] == sid


def test_open_recent_records_path(studio):
    studio.dirty_prompt = lambda: "discard"
    studio.new_session_action()
    path = studio.save_session()
    assert str(path) in studio.context.settings.recent_sessions
    assert studio.open_session(path)
    assert studio.context.settings.recent_sessions[0] == str(path)


def test_open_session_loads_editable_state(studio):
    studio.dirty_prompt = lambda: "discard"
    studio.new_session_action()
    studio.new_session.set_title("Round Trip Check")
    saved = studio.save_session()
    studio.close_session()
    assert studio.open_session(saved)
    session = studio.new_session.current_session()
    assert session["title"] == "Round Trip Check"
    assert not studio.new_session.is_dirty
    assert studio.new_session.session_path == saved


def test_close_dirty_session_prompts(studio):
    prompts = []

    def fake_prompt():
        prompts.append(True)
        return "cancel"

    studio.dirty_prompt = fake_prompt
    studio.new_session._dirty = True
    assert not studio.close_session()      # cancel blocks the close
    assert prompts
    studio.dirty_prompt = lambda: "discard"
    assert studio.close_session()


def test_duplicate_creates_new_session_id(studio):
    studio.dirty_prompt = lambda: "discard"
    studio.new_session_action()
    original = studio.save_session()
    copy_path = studio.duplicate_session()
    import json
    a = json.loads(original.read_text(encoding="utf-8"))
    b = json.loads(copy_path.read_text(encoding="utf-8"))
    assert a["session_id"] != b["session_id"]
    assert b["title"].endswith("(copy)")


def test_delete_moves_to_workspace_trash(studio):
    studio.dirty_prompt = lambda: "discard"
    studio.new_session_action()
    path = studio.save_session()
    trashed = studio.delete_session()
    assert trashed is not None and trashed.is_file()
    assert not path.exists()
    assert "trash" in str(trashed)


def test_factory_sessions_listed_in_library(studio):
    studio.session_library.refresh()
    origins = {r["origin"] for r in studio.session_library._rows}
    assert "factory" in origins
    factory_rows = [r for r in studio.session_library._rows
                    if r["origin"] == "factory"]
    assert len(factory_rows) == 61


def test_open_factory_session_from_library(studio):
    studio.dirty_prompt = lambda: "discard"
    studio.session_library.refresh()
    row = next(r for r in studio.session_library._rows
               if "Schumann" in r["title"])
    assert studio.open_session(row["path"])
    session = studio.new_session.current_session()
    assert session is not None
    # the Schumann family beat came through
    assert any(abs(la.get("beat_hz", 0) - 7.83) < 0.01
               for la in session["layers"]
               if la.get("type") == "binaural")


def test_session_menu_commands_exist(main_window):
    names = main_window.command_names()
    for cmd in ("Session: new", "Session: open…", "Session: save",
                "Session: save as…", "Session: close",
                "Session: duplicate",
                "Session: delete (to workspace trash)",
                "Session: import…"):
        assert cmd in names
    # the File menu exists with a Workspace submenu
    menus = [a.text() for a in main_window.menuBar().actions()]
    assert "&File" in menus
