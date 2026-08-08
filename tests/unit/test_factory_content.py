"""Factory content: curated session library validity + idempotent
workspace sync (v8.5.2 plan pack 07_TESTS; neutral naming v8.5.3)."""
import json
from pathlib import Path

import pytest

from rgcs_desktop.services import factory_content as fc
from rgcs_desktop.services.schemas import validate_instance
from rgcs_desktop.services.sonic_timeline import validate_session


# ---------------------------------------------------------------- data
def test_manifest_lists_61_curated_sessions():
    items = fc.factory_items()
    curated = [i for i in items
               if i["content_family"] == "curated_binaural"]
    assert len(curated) == 61
    assert len({i["factory_id"] for i in items}) == len(items)


def test_manifest_hashes_match_packaged_bytes():
    for item in fc.factory_items():
        assert fc._sha256(fc.factory_file_bytes(item)) == item["sha256"], \
            item["factory_id"]


def test_manifest_policies_and_claim_boundary():
    body = fc.load_factory_manifest()
    assert "not endorsed" in body["note"]
    assert "never overwrite" in body["note"]
    for item in body["items"]:
        assert item["install_policy"] in fc.INSTALL_POLICIES
        assert item["relative_path"].startswith("library/")


def test_every_curated_session_passes_both_gates():
    for item in fc.factory_items():
        session = json.loads(fc.factory_file_bytes(item))
        errors = validate_instance(session,
                                   "frequency_session.schema.json")
        assert errors == [], f"{item['factory_id']}: {errors[:2]}"
        validate_session(session)  # raises TimelineError on bad totals


def test_curated_notes_keep_claim_boundary_language():
    for item in fc.factory_items():
        session = json.loads(fc.factory_file_bytes(item))
        assert "not a medical claim" in session.get("notes", ""), \
            item["factory_id"]


# ---------------------------------------------------------------- sync
def test_existing_workspace_folder_does_not_crash(tmp_path):
    ws = tmp_path / "RGCS Workspace"
    ws.mkdir()                       # folder already exists
    report = fc.sync_factory_content(ws)
    assert len(report["added"]) == 61
    assert report["kept_user_modified"] == []


def test_sync_is_idempotent(tmp_path):
    fc.sync_factory_content(tmp_path)
    report = fc.sync_factory_content(tmp_path)
    assert report["added"] == []
    assert report["updated"] == []
    assert len(report["unchanged"]) == 61


def test_user_modified_file_never_overwritten(tmp_path):
    fc.sync_factory_content(tmp_path)
    item = fc.factory_items()[0]
    target = tmp_path / item["relative_path"]
    edited = json.loads(target.read_text(encoding="utf-8"))
    edited["title"] = "My edited session"
    target.write_text(json.dumps(edited), encoding="utf-8")

    report = fc.sync_factory_content(tmp_path)
    assert item["factory_id"] in report["kept_user_modified"]
    body = json.loads(target.read_text(encoding="utf-8"))
    assert body["title"] == "My edited session"


def test_preexisting_unknown_file_treated_as_users(tmp_path):
    item = fc.factory_items()[0]
    target = tmp_path / item["relative_path"]
    target.parent.mkdir(parents=True)
    target.write_text("{\"mine\": true}", encoding="utf-8")

    report = fc.sync_factory_content(tmp_path)
    assert item["factory_id"] in report["kept_user_modified"]
    assert json.loads(target.read_text(encoding="utf-8")) == {"mine": True}


def test_update_if_unmodified_replaces_stale_factory_copy(tmp_path):
    manifest = json.loads(json.dumps(fc.load_factory_manifest()))
    item = manifest["items"][0]
    item["install_policy"] = "update_if_unmodified"
    fc.sync_factory_content(tmp_path, manifest)

    # simulate an older factory version on disk: content differs from
    # the shipped sha but matches what the state file recorded
    target = tmp_path / item["relative_path"]
    target.write_text("{\"old_factory_version\": true}", encoding="utf-8")
    state_path = tmp_path / fc.STATE_RELPATH
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["installed"][item["factory_id"]] = fc._sha256(
        target.read_bytes())
    state_path.write_text(json.dumps(state), encoding="utf-8")

    report = fc.sync_factory_content(tmp_path, manifest)
    assert item["factory_id"] in report["updated"]
    assert fc._sha256(target.read_bytes()) == item["sha256"]


def test_repair_restores_deleted_factory_file(tmp_path):
    fc.sync_factory_content(tmp_path)
    item = fc.factory_items()[3]
    target = tmp_path / item["relative_path"]
    target.unlink()
    report = fc.repair_factory_content(tmp_path)
    assert item["factory_id"] in report["added"]
    assert target.is_file()


def test_deprecated_hide_never_installs(tmp_path):
    manifest = json.loads(json.dumps(fc.load_factory_manifest()))
    item = manifest["items"][0]
    item["install_policy"] = "deprecated_hide"
    report = fc.sync_factory_content(tmp_path, manifest)
    assert item["factory_id"] in report["hidden"]
    assert not (tmp_path / item["relative_path"]).exists()


def test_unknown_policy_refused(tmp_path):
    manifest = {"items": [{"factory_id": "x", "install_policy": "nuke",
                           "relative_path": "library/x.json",
                           "package_relpath": "missing.json",
                           "sha256": "0" * 64}]}
    with pytest.raises(fc.FactoryContentError, match="install policy"):
        fc.sync_factory_content(tmp_path, manifest)


def test_legacy_factory_dir_migrates_to_trash(tmp_path):
    """A factory subdir from an older release (renamed family) moves to
    the workspace trash — never deleted, never left to double-list."""
    legacy = (tmp_path / "library" / "frequency_sessions" / "factory"
              / "old_family_name")
    legacy.mkdir(parents=True)
    (legacy / "old.json").write_text("{\"session_id\": \"OLD\"}",
                                     encoding="utf-8")
    report = fc.sync_factory_content(tmp_path)
    assert report["migrated_legacy"] == ["old_family_name"]
    assert not legacy.exists()
    trash = tmp_path / "library" / "trash"
    moved = list(trash.glob("legacy_factory_old_family_name_*/old.json"))
    assert len(moved) == 1
    # a second sync has nothing left to migrate
    assert fc.sync_factory_content(tmp_path)["migrated_legacy"] == []


def test_curated_content_carries_no_vendor_branding():
    """v8.5.3: no device/vendor names in filenames, ids, or content."""
    import re
    banned = re.compile(r"aha.?halo|spooky|s2d", re.IGNORECASE)
    body = fc.load_factory_manifest()
    assert not banned.search(json.dumps(body))
    for item in fc.factory_items():
        text = fc.factory_file_bytes(item).decode("utf-8")
        assert not banned.search(text), item["factory_id"]
        assert not banned.search(item["package_relpath"])


def test_sync_reports_state_path(tmp_path):
    report = fc.sync_factory_content(tmp_path)
    state = json.loads(Path(report["state_path"])
                       .read_text(encoding="utf-8"))
    assert state["state_kind"] == "rgcs.factory_state/v1"
    assert len(state["installed"]) == 61
