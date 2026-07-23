"""P07 — CW packed-decimal / mixed-radix codec V2, with null windows.

This is the second-generation companion to the R10.6 reversible-view
search (``r10/base10.py`` is codec V1). V1 asked whether any reversible
base-N *view* of the twelve-digit CW vectors exposes structure a matched
null does not; the answer was **NO_DECODER_IDENTIFIED**. V2 does not
re-open that question. It hardens the machinery instead: it makes the
packing, the mixed-radix layout, and the injectivity **exact and
auditable**, and it adds a discipline V1 lacked -- a *null window* that
keeps unknown digits NULL until a padding rule is independently supplied.

The load-bearing idea, restated because it is the whole point:

    A reversible codec RELOCATES information; it cannot CREATE it.

Rewriting a twelve-digit number as forty bits, or as a four-bit header
plus a twelve-octal-digit path, moves the same information into a
different frame. Every bit that comes out was already in. So a clean
**round-trip is necessary but never sufficient** to claim a decoding:
the round-trip proves the frame is lossless, and proves nothing about
content. A perfectly reversible codec over meaningless input yields
perfectly reversible meaningless output.

The **null window** is the second discipline. When some digit positions
are genuinely UNKNOWN, the honest representation leaves them ``None``.
The codec refuses to fill a masked position on its own, because any
digit it invented would be indistinguishable, on round-trip, from a
digit that was really there -- reversibility would *launder* the
invention. Masked positions stay NULL until an explicit, external
``padding_rule`` supplies them; there is no default padding, and no
"obvious" fill.

Because V2 only relocates and never recovers, its standing verdict
carries V1's result forward: **REVERSIBLE_CODEC_NO_CONTENT /
NO_DECODER_IDENTIFIED**. A codec that was *preregistered* -- frozen
before its output was inspected and then confirmed against held-out
material -- would be a different result. Nothing here is that. Nothing
here is measured, and no physical quantity is claimed.

All inputs are GENERIC twelve-digit decimals supplied by the caller.
This module hardcodes no real CW vector.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum

WINDOW_WIDTH = 12                       # decimal digits per vector
PACK_BITS = 40                          # 2**39 < 10**12 <= 2**40
HEADER_BITS = 4                         # header field, 0..15
PATH_BITS = 36                          # 12 octal digits * 3 bits
PATH_DIGITS = 12                        # octal digits in the path
DECIMAL_MODULUS = 10 ** WINDOW_WIDTH    # 10**12


class CodecError(ValueError):
    """Raised on a non-reversible codec, an out-of-range field, an
    attempt to pad a null window without a rule, or a retrofit decode."""


class DerivationFamily(Enum):
    PACKED_DECIMAL = "PACKED_DECIMAL"
    MIXED_RADIX = "MIXED_RADIX_HEADER_PATH"


class NullFamily(Enum):
    NO_WINDOW = "NO_NULL_WINDOW"
    NULL_WINDOW = "NULL_WINDOW"


class CollisionClass(Enum):
    INJECTIVE = "INJECTIVE"
    COLLIDING = "COLLIDING"


# --- the result schema -------------------------------------------------

@dataclass(frozen=True)
class CodecResult:
    """One vector viewed through the V2 codec. Every field is either an
    exact reversible relabeling of the input or an explicit NULL."""

    vector_id: str
    raw_decimal: int | None
    window_width: int
    null_mask: tuple[bool, ...]
    offset: int
    padding_rule: str | None
    packed_integer: int | None
    bit_width: int
    header_width: int
    header_value: int | None
    path_width: int
    octal_path: str | None
    mixed_radix_layout: tuple
    inverse_transform: str
    round_trip: bool | None
    collision_class: str
    derivation_family: str
    null_family: str
    prospective_status: str


#: The mixed-radix layout, as (field_name, width_bits, radix) descriptors.
MIXED_RADIX_LAYOUT = (
    ("header", HEADER_BITS, 16),
    ("octal_path", PATH_BITS, 8),
)


# --- packed decimal: 40 bits, exactly, and 40 is minimal ---------------

def pack_decimal(n: int) -> int:
    """Pack a 12-digit decimal (0..10**12-1) into a 40-bit code, exactly.

    The value IS the code: a 12-digit decimal fits in 40 bits because
    2**39 < 10**12 <= 2**40. The packing is lossless by construction and
    inverted by :func:`unpack_decimal`."""
    if not isinstance(n, int) or isinstance(n, bool):
        raise CodecError("packed input must be a plain int")
    if not 0 <= n < DECIMAL_MODULUS:
        raise CodecError(
            f"value {n} outside the 12-digit range [0, 10**12)")
    return n & ((1 << PACK_BITS) - 1)


def unpack_decimal(bits: int) -> int:
    """Invert :func:`pack_decimal`. Exact for any packed 12-digit code."""
    if not isinstance(bits, int) or isinstance(bits, bool):
        raise CodecError("packed code must be a plain int")
    if not 0 <= bits < (1 << PACK_BITS):
        raise CodecError(f"code {bits} does not fit in {PACK_BITS} bits")
    if bits >= DECIMAL_MODULUS:
        raise CodecError(
            f"code {bits} is a valid 40-bit pattern but not a 12-digit "
            f"decimal; the 40-bit space is larger than 10**12")
    return bits


def packed_decimal_bits() -> dict:
    """State the bit-width facts exactly. 40 is minimal; 39 is not."""
    return {
        "bits": (DECIMAL_MODULUS - 1).bit_length(),      # 40
        "lower_bound": "2**39 < 10**12",
        "lower_holds": 2 ** 39 < DECIMAL_MODULUS,
        "upper_bound": "10**12 <= 2**40",
        "upper_holds": DECIMAL_MODULUS <= 2 ** 40,
    }


def prove_bit_width_minimal() -> dict:
    """39 bits cannot hold 10**12 distinct codes: pigeonhole.

    A 39-bit field has 2**39 = 549,755,813,888 patterns, which is fewer
    than 10**12 = 1,000,000,000,000 twelve-digit values, so any 39-bit
    encoding of all twelve-digit decimals must map two distinct inputs
    to one code -- it cannot be injective."""
    codes_39 = 2 ** 39
    codes_40 = 2 ** 40
    return {
        "needed_values": DECIMAL_MODULUS,
        "capacity_39_bits": codes_39,
        "capacity_40_bits": codes_40,
        "39_is_insufficient": codes_39 < DECIMAL_MODULUS,
        "40_is_sufficient": codes_40 >= DECIMAL_MODULUS,
        "minimal_bits": PACK_BITS,
        "pigeonhole": (
            "2**39 < 10**12, so a 39-bit field has fewer codes than "
            "there are 12-digit values and cannot be injective"),
    }


# --- mixed radix: 4-bit header + 36-bit octal path ---------------------

def encode_header_path(header: int, octal_digits) -> int:
    """Pack a 4-bit header and twelve octal digits into a 40-bit code.

    header in 0..15 occupies the top 4 bits; the twelve base-8 digits
    (each 0..7) occupy the low 36 bits, most-significant digit first.
    Exactly inverted by :func:`decode_header_path`."""
    if not isinstance(header, int) or isinstance(header, bool):
        raise CodecError("header must be a plain int")
    if not 0 <= header < (1 << HEADER_BITS):
        raise CodecError(f"header {header} outside 0..15")
    digits = tuple(octal_digits)
    if len(digits) != PATH_DIGITS:
        raise CodecError(f"octal path must have {PATH_DIGITS} digits")
    path = 0
    for d in digits:
        if not isinstance(d, int) or isinstance(d, bool) or not 0 <= d < 8:
            raise CodecError(f"octal digit {d!r} outside 0..7")
        path = (path << 3) | d
    return (header << PATH_BITS) | path


def decode_header_path(code: int) -> tuple:
    """Invert :func:`encode_header_path`: (header, twelve octal digits)."""
    if not isinstance(code, int) or isinstance(code, bool):
        raise CodecError("code must be a plain int")
    if not 0 <= code < (1 << PACK_BITS):
        raise CodecError(f"code {code} does not fit in {PACK_BITS} bits")
    header = code >> PATH_BITS
    path = code & ((1 << PATH_BITS) - 1)
    digits = []
    for shift in range(PATH_DIGITS - 1, -1, -1):
        digits.append((path >> (3 * shift)) & 0x7)
    return header, tuple(digits)


def octal_path_string(octal_digits) -> str:
    return "".join(str(d) for d in octal_digits)


# --- radix views: relabelings of one number ----------------------------

@dataclass(frozen=True)
class RadixView:
    """One rendering of an integer in some radix. ``value`` is the
    underlying integer; ``payload`` is the rendering. Two views with the
    same ``value`` are relabelings -- they carry identical information."""

    name: str
    radix: int
    payload: str
    value: int


def decimal_view(n: int) -> RadixView:
    return RadixView("decimal", 10, str(n).zfill(WINDOW_WIDTH), n)


def binary_view(n: int) -> RadixView:
    return RadixView("binary", 2, format(n, f"0{PACK_BITS}b"), n)


def octal_view(n: int) -> RadixView:
    return RadixView("octal", 8, format(n, "o"), n)


def is_relabeling(a_view: RadixView, b_view: RadixView) -> bool:
    """True iff two radix views render the same underlying integer.

    Different renderings of one number are relabelings, not new content:
    the payloads differ, the information does not."""
    return a_view.value == b_view.value


# --- null windows: unknown stays NULL until a rule is supplied ---------

@dataclass(frozen=True)
class PaddingRule:
    """An explicit, external rule that fills masked positions. There is
    no default rule; a position is filled only if this rule names it."""

    rule_id: str
    fills: dict                          # position -> decimal digit 0..9

    def fill(self, position: int) -> int:
        if position not in self.fills:
            raise CodecError(
                f"padding rule {self.rule_id!r} does not cover masked "
                f"position {position}; it may not be filled")
        d = self.fills[position]
        if not isinstance(d, int) or isinstance(d, bool) or not 0 <= d < 10:
            raise CodecError(f"padding digit {d!r} outside 0..9")
        return d


def _normalise_mask(null_mask) -> tuple:
    if null_mask is None:
        return (False,) * WINDOW_WIDTH
    mask = tuple(bool(x) for x in null_mask)
    if len(mask) != WINDOW_WIDTH:
        raise CodecError(f"null_mask must have {WINDOW_WIDTH} positions")
    return mask


def masked_digits(raw_decimal: int, null_mask,
                  padding_rule: PaddingRule | None = None) -> list:
    """Render the digits, keeping masked positions NULL.

    An unmasked position shows its decimal digit. A masked position is
    ``None`` unless ``padding_rule`` explicitly supplies it -- the raw
    digit under a mask is treated as unknown and is never used to fill."""
    mask = _normalise_mask(null_mask)
    digs = [int(c) for c in str(raw_decimal).zfill(WINDOW_WIDTH)]
    if len(digs) != WINDOW_WIDTH:
        raise CodecError("raw_decimal exceeds 12 digits")
    out: list = []
    for i, d in enumerate(digs):
        if mask[i]:
            out.append(None if padding_rule is None
                       else padding_rule.fill(i))
        else:
            out.append(d)
    return out


def refuse_padding_without_rule(null_mask) -> None:
    """Refuse to fill a null window when no padding rule is supplied.

    A masked position is genuinely unknown; inventing a digit for it and
    then round-tripping would launder the invention as if it had been
    real. Filling requires an explicit external rule."""
    mask = _normalise_mask(null_mask)
    if any(mask):
        raise CodecError(
            "refused: a null window has UNKNOWN positions and no padding "
            "rule was supplied. Masked digits stay NULL; a reversible "
            "codec must not invent a digit, because the round-trip would "
            "then present the invention as recovered content. Supply an "
            "explicit padding_rule to fill them.")


# --- collision audit: a lossless codec must not collide ----------------

def collision_scan(inputs, transform=pack_decimal) -> dict:
    """Verify ``transform`` is injective over ``inputs``.

    A lossless codec maps distinct inputs to distinct codes. A lossy map
    -- one that truncates or drops information -- can send two distinct
    inputs to one code, and this scan detects it."""
    seen: dict = {}
    collisions = []
    for n in inputs:
        code = transform(n)
        if code in seen and seen[code] != n:
            collisions.append((seen[code], n, code))
        else:
            seen.setdefault(code, n)
    injective = not collisions
    return {
        "count": len(list(inputs)) if not hasattr(inputs, "__len__")
        else len(inputs),
        "distinct_codes": len(seen),
        "collisions": collisions,
        "injective": injective,
        "collision_class": (CollisionClass.INJECTIVE.value if injective
                            else CollisionClass.COLLIDING.value),
    }


def lossy_truncating_map(n: int) -> int:
    """A deliberately lossy view: drop the most-significant digit.

    Provided so the collision audit has something that DOES collide --
    ``n % 10**11`` maps every pair of 12-digit numbers that share their
    low 11 digits to the same code. Not a codec; a negative control."""
    if not 0 <= n < DECIMAL_MODULUS:
        raise CodecError("value outside the 12-digit range")
    return n % (10 ** (WINDOW_WIDTH - 1))


# --- no retrofit: a decoding claimed after the fact is refused ---------

def refuse_retrofit_decoding(*_args, **_kwargs) -> None:
    """Refuse a decoding claimed AFTER inspecting the codec's outputs.

    A frame chosen because its output "looks meaningful" is fitted to
    the data, not tested against it. Only a preregistered decoder --
    frozen before its output was seen and confirmed on held-out
    material -- could claim content. Carry forward NO_DECODER_IDENTIFIED:
    a reversible codec that relocates information is never, by that fact,
    a recovery of content."""
    raise CodecError(
        "refused: no retrofit decoding. A decoder identified after "
        "inspecting the codec's outputs is fitted, not preregistered, "
        "and a reversible relabeling of a number is not recovered "
        "content. The standing result is NO_DECODER_IDENTIFIED / "
        "REVERSIBLE_CODEC_NO_CONTENT.")


# --- assembling a CodecResult ------------------------------------------

def encode_vector(vector_id: str, raw_decimal: int, *,
                  null_mask=None, offset: int = 0,
                  padding_rule: PaddingRule | None = None,
                  derivation_family: DerivationFamily
                  = DerivationFamily.PACKED_DECIMAL) -> CodecResult:
    """Build a :class:`CodecResult` for one generic 12-digit input.

    With no null window (or a fully filled one) the packed 40-bit code,
    its header/octal-path relabeling, and the round-trip are all
    present. With an unfilled null window the masked positions are NULL,
    no code can be formed, and the status is NULL_UNTIL_RULE_SUPPLIED."""
    if not 0 <= raw_decimal < DECIMAL_MODULUS:
        raise CodecError("raw_decimal outside the 12-digit range")
    mask = _normalise_mask(null_mask)
    has_window = any(mask)
    null_family = (NullFamily.NULL_WINDOW if has_window
                   else NullFamily.NO_WINDOW)

    digs = masked_digits(raw_decimal, mask, padding_rule)
    unfilled = any(d is None for d in digs)

    if unfilled:
        packed = None
        header_value = None
        octal_path = None
        round_trip = None
        prospective_status = "NULL_UNTIL_RULE_SUPPLIED"
        stored_raw = None                # unknown digits: no whole value
    else:
        value = int("".join(str(d) for d in digs))
        packed = pack_decimal(value)
        header_value, octal_digits = decode_header_path(packed)
        octal_path = octal_path_string(octal_digits)
        round_trip = (unpack_decimal(packed) == value
                      and encode_header_path(header_value,
                                             octal_digits) == packed)
        prospective_status = "NO_PREREGISTERED_DECODER"
        stored_raw = value

    return CodecResult(
        vector_id=vector_id,
        raw_decimal=stored_raw,
        window_width=WINDOW_WIDTH,
        null_mask=mask,
        offset=offset,
        padding_rule=(padding_rule.rule_id if padding_rule else None),
        packed_integer=packed,
        bit_width=PACK_BITS,
        header_width=HEADER_BITS,
        header_value=header_value,
        path_width=PATH_BITS,
        octal_path=octal_path,
        mixed_radix_layout=MIXED_RADIX_LAYOUT,
        inverse_transform=(
            "unpack_decimal(pack_decimal(x)) == x; "
            "decode_header_path(encode_header_path(h, p)) == (h, p)"),
        round_trip=round_trip,
        collision_class=CollisionClass.INJECTIVE.value,
        derivation_family=derivation_family.value,
        null_family=null_family.value,
        prospective_status=prospective_status,
    )


def result_fingerprint(result: CodecResult) -> str:
    """A stable hash of the reversible fields, for an audit trail."""
    parts = (result.vector_id, str(result.raw_decimal),
             str(result.packed_integer), str(result.header_value),
             str(result.octal_path), "".join("1" if m else "0"
                                              for m in result.null_mask),
             result.prospective_status)
    return hashlib.sha256("\x1f".join(parts).encode()).hexdigest()


# --- the report --------------------------------------------------------

def cwcodec2_report() -> dict:
    return {
        "what_this_is": (
            "a packed-decimal and mixed-radix (4-bit header + 12-octal-"
            "digit path) codec with null windows; a hardened V2 of the "
            "R10.6 reversible-view search"),
        "packed_decimal_bits": packed_decimal_bits(),
        "bit_width_minimal": prove_bit_width_minimal(),
        "mixed_radix_layout": list(MIXED_RADIX_LAYOUT),
        "null_window_discipline": (
            "masked positions stay None until an explicit padding_rule is "
            "supplied; the codec never invents a digit, because a "
            "reversible round-trip would launder the invention as "
            "recovered content"),
        "evidence_class": "DERIVED_MATHEMATICS",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": "REVERSIBLE_CODEC_NO_CONTENT",
        "decoder_status": "NO_DECODER_IDENTIFIED",
        "what_this_does_not_say": (
            "It does not say the vectors are meaningless, and it does not "
            "say no codec exists. It says a reversible codec RELOCATES "
            "information and cannot CREATE it, so a clean round-trip is "
            "necessary but never sufficient to claim a decoding. Masked "
            "digits are kept NULL rather than padded, because no padding "
            "rule is independently supplied here. A preregistered codec, "
            "frozen before its output was seen and confirmed on held-out "
            "material, would be a different result; this is "
            "NO_DECODER_IDENTIFIED, not NO_DECODER_POSSIBLE."),
    }
