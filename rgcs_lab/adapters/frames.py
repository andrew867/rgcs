"""Quaternion frames adapter."""

from __future__ import annotations

from rgcs_lab.adapters import resolve
from rgcs_lab.common.receipts import build_receipt
from rgcs_lab.common.status import ModuleResult, Status
from rgcs_lab.reference import frames as ref


DOES = "Compose ordered unit-quaternion frame transforms with round-trip checks."
DOES_NOT = "Does not demonstrate a physical field effect."


def example(name: str = "earth-south-up") -> ModuleResult:
    mod = resolve("rgcs_frames", "rgcs_lab.reference.frames")
    if hasattr(mod, "compose_named"):
        payload = mod.compose_named(name)
    else:
        payload = ref.compose_named(name)
    receipt = build_receipt(
        module="frames",
        status=Status.GREEN.value,
        claim_class=["EXACT_ARITHMETIC", "IMPLEMENTED_SOFTWARE"],
        inputs={"example": name},
        models=["unit-quaternion-hamilton-v1"],
        result=payload,
        tests=["frames_identity", "frames_inverse", "frames_roundtrip"],
        warnings=["PHYSICAL FIELD EFFECT: YELLOW — not demonstrated"],
    )
    return ModuleResult(
        module="frames",
        status=Status.GREEN,
        claim_class=["EXACT_ARITHMETIC", "IMPLEMENTED_SOFTWARE"],
        input={"example": name},
        models=receipt["models"],
        result=payload,
        warnings=receipt["warnings"],
        receipt=receipt,
        does=DOES,
        does_not=DOES_NOT,
        tests=receipt["tests"],
        source=getattr(mod, "__name__", "rgcs_lab.reference.frames"),
    )
