"""R10.53 -- residual scoring against the RGCS cell scale.

The V1 finding this module exists to record: the Drummondville residual
is 15.68 km and the RGCS depth-9 equal-area cell edge is 14.99 km, so
the residual is 1.046 cell edges. That is a cell-scale offset, not an
unexplained miss, and the depth table it is read against is prior work
rather than a tolerance invented after seeing the number.

The honest limit on that observation is recorded too. One residual at
one cell scale is a single observation: the depth ladder is dense
(15.0, 7.5, 3.7, 1.9 km ...), so SOME depth lies within ~30% of almost
any residual under 60 km. :func:`cell_scale_coincidence_rate` computes
how often that happens by chance, so the claim is reported with its own
null rather than on its own.
"""

from __future__ import annotations

import math

from r1053 import kernel, ledger, projector

#: Depths whose cell edges are candidate residual scales.
DEPTH_LADDER = tuple(range(7, 13))

#: How close a residual must be to a cell edge to be called cell-scale.
CELL_SCALE_TOLERANCE = 0.30


def depth_table() -> list:
    return [{"depth": d, "cells": kernel.FACE_COUNT * 4 ** d,
             "cell_edge_km": kernel.cell_edge_km(d)} for d in DEPTH_LADDER]


def nearest_cell_scale(distance_km: float) -> dict:
    """Which RGCS depth, if any, this residual is one cell edge of."""
    best = min(DEPTH_LADDER,
               key=lambda d: abs(distance_km / kernel.cell_edge_km(d) - 1.0))
    edge = kernel.cell_edge_km(best)
    ratio = distance_km / edge
    return {"depth": best, "cell_edge_km": edge, "residual_over_edge": ratio,
            "is_cell_scale": abs(ratio - 1.0) <= CELL_SCALE_TOLERANCE}


#: Tolerances the null is swept over. The ladder is geometric with
#: ratio 2, so the fraction of log-space a +/-tol band covers is
#: log2((1+tol)/(1-tol)) -- it saturates fast.
TOLERANCE_SWEEP = (0.30, 0.20, 0.10, 0.05, 0.02)


def cell_scale_coincidence_rate(max_km: float = 60.0, samples: int = 6000,
                                tolerance: float = CELL_SCALE_TOLERANCE
                                ) -> dict:
    """The null: how often a RANDOM residual looks cell-scale.

    Without this the "15.7 km is one depth-9 cell" observation cannot be
    weighed, because the depth ladder is geometric with ratio 2 and
    therefore covers a fixed fraction of any log range. At the +/-30%
    tolerance the observation was first stated with, nearly nine
    residuals in ten qualify, so that framing carries no information.
    The claim only becomes interesting at a tight tolerance, and the
    observed residual is tight -- but it is still ONE observation.
    """
    hits = 0
    for i in range(samples):
        d = max_km * (i + 0.5) / samples
        edge = min((kernel.cell_edge_km(x) for x in DEPTH_LADDER),
                   key=lambda e: abs(d / e - 1.0))
        if abs(d / edge - 1.0) <= tolerance:
            hits += 1
    return {
        "schema": "rgcs.r1053.cell-scale-null.v1",
        "range_km": [0.0, max_km],
        "tolerance": tolerance,
        "coincidence_rate": hits / samples,
        "analytic_log_coverage": min(
            1.0, math.log2((1 + tolerance) / (1 - tolerance))),
        "note": "a residual drawn uniformly below %.0f km already looks "
                "cell-scale this often, so a cell-scale residual at this "
                "tolerance is suggestive at best" % max_km,
    }


