"""R12 — quaternary triangular refinement on the frozen icosahedron, and
the reason its cells are not equal-area.

Each triangular face of the canonical icosahedron is subdivided by
connecting the midpoints of its three edges, which replaces one triangle
with **four**: three at the corners and one inverted in the centre. After
``L`` levels a face carries ``4**L`` cells and the whole solid carries
``20 * 4**L``. At the working depth of eleven levels that is exactly::

    4**11        = 4_194_304          cells per face
    20 * 4**11   = 83_886_080         cells over the solid

and the address budget the R12 packet grammar reserves for it -- five
face bits and twenty-two path bits, twenty-seven bits in all -- holds
``2**27 = 134_217_728`` codes, comfortably more than the tessellation
needs. The slack is stated, not waved at.

**The correction the sphere forces.** On a flat triangle midpoint
subdivision produces four congruent sub-triangles of exactly equal area.
On a sphere it cannot: the edge midpoints must be pushed back out onto
the sphere before they are used, and re-normalising them makes the centre
cell bulge and the corner cells shrink. The four children are therefore
UNEQUAL in area, and the inequality grows with the parent's size, so a
refinement of the icosahedron is emphatically **not** an equal-area grid.
Treating it as one -- assigning every cell the same weight, reading cell
count as area -- is a real error, and :func:`refuse_equal_area_assumption`
refuses it. The area of a cell is computed exactly from spherical excess
(Girard's theorem, via the Van Oosterom-Strackee formula), and
:func:`area_spread` reports the non-zero range across cells at a level.

**The completeness check has POWER.** However unequal the individual
cells are, their solid angles must sum to ``4*pi`` at every level,
because the children of a triangle exactly tile their parent and the
faces exactly tile the sphere. :func:`total_solid_angle` confirms this to
tolerance, which is what tells us the tessellation loses nothing: it is
the positive control that the area machinery is measuring the whole
sphere and not a subset of it.

The solid itself is not rebuilt here. It is imported from
:mod:`r11.earthface` and asserted to be the very same object, so the
refinement is defined on the icosahedron that was frozen before any
target data, and never on a fresh one that might have been oriented to
suit a result.

Nothing here is measured. The standing verdict is
**QUATERNARY_REFINEMENT_GEOMETRY_EXACT**.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from enum import Enum

import numpy as np

from r11.earthface import CANONICAL_ICOSAHEDRON, Icosahedron

# =======================================================================
# Claim classes and the standing verdict
# =======================================================================


class ClaimClass(Enum):
    """The claim classes this repository is allowed to emit."""

    EXACT_IDENTITY = "EXACT_IDENTITY"
    SOURCE_ESTABLISHED_PHYSICS = "SOURCE_ESTABLISHED_PHYSICS"
    REPOSITORY_COMPUTATIONAL_RESULT = "REPOSITORY_COMPUTATIONAL_RESULT"
    ENGINEERING_CANDIDATE = "ENGINEERING_CANDIDATE"
    RETROSPECTIVE_NUMERIC_MATCH = "RETROSPECTIVE_NUMERIC_MATCH"
    PROSPECTIVE_PREDICTION = "PROSPECTIVE_PREDICTION"
    BENCH_MEASUREMENT = "BENCH_MEASUREMENT"
    UNSUPPORTED = "UNSUPPORTED"
    BLOCKED_MISSING_DATA = "BLOCKED_MISSING_DATA"


VERDICT = "QUATERNARY_REFINEMENT_GEOMETRY_EXACT"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"


class IcosaRefineError(ValueError):
    """Raised on a wrong face count, a malformed path, an out-of-range
    level, an equal-area assumption, or a solid that is not the frozen
    canonical icosahedron."""


# =======================================================================
# The solid: imported, never rebuilt
# =======================================================================

#: The refinement is defined on the SAME frozen solid r11.earthface built.
#: Not a copy, not a fresh build: the identical object, so nothing here
#: can quietly re-orient the icosahedron to suit a result.
ICOSAHEDRON = CANONICAL_ICOSAHEDRON

FACE_COUNT = 20
CHILDREN_PER_TRIANGLE = 4                 # midpoint subdivision
WORKING_LEVELS = 11                       # the R12 refinement depth

#: The address budget the packet grammar reserves: 5 face + 22 path bits.
FACE_BITS = 5
PATH_BITS = 22
ADDRESS_BITS = FACE_BITS + PATH_BITS      # 27


def assert_same_icosahedron(ico: Icosahedron = ICOSAHEDRON) -> bool:
    """Confirm the solid IS r11.earthface's frozen canonical object.

    Identity, not equality: ``is`` the same object. A refinement defined
    on a look-alike built here would be one rotation away from the frozen
    one, and that rotation is exactly the freedom r11.earthface refuses."""
    if ico is not CANONICAL_ICOSAHEDRON:
        raise IcosaRefineError(
            "refused: the refinement must run on the SAME frozen solid "
            "imported from r11.earthface, not a rebuilt or rotated copy. "
            "A fresh icosahedron could be oriented to suit a result; the "
            "frozen one cannot.")
    if len(ico.faces) != FACE_COUNT:
        raise IcosaRefineError(
            f"the icosahedron must have {FACE_COUNT} faces, has "
            f"{len(ico.faces)}")
    if ico.vertices.shape != (12, 3):
        raise IcosaRefineError("the icosahedron must have 12 vertices")
    return True


# =======================================================================
# Cell counting and the address budget, exactly
# =======================================================================

def cells_per_face(level: int) -> int:
    """``4**level`` cells on one face after ``level`` refinements."""
    _check_level(level)
    return CHILDREN_PER_TRIANGLE ** level


def total_cells(level: int) -> int:
    """``20 * 4**level`` cells over the whole solid."""
    return FACE_COUNT * cells_per_face(level)


def _check_level(level: int) -> int:
    if not isinstance(level, int) or isinstance(level, bool):
        raise IcosaRefineError("level must be a plain int")
    if level < 0:
        raise IcosaRefineError("level must be non-negative")
    return level


def address_budget(level: int = WORKING_LEVELS) -> dict:
    """State the count and the bit budget exactly, with the slack.

    At the working depth the cell count is checked against its literal
    value and against the twenty-seven-bit address space; the surplus
    codes are reported rather than left implicit."""
    _check_level(level)
    per_face = cells_per_face(level)
    total = total_cells(level)
    capacity = 1 << ADDRESS_BITS
    return {
        "level": level,
        "children_per_triangle": CHILDREN_PER_TRIANGLE,
        "cells_per_face": per_face,
        "total_cells": total,
        "face_bits": FACE_BITS,
        "path_bits": PATH_BITS,
        "address_bits": ADDRESS_BITS,
        "address_capacity": capacity,          # 2**27 == 134_217_728
        "path_capacity": 1 << PATH_BITS,       # 2**22 == 4_194_304
        "path_bits_hold_one_face": (1 << PATH_BITS) == per_face
        if level == WORKING_LEVELS else (1 << PATH_BITS) >= per_face,
        "budget_sufficient": total <= capacity,
        "slack_codes": capacity - total,
        "claim_class": ClaimClass.EXACT_IDENTITY.value,
        "why": (
            f"midpoint subdivision quadruples the cell count each level, "
            f"so {level} levels give 4**{level} = {per_face} per face "
            f"and 20 * 4**{level} = {total} over the solid; the "
            f"{ADDRESS_BITS}-bit address space holds {capacity}, leaving "
            f"{capacity - total} spare codes"),
    }


# =======================================================================
# Cell addresses: (face, path) <-> integer, exact round trip
# =======================================================================

def _check_path(path, levels: int = WORKING_LEVELS) -> tuple:
    try:
        digits = tuple(path)
    except TypeError as exc:
        raise IcosaRefineError("path must be an iterable of ints") from exc
    if len(digits) != levels:
        raise IcosaRefineError(
            f"a level-{levels} path has exactly {levels} entries, got "
            f"{len(digits)}")
    for d in digits:
        if not isinstance(d, int) or isinstance(d, bool):
            raise IcosaRefineError(f"path entry {d!r} must be a plain int")
        if not 0 <= d < CHILDREN_PER_TRIANGLE:
            raise IcosaRefineError(
                f"path entry {d} outside 0..{CHILDREN_PER_TRIANGLE - 1}; "
                f"each level chooses one of {CHILDREN_PER_TRIANGLE} "
                f"sub-triangles")
    return digits


def _check_face(face: int) -> int:
    if not isinstance(face, int) or isinstance(face, bool):
        raise IcosaRefineError("face must be a plain int")
    if not 0 <= face < FACE_COUNT:
        raise IcosaRefineError(
            f"face {face} outside 0..{FACE_COUNT - 1}")
    return face


def cell_address(face: int, path, levels: int = WORKING_LEVELS) -> int:
    """Pack ``(face, path)`` into one integer address, exactly.

    ``path`` is ``levels`` entries in ``0..3``, most significant level
    first. Face occupies the high bits, the base-4 path the low bits.
    Inverted by :func:`address_to_cell`."""
    _check_face(face)
    digits = _check_path(path, levels)
    index = 0
    for d in digits:
        index = index * CHILDREN_PER_TRIANGLE + d
    return face * (CHILDREN_PER_TRIANGLE ** levels) + index


def address_to_cell(address: int, levels: int = WORKING_LEVELS) -> tuple:
    """Invert :func:`cell_address`: ``(face, path)``. Exact."""
    if not isinstance(address, int) or isinstance(address, bool):
        raise IcosaRefineError("address must be a plain int")
    total = total_cells(levels)
    if not 0 <= address < total:
        raise IcosaRefineError(
            f"address {address} outside 0..{total - 1} for {levels} levels")
    per_face = CHILDREN_PER_TRIANGLE ** levels
    face, index = divmod(address, per_face)
    digits = []
    for _ in range(levels):
        index, d = divmod(index, CHILDREN_PER_TRIANGLE)
        digits.append(d)
    digits.reverse()
    return face, tuple(digits)


# =======================================================================
# The geometry of one cell
# =======================================================================

def _normalise(v: np.ndarray) -> np.ndarray:
    a = np.asarray(v, dtype=float)
    n = float(np.linalg.norm(a))
    if n == 0.0:
        raise IcosaRefineError("cannot normalise a zero vector")
    return a / n


def _subdivide(tri: tuple) -> tuple:
    """One triangle -> four children, midpoints re-projected to the sphere.

    Child ordering: ``0`` corner at ``a``, ``1`` corner at ``b``, ``2``
    corner at ``c``, ``3`` the inverted centre triangle. The midpoints
    are normalised back onto the unit sphere, which is precisely what
    makes the four children unequal in area."""
    a, b, c = tri
    m_ab = _normalise(a + b)
    m_bc = _normalise(b + c)
    m_ca = _normalise(c + a)
    return (
        (a, m_ab, m_ca),
        (m_ab, b, m_bc),
        (m_ca, m_bc, c),
        (m_ab, m_bc, m_ca),
    )


def face_triangle(face: int, ico: Icosahedron = ICOSAHEDRON) -> tuple:
    """The three unit vertices of a base face, as a tuple of arrays."""
    _check_face(face)
    tri = ico.triangle(face)
    return (np.asarray(tri[0], dtype=float),
            np.asarray(tri[1], dtype=float),
            np.asarray(tri[2], dtype=float))


def cell_triangle(face: int, path, ico: Icosahedron = ICOSAHEDRON) -> tuple:
    """The three sphere vertices of the cell reached by ``(face, path)``.

    Descends the refinement one level per path entry, subdividing and
    selecting the chosen child each step."""
    levels = len(tuple(path))
    digits = _check_path(path, levels)
    tri = face_triangle(face, ico)
    for d in digits:
        tri = _subdivide(tri)[d]
    return tri


def cell_area_spherical(face: int, path,
                        ico: Icosahedron = ICOSAHEDRON) -> float:
    """Exact solid angle of one cell, by spherical excess.

    Girard's theorem gives the area of a spherical triangle as its
    angular excess; the Van Oosterom-Strackee half-angle-tangent form
    evaluates it stably from the three unit vertices::

        tan(Omega/2) = |a . (b x c)| / (1 + a.b + b.c + c.a)

    The result is in steradians. It is not ``4*pi / total_cells``: that
    would be the equal-area value the sphere refuses to provide."""
    a, b, c = cell_triangle(face, path, ico)
    a, b, c = _normalise(a), _normalise(b), _normalise(c)
    numerator = abs(float(np.dot(a, np.cross(b, c))))
    denominator = (1.0 + float(np.dot(a, b))
                   + float(np.dot(b, c)) + float(np.dot(c, a)))
    return 2.0 * math.atan2(numerator, denominator)


def _all_cell_triangles(level: int, ico: Icosahedron = ICOSAHEDRON) -> list:
    """Every cell triangle at ``level``, across all twenty faces.

    Feasible only for small ``level``; the count is ``20 * 4**level`` and
    the caller is responsible for keeping it tractable."""
    _check_level(level)
    out = []
    for face in range(FACE_COUNT):
        frontier = [face_triangle(face, ico)]
        for _ in range(level):
            nxt = []
            for tri in frontier:
                nxt.extend(_subdivide(tri))
            frontier = nxt
        out.extend(frontier)
    return out


#: Enumerating cells is exponential, so the area and solid-angle helpers
#: cap the level they will expand. The disciplines they demonstrate --
#: unequal areas, complete solid angle -- are already unmistakable by
#: level four (20 * 4**4 = 5120 cells) and do not change with depth.
MAX_ENUMERABLE_LEVEL = 6


def _check_enumerable(level: int) -> int:
    _check_level(level)
    if level > MAX_ENUMERABLE_LEVEL:
        raise IcosaRefineError(
            f"refused: enumerating every cell at level {level} would "
            f"expand {total_cells(level)} triangles. The area spread and "
            f"the solid-angle completeness are properties of the "
            f"subdivision, not of the depth, and are demonstrated at "
            f"levels up to {MAX_ENUMERABLE_LEVEL}. The exact cell COUNT "
            f"and ADDRESS round trip are available at any level.")
    return level


def cell_areas(level: int, ico: Icosahedron = ICOSAHEDRON) -> list:
    """Solid angles of every cell at ``level`` (small levels only)."""
    _check_enumerable(level)
    out = []
    for a, b, c in _all_cell_triangles(level, ico):
        a, b, c = _normalise(a), _normalise(b), _normalise(c)
        num = abs(float(np.dot(a, np.cross(b, c))))
        den = (1.0 + float(np.dot(a, b)) + float(np.dot(b, c))
               + float(np.dot(c, a)))
        out.append(2.0 * math.atan2(num, den))
    return out


def area_spread(level: int = 2, ico: Icosahedron = ICOSAHEDRON) -> dict:
    """The non-zero range of cell areas at a level.

    At ``level == 0`` the twenty base faces are congruent and the spread
    is zero to floating tolerance; from ``level == 1`` on, midpoint
    re-projection makes the centre cell larger than its corner siblings
    and the spread is strictly positive. That positivity is the whole
    point: it is the quantitative refusal of the equal-area assumption."""
    areas = cell_areas(level, ico)
    lo, hi = min(areas), max(areas)
    mean = sum(areas) / len(areas)
    equal_area_value = 4.0 * math.pi / len(areas)
    return {
        "level": level,
        "cell_count": len(areas),
        "min_area": lo,
        "max_area": hi,
        "mean_area": mean,
        "spread": hi - lo,
        "relative_spread": (hi - lo) / mean if mean else 0.0,
        "equal_area_value": equal_area_value,
        "max_over_min": hi / lo if lo else float("inf"),
        "is_equal_area": (hi - lo) < 1e-12,
        "claim_class": ClaimClass.REPOSITORY_COMPUTATIONAL_RESULT.value,
        "why": (
            "re-projecting edge midpoints onto the sphere enlarges the "
            "central child and shrinks the corner children, so the four "
            "sub-cells of any triangle are unequal in area and the "
            "spread across a level is strictly positive"),
    }


def total_solid_angle(level: int = 2,
                      ico: Icosahedron = ICOSAHEDRON) -> dict:
    """POWER: the cells at a level cover exactly ``4*pi`` steradians.

    However unequal the cells are, they tile the sphere without gap or
    overlap, so their solid angles sum to the full ``4*pi``. This is the
    positive control on the area machinery: it confirms the tessellation
    is complete and that :func:`cell_area_spherical` measures the whole
    sphere rather than a part of it."""
    areas = cell_areas(level, ico)
    total = math.fsum(areas)
    target = 4.0 * math.pi
    return {
        "level": level,
        "cell_count": len(areas),
        "total_solid_angle": total,
        "expected": target,
        "abs_error": abs(total - target),
        "complete": abs(total - target) < 1e-9,
        "tolerance": 1e-9,
        "claim_class": ClaimClass.REPOSITORY_COMPUTATIONAL_RESULT.value,
        "why": (
            "the four children of a triangle exactly tile their parent "
            "and the twenty faces exactly tile the sphere, so the solid "
            "angles sum to 4*pi at every level regardless of how "
            "unequal the individual cells are"),
    }


def refuse_equal_area_assumption(level: int = WORKING_LEVELS,
                                 *_args, **_kwargs) -> None:
    """Refuse to treat quaternary refinement as an equal-area grid.

    The seductive shortcut is to give every cell the weight
    ``4*pi / total_cells`` -- to read cell count as area. On a sphere
    that is wrong: midpoint subdivision with re-projection produces
    unequal cells, and the error is systematic, not noise. It biases any
    density, any average and any coverage statistic computed over the
    grid, understating the crowded corners and overstating the roomy
    centres."""
    demo_level = min(2, MAX_ENUMERABLE_LEVEL)
    spread = area_spread(demo_level)
    raise IcosaRefineError(
        f"refused: quaternary refinement is NOT an equal-area grid. "
        f"Midpoint subdivision re-projects edge midpoints onto the "
        f"sphere, which makes the four children of every triangle "
        f"unequal in area; at level {demo_level} the cell areas already "
        f"range over {spread['spread']:.6g} steradians "
        f"(max/min = {spread['max_over_min']:.4f}), so they are "
        f"demonstrably not the uniform {spread['equal_area_value']:.6g} "
        f"an equal-area assumption would assign. Weighting every cell "
        f"equally, or reading the cell count at level {level} as area, "
        f"biases every density and coverage statistic computed on the "
        f"grid. Use cell_area_spherical for exact per-cell solid angles.")


# =======================================================================
# Fingerprint and report
# =======================================================================

def refine_fingerprint(level: int = 2) -> str:
    """A stable hash over the cell-count facts and a sample area."""
    budget = address_budget(WORKING_LEVELS)
    sample = cell_area_spherical(0, tuple([3] + [0] * (WORKING_LEVELS - 1)))
    parts = (
        str(budget["cells_per_face"]),
        str(budget["total_cells"]),
        str(budget["address_capacity"]),
        f"{sample:.15e}",
    )
    return hashlib.sha256("\x1f".join(parts).encode()).hexdigest()


def icosarefine_report() -> dict:
    demo = min(2, MAX_ENUMERABLE_LEVEL)
    return {
        "what_this_is": (
            "eleven-level quaternary (midpoint) triangular refinement on "
            "the frozen canonical icosahedron, with exact cell counts, an "
            "exact (face, path) address round trip, exact spherical-excess "
            "cell areas that are provably unequal, and a 4*pi "
            "completeness control"),
        "same_icosahedron_as_r11_earthface": assert_same_icosahedron(),
        "address_budget": address_budget(WORKING_LEVELS),
        "cells_per_face_L11": cells_per_face(WORKING_LEVELS),
        "total_cells_L11": total_cells(WORKING_LEVELS),
        "area_spread": area_spread(demo),
        "total_solid_angle": total_solid_angle(demo),
        "fingerprint": refine_fingerprint(),
        "refusals": ["refuse_equal_area_assumption"],
        "claim_class": ClaimClass.REPOSITORY_COMPUTATIONAL_RESULT.value,
        "measured_here": "nothing",
        "physical_validation": PHYSICAL_VALIDATION,
        "verdict": VERDICT,
        "what_this_does_not_say": (
            "It does not say the icosahedron is a feature of any body, "
            "and it does not say the cells correspond to anything "
            "physical. It says the refinement geometry is exact: each "
            "level quadruples the cells, eleven levels give exactly "
            "4**11 = 4_194_304 per face and 20 * 4**11 = 83_886_080 "
            "over the solid, and that fits the twenty-seven-bit address "
            "budget with room to spare. Because the subdivision projects "
            "edge midpoints onto the sphere, the cells are UNEQUAL in "
            "area -- it is not an equal-area grid, and treating it as "
            "one is a real error that biases every statistic computed on "
            "it. The cells nonetheless tile the sphere completely, their "
            "solid angles summing to 4*pi. The solid is the very object "
            "frozen in r11.earthface, imported and not rebuilt. Nothing "
            "here is measured and no physical validation is claimed."),
    }


__all__ = [
    "ClaimClass", "IcosaRefineError", "VERDICT",
    "ICOSAHEDRON", "FACE_COUNT", "CHILDREN_PER_TRIANGLE", "WORKING_LEVELS",
    "FACE_BITS", "PATH_BITS", "ADDRESS_BITS", "MAX_ENUMERABLE_LEVEL",
    "assert_same_icosahedron", "cells_per_face", "total_cells",
    "address_budget", "cell_address", "address_to_cell",
    "face_triangle", "cell_triangle", "cell_area_spherical",
    "cell_areas", "area_spread", "total_solid_angle",
    "refuse_equal_area_assumption", "refine_fingerprint",
    "icosarefine_report",
]
