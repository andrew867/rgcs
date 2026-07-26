"""Quaternion frames adapter — executes the Codex core (rgcs_lab.frames)."""

from __future__ import annotations

import math

from rgcs_lab.adapters import guard_fallback, resolve_core
from rgcs_lab.common.receipts import build_receipt
from rgcs_lab.common.status import ModuleResult, Status

DOES = "Compose ordered unit-quaternion frame transforms with round-trip checks."
DOES_NOT = "Does not demonstrate a physical field effect."

_EXAMPLES = {
    # name -> (from_frame, to_frame, axis, angle_rad)
    "earth-south-up": ("earth-east-north-up", "earth-south-up",
                       [0.0, 0.0, 1.0], math.pi),
    "identity": ("identity", "identity", [0.0, 0.0, 1.0], 0.0),
}


def example(name: str = "earth-south-up") -> ModuleResult:
    if name not in _EXAMPLES:
        raise ValueError(f"unknown frame example: {name}")
    core, backend = resolve_core("rgcs_lab.frames", "rgcs_lab.reference.frames")

    if backend == "codex":
        from_frame, to_frame, axis, angle = _EXAMPLES[name]
        rec = core.rotation_receipt(from_frame, to_frame, axis, angle)
        q = core.from_axis_angle(axis, angle)
        inv = q.inverse()
        basis = {
            "e1": q.rotate([1.0, 0.0, 0.0]),
            "e2": q.rotate([0.0, 1.0, 0.0]),
            "e3": q.rotate([0.0, 0.0, 1.0]),
        }
        round_trip = {k: inv.rotate(v) for k, v in basis.items()}
        payload = dict(rec["result"])
        payload["example"] = name
        payload["basis_out"] = basis
        payload["round_trip_basis"] = round_trip
        source = core.__name__
    else:  # labelled reference fallback (never GREEN)
        payload = core.compose_named(name)
        source = core.__name__

    warnings = ["PHYSICAL FIELD EFFECT: YELLOW — not demonstrated",
                f"backend={source}"]
    status = guard_fallback(Status.GREEN, backend, warnings)
    receipt = build_receipt(
        module="frames",
        status=status.value,
        claim_class=["EXACT_ARITHMETIC", "IMPLEMENTED_SOFTWARE"],
        inputs={"example": name},
        models=["unit-quaternion-hamilton-v1"],
        result=payload,
        tests=["frames_identity", "frames_inverse", "frames_roundtrip",
               "tests/rgcs_lab/test_frames.py"],
        warnings=warnings,
    )
    return ModuleResult(
        module="frames",
        status=status,
        claim_class=["EXACT_ARITHMETIC", "IMPLEMENTED_SOFTWARE"],
        input={"example": name},
        models=receipt["models"],
        result=payload,
        warnings=warnings,
        receipt=receipt,
        does=DOES,
        does_not=DOES_NOT,
        tests=receipt["tests"],
        source=source,
    )
