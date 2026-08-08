"""v8.5.3 polish: pre-upgrade backup manifest, library metadata/
favorites, export collision behavior."""
import json
from pathlib import Path

import pytest

from rgcs_desktop.services import factory_content as fc
from rgcs_desktop.services.session_store import SessionStore
from rgcs_desktop.services.sonic_export_selection import (
    ExportSelectionError, export_selected)
from rgcs_desktop.services.sonic_recipes import (load_recipes,
                                                 recipe_to_session)


@pytest.fixture()
def session() -> dict:
    return recipe_to_session(load_recipes()[0], duration_s=12.0)


# ------------------------------------------------------ backup manifest
def test_update_writes_backup_manifest_first(tmp_path):
    manifest = json.loads(json.dumps(fc.load_factory_manifest()))
    item = manifest["items"][0]
    item["install_policy"] = "update_if_unmodified"
    fc.sync_factory_content(tmp_path, manifest)

    target = tmp_path / item["relative_path"]
    prior = "{\"old_factory_version\": true}"
    target.write_text(prior, encoding="utf-8")
    state_path = tmp_path / fc.STATE_RELPATH
    state = json.loads(state_path.read_text(encoding="utf-8"))
    prior_sha = fc._sha256(target.read_bytes())
    state["installed"][item["factory_id"]] = prior_sha
    state_path.write_text(json.dumps(state), encoding="utf-8")

    report = fc.sync_factory_content(tmp_path, manifest)
    assert report["backup_manifest"] is not None
    backup = json.loads(Path(report["backup_manifest"])
                        .read_text(encoding="utf-8"))
    change = next(c for c in backup["changes"]
                  if c["factory_id"] == item["factory_id"])
    assert change["action"] == "update"
    assert change["prior_sha256"] == prior_sha


def test_plain_install_and_noop_write_no_backup(tmp_path):
    report = fc.sync_factory_content(tmp_path)   # fresh install: adds
    assert report["backup_manifest"] is None
    report = fc.sync_factory_content(tmp_path)   # no-op
    assert report["backup_manifest"] is None


# ---------------------------------------------------- library metadata
def test_list_sessions_carries_search_metadata(tmp_path):
    fc.sync_factory_content(tmp_path)
    store = SessionStore(tmp_path)
    rows = store.list_sessions()
    schumann = next(r for r in rows if "Schumann" in r["title"])
    assert schumann["beat_hz"] == pytest.approx(7.83)
    assert schumann["carrier_hz"] is not None
    assert schumann["category"]
    assert schumann["favorite"] is False


def test_favorites_toggle_round_trip(tmp_path):
    fc.sync_factory_content(tmp_path)
    store = SessionStore(tmp_path)
    row = store.list_sessions()[0]
    assert store.toggle_favorite(row["session_id"]) is True
    assert store.list_sessions()[0]["favorite"] is True
    assert store.toggle_favorite(row["session_id"]) is False


def test_imported_sessions_get_imported_origin(tmp_path, session):
    store = SessionStore(tmp_path)
    src = tmp_path / "incoming.json"
    src.write_text(json.dumps(session), encoding="utf-8")
    store.import_session(src)
    rows = store.list_sessions()
    assert any(r["origin"] == "imported" for r in rows)


# ------------------------------------------------------- collisions
def test_collision_increment_keeps_both(session, tmp_path):
    first = export_selected(session, ["session_json"], tmp_path,
                            on_collision="increment")
    second = export_selected(session, ["session_json"], tmp_path,
                             on_collision="increment")
    assert first["session_json"] != second["session_json"]
    assert first["session_json"].is_file()
    assert second["session_json"].is_file()
    assert second["session_json"].name.endswith("_2.session.json")


def test_collision_overwrite_replaces(session, tmp_path):
    first = export_selected(session, ["session_json"], tmp_path)
    second = export_selected(session, ["session_json"], tmp_path)
    assert first["session_json"] == second["session_json"]
    files = [p for p in tmp_path.iterdir() if p.is_file()]
    assert len(files) == 1


def test_unknown_collision_mode_refused(session, tmp_path):
    with pytest.raises(ExportSelectionError, match="collision"):
        export_selected(session, ["session_json"], tmp_path,
                        on_collision="ask-me")


def test_export_provenance_has_version_commit_hash(session, tmp_path):
    written = export_selected(session, ["session_json"], tmp_path)
    prov = written["provenance"]
    assert prov["software"]
    assert prov["git_commit"]
    assert len(prov["input_sha256"]) == 64
