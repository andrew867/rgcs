"""R10.16B — the prefix/proximity test.

This test needs NO geometry, NO face, NO orientation, NO shell rule and
NO projection. It is purely combinatorial, and it constrains every
profile family at once.

If the octal payload is a recursive hierarchical address, then shared
prefix length MUST increase as real-world separation decreases: two
points in the same level-k cell share k leading symbols. That is the
defining property of a hierarchical address, and it is independent of
how the profile later assigns face, shell, epoch or route bits.

So: rank the anchor pairs by shared prefix length and by true
distance. A genuine hierarchy gives a strongly NEGATIVE rank
correlation. Anything else falsifies the hierarchical reading for that
symbol stream, whatever the downstream semantic profile does.
"""

from __future__ import annotations

import math
from itertools import combinations

#: Claimed places for the strict anchors plus the derived Avebury
#: relation. Avebury's payload is CONSTRUCTED as Stonehenge*8+1, so it
#: is a construction, not an independent observation, and it is
#: labelled as such wherever it is used.
REFERENCE_POINTS = {
    "Stonehenge": ("587652", 51.1789, -1.8262, "independent"),
    "Toronto": ("893044", 43.6532, -79.3832, "independent"),
    "Montreal": ("587924", 45.5019, -73.5674, "independent"),
    "Erie": ("784952", 42.1292, -80.0851, "independent"),
    "Avebury": ("4701217", 51.4286, -1.8544,
                "CONSTRUCTED as Stonehenge octal right-append 1"),
}


def great_circle_km(lat1, lon1, lat2, lon2) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    a = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2)
    return 2 * 6371.0088 * math.asin(min(1.0, math.sqrt(a)))


def shared_prefix(a: str, b: str) -> int:
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


def _spearman(xs, ys) -> float:
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    rx, ry = rank(xs), rank(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx)
                    * sum((b - my) ** 2 for b in ry))
    return num / den if den else float("nan")


def prefix_proximity_test(points: dict | None = None,
                          exclude_constructed: bool = True) -> dict:
    """Rank-correlate shared octal prefix against true distance."""
    pts = dict(points or REFERENCE_POINTS)
    if exclude_constructed:
        pts = {k: v for k, v in pts.items() if v[3] == "independent"}
    rows = []
    for a, b in combinations(sorted(pts), 2):
        pa, la1, lo1, _ = pts[a]
        pb, la2, lo2, _ = pts[b]
        oa, ob = format(int(pa), "o"), format(int(pb), "o")
        rows.append({
            "pair": f"{a} <-> {b}",
            "octal_a": oa, "octal_b": ob,
            "shared_prefix": shared_prefix(oa, ob),
            "distance_km": great_circle_km(la1, lo1, la2, lo2),
        })
    prefixes = [r["shared_prefix"] for r in rows]
    dists = [r["distance_km"] for r in rows]
    rho = _spearman(prefixes, dists)
    # A hierarchy demands rho << 0 (more shared prefix -> closer).
    consistent = rho < -0.5
    # the sharpest single contradiction
    worst = None
    for r in rows:
        for s in rows:
            if r["shared_prefix"] > s["shared_prefix"] and \
                    r["distance_km"] > s["distance_km"]:
                gap = ((r["shared_prefix"] - s["shared_prefix"]),
                       r["distance_km"] - s["distance_km"])
                if worst is None or gap[1] > worst["distance_excess_km"]:
                    worst = {
                        "closer_by_address": r["pair"],
                        "shared_prefix": r["shared_prefix"],
                        "actual_distance_km": r["distance_km"],
                        "farther_by_address": s["pair"],
                        "its_shared_prefix": s["shared_prefix"],
                        "its_distance_km": s["distance_km"],
                        "distance_excess_km": gap[1]}
    return {
        "schema": "rgcs.r1016b.prefix-proximity.v1",
        "rows": sorted(rows, key=lambda r: -r["shared_prefix"]),
        "spearman_rho_prefix_vs_distance": rho,
        "hierarchy_consistent": bool(consistent),
        "requirement": "a recursive hierarchical address requires a "
                       "strongly NEGATIVE rank correlation: more "
                       "shared leading symbols must mean closer",
        "sharpest_contradiction": worst,
        "geometry_free": True,
        "constrains": "every profile family at once, because it never "
                      "uses face, orientation, shell, terminal or any "
                      "projection choice",
        "verdict": ("HIERARCHY_CONSISTENT" if consistent
                    else "PREFIX_PROXIMITY_CONTRADICTION"),
    }


def stonehenge_avebury_relation() -> dict:
    """The exact right-append relation, and what it does and does not
    establish."""
    s = int(REFERENCE_POINTS["Stonehenge"][0])
    a = int(REFERENCE_POINTS["Avebury"][0])
    so, ao = format(s, "o"), format(a, "o")
    right_append = (a == s * 8 + 1)
    left_append = ao.endswith(so)
    d = great_circle_km(51.1789, -1.8262, 51.4286, -1.8544)
    return {
        "schema": "rgcs.r1016b.stonehenge-avebury.v1",
        "stonehenge_payload_decimal": s,
        "stonehenge_payload_octal": so,
        "avebury_payload_decimal": a,
        "avebury_payload_octal": ao,
        "right_append_child": ao[len(so):] if right_append else None,
        "right_append_preserved": bool(right_append),
        "left_append_preserved": bool(left_append),
        "relation": "Avebury = Stonehenge * 8 + 1 exactly",
        "surface_separation_km": d,
        "implied_cell_scale_km": d,
        "status": "EXACT_ARITHMETIC_RELATION",
        "what_it_establishes": (
            "that the two payloads stand in an exact octal "
            "parent/child relation, and that one right-append "
            "corresponds to about 27.8 km of claimed separation"),
        "what_it_does_NOT_establish": (
            "that either payload denotes its claimed place. The "
            "Avebury payload is CONSTRUCTED from the Stonehenge "
            "payload by appending a digit, so agreement between them "
            "is a property of the construction, not an independent "
            "confirmation. Treating it as validation would be "
            "TRAINING_ANCHOR_ONLY_NOT_GENERALIZATION."),
    }
