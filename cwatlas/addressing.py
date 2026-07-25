"""P25/P26 — Face selection and recursive eight-way icosahedral addressing.

The forward half of the CW-HCM-ICO-1 addressing codec:

* **P25 — face selection with deterministic tie-breaking.** A unit direction
  exits the spherical icosahedron through exactly one of the 20 faces. A
  direction that lands *exactly* on a shared edge (or a vertex) is equidistant
  from two (or more) face centres; that ambiguity is resolved, by rule, to the
  **lowest-id adjacent face**, so the result is single-valued and identical
  across runs and platforms. The ambiguity is not hidden: the returned
  :class:`FaceSelection` records that the point was on a boundary and lists the
  tied faces.

* **P26 — recursive one-to-eight refinement.** Descending the selected face by
  the octal refinement of :mod:`cwatlas.subdivision` produces a path of octal
  digits ``0..7`` of a requested depth ``D``. A twelve-deep path packs into 36
  bits and aligns with the ``CW-PACK40-1`` path field. The forward map
  ``point -> (face, octal path)`` is deterministic and stable, and the path
  decodes back to the spherical cell it names.

MATHEMATICAL_TRANSLATION / SOFTWARE level. A face id, an octal digit, and a
path are cell selectors in a synthetic tessellation, not places. This module
asserts nothing geographic about any source vector. See :mod:`cwatlas.claims`.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from cwatlas import claims
from cwatlas.icosahedron import Icosahedron, build_icosahedron
from cwatlas.subdivision import (
    CHILDREN_PER_NODE,
    MAX_CHILD_INDEX,
    SphericalTriangle,
    child,
)
from cwatlas.subdivision import _QUADRANTS  # reuse the octal child geometry

#: Codec identity for the icosahedral addressing codec.
CODEC_ID = "CW-HCM-ICO-1"
CODEC_VERSION = "1.0.0"

#: A twelve-deep octal path is 12 * 3 = 36 bits, the ``CW-PACK40-1`` path
#: field. This is the canonical depth the packer aligns with.
CWPACK40_DEPTH = 12
BITS_PER_DIGIT = 3

#: Deepest refinement the reused subdivision construction can build before its
#: absolute collinearity guard (:class:`SphericalTriangle.of`) refuses the
#: vanishingly small child cell. The canonical CW-PACK40 depth (12) sits safely
#: inside this floor; deeper requests are refused cleanly rather than leaking a
#: construction error.
MAX_REFINEMENT_DEPTH = 13

#: Tolerance on the cosine-to-centre used to declare a face tie (a point on a
#: shared edge or vertex). The gap between adjacent face centres is large, so
#: a tight tolerance only fires on genuine boundary points.
_TIE_TOL = 1e-12

#: A barycentric coordinate below this is treated as "outside the cell". These
#: coordinates are dimensionless (fractions of a cell), so this tolerance is
#: cell-size independent and holds at every refinement depth.
_INSIDE_TOL = 1e-9


class AddressError(ValueError):
    """Raised on an invalid direction, depth, face id, or path digit."""


def _unit(point) -> np.ndarray:
    """Validate and normalise a direction; refuse degenerate input."""
    p = np.asarray(point, dtype=np.float64).reshape(-1)
    if p.shape != (3,):
        raise AddressError("point must be a 3-vector")
    if not np.all(np.isfinite(p)):
        raise AddressError("point must be finite")
    norm = float(np.linalg.norm(p))
    if norm < 1e-15:
        raise AddressError("point must be a non-zero direction on the sphere")
    return p / norm


def barycentric(tri: SphericalTriangle, point) -> tuple[float, float, float]:
    """Scale-invariant barycentric ``(u, v, w)`` of ``point`` on ``tri``.

    Equivalent to :func:`cwatlas.subdivision.to_barycentric` — radial
    projection onto the triangle plane, then affine barycentric — but the
    degeneracy guard is *relative* (``det == |normal|**2 > 0``) instead of an
    absolute threshold. Because barycentric coordinates are dimensionless, this
    stays exact for the vanishingly small cells at CW-PACK40 depth 12, where the
    absolute-tolerance guard would otherwise refuse a perfectly valid cell.
    """
    p = _unit(point)
    a, b, c = tri.a, tri.b, tri.c
    v0, v1 = b - a, c - a
    normal = np.cross(v0, v1)
    nn = float(normal @ normal)
    if nn <= 0.0:
        raise AddressError("degenerate cell: corners are collinear")
    denom = float(normal @ p)
    # Relative grazing check: p must not be (near) parallel to the cell plane.
    if denom * denom <= nn * 1e-30:
        raise AddressError(
            "refused: direction does not radially intersect the cell plane")
    t = float(normal @ a) / denom
    v2 = t * p - a
    d00 = float(v0 @ v0)
    d01 = float(v0 @ v1)
    d11 = float(v1 @ v1)
    d20 = float(v2 @ v0)
    d21 = float(v2 @ v1)
    det = d00 * d11 - d01 * d01  # == nn > 0
    v = (d11 * d20 - d01 * d21) / det
    w = (d00 * d21 - d01 * d20) / det
    u = 1.0 - v - w
    return (u, v, w)


def locate_child(tri: SphericalTriangle, point) -> int:
    """Octal child index ``0..7`` of the sub-cell of ``tri`` containing ``point``.

    Same quadrant-then-half rule as :func:`cwatlas.subdivision.child_index`,
    but built on the scale-invariant :func:`barycentric` so it is stable at any
    depth. A point outside the parent cell is a refusal.
    """
    u, v, w = barycentric(tri, point)
    if min(u, v, w) < -_INSIDE_TOL:
        raise AddressError(
            f"refused: point is outside the cell (bary={u:.6g},{v:.6g},{w:.6g})")
    if u >= 0.5:
        quad = 0
    elif v >= 0.5:
        quad = 1
    elif w >= 0.5:
        quad = 2
    else:
        quad = 3
    pb = np.array([u, v, w], dtype=np.float64)
    P, Q, R = (np.array(x, dtype=np.float64) for x in _QUADRANTS[quad])
    mat = np.array([Q - P, R - P], dtype=np.float64).T  # (3, 2)
    lq, lr = np.linalg.lstsq(mat, pb - P, rcond=None)[0]
    half = 0 if lq >= lr else 1
    return quad * 2 + half


@dataclass(frozen=True)
class FaceSelection:
    """The face a direction selects, plus the tie-breaking provenance.

    Attributes
    ----------
    face_id:
        The selected face id ``0..19``. On a boundary this is the lowest id
        among ``tied_face_ids`` (the deterministic tie-break rule).
    on_boundary:
        ``True`` when the direction was equidistant (within tolerance) from
        more than one face centre, i.e. it lay on a shared edge or vertex.
    tied_face_ids:
        The face ids that were equidistant, ascending. Length 1 for an
        interior point, 2 for an edge, up to 5 for a vertex.
    cos_to_centre:
        The (maximal) cosine between the direction and the winning face
        centre; a bookkeeping quantity, not a distance claim.
    """

    face_id: int
    on_boundary: bool
    tied_face_ids: tuple[int, ...]
    cos_to_centre: float


def select_face(ico: Icosahedron, point) -> FaceSelection:
    """Select the icosahedral face for ``point`` with deterministic tie-break.

    The radial ray through ``point`` exits the icosahedron through the face
    whose unit centre direction is closest to ``point`` (nearest-centre ==
    spherical-triangle membership, the Voronoi boundary being the shared edge
    arc). If two or more centres are equidistant within ``_TIE_TOL`` — the
    point lies exactly on a shared edge or a vertex — the tie is resolved to
    the **lowest-id** adjacent face. The result is therefore single-valued and
    reproducible, and the ambiguity is reported rather than hidden.
    """
    p = _unit(point)
    dots = ico.face_normals @ p
    max_dot = float(dots.max())
    tied = tuple(int(i) for i in np.nonzero(dots >= max_dot - _TIE_TOL)[0])
    # np.nonzero returns ascending indices, so tied[0] is the lowest id.
    return FaceSelection(
        face_id=tied[0],
        on_boundary=len(tied) > 1,
        tied_face_ids=tied,
        cos_to_centre=max_dot,
    )


def face_triangle(ico: Icosahedron, face_id: int) -> SphericalTriangle:
    """The spherical triangle of a face, corners in stable ``(i<j<k)`` order."""
    if not isinstance(face_id, int) or isinstance(face_id, bool):
        raise AddressError("face_id must be a plain int")
    if not 0 <= face_id < len(ico.faces):
        raise AddressError(f"face_id out of range 0..{len(ico.faces) - 1}: "
                           f"{face_id!r}")
    i, j, k = ico.faces[face_id]
    return SphericalTriangle.of(ico.vertices[i], ico.vertices[j],
                                ico.vertices[k])


@dataclass(frozen=True)
class Address:
    """An icosahedral address: a face id and an octal refinement path.

    ``path`` is a tuple of octal digits ``0..7`` of length ``depth``; the
    empty path addresses the whole face.
    """

    face_id: int
    path: tuple[int, ...]

    @property
    def depth(self) -> int:
        return len(self.path)

    def octal_string(self) -> str:
        """The path as a string of octal digits (empty string at depth 0)."""
        return "".join(str(d) for d in self.path)

    def packed_bits(self) -> tuple[int, int]:
        """Return ``(value, bit_length)`` packing the path 3 bits per digit.

        A depth-12 path yields a 36-bit value, the ``CW-PACK40-1`` path field.
        """
        value = 0
        for d in self.path:
            value = (value << BITS_PER_DIGIT) | d
        return value, BITS_PER_DIGIT * len(self.path)


def _validate_depth(depth: int) -> None:
    if not isinstance(depth, int) or isinstance(depth, bool):
        raise AddressError("depth must be a plain int")
    if depth < 0:
        raise AddressError(f"depth must be non-negative, got {depth!r}")
    if depth > MAX_REFINEMENT_DEPTH:
        raise AddressError(
            f"depth {depth} exceeds MAX_REFINEMENT_DEPTH "
            f"({MAX_REFINEMENT_DEPTH}); deeper cells are below the reused "
            f"subdivision construction's numerical floor")


def encode_path(ico: Icosahedron, point, depth: int) -> Address:
    """Encode a direction into ``(face, octal path)`` at the requested depth.

    Selects the face (P25), then descends the one-to-eight refinement ``depth``
    times, recording the octal child index at each level (P26). Deterministic
    and stable: the same direction and depth always give the same address.
    """
    _validate_depth(depth)
    face_id = select_face(ico, point).face_id
    tri = face_triangle(ico, face_id)
    p = _unit(point)
    path: list[int] = []
    for _ in range(depth):
        idx = locate_child(tri, p)
        path.append(idx)
        tri = child(tri, idx)
    return Address(face_id=face_id, path=tuple(path))


def _validate_path(path) -> tuple[int, ...]:
    out: list[int] = []
    for d in tuple(path):
        if not isinstance(d, (int, np.integer)) or isinstance(d, bool):
            raise AddressError(f"path digit must be an int, got {d!r}")
        d = int(d)
        if not 0 <= d <= MAX_CHILD_INDEX:
            raise AddressError(
                f"path digit out of range 0..{MAX_CHILD_INDEX}: {d!r}")
        out.append(d)
    return tuple(out)


def path_cell(ico: Icosahedron, face_id: int, path) -> SphericalTriangle:
    """Decode ``(face, octal path)`` back to the spherical cell it names.

    The exact inverse of the descent in :func:`encode_path`: starting from the
    face triangle, apply each octal child selection in turn.
    """
    tri = face_triangle(ico, face_id)
    for d in _validate_path(path):
        tri = child(tri, d)
    return tri


def addressing_report() -> dict:
    """Governance report: what this module is and, emphatically, is not."""
    ico = build_icosahedron()
    return {
        "phase": "P25/P26",
        "what_this_is": (
            "deterministic icosahedral face selection with lowest-id "
            "edge/vertex tie-breaking, plus recursive one-to-eight octal "
            "refinement producing a stable (face, octal path) address"),
        "codec_id": CODEC_ID,
        "codec_version": CODEC_VERSION,
        "num_faces": len(ico.faces),
        "children_per_node": CHILDREN_PER_NODE,
        "tie_break_rule": "LOWEST_ID_ADJACENT_FACE",
        "cwpack40_depth": CWPACK40_DEPTH,
        "cwpack40_path_bits": BITS_PER_DIGIT * CWPACK40_DEPTH,
        "max_refinement_depth": MAX_REFINEMENT_DEPTH,
        "claim_class": claims.ClaimClass.MATHEMATICAL_TRANSLATION.value,
        "level": "SOFTWARE",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "CW_ATLAS_ADDRESSING_DETERMINISTIC_STABLE_NO_GEO_CLAIM",
        "what_this_does_not_say": (
            "A face id and an octal path are selectors in a synthetic "
            "tessellation, not a place. No geographic or extraterrestrial "
            "meaning is asserted about any source vector."),
    }
