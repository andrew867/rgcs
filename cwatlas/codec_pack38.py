"""P20 — CW-PACK38-1: 2-bit header plus three 12-bit fields candidate codec.

The earlier 38-bit packing candidate, retained as a separate versioned codec
(System Contract: preserve every legacy interpretation as a named version).

A reversible arithmetic re-expression of four decimal fields into a single
38-bit word:

* a **header** field, 2 bits wide (``0..3``); and
* **three** field values, each 12 bits wide (``0..4095``).

The packed word is ``(header << 36) | (f0 << 24) | (f1 << 12) | f2`` — that is,
``2 + 3 * 12 == 38`` bits. Encoding and decoding are exact inverses:
``decode(encode(h, (f0, f1, f2))) == (h, (f0, f1, f2))`` for every admissible
tuple. Any field that exceeds its width is **refused**, never truncated.

This is a CANDIDATE / legacy codec. Its output is a ``MATHEMATICAL_TRANSLATION``
— an arithmetic re-expression — and **never** a geographic decode. Per System
Contract invariant 4, a legacy decode may yield zero, one, or many candidates,
never a forced geographic pin. See :mod:`cwatlas.claims`.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from cwatlas import claims

#: Codec identity.
CODEC_ID = "CW-PACK38-1"
CODEC_VERSION = "1.0.0"

#: Field widths (bits).
HEADER_BITS = 2
FIELD_BITS = 12
NUM_FIELDS = 3
TOTAL_BITS = HEADER_BITS + NUM_FIELDS * FIELD_BITS  # 38

#: Inclusive maxima per field.
HEADER_MAX = (1 << HEADER_BITS) - 1  # 3
FIELD_MAX = (1 << FIELD_BITS) - 1  # 4095
PACKED_MAX = (1 << TOTAL_BITS) - 1

#: Left-shift for each of the three fields (most significant first).
_FIELD_SHIFTS = tuple(
    (NUM_FIELDS - 1 - i) * FIELD_BITS for i in range(NUM_FIELDS)
)  # (24, 12, 0)


@dataclass(frozen=True)
class Pack38Word:
    """A single CW-PACK38-1 word and its exact field decomposition.

    Attributes
    ----------
    header:
        The 2-bit header value, ``0..3``.
    fields:
        The three 12-bit field values, each ``0..4095``, most significant
        first.
    packed:
        The full 38-bit integer.
    """

    header: int
    fields: tuple[int, int, int]
    packed: int


def _check_int(name: str, value: int) -> int:
    """Reject non-integers and booleans; return the plain int."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an int, got {type(value).__name__}")
    return value


def _check_fields(fields) -> tuple[int, int, int]:
    """Validate a 3-tuple of 12-bit field values; refuse overflow."""
    seq = tuple(fields)
    if len(seq) != NUM_FIELDS:
        raise ValueError(
            f"expected exactly {NUM_FIELDS} fields, got {len(seq)}")
    checked = []
    for idx, val in enumerate(seq):
        val = _check_int(f"field[{idx}]", val)
        if not 0 <= val <= FIELD_MAX:
            raise ValueError(
                f"field[{idx}] {val} out of range for {FIELD_BITS}-bit field "
                f"(0..{FIELD_MAX}); refused, not truncated")
        checked.append(val)
    return tuple(checked)  # type: ignore[return-value]


def encode(header: int, fields) -> Pack38Word:
    """Pack a header and three 12-bit fields into a 38-bit CW-PACK38-1 word.

    Every field is range-checked; an out-of-range value is refused, never
    truncated.
    """
    header = _check_int("header", header)
    if not 0 <= header <= HEADER_MAX:
        raise ValueError(
            f"header {header} out of range for {HEADER_BITS}-bit field "
            f"(0..{HEADER_MAX}); refused, not truncated")
    checked = _check_fields(fields)
    packed = header << (NUM_FIELDS * FIELD_BITS)
    for val, shift in zip(checked, _FIELD_SHIFTS):
        packed |= val << shift
    return Pack38Word(header=header, fields=checked, packed=packed)


def decode(packed: int) -> Pack38Word:
    """Unpack a 38-bit CW-PACK38-1 word into its header and three fields.

    Exact inverse of :func:`encode`. Refuses a word outside the 38-bit range.
    """
    packed = _check_int("packed", packed)
    if not 0 <= packed <= PACKED_MAX:
        raise ValueError(
            f"packed {packed} out of range for {TOTAL_BITS}-bit word "
            f"(0..{PACKED_MAX}); refused")
    header = packed >> (NUM_FIELDS * FIELD_BITS)
    fields = tuple(
        (packed >> shift) & FIELD_MAX for shift in _FIELD_SHIFTS
    )
    return Pack38Word(header=header, fields=fields, packed=packed)


def _receipt_id(word: Pack38Word) -> str:
    """Deterministic receipt id derived from codec identity and payload."""
    digest = hashlib.sha256(
        f"{CODEC_ID}:{CODEC_VERSION}:{word.packed}".encode("ascii")
    ).hexdigest()[:16]
    return f"{CODEC_ID}-{digest}"


def to_codec_result(word: Pack38Word) -> dict:
    """Emit a CodecResult dict (per ``codec_result.schema.json``).

    A ``MATHEMATICAL_TRANSLATION`` with status ``NO_UNIQUE_GEOGRAPHIC_DECODE``:
    the packed word is re-expressed arithmetically, never decoded to a place,
    and no single geographic pin is forced (invariant 4).
    """
    candidate = {
        "claim_class": claims.ClaimClass.MATHEMATICAL_TRANSLATION.value,
        "header": word.header,
        "fields": list(word.fields),
        "packed": word.packed,
        "bit_layout": (
            f"{HEADER_BITS}-bit header + {NUM_FIELDS}x{FIELD_BITS}-bit fields"),
        "interpretation": "arithmetic re-expression only; not a location",
    }
    return {
        "status": "NO_UNIQUE_GEOGRAPHIC_DECODE",
        "codec_id": CODEC_ID,
        "candidates": [candidate],
        "receipt_id": _receipt_id(word),
        "warnings": [
            "MATHEMATICAL_TRANSLATION: this is an arithmetic re-expression, "
            "not a geographic decode; no pin is produced.",
        ],
    }


def refuse_as_geographic(*_a, **_k):
    """Refuse any attempt to treat a packed CW-PACK38-1 word as a location."""
    return claims.refuse_source_as_geographic()


def codec_pack38_report() -> dict:
    """Governance report: what this codec is and, emphatically, is not."""
    return {
        "phase": "P20",
        "what_this_is": (
            "CW-PACK38-1, a reversible 2-bit-header + three-12-bit-field "
            "arithmetic packing codec (the earlier 38-bit candidate)"),
        "codec_id": CODEC_ID,
        "codec_version": CODEC_VERSION,
        "bit_layout": {
            "header_bits": HEADER_BITS,
            "field_bits": FIELD_BITS,
            "num_fields": NUM_FIELDS,
            "total_bits": TOTAL_BITS,
            "header_max": HEADER_MAX,
            "field_max": FIELD_MAX,
        },
        "reversible": True,
        "overflow_policy": "REFUSED_NOT_TRUNCATED",
        "claim_class": claims.ClaimClass.MATHEMATICAL_TRANSLATION.value,
        "level": "SOFTWARE",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "CW_ATLAS_PACK38_REVERSIBLE_NO_GEO_CLAIM",
        "what_this_does_not_say": (
            "A packed 38-bit word is an arithmetic re-expression of four "
            "integers, not a place. A legacy decode yields zero, one, or many "
            "candidates and never a forced geographic pin."),
    }
