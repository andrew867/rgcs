"""Phryll v2 single-artifact exports: one file per call, never a
bundle (v8.5.2 export UX)."""
import json
from pathlib import Path

import pytest

from rgcs_desktop.services.phryll_v2.pipeline import (
    SINGLE_ARTIFACT_KINDS, export_single_artifact)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "phryll_v2"


@pytest.fixture(scope="module")
def raw_crystal() -> dict:
    return json.loads((FIXTURES / "crystal_profile_example.json")
                      .read_text(encoding="utf-8"))


def test_stl_only_export_writes_exactly_one_stl(raw_crystal, tmp_path):
    receipt = export_single_artifact(raw_crystal, tmp_path, "sleeve_stl")
    path = Path(receipt["path"])
    assert path.is_file()
    assert path.suffix == ".stl"
    assert len(receipt["sha256"]) == 64
    # exactly one file, no bundle directory, no zip, no _work leftovers
    entries = list(tmp_path.iterdir())
    assert entries == [path]


def test_every_kind_writes_one_new_file(raw_crystal, tmp_path):
    seen = set()
    for kind in SINGLE_ARTIFACT_KINDS:
        receipt = export_single_artifact(raw_crystal, tmp_path, kind)
        path = Path(receipt["path"])
        assert path.is_file(), kind
        assert path not in seen, f"{kind} reused another kind's file"
        seen.add(path)
    files = {p for p in tmp_path.iterdir() if p.is_file()}
    assert files == seen
    assert not any(p.is_dir() for p in tmp_path.iterdir())


def test_receipt_json_round_trips(raw_crystal, tmp_path):
    receipt = export_single_artifact(raw_crystal, tmp_path,
                                     "receipt_json")
    body = json.loads(Path(receipt["path"]).read_text(encoding="utf-8"))
    for key in ("design", "coil_sleeve", "bottom_coupling",
                "eye_alignment", "fit"):
        assert key in body
    assert body["fit"]["ok"] is True


def test_unknown_kind_is_refused(raw_crystal, tmp_path):
    with pytest.raises(ValueError, match="unknown artifact kind"):
        export_single_artifact(raw_crystal, tmp_path, "everything")
