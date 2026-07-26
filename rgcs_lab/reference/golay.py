"""Extended binary Golay G24 reference (integration-held until Codex lands).

Cyclic Golay (23,12) with generator polynomial
``1 + x + x^5 + x^6 + x^7 + x^9 + x^11``, then overall-parity extension
to (24,12). Bit order: MSB-first. Convention: ``rgcs.golay.g24.cyclic-v1``.
"""

from __future__ import annotations

from dataclasses import dataclass

# g(x) = 1 + x + x^5 + x^6 + x^7 + x^9 + x^11  (degree 11)
_G_POLY = 0b101011100011  # bits 0..11, bit0 = x^0


def _parity(bits: list[int]) -> int:
    return sum(bits) & 1


def _int_to_bits(value: int, width: int) -> list[int]:
    if value < 0 or value >= (1 << width):
        raise ValueError(f"value {value} does not fit in {width} bits")
    return [(value >> (width - 1 - i)) & 1 for i in range(width)]


def _bits_to_int(bits: list[int]) -> int:
    v = 0
    for b in bits:
        v = (v << 1) | (b & 1)
    return v


def _poly_mod(dividend: int, divisor: int) -> int:
    """Polynomial remainder dividend % divisor over GF(2)."""
    deg_d = divisor.bit_length() - 1
    while dividend.bit_length() - 1 >= deg_d and dividend:
        shift = dividend.bit_length() - 1 - deg_d
        dividend ^= divisor << shift
    return dividend


def encode12(info: int) -> int:
    """Encode 12 information bits → 24-bit extended Golay codeword."""
    # Systematic cyclic encode into 23 bits: c(x) = m(x) x^11 - (m x^11 mod g)
    m = info & 0xFFF
    shifted = m << 11
    rem = _poly_mod(shifted, _G_POLY)
    code23 = shifted ^ rem  # 23-bit value in low bits
    bits23 = _int_to_bits(code23, 23)
    # Overall parity extension (even parity over 24 bits).
    bits24 = bits23 + [_parity(bits23)]
    return _bits_to_int(bits24)


def _syndrome23(bits23: list[int]) -> int:
    """Syndrome as remainder of received polynomial mod g."""
    return _poly_mod(_bits_to_int(bits23), _G_POLY)


def _weight(bits: list[int]) -> int:
    return sum(bits)


def _masks(n: int, weight: int):
    if weight == 0:
        yield [0] * n
        return
    idx = list(range(weight))
    while True:
        m = [0] * n
        for i in idx:
            m[i] = 1
        yield m
        for i in range(weight - 1, -1, -1):
            if idx[i] != i + n - weight:
                break
        else:
            return
        idx[i] += 1
        for j in range(i + 1, weight):
            idx[j] = idx[j - 1] + 1


def decode24(received: int) -> tuple[int, int, str, list[int], list[int]]:
    """Decode a 24-bit word.

    Returns (info12, corrected24, status, syndrome_bits, correction_mask).
    Corrects up to 3 errors; four or more may be uncorrectable.
    """
    r = _int_to_bits(received, 24)
    # Fast path: already a codeword.
    if _syndrome23(r[:23]) == 0 and _parity(r) == 0:
        info = _bits_to_int(r[:12])  # systematic: info in top 12 of 23? 
        # Our encode places m in bits [0..11] of the 23-bit word (MSB side
        # of the 23-bit field = high bits of code23).
        # code23 = (m << 11) ^ rem, so top 12 bits of the 23-bit string are m.
        info = _bits_to_int(r[:12])
        return info, received, "ok", [0] * 11, [0] * 24

    syn = _syndrome23(r[:23])
    syn_bits = _int_to_bits(syn, 11)

    best = None
    for w in (1, 2, 3):
        for mask in _masks(24, w):
            trial = [(a ^ b) for a, b in zip(r, mask)]
            if _syndrome23(trial[:23]) == 0 and _parity(trial) == 0:
                best = (trial, mask)
                break
        if best:
            break

    if best is None:
        return _bits_to_int(r[:12]), received, "uncorrectable", syn_bits, [0] * 24

    trial, mask = best
    return (
        _bits_to_int(trial[:12]),
        _bits_to_int(trial),
        "corrected",
        syn_bits,
        mask,
    )


@dataclass
class GolayDemoResult:
    convention: str
    blocks_in: list[int]
    codewords: list[int]
    flipped: list[int]
    decoded_blocks: list[int]
    statuses: list[str]
    syndromes: list[list[int]]
    correction_masks: list[list[int]]
    round_trip_ok: bool


def encode_address36(a0: int, a1: int, a2: int) -> list[int]:
    return [encode12(a0), encode12(a1), encode12(a2)]


def demo_with_flips(
    a0: int = 0xA5A,
    a1: int = 0x5C3,
    a2: int = 0x0F1,
    flips_per_block: int = 1,
    seed: int = 1,
) -> GolayDemoResult:
    if flips_per_block < 0:
        raise ValueError("flips_per_block must be >= 0")
    blocks = [a0 & 0xFFF, a1 & 0xFFF, a2 & 0xFFF]
    codewords = encode_address36(*blocks)
    flipped = []
    decoded = []
    statuses = []
    syndromes = []
    masks = []
    for i, cw in enumerate(codewords):
        bits = _int_to_bits(cw, 24)
        positions = []
        x = (seed * 17 + i * 31) & 0xFFFF
        while len(positions) < min(flips_per_block, 24):
            pos = x % 24
            if pos not in positions:
                positions.append(pos)
            x = (x * 1103515245 + 12345) & 0x7FFFFFFF
        for p in positions:
            bits[p] ^= 1
        recv = _bits_to_int(bits)
        flipped.append(recv)
        info, _, status, syn, mask = decode24(recv)
        decoded.append(info)
        statuses.append(status)
        syndromes.append(syn)
        masks.append(mask)

    rt_ok = True
    for b, cw in zip(blocks, codewords):
        info, _, status, _, _ = decode24(cw)
        if info != b or status != "ok":
            rt_ok = False

    return GolayDemoResult(
        convention="rgcs.golay.g24.cyclic-v1",
        blocks_in=blocks,
        codewords=codewords,
        flipped=flipped,
        decoded_blocks=decoded,
        statuses=statuses,
        syndromes=syndromes,
        correction_masks=masks,
        round_trip_ok=rt_ok,
    )


def to_dict(demo: GolayDemoResult) -> dict:
    return {
        "convention": demo.convention,
        "bit_order": "msb-first-within-block",
        "generator_poly": "1+x+x^5+x^6+x^7+x^9+x^11",
        "blocks_in": demo.blocks_in,
        "codewords": demo.codewords,
        "corruption": demo.flipped,
        "decoded_blocks": demo.decoded_blocks,
        "correction_status": demo.statuses,
        "syndrome": demo.syndromes,
        "correction_mask": demo.correction_masks,
        "exact_round_trip": demo.round_trip_ok,
    }
