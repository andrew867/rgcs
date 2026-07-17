"""JSON contracts and validation (Agent A12).

The drive-recipe and log-event schemas come from the pack (adapted
and versioned here); device capabilities, arm lease, run manifest,
result summary and fault record are added. Validation is strict:
unknown schema versions, missing limits, non-finite numbers,
out-of-profile frequencies, and excessive duty/duration are REJECTED
— invalid JSON never reaches the output driver (A12 gate)."""

from __future__ import annotations

import hashlib
import json
import math

SCHEMA_VERSION = "1.0.0"

DRIVE_RECIPE_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "rgcs.fkey.drive_recipe/1",
    "type": "object",
    "required": ["schema_version", "recipe_id", "evidence_class",
                 "device_requirements", "segments", "sensor_plan",
                 "limits"],
    "properties": {
        "schema_version": {"const": SCHEMA_VERSION},
        "recipe_id": {"type": "string", "minLength": 1},
        "revision": {"type": "integer", "minimum": 1},
        "evidence_class": {"enum": ["ANALYTIC_MODEL",
                                    "NUMERICAL_SIMULATION",
                                    "SYNTHETIC_INSTRUMENT_RUN",
                                    "BENCH_MEASUREMENT_PLAN"]},
        "specimen_revision": {"type": ["string", "null"]},
        "hypothesis_id": {"type": ["string", "null"]},
        "device_requirements": {
            "type": "object",
            "required": ["profile", "frequency_min_hz",
                         "frequency_max_hz"],
            "properties": {
                "profile": {"type": "string"},
                "frequency_min_hz": {"type": "number",
                                     "minimum": 0},
                "frequency_max_hz": {"type": "number",
                                     "exclusiveMinimum": 0},
                "output_pins": {"type": "array",
                                "items": {}},
            }},
        "segments": {
            "type": "array", "minItems": 1, "maxItems": 256,
            "items": {
                "type": "object",
                # amplitude_frac is REQUIRED: a drive segment with an
                # unspecified amplitude would otherwise default to
                # something, and any default is the wrong answer for
                # an actuation instrument (explicit beats assumed)
                "required": ["label", "kind", "frequency_hz",
                             "duration_s", "amplitude_frac"],
                "properties": {
                    "label": {"type": "string"},
                    "kind": {"enum": ["sine", "square", "pulse",
                                      "sweep", "burst", "off"]},
                    "frequency_hz": {"type": "string"},
                    "sweep_end_hz": {"type": ["string", "null"]},
                    "duty": {"type": "number",
                             "exclusiveMinimum": 0,
                             "maximum": 0.5},
                    "duration_s": {"type": "number",
                                   "exclusiveMinimum": 0},
                    "amplitude_frac": {"type": "number",
                                       "minimum": 0, "maximum": 1},
                    "backend": {"type": "string"},
                }}},
        "sensor_plan": {
            "type": "object",
            "required": ["channels"],
            "properties": {"channels": {
                "type": "array",
                "items": {"type": "object",
                          "required": ["name", "calibrated"],
                          "properties": {
                              "name": {"type": "string"},
                              "calibrated": {"type": "boolean"},
                          }}}}},
        "limits": {
            "type": "object",
            "required": ["max_duty", "max_continuous_s",
                         "max_amplitude_frac"],
            "properties": {
                "max_duty": {"type": "number",
                             "exclusiveMinimum": 0, "maximum": 0.5},
                "max_continuous_s": {"type": "number",
                                     "exclusiveMinimum": 0,
                                     "maximum": 60},
                "max_amplitude_frac": {"type": "number",
                                       "exclusiveMinimum": 0,
                                       "maximum": 1},
            }},
    },
}

ARM_LEASE_SCHEMA = {
    "$id": "rgcs.fkey.arm_lease/1", "type": "object",
    "required": ["token", "ttl_s"],
    "properties": {"token": {"type": "string", "minLength": 8},
                   "ttl_s": {"type": "number",
                             "exclusiveMinimum": 0,
                             "maximum": 120}}}

RESULT_SUMMARY_SCHEMA = {
    "$id": "rgcs.fkey.result_summary/1", "type": "object",
    "required": ["recipe_id", "evidence_class", "completed",
                 "synthetic"],
    "properties": {"synthetic": {"type": "boolean"},
                   "evidence_class": {
                       "enum": ["SYNTHETIC_INSTRUMENT_RUN",
                                "BENCH_MEASUREMENT_PLAN"]}}}


