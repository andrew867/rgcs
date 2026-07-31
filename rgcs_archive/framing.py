"""R10.61A -- framing profiles. Five readings, no default winner.

THE CORRECTION THIS MODULE EXISTS FOR
-------------------------------------
R10.61 treated 126 bits as arithmetically forced. It is not. The decimal
payload has **123 significant bits**, and::

    123 = 21 + 3*34

so 123 is ALREADY a legal wide-envelope width. Padding to 126 is a
CHOICE, and calling it "the next legal width" concealed that. The correct
phrasing, used throughout this module, is:

    the first legal width STRICTLY GREATER than the significant width

Five profiles are carried side by side. Every parse receipt names its
:data:`framing_profile_id`, and nothing selects one.

A profile may NEVER be promoted because it yields readable text, a smooth
route, a famous place, a preferred state triple, a smaller geometry
residual, or a better-looking visualisation. Promotion requires an
independently frozen framing rule, or multiple external records that
prospectively discriminate between profiles.

FP-C IS NOT FP-B
----------------
Stripping a 3-bit field from each edge of the 132-bit container is not
the same operation as removing decimal characters, and it does not
produce the same payload:

    FP-B  064542306375724625654273330377576404214647
    FP-C  365444442152520604177466460607536105260021

Both are 126 bits and D=35. They are different numbers. That is asserted
by test.
"""

from __future__ import annotations

import hashlib

WIDTH_BASE = 21
WIDTH_STEP = 3
CORE_OCTAL_DIGITS = 7                      # E3(1) + S_tor(2) + S_pol(2) + S_rad(2)

DECIMAL_HEADER = "16"
DECIMAL_TERMINAL = "3"
CONTAINER_BITS = 132
EDGE_FIELD_BITS = 3

FIXTURE_RECORD = "1687549873523387598456323376543328567433"

#: Statuses a profile may carry. There is no "SELECTED".
PROFILE_STATUS = ("ACTIVE_CANDIDATE", "DIAGNOSTIC_ONLY", "SUPERSEDED")

#: Reasons a profile may NEVER be promoted.
FORBIDDEN_PROMOTION_GROUNDS = (
    "readable_text", "smooth_route", "famous_place", "preferred_state_triple",
    "smaller_geometry_residual", "better_looking_visualization",
)


class FramingError(ValueError):
    """A record cannot be framed under the requested profile."""


def legal_width(bits: int) -> bool:
    return bits >= WIDTH_BASE and (bits - WIDTH_BASE) % WIDTH_STEP == 0


def first_legal_width_strictly_greater(bits: int) -> int:
    """The first legal width STRICTLY GREATER than ``bits``.

    Deliberately not called "next legal width": when ``bits`` is itself
    legal -- as 123 is -- that phrasing hides a choice.
    """
    w = max(WIDTH_BASE, bits + 1)
    while not legal_width(w):
        w += 1
    return w


def smallest_legal_width_at_or_above(bits: int) -> int:
    if bits <= WIDTH_BASE:
        return WIDTH_BASE
    over = (bits - WIDTH_BASE) % WIDTH_STEP
    return bits if over == 0 else bits + (WIDTH_STEP - over)


def _decimal_payload(record: str) -> str:
    s = str(record).strip()
    if not s.isdigit():
        raise FramingError(f"{record!r} is not a decimal record")
    if not (s.startswith(DECIMAL_HEADER) and s.endswith(DECIMAL_TERMINAL)):
        raise FramingError("record lacks the decimal '16' header / '3' terminal")
    return s[len(DECIMAL_HEADER):-len(DECIMAL_TERMINAL)]


def _envelope(octal: str, width: int, **extra) -> dict:
    d = (width - WIDTH_BASE) // WIDTH_STEP
    chain = len(octal) - CORE_OCTAL_DIGITS
    if chain != d:
        raise FramingError(f"chain digits {chain} disagree with D={d}")
    return {
        "envelope_width_bits": width,
        "octal_payload": octal,
        "octal_digits": len(octal),
        "D": d,
        "legal_splits": d + 1,
        "width_law": f"W = 21 + 3D  ->  {width} = 21 + 3({d})",
        **extra,
    }


def fp_a(record: str) -> dict:
    """FP-A DECIMAL_AFFIX_MINIMAL -- no padding. 123 bits is already legal."""
    pay = _decimal_payload(record)
    v = int(pay)
    sig = v.bit_length()
    if not legal_width(sig):
        raise FramingError(
            f"significant width {sig} is not legal; FP-A does not apply")
    return _envelope(format(v, f"0{sig // 3}o"), sig,
                     framing_profile_id="FP-A",
                     name="DECIMAL_AFFIX_MINIMAL",
                     status="ACTIVE_CANDIDATE",
                     padding="NO_PADDING",
                     significant_bits=sig, pad_bits=0,
                     decimal_payload=pay,
                     rule="strip decimal '16' prefix and '3' suffix; the "
                          "significant width is itself legal, so no padding "
                          "is applied")


def fp_b(record: str) -> dict:
    """FP-B DECIMAL_AFFIX_STRICT_NEXT -- pad to the first STRICTLY greater."""
    pay = _decimal_payload(record)
    v = int(pay)
    sig = v.bit_length()
    w = first_legal_width_strictly_greater(sig)
    return _envelope(format(v, f"0{w // 3}o"), w,
                     framing_profile_id="FP-B",
                     name="DECIMAL_AFFIX_STRICT_NEXT",
                     status="ACTIVE_CANDIDATE",
                     padding="PAD_STRICT_NEXT",
                     significant_bits=sig, pad_bits=w - sig,
                     decimal_payload=pay,
                     rule="strip the decimal affixes, then left-pad to the "
                          "FIRST LEGAL WIDTH STRICTLY GREATER than the "
                          "significant width")


