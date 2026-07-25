"""P27/P28 — Inverse localization and continuous residual coordinates.

The inverse half of the CW-HCM-ICO-1 addressing codec, and its reversible core:

* **P27 — inverse cell centroid and barycentric localization.** An address
  ``(face, octal path)`` names a spherical cell, not a point. This returns the
  cell itself (its three corners), its centroid direction, and its size,
  refusing to invent point precision the address does not carry. Refining a
  direction and then localizing returns a cell that *contains* that direction
  (POWER), and the cell's characteristic size shrinks by ~1/2 per depth.

* **P28 — continuous local residual coordinates.** To make the address exact,
  the terminal cell carries an optional continuous residual: the point's
  barycentric offset from the cell centroid. ``point = cell_centroid (+)
  residual``. With the residual, ``forward`` then ``inverse`` reconstructs the
  original direction to full floating-point precision — the reversible
  CW-HCM-ICO core (``CANONICAL_ROUND_TRIP``).

A round-trip is a verified property of the codec. It is not evidence that any
operator-reported source vector identifies a real location.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from cwatlas import claims
from cwatlas.addressing import (
    Address,
    AddressError,
    barycentric,
    encode_path,
    face_triangle,  # noqa: F401  (re-exported convenience)
    path_cell,
)
from cwatlas.icosahedron import Icosahedron
from cwatlas.subdivision import SphericalTriangle, from_barycentric

CODEC_ID = "CW-HCM-ICO-1"
CODEC_VERSION = "1.0.0"

#: The barycentric coordinate of a triangle's centroid.
CENTROID_BARY = (1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0)

#: A point is deemed inside a cell if no barycentric coordinate is more
#: negative than this (matches the subdivision inside-tolerance).
_INSIDE_TOL = 1e-9


def cell_centroid(cell: SphericalTriangle) -> np.ndarray:
    """Unit direction of the cell centroid (mean of corners, re-normalised)."""
    c = (cell.a + cell.b + cell.c) / 3.0
    n = float(np.linalg.norm(c))
    if n < 1e-15:
        raise AddressError("degenerate cell: centroid collapsed to origin")
    return c / n


def cell_diameter(cell: SphericalTriangle) -> float:
    """Largest chord between the cell corners; the cell's characteristic size.

    Under one-to-eight refinement this halves per depth: the four midpoint
    quadrants have half-length edges, and the median bisection of each keeps
    the quadrant's longest edge, so the diameter is set by that half-length.
    """
    a, b, c = cell.a, cell.b, cell.c
    return max(
        float(np.linalg.norm(a - b)),
        float(np.linalg.norm(b - c)),
        float(np.linalg.norm(c - a)),
    )


@dataclass(frozen=True)
class CellLocalization:
    """The result of localizing an address to a cell (P27).

    Attributes
    ----------
    face_id, path:
        The address that was localized.
    cell:
        The spherical triangle the address names.
    centroid:
        Unit direction of the cell centroid — the address's representative
        direction, not a decoded point.
    diameter:
        The cell's characteristic size (largest corner chord).
    """

    face_id: int
    path: tuple[int, ...]
    cell: SphericalTriangle
    centroid: np.ndarray
    diameter: float

    def contains(self, point) -> bool:
        """Whether ``point`` lies inside this cell (within tolerance)."""
        u, v, w = barycentric(self.cell, point)
        return min(u, v, w) >= -_INSIDE_TOL


def localize_cell(ico: Icosahedron, face_id: int, path) -> CellLocalization:
    """Localize an address ``(face, octal path)`` to its spherical cell (P27).

    Returns the cell, its centroid direction, and its diameter — the region
    the address determines, without inventing sub-cell precision.
    """
    cell = path_cell(ico, face_id, path)
    return CellLocalization(
        face_id=face_id,
        path=tuple(int(d) for d in path),
        cell=cell,
        centroid=cell_centroid(cell),
        diameter=cell_diameter(cell),
    )


def refine_then_localize(
    ico: Icosahedron, point, depth: int,
) -> CellLocalization:
    """Encode a direction to depth ``depth`` then localize (P27, POWER).

    The returned cell contains the original direction: ``result.contains(point)``
    is ``True``.
    """
    addr = encode_path(ico, point, depth)
    return localize_cell(ico, addr.face_id, addr.path)


@dataclass(frozen=True)
class ExactAddress:
    """An exact icosahedral address: an :class:`Address` plus a residual (P28).

    ``residual`` is the barycentric offset of the point from the terminal
    cell's centroid; its three components sum to zero (both the point's
    barycentric and the centroid's sum to one). Together with the address it
    reconstructs the original direction exactly.
    """

    face_id: int
    path: tuple[int, ...]
    residual: tuple[float, float, float]

    @property
    def address(self) -> Address:
        return Address(face_id=self.face_id, path=self.path)

    @property
    def depth(self) -> int:
        return len(self.path)


def forward(ico: Icosahedron, point, depth: int) -> ExactAddress:
    """Direction -> exact address ``(face, path, residual)`` (P28 forward).

    The reversible CW-HCM-ICO core: the discrete address places the point in a
    terminal cell, and the continuous residual pins it exactly within that
    cell. Inverting with :func:`inverse` recovers the direction to full
    precision.
    """
    addr = encode_path(ico, point, depth)
    cell = path_cell(ico, addr.face_id, addr.path)
    u, v, w = barycentric(cell, point)
    residual = (u - CENTROID_BARY[0],
                v - CENTROID_BARY[1],
                w - CENTROID_BARY[2])
    return ExactAddress(face_id=addr.face_id, path=addr.path, residual=residual)


def inverse(ico: Icosahedron, exact: ExactAddress) -> np.ndarray:
    """Exact address -> unit direction (P28 inverse).

    Reconstructs the terminal cell from the address, adds the residual back
    onto the centroid barycentric, and projects to the sphere.
    """
    if not isinstance(exact, ExactAddress):
        raise AddressError("inverse expects an ExactAddress")
    r = np.asarray(exact.residual, dtype=np.float64).reshape(-1)
    if r.shape != (3,) or not np.all(np.isfinite(r)):
        raise AddressError("residual must be a finite 3-vector")
    cell = path_cell(ico, exact.face_id, exact.path)
    bary = (CENTROID_BARY[0] + r[0],
            CENTROID_BARY[1] + r[1],
            CENTROID_BARY[2] + r[2])
    return from_barycentric(cell, bary)


def localize_report() -> dict:
    """Governance report for the inverse / residual core."""
    return {
        "phase": "P27/P28",
        "what_this_is": (
            "inverse localization of an icosahedral address to its spherical "
            "cell (centroid, corners, diameter) plus continuous residual "
            "coordinates giving an exact, reversible point round-trip"),
        "codec_id": CODEC_ID,
        "codec_version": CODEC_VERSION,
        "residual_convention": "BARYCENTRIC_OFFSET_FROM_TERMINAL_CELL_CENTROID",
        "diameter_shrink_per_depth": "~0.5",
        "claim_class": claims.ClaimClass.CANONICAL_ROUND_TRIP.value,
        "level": "SOFTWARE",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "round_trip_tolerance": 1e-9,
        "verdict": "CW_ATLAS_LOCALIZE_REVERSIBLE_RESIDUAL_ROUND_TRIP",
        "what_this_does_not_say": (
            "An exact canonical round-trip is a verified property of the "
            "codec, not evidence that any operator-reported source vector "
            "identifies a real location. A cell centroid is a representative "
            "of a synthetic cell, not a decoded destination."),
    }
