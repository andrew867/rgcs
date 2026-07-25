"""P07 — South-Up basis and viewpoint-safe handedness.

The locked orientation is **South-Up**, with **positive rotation clockwise when
viewed externally from above Antarctica**; the *same* physical rotation appears
**anticlockwise** from the North-down viewpoint (Locked Decisions §8–§10). The
classic failure mode is a sign flip: "clockwise" is meaningless until you say
*from which side you are looking*. This module makes the viewpoint an explicit,
mandatory part of every rotation so a sign is never ambiguous.

Design:

* A rotation is requested with an ``angle``, a ``sense`` (clockwise or
  anticlockwise), and a ``viewpoint``. The **same physical matrix** results
  from equivalent descriptions — ``(θ, CLOCKWISE, ANTARCTIC_EXTERNAL)`` equals
  ``(θ, ANTICLOCKWISE, NORTH_DOWN)`` — which is exactly the locked equivalence.
* A rotation requested **without a declared viewpoint is refused.**
* Given a physical matrix, :func:`describe_sense` reports the opposite sense
  label from each viewpoint, so a round-trip through both viewpoints is
  consistent.

Pure ``DERIVED_MATHEMATICS``: rotation arithmetic about the body axis. Nothing
measured, nothing physical claimed. Every value passed in.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

import numpy as np

from cwatlas.r1082 import claims

#: The locked orientation constants (schema consts).
POLE = "SOUTH_UP"
POSITIVE_ROTATION = "CLOCKWISE"
POSITIVE_ROTATION_VIEWPOINT = "EXTERNAL_ABOVE_ANTARCTICA"


class SouthUpError(ValueError):
    """Raised on an ambiguous rotation (e.g. no declared viewpoint)."""


class Viewpoint(Enum):
    """Which side of the body axis the observer looks from."""

    #: External, above Antarctica, looking toward the geocentre (the locked
    #: positive-rotation viewpoint). Positive rotation is CLOCKWISE here.
    ANTARCTIC_EXTERNAL = "EXTERNAL_ABOVE_ANTARCTICA"
    #: The opposite view, from above the North pole looking down. The same
    #: rotation appears ANTICLOCKWISE here.
    NORTH_DOWN = "NORTH_DOWN"


class Sense(Enum):
    """A rotation sense, only meaningful once a viewpoint is declared."""

    CLOCKWISE = "CLOCKWISE"
    ANTICLOCKWISE = "ANTICLOCKWISE"


def _rot_z(angle_rad: float) -> np.ndarray:
    """Standard right-handed rotation about +Z (the mean rotation axis)."""
    c, s = math.cos(angle_rad), math.sin(angle_rad)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]], dtype=float)


def _positive_from_antarctic(sense: Sense, viewpoint: Viewpoint) -> bool:
    """Whether ``(sense, viewpoint)`` is the locked positive (Rz(+θ)) sense.

    Rz(+θ) carries +X toward +Y. Viewed from the Antarctic external side (the
    -Z hemisphere, looking toward the geocentre) that appears CLOCKWISE; viewed
    from North-down (+Z, looking down) it appears ANTICLOCKWISE. So the locked
    positive matrix is produced by CLOCKWISE@ANTARCTIC or ANTICLOCKWISE@NORTH.
    """
    if viewpoint is Viewpoint.ANTARCTIC_EXTERNAL:
        return sense is Sense.CLOCKWISE
    return sense is Sense.ANTICLOCKWISE


def rotation_matrix(angle_deg: float, sense: Sense,
                    viewpoint: Viewpoint) -> np.ndarray:
    """The physical rotation matrix for a viewpoint-declared request.

    ``viewpoint`` is mandatory — a rotation without a declared viewpoint is
    refused (its sign would be ambiguous). Equivalent descriptions of the same
    physical rotation return the same matrix.
    """
    if viewpoint is None:
        refuse_rotation_without_viewpoint()
    if not isinstance(viewpoint, Viewpoint):
        raise SouthUpError(f"viewpoint must be a Viewpoint, got {viewpoint!r}.")
    if not isinstance(sense, Sense):
        raise SouthUpError(f"sense must be a Sense, got {sense!r}.")
    if not math.isfinite(angle_deg):
        raise SouthUpError("angle_deg must be finite.")
    signed = angle_deg if _positive_from_antarctic(sense, viewpoint) else -angle_deg
    return _rot_z(math.radians(signed))


def describe_sense(angle_deg: float, viewpoint: Viewpoint) -> Sense:
    """Name the sense of the locked *positive* rotation from ``viewpoint``.

    A positive locked rotation (Rz(+θ)) is CLOCKWISE from the Antarctic
    external viewpoint and ANTICLOCKWISE from North-down — the two are always
    opposite, which is the whole point of declaring the viewpoint.
    """
    if viewpoint is None:
        refuse_rotation_without_viewpoint()
    if not isinstance(viewpoint, Viewpoint):
        raise SouthUpError(f"viewpoint must be a Viewpoint, got {viewpoint!r}.")
    positive = angle_deg >= 0.0
    if viewpoint is Viewpoint.ANTARCTIC_EXTERNAL:
        return Sense.CLOCKWISE if positive else Sense.ANTICLOCKWISE
    return Sense.ANTICLOCKWISE if positive else Sense.CLOCKWISE


def refuse_rotation_without_viewpoint(*_a, **_k) -> None:
    """A rotation applied without a declared viewpoint is refused."""
    raise SouthUpError(
        "refused: a rotation sign is ambiguous without a declared viewpoint. "
        "Clockwise from above Antarctica is anticlockwise from North-down. "
        "Declare a Viewpoint (ANTARCTIC_EXTERNAL or NORTH_DOWN) so the sign is "
        "never ambiguous.")


@dataclass(frozen=True)
class TangentBasis:
    """An orthonormal, right-handed local basis (east, north, up) at a point.

    Columns are unit vectors; ``matrix`` is the 3x3 whose columns are
    (east, north, up). It is verified orthonormal with determinant +1.
    """

    matrix: np.ndarray

    def is_orthonormal(self, tol: float = 1e-9) -> bool:
        m = self.matrix
        return bool(np.allclose(m.T @ m, np.eye(3), atol=tol))

    def determinant(self) -> float:
        return float(np.linalg.det(self.matrix))


def tangent_basis(lat_deg: float, lon_deg: float) -> TangentBasis:
    """Build the local ENU tangent basis at ``(lat, lon)`` on the sphere.

    Used to construct the Wilkes/SAA tangent frame; the basis is orthonormal
    with determinant +1 (a right-handed frame), which the caller verifies.
    """
    lat, lon = math.radians(lat_deg), math.radians(lon_deg)
    sin_lat, cos_lat = math.sin(lat), math.cos(lat)
    sin_lon, cos_lon = math.sin(lon), math.cos(lon)
    up = np.array([cos_lat * cos_lon, cos_lat * sin_lon, sin_lat])
    east = np.array([-sin_lon, cos_lon, 0.0])
    north = np.array([-sin_lat * cos_lon, -sin_lat * sin_lon, cos_lat])
    m = np.column_stack([east, north, up])
    return TangentBasis(matrix=m)


def south_up_basis() -> np.ndarray:
    """The global South-Up orientation matrix.

    South-Up flips the pole so the body's South is "up". It is a proper
    rotation (determinant +1): a 180-degree turn about the +X (prime-meridian)
    axis, which maps +Z (North) to -Z and keeps handedness.
    """
    return np.array([[1.0, 0.0, 0.0],
                     [0.0, -1.0, 0.0],
                     [0.0, 0.0, -1.0]], dtype=float)


def southup_report() -> dict:
    """P07 declaration receipt. Viewpoint mandatory; sign never ambiguous."""
    return {
        "phase_id": "P07",
        "tranche": "T02",
        "what_this_is": (
            "the locked South-Up orientation with viewpoint-safe handedness: "
            "positive rotation is clockwise from the Antarctic external "
            "viewpoint and the same rotation is anticlockwise from North-down; "
            "a rotation without a declared viewpoint is refused."),
        "pole": POLE,
        "positive_rotation": POSITIVE_ROTATION,
        "positive_rotation_viewpoint": POSITIVE_ROTATION_VIEWPOINT,
        "viewpoints": [v.value for v in Viewpoint],
        "senses": [s.value for s in Sense],
        "south_up_basis_determinant": float(np.linalg.det(south_up_basis())),
        "rotation_without_viewpoint": "REFUSED",
        "evidence_class": claims.EvidenceClass.DERIVED_MATHEMATICS.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
        "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
        "verdict": "SOUTH_UP_VIEWPOINT_SAFE_HANDEDNESS_NO_AMBIGUOUS_SIGN",
        "what_this_does_not_say": (
            "The orientation is a declared operator convention realized as "
            "rotation arithmetic; it validates nothing physical."),
    }
