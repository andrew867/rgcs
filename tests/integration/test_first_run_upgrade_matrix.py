"""v8.5.3 polish item 9: the first-run / upgrade smoke matrix.

Five scenarios that historically broke installs, each proven safe:
fresh workspace, existing empty folder, existing workspace with a
user-modified factory file, an old (pre-library) workspace, and
demo-content-checked over an existing folder."""
import json

import pytest

from rgcs_desktop.services import factory_content as fc
from rgcs_desktop.workspaces import Workspace

pytest.importorskip("PySide6")


@pytest.fixture()
def ctx():
    from rgcs_desktop.app.context import AppContext
    context = AppContext()
    yield context
    context.shutdown()


def _factory_count(root) -> int:
    factory = root / "library" / "frequency_sessions" / "factory" / \
        "curated"
    return len(list(factory.glob("*.json"))) if factory.is_dir() else 0


def test_scenario_1_fresh_workspace(ctx, tmp_path):
    from rgcs_desktop.app.first_run import apply_first_run
    root = tmp_path / "fresh"
    apply_first_run(ctx, root, seed_demo=False)
    assert (root / "workspace.db").is_file()
    assert _factory_count(root) == 61


def test_scenario_2_existing_empty_folder(ctx, tmp_path):
    from rgcs_desktop.app.first_run import apply_first_run
    root = tmp_path / "RGCS Workspace"
    root.mkdir()
    apply_first_run(ctx, root, seed_demo=False)
    assert (root / "workspace.db").is_file()
    assert _factory_count(root) == 61


def test_scenario_3_user_modified_factory_file(ctx, tmp_path):
    from rgcs_desktop.app.first_run import apply_first_run
    root = tmp_path / "ws"
    apply_first_run(ctx, root, seed_demo=False)
    item = fc.factory_items()[0]
    target = root / item["relative_path"]
    body = json.loads(target.read_text(encoding="utf-8"))
    body["title"] = "Mine now"
    target.write_text(json.dumps(body), encoding="utf-8")

    ctx.close_workspace()
    ctx.open_workspace(root)   # upgrade-style reopen re-syncs
    kept = json.loads(target.read_text(encoding="utf-8"))
    assert kept["title"] == "Mine now"
    assert ctx.last_factory_sync is not None
    assert item["factory_id"] in \
        ctx.last_factory_sync["kept_user_modified"]


def test_scenario_4_old_workspace_gains_library(ctx, tmp_path):
    """A v8.5.0-era workspace: workspace.db + user artifacts, no
    library/. Opening it adds factory content and touches nothing
    else."""
    root = tmp_path / "old"
    ws = Workspace.create(root, "old")
    ws.put_object("note", "precious", {"v": 1})
    ws.close()
    (root / "exports").mkdir()
    (root / "exports" / "old_render.wav").write_bytes(b"RIFFdata")

    ctx.open_workspace(root)
    assert _factory_count(root) == 61
    assert (root / "exports" / "old_render.wav").read_bytes() == \
        b"RIFFdata"
    names = [o["name"] for o in ctx.workspace.list_objects("note")]
    assert names == ["precious"]


def test_scenario_5_demo_checked_folder_exists(ctx, tmp_path):
    """The historical crash: demo content checked AND the folder (with
    a workspace) already exists."""
    from rgcs_desktop.app.first_run import apply_first_run
    root = tmp_path / "RGCS Workspace"
    apply_first_run(ctx, root, seed_demo=True)
    # run the wizard result again — reinstall / re-run first run
    apply_first_run(ctx, root, seed_demo=True)
    assert ctx.workspace is not None
    assert _factory_count(root) == 61
    # a second sync reported no clobbering
    assert ctx.last_factory_sync["kept_user_modified"] == []
