"""Workspace lifecycle (v8.5.2): idempotent first run, open-or-create,
failure-safe switching, close semantics."""
from pathlib import Path

import pytest

from rgcs_desktop.workspaces import Workspace, WorkspaceError


def test_open_or_create_creates_then_opens(tmp_path):
    ws = Workspace.open_or_create(tmp_path / "ws", "fresh")
    ws.put_object("note", "n1", {"text": "hello"})
    ws.close()
    again = Workspace.open_or_create(tmp_path / "ws")
    try:
        assert [o["name"] for o in again.list_objects("note")] == ["n1"]
    finally:
        again.close()


def test_open_or_create_tolerates_existing_plain_folder(tmp_path):
    root = tmp_path / "RGCS Workspace"
    root.mkdir()                       # exists, but no workspace yet
    (root / "unrelated.txt").write_text("keep me", encoding="utf-8")
    ws = Workspace.open_or_create(root)
    try:
        assert (root / "workspace.db").is_file()
        assert (root / "unrelated.txt").read_text(
            encoding="utf-8") == "keep me"
    finally:
        ws.close()


@pytest.fixture()
def qt_context():
    from rgcs_desktop.app.context import AppContext
    ctx = AppContext()
    yield ctx
    ctx.shutdown()


def test_first_run_reruns_do_not_crash(qt_context, tmp_path):
    from rgcs_desktop.app.first_run import apply_first_run
    root = tmp_path / "RGCS Workspace"
    apply_first_run(qt_context, root, seed_demo=False)
    # the historical crash: folder + workspace.db already exist
    apply_first_run(qt_context, root, seed_demo=True)
    assert qt_context.workspace is not None
    assert (root / "workspace.db").is_file()


def test_first_run_installs_curated_factory_sessions(qt_context,
                                                     tmp_path):
    from rgcs_desktop.app.first_run import apply_first_run
    root = tmp_path / "ws"
    apply_first_run(qt_context, root, seed_demo=False)
    factory = root / "library" / "frequency_sessions" / "factory" / \
        "aha_halo_curated"
    assert len(list(factory.glob("*.json"))) == 61
    assert qt_context.last_factory_sync is not None
    assert len(qt_context.last_factory_sync["added"]) == 61


def test_create_workspace_opens_existing_instead_of_raising(qt_context,
                                                            tmp_path):
    root = tmp_path / "ws"
    qt_context.create_workspace(root, "first")
    qt_context.workspace.put_object("note", "keep", {"v": 1})
    # historically raised "workspace already exists"
    qt_context.create_workspace(root, "second")
    names = [o["name"]
             for o in qt_context.workspace.list_objects("note")]
    assert names == ["keep"]


def test_failed_open_leaves_current_workspace_usable(qt_context,
                                                     tmp_path):
    root = tmp_path / "good"
    qt_context.create_workspace(root, "good")
    qt_context.workspace.put_object("note", "still-here", {"v": 1})
    with pytest.raises(WorkspaceError):
        qt_context.open_workspace(tmp_path / "does-not-exist")
    # the old workspace must still be open and queryable — not a
    # closed-but-referenced husk
    names = [o["name"]
             for o in qt_context.workspace.list_objects("note")]
    assert names == ["still-here"]


def test_close_workspace_clears_pointer_and_setting(qt_context,
                                                    tmp_path):
    qt_context.create_workspace(tmp_path / "ws", "ws")
    qt_context.close_workspace()
    assert qt_context.workspace is None
    assert qt_context.settings.last_workspace in (None, "")
    # closing again is a no-op, not an error
    qt_context.close_workspace()


def test_upgrade_adds_new_factory_files_to_old_workspace(qt_context,
                                                         tmp_path):
    """A pre-8.5.2 workspace (no library/) gains the curated sessions
    on next open — the factory-content upgrade path."""
    root = tmp_path / "old-ws"
    ws = Workspace.create(root, "old")
    ws.close()
    qt_context.open_workspace(root)
    factory = root / "library" / "frequency_sessions" / "factory" / \
        "aha_halo_curated"
    assert len(list(factory.glob("*.json"))) == 61
