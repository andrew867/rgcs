"""P19 — CW-PACK40-1: 4-bit header plus 36-bit path candidate codec.

A reversible arithmetic re-expression of two decimal fields into a single
40-bit word:

* a **header** field, 4 bits wide (``0..15``); and
* a **path** field, 36 bits wide (``0..2**36 - 1``), rendered as exactly
  **twelve octal digits** (3 bits per digit, ``12 * 3 == 36`` bits).

The packed word is ``(header << 36) | path``. Encoding and decoding are exact
inverses (a POWER round-trip): ``decode(encode(h, p)) == (h, p)`` for every
admissible pair. A value that exceeds its field width is **refused**, never
truncated or wrapped — silent truncation would fabricate a different word.

This is a CANDIDATE / legacy codec. Its output is a ``MATHEMATICAL_TRANSLATION``
— an arithmetic re-expression of an integer — and **never** a geographic
decode. Per System Contract invariant 4, a legacy decode may yield zero, one,
or many candidates, but it may never force a single geographic pin. See
:mod:`cwatlas.claims`.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from cwatlas import claims

#: Codec identity.
CODEC_ID = "CW-PACK40-1"
CODEC_VERSION = "1.0.0"

#: Field widths (bits). The header and path together fill the 40-bit word.
HEADER_BITS = 4
PATH_BITS = 36
TOTAL_BITS = HEADER_BITS + PATH_BITS  # 40

#: The 36-bit path is displayed as twelve base-8 digits (3 bits each).
OCTAL_DIGIT_BITS = 3
PATH_OCTAL_DIGITS = PATH_BITS // OCTAL_DIGIT_BITS  # 12

#: Inclusive maxima per field.
HEADER_MAX = (1 << HEADER_BITS) - 1  # 15
PATH_MAX = (1 << PATH_BITS) - 1  # 68719476735
PACKED_MAX = (1 << TOTAL_BITS) - 1


@dataclass(frozen=True)
class Pack40Word:
    """A single CW-PACK40-1 word and its exact field decomposition.

    Attributes
    ----------
    header:
        The 4-bit header value, ``0..15``.
    path:
        The 36-bit path value, ``0..2**36 - 1``.
    packed:
        The full 40-bit integer, ``(header << 36) | path``.
    path_octal:
        The 36-bit path rendered as exactly twelve octal digits.
    """

    header: int
    path: int
    packed: int
    path_octal: str


def _check_int(name: str, value: int) -> int:
    """Reject non-integers and booleans; return the plain int."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an int, got {type(value).__name__}")
    return value


def path_to_octal(path: int) -> str:
    """Render a 36-bit path as exactly twelve octal digits.

    Refuses a path outside ``0..PATH_MAX`` rather than truncating it.
    """
    path = _check_int("path", path)
    if not 0 <= path <= PATH_MAX:
        raise ValueError(
            f"path {path} out of range for {PATH_BITS}-bit field "
            f"(0..{PATH_MAX}); refused, not truncated")
    return format(path, f"0{PATH_OCTAL_DIGITS}o")


def octal_to_path(path_octal: str) -> int:
    """Parse exactly twelve octal digits back into a 36-bit path.

    Refuses any string that is not twelve base-8 digits.
    """
    if not isinstance(path_octal, str):
        raise ValueError("path_octal must be a str")
    if len(path_octal) != PATH_OCTAL_DIGITS:
        raise ValueError(
            f"path_octal must be exactly {PATH_OCTAL_DIGITS} digits, "
            f"got {len(path_octal)}")
    if any(ch not in "01234567" for ch in path_octal):
        raise ValueError("path_octal must contain only octal digits 0-7")
    value = int(path_octal, 8)
    # Twelve octal digits can only ever encode 36 bits, so this holds by
    # construction; assert the invariant defensively.
    assert 0 <= value <= PATH_MAX
    return value


