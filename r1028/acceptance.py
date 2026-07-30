"""R10.48E — decode acceptance criteria from the source note.

Two source statements that were never implemented, both from line 108 of
the 2026-07-29 note:

    "Remember to reference mean sea height with level 3."
    "We usually land in oceans or bodies of water, not us military
     installations like some of the vectors we have given you thus far."

The second is the more important of the two and I had not logged it at
all. It is a DECODE ACCEPTANCE CRITERION: it says what a correct decode
should look like, independently of any labelled anchor. That makes it the
only check available that does not require ground truth we do not have.

It also contains a self-flag: the source says some of the vectors it
supplied ARE at military installations, and treats that as anomalous.
So a decode landing on such a site is not automatically wrong -- it is
in the category the source itself marked as exceptional.

WHAT THIS MODULE DOES AND DOES NOT DO
-------------------------------------
It defines the criteria, the datum, and the scoring contract. It CANNOT
score anything yet, because scoring needs a decoded coordinate and the
projector remains unrecovered (R10.25). A land/water test also needs a
coastline dataset, which is not present in this environment; the
criterion records that dependency rather than approximating it.
"""

from __future__ import annotations

#: SOURCE line 108: level 3 references MEAN SEA HEIGHT.
#: R10.17 reached the same conclusion independently: using the recorded
#: 840 m land-zero put every seed point above the shell boundary, while
#: the MSL datum placed 6 of 7 in S3 with the Baltic separating as a
#: benthic monitor. Two routes, same answer.
LEVEL3_DATUM = "MEAN_SEA_LEVEL"
LEVEL3_DATUM_M = 0.0
SUPERSEDED_DATUMS = {
    "RECORDED_LAND_ZERO_840M": 840.0,
    "RECORDED_LAND_ZERO_MODERN_797M": 797.0,
}

#: SOURCE line 108, the acceptance criterion.
EXPECTED_SURFACE = "WATER"
EXPECTATION_NOTE = (
    "the source states decodes usually land in oceans or bodies of "
    "water; a majority-land decode set is evidence AGAINST the decode, "
    "not merely uninformative")

#: The source's own anomaly flag: it says some supplied vectors sit on
#: US military installations and treats that as notable.
SOURCE_FLAGGED_ANOMALY = "US_MILITARY_INSTALLATION"


def datum_offset_m(datum: str = LEVEL3_DATUM) -> float:
    """Height reference for level 3. MSL is 0 by definition."""
    if datum == LEVEL3_DATUM:
        return LEVEL3_DATUM_M
    if datum in SUPERSEDED_DATUMS:
        return SUPERSEDED_DATUMS[datum]
    raise ValueError(f"unknown datum {datum!r}")


def water_criterion(decodes) -> dict:
    """Score a set of decoded coordinates against the water expectation.

    ``decodes`` is an iterable of dicts with at least ``over_water``
    (bool or None). None means "not determined" and is counted
    separately rather than guessed.
    """
    rows = list(decodes)
    known = [d for d in rows if d.get("over_water") is not None]
    water = [d for d in known if d["over_water"]]
    frac = len(water) / len(known) if known else None
    return {
        "criterion": "SOURCE_EXPECTS_MOSTLY_WATER",
        "decodes": len(rows),
        "determined": len(known),
        "undetermined": len(rows) - len(known),
        "over_water": len(water),
        "water_fraction": frac,
        "meets_expectation": (frac is not None and frac > 0.5),
        "verdict": ("NOT_SCOREABLE_NO_COORDINATES" if not known
                    else "CONSISTENT_WITH_SOURCE" if frac > 0.5
                    else "CONTRADICTS_SOURCE_EXPECTATION"),
        "note": EXPECTATION_NOTE,
    }


def readiness() -> dict:
    """Can the criterion actually be run? Not yet, and here is why."""
    return {
        "criterion_defined": True,
        "datum_defined": True,
        "needs_decoded_coordinates": True,
        "projector_status": "UNRECOVERED (R10.25 exact failure)",
        "needs_land_water_mask": True,
        "land_water_mask_present": False,
        "scoreable_now": False,
        "blocking": [
            "the projector cannot emit a coordinate, so there is nothing "
            "to test",
            "no coastline dataset in this environment; a land/water call "
            "must not be approximated by eye",
        ],
        "why_it_matters": "this is the ONLY decode check that needs no "
                          "labelled anchor. Once coordinates exist it "
                          "scores every decode at once, and a "
                          "majority-land result would falsify a "
                          "projector that no anchor test could reach.",
        "baseline_to_beat": "Earth is about 71% water, so a correct "
                            "decode set should exceed that; landing at "
                            "or below 71% is NOT support",
    }
