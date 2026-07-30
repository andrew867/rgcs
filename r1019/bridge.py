"""R10.19 — the SurfaceBridge: variable/transport wire -> SurfaceWord.

WHAT WAS RECOVERED
------------------
The R10.8-era affine ``y = (923x + 550585316) mod 2^30`` was shelved at
R10.9 as ``R109-MTL-02-SUPERSEDED`` because, applied to a WHOLE wire, it
produced nothing defensible.  It was applied to the wrong operand.

Applied after stripping the lexical ``16`` transport header ONLY, it
reproduces both recorded same-location pairs EXACTLY:

    1643789253 -> 43789253 -> 165876523   Stonehenge   EXACT
    1672875493 -> 72875493 -> 168930443   Toronto      EXACT

with ZERO parameters fitted in this run: 923 and 550585316 are read from
:mod:`r109.superseded`, recorded long before this analysis.

WHY THAT IS EVIDENCE, AND HOW MUCH
----------------------------------
Two points do not pin an affine mod 2^30 here.  ``X2 - X1 = 29086240``
and ``gcd(29086240, 2^30) = 32``, so exactly 32 ``(A, B)`` pairs satisfy
both equations.  The recorded pair is one of those 32 -- and is the
member with the smallest ``A``.  A constant pair recorded in advance
landing inside that family by chance has probability
``32 / 2^60 = 2.8e-17``.  The operator confirms all vectors are source
material, not generated here, so this is not circular.

WHAT IT IS NOT
--------------
It is NOT the general transport-row bridge.  Applied to the 66
variable/transport rows (62 parseable, Montreal quarantined):

  * anchor-profile hits (F5 in {4,5} AND S3 == 3): 3 of 62;
  * TWO OF THOSE THREE ARE STONEHENGE AND TORONTO THEMSELVES -- the
    anchors sit inside the transport list, so they are training data,
    not confirmations;
  * independent confirmations: 1 of 60, against 0.5 expected by chance.

That is chance.

The Avebury cross-check appears to fail here -- 1647012173 maps to
993148035, sharing 0 of 10 surface_octal10 prefix symbols with
Stonehenge -- but that was a CATEGORY ERROR, not evidence.  Avebury
belongs to a different family entirely.  Its relation to Stonehenge
lives in PAYLOAD OCTAL space, where it is exact:

    Stonehenge 165876523  payload octal = 2173604
    Avebury    1647012173 payload octal = 21736041 = 2173604 || 1

i.e. 4701217 = 587652 * 8 + 1, one octal level deeper.  See
:mod:`r1019.families` and R10.19B.  The affine must never be applied to
this family.

PROVENANCE CAVEAT
-----------------
The only product recorded for these constants in
``r109.superseded.LEDGER`` is the Montreal mapping, and the tag is
``MTL``.  The constants are therefore Montreal-lane derived.  Montreal
is quarantined (R10.18C), so the constants are used here as opaque
recorded numbers and Montreal values are never evaluated.

CLASSIFICATION
--------------
``R10_19_SURFACE_BRIDGE_HEADER_STRIPPED_AFFINE_CANDIDATE``
CONFIRMED for canonical same-location pairs; REFUTED as a general
transport canonicalization.  It may not be used to manufacture anchors.
"""

from __future__ import annotations

from r1016.quarantine import assert_clean

#: Read from the recorded ledger, never fitted here.
MULTIPLIER = 923
OFFSET = 550585316
MODULUS = 1 << 30

TRANSPORT_HEADER = "16"

LABEL = "R10_19_SURFACE_BRIDGE_HEADER_STRIPPED_AFFINE_CANDIDATE"

#: Status per lane. The bridge is not a general canonicalizer.
#: R10.47C RETRACTION. A THIRD labelled same-location pair (CYYT/St
#: John's, 1658274383 -> 165892733) is the first out-of-sample test of
#: this map, and it MISSES by 484,856,892. Enumerating the 32-member
#: (A,B) family that fits the first two pairs, ZERO members reproduce
#: the third. Two points cannot over-determine an affine mod 2^30, so
#: the earlier "2 of 2 exact" was the minimum needed to DEFINE the map,
#: never a test of it. The R10.19 figure 32/2^60 answered whether a
#: pre-recorded constant lands in the fitting family - a different and
#: much weaker question than whether the map generalises.
STATUS = {
    "canonical_same_location_pairs":
        "REFUTED_2_OF_3_THIRD_LABELLED_PAIR_MISSES",
    "general_transport_bridge": "REFUTED_NO_AFFINE_FITS_ALL_THREE_PAIRS",
    "_superseded_claim": "CONFIRMED_2_OF_2_EXACT",
    "general_transport_rows": "REFUTED_AT_CHANCE_1_OF_60",
    "right_append_child_relation":
        "NOT_AN_AFFINE_RELATION_SEE_R10_19B_PAYLOAD_OCTAL_FAMILY",
}

#: The two recorded same-location pairs (transport wire -> surface word).
SAME_LOCATION_PAIRS = {
    "Stonehenge": (1643789253, 165876523),
    "Toronto": (1672875493, 168930443),
}

#: The THIRD labelled pair, which the affine does NOT reproduce. It is
#: the out-of-sample test the first two could never provide.
REFUTING_PAIR = {"CYYT_StJohns": (1658274383, 165892733)}


class BridgeError(ValueError):
    """The value is not a header-bearing transport wire."""


#: Recorded canonical SurfaceWords. These are OUTPUTS of the bridge and
#: must never be fed back in as inputs -- the R10.16C category error.
#: The lexical header cannot catch this on its own: 165876523 also
#: begins with "16", so a purely lexical guard would silently mangle a
#: SurfaceWord into a second, meaningless 30-bit value.
RECORDED_SURFACE_WORDS = frozenset(
    str(t) for _, t in SAME_LOCATION_PAIRS.values()) | {"167849523"}