def fp_c(record: str) -> dict:
    """FP-C FIXED132_EDGE_FIELDS -- strip one 3-bit field from each edge.

    A bit-field operation on the 132-bit container. NOT equivalent to
    removing decimal characters, and it yields a different payload.
    """
    s = str(record).strip()
    if not s.isdigit():
        raise FramingError(f"{record!r} is not a decimal record")
    v = int(s)
    if v.bit_length() > CONTAINER_BITS:
        raise FramingError(
            f"record needs {v.bit_length()} bits, container is {CONTAINER_BITS}")
    bits = format(v, f"0{CONTAINER_BITS}b")
    prefix, suffix = bits[:EDGE_FIELD_BITS], bits[-EDGE_FIELD_BITS:]
    mid = bits[EDGE_FIELD_BITS:-EDGE_FIELD_BITS]
    octal = "".join(format(int(mid[i:i + 3], 2), "o")
                    for i in range(0, len(mid), 3))
    return _envelope(octal, len(mid),
                     framing_profile_id="FP-C",
                     name="FIXED132_EDGE_FIELDS",
                     status="ACTIVE_CANDIDATE",
                     padding="BIT_FIELD_STRIP",
                     container_bits=CONTAINER_BITS,
                     edge_prefix_bits=prefix, edge_suffix_bits=suffix,
                     significant_bits=v.bit_length(),
                     rule="left-pad the WHOLE decimal record to 132 bits, "
                          "then remove one 3-bit field from each edge; this "
                          "is a bit-field operation, not decimal stripping")


def fp_d(record: str) -> dict:
    """FP-D WHOLE132_CONTAINER -- diagnostic only, no route authority."""
    s = str(record).strip()
    v = int(s)
    bits = format(v, f"0{CONTAINER_BITS}b")
    octal = "".join(format(int(bits[i:i + 3], 2), "o")
                    for i in range(0, len(bits), 3))
    return {
        "framing_profile_id": "FP-D",
        "name": "WHOLE132_CONTAINER",
        "status": "DIAGNOSTIC_ONLY",
        "rgcs_route_authority": False,
        "envelope_width_bits": CONTAINER_BITS,
        "octal_payload": octal, "octal_digits": len(octal),
        "significant_bits": v.bit_length(),
        "D": None, "legal_splits": None,
        "rule": "retain the full 132-bit transport object for conventional "
                "packing and container tests only",
        "why_no_route": "132 is not a legal wide-envelope width "
                        "(132 - 21 = 111, and 111 % 3 == 0 gives D=37, but "
                        "the container includes transport framing that the "
                        "grammar does not model)",
    }


#: FP-E. Kept ONLY as a negative regression fixture.
FP_E_PAYLOAD = "101672770075311773227352216477536105260021"


def fp_e() -> dict:
    """FP-E SUPERSEDED_OCTAL_TERMINAL_STRIP -- must never auto-select."""
    return {
        "framing_profile_id": "FP-E",
        "name": "SUPERSEDED_OCTAL_TERMINAL_STRIP",
        "status": "SUPERSEDED",
        "must_never_autoselect": True,
        "octal_payload": FP_E_PAYLOAD,
        "octal_digits": len(FP_E_PAYLOAD),
        "rule": "R10.63 stripped the terminal in OCTAL space rather than in "
                "decimal space; retained only as a negative regression "
                "fixture",
    }


#: Profiles offered for routing. FP-D and FP-E are excluded by status.
ROUTE_PROFILES = ("FP-A", "FP-B", "FP-C")

_BUILDERS = {"FP-A": fp_a, "FP-B": fp_b, "FP-C": fp_c, "FP-D": fp_d}


def profile(record: str, profile_id: str) -> dict:
    if profile_id == "FP-E":
        return fp_e()
    if profile_id not in _BUILDERS:
        raise FramingError(f"unknown framing profile {profile_id!r}")
    return _BUILDERS[profile_id](record)


def all_profiles(record: str) -> dict:
    """Every profile, side by side, with no winner.

    ``selected_profile`` is permanently ``None``. Selecting one requires an
    independently frozen framing rule or multiple external records that
    prospectively discriminate -- never an attractive-looking output.
    """
    rows = []
    for pid in ("FP-A", "FP-B", "FP-C", "FP-D"):
        try:
            rows.append(profile(record, pid))
        except FramingError as exc:
            rows.append({"framing_profile_id": pid, "error": str(exc)})
    rows.append(fp_e())
    return {
        "schema": "rgcs.r1061a.framing-profiles.v1",
        "record": str(record).strip(),
        "profiles": rows,
        "route_capable": [r["framing_profile_id"] for r in rows
                          if r.get("status") == "ACTIVE_CANDIDATE"],
        "selected_profile": None,
        "selection_requires": "an independently frozen framing rule, or "
                              "multiple external records that prospectively "
                              "discriminate between profiles",
        "forbidden_promotion_grounds": list(FORBIDDEN_PROMOTION_GROUNDS),
        "record_sha256": hashlib.sha256(
            str(record).strip().encode()).hexdigest(),
    }
