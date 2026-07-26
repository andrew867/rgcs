"""Extended binary Golay (24, 12, 8) transport wrapper."""

from __future__ import annotations

from dataclasses import dataclass

from .receipts import receipt

GOLAY23_POLY = 0b101011100011
DATA_BITS = 12
CODE_BITS = 24
MASK12 = (1 << DATA_BITS) - 1
MASK23 = (1 << 23) - 1


@dataclass(frozen=True)
class DecodeResult:
    decoded: int | None
    corrected_codeword: int | None
    distance: int
    correction_mask: int
    status: str


def _poly_mod(value: int) -> int:
    v = value
    while v.bit_length() >= GOLAY23_POLY.bit_length():
        shift = v.bit_length() - GOLAY23_POLY.bit_length()
        v ^= GOLAY23_POLY << shift
    return v


def encode_block(data: int) -> int:
    if not 0 <= data <= MASK12:
        raise ValueError("Golay data block must be a 12-bit integer")
    shifted = data << 11
    parity11 = _poly_mod(shifted)
    cw23 = (shifted | parity11) & MASK23
    overall = cw23.bit_count() & 1
    return (cw23 << 1) | overall


CODEBOOK = {encode_block(data): data for data in range(1 << DATA_BITS)}


def decode_block(word: int) -> DecodeResult:
    if not 0 <= word < (1 << CODE_BITS):
        raise ValueError("Golay code block must be a 24-bit integer")
    best: list[tuple[int, int, int]] = []
    min_dist = CODE_BITS + 1
    for codeword, data in CODEBOOK.items():
        dist = (word ^ codeword).bit_count()
        if dist < min_dist:
            min_dist = dist
            best = [(codeword, data, dist)]
        elif dist == min_dist:
            best.append((codeword, data, dist))
    if min_dist <= 3 and len(best) == 1:
        codeword, data, dist = best[0]
        return DecodeResult(data, codeword, dist, word ^ codeword,
                            "CORRECTED" if dist else "OK")
    return DecodeResult(None, None, min_dist, 0,
                        "UNCORRECTABLE_OR_AMBIGUOUS")


def split36(address36: int) -> list[int]:
    if not 0 <= address36 < (1 << 36):
        raise ValueError("address must be a 36-bit integer")
    return [(address36 >> shift) & MASK12 for shift in (24, 12, 0)]


def encode_address(address36: int) -> int:
    out = 0
    for block in split36(address36):
        out = (out << CODE_BITS) | encode_block(block)
    return out


def decode_address(code72: int) -> dict[str, object]:
    if not 0 <= code72 < (1 << 72):
        raise ValueError("encoded address must be a 72-bit integer")
    blocks = [(code72 >> shift) & ((1 << CODE_BITS) - 1)
              for shift in (48, 24, 0)]
    decoded_blocks: list[int] = []
    results = [decode_block(block) for block in blocks]
    exact = all(r.decoded is not None for r in results)
    decoded = None
    if exact:
        decoded = 0
        for r in results:
            assert r.decoded is not None
            decoded_blocks.append(r.decoded)
            decoded = (decoded << DATA_BITS) | r.decoded
    return {
        "encoded_blocks": blocks,
        "decoded_blocks": decoded_blocks if exact else None,
        "decoded_address": decoded,
        "block_status": [r.status for r in results],
        "correction_masks": [r.correction_mask for r in results],
        "distances": [r.distance for r in results],
        "exact_round_trip": exact,
    }


def demo(address36: int = 165876523, flips: list[int] | None = None
         ) -> dict[str, object]:
    if address36 >= (1 << 30):
        raise ValueError("default public transport wraps the 30-bit packet")
    mask = 0
    for bit in flips or []:
        if not 0 <= bit < 72:
            raise ValueError("flip positions must be in [0, 71]")
        mask ^= 1 << bit
    encoded = encode_address(address36)
    corrupted = encoded ^ mask
    decoded = decode_address(corrupted)
    status = "GREEN" if decoded["decoded_address"] == address36 else "YELLOW"
    result = {
        "generator": "binary Golay (23,12,7) systematic polynomial plus even parity extension",
        "generator_polynomial_binary": format(GOLAY23_POLY, "012b"),
        "bit_ordering": "most-significant block first; flip bit 0 is least-significant bit of 72-bit codeword",
        "source_packet_bits": 30,
        "transport_address_bits": 36,
        "original_address": address36,
        "original_blocks": split36(address36),
        "encoded_address": encoded,
        "encoded_blocks": [(encoded >> shift) & ((1 << CODE_BITS) - 1)
                           for shift in (48, 24, 0)],
        "corruption_mask": mask,
        "corrupted_address": corrupted,
        **decoded,
    }
    return receipt(
        "golay", status, ["EXACT_ARITHMETIC", "IMPLEMENTED_SOFTWARE"],
        {"address36": address36, "flips": flips or []},
        [{"name": "extended_binary_golay", "n": 24, "k": 12, "d": 8}],
        result,
        ["tests/rgcs_lab/test_golay.py"],
        warnings=["Four or more flipped bits are reported as uncorrectable or ambiguous."],
    )

