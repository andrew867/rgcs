"""R10.10 Phase 4 — recursive child-orientation table, derived
geometrically from the chart subdivision (never hand-assigned).

Quaternary children of triangle (A,B,C) in chart space, exactly as the
recovered V1 convention subdivides:

    child 0: (A,   mAB, mCA)      corner A
    child 1: (mAB, B,   mBC)      corner B
    child 2: (mCA, mBC, C)        corner C
    child 3: (mAB, mBC, mCA)      inverted centre

For each child, the local->parent corner correspondence is DERIVED
from barycentric structure: a corner-child vertex maps to the parent
corner of its maximal barycentric weight (its own corner) or, for
edge midpoints, to the parent direction it points toward within that
child; a centre-child vertex has exactly one zero barycentric
coordinate and maps to the OPPOSITE parent corner. The point-up/
point-down flag comes from the signed chart area.

Orientation recursion: O_0 = base-face orientation;
O_(k+1) = child_transition[path_k] ∘ O_k.
"""

from __future__ import annotations

from fractions import Fraction as F

from r1010.orientation import IDENTITY, Orientation

_A, _B, _C = (F(1), F(0)), (F(0), F(1)), (F(0), F(0))
# chart corners: use barycentric weights (wA, wB, wC) directly
_CORNERS = {"A": (F(1), F(0), F(0)), "B": (F(0), F(1), F(0)),
            "C": (F(0), F(0), F(1))}


def _mid(p, q):
    return tuple((a + b) / 2 for a, b in zip(p, q))


def derive_table() -> dict:
    """Derive the four child transitions + parity/inversion flags."""
    A, B, C = _CORNERS["A"], _CORNERS["B"], _CORNERS["C"]
    mAB, mBC, mCA = _mid(A, B), _mid(B, C), _mid(C, A)
    children = {0: (A, mAB, mCA), 1: (mAB, B, mBC),
                2: (mCA, mBC, C), 3: (mAB, mBC, mCA)}

    def parent_label(vertex, child_id):
        zeros = [i for i, w in enumerate(vertex) if w == 0]
        if len(zeros) == 2:                     # a parent corner itself
            return [i for i, w in enumerate(vertex) if w != 0][0]
        (z,) = zeros                            # an edge midpoint
        if child_id == 3:
            return z                            # centre: OPPOSITE corner
        # corner child k: the midpoint points toward the non-k corner
        # it contains: weights 1/2 at two corners; the direction label
        # is the one that is NOT the child's own corner.
        halves = [i for i, w in enumerate(vertex) if w == F(1, 2)]
        own = child_id
        others = [h for h in halves if h != own]
        return others[0]

    table = {}
    for cid, verts in children.items():
        perm = tuple(parent_label(v, cid) for v in verts)
        # signed chart area (in (wA, wB) plane): barycentric winding
        pts = [(float(v[0]), float(v[1])) for v in verts]
        area2 = ((pts[1][0] - pts[0][0]) * (pts[2][1] - pts[0][1])
                 - (pts[2][0] - pts[0][0]) * (pts[1][1] - pts[0][1]))
        # "inverted centre": every local corner corresponds to the
        # OPPOSITE parent corner (its zero barycentric coordinate) —
        # the point-down medial triangle. Independent of winding.
        opposite = all(
            len([i for i, w in enumerate(v) if w == 0]) == 1
            and perm[j] == [i for i, w in enumerate(v) if w == 0][0]
            for j, v in enumerate(verts))
        o = Orientation(perm)
        table[cid] = {
            "orientation": o,
            "serialized": o.serialize(),
            "permutation_parity": o.parity,
            "winding_preserved": area2 > 0,
            "geometric_inversion": opposite,    # point-down centre child
        }
    return table


CHILD_TABLE = derive_table()


def trace_orientation(base: Orientation, path) -> list[dict]:
    """Trace O_k through a quaternary path; returns per-level states."""
    states = [{"level": 0, "orientation": base.serialize(),
               "parity": base.parity, "inverted": False}]
    o = base
    inverted = False
    for k, digit in enumerate(path, start=1):
        entry = CHILD_TABLE[int(digit)]
        o = entry["orientation"].compose(o)
        if entry["geometric_inversion"]:
            inverted = not inverted
        states.append({"level": k, "digit": int(digit),
                       "orientation": o.serialize(), "parity": o.parity,
                       "inverted": inverted})
    return states


def table_receipt() -> dict:
    return {
        "children": {str(cid): {
            "serialized": e["serialized"],
            "permutation_parity": e["permutation_parity"],
            "winding_preserved": e["winding_preserved"],
            "geometric_inversion": e["geometric_inversion"],
        } for cid, e in CHILD_TABLE.items()},
        "derivation": "barycentric zero/max structure + signed chart area",
        "centre_child_note": "child 3 permutation is CYCLIC (even parity) "
                             "but geometrically point-inverted — the two "
                             "flags are independent and both tracked",
    }
