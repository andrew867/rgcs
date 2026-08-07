"""Frequency Key Studio export tests: recipe JSON, YouTube sheet."""
import json

from rgcs_desktop.services.sonic_exports import (
    export_recipe_json, export_youtube_metadata_sheet)
from rgcs_desktop.services.sonic_recipes import (recipe_by_id,
                                                 recipe_to_session)


def test_recipe_json_deterministic(tmp_path):
    session = recipe_to_session(recipe_by_id("RGCS-BIN-0001"),
                                duration_s=60.0)
    a = export_recipe_json(dict(session), tmp_path / "a.json")
    b = export_recipe_json(dict(session), tmp_path / "b.json")
    assert a.read_text(encoding="utf-8") == b.read_text(encoding="utf-8")
    body = json.loads(a.read_text(encoding="utf-8"))
    assert len(body["sha256"]) == 64


def test_youtube_sheet_contains_recipe(tmp_path):
    session = recipe_to_session(recipe_by_id("RGCS-SCH-0001"),
                                duration_s=60.0)
    path = export_youtube_metadata_sheet(session, tmp_path / "yt.txt")
    text = path.read_text(encoding="utf-8")
    assert "925 Hz + 7.83 Hz" in text
    assert "Left: 921.085 Hz" in text
    assert "Right: 928.915 Hz" in text
    assert "comfortable volume" in text
    assert "RGCS Frequency Key Studio" in text
