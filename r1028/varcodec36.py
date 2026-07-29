"""THE 36-bit VARIABLE-LENGTH CODEC.

R10.47C SUPERSEDES the fixed R4|S8|P12|tail reading used here. Every
field label is a MAXIMUM CAPACITY, not an always-full field; see
:mod:`r1028.staged` for the variable staged parser that enumerates all
legal (root, section, path, epoch) boundaries. This module is retained
as the FIXED-BOUNDARY DIAGNOSTIC LANE.


Earlier runs parsed every vector as a FIXED 36-bit word with an
``F5 | Q22 | S3`` split. That was wrong on two counts, and the source
note states both corrections plainly.

CORRECTION 1 -- THE WORD IS VARIABLE LENGTH
    "the 12-bit section can be as small as three bits but as wide as
     twelve bits. three bits = check digit only, no epoch"

so the trailing section is 3, 6, 9 or 12 bits and the word is:

    4-bit root | 8-bit surface | 12-bit path | tail(3|6|9|12)
    = 27, 30, 33 or 36 bits
    =  9, 10, 11 or 12 OCTAL digits

Octal digit count therefore READS OFF the tail width directly. That is
what "36-bit variable length encoding, octal is the base system in use"
means: the octal length is the length prefix.

CORRECTION 2 -- THE ROOT IS 4 BITS, NOT 5
    "always 4-bit root zero padded"

The previous ``F5`` took five bits, stealing the top bit of the 8-bit
surface field. That single misalignment is why the three verified
anchors appeared to carry TWO different roots (4 and 5) when in fact
they share ONE:

    Stonehenge  R4=2   Erie  R4=2   Toronto  R4=2
    Anchorage   R4=3   Santa Fe R4=3

The anchors are a single root family, and the discriminating
information lives in S8/P12 where the source says it does.

TAIL STRUCTURE (source, verbatim):
    o3: epoch refinement   (optional)
    o3: epoch refinement   (optional)
    o3: epoch frequency    (optional)
    m3: check digit        (MANDATORY)

The mandatory check digit is the LAST 3 bits, so it is present at every
width -- which is exactly why a 3-bit tail means "check digit only, no
epoch".
"""

from __future__ import annotations

from r1016.quarantine import assert_clean

