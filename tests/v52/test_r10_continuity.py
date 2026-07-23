"""P14/P15 — continuity manifest, export, restore, successor drill."""

from __future__ import annotations

import pytest

from r10 import continuity as C


def _tree(tmp_path):
    (tmp_path / "a.txt").write_text("alpha\n")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.txt").write_text("beta\n")
    return ["a.txt", "sub/b.txt"]


def test_manifest_is_deterministic(tmp_path):
    rels = _tree(tmp_path)
    m1 = C.build_manifest(tmp_path, rels)
    m2 = C.build_manifest(tmp_path, list(reversed(rels)))
    # sorted + content-hashed, so order of input does not matter
    assert [e.path for e in m1] == [e.path for e in m2]
    assert C.manifest_to_json(m1, commit="x") == C.manifest_to_json(m2, commit="x")


def test_a_missing_canonical_artifact_is_an_error(tmp_path):
    _tree(tmp_path)
    with pytest.raises(C.ContinuityError):
        C.build_manifest(tmp_path, ["a.txt", "does_not_exist.txt"])


def test_restore_verifies_an_unchanged_tree(tmp_path):
    rels = _tree(tmp_path)
    m = C.build_manifest(tmp_path, rels)
    rep = C.verify_restore(tmp_path, m)
    assert rep["ok"] and rep["verdict"] == "RESTORE_VERIFIED"
    C.refuse_restore_on_mismatch(rep)     # must not raise


def test_a_tampered_file_is_detected(tmp_path):
    rels = _tree(tmp_path)
    m = C.build_manifest(tmp_path, rels)
    (tmp_path / "a.txt").write_text("TAMPERED\n")
    rep = C.verify_restore(tmp_path, m)
    assert not rep["ok"]
    assert "a.txt" in rep["altered"]
    with pytest.raises(C.ContinuityError):
        C.refuse_restore_on_mismatch(rep)


def test_a_deleted_file_is_detected(tmp_path):
    rels = _tree(tmp_path)
    m = C.build_manifest(tmp_path, rels)
    (tmp_path / "sub" / "b.txt").unlink()
    rep = C.verify_restore(tmp_path, m)
    assert "sub/b.txt" in rep["missing"]
    assert rep["verdict"] == "RESTORE_INCOMPLETE"


def test_export_round_trips(tmp_path):
    rels = _tree(tmp_path)
    m = C.build_manifest(tmp_path, rels)
    dest = tmp_path / "MANIFEST.json"
    C.export_manifest(m, dest, commit="deadbeef")
    text = dest.read_text()
    assert "rgcs.continuity_manifest.v1" in text
    assert "deadbeef" in text


def test_successor_drill_enumerates_the_clean_room_steps():
    ck = C.successor_checklist()
    assert ck["bus_factor_target"] == 0
    steps = " ".join(ck["steps"]).lower()
    assert "clone" in steps and "restore an archive" in steps
    assert "test suite" in steps


def test_report_claims_no_measurement():
    r = C.continuity_report()
    assert r["measured_here"] == "nothing"
    assert r["verdict"] == "CONTINUITY_SOFTWARE_ONLY"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