def encode(header: int, path: int) -> Pack40Word:
    """Pack a ``(header, path)`` pair into a 40-bit CW-PACK40-1 word.

    Both fields are range-checked; an out-of-range value is refused, never
    truncated. Returns a :class:`Pack40Word` carrying the packed integer and
    the twelve-octal-digit rendering of the path.
    """
    header = _check_int("header", header)
    path = _check_int("path", path)
    if not 0 <= header <= HEADER_MAX:
        raise ValueError(
            f"header {header} out of range for {HEADER_BITS}-bit field "
            f"(0..{HEADER_MAX}); refused, not truncated")
    if not 0 <= path <= PATH_MAX:
        raise ValueError(
            f"path {path} out of range for {PATH_BITS}-bit field "
            f"(0..{PATH_MAX}); refused, not truncated")
    packed = (header << PATH_BITS) | path
    return Pack40Word(
        header=header,
        path=path,
        packed=packed,
        path_octal=path_to_octal(path),
    )


def decode(packed: int) -> Pack40Word:
    """Unpack a 40-bit CW-PACK40-1 word into its ``(header, path)`` fields.

    Exact inverse of :func:`encode`. Refuses a word outside the 40-bit range.
    """
    packed = _check_int("packed", packed)
    if not 0 <= packed <= PACKED_MAX:
        raise ValueError(
            f"packed {packed} out of range for {TOTAL_BITS}-bit word "
            f"(0..{PACKED_MAX}); refused")
    header = packed >> PATH_BITS
    path = packed & PATH_MAX
    return Pack40Word(
        header=header,
        path=path,
        packed=packed,
        path_octal=path_to_octal(path),
    )


def decode_octal(header: int, path_octal: str) -> Pack40Word:
    """Build a word from a header and a twelve-octal-digit path string."""
    return encode(header, octal_to_path(path_octal))


def _receipt_id(word: Pack40Word) -> str:
    """Deterministic receipt id derived from codec identity and payload.

    No wall-clock; identical inputs always yield the same id.
    """
    digest = hashlib.sha256(
        f"{CODEC_ID}:{CODEC_VERSION}:{word.packed}".encode("ascii")
    ).hexdigest()[:16]
    return f"{CODEC_ID}-{digest}"


def to_codec_result(word: Pack40Word) -> dict:
    """Emit a CodecResult dict (per ``codec_result.schema.json``).

    The result is a ``MATHEMATICAL_TRANSLATION``: the packed word is
    re-expressed arithmetically, never decoded to a place. The status is
    ``NO_UNIQUE_GEOGRAPHIC_DECODE`` because a legacy candidate codec never
    forces one geographic pin (invariant 4).
    """
    candidate = {
        "claim_class": claims.ClaimClass.MATHEMATICAL_TRANSLATION.value,
        "header": word.header,
        "path": word.path,
        "packed": word.packed,
        "path_octal": word.path_octal,
        "bit_layout": f"{HEADER_BITS}-bit header + {PATH_BITS}-bit path",
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
    """Refuse any attempt to treat a packed CW-PACK40-1 word as a location."""
    return claims.refuse_source_as_geographic()


def codec_pack40_report() -> dict:
    """Governance report: what this codec is and, emphatically, is not."""
    return {
        "phase": "P19",
        "what_this_is": (
            "CW-PACK40-1, a reversible 4-bit-header + 36-bit-path (twelve "
            "octal digits) arithmetic packing codec"),
        "codec_id": CODEC_ID,
        "codec_version": CODEC_VERSION,
        "bit_layout": {
            "header_bits": HEADER_BITS,
            "path_bits": PATH_BITS,
            "total_bits": TOTAL_BITS,
            "path_octal_digits": PATH_OCTAL_DIGITS,
            "header_max": HEADER_MAX,
            "path_max": PATH_MAX,
        },
        "reversible": True,
        "overflow_policy": "REFUSED_NOT_TRUNCATED",
        "claim_class": claims.ClaimClass.MATHEMATICAL_TRANSLATION.value,
        "level": "SOFTWARE",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "CW_ATLAS_PACK40_REVERSIBLE_NO_GEO_CLAIM",
        "what_this_does_not_say": (
            "A packed 40-bit word is an arithmetic re-expression of two "
            "integers, not a place. A legacy decode yields zero, one, or many "
            "candidates and never a forced geographic pin."),
    }
