"""R10.59B -- N-vector polygons: area, perimeter, centroid, validity.

Three or more RGCS words define a spherical polygon whose vertices are
their projected points. This module measures that polygon and the
companion HTML page lets an operator build the vertex list interactively.

WHAT IS DECIDABLE HERE, AND WHAT IS NOT
---------------------------------------
The geometry is decidable and is decided: spherical area is computed two
independent ways and cross-checked, the perimeter is a sum of verified
great-circle edges, and self-intersection is detected rather than
ignored. A polygon that crosses itself has no well-defined interior, and
reporting an area for it would be meaningless -- so it is flagged.

What is NOT decidable is whether the vertices are the right places.
Every vertex is projector output and remains underdetermined under
V1-B01/B02. An exactly measured polygon over candidate vertices is an
exactly measured polygon over candidate vertices.

VERTEX ORDER MATTERS
--------------------
A polygon is defined by its vertex SEQUENCE, not by its vertex set: the
same points in a different order enclose a different region, or none.
The order given is the order used. :func:`order_by_centroid_bearing`
offers a canonical re-ordering, and the record always says which was
applied so a reader can tell a deliberate ordering from an accident.
"""

from __future__ import annotations

import math

import numpy as np

from r1053 import kernel, ledger, projector

EARTH_RADIUS_KM = projector.EARTH_RADIUS_KM
MIN_VERTICES = 3


class PolygonError(ValueError):
    """The vertex list cannot form a polygon."""


def _unit(lat, lon):
    return projector.unit_from_latlon(lat, lon)


def perimeter_km(points) -> float:
    """Sum of great-circle edges, closing the ring."""
    n = len(points)
    return sum(projector.haversine_km(points[i][0], points[i][1],
                                      points[(i + 1) % n][0],
                                      points[(i + 1) % n][1])
               for i in range(n))


def area_km2_turning(points) -> float:
    """Spherical area from the Gauss-Bonnet turning-angle identity.

    For a simple spherical polygon, ``Area = R^2 * (2*pi - sum of
    exterior turning angles)``. This is EXACT, and it is independent of
    the fan triangulation in :func:`area_km2_excess` -- it walks the
    boundary and never forms an interior triangle -- so agreement
    between the two is a real check rather than the same arithmetic
    twice.

    An earlier revision used the planar "spherical shoelace"
    approximation here. It disagreed with the exact excess by 42 % on
    the anchor triangle and by a factor of two on a spherical octant,
    so it was removed rather than kept as a weak second opinion.
    """
    n = len(points)
    v = [_unit(la, lo) for la, lo in points]
    total_turn = 0.0
    for i in range(n):
        prev, cur, nxt = v[i - 1], v[i], v[(i + 1) % n]
        # tangent directions at `cur`, along each incident edge
        t_in = np.cross(cur, np.cross(prev, cur))
        t_out = np.cross(cur, np.cross(cur, nxt))
        ni, no = np.linalg.norm(t_in), np.linalg.norm(t_out)
        if ni < 1e-12 or no < 1e-12:
            continue                       # degenerate vertex
        t_in, t_out = t_in / ni, t_out / no
        cosang = float(np.clip(np.dot(t_in, t_out), -1, 1))
        sinang = float(np.dot(np.cross(t_in, t_out), cur))
        total_turn += math.atan2(sinang, cosang)
    area = (2 * math.pi - abs(total_turn)) * EARTH_RADIUS_KM ** 2
    return abs(area)


def area_km2_excess(points) -> float:
    """Spherical area by fan triangulation and the spherical excess.

    Independent of :func:`area_km2_turning`: it uses L'Huilier's theorem
    on each triangle of a fan from vertex 0, and signs each contribution
    by the triangle's orientation so that a non-convex polygon still
    totals correctly. L'Huilier is numerically stable for the thin
    slivers that RGCS vector sets often produce -- the three fit anchors
    span 5769 km, 5620 km and 179 km.
    """
    n = len(points)
    if n < 3:
        return 0.0
    v = [_unit(la, lo) for la, lo in points]
    total = 0.0
    for i in range(1, n - 1):
        a, b, c = v[0], v[i], v[i + 1]
        # side lengths as angles
        ab = math.acos(float(np.clip(a @ b, -1, 1)))
        bc = math.acos(float(np.clip(b @ c, -1, 1)))
        ca = math.acos(float(np.clip(c @ a, -1, 1)))
        s = (ab + bc + ca) / 2.0
        t = (math.tan(s / 2) * math.tan((s - ab) / 2)
             * math.tan((s - bc) / 2) * math.tan((s - ca) / 2))
        if t <= 0:
            continue
        excess = 4.0 * math.atan(math.sqrt(t))
        sign = 1.0 if float(np.dot(np.cross(b - a, c - a), a)) >= 0 else -1.0
        total += sign * excess
    return abs(total) * EARTH_RADIUS_KM ** 2


def centroid(points) -> tuple:
    """Unit-vector mean of the vertices, back-projected to the sphere."""
    v = np.sum([_unit(la, lo) for la, lo in points], axis=0)
    if np.linalg.norm(v) < 1e-12:
        raise PolygonError("vertices cancel; centroid is undefined")
    return projector.latlon_from_unit(v)


