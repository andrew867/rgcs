"""Frequency Studio session CRUD service (v8.5.2 plan pack 07_TESTS:
test_frequency_studio_crud, service half)."""
import json
from pathlib import Path

import pytest

from rgcs_desktop.services import factory_content as fc
from rgcs_desktop.services.session_store import (SessionStore,
                                                 SessionStoreError,
                                                 load_session_file)
from rgcs_desktop.services.sonic_recipes import (load_recipes,
                                                 recipe_to_session)


@pytest.fixture()
def session() -> dict:
    return recipe_to_session(load_recipes()[0], duration_s=60.0)


@pytest.fixture()
def store(tmp_path) -> SessionStore:
    return SessionStore(tmp_path)


def test_save_and_open_round_trip(store, session):
    path = store.save(session)
    assert path.is_file()
    assert path.suffix == ".json"
    body = store.open(path)
    assert body["session_id"] == session["session_id"]
    assert body["schema_version"] == session["schema_version"]


def test_save_refuses_invalid_session(store):
    with pytest.raises(SessionStoreError, match="invalid"):
        store.save({"schema_version": "1.0.0"})


def test_save_refuses_bad_timeline(store, session):
    session["segments"][0]["duration_s"] = 9999.0
    with pytest.raises(SessionStoreError, match="timeline"):
        store.save(session)


def test_save_as_uses_title_and_never_clobbers(store, session):
    first = store.save_as(session, "My Sleep Mix")
    second = store.save_as(session, "My Sleep Mix")
    assert first.name == "My_Sleep_Mix.session.json"
    assert second.name == "My_Sleep_Mix_2.session.json"
    assert first != second and first.is_file() and second.is_file()


def test_duplicate_mints_new_id_and_copy_title(store, session):
    original = store.save(session)
    copy_path = store.duplicate(original)
    copy = store.open(copy_path)
    assert copy["session_id"] != session["session_id"]
    assert copy["title"].endswith("(copy)")
    assert store.open(original)["session_id"] == session["session_id"]


def test_delete_moves_to_workspace_trash(store, session):
    path = store.save(session)
    trashed = store.delete(path)
    assert not path.exists()
    assert trashed.is_file()
    assert trashed.parent == store.trash_dir
    # trash keeps the original name recoverable
    assert path.name in trashed.name


def test_factory_sessions_are_read_only(store, session, tmp_path):
    fc.sync_factory_content(tmp_path)
    factory_rows = [r for r in store.list_sessions()
                    if r["origin"] == "factory"]
    assert len(factory_rows) == 61
    target = Path(factory_rows[0]["path"])
    with pytest.raises(SessionStoreError, match="read-only"):
        store.save(session, target)


def test_duplicate_factory_session_lands_in_user_dir(store, tmp_path):
    fc.sync_factory_content(tmp_path)
    row = next(r for r in store.list_sessions()
               if r["origin"] == "factory")
    copy_path = store.duplicate(row["path"])
    assert copy_path.resolve().is_relative_to(store.user_dir.resolve())


def test_import_session_copies_and_avoids_id_collision(store, session,
                                                       tmp_path):
    external = tmp_path / "incoming.json"
    external.write_text(json.dumps(session), encoding="utf-8")
    first = store.import_session(external)
    second = store.import_session(external)
    ids = {store.open(first)["session_id"],
           store.open(second)["session_id"]}
    assert len(ids) == 2          # collision minted a fresh ID
    assert external.is_file()     # source untouched


def test_list_sessions_reports_origin_and_metadata(store, session,
                                                   tmp_path):
    fc.sync_factory_content(tmp_path)
    store.save(session)
    rows = store.list_sessions()
    origins = {r["origin"] for r in rows}
    assert origins == {"factory", "user"}
    assert all(r["session_id"] and r["title"] for r in rows)


def test_load_session_file_states_timeline_errors(tmp_path, session):
    session["segments"][0]["duration_s"] = 9999.0
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(session), encoding="utf-8")
    with pytest.raises(SessionStoreError, match="timeline invalid"):
        load_session_file(bad)


def test_load_session_file_states_schema_errors(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{\"schema_version\": \"1.0.0\"}", encoding="utf-8")
    with pytest.raises(SessionStoreError, match="invalid"):
        load_session_file(bad)
