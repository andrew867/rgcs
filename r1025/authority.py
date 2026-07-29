"""R10.25 Agent 00 — authority cleanup, applied.

Three edits were outstanding from R10.18D. They are applied here rather
than left as recommendations.

1. GEOGRAPHIC BUCKET NAMES -> SIGNATURE CLASSES.
   A bucket called ``NW_PENNSYLVANIA_LAKE_ERIE`` asserts a geographic
   conclusion in the name of a structure that only ever measured a
   packet signature. Reading the name back later is then circular. The
   classes below are named for what was actually measured -- shared F5,
   shared path prefix depth -- and carry no place claim.

2. THE 3/3 ANCHOR RESULT -> ``SELF_CONSISTENT_NOT_GEOMETRICALLY_TESTED``.
   Three anchors carrying only TWO distinct F5 values cannot corroborate
   a face map: the map is fitted from those same anchors. "3/3" was
   describing a fit, not a test.

3. 167854923 UNBUCKETED.
   It is a frozen blind holdout with a lunar/historical source claim.
   Filing it under a terrestrial regional bucket would quietly close the
   lunar trail. Tracked code already holds it as a lunar candidate; this
   module states the rule so it cannot drift back.
"""

from __future__ import annotations

from r1016.quarantine import QUARANTINED

#: Old geographic bucket -> measured-signature class.
SIGNATURE_CLASS_RENAMES = {
    "NW_PENNSYLVANIA_LAKE_ERIE": "F5_5_SHARED_ROOT_PREFIX_CLASS",
    "BRITISH_CLUSTER": "F5_4_SHARED_ROOT_PREFIX_CLASS",
    "NORTH_AMERICA_F5_5_FAMILY": "F5_5_SHARED_ROOT_PREFIX_CLASS",
}

#: Vectors that must never be filed into a terrestrial regional class.
UNBUCKETED = {
    "167854923": "FROZEN_BLIND_HOLDOUT_LUNAR_OR_HISTORICAL_TRAIL_OPEN",
}

ANCHOR_RESULT_STATUS = "SELF_CONSISTENT_NOT_GEOMETRICALLY_TESTED"

ANCHOR_RESULT_REASON = (
    "three hard anchors carry only two distinct F5 values, so the "
    "F5 -> face map is fitted from the same anchors it is scored on and "
    "contributes no evidence; only child-map consistency and containment "
    "can corroborate a projector"
)


def signature_class(name: str) -> str:
    """Rename a geographic bucket to its measured-signature class."""
    return SIGNATURE_CLASS_RENAMES.get(name, name)


def assert_no_place_name_scoring(bucket_names) -> None:
    """Refuse any bucket whose name encodes a geographic conclusion."""
    bad = [b for b in bucket_names if b in SIGNATURE_CLASS_RENAMES]
    if bad:
        raise ValueError(
            f"INVALID RUN: geographic bucket name(s) {bad} reached "
            f"scoring. Rename to signature classes first: "
            f"{[SIGNATURE_CLASS_RENAMES[b] for b in bad]}")


def cleanup_receipt() -> dict:
    return {
        "schema": "rgcs.r1025.authority-cleanup.v1",
        "renames_applied": dict(SIGNATURE_CLASS_RENAMES),
        "unbucketed": dict(UNBUCKETED),
        "anchor_result_status": ANCHOR_RESULT_STATUS,
        "anchor_result_reason": ANCHOR_RESULT_REASON,
        "quarantined": sorted(QUARANTINED),
        "verdict": "R10_25_AGENT_00_AUTHORITY_CLEANUP_GREEN",
    }
