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

#: R10.16C: hierarchy metrics use the SURFACE ADDRESS, i.e. the
#: ten-digit octal rendering of the surface word, NOT a payload octal
#: obtained by reparsing that word as a lexical 16...3 transport wire.
#: The reparse produced a spurious contradiction that is retracted.
SURFACE_ANCHORS = {
    "Stonehenge": (165876523, 51.1789, -1.8262, "independent"),
    "Toronto": (168930443, 43.6532, -79.3832, "independent"),
    "Montreal": (168500683, 45.5019, -73.5674, "independent"),
    "Erie": (167849523, 42.1292, -80.0851, "independent"),
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


def surface_prefix_proximity_test(points: dict | None = None) -> dict:
    """THE corrected metric: surface_octal10 prefix vs true distance."""
    from r1016.addressing import SurfaceWord
    pts = dict(points or SURFACE_ANCHORS)
    rows = []
    for a, b in combinations(sorted(pts), 2):
        wa, la1, lo1, _ = pts[a]
        wb, la2, lo2, _ = pts[b]
        sa, sb = SurfaceWord(wa), SurfaceWord(wb)
        rows.append({
            "pair": f"{a} <-> {b}",
            "surface_octal10_a": sa.surface_octal10,
            "surface_octal10_b": sb.surface_octal10,
            "shared_prefix": shared_prefix(sa.surface_octal10,
                                           sb.surface_octal10),
            "distance_km": great_circle_km(la1, lo1, la2, lo2),
        })
    prefixes = [r["shared_prefix"] for r in rows]
    dists = [r["distance_km"] for r in rows]
    rho = _spearman(prefixes, dists)
    consistent = rho < -0.5
    # monotonic separation: does every close pair outrank every far one?
    by_prefix = {}
    for r in rows:
        by_prefix.setdefault(r["shared_prefix"], []).append(
            r["distance_km"])
    levels = sorted(by_prefix, reverse=True)
    clean = all(max(by_prefix[levels[i]]) < min(by_prefix[levels[i + 1]])
                for i in range(len(levels) - 1)) if len(levels) > 1         else False
    return {
        "schema": "rgcs.r1016c.surface-prefix-proximity.v1",
        "metric": "SurfaceWord.surface_octal10",
        "rows": sorted(rows, key=lambda r: -r["shared_prefix"]),
        "spearman_rho_prefix_vs_distance": rho,
        "hierarchy_consistent": bool(consistent),
        "cleanly_separated_by_prefix_level": bool(clean),
        "levels": {str(k): sorted(v) for k, v in by_prefix.items()},
        "requirement": "a recursive hierarchical address requires a "
                       "strongly NEGATIVE rank correlation",
        "geometry_free": True,
        "verdict": ("SURFACE_OCTAL10_HIERARCHY_NEGATIVE_RHO"
                    if consistent else "PREFIX_PROXIMITY_CONTRADICTION"),
    }


def payload_prefix_diagnostic() -> dict:
    """RETRACTED metric, kept only as a labelled diagnostic."""
    from r1016.addressing import REPARSE_DIAGNOSTIC, TransportWire
    pts = {"Stonehenge": (165876523, 51.1789, -1.8262),
           "Toronto": (168930443, 43.6532, -79.3832),
           "Montreal": (168500683, 45.5019, -73.5674),
           "Erie": (167849523, 42.1292, -80.0851)}
    rows = []
    for a, b in combinations(sorted(pts), 2):
        wa, la1, lo1 = pts[a]
        wb, la2, lo2 = pts[b]
        oa = TransportWire(str(wa)).payload_octal
        ob = TransportWire(str(wb)).payload_octal
        rows.append({"pair": f"{a} <-> {b}",
                     "shared_prefix": shared_prefix(oa, ob),
                     "distance_km": great_circle_km(la1, lo1, la2, lo2)})
    rho = _spearman([r["shared_prefix"] for r in rows],
                    [r["distance_km"] for r in rows])
    return {
        "schema": "rgcs.r1016c.payload-prefix-diagnostic.v1",
        "scope": REPARSE_DIAGNOSTIC,
        "status": "RETRACTED_AS_A_HIERARCHY_METRIC",
        "rows": rows,
        "spearman_rho_prefix_vs_distance": rho,
        "why_retracted": "this reparses a resolved surface word as a "
                         "lexical 16...3 transport wire, which is a "
                         "category error; the surface address is the "
                         "ten-digit octal of the surface word itself",
    }



#: RETAINED for the Stonehenge/Avebury relation and for the retracted
#: payload-prefix diagnostic. These are TRANSPORT-layer payloads and
#: must never be used for a hierarchy metric; use SURFACE_ANCHORS and
#: surface_prefix_proximity_test() instead.
REFERENCE_POINTS = {
    "Stonehenge": ("587652", 51.1789, -1.8262, "independent"),
    "Toronto": ("893044", 43.6532, -79.3832, "independent"),
    "Montreal": ("850068", 45.5019, -73.5674, "independent"),
    "Erie": ("784952", 42.1292, -80.0851, "independent"),
    "Avebury": ("4701217", 51.4286, -1.8544,
                "CONSTRUCTED as Stonehenge octal right-append 1"),
}


def prefix_proximity_test(points: dict | None = None,
                          exclude_constructed: bool = True) -> dict:
    """RETRACTED transport-layer metric, kept only as a diagnostic.

    Superseded by surface_prefix_proximity_test(). Reparsing a surface
    word as a lexical 16...3 transport wire is a category error; this
    function is retained so the retraction stays visible and testable.
    """
    from itertools import combinations as _c
    pts = dict(points or REFERENCE_POINTS)
    if exclude_constructed:
        pts = {k: v for k, v in pts.items() if v[3] == "independent"}
    rows = []
    for a, b in _c(sorted(pts), 2):
        pa, la1, lo1, _ = pts[a]
        pb, la2, lo2, _ = pts[b]
        oa, ob = format(int(pa), "o"), format(int(pb), "o")
        rows.append({"pair": f"{a} <-> {b}",
                     "shared_prefix": shared_prefix(oa, ob),
                     "distance_km": great_circle_km(la1, lo1, la2, lo2)})
    rho = _spearman([r["shared_prefix"] for r in rows],
                    [r["distance_km"] for r in rows])
    worst = None
    for r in rows:
        for s in rows:
            if r["shared_prefix"] > s["shared_prefix"] and                     r["distance_km"] > s["distance_km"]:
                excess = r["distance_km"] - s["distance_km"]
                if worst is None or excess > worst["distance_excess_km"]:
                    worst = {"closer_by_address": r["pair"],
                             "shared_prefix": r["shared_prefix"],
                             "actual_distance_km": r["distance_km"],
                             "farther_by_address": s["pair"],
                             "its_shared_prefix": s["shared_prefix"],
                             "its_distance_km": s["distance_km"],
                             "distance_excess_km": excess}
    return {"schema": "rgcs.r1016c.retracted-payload-metric.v1",
            "status": "RETRACTED_SUPERSEDED_BY_SURFACE_METRIC",
            "scope": "SURFACE_WORD_REPARSED_AS_WIRE_DIAGNOSTIC",
            "rows": sorted(rows, key=lambda r: -r["shared_prefix"]),
            "spearman_rho_prefix_vs_distance": rho,
            "hierarchy_consistent": bool(rho < -0.5),
            "geometry_free": True,
            "sharpest_contradiction": worst,
            "verdict": "PREFIX_PROXIMITY_CONTRADICTION"}


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