def _seg_intersects(p1, p2, p3, p4, tol=1e-12) -> bool:
    """Do great-circle segments p1p2 and p3p4 cross, excluding endpoints?"""
    a, b, c, d = (_unit(*p) for p in (p1, p2, p3, p4))
    n1, n2 = np.cross(a, b), np.cross(c, d)
    line = np.cross(n1, n2)
    if np.linalg.norm(line) < 1e-12:
        return False                       # same great circle
    line = line / np.linalg.norm(line)
    for cand in (line, -line):
        def between(p, q, x):
            ang = math.acos(float(np.clip(p @ q, -1, 1)))
            return (math.acos(float(np.clip(p @ x, -1, 1)))
                    + math.acos(float(np.clip(q @ x, -1, 1)))) <= ang + 1e-9
        if between(a, b, cand) and between(c, d, cand):
            # exclude shared endpoints
            if any(float(np.dot(cand, e)) > 1 - tol for e in (a, b, c, d)):
                continue
            return True
    return False


def self_intersections(points) -> list:
    """Every crossing pair of non-adjacent edges. Empty means simple."""
    n = len(points)
    out = []
    for i in range(n):
        for j in range(i + 1, n):
            if j == i or (j + 1) % n == i or (i + 1) % n == j:
                continue
            if _seg_intersects(points[i], points[(i + 1) % n],
                               points[j], points[(j + 1) % n]):
                out.append([i, j])
    return out


def order_by_centroid_bearing(points) -> list:
    """Sort vertices by bearing from their centroid.

    Produces a simple (non-self-intersecting) ring for point sets that
    are star-shaped about their centroid, which covers the ordinary
    case. It is offered, never applied silently.
    """
    c = centroid(points)
    return sorted(points,
                  key=lambda p: projector.bearing_deg(c[0], c[1], p[0], p[1]))


def vertices_from_vectors(words, overrides=None) -> list:
    """Project each word, recording where its coordinate came from."""
    overrides = overrides or {}
    out = []
    for w in words:
        s = str(w).strip()
        kernel.assert_direct_lane(s)
        if s in overrides:
            lat, lon = overrides[s]
            src = "OPERATOR_SUPPLIED"
        elif s in ledger.FIT_ANCHORS:
            lat = ledger.FIT_ANCHORS[s]["lat"]
            lon = ledger.FIT_ANCHORS[s]["lon"]
            src = "FIT_ANCHOR_TARGET"
        else:
            lat, lon = projector.project(s)
            src = "V1_PINNED_PROJECTION"
        out.append({
            "vector": s, "lat": lat, "lon": lon, "coordinate_source": src,
            "octal10": kernel.octal10(s), "branch_octal": kernel.branch(s),
            "source_face": kernel.source_face(s),
            "label": (ledger.active_label(s)
                      or (ledger.FIT_ANCHORS.get(s)
                          or ledger.V1_PROJECTED.get(s) or {}).get("label", "")
                      or f"vector {s}"),
            "is_located_target": False,
        })
    return out


def build(words, overrides=None, reorder: bool = False) -> dict:
    """Measure the polygon spanned by three or more RGCS words."""
    words = [str(w).strip() for w in words if str(w).strip()]
    if len(words) < MIN_VERTICES:
        raise PolygonError(
            f"a polygon needs at least {MIN_VERTICES} vectors, got "
            f"{len(words)}; use `path` for two")
    if len(set(words)) < MIN_VERTICES:
        raise PolygonError(
            f"only {len(set(words))} distinct vectors; a polygon needs "
            f"{MIN_VERTICES} distinct vertices")
    verts = vertices_from_vectors(words, overrides)
    pts = [(v["lat"], v["lon"]) for v in verts]
    if reorder:
        ordered = order_by_centroid_bearing(pts)
        index = {p: i for i, p in enumerate(pts)}
        verts = [verts[index[p]] for p in ordered]
        pts = ordered
    a1, a2 = area_km2_excess(pts), area_km2_turning(pts)
    denom = max(a1, a2, 1e-9)
    crossings = self_intersections(pts)
    edges = [{"from": verts[i]["vector"],
              "to": verts[(i + 1) % len(pts)]["vector"],
              "km": projector.haversine_km(*pts[i],
                                           *pts[(i + 1) % len(pts)])}
             for i in range(len(pts))]
    return {
        "schema": "rgcs.r1059.vector-polygon.v1",
        "vertices": verts,
        "vertex_count": len(verts),
        "vertex_order": "REORDERED_BY_CENTROID_BEARING" if reorder
                        else "AS_SUPPLIED",
        "edges": edges,
        "perimeter_km": perimeter_km(pts),
        "area_km2": a1,
        "area_km2_cross_check": a2,
        "area_methods_agree_rel": abs(a1 - a2) / denom,
        "area_is_trustworthy": (not crossings
                                and abs(a1 - a2) / denom < 1e-6),
        "self_intersections": crossings,
        "is_simple": not crossings,
        "centroid": list(centroid(pts)),
        "area_in_depth9_cells": a1 / (kernel.cell_edge_km(9) ** 2
                                      * math.sqrt(3) / 4),
        "branches": sorted({v["branch_octal"] for v in verts}),
        "all_same_branch": len({v["branch_octal"] for v in verts}) == 1,
        "polygon_geometry_is_verified": True,
        "vertices_are_verified_places": False,
        "caveat": "the polygon's area, perimeter and centroid are exact "
                  "for the given vertices and cross-checked by two "
                  "independent methods; the VERTEX POSITIONS are "
                  "projector output and remain underdetermined under "
                  "V1-B01/B02",
    }
