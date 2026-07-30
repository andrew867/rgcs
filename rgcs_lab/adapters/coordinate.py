"""Coordinate adapter — stable rgcs_coordinate domain API only."""

from __future__ import annotations

from typing import Any

import rgcs_coordinate as rc

from rgcs_lab.common.receipts import build_receipt
from rgcs_lab.common.status import ModuleResult, Status


DOES = "Exact structural decode/encode of the Federation/Terra 30-bit packet."
DOES_NOT = "Does not yet establish a unique physical source map."
SOURCE = "rgcs_coordinate"


def decode(raw: int | str) -> ModuleResult:
    value = int(raw)
    trace = rc.decode_coordinate(value)
    payload = trace.to_dict()
    receipt = build_receipt(
        module="coordinate",
        status=Status.GREEN.value,
        claim_class=["EXACT_ARITHMETIC", "TRAINING_EQUALITY", "UNDERDETERMINED"],
        inputs={"raw_decimal": str(value), "codec": rc.DEFAULT_CODEC},
        models=[rc.DEFAULT_CODEC],
        result=payload,
        tests=["roundtrip_coordinate", "golden_vectors"],
        warnings=[
            "PHYSICAL PROJECTION: YELLOW UNDERDETERMINED",
            "Stonehenge decimal is a training equality",
        ],
    )
    return ModuleResult(
        module="coordinate",
        status=Status.GREEN,
        claim_class=["EXACT_ARITHMETIC", "TRAINING_EQUALITY", "UNDERDETERMINED"],
        input={"raw_decimal": str(value)},
        models=[rc.DEFAULT_CODEC],
        result=payload,
        warnings=receipt["warnings"],
        receipt=receipt,
        does=DOES,
        does_not=DOES_NOT,
        tests=receipt["tests"],
        source=SOURCE,
    )


def roundtrip(raw: int | str) -> ModuleResult:
    value = int(raw)
    info = rc.roundtrip_coordinate(value)
    ok = bool(info.get("exact") or info.get("ok") or info.get("matches"))
    # federation_terra roundtrip returns a structured dict — normalize.
    if "reencoded" in info:
        ok = info.get("reencoded") == value or info.get("exact", ok)
    status = Status.GREEN if ok else Status.RED
    receipt = build_receipt(
        module="coordinate",
        status=status.value,
        claim_class=["EXACT_ARITHMETIC"],
        inputs={"raw_decimal": str(value)},
        models=[rc.DEFAULT_CODEC],
        result=info if isinstance(info, dict) else {"value": info},
        tests=["roundtrip_coordinate"],
    )
    return ModuleResult(
        module="coordinate",
        status=status,
        claim_class=["EXACT_ARITHMETIC"],
        input={"raw_decimal": str(value)},
        models=[rc.DEFAULT_CODEC],
        result=receipt["result"],
        receipt=receipt,
        does=DOES,
        does_not=DOES_NOT,
        tests=receipt["tests"],
        source=SOURCE,
    )


def doctor() -> dict[str, Any]:
    return {
        "module": "coordinate",
        "version": rc.__version__,
        "codecs": rc.list_codecs(),
        "standing": "PHYSICAL_PROJECTION_UNDERDETERMINED",
    }
