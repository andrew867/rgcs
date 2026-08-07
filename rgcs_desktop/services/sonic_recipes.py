"""Frequency Key Studio recipe library: seed recipes and beat targets
load from packaged data files; recipes convert to renderable sessions;
search runs over frequency, intent, and family."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from rgcs_desktop.services.schemas import validate_instance
from rgcs_desktop.services.sonic_timeline import standard_session_shape

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
RECIPES_FILE = DATA_DIR / "frequency_key_studio_recipes.json"
BEATS_FILE = DATA_DIR / "frequency_key_studio_beats.json"

#: default per-layer settings when a recipe names a layer by type only
_LAYER_DEFAULTS = {
    "binaural": {"gain_db": -6.0},
    "monaural": {"gain_db": -6.0},
    "isochronic": {"gain_db": -6.0, "duty": 0.5},
    "white_noise": {"gain_db": -20.0, "seed": 0},
    "pink_noise": {"gain_db": -18.0, "seed": 0},
    "brown_noise": {"gain_db": -18.0, "seed": 0},
    "surf_noise": {"gain_db": -16.0, "seed": 0},
}

USER_NOTE = "Experimental audio recipe. Use comfortable volume. Results vary."


class RecipeError(ValueError):
    """A refused or unknown recipe (with the reason)."""


@lru_cache(maxsize=1)
def _recipes_raw() -> dict:
    return json.loads(RECIPES_FILE.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _beats_raw() -> dict:
    return json.loads(BEATS_FILE.read_text(encoding="utf-8"))


def load_recipes() -> list[dict]:
    return list(_recipes_raw()["recipes"])


def load_beat_targets() -> list[dict]:
    return list(_beats_raw()["beats"])


def recipe_by_id(recipe_id: str) -> dict:
    for recipe in load_recipes():
        if recipe["recipe_id"] == recipe_id:
            return recipe
    raise RecipeError(f"unknown recipe {recipe_id!r} (have: "
                      f"{', '.join(r['recipe_id'] for r in load_recipes())})")


def search_recipes(query: str = "", *, frequency_hz: float | None = None,
                   family: str | None = None) -> list[dict]:
    """Search by free text over title/intent, exact-ish frequency
    (carrier or beat within 1%), and family."""
    out = []
    q = query.strip().lower()
    for recipe in load_recipes():
        if family and recipe.get("family") != family:
            continue
        if frequency_hz is not None:
            near = any(
                abs(float(recipe.get(k, 0.0)) - frequency_hz)
                <= 0.01 * max(frequency_hz, 1.0)
                for k in ("carrier_hz", "beat_hz"))
            if not near:
                continue
        if q:
            haystack = " ".join(str(recipe.get(k, "")) for k in
                                ("title", "intent", "family",
                                 "recipe_id")).lower()
            if q not in haystack:
                continue
        out.append(recipe)
    return out


def recipe_to_session(recipe: dict, *, duration_s: float | None = None,
                      sample_rate: int = 48000) -> dict:
    """A renderable frequency_session dict from a seed recipe, using
    the companion's standard session shape."""
    beat = float(recipe["beat_hz"])
    carrier = float(recipe["carrier_hz"])
    duration = float(duration_s if duration_s is not None
                     else float(recipe.get("duration_min", 20)) * 60.0)
    layers = []
    for i, kind in enumerate(recipe.get("layers", ["binaural"])):
        kind = kind.strip()
        if kind == "surf":
            kind = "surf_noise"
        if kind not in _LAYER_DEFAULTS:
            raise RecipeError(f"recipe layer type {kind!r} is not "
                              f"renderable")
        layer = {"layer_id": f"L{i + 1}", "type": kind,
                 "fade_in_s": min(2.0, duration / 10),
                 "fade_out_s": min(3.0, duration / 8),
                 **_LAYER_DEFAULTS[kind]}
        if kind in ("binaural", "monaural"):
            layer["carrier_hz"] = carrier
            layer["beat_hz"] = beat
        if kind == "isochronic":
            layer["carrier_hz"] = carrier
        layers.append(layer)

    session = {
        "schema_version": "1.0.0",
        "session_id": f"SES-{recipe['recipe_id']}",
        "title": recipe["title"],
        "intent": recipe.get("intent", ""),
        "family": recipe.get("family", ""),
        "duration_s": duration,
        "sample_rate": sample_rate,
        "segments": standard_session_shape(beat, duration),
        "layers": layers,
        "notes": USER_NOTE,
        "source_ids": [recipe.get("source_basis", "")],
    }
    errors = validate_instance(session, "frequency_session.schema.json")
    if errors:
        raise RecipeError("recipe produced an invalid session: "
                          + "; ".join(errors))
    return session


def validate_all_seed_recipes() -> dict:
    """Convert every seed recipe to a session and validate it; returns
    {recipe_id: 'ok' | error}. Used by tests and --doctor style checks."""
    results = {}
    for recipe in load_recipes():
        try:
            recipe_to_session(recipe, duration_s=60.0)
            results[recipe["recipe_id"]] = "ok"
        except (RecipeError, Exception) as exc:  # noqa: BLE001
            results[recipe["recipe_id"]] = str(exc)
    return results
