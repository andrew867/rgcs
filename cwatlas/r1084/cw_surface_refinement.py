"""Surface refinement operator — decimal simplex lattice, Family C (§4.1).

At each level the current triangle is subdivided by the 10-per-edge lattice
into exactly 100 sub-triangles: 55 "UP" (same orientation) and 45 "DOWN"
(folded). The (X, Y) digit pair selects one child bijectively:

* ``x + y <= 9``  -> UP child with lattice corner (x, y);
* ``x + y >= 10`` -> DOWN child at (i, j) = (9 - x, 9 - y) (the folding
  rule; orientation flips).

100 digit pairs <-> 100 children, so the operator is exactly invertible and
every child is a genuine sub-triangle of its parent (containment is an
identity in rational arithmetic). This is recursive, not flattening: DOWN
children reverse orientation, so the same digit means a different direction
at different levels — the stream cannot be collapsed into completed decimal
fractions (regression-tested).

Compensation profiles (§8) scale the child-origin displacement (C1 family)
before clipping back into the parent; clipping preserves the containment
invariant and is recorded on the child record.
"""

from __future__ import annotations

from fractions import Fraction

from cwatlas.r1084.cw_hedron_state import SurfaceTriangleState

F = Fraction
TENTH = F(1, 10)


def root_triangle() -> SurfaceTriangleState:
    """The whole physical face in its own chart: corners (0,0),(1,0),(0,1)."""
    return SurfaceTriangleState(
        corners=((F(0), F(0)), (F(1), F(0)), (F(0), F(1))),
        orientation=+1, depth=0)


def _affine(tri: SurfaceTriangleState, a: Fraction, b: Fraction
            ) -> tuple[Fraction, Fraction]:
    """Map local unit-triangle coords (a, b) into the parent-face chart."""
    (u0, v0), (u1, v1), (u2, v2) = tri.corners
    return (u0 + a * (u1 - u0) + b * (u2 - u0),
            v0 + a * (v1 - v0) + b * (v2 - v0))


def child_lattice_cell(x: int, y: int) -> tuple[str, int, int]:
    """Digit pair -> (kind, i, j) lattice cell. Bijective over 0..9 x 0..9."""
    if not (0 <= x <= 9 and 0 <= y <= 9):
        raise ValueError(f"digits out of range: ({x}, {y})")
    if x + y <= 9:
        return ("UP", x, y)
    return ("DOWN", 9 - x, 9 - y)


def refine(tri: SurfaceTriangleState, x: int, y: int, *,
           tangential_scale: Fraction = F(1)
           ) -> tuple[SurfaceTriangleState, dict]:
    """Apply one (X, Y) instruction; returns (child, record).

    ``tangential_scale`` is the declared per-level compensation on the child
    origin displacement (C1 profile; 1 = none). If scaling pushes the cell
    outside the parent it is clipped back and ``clipped`` is recorded — the
    containment invariant is never sacrificed.
    """
    kind, i, j = child_lattice_cell(x, y)
    s = tangential_scale
    clipped = False
    if kind == "UP":
        oa, ob = F(i, 10) * s, F(j, 10) * s
        if oa + ob > F(9, 10):  # keep the (1/10)-size cell inside the parent
            over = oa + ob - F(9, 10)
            oa, ob, clipped = oa - over / 2, ob - over / 2, True
            oa, ob = max(oa, F(0)), max(ob, F(0))
        locs = ((oa, ob), (oa + TENTH, ob), (oa, ob + TENTH))
        orient = tri.orientation
    else:
        oa, ob = F(i, 10) * s, F(j, 10) * s
        if oa + ob > F(8, 10):
            over = oa + ob - F(8, 10)
            oa, ob, clipped = oa - over / 2, ob - over / 2, True
            oa, ob = max(oa, F(0)), max(ob, F(0))
        locs = ((oa + TENTH, ob + TENTH), (oa, ob + TENTH),
                (oa + TENTH, ob))
        orient = -tri.orientation
    child = SurfaceTriangleState(
        corners=tuple(_affine(tri, a, b) for a, b in locs),
        orientation=orient, depth=tri.depth + 1)
    record = {"kind": kind, "lattice": (i, j), "digits": (x, y),
              "clipped": clipped, "orientation": orient}
    return child, record


def refine_partial(tri: SurfaceTriangleState, x: int, y: int | None
                   ) -> tuple[SurfaceTriangleState, dict]:
    """Apply a partial final level exactly (§1.3): with X alone the cell is
    the union band of column x — represented as the smallest enclosing
    triangle of that band; with X and Y the full pair applies."""
    if y is not None:
        return refine(tri, x, y)
    # column band: a <- [x/10, (x+1)/10], b free: enclosing triangle has
    # corners (x/10, 0), ((x+1)/10, 0), (x/10, 1 - x/10)
    a0 = F(x, 10)
    locs = ((a0, F(0)), (a0 + TENTH, F(0)), (a0, 1 - a0))
    child = SurfaceTriangleState(
        corners=tuple(_affine(tri, a, b) for a, b in locs),
        orientation=tri.orientation, depth=tri.depth + 1)
    return child, {"kind": "PARTIAL_X_BAND", "lattice": (x, None),
                   "digits": (x, None), "clipped": False,
                   "orientation": tri.orientation}


def locate_digits(tri: SurfaceTriangleState, u: Fraction, v: Fraction
                  ) -> tuple[int, int]:
    """Inverse operator (encoder step): the (X, Y) digits whose child cell
    contains chart point (u, v). Exact rational arithmetic."""
    (u0, v0), (u1, v1), (u2, v2) = tri.corners
    d = (u1 - u0) * (v2 - v0) - (u2 - u0) * (v1 - v0)
    a = ((u - u0) * (v2 - v0) - (u2 - u0) * (v - v0)) / d
    b = ((u1 - u0) * (v - v0) - (u - u0) * (v1 - v0)) / d
    if not (0 <= a and 0 <= b and a + b <= 1):
        raise ValueError("point not inside triangle")
    i = min(int(a * 10), 9)
    j = min(int(b * 10), 9)
    fa, fb = a * 10 - i, b * 10 - j
    if fa + fb <= 1:
        x, y = i, j                     # UP cell
    else:
        x, y = 9 - i, 9 - j             # DOWN cell (folding rule inverse)
    return x, y
