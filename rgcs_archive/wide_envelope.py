"""R10.61 -- the 126-bit wide-envelope codec and its 36 legal splits.

FRAMING, CORRECTED
------------------
A long decimal record is framed in DECIMAL, not in octal::

    record  = decimal_header | decimal_payload | decimal_terminal
    header  = "16"
    terminal= "3"

For the reference fixture that gives a 37-digit payload whose integer is
**123 significant bits**. It is then LEFT-PADDED to the next legal
wide-envelope width, 126 bits = 42 octal digits.

An earlier revision of this analysis (R10.63) stripped the terminal in
OCTAL space instead -- it removed the last octal digit of the
header-stripped value. That also produced 126 bits, so it looked right,
but it is a different number:

    octal-stripped (wrong) 101672770075311773227352216477536105260021
    decimal-stripped (right) 064542306375724625654273330377576404214647

Every result computed on the first string was computed on the wrong
payload. :data:`SUPERSEDED_PAYLOAD_OCTAL` records it so the error cannot
quietly reappear, and :func:`fixture_receipt` asserts the correct one.

SUPERSEDED AS THE FRAMING AUTHORITY (R10.61A)
---------------------------------------------
This module treated 126 bits as arithmetically forced. It is not: the
payload's 123 significant bits are ALREADY a legal width (21 + 3*34), so
padding to 126 is a CHOICE. :mod:`rgcs_archive.framing` now carries five
profiles side by side with no default winner, and it is the framing
authority. What remains here is the split/grammar machinery, which is
profile-independent.

WIDTH LAW
---------
    W = 21 + 3D          126 = 21 + 3(35)        D = 35

so the record is ONE wide envelope carrying 35 three-bit refinement
symbols. It is not four independent fixed words; earlier width
segmentations admitted four blocks only because the framing bits had not
been removed.

GRAMMAR
-------
    C_L^(dL) | E3 | S_tor,6 | S_pol,6 | S_rad,6 | C_R^(dR)
    dL + dR = 35,  dL in 0..35  ->  36 legal splits

The outbound/inbound reading -- C_L ascending from the source-local
shell toward a pivot, C_R descending into the destination-local shell --
is SOURCE-PROVENANCE GUIDANCE, not verified semantics. No split is
selected. :func:`enumerate_splits` returns all 36 and ranks nothing.
"""

from __future__ import annotations

import hashlib

DECIMAL_HEADER = "16"
DECIMAL_TERMINAL = "3"

#: Legal wide-envelope widths follow W = 21 + 3D for integer D >= 0.
WIDTH_BASE = 21
WIDTH_STEP = 3

CORE_FIELDS = ("E3", "S_tor", "S_pol", "S_rad")
CORE_OCTAL_DIGITS = 7          # E3(1) + 2 + 2 + 2

#: SUPERSEDED as framing authority -- see rgcs_archive.framing.
FRAMING_AUTHORITY = "rgcs_archive.framing"
SUPERSEDED_AS_SINGLE_AUTHORITY = True

#: The reference fixture, under framing profile FP-B specifically.
FIXTURE_PROFILE = "FP-B"
FIXTURE_RECORD = "1687549873523387598456323376543328567433"
FIXTURE_PAYLOAD_DECIMAL = "8754987352338759845632337654332856743"
FIXTURE_SIGNIFICANT_BITS = 123
FIXTURE_WIDTH_BITS = 126
FIXTURE_PAYLOAD_OCTAL = "064542306375724625654273330377576404214647"
FIXTURE_D = 35
FIXTURE_SPLITS = 36

#: The R10.63 error, kept visible on purpose. Never use this value.
SUPERSEDED_PAYLOAD_OCTAL = "101672770075311773227352216477536105260021"
SUPERSEDED_REASON = (
    "R10.63 stripped the terminal in octal space (dropped the last octal "
    "digit of the header-stripped value) rather than in decimal space. It "
    "also yields 126 bits, so it passed casual inspection, but it is a "
    "different payload and every result computed on it is void.")


class EnvelopeError(ValueError):
    """The record is not a legal wide envelope."""


