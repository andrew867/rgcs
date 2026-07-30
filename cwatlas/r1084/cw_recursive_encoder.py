"""Inverse encoder — geodetic point -> recursive digit stream (§10).

Exactly inverts :mod:`cwatlas.r1084.cw_recursive_decoder` for the C0
(uncompensated) profile: at each level the surface digits come from
:func:`cw_surface_refinement.locate_digits` on the *current* triangle (so
folding is honoured — this is not a positional-fraction encoder), and the
radial digit from nested-tenth location in the current interval.
"""

from __future__ import annotations

import math
from fractions import Fraction

import numpy as np

from cwatlas.r1084 import cw_radial_refinement as radial
from cwatlas.r1084 import cw_surface_refinement as surf
from cwatlas.r1084.cw_recursive_decoder import (
    face_vertices_earth, point_chart_coords)

F = Fraction


def _latlon_unit(lat_deg: float, lon_deg: float):
    la, lo = math.radians(lat_deg), math.radians(lon_deg)
    return np.array([math.cos(la) * math.cos(lo),
                     math.cos(la) * math.sin(lo), math.sin(la)])


def encode_point(lat_deg: float, lon_deg: float, r_km: float, *,
                 mesh_face: int, vertex_order=(0, 1, 2), orientation=None,
                 levels: int = 3,
                 root_radial: str = radial.PRIMARY_ROOT) -> str:
    """Encode a geodetic point to ``levels`` complete XYZ triplets."""
    if orientation is None:
        orientation = np.eye(3)
    verts = face_vertices_earth(mesh_face, vertex_order, orientation)
    u, v = point_chart_coords(verts, _latlon_unit(lat_deg, lon_deg))

    tri = surf.root_triangle()
    shell = radial.root_state(root_radial)
    iv = shell.interval
    r = F(r_km).limit_denominator(10 ** 9)
    if not (iv.r_min <= r < iv.r_max):
        raise ValueError(f"radius {r_km} km outside root profile "
                         f"{root_radial}")
    digits = []
    for _ in range(levels):
        x, y = surf.locate_digits(tri, u, v)
        tri, _rec = surf.refine(tri, x, y)
        step = iv.thickness / 10
        z = min(int((r - iv.r_min) / step), 9)
        iv_lo = iv.r_min + z * step
        from cwatlas.r1084.cw_hedron_state import RadialInterval
        iv = RadialInterval(iv_lo, iv_lo + step)
        digits += [str(x), str(y), str(z)]
    return "".join(digits)
