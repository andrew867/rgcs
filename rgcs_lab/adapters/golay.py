"""Golay adapter — prefer rgcs_golay, else lab reference."""

from __future__ import annotations

from rgcs_lab.adapters import resolve
from rgcs_lab.common.receipts import build_receipt
from rgcs_lab.common.status import ModuleResult, Status
from rgcs_lab.reference import golay as ref


DOES = "Encode/decode a 36-bit address with extended binary Golay G24 blocks."
DOES_NOT = "Does not show that an external civilization uses Golay coding."


def demo(flips_per_block: int = 1, seed: int = 1) -> ModuleResult:
    mod = resolve("rgcs_golay", "rgcs_lab.reference.golay")
    if hasattr(mod, "demo_with_flips"):
        raw = mod.demo_with_flips(flips_per_block=flips_per_block, seed=seed)
        payload = mod.to_dict(raw) if hasattr(mod, "to_dict") else dict(raw)
    else:
        raw = ref.demo_with_flips(flips_per_block=flips_per_block, seed=seed)
        payload = ref.to_dict(raw)

    # Status of the codec itself is GREEN; physical origin remains YELLOW warning.
    uncorrectable = any(s == "uncorrectable" for s in payload.get("correction_status", []))
    status = Status.GREEN
    warnings = [
        "PHYSICAL ORIGIN OF ANY EXTERNAL SIGNAL: YELLOW — not demonstrated",
        f"backend={getattr(mod, '__name__', 'reference')}",
    ]
    if flips_per_block >= 4:
        warnings.append("four or more flips may be uncorrectable or miscorrected")
    if uncorrectable:
        warnings.append("at least one block reported uncorrectable")

    receipt = build_receipt(
        module="golay",
        status=status.value,
        claim_class=["EXACT_ARITHMETIC", "IMPLEMENTED_SOFTWARE"],
        inputs={"flips_per_block": flips_per_block, "seed": seed},
        models=[payload.get("convention", "rgcs.golay.g24.systematic-v1")],
        result=payload,
        tests=["golay_roundtrip", "golay_flip_demo"],
        warnings=warnings,
    )
    return ModuleResult(
        module="golay",
        status=status,
        claim_class=["EXACT_ARITHMETIC", "IMPLEMENTED_SOFTWARE"],
        input={"flips_per_block": flips_per_block, "seed": seed},
        models=receipt["models"],
        result=payload,
        warnings=warnings,
        receipt=receipt,
        does=DOES,
        does_not=DOES_NOT,
        tests=receipt["tests"],
        source=getattr(mod, "__name__", "rgcs_lab.reference.golay"),
    )