def canonical_json(obj) -> str:
    """Canonical serialization for hashing (A12): sorted keys, no
    whitespace variation, floats refused in favour of strings for
    exact fields."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def content_hash(obj) -> str:
    return hashlib.sha256(canonical_json(obj).encode()).hexdigest()


def _finite_numbers_ok(obj) -> bool:
    if isinstance(obj, float):
        return math.isfinite(obj)
    if isinstance(obj, dict):
        return all(_finite_numbers_ok(v) for v in obj.values())
    if isinstance(obj, list):
        return all(_finite_numbers_ok(v) for v in obj)
    return True


def validate_recipe(recipe) -> dict:
    """Schema + semantic checks. Returns {'valid', 'errors'} and
    never raises on bad input data (raising is for programmer
    errors; a device must fault gracefully)."""
    errors = []
    if not isinstance(recipe, dict):
        return {"valid": False, "errors": ["recipe is not an object"]}
    try:
        import jsonschema
        v = jsonschema.Draft202012Validator(DRIVE_RECIPE_SCHEMA)
        errors += [f"{'/'.join(map(str, e.path))}: {e.message}"
                   for e in v.iter_errors(recipe)]
    except ImportError:                       # pragma: no cover
        errors += _manual_schema_check(recipe)
    if errors:
        return {"valid": False, "errors": errors}
    if not _finite_numbers_ok(recipe):
        return {"valid": False,
                "errors": ["non-finite number in recipe"]}
    # semantic checks
    req = recipe["device_requirements"]
    lim = recipe["limits"]
    total = 0.0
    for i, seg in enumerate(recipe["segments"]):
        try:
            from .relations import hz
            f = hz(seg["frequency_hz"])
        except Exception as exc:              # noqa: BLE001
            errors.append(f"segment {i}: bad frequency "
                          f"({exc})")
            continue
        if not (req["frequency_min_hz"] <= float(f)
                <= req["frequency_max_hz"]):
            errors.append(f"segment {i}: {f} Hz outside device "
                          "profile")
        if seg.get("duty", 0.5) > lim["max_duty"]:
            errors.append(f"segment {i}: duty above limit")
        if seg.get("amplitude_frac", 1.0) > \
                lim["max_amplitude_frac"]:
            errors.append(f"segment {i}: amplitude above limit")
        total += seg["duration_s"]
    if total > lim["max_continuous_s"]:
        errors.append(f"total duration {total}s exceeds limit "
                      f"{lim['max_continuous_s']}s")
    return {"valid": not errors, "errors": errors}


def _manual_schema_check(recipe) -> list:      # pragma: no cover
    errs = []
    for k in DRIVE_RECIPE_SCHEMA["required"]:
        if k not in recipe:
            errs.append(f"missing {k}")
    if recipe.get("schema_version") != SCHEMA_VERSION:
        errs.append("unknown schema version")
    return errs


def migrate(recipe: dict) -> dict:
    """Compatibility: prior versions get an explicit refusal (there
    are none yet) rather than a silent best-effort parse."""
    ver = recipe.get("schema_version")
    if ver == SCHEMA_VERSION:
        return {"migrated": False, "recipe": recipe}
    return {"migrated": False, "recipe": None,
            "refusal": f"schema version {ver!r} has no migration "
                       "path; regenerate the recipe (A12: explicit "
                       "refusal beats silent acceptance)"}


def example_recipe(recipe_id: str, segments: list,
                   profile: str = "SIMULATOR",
                   hypothesis_id: str | None = None) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "recipe_id": recipe_id,
        "revision": 1,
        "evidence_class": "SYNTHETIC_INSTRUMENT_RUN",
        "specimen_revision":
            "SP-EBAY-137330949270-PREARRIVAL/r1",
        "hypothesis_id": hypothesis_id,
        "device_requirements": {"profile": profile,
                                "frequency_min_hz": 1,
                                "frequency_max_hz": 200_000},
        "segments": segments,
        "sensor_plan": {"channels": [
            {"name": "piezo_pickup", "calibrated": False},
            {"name": "temperature", "calibrated": False},
            {"name": "supply_telemetry_slow", "calibrated": False},
        ]},
        "limits": {"max_duty": 0.5, "max_continuous_s": 30,
                   "max_amplitude_frac": 0.5},
    }
