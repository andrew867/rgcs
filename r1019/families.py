"""R10.19B — bridge-family sorting. NO UNIVERSAL BRIDGE.

Operator instruction: do not run one universal bridge. Sort vectors into
bridge families first, then route each family to its own decoder.

THE STRUCTURAL SPLIT
--------------------
One test does the real work: ``value < 2^30``.

  * below 2^30  -> the value IS a SurfaceWord already. It needs no
    bridge at all. Every such row in the ledger is 9 digits.
  * at or above 2^30 -> a variable/transport form. It needs a decoder,
    and WHICH decoder is a question of provenance, not of digits.

Family within each side is therefore taken from the declared
``record_group``, not guessed from the digit string. This module never
infers a private-path or two-sided codec family from digits alone.

WHY THERE IS NO AFFINE FALLBACK
-------------------------------
The header-stripped affine is confirmed for exactly two rows:

    1643789253 -> 165876523   (Stonehenge)
    1672875493 -> 168930443   (Toronto)

Applied to everything else it lands at chance (R10.19: 1 independent hit
in 60, against 0.5 expected). So it is not a fallback and this module
has no ``else: return AFFINE`` branch. Unrecognised rows are returned as
``UNRESOLVED_VARIABLE_ROUTE``, never affine-projected.

PRECEDENCE DEFECT THIS MODULE FIXES
-----------------------------------
A direct SurfaceWord such as ``165829473`` also starts with ``16`` and
ends with ``3``. A classifier that tests the lexical ``16`` header
BEFORE the 30-bit test routes it into the affine lane and silently
mangles it -- the R10.16C category error. The 30-bit test must come
first. See ``docs/r1019/R10_19B_FAMILY_SORT_RESULT.md``.
"""

from __future__ import annotations

from r1016.quarantine import QUARANTINED, assert_clean

SURFACE_MODULUS = 1 << 30

#: Confirmed header-stripped affine pairs. This list is CLOSED.
AFFINE_SAME_LOCATION = {
    "1643789253": 165876523,
    "1672875493": 168930443,
}

#: The canonical targets of those pairs. They are SurfaceWords and must
#: never be fed back through a bridge.
SAME_LOCATION_TARGETS = frozenset(
    str(v) for v in AFFINE_SAME_LOCATION.values())

#: Stonehenge payload octal. Avebury right-appends one symbol to it:
#: 1647012173 -> 21736041 == 2173604 || 1, i.e. one level deeper.
STONEHENGE_PAYLOAD_OCTAL = "2173604"

#: Curatorial exclusions. These cannot be derived from the digits; they
#: are recorded decisions and are carried explicitly.
CORRUPTED_COLLISION = {"1658792343"}

#: Transport examples, not geographic addresses. ``16343`` is only five
#: digits and so falls below 2^30; without this guard it would be typed
#: as a direct SurfaceWord.
WORKED_EXAMPLE_GROUP = "worked_examples"

#: record_group -> family, for values at or above 2^30.
VARIABLE_FAMILY_BY_GROUP = {
    "r10_11f_28_intake": "R10_11F_TWO_SIDED_VARIABLE_CODEC",
    "private_path_17": "PRIVATE_PATH_BASE100_OR_TWO_SIDED_VARIABLE_CODEC",
}

#: Families that must NEVER be affine-projected.
NO_AFFINE = frozenset({
    "R10_11F_TWO_SIDED_VARIABLE_CODEC",
    "PRIVATE_PATH_BASE100_OR_TWO_SIDED_VARIABLE_CODEC",
    "PACKED40_4BIT_HEADER_36BIT_PATH",
    "BASE100_OR_NON16_VARIABLE_ROUTE",
    "QUARANTINED_MONTREAL_FAMILY",
    "CORRUPTED_COLLISION_EXCLUDED",
    "WORKED_EXAMPLE_NOT_GEOGRAPHIC",
    "UNRESOLVED_VARIABLE_ROUTE",
})

#: Families that may be handed to the R10.18D projector.
PROJECTABLE = frozenset({
    "DIRECT_OR_CANONICAL_30BIT_SURFACEWORD",
    "DIRECT_30BIT_SURFACEWORD_RAW",
    "KNOWN_SAME_LOCATION_CANONICAL_TARGET",
    "HEADER_STRIPPED_AFFINE_SAME_LOCATION_BRIDGE",
})


def is_transport_form(value: str) -> bool:
    """Lexical transport shape. NOT sufficient to type a value."""
    s = str(value)
    return s.startswith("16") and s.endswith("3") and s[2:-1].isdigit()


def payload_octal(value) -> str:
    s = str(value)
    return format(int(s[2:-1]), "o") if is_transport_form(s) else ""


def right_appends_stonehenge(value) -> tuple:
    """Is this Stonehenge's payload octal with symbols appended?"""
    po = payload_octal(value)
    if po and po != STONEHENGE_PAYLOAD_OCTAL and \
            po.startswith(STONEHENGE_PAYLOAD_OCTAL):
        return True, po[len(STONEHENGE_PAYLOAD_OCTAL):]
    return False, ""