def strip_header(wire) -> int:
    """Remove the lexical ``16`` transport header. Nothing else.

    Refuses a value already typed as a SurfaceWord. Note the residual
    ambiguity: transport wires and SurfaceWords are not separable by
    digit count alone (both may be 9-10 digits and below 2^30), so this
    guard is a recorded-value check, not a decision procedure. An
    unrecorded 9-digit value cannot be typed from its digits and the
    caller must supply the lane.
    """
    s = str(wire).strip()
    if not s.isdigit():
        raise BridgeError(f"{wire!r} is not a decimal transport wire")
    if s in RECORDED_SURFACE_WORDS:
        raise BridgeError(
            f"{s} is a recorded canonical SurfaceWord, not a transport "
            f"wire; bridging an output back into the input is the "
            f"R10.16C category error, and the leading {TRANSPORT_HEADER!r} "
            f"does not distinguish the two types")
    if not s.startswith(TRANSPORT_HEADER):
        raise BridgeError(
            f"{s} carries no {TRANSPORT_HEADER!r} transport header; the "
            f"bridge operates on the header-stripped payload only, and "
            f"applying it to a whole wire is what shelved this model at "
            f"R10.9")
    return int(s[len(TRANSPORT_HEADER):])


def bridge(wire) -> int:
    """Header-stripped affine. Returns a 30-bit candidate SurfaceWord."""
    assert_clean([wire], where="R10.19 surface bridge")
    return (MULTIPLIER * strip_header(wire) + OFFSET) % MODULUS


def fields(word: int) -> tuple:
    """(F5, Q22, S3) of a 30-bit word."""
    return (word >> 25) & 31, (word >> 3) & ((1 << 22) - 1), word & 7


def verify_same_location_pairs() -> dict:
    """Re-derive the two exact reproductions. No fitting, no search."""
    rows = []
    for name, (wire, target) in SAME_LOCATION_PAIRS.items():
        got = bridge(wire)
        rows.append({
            "anchor": name, "transport_wire": wire,
            "header_stripped": strip_header(wire),
            "bridged": got, "recorded_surface_word": target,
            "exact": got == target,
            "surface_octal10": format(got, "010o"),
        })
    return {
        "schema": "rgcs.r1019.same-location-bridge.v1",
        "label": LABEL, "rows": rows,
        "exact_reproductions": sum(1 for r in rows if r["exact"]),
        "parameters_fitted_in_this_run": 0,
        "constants_source": "r109.superseded.LEDGER (recorded pre-R10.19)",
    }


def solution_family_size() -> dict:
    """How many (A, B) pairs fit BOTH recorded pairs mod 2^30.

    This is the honest strength of the evidence: the recorded constants
    are not uniquely forced, so the claim is membership in a small
    family, not a one-in-2^60 coincidence.
    """
    from math import gcd
    (x1, y1), (x2, y2) = (
        (strip_header(w), t) for w, t in SAME_LOCATION_PAIRS.values())
    dx, dy = (x2 - x1) % MODULUS, (y2 - y1) % MODULUS
    g = gcd(dx, MODULUS)
    if dy % g:
        return {"solvable": False, "family_size": 0}
    inv = pow(dx // g, -1, MODULUS // g)
    a0 = (dy // g * inv) % (MODULUS // g)
    fam = sorted((a0 + k * (MODULUS // g)) % MODULUS for k in range(g))
    return {
        "schema": "rgcs.r1019.affine-family.v1",
        "solvable": True, "family_size": len(fam),
        "recorded_multiplier_in_family": MULTIPLIER in fam,
        "recorded_multiplier_rank": fam.index(MULTIPLIER),
        "probability_recorded_pair_lands_in_family_by_chance":
            len(fam) / 2 ** 60,
        "note": "two points do not pin the affine: gcd(dX, 2^30) = "
                f"{g}, so {len(fam)} (A,B) pairs fit both. The recorded "
                "pair is the smallest-A member of that family.",
    }


def generalization_report(transport_wires, anchor_f5=(4, 5),
                          anchor_s3=(3,)) -> dict:
    """Apply the bridge to transport rows and score against chance.

    Anchors present in ``transport_wires`` are reported separately: they
    are training data and must never be counted as confirmations.
    """
    assert_clean(transport_wires, where="R10.19 generalization scoring")
    anchors = {str(w) for w, _ in SAME_LOCATION_PAIRS.values()}
    rows, independent, hits = [], 0, 0
    for w in transport_wires:
        s = str(w).strip()
        try:
            v = bridge(s)
        except BridgeError:
            continue
        f5, _, s3 = fields(v)
        ok = f5 in anchor_f5 and s3 in anchor_s3
        is_anchor = s in anchors
        if not is_anchor:
            independent += 1
            hits += ok
        rows.append({"transport_wire": s, "bridged_surface_word": v,
                     "surface_octal10": format(v, "010o"),
                     "F5": f5, "S3": s3, "matches_anchor_profile": ok,
                     "is_training_anchor": is_anchor})
    p = (len(set(anchor_f5)) / 32) * (len(set(anchor_s3)) / 8)
    expected = independent * p
    return {
        "schema": "rgcs.r1019.bridge-generalization.v1",
        "label": LABEL,
        "rows": rows,
        "parseable": len(rows),
        "independent_rows": independent,
        "independent_hits": hits,
        "expected_by_chance": expected,
        "enrichment": (hits / expected) if expected else None,
        "verdict": ("ENRICHED" if expected and hits >= 3 * expected
                    and hits >= 5 else "AT_CHANCE"),
        "note": "anchors inside the transport list are excluded from "
                "the numerator; counting them is training leakage.",
    }
