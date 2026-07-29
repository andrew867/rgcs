"""R10.28 / R10.29 — the 36-bit codec harness.

36 bits = 12 octal digits exactly (8**12 = 2**36). That identity is the
only thing about "36" that is certain here; every partition below is a
CANDIDATE and each is tested, not assumed.

Partitions (from the source notes):

    R4  | S8  | P12 | E12          primary
    H3  | H3  | Core24 | T3 | T3   parallel
    H3  | Core30 | T3              parallel (demoted)

The demoted one is the interesting one structurally: a 3-bit header, a
30-bit core and a 3-bit terminal is exactly one octal digit + the
established 10-digit ``surface_octal10`` + one octal digit. So it is
directly testable against the R10.16C SurfaceWord profile, and it is
the only partition that CAN be falsified by existing evidence.

E12 sub-structure, per the source note:

    E12 = o3 epoch refinement | o3 epoch refinement | o3 epoch frequency
          | m3 check

so the final 3 bits are a check field by construction. See
:mod:`r1028.checksum` for why that field cannot be solved yet.
"""

from __future__ import annotations

from dataclasses import dataclass

WORD_BITS = 36
OCTAL_DIGITS = 12

#: Observed profile of the three verified 30-bit anchors (R10.16C).
#: A Core30 outside this profile is evidence against that partition for
#: that vector -- it is not proof, but it is a real test.
ANCHOR_F5 = frozenset({4, 5})
ANCHOR_S3 = frozenset({3})

PARTITIONS = {
    "R4_S8_P12_E12": (("R4", 4), ("S8", 8), ("P12", 12), ("E12", 12)),
    "H3_H3_CORE24_T3_T3": (("H3a", 3), ("H3b", 3), ("Core24", 24),
                           ("T3a", 3), ("T3b", 3)),
    "H3_CORE30_T3": (("H3", 3), ("Core30", 30), ("T3", 3)),
}

PARTITION_PRIORITY = {
    "R4_S8_P12_E12": "primary",
    "H3_H3_CORE24_T3_T3": "parallel",
    "H3_CORE30_T3": "parallel_demoted",
}


class Codec36Error(ValueError):
    pass


@dataclass(frozen=True)
class Block36:
    value: int

    def __post_init__(self):
        if not 0 <= self.value < (1 << WORD_BITS):
            raise Codec36Error(
                f"{self.value} does not fit in {WORD_BITS} bits")

    @property
    def octal(self) -> str:
        return format(self.value, f"0{OCTAL_DIGITS}o")

    def split(self, partition: str) -> dict:
        parts = PARTITIONS.get(partition)
        if parts is None:
            raise Codec36Error(f"unknown partition {partition!r}")
        out, pos = {}, WORD_BITS
        for name, width in parts:
            pos -= width
            out[name] = (self.value >> pos) & ((1 << width) - 1)
        if pos:                                   # pragma: no cover
            raise Codec36Error(f"{partition} does not sum to 36 bits")
        return out

    def e12_fields(self) -> dict:
        """o3 | o3 | o3 | m3, per the source note."""
        e = self.value & 0xFFF
        return {"epoch_refine_1": (e >> 9) & 7, "epoch_refine_2": (e >> 6) & 7,
                "epoch_frequency": (e >> 3) & 7, "m3_check": e & 7}


def to_blocks(value: int) -> list:
    """Split an arbitrary integer into 36-bit blocks, LOW-ORDER LAST.

    Blocks are cut from the least significant end so the final block is
    always full; a short block, if any, is the leading one. Which end
    the codec actually pads is NOT known, so ``leading_block_is_short``
    is reported rather than silently normalised.
    """
    if value < 0:
        raise Codec36Error("negative value")
    blocks, v = [], value
    if v == 0:
        return [Block36(0)]
    while v:
        blocks.append(Block36(v & ((1 << WORD_BITS) - 1)))
        v >>= WORD_BITS
    return list(reversed(blocks))


def core30_is_surfaceword_compatible(core30: int) -> dict:
    """Test a Core30 against the verified anchor profile."""
    f5, s3 = (core30 >> 25) & 31, core30 & 7
    return {"F5": f5, "S3": s3,
            "surface_octal10": format(core30, "010o"),
            "F5_in_anchor_profile": f5 in ANCHOR_F5,
            "S3_in_anchor_profile": s3 in ANCHOR_S3,
            "compatible": f5 in ANCHOR_F5 and s3 in ANCHOR_S3}


def analyse(value: int) -> dict:
    """Full partition report for one integer."""
    octal = format(value, "o")
    blocks = to_blocks(value)
    rows = []
    for i, b in enumerate(blocks):
        for pname in PARTITIONS:
            fields = b.split(pname)
            row = {"block_index": i, "block_octal": b.octal,
                   "partition": pname,
                   "priority": PARTITION_PRIORITY[pname],
                   **{f"field_{k}": v for k, v in fields.items()}}
            if pname == "H3_CORE30_T3":
                row.update({f"core30_{k}": v for k, v in
                            core30_is_surfaceword_compatible(
                                fields["Core30"]).items()})
            if pname == "R4_S8_P12_E12":
                row.update({f"e12_{k}": v for k, v in b.e12_fields().items()})
            rows.append(row)
    return {
        "value": value,
        "octal": octal,
        "octal_digits": len(octal),
        "bit_length": value.bit_length(),
        "single_block_exact_36_bit": len(octal) == OCTAL_DIGITS,
        "blocks": len(blocks),
        "leading_block_is_short": len(octal) % OCTAL_DIGITS != 0,
        "rows": rows,
    }