def legal_width(bits: int) -> bool:
    """Does ``bits`` satisfy W = 21 + 3D for integer D >= 0?"""
    return bits >= WIDTH_BASE and (bits - WIDTH_BASE) % WIDTH_STEP == 0


#: The fixture's 123 significant bits are THEMSELVES a legal width
#: (21 + 3*34), yet the specification pads to 126. So "next legal width"
#: means the next one STRICTLY GREATER, i.e. the envelope always carries
#: at least one leading pad bit. That convention is recorded here because
#: a reader could just as reasonably have stopped at 123, and the choice
#: changes D from 34 to 35 and the split count from 35 to 36.
REQUIRE_PAD_BIT = True


def next_legal_width(bits: int, require_pad: bool = REQUIRE_PAD_BIT) -> int:
    """Smallest legal envelope width above ``bits``.

    With ``require_pad`` (the specified behaviour) the result is strictly
    greater than ``bits``, so a payload never exactly fills its envelope.
    Set it False to get the smallest legal width at or above ``bits``.
    """
    if bits < WIDTH_BASE:
        return WIDTH_BASE
    over = (bits - WIDTH_BASE) % WIDTH_STEP
    exact = over == 0
    if exact:
        return bits + WIDTH_STEP if require_pad else bits
    return bits + (WIDTH_STEP - over)


def strip_framing(record: str) -> dict:
    """Remove the decimal header and terminal. Decimal space, not octal."""
    s = str(record).strip()
    if not s.isdigit():
        raise EnvelopeError(f"{record!r} is not a decimal record")
    if not s.startswith(DECIMAL_HEADER):
        raise EnvelopeError(
            f"record does not carry the {DECIMAL_HEADER!r} decimal header")
    if not s.endswith(DECIMAL_TERMINAL):
        raise EnvelopeError(
            f"record does not carry the {DECIMAL_TERMINAL!r} decimal terminal")
    payload = s[len(DECIMAL_HEADER):-len(DECIMAL_TERMINAL)]
    if not payload:
        raise EnvelopeError("nothing left after framing removal")
    return {
        "record": s,
        "header": DECIMAL_HEADER,
        "terminal": DECIMAL_TERMINAL,
        "payload_decimal": payload,
        "payload_digits": len(payload),
        "header_count_in_record": s.count(DECIMAL_HEADER),
    }


def parse_record(record: str) -> dict:
    """Full wide-envelope parse: framing, padding, width law, octal payload."""
    fr = strip_framing(record)
    value = int(fr["payload_decimal"])
    sig = value.bit_length()
    width = next_legal_width(sig)
    sig_is_itself_legal = legal_width(sig)
    if not legal_width(width):
        raise EnvelopeError(f"width {width} violates W = 21 + 3D")
    d = (width - WIDTH_BASE) // WIDTH_STEP
    if width % 3:
        raise EnvelopeError(f"width {width} is not a whole number of octal digits")
    octal = format(value, f"0{width // 3}o")
    chain_digits = len(octal) - CORE_OCTAL_DIGITS
    if chain_digits != d:
        raise EnvelopeError(
            f"chain digits {chain_digits} disagree with D={d} from the width law")
    return {
        "schema": "rgcs.r1061.wide-envelope.v1",
        **fr,
        "payload_int": value,
        "significant_bits": sig,
        "padded_width_bits": width,
        "pad_bits": width - sig,
        "significant_bits_are_themselves_a_legal_width": sig_is_itself_legal,
        "pad_convention": ("REQUIRE_AT_LEAST_ONE_PAD_BIT" if REQUIRE_PAD_BIT
                           else "SMALLEST_LEGAL_AT_OR_ABOVE"),
        "payload_octal": octal,
        "octal_digits": len(octal),
        "D": d,
        "legal_splits": d + 1,
        "width_law": f"W = {WIDTH_BASE} + {WIDTH_STEP}D  ->  "
                     f"{width} = {WIDTH_BASE} + {WIDTH_STEP}({d})",
        "result_class": "RGCS_ENVELOPE_CANDIDATE",
        "selected_split": None,
        "note": "no split is selected; enumerate_splits returns all of them",
    }


