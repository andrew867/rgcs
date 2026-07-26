"""The recursive interleaved-XYZ decoder — exact §3 transformation chain.

    raw vector -> ordered XYZ levels -> face context (codebook) -> surface
    cell (X,Y per level) -> radial interval (Z per level) -> declared
    compensation -> final region + uncertainty -> Earth frame -> geodetic.

Latitude/longitude are produced only at the final stage (and for per-level
cell *reporting* polygons). There is no direct local-XYZ -> lat/lon path in
this module, no completed-decimal-fraction path, and no shell-from-last-
digit rule (regression-tested).
"""

from __future__ import annotations

import math
from fractions import Fraction

import numpy as np

from cwatlas.icosahedron import build_icosahedron
from cwatlas.r1084 import cw_gravity_gradient as grav
from cwatlas.r1084 import cw_radial_refinement as radial
from cwatlas.r1084 import cw_surface_refinement as surf
from cwatlas.r1084.cw_hedron_state import (
    DecodedPointCandidate, DecodedRegion, EarthFrameState,
    PhysicalMeshFaceID, RecursiveDecodeTrace, SourceFaceID,
    UncertaintyCertificate)
from cwatlas.r1084.cw_recursive_xyz import parse_levels

F = Fraction
R_KM = 6371.0

#: Declared, finite compensation profiles (§8). Values are
#: (tangential_scale, radial_scale) applied per level.
COMPENSATION_PROFILES = {
    "C0_none": (F(1), F(1)),
    "C1_tangential_10_9": (F(10, 9), F(1)),
    "C2_radial_10_9": (F(1), F(10, 9)),
    "C3_metric_10_9": (F(10, 9), F(10, 9)),
    "CTRL_tangential_9_8": (F(9, 8), F(1)),
    "CTRL_tangential_81_80": (F(81, 80), F(1)),
    "CTRL_tangential_55_54": (F(55, 54), F(1)),
}
#: C4 (gravity-gradient-normalised radial step) is a computed comparison in
#: the gravity report, not a cell transform; C5 (phase/epoch metric) has no
#: repository metric authority and is recorded as NOT_APPLICABLE.


def face_vertices_earth(mesh_face: int, vertex_order, orientation):
    """Ordered face vertices (A, B, C) in the Earth frame."""
    ico = build_icosahedron()
    idx = [ico.faces[mesh_face][k] for k in vertex_order]
    return [np.asarray(orientation) @ ico.vertices[i] for i in idx]


def chart_to_unit(verts, u, v):
    a, b, c = verts
    p = a + float(u) * (b - a) + float(v) * (c - a)
    return p / np.linalg.norm(p)


def unit_to_latlon(p):
    return (math.degrees(math.asin(max(-1.0, min(1.0, float(p[2]))))),
            math.degrees(math.atan2(float(p[1]), float(p[0]))))


def tri_polygon_latlon(verts, tri):
    return tuple(unit_to_latlon(chart_to_unit(verts, u, v))
                 for u, v in tri.corners)


def tri_geodesic_diameter_km(verts, tri):
    pts = [chart_to_unit(verts, u, v) for u, v in tri.corners]
    return max(R_KM * math.acos(max(-1.0, min(1.0, float(p @ q))))
               for p, q in ((pts[0], pts[1]), (pts[1], pts[2]),
                            (pts[0], pts[2])))


def tri_area_km2(verts, tri):
    pts = [chart_to_unit(verts, u, v) for u, v in tri.corners]
    # l'Huilier spherical excess
    def side(p, q):
        return math.acos(max(-1.0, min(1.0, float(p @ q))))
    a, b, c = side(pts[1], pts[2]), side(pts[0], pts[2]), side(pts[0], pts[1])
    s = (a + b + c) / 2
    t = math.tan(s / 2) * math.tan((s - a) / 2) * \
        math.tan((s - b) / 2) * math.tan((s - c) / 2)
    return 4 * math.atan(math.sqrt(max(t, 0.0))) * R_KM ** 2