ROOT_BITS, SURFACE_BITS, PATH_BITS = 4, 8, 12
FIXED_BITS = ROOT_BITS + SURFACE_BITS + PATH_BITS      # 24
TAIL_WIDTHS = (3, 6, 9, 12)
VALID_OCTAL_LENGTHS = tuple((FIXED_BITS + t) // 3 for t in TAIL_WIDTHS)


class VarCodecError(ValueError):
    pass


VALID_WIDTHS = tuple(FIXED_BITS + t for t in TAIL_WIDTHS)   # 27,30,33,36


def active_width(value: int) -> int:
    """R10.38 parsing rule: the SMALLEST valid width that contains the
    integer, then left-zero-pad. Do NOT force 36 bits unless bit_length
    requires it.

    This is equivalent to reading the width off the octal length for
    every in-range value, and ``width_rules_agree`` proves it.
    """
    bl = max(1, value.bit_length())
    for w in VALID_WIDTHS:
        if bl <= w:
            return w
    raise VarCodecError(
        f"{value} needs {bl} bits; the widest single variable-length "
        f"word is {VALID_WIDTHS[-1]} bits. Multi-block, not one word.")


def width_rules_agree(value: int) -> bool:
    """bit_length rule and octal-length rule must give the same width."""
    try:
        return active_width(value) == len(format(value, "o")) * 3
    except VarCodecError:
        return False


def tail_bits_for(octal_len: int) -> int:
    t = octal_len * 3 - FIXED_BITS
    if t not in TAIL_WIDTHS:
        raise VarCodecError(
            f"{octal_len} octal digits implies a {t}-bit tail; the source "
            f"allows only {TAIL_WIDTHS} (totals {VALID_OCTAL_LENGTHS} "
            f"octal digits). This value is not a single variable-length "
            f"word and must not be forced into one.")
    return t


def decode(value: int) -> dict:
    """Decode one variable-length word. Length is read from the octal."""
    assert_clean([value], where="R10.37 variable-length decode")
    octal = format(value, "o")
    total = active_width(value)            # R10.38 authoritative rule
    tail = total - FIXED_BITS
    pos = total
    pos -= ROOT_BITS
    root = (value >> pos) & ((1 << ROOT_BITS) - 1)
    pos -= SURFACE_BITS
    surface = (value >> pos) & ((1 << SURFACE_BITS) - 1)
    pos -= PATH_BITS
    path = (value >> pos) & ((1 << PATH_BITS) - 1)
    raw_tail = value & ((1 << tail) - 1)

    # tail fields are 3-bit groups; the LAST is the mandatory check.
    groups = [(raw_tail >> (tail - 3 * (i + 1))) & 7
              for i in range(tail // 3)]
    names = ["epoch_refine_1", "epoch_refine_2", "epoch_frequency"]
    fields = {}
    # present optional fields fill from the FRONT of the tail
    for i, g in enumerate(groups[:-1]):
        fields[names[i]] = g
    check = groups[-1]

    return {
        "value": value, "octal": octal, "octal_digits": len(octal),
        "bits": format(value, f"0{total}b"),
        "width_rules_agree": width_rules_agree(value),
        "E3": groups,
        "total_bits": total, "tail_bits": tail,
        "R4_root": root, "S8_surface": surface, "P12_path": path,
        "tail_groups": groups, "check_digit_m3": check,
        "epoch_fields_present": len(groups) - 1,
        "has_epoch": tail > 3,
        **fields,
    }


def try_decode(value: int) -> dict | None:
    try:
        return decode(value)
    except VarCodecError:
        return None


def surface_split(surface: int) -> dict:
    """S8 carries 'layer 2 and 3, not always including level 3'."""
    return {"layer2_hi5": (surface >> 3) & 31,
            "layer3_lo3": surface & 7,
            "note": "source: 'surface refinements can be less than 20 "
                    "bits, but always one of each from the 8-bit and "
                    "12-bit parts'"}


def path_split(path: int) -> dict:
    """P12 is the local root path refinement chain, 4 x 3-bit steps."""
    return {"steps_octal": [(path >> (9 - 3 * i)) & 7 for i in range(4)],
            "note": "source: '12-bit local root path refinement chain to "
                    "find smallest hedron triangle for surface refinement'"}


def decode_report(labelled) -> dict:
    """labelled: iterable of (label, decimal string)."""
    rows, rejected = [], []
    for label, raw in labelled:
        d = try_decode(int(raw))
        if d is None:
            rejected.append({
                "label": label, "raw": raw,
                "octal_digits": len(format(int(raw), "o")),
                "reason": "octal length implies a tail outside 3/6/9/12; "
                          "not a single variable-length word"})
            continue
        rows.append({"label": label, "raw": raw, **d,
                     **surface_split(d["S8_surface"]),
                     **path_split(d["P12_path"])})
    roots = {r["R4_root"] for r in rows}
    checks = {r["check_digit_m3"] for r in rows}
    return {
        "schema": "rgcs.r1037.varcodec.v1",
        "rows": rows, "rejected": rejected,
        "decoded": len(rows), "rejected_count": len(rejected),
        "distinct_roots": sorted(roots),
        "distinct_check_digits": sorted(checks),
        "valid_octal_lengths": list(VALID_OCTAL_LENGTHS),
    }


#: R10.38B family typing, by active width and parse outcome.
FAMILY_VARIABLE30 = "VARIABLE30_TERRA_SURFACE_CELL"
FAMILY_VARIABLE36 = "VARIABLE36_EXTENDED_SURFACE_CELL"
FAMILY_MULTIBLOCK = "MULTIBLOCK_OR_DIFFERENT_ROUTE"

#: Corrected field semantics (R10.38B). Roles are CANDIDATES; only the
#: same-cell relation below is established.
FIELD_SEMANTICS = {
    "R4": "root / body / system family",
    "S8": "major surface zone / triangle-family CANDIDATE",
    "P12": "local geometric cell CANDIDATE",
    "tail": "epoch / state / check - NON-SPATIAL",
}


def family_of(value: int) -> str:
    try:
        w = active_width(value)
    except VarCodecError:
        return FAMILY_MULTIBLOCK
    return FAMILY_VARIABLE30 if w <= 30 else FAMILY_VARIABLE36


def cell_key(value: int) -> tuple:
    """The geometric identity of a word: R4/S8/P12. The tail is NOT part
    of it, so same-cell tail variants share a key."""
    d = decode(value)
    return (d["R4_root"], d["S8_surface"], d["P12_path"])


def same_cell(a: int, b: int) -> bool:
    return cell_key(a) == cell_key(b)


def check_depends_on_tail(values) -> dict:
    """If two words share R4/S8/P12 but differ in check digit, the check
    CANNOT be a function of the geometric fields alone. That is a hard
    constraint on any future checksum rule."""
    by = {}
    for v in values:
        by.setdefault(cell_key(v), []).append(decode(v))
    proof = []
    for key, ds in by.items():
        checks = {d["check_digit_m3"] for d in ds}
        if len(ds) > 1 and len(checks) > 1:
            proof.append({"cell": key, "checks": sorted(checks),
                          "values": [d["value"] for d in ds]})
    return {
        "same_cell_groups": len(by),
        "groups_with_differing_checks": len(proof),
        "proof": proof,
        "check_is_function_of_geometry_alone": not proof,
        "conclusion": ("REFUTED: the check digit varies within a fixed "
                       "R4/S8/P12 cell, so it must read the tail (or the "
                       "whole word), not the geometric fields alone"
                       if proof else "not refuted by this corpus"),
    }