def split_at(payload_octal: str, d_left: int) -> dict:
    """One (dL, dR) split of the payload into chains and the 21-bit core."""
    n = len(payload_octal)
    total = n - CORE_OCTAL_DIGITS
    if total < 0:
        raise EnvelopeError(f"payload too short for the {CORE_OCTAL_DIGITS}-digit core")
    if not 0 <= d_left <= total:
        raise EnvelopeError(f"d_left {d_left} outside 0..{total}")
    i = 0
    c_left = payload_octal[i:i + d_left]; i += d_left
    e3 = payload_octal[i]; i += 1
    s_tor = payload_octal[i:i + 2]; i += 2
    s_pol = payload_octal[i:i + 2]; i += 2
    s_rad = payload_octal[i:i + 2]; i += 2
    c_right = payload_octal[i:]
    bit = lambda a, b: [a * 3, b * 3]                       # noqa: E731
    return {
        "d_left": d_left, "d_right": len(c_right),
        "chain_left": c_left, "chain_right": c_right,
        "chain_left_reversed": c_left[::-1],
        "chain_right_reversed": c_right[::-1],
        "E3": int(e3, 8),
        "S_tor": int(s_tor, 8), "S_pol": int(s_pol, 8), "S_rad": int(s_rad, 8),
        "bits_chain_left": bit(0, d_left),
        "bits_core": bit(d_left, d_left + CORE_OCTAL_DIGITS),
        "bits_chain_right": bit(d_left + CORE_OCTAL_DIGITS, n),
        "chain_direction_assumed": "L=outbound/ascending, R=inbound/descending",
        "pivot_semantics": "UNVERIFIED_SOURCE_PROVENANCE_GUIDANCE",
        "authority": "STRUCTURAL_PARSE_ONLY",
    }


def enumerate_splits(payload_octal: str) -> list:
    """Every legal split. Ranked by nothing, because nothing selects one."""
    total = len(payload_octal) - CORE_OCTAL_DIGITS
    return [split_at(payload_octal, d) for d in range(total + 1)]


def fixture_receipt() -> dict:
    """Reproduce the reference fixture and assert every quoted value.

    The spec's quoted numbers are checked rather than trusted: if any of
    them failed, this raises instead of adjusting the parser.
    """
    p = parse_record(FIXTURE_RECORD)
    checks = {
        "payload_decimal": (p["payload_decimal"], FIXTURE_PAYLOAD_DECIMAL),
        "significant_bits": (p["significant_bits"], FIXTURE_SIGNIFICANT_BITS),
        "padded_width_bits": (p["padded_width_bits"], FIXTURE_WIDTH_BITS),
        "payload_octal": (p["payload_octal"], FIXTURE_PAYLOAD_OCTAL),
        "D": (p["D"], FIXTURE_D),
        "legal_splits": (p["legal_splits"], FIXTURE_SPLITS),
    }
    bad = {k: v for k, v in checks.items() if v[0] != v[1]}
    if bad:
        raise EnvelopeError(f"fixture does not reproduce: {bad}")
    if p["payload_octal"] == SUPERSEDED_PAYLOAD_OCTAL:
        raise EnvelopeError("parser reproduced the superseded R10.63 payload")
    return {
        "schema": "rgcs.r1061.fixture-receipt.v1",
        "framing_profile_id": FIXTURE_PROFILE,
        "framing_authority": FRAMING_AUTHORITY,
        "note": "these values hold for FP-B only; FP-A gives 123 bits/D=34 "
                "and FP-C gives a different 126-bit payload",
        "record": FIXTURE_RECORD,
        "parse": p,
        "checks": {k: {"computed": a, "expected": b, "match": a == b}
                   for k, (a, b) in checks.items()},
        "all_match": True,
        "superseded_payload_rejected": SUPERSEDED_PAYLOAD_OCTAL,
        "superseded_reason": SUPERSEDED_REASON,
        "payload_sha256": hashlib.sha256(
            p["payload_octal"].encode()).hexdigest(),
    }
