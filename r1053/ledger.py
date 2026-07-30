"""R10.53 -- the V1 coordinate ledger, labels, and the wide-envelope gate.

The projected coordinates in :data:`V1_PROJECTED` are OPERATOR-SUPPLIED
recorded V1 outputs, taken verbatim from the pack's
``02_COORDINATE_LEDGER.json``. They are the authoritative V1 values and
are what the map artifacts plot.

They are NOT re-derived here, and the reason is recorded rather than
hidden: with three anchors the projector's ``A`` retains two free
parameters (see :func:`r1053.projector.underdetermination_report`), so
the pack's outputs correspond to one member of that family and this
repository's pinning rule selects a different member. Both satisfy the
anchors exactly. Until a pinning rule is recorded upstream, or a fourth
and fifth anchor arrive, the numbers cannot be reproduced from the law
as stated -- that is blocker V1-B01, not a defect in either side.

LABEL DISCIPLINE
----------------
The operator's rule, adopted here in full::

    CITY_NAME  != EXACT TARGET
    CITY_NAME  == nearest human-readable regional label
    PROJECTED  == operational cell / corridor / object-position candidate

So a residual against a city centre is a label-to-cell offset, not a
miss, and it is scored against the RGCS depth-9 cell scale.
"""

from __future__ import annotations

#: CORRECTION: 165879243 is no longer labelled Montreal.
ACTIVE_LABELS = {
    "165879243": "Drummondville / Saint-Eugene farm corridor working target",
}

#: The retired label, kept as provenance only. It may not be scored,
#: may not fit the projector, and may not be cited as a target.
RETIRED_LABELS = {
    "165879243": {
        "retired_label": "Montreal",
        "status": "HINT_PROVENANCE_ONLY",
        "may_be_scored": False,
        "may_fit_projector": False,
        "note": "retired by operator instruction at R10.53; the direct "
                "Montreal lane stays out of every fit (correction 11)",
    },
}

#: Fit anchors. Only these three determine A.
FIT_ANCHORS = {
    "165876523": {"label": "Stonehenge hard anchor",
                  "lat": 51.1789, "lon": -1.8262, "role": "fit_anchor"},
    "167849523": {"label": "Erie hard anchor",
                  "lat": 42.1292, "lon": -80.0851, "role": "fit_anchor"},
    "168930443": {"label": "Toronto hard anchor",
                  "lat": 43.6532, "lon": -79.3832, "role": "fit_anchor"},
}

#: Operator-supplied V1 projected outputs, verbatim from the pack.
V1_PROJECTED = {
    "165879243": {
        "label": "Drummondville / Saint-Eugene farm corridor working target",
        "lat": 45.8418969, "lon": -72.6788251, "role": "v1_candidate"},
    "165892743": {"label": "Orange triplet A",
                  "lat": 50.687111, "lon": 0.456825,
                  "role": "projected_candidate"},
    "165892763": {"label": "Orange triplet B",
                  "lat": 50.675152, "lon": 0.505141,
                  "role": "projected_candidate"},
    "165892783": {"label": "Orange triplet C",
                  "lat": 50.627764, "lon": 0.666452,
                  "role": "projected_candidate"},
}

#: Ground references for residual scoring.
REFERENCES = {
    "Drummondville_city": {
        "lat": 45.88058, "lon": -72.48405,
        "source": "Quebec official toponymy",
        "kind": "city_centre_label",
        "note": "a regional human label, NOT the expected exact target"},
    "Rue_Saint_Frederic_corridor_proxy": {
        "lat": 45.883, "lon": -72.486,
        "source": "pack proxy - exact civic point still to verify",
        "kind": "witness_observer_line",
        "note": "the 2015 observer balcony location, i.e. where the "
                "witness stood, not where an object was over ground"},
    "Saint_Eugene": {
        "lat": 45.8, "lon": -72.7,
        "source": "Quebec official toponymy (no_seq 56466)",
        "kind": "rural_municipality",
        "note": "the farm corridor WSW of Drummondville"},
}

#: CORRECTION 6 / task 6: the wide-envelope batch stays gated. These are
#: 11-13 digit records; they exceed 30 bits and so cannot enter the
#: direct lane at all. They are listed to keep the gate explicit.
GATED_WIDE_ENVELOPE = (
    "1687293589323", "16872394203", "168732948753", "168752934853",
    "168752493633", "1687529232333", "16875938393",
)

#: Labels that may not be asserted at V1.
BLOCKED_LABELS = (
    "165879243 as Montreal",
    "1658274383 as resolved CYYT bridge",
    "165892733 as resolved CYYT compact",
)

#: Operator scoring bands (R10.53 revision). A city name is a regional
#: label, so 5-25 km is an adjacent-operational-cell hit, not a miss.
V1_CELL_BANDS = (
    (0.0, 5.0, "LOCAL_HIT"),
    (5.0, 25.0, "OPERATIONAL_CELL_OR_ADJACENT_CELL_HIT"),
    (25.0, 75.0, "REGIONAL_CORRIDOR_HIT"),
    (75.0, 200.0, "COARSE_V1_CORRIDOR_HIT"),
    (200.0, float("inf"), "WEAK_OR_FAIL_PENDING_SEMANTICS"),
)

#: The pack's original bands, kept so the revision is auditable.
PACK_BANDS = (
    (0.0, 25.0, "STRONG_LOCAL_MATCH"),
    (25.0, 75.0, "REGIONAL_MATCH"),
    (75.0, 200.0, "V1_CORRIDOR_MATCH"),
    (200.0, float("inf"), "WEAK_OR_FAIL_PENDING_SEMANTICS"),
)

LABEL_RULE = (
    "CITY_NAME != EXACT TARGET; CITY_NAME is the nearest human-readable "
    "regional label and PROJECTED_POINT is the operational cell / "
    "corridor / object-position candidate")


def is_gated(word) -> bool:
    """True if the value belongs to the gated wide-envelope batch."""
    return str(word).strip() in GATED_WIDE_ENVELOPE


def classify(distance_km: float, bands=V1_CELL_BANDS) -> str:
    for lo, hi, name in bands:
        if lo <= distance_km < hi:
            return name
    return bands[-1][2]


def active_label(word) -> str:
    return ACTIVE_LABELS.get(str(word).strip(), "")
