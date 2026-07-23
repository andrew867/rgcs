"""P06 — root frames, and the refusal to accept an underdetermined one.

The Tier-A instruction is that Earth-to-Moon or Earth-to-Mars addresses
must be built on **calculated roots**, not on latitude and longitude.
Lat/lon, elevation, and ephemerides are *calibration observations*; the
address frame is a root with a declared orientation, epoch, handedness,
scale, and uncertainty.

The one piece of mathematics that keeps this honest is
roll-identifiability. **A single direction does not determine a frame.**
Point "primary axis toward the Sun" and the frame can still spin freely
about that axis -- one degree of freedom, the roll, is unfixed. So a
root built from one direction is ``ROOT_UNDERDETERMINED`` and is
refused. A frame needs a primary direction *and* a second, non-parallel
direction; from those two the full orientation (a quaternion) is
determined by Gram-Schmidt, and this module builds and round-trips it
exactly enough to verify.

Nothing here is a physical claim. A root frame is a coordinate
convention with its uncertainty attached; declaring one does not reach,
actuate, or measure anything.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


class RootUnderdetermined(ValueError):
    """Raised when a frame is built from too little to fix its roll."""


class RootError(ValueError):
    """Raised on an otherwise malformed root."""


def _unit(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    if n == 0:
        raise RootError("zero-length direction")
    return v / n


def orientation_from_two_directions(primary: np.ndarray,
                                    secondary: np.ndarray) -> np.ndarray:
    """A rotation matrix from two non-parallel directions.

    primary -> x axis; the component of secondary orthogonal to primary
    -> y axis; z = x cross y. Refuses parallel inputs (they leave roll
    unfixed, which is the whole point).
    """
    x = _unit(np.asarray(primary, float))
    s = _unit(np.asarray(secondary, float))
    if abs(np.dot(x, s)) > 1 - 1e-9:
        raise RootUnderdetermined(
            "primary and secondary directions are parallel, so the roll "
            "about the primary axis is unfixed. Two non-parallel "
            "directions are required to determine a frame.")
    y = _unit(s - np.dot(s, x) * x)
    z = np.cross(x, y)
    return np.column_stack([x, y, z])


def matrix_to_quaternion(R: np.ndarray) -> np.ndarray:
    """Rotation matrix -> unit quaternion (w, x, y, z)."""
    t = np.trace(R)
    if t > 0:
        w = np.sqrt(1 + t) / 2
        x = (R[2, 1] - R[1, 2]) / (4 * w)
        y = (R[0, 2] - R[2, 0]) / (4 * w)
        z = (R[1, 0] - R[0, 1]) / (4 * w)
    else:
        i = int(np.argmax([R[0, 0], R[1, 1], R[2, 2]]))
        j, k = (i + 1) % 3, (i + 2) % 3
        r = np.sqrt(1 + R[i, i] - R[j, j] - R[k, k])
        q = np.zeros(4)
        q[i + 1] = r / 2
        q[j + 1] = (R[j, i] + R[i, j]) / (2 * r)
        q[k + 1] = (R[k, i] + R[i, k]) / (2 * r)
        q[0] = (R[k, j] - R[j, k]) / (2 * r)
        w, x, y, z = q
    v = np.array([w, x, y, z])
    return v / np.linalg.norm(v)


def quaternion_to_matrix(q: np.ndarray) -> np.ndarray:
    w, x, y, z = q / np.linalg.norm(q)
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ])


@dataclass(frozen=True)
class RootFrame:
    """A calculated root. Orientation must be fully determined."""

    root_id: str
    domain: str                  # UNIVERSAL | SOLAR | EARTH_MOON | ...
    body: str
    parent_root: str | None
    epoch: str
    primary_direction: tuple
    secondary_direction: tuple | None
    handedness: str              # RIGHT | LEFT
    centre: tuple
    scale: float
    derivation: str              # CALCULATED | CALIBRATION_OBSERVATION
    source_authority: str
    evidence_status: str
    prospective: bool = False

    def __post_init__(self) -> None:
        if self.secondary_direction is None:
            raise RootUnderdetermined(
                f"{self.root_id}: no secondary direction, so roll is "
                f"unfixed. A single direction cannot determine a frame.")
        if self.handedness not in ("RIGHT", "LEFT"):
            raise RootError("handedness must be RIGHT or LEFT")
        if self.scale <= 0:
            raise RootError("scale must be positive")
        if not self.epoch:
            raise RootError("a root requires an epoch")

    def orientation(self) -> np.ndarray:
        R = orientation_from_two_directions(
            self.primary_direction, self.secondary_direction)
        if self.handedness == "LEFT":
            R = R @ np.diag([1, 1, -1])
        return R

    def quaternion(self) -> np.ndarray:
        return matrix_to_quaternion(self.orientation())


def refuse_single_direction_root(root_id: str) -> None:
    raise RootUnderdetermined(
        f"{root_id}: one direction leaves the roll free. Latitude and "
        f"longitude are calibration observations, not a frame; a root "
        f"needs a primary direction, a non-parallel secondary "
        f"direction, an epoch, a handedness, a scale, and an "
        f"uncertainty before any address on it is valid.")


def rootframe_report() -> dict:
    return {
        "rule": "a root needs two non-parallel directions to fix roll",
        "single_direction_verdict": "ROOT_UNDERDETERMINED",
        "calibration_vs_frame": (
            "lat/lon/elevation/ephemerides are CALIBRATION_OBSERVATION; "
            "the address frame is a CALCULATED root"),
        "required_fields": [
            "primary_direction", "secondary_direction", "epoch",
            "handedness", "scale", "uncertainty", "source_authority",
            "evidence_status"],
        "evidence_class": "DERIVED_MATHEMATICS",
        "measured_here": "nothing",
        "what_this_does_not_say": (
            "A root frame is a coordinate convention with uncertainty. "
            "Declaring one reaches nothing, actuates nothing, and "
            "measures nothing; it is bookkeeping that must be fully "
            "specified before an address built on it means anything."),
    }
