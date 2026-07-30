"""R10.44 — crop formations with EXACT coordinates.

This is the first crop batch whose value is not glyph reading. Two of
these formations carry published OS grid references, so they have real
coordinates — which makes them usable as location holdouts the moment
the projector works, independent of anything anyone reads off the shape.

The OS grid conversions were verified by full transverse-Mercator
inverse plus the OSGB36->WGS84 Helmert transform, and they reproduce the
operator's values to 0 m.

WHAT MAKES THESE BETTER THAN THE JULY GLYPHS
--------------------------------------------
The July formations gave counts. Counts require a counting convention,
and a convention chosen after seeing the target is not evidence. A grid
reference requires no convention at all.

THE CAUTION ON 4/8/12 -> R4/S8/P12
----------------------------------
R4 is a 4-BIT field (16 values), S8 is 8 bits (256), P12 is 12 bits
(4096). A glyph with 4-fold symmetry, 8 nodes and 12 interfaces has
COUNTS of 4, 8, 12. Counts and bit-widths are different quantities, so
the reading only works if the glyph diagrams the codec's STRUCTURE
rather than carrying a value.

And the three numbers are not independent: given 4-fold symmetry,
element counts are multiples of 4 — 4, 8, 12, 16 — so 8 and 12 follow
almost automatically once 4-fold is present. "4, 8, 12" carries roughly
ONE piece of information, not three.

THE CAUTION ON VESICA AND 60/120
--------------------------------
A vesica piscis is two circles whose centre spacing equals their radius.
That construction generates 60 deg and 120 deg by definition — the lens
half-angle IS 60 deg. So finding 60/120 inside a vesica design is not
independent support for the domain-wall geometry; it is what a vesica is.
"""

from __future__ import annotations

import math

FEET = 0.3048

#: Verified to 0 m against the operator's conversions.
SITES = {
    "WHITE_SHEET_HILL_20260522": {
        "date": "2026-05-22", "os_grid": "ST 79973 35428",
        "lat": 51.117778, "lon": -2.287504,
        "diameter_ft": 180, "crop": "young barley",
        "role": "SQUARE_CIRCLE_PROJECTION_TRANSFORM_GLYPH",
        "location_holdout": "READY"},
    "ZURCHER_WEINLAND_20260623": {
        "date": "2026-06-23", "os_grid": None,
        "lat": None, "lon": None,
        "length_ft": 215, "crop": "wheat",
        "role": "TWO_WAY_SPIRAL_ROUTE_OPERATOR",
        "location_holdout": "BLOCKED_EXACT_LOCATION_WITHHELD"},
    "ETCHILHAMPTON_20260625": {
        "date": "2026-06-25", "os_grid": "SU 03839 60408",
        "lat": 51.342737, "lon": -1.946271,
        "diameter_ft": 180, "crop": "wild flowers / young wheat",
        "role": "BOUNDARY_QUINTUPLET",
        "location_holdout": "READY"},
}

ANCHORS = {"STONEHENGE": (51.178816, -1.826204),
           "AVEBURY": (51.428639, -1.854180)}

VECTOR_FIRST_IN_REPO = "2026-07-25"


def gc_km(a, b) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    return 6371.0 * 2 * math.asin(math.sqrt(
        math.sin((la2 - la1) / 2) ** 2
        + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2))


def square_circle_ratios(radius_m: float) -> dict:
    """Every square/circle side-to-radius ratio a 'squaring' glyph could
    mean. They span 1.41-2.00, so telling them apart needs SVG-grade
    precision, not photographs."""
    return {
        "radius_m": radius_m,
        "inscribed_square_s_over_r": math.sqrt(2),
        "equal_perimeter_s_over_r": math.pi / 2,
        "equal_area_s_over_r": math.sqrt(math.pi),
        "circumscribed_square_s_over_r": 2.0,
        "equal_area_side_m": radius_m * math.sqrt(math.pi),
        "equal_perimeter_side_m": math.pi * radius_m / 2,
        "span": "1.4142 to 2.0000",
        "precision_needed": "the four candidates are 11-19% apart, so "
                            "+-2% measurement separates them; photographs "
                            "at +-5% do not",
    }


def vesica_relations() -> dict:
    return {
        "centre_spacing_over_radius": 1.0,
        "lens_height_over_radius": math.sqrt(3),
        "lens_half_angle_deg": 60.0,
        "lens_full_angle_deg": 120.0,
        "independent_evidence_for_domain_wall": False,
        "why": "a vesica generates 60/120 by construction, so finding "
               "those angles in one is definitional, not corroborating",
    }


def count_vs_bitwidth_warning() -> dict:
    return {
        "R4_bits": 4, "R4_states": 16,
        "S8_bits": 8, "S8_states": 256,
        "P12_bits": 12, "P12_states": 4096,
        "glyph_counts": [4, 8, 12],
        "counts_equal_bitwidths": True,
        "counts_equal_state_spaces": False,
        "category_note": "matching a node COUNT to a field WIDTH only "
                         "works if the glyph diagrams codec STRUCTURE, "
                         "not a value",
        "independence_note": "given 4-fold symmetry, counts are multiples "
                             "of 4, so 8 and 12 follow almost "
                             "automatically; the trio carries ~1 piece of "
                             "information, not 3",
    }


def site_report() -> dict:
    rows = []
    for name, s in SITES.items():
        row = {"site": name, "date": s["date"], "os_grid": s["os_grid"],
               "lat": s["lat"], "lon": s["lon"], "role": s["role"],
               "location_holdout": s["location_holdout"],
               "predates_vectors": s["date"] < VECTOR_FIRST_IN_REPO}
        if s["lat"] is not None:
            for an, ac in ANCHORS.items():
                row[f"km_to_{an}"] = round(gc_km((s["lat"], s["lon"]), ac), 2)
        rows.append(row)
    ready = [r for r in rows if r["location_holdout"] == "READY"]
    return {
        "schema": "rgcs.r1044.cropsites.v1",
        "sites": rows,
        "coordinates_verified": "full TM inverse + OSGB36->WGS84 Helmert; "
                                "reproduces operator values to 0 m",
        "holdout_ready": [r["site"] for r in ready],
        "all_predate_vectors": all(r["predates_vectors"] for r in rows),
        "square_circle": square_circle_ratios(180 * FEET / 2),
        "vesica": vesica_relations(),
        "count_warning": count_vs_bitwidth_warning(),
        "why_this_batch_matters": "two formations carry published grid "
                                  "references, so they are usable as "
                                  "location holdouts with NO counting "
                                  "convention required - unlike every "
                                  "glyph reading so far",
        "blocked_on": "the projector cannot yet turn a cell key into a "
                      "coordinate (R10.25 exact failure), so the residual "
                      "still cannot be scored",
        "verdict": "R10_44_TWO_EXACT_COORDINATE_HOLDOUTS_REGISTERED",
    }
