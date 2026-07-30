"""R10.53 -- the direct 9-digit octal lane and the V1 geometric kernel.

NON-NEGOTIABLE CORRECTIONS 1-3, implemented here
------------------------------------------------
1. A 9-digit direct word is NOT ``16 | payload | 3``. The leading "16"
   is a lexical coincidence of the decimal rendering, not a field. Any
   attempt to strip it is refused by :func:`assert_direct_lane`.
2. Direct words are decoded by the BINARY/OCTAL path first: the word is
   a 30-bit integer, cut as ``F5 | Q22 | S3``.
3. The decimal transport/body header table is scoped to WIDE ENVELOPE
   records only. :func:`decimal_header_table_applies` returns False for
   every direct word, and the wide-envelope batch stays gated.

THE V1 KERNEL
-------------
    F5   -> source_face = (F5 + 14) % 20   on the icosahedron
    Q22  -> 11 two-bit symbols, one 4-way spherical refinement each
    t    -> the SOURCE ODDS SPLIT 10/19, not the 1/2 midpoint
    S3   -> M3 check digit, NOT geometry (correction 10)

The edge split parameter is the source ratio 10/19 = 0.526315..., and
it is used for every level. Using 1/2 recovers ordinary geodesic
subdivision; the ratio is what makes this the RGCS refinement rather
than a generic geodesic grid.
"""

from __future__ import annotations

import math

import numpy as np

from r1025 import hedra

#: SOURCE ODDS SPLIT. Recorded in the pack as ``t = 10/19``.
SPLIT_T = 10.0 / 19.0

#: (F5 + 14) % 20 -- recorded in the pack as the source-face map.
FACE_OFFSET = 14
FACE_COUNT = 20

#: Q22 carries 11 two-bit refinement symbols.
Q22_SYMBOLS = 11
Q22_BITS = 22

WORD_BITS = 30
EARTH_RADIUS_KM = 6371.0

_V, _F = hedra._icosahedron()
_V = [np.asarray(v, float) / np.linalg.norm(v) for v in _V]


class DirectLaneError(ValueError):
    """The value was handled as though it were a transport wire."""


def assert_direct_lane(word) -> int:
    """Accept a direct RGCS-30 word; refuse the ``16|payload|3`` reading.

    CORRECTION 1. A 9-digit direct word must not be header-stripped. The
    guard is structural, not lexical: a direct word is exactly a 30-bit
    integer, and stripping two decimal digits from one produces a value
    that is no longer 30 bits wide and no longer addresses anything.
    """
    s = str(word).strip()
    if not s.isdigit():
        raise DirectLaneError(f"{word!r} is not a decimal RGCS word")
    v = int(s)
    if v.bit_length() > WORD_BITS:
        raise DirectLaneError(
            f"{s} is {v.bit_length()} bits wide; a direct RGCS-30 word is "
            f"at most {WORD_BITS}. Wide-envelope records go through the "
            f"gated bridge, not this lane")
    return v


def decimal_header_table_applies(word) -> bool:
    """CORRECTION 3: the decimal header table is wide-envelope only.

    Returns False for every direct 9/10-digit word. The table
    (16 = Sol-member, 16-5 Terra, 16-7 Luna) was recovered from wide
    records and has never been shown to apply to a direct word; scoping
    it here is what keeps the two lanes from contaminating each other.
    """
    try:
        assert_direct_lane(word)
    except DirectLaneError:
        return True            # wide envelope: table is in scope
    return False


def fields(word) -> tuple:
    """Cut a direct word as F5 | Q22 | S3. The binary path, first."""
    v = assert_direct_lane(word)
    return (v >> 25) & 31, (v >> 3) & ((1 << Q22_BITS) - 1), v & 7


def octal10(word) -> str:
    """The 10-symbol octal rendering -- the direct lane's native form."""
    return format(assert_direct_lane(word), "010o")


def branch(word) -> str:
    """The leading three octal symbols. 117 = British, 120 = N.American.

    Recorded because it is the sharpest structural partition found so
    far and it constrains which labels are admissible for a word.
    """
    return octal10(word)[:3]


def q22_symbols(q22: int) -> list:
    """The 11 two-bit refinement symbols, most significant first."""
    return [(q22 >> (Q22_BITS - 2 - 2 * i)) & 3 for i in range(Q22_SYMBOLS)]


def _slerp(a, b, t):
    d = float(np.clip(np.dot(a, b), -1.0, 1.0))
    o = math.acos(d)
    if o < 1e-12:
        return a
    s = math.sin(o)
    return (math.sin((1.0 - t) * o) / s) * a + (math.sin(t * o) / s) * b


def refine(tri, symbol: int, t: float = SPLIT_T) -> tuple:
    """One 4-way spherical refinement of ``tri`` at split parameter t."""
    a, b, c = tri
    ab, bc, ca = _slerp(a, b, t), _slerp(b, c, t), _slerp(c, a, t)
    return {0: (a, ab, ca), 1: (ab, b, bc),
            2: (ca, bc, c), 3: (ab, bc, ca)}[symbol]


def source_face(word) -> int:
    f5, _, _ = fields(word)
    return (f5 + FACE_OFFSET) % FACE_COUNT


def cell(word, depth: int = Q22_SYMBOLS, t: float = SPLIT_T) -> tuple:
    """The addressed spherical cell, as a triangle of unit vectors."""
    _, q22, _ = fields(word)
    tri = tuple(_V[i] for i in _F[source_face(word)])
    for s in q22_symbols(q22)[:depth]:
        tri = refine(tri, s, t)
    return tri


def kernel_vector(word, depth: int = Q22_SYMBOLS, t: float = SPLIT_T):
    """``u`` -- the pre-projection unit vector for a direct word."""
    tri = cell(word, depth, t)
    u = np.asarray(tri[0]) + np.asarray(tri[1]) + np.asarray(tri[2])
    return u / np.linalg.norm(u)


def cell_edge_km(depth: int) -> float:
    """Equal-area edge proxy for an icosahedral 4-way grid at ``depth``.

    Recorded because the V1 residual scale is read against it: depth 9
    is 14.99 km and depth 11 is 3.75 km, so a ~15 km residual is one
    depth-9 cell edge rather than an unexplained miss.
    """
    area = 4.0 * math.pi * EARTH_RADIUS_KM ** 2 / (FACE_COUNT * 4 ** depth)
    return math.sqrt(4.0 * area / math.sqrt(3.0))
