"""Frequency Key Studio recipe library tests."""
import pytest

from rgcs_desktop.services.schemas import validate_instance
from rgcs_desktop.services.sonic_recipes import (
    RecipeError, load_beat_targets, load_recipes, recipe_by_id,
    recipe_to_session, search_recipes, validate_all_seed_recipes)


def test_seed_recipes_load():
    recipes = load_recipes()
    assert len(recipes) == 7
    ids = {r["recipe_id"] for r in recipes}
    assert "RGCS-SCH-0001" in ids
    assert "RGCS-FKY-1337" in ids


def test_beat_targets_load():
    beats = load_beat_targets()
    assert len(beats) == 11
    assert any(b["hz"] == 7.83 for b in beats)
    assert any(b["hz"] == 20.48 for b in beats)


def test_recipe_by_id_and_unknown():
    assert recipe_by_id("RGCS-BIN-0001")["carrier_hz"] == 102.0
    with pytest.raises(RecipeError):
        recipe_by_id("RGCS-NOPE-0000")


def test_every_seed_recipe_converts_and_validates():
    results = validate_all_seed_recipes()
    assert all(v == "ok" for v in results.values()), results


def test_recipe_to_session_schema_valid():
    session = recipe_to_session(recipe_by_id("RGCS-SCH-0001"),
                                duration_s=120.0)
    assert validate_instance(session,
                             "frequency_session.schema.json") == []
    assert session["duration_s"] == 120.0
    kinds = [la["type"] for la in session["layers"]]
    assert kinds == ["binaural", "brown_noise"]
    assert session["layers"][0]["carrier_hz"] == 925.0
    assert "comfortable volume" in session["notes"]


def test_gateway_recipe_maps_surf_layer():
    session = recipe_to_session(recipe_by_id("RGCS-GWY-0001"),
                                duration_s=60.0)
    assert [la["type"] for la in session["layers"]] == \
        ["binaural", "pink_noise", "surf_noise"]


def test_search_recipes():
    assert {r["recipe_id"] for r in search_recipes("schumann")} == \
        {"RGCS-SCH-0001"}
    hits = search_recipes(frequency_hz=925.0)
    assert {r["recipe_id"] for r in hits} == {"RGCS-SCH-0001",
                                              "RGCS-FKY-0925"}
    assert {r["recipe_id"] for r in search_recipes(family="isochronic")} \
        == {"RGCS-ISO-0001"}
    beats = search_recipes(frequency_hz=6.3)
    assert {r["recipe_id"] for r in beats} == {"RGCS-AST-0001"}
