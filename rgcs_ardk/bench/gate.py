"""Structural refusal gate for field-asymmetry bench results."""

from __future__ import annotations

from enum import Enum
import math
import re
from typing import Any, Mapping


class BenchVerdictRefused(RuntimeError):
    """Raised when incomplete or out-of-bound evidence requests a verdict."""


class BenchVerdict(str, Enum):
    PASS = "PASS_FIELD_ASYMMETRY"
    FAIL = "FAIL_FIELD_ASYMMETRY"


REQUIRED_CONTROLS = (
    "all_active",
    "binary_best",
    "equal_resource_randomized",
    "reversed_lag",
    "rotated",
    "mirrored",
    "dummy_load",
)

_DISALLOWED_PRIMARY = {
    "force",
    "thrust",
    "lift",
    "propulsion",
    "gravity",
    "mass reduction",
    "energy output",
}
_OVERREACH_PATTERN = re.compile(
    r"\b(?:force|thrust|lift|propulsion|antigravity|over-unity|craft)\b"
    r".{0,24}\b(?:confirmed|detected|demonstrated|produced|achieved|works)\b",
    re.IGNORECASE,
)


def _positive_number(mapping: Mapping[str, Any], name: str) -> float:
    value = mapping.get(name)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BenchVerdictRefused(f"missing {name} uncertainty")
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise BenchVerdictRefused(f"invalid {name} uncertainty")
    return value


def _required_nonempty(result: Mapping[str, Any], name: str, message: str) -> Any:
    value = result.get(name)
    if value is None or value == "" or value == [] or value == {}:
        raise BenchVerdictRefused(message)
    return value


def evaluate_bench_result(result: Mapping[str, Any]) -> BenchVerdict:
    """Return a bounded verdict, or raise when the evidence is incomplete."""
    primary = str(result.get("primary_observable", "")).strip().lower()
    if primary != "deltab":
        if primary in _DISALLOWED_PRIMARY:
            raise BenchVerdictRefused("forbidden primary observable")
        raise BenchVerdictRefused("primary observable must be DeltaB")
    claim_language = str(result.get("claim_language", ""))
    if _OVERREACH_PATTERN.search(claim_language):
        raise BenchVerdictRefused("result language exceeds the field-asymmetry boundary")
    uncertainty = result.get("uncertainty")
    if not isinstance(uncertainty, Mapping):
        raise BenchVerdictRefused("missing declared uncertainty")
    _positive_number(uncertainty, "angular_deg")
    _positive_number(uncertainty, "amplitude_norm")
    controls = result.get("controls")
    if not isinstance(controls, Mapping):
        raise BenchVerdictRefused("missing required controls")
    missing = [name for name in REQUIRED_CONTROLS if name not in controls or controls[name] is None]
    if missing:
        raise BenchVerdictRefused(f"missing controls: {missing}")
    if result.get("crystal_lane_included"):
        crystal_controls = (controls.get("no_crystal"), controls.get("dummy_crystal"))
        if all(value is None for value in crystal_controls):
            raise BenchVerdictRefused("crystal lane requires no-crystal or dummy-crystal control")
    _required_nonempty(result, "raw_data_hashes", "missing raw data hashes")
    _required_nonempty(
        result,
        "instrument_calibration_ids",
        "missing calibration identifiers",
    )
    criteria_names = (
        "angle_tracks",
        "magnitude_beats_nulls",
        "transforms_pass",
        "artifacts_bounded",
    )
    missing_criteria = [name for name in criteria_names if not isinstance(result.get(name), bool)]
    if missing_criteria:
        raise BenchVerdictRefused(f"missing boolean criteria: {missing_criteria}")
    return (
        BenchVerdict.PASS
        if all(result[name] for name in criteria_names)
        else BenchVerdict.FAIL
    )