def classify(value, record_group: str = "", *,
             worked_example: bool = False) -> dict:
    """Sort ONE vector into its bridge family.

    ``record_group`` is declared provenance. Without it, variable rows
    resolve only as far as their structural family allows.
    """
    s = str(value).strip()
    out = {"raw_vector": s, "record_group": record_group}

    def done(family, **kw):
        return out | {"bridge_family": family,
                      "may_affine_project": family not in NO_AFFINE,
                      "projectable": family in PROJECTABLE, **kw}

    # 1. Quarantine is absolute and comes first.
    if s in QUARANTINED:
        return done("QUARANTINED_MONTREAL_FAMILY",
                    reason=QUARANTINED[s])
    # 2. Recorded curatorial exclusions.
    if s in CORRUPTED_COLLISION:
        return done("CORRUPTED_COLLISION_EXCLUDED")
    if not s.isdigit():
        return done("UNRESOLVED_VARIABLE_ROUTE", reason="not decimal")

    # 2b. The Stonehenge right-append is a POSITIVE structural finding
    #     and outranks a curatorial group label. Avebury 1647012173 is
    #     filed under worked_examples, but its payload octal 21736041
    #     is Stonehenge's 2173604 with one symbol appended -- a real
    #     child-cell relation, not an example.
    appends, tail = right_appends_stonehenge(s)
    if appends:
        return done("PAYLOAD_OCTAL_STONEHENGE_RIGHT_APPEND_FAMILY",
                    payload_octal=payload_octal(s),
                    appended_symbols=tail, needs_bridge=True)

    if worked_example:
        return done("WORKED_EXAMPLE_NOT_GEOGRAPHIC")

    n = int(s)

    # 3. The two confirmed affine pairs, and their canonical targets.
    if s in AFFINE_SAME_LOCATION:
        return done("HEADER_STRIPPED_AFFINE_SAME_LOCATION_BRIDGE",
                    surface_word=AFFINE_SAME_LOCATION[s],
                    header_stripped=int(s[2:]))
    if s in SAME_LOCATION_TARGETS:
        return done("KNOWN_SAME_LOCATION_CANONICAL_TARGET",
                    surface_word=n)

    # 4. THE STRUCTURAL SPLIT. This must precede any lexical header
    #    test: a direct SurfaceWord also starts with "16".
    if n < SURFACE_MODULUS:
        fam = ("DIRECT_OR_CANONICAL_30BIT_SURFACEWORD"
               if record_group == "earth_root_35"
               else "DIRECT_30BIT_SURFACEWORD_RAW")
        return done(fam, surface_word=n,
                    surface_octal10=format(n, "010o"),
                    needs_bridge=False)

    # 5. At or above 2^30: variable form. Provenance decides.
    fam = VARIABLE_FAMILY_BY_GROUP.get(record_group)
    if fam:
        return done(fam, needs_bridge=True)
    if record_group == "earth_root_35":
        if len(s) == 12:
            bits = format(n, "040b")
            return done("PACKED40_4BIT_HEADER_36BIT_PATH",
                        header4=int(bits[:4], 2),
                        path12_octal=format(int(bits[4:], 2), "012o"))
        return done("BASE100_OR_NON16_VARIABLE_ROUTE")

    # 6. NO AFFINE FALLBACK.
    return done("UNRESOLVED_VARIABLE_ROUTE",
                reason="variable form with no declared provenance; the "
                       "affine is confirmed for two rows only and is "
                       "never used as a fallback")


def sort_ledger(rows) -> dict:
    """Sort an iterable of ledger rows into families."""
    assert_clean([r.get("raw_vector", "") for r in rows],
                 where="R10.19B family sort")
    out, counts = [], {}
    for r in rows:
        c = classify(r.get("raw_vector", ""), r.get("record_group", ""),
                     worked_example=str(
                         r.get("record_group", "")) == WORKED_EXAMPLE_GROUP)
        out.append(c)
        counts[c["bridge_family"]] = counts.get(c["bridge_family"], 0) + 1
    affine = sum(1 for c in out if c["bridge_family"]
                 == "HEADER_STRIPPED_AFFINE_SAME_LOCATION_BRIDGE")
    return {
        "schema": "rgcs.r1019b.family-sort.v1",
        "verdict": "R10_19B_VARIABLE_VECTOR_FAMILIES_SORTED",
        "claim": "NO_UNIVERSAL_BRIDGE_CLAIM",
        "rows": out,
        "total": len(out),
        "family_counts": dict(sorted(counts.items())),
        "affine_rows": affine,
        "affine_is_closed_at_two": affine <= 2,
        "projectable": sum(1 for c in out if c["projectable"]),
        "never_affine": sum(1 for c in out if not c["may_affine_project"]),
    }