def decode(raw: str, *, mesh_face: int, vertex_order=(0, 1, 2),
           orientation=None, family: str = "IDENTITY",
           codebook: str = "E_VERTEX_TRIPLE_CANONICAL",
           source_face: int | None = None,
           compensation: str = "C0_none",
           root_radial: str = radial.PRIMARY_ROOT) -> RecursiveDecodeTrace:
    """Full recursive decode of one source vector under one declared frame
    context. Returns the complete per-level trace."""
    if orientation is None:
        orientation = np.eye(3)
    tang, rad = COMPENSATION_PROFILES[compensation]
    verts = face_vertices_earth(mesh_face, vertex_order, orientation)
    levels, partial = parse_levels(raw)

    frame = EarthFrameState(
        family=family, codebook=codebook,
        source_face=SourceFaceID(mesh_face if source_face is None
                                 else source_face),
        mesh_face=PhysicalMeshFaceID(mesh_face),
        vertex_order=tuple(vertex_order))
    trace = RecursiveDecodeTrace(raw=raw, frame=frame,
                                 compensation=compensation)

    tri = surf.root_triangle()
    shell = radial.root_state(root_radial)
    parents = [(tri, shell)]
    for n, lv in enumerate(levels, start=1):
        tri2, srec = surf.refine(tri, lv.x_digit, lv.y_digit,
                                 tangential_scale=tang)
        shell2, rrec = radial.refine(shell, lv.z_digit, radial_scale=rad)
        if not tri.contains_triangle(tri2):
            raise AssertionError("surface containment invariant violated")
        if not shell.interval.contains_interval(shell2.interval):
            raise AssertionError("radial containment invariant violated")
        iv = shell2.interval
        trace.levels.append({
            "level": n, "instruction": lv.as_tuple(),
            "surface": srec,
            "surface_polygon_latlon": tri_polygon_latlon(verts, tri2),
            "surface_diameter_km": tri_geodesic_diameter_km(verts, tri2),
            "radial": rrec,
            "gravity": grav.shell_row(f"L{n}", float(iv.r_min),
                                      float(iv.r_max))
            if iv.r_min > 0 else {"note": "inner bound at r=0; g "
                                          "undefined at origin"},
        })
        tri, shell = tri2, shell2
        parents.append((tri, shell))

    partial_axes = ()
    if partial is not None:
        tri2, srec = surf.refine_partial(tri, partial.x_digit,
                                         partial.y_digit)
        partial_axes = partial.axes_present
        trace.levels.append({
            "level": len(levels) + 1, "instruction": "PARTIAL",
            "axes_present": partial_axes, "surface": srec,
            "surface_polygon_latlon": tri_polygon_latlon(verts, tri2),
            "surface_diameter_km": tri_geodesic_diameter_km(verts, tri2),
            "radial": {"note": "no Z digit: radial interval unchanged "
                               "(axis-specific uncertainty)"},
        })
        tri = tri2

    diam = tri_geodesic_diameter_km(verts, tri)
    area = tri_area_km2(verts, tri)
    dr = float(shell.interval.thickness)
    n_lv = len(levels)
    depths = (n_lv + (1 if partial and partial.x_digit is not None else 0),
              n_lv + (1 if partial and partial.y_digit is not None else 0),
              n_lv)
    region = DecodedRegion(
        surface=tri, radial=shell,
        polygon_latlon=tri_polygon_latlon(verts, tri),
        uncertainty=UncertaintyCertificate(
            surface_max_radius_km=diam / 2,
            radial_thickness_km=dr,
            effective_3d_scale_km=(area * dr) ** (1 / 3) if dr > 0 else 0.0,
            axis_depths=depths,
            partial_level_axes=partial_axes))
    cu = sum(c[0] for c in tri.corners) / 3
    cv = sum(c[1] for c in tri.corners) / 3
    lat, lon = unit_to_latlon(chart_to_unit(verts, cu, cv))
    trace.region = region
    trace.representative = DecodedPointCandidate(
        lat_deg=lat, lon_deg=lon,
        height_km_interval=(float(shell.interval.r_min) - R_KM,
                            float(shell.interval.r_max) - R_KM))
    return trace


def point_chart_coords(verts, direction):
    """Exact-ish chart coordinates (u, v) of a unit direction via central
    projection onto the face plane; raises if outside the face."""
    a, b, c = verts
    m = np.column_stack([a, b, c])
    w = np.linalg.solve(m, np.asarray(direction, dtype=float))
    if min(w) < -1e-12:
        raise ValueError("direction not inside this face")
    w = w / w.sum()
    return (F(w[1]).limit_denominator(10 ** 12),
            F(w[2]).limit_denominator(10 ** 12))