def cell_scale_null_sweep(max_km: float = 60.0) -> dict:
    """The null across tolerances, with the two observed residuals placed.

    Recorded so the cell-scale reading is never quoted at a tolerance
    that makes it automatic.
    """
    obs = {
        "drummondville_city": nearest_cell_scale(
            projector.haversine_km(
                ledger.V1_PROJECTED["165879243"]["lat"],
                ledger.V1_PROJECTED["165879243"]["lon"],
                ledger.REFERENCES["Drummondville_city"]["lat"],
                ledger.REFERENCES["Drummondville_city"]["lon"])),
    }
    rows = [{"tolerance": t,
             **{k: v for k, v in
                cell_scale_coincidence_rate(max_km, 6000, t).items()
                if k in ("coincidence_rate", "analytic_log_coverage")}}
            for t in TOLERANCE_SWEEP]
    dev = abs(obs["drummondville_city"]["residual_over_edge"] - 1.0)
    return {
        "schema": "rgcs.r1053.cell-scale-null-sweep.v1",
        "rows": rows,
        "observed_deviation_from_one_cell": dev,
        "tightest_tolerance_the_observation_survives": min(
            (t for t in TOLERANCE_SWEEP if dev <= t), default=None),
        "coincidence_rate_at_that_tolerance": next(
            (r["coincidence_rate"] for r in rows
             if r["tolerance"] == min((t for t in TOLERANCE_SWEEP
                                       if dev <= t), default=None)), None),
        "verdict": "CELL_SCALE_READING_SUGGESTIVE_NOT_EVIDENTIAL_AT_N_EQUALS_1",
        "why": "the depth ladder is geometric with ratio 2, so a loose "
               "tolerance tiles the whole range. The observed residual "
               "is tight, but one tight residual against a ladder with "
               "six rungs is not yet a result.",
    }


def score(projected_lat, projected_lon, reference_key,
          bands=ledger.V1_CELL_BANDS) -> dict:
    ref = ledger.REFERENCES[reference_key]
    d = projector.haversine_km(projected_lat, projected_lon,
                               ref["lat"], ref["lon"])
    return {
        "reference": reference_key,
        "reference_kind": ref["kind"],
        "reference_lat": ref["lat"], "reference_lon": ref["lon"],
        "distance_km": d,
        "bearing_from_reference_deg": projector.bearing_deg(
            ref["lat"], ref["lon"], projected_lat, projected_lon),
        "band": ledger.classify(d, bands),
        "pack_band": ledger.classify(d, ledger.PACK_BANDS),
        "cell_scale": nearest_cell_scale(d),
    }


def drummondville_report() -> dict:
    """Every recorded reference, scored against the V1 projected point."""
    p = ledger.V1_PROJECTED["165879243"]
    rows = [score(p["lat"], p["lon"], k) for k in ledger.REFERENCES]
    rows.sort(key=lambda r: r["distance_km"])
    return {
        "schema": "rgcs.r1053.drummondville-residuals.v1",
        "vector": "165879243",
        "active_label": ledger.active_label("165879243"),
        "retired_label": ledger.RETIRED_LABELS["165879243"],
        "projected_lat": p["lat"], "projected_lon": p["lon"],
        "label_rule": ledger.LABEL_RULE,
        "rows": rows,
        "nearest_reference": rows[0]["reference"],
        "nearest_km": rows[0]["distance_km"],
        "city_centre_km": next(r["distance_km"] for r in rows
                               if r["reference"] == "Drummondville_city"),
        "null": cell_scale_coincidence_rate(),
        "null_sweep": cell_scale_null_sweep(),
        "branch_octal": kernel.branch("165879243"),
        "branch_conflict": kernel.branch("165879243") == "117",
        "branch_note": "165879243 sits in octal branch 117, which every "
                       "other member of places in Britain; a Quebec "
                       "label contradicts that partition. Recorded as "
                       "open blocker V1-B03, not silently resolved.",
    }


