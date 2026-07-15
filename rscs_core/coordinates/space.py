"""Spatial and orientation coordinates: RSCS-C.1 (space) and RSCS-C.8 (frame).

RSCS-C.1 SpatialCoordinate: a point in Euclidean 3-space E^3, unit mm, in a
named reference frame. The v2 crystal-axis frame (NOTATION_AND_UNITS §2.6,
x from the wide apex) is one chart of this coordinate.

RSCS-C.8 OrientationFrame: an element of SO(3) x {+/-} (rotation plus
handedness) that names a reference frame and relates it to others. The v2
planar scale-rotation eigenstructure (RGCS-M.32, lambda_s = -a + i) is a
chart of the rotation part; adapted math only (EP-08-01), no visual-
perception import (EXCLUSION_MATRIX SRC-3-08).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ClassVar

import numpy as np

from ._base import RSCSCoordinate, require_finite_array

__all__ = ["SpatialCoordinate", "OrientationFrame"]


@dataclass(frozen=True)
class SpatialCoordinate(RSCSCoordinate):
    """RSCS-C.1. A point (x, y, z) in mm within a named frame."""

    registry_id: ClassVar[str] = "RSCS-C.1"

    xyz_mm: tuple[float, float, float]
    frame: str = "crystal_axis"

    def __post_init__(self) -> None:
        object.__setattr__(self, "xyz_mm", self._seq("xyz_mm", self.xyz_mm, 3))
        if not isinstance(self.frame, str) or not self.frame:
            raise ValueError("frame must be a non-empty string")

    @property
    def vector(self) -> np.ndarray:
        return np.asarray(self.xyz_mm, dtype=float)

    def components(self) -> dict[str, Any]:
        return {"xyz_mm": self.vector, "frame": self.frame}


def _is_rotation(mat: np.ndarray, atol: float = 1e-9) -> bool:
    """True iff mat is a proper/improper orthogonal 3x3 (R^T R = I)."""
    return (mat.shape == (3, 3)
            and np.allclose(mat.T @ mat, np.eye(3), atol=atol)
            and abs(abs(float(np.linalg.det(mat))) - 1.0) <= 1e-6)


@dataclass(frozen=True)
class OrientationFrame(RSCSCoordinate):
    """RSCS-C.8. A reference frame: rotation in SO(3) plus handedness.

    ``rotation`` is a 3x3 orthogonal matrix; ``handedness`` is +1 (right) or
    -1 (left). ``name`` labels the frame for frame-identity checks in
    transforms (RSCS-O.1).
    """

    registry_id: ClassVar[str] = "RSCS-C.8"

    rotation: np.ndarray = field(default_factory=lambda: np.eye(3))
    handedness: int = 1
    name: str = "world"

    def __post_init__(self) -> None:
        rot = require_finite_array("rotation", self.rotation, ndim=2,
                                   shape=(3, 3))
        if not _is_rotation(rot):
            raise ValueError("rotation must be an orthogonal 3x3 matrix "
                             "(R^T R = I, |det| = 1)")
        object.__setattr__(self, "rotation", rot)
        if self.handedness not in (1, -1):
            raise ValueError("handedness must be +1 or -1")
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("name must be a non-empty string")

    @classmethod
    def identity(cls, name: str = "world") -> "OrientationFrame":
        return cls(np.eye(3), 1, name)

    def compose(self, other: "OrientationFrame") -> "OrientationFrame":
        """Compose two frames: rotation product, handedness product."""
        return OrientationFrame(self.rotation @ other.rotation,
                                self.handedness * other.handedness,
                                f"{self.name}o{other.name}")

    def inverse(self) -> "OrientationFrame":
        return OrientationFrame(self.rotation.T, self.handedness,
                                f"{self.name}^-1")

    def components(self) -> dict[str, Any]:
        return {"rotation": self.rotation, "handedness": self.handedness,
                "name": self.name}
