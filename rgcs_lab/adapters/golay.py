"""Golay adapter — executes the Codex G24 core (rgcs_lab.golay)."""

from __future__ import annotations

from rgcs_lab.adapters import guard_fallback, resolve_core
from rgcs_lab.common.receipts import build_receipt
from rgcs_lab.common.status import ModuleResult, Status

DOES = "Encode/decode a 36-bit address with extended binary Golay G24 blocks."
DOES_NOT = "Does not show that an external civilization uses Golay coding."

#: Codex core status vocabulary -> hub fixture vocabulary.
_STATUS_MAP = {
    "OK": "ok",
    "CORRECTED": "corrected",
    "UNCORRECTABLE_OR_AMBIGUOUS": "uncorrectable",
}

DEFAULT_ADDRESS36 = 165876523


def _flip_positions(flips_per_block: int, seed: int, block_index: int) -> list[int]:
    """Deterministic per-block flip positions (same LCG as the legacy demo)."""
    positions: list[int] = []
    x = (seed * 17 + block_index * 31) & 0xFFFF
    while len(positions) < min(flips_per_block, 24):
        pos = x % 24
        if pos not in positions:
            positions.append(pos)
        x = (x * 1103515245 + 12345) & 0x7FFFFFFF
    return positions


def demo(flips_per_block: int = 1, seed: int = 1) -> ModuleResult:
    if flips_per_block < 0:
        raise ValueError("flips_per_block must be >= 0")
    core, backend = resolve_core("rgcs_lab.golay", "rgcs_lab.reference.golay")

    if backend == "codex":
        blocks = core.split36(DEFAULT_ADDRESS36)
        codewords = [core.encode_block(b) for b in blocks]
        flipped: list[int] = []
        decoded: list[int | None] = []
        statuses: list[str] = []
        masks: list[int] = []
        distances: list[int] = []
        for i, cw in enumerate(codewords):
            recv = cw
            for pos in _flip_positions(flips_per_block, seed, i):
                recv ^= 1 << pos
            flipped.append(recv)
            res = core.decode_block(recv)
            decoded.append(res.decoded)
            statuses.append(_STATUS_MAP.get(res.status, "uncorrectable"))
            masks.append(res.correction_mask)
            distances.append(res.distance)
        # Round-trip check on the UNCORRUPTED codewords (codec exactness).
        exact = all(
            core.decode_block(cw).decoded == b and core.decode_block(cw).status == "OK"
            for b, cw in zip(blocks, codewords)
        )
        payload = {
            "convention": "rgcs.golay.g24.systematic-v1",
            "bit_order": "flip bit 0 is least-significant bit of each 24-bit block",
            "generator_polynomial_binary": format(core.GOLAY23_POLY, "012b"),
            "address36": DEFAULT_ADDRESS36,
            "blocks_in": blocks,
            "codewords": codewords,
            "corruption": flipped,
            "decoded_blocks": decoded,
            "correction_status": statuses,
            "correction_mask": masks,
            "distances": distances,
            "exact_round_trip": exact,
        }
        source = core.__name__
    else:  # labelled reference fallback (never GREEN)
        raw = core.demo_with_flips(flips_per_block=flips_per_block, seed=seed)
        payload = core.to_dict(raw)
        source = core.__name__

    uncorrectable = any(
        s == "uncorrectable" for s in payload.get("correction_status", [])
    )
    warnings = [
        "PHYSICAL ORIGIN OF ANY EXTERNAL SIGNAL: YELLOW — not demonstrated",
        f"backend={source}",
    ]
    if flips_per_block >= 4:
        warnings.append("four or more flips may be uncorrectable or miscorrected")
    if uncorrectable:
        warnings.append("at least one block reported uncorrectable")

    status = guard_fallback(Status.GREEN, backend, warnings)
    receipt = build_receipt(
        module="golay",
        status=status.value,
        claim_class=["EXACT_ARITHMETIC", "IMPLEMENTED_SOFTWARE"],
        inputs={"flips_per_block": flips_per_block, "seed": seed},
        models=[payload.get("convention", "rgcs.golay.g24.systematic-v1")],
        result=payload,
        tests=["golay_roundtrip", "golay_flip_demo",
               "tests/rgcs_lab/test_golay.py"],
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
        source=source,
    )