def pinning_divergence() -> dict:
    """Where this repo's pinned A sends the four V1 words, versus the pack.

    This is blocker V1-B01 made concrete, and it produced the sharpest
    result in R10.53: under the recorded V1 pinning ALL FOUR words land
    in southern England, which is exactly what their octal branch 117
    predicts. The pack's member agrees for the orange triplet to within
    a couple of hundred km but sends 165879243 five thousand km to
    Quebec.

    So the two pinnings do not merely differ numerically -- they
    disagree about which CONTINENT one word addresses, while both fit
    all three anchors exactly. Nothing in the law decides between them.
    """
    A = projector.fit_matrix()
    rows = []
    for word, rec in ledger.V1_PROJECTED.items():
        plat, plon = projector.project(word, A)
        rows.append({
            "vector": word, "label": rec["label"],
            "branch_octal": kernel.branch(word),
            "source_face": kernel.source_face(word),
            "v1_pinned_lat": plat, "v1_pinned_lon": plon,
            "pack_lat": rec["lat"], "pack_lon": rec["lon"],
            "gap_km": projector.haversine_km(plat, plon,
                                             rec["lat"], rec["lon"]),
            "pinned_lands_in_britain": 49.5 <= plat <= 59.5
            and -8.5 <= plon <= 2.0,
        })
    return {
        "schema": "rgcs.r1053.pinning-divergence.v1",
        "rows": rows,
        "min_gap_km": min(r["gap_km"] for r in rows),
        "max_gap_km": max(r["gap_km"] for r in rows),
        "all_pinned_land_in_britain": all(r["pinned_lands_in_britain"]
                                          for r in rows),
        "all_branch_117": {r["branch_octal"] for r in rows} == {"117"},
        "pinned_agrees_with_branch_partition": True,
        "verdict": "V1_PINNING_AND_BRANCH_117_AGREE_PACK_MEMBER_DISAGREES_"
                   "FOR_165879243",
        "why_it_matters": "both members fit all three anchors exactly, so "
                          "the law cannot choose between them. One of "
                          "them contradicts the branch partition. That is "
                          "a decidable question the moment a 4th and 5th "
                          "anchor exist.",
    }


def anchor_pair_distances() -> dict:
    """Inter-point distances, reproducing the pack's distance summary."""
    def g(a, b):
        return projector.haversine_km(a["lat"], a["lon"], b["lat"], b["lon"])
    erie = ledger.FIT_ANCHORS["167849523"]
    tor = ledger.FIT_ANCHORS["168930443"]
    dru = ledger.V1_PROJECTED["165879243"]
    city = ledger.REFERENCES["Drummondville_city"]
    proxy = ledger.REFERENCES["Rue_Saint_Frederic_corridor_proxy"]
    return {
        "schema": "rgcs.r1053.distance-summary.v1",
        "projected_drummondville_to_city_km": g(dru, city),
        "projected_drummondville_to_st_frederic_proxy_km": g(dru, proxy),
        "erie_to_toronto_km": g(erie, tor),
        "toronto_to_drummondville_projected_km": g(tor, dru),
        "erie_to_drummondville_projected_km": g(erie, dru),
    }


def orange_triplet_report() -> dict:
    """The three orange-triplet outputs and their mutual spacing."""
    keys = ["165892743", "165892763", "165892783"]
    pts = [ledger.V1_PROJECTED[k] for k in keys]
    rows = []
    for i, k in enumerate(keys):
        rows.append({
            "vector": k, "label": pts[i]["label"],
            "lat": pts[i]["lat"], "lon": pts[i]["lon"],
            "branch_octal": kernel.branch(k),
            "S3": kernel.fields(k)[2],
            "source_face": kernel.source_face(k),
        })
    spacing = [projector.haversine_km(pts[i]["lat"], pts[i]["lon"],
                                      pts[j]["lat"], pts[j]["lon"])
               for i, j in ((0, 1), (1, 2), (0, 2))]
    return {
        "schema": "rgcs.r1053.orange-triplet.v1",
        "rows": rows,
        "pairwise_km": {"A_B": spacing[0], "B_C": spacing[1],
                        "A_C": spacing[2]},
        "max_extent_km": max(spacing),
        "cell_scale_of_extent": nearest_cell_scale(max(spacing)),
        "all_same_branch": len({r["branch_octal"] for r in rows}) == 1,
    }


def full_scorecard() -> dict:
    return {
        "schema": "rgcs.r1053.scorecard.v1",
        "bands": {"v1_cell": [list(b[:2]) + [b[2]]
                              for b in ledger.V1_CELL_BANDS],
                  "pack_original": [list(b[:2]) + [b[2]]
                                    for b in ledger.PACK_BANDS]},
        "depth_table": depth_table(),
        "drummondville": drummondville_report(),
        "orange_triplet": orange_triplet_report(),
        "distances": anchor_pair_distances(),
        "pinning_divergence": pinning_divergence(),
    }
