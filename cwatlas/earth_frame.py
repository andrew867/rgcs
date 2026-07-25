"""P11 -- Earth body-fixed root and versioned orientation profiles.

The Earth body-fixed root defines the frame's *conventions*: the origin at
the geocentre, the rotation axis (+Z), and the prime meridian direction
(+X toward 0 deg longitude), with an optional crustal anchor tying the frame
to a physical reference station.

An :class:`OrientationProfile` is a versioned record of how the body-fixed
root is realized as ECEF -- small pole (polar-motion) and prime-meridian
offsets. Switching profiles changes the mapping *deterministically*, and the
switch is recorded in an :class:`OrientationApplication` receipt. Legacy
profiles are retained as named versions, never overwritten.

The mapping is a pure rotation, so it is exactly reversible. Nothing here
validates anything physical or claims a source-vector geographic semantics.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED

Offsets and vectors are passed in; no wall-clock is read.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

import numpy as np

from cwatlas import claims

ARCSEC_TO_RAD = math.pi / (180.0 * 3600.0)
BODY_ID = "EARTH"


class OrientationError(ValueError):
    """Raised on an invalid orientation profile or vector."""


@dataclass(frozen=True)
class EarthBodyFixedRoot:
    """Conventions of the Earth body-fixed frame.

    Defaults are the canonical geocentric conventions. A ``crustal_anchor``
    (ECEF metres) optionally ties the abstract frame to a reference station.
    """

    geocentre_m: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation_axis: Tuple[float, float, float] = (0.0, 0.0, 1.0)
    prime_meridian_dir: Tuple[float, float, float] = (1.0, 0.0, 0.0)
    crustal_anchor_m: Optional[Tuple[float, float, float]] = None

    def __post_init__(self) -> None:
        for name in ("geocentre_m", "rotation_axis", "prime_meridian_dir"):
            v = getattr(self, name)
            if len(v) != 3 or not all(math.isfinite(c) for c in v):
                raise OrientationError(f"{name} must be three finite floats")
        if self.crustal_anchor_m is not None:
            a = self.crustal_anchor_m
            if len(a) != 3 or not all(math.isfinite(c) for c in a):
                raise OrientationError(
                    "crustal_anchor_m must be three finite floats or None")
        if np.linalg.norm(self.rotation_axis) == 0.0:
            raise OrientationError("rotation_axis must be non-zero")
        if np.linalg.norm(self.prime_meridian_dir) == 0.0:
            raise OrientationError("prime_meridian_dir must be non-zero")


@dataclass(frozen=True)
class OrientationProfile:
    """A versioned realization of the body-fixed root as ECEF.

    Parameters are small offsets: polar motion (``pole_x_arcsec``,
    ``pole_y_arcsec``) and a prime-meridian longitude offset
    (``prime_meridian_offset_deg``). The identity profile has all offsets
    zero. Different profiles produce different, deterministic rotations.
    """

    profile_id: str
    version: str
    pole_x_arcsec: float = 0.0
    pole_y_arcsec: float = 0.0
    prime_meridian_offset_deg: float = 0.0

    def __post_init__(self) -> None:
        if not self.profile_id:
            raise OrientationError("profile_id must be a non-empty string")
        if not self.version:
            raise OrientationError("version must be a non-empty string")
        for name in (
            "pole_x_arcsec", "pole_y_arcsec", "prime_meridian_offset_deg",
        ):
            if not math.isfinite(getattr(self, name)):
                raise OrientationError(f"{name} must be finite")

    @property
    def profile_key(self) -> str:
        return f"{self.profile_id}@{self.version}"

    def rotation_matrix(self) -> np.ndarray:
        """The deterministic 3x3 rotation this profile applies to a vector.

        Composed as Rz(prime meridian) . Ry(pole_x) . Rx(pole_y). The
        identity profile yields the identity matrix.
        """
        xp = self.pole_x_arcsec * ARCSEC_TO_RAD
        yp = self.pole_y_arcsec * ARCSEC_TO_RAD
        pm = math.radians(self.prime_meridian_offset_deg)
        return _rot_z(pm) @ _rot_y(xp) @ _rot_x(yp)

    def matrix_hash(self) -> str:
        m = self.rotation_matrix()
        # Round to a fixed grid so the hash is reproducible across platforms.
        blob = ",".join(f"{v:.15e}" for v in np.round(m, 15).ravel())
        return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _rot_x(a: float) -> np.ndarray:
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], dtype=float)


def _rot_y(a: float) -> np.ndarray:
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], dtype=float)


def _rot_z(a: float) -> np.ndarray:
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], dtype=float)


#: Versioned profile registry. Legacy profiles are retained, never dropped.
ORIENTATION_PROFILES: Dict[str, OrientationProfile] = {
    "IDENTITY@1.0.0": OrientationProfile("IDENTITY", "1.0.0"),
    "IERS-NOMINAL@1.0.0": OrientationProfile(
        "IERS-NOMINAL", "1.0.0",
        pole_x_arcsec=0.161, pole_y_arcsec=0.335,
        prime_meridian_offset_deg=0.0),
    "IERS-NOMINAL@2.0.0": OrientationProfile(
        "IERS-NOMINAL", "2.0.0",
        pole_x_arcsec=0.170, pole_y_arcsec=0.340,
        prime_meridian_offset_deg=0.0),
}


def get_profile(profile_key: str) -> OrientationProfile:
    try:
        return ORIENTATION_PROFILES[profile_key]
    except KeyError:
        raise OrientationError(
            f"unknown orientation profile {profile_key!r}; known: "
            f"{sorted(ORIENTATION_PROFILES)}")


@dataclass(frozen=True)
class OrientationApplication:
    """A record that a profile was applied to a vector (recorded switch)."""

    profile_key: str
    matrix_hash: str
    input_vector: Tuple[float, float, float]
    output_vector: Tuple[float, float, float]


def apply_orientation(
    vector_ecef: Tuple[float, float, float], profile: OrientationProfile,
) -> OrientationApplication:
    """Apply ``profile`` to ``vector_ecef`` and return a recorded result."""
    v = np.asarray(vector_ecef, dtype=float)
    if v.shape != (3,) or not np.all(np.isfinite(v)):
        raise OrientationError("vector_ecef must be three finite floats")
    out = profile.rotation_matrix() @ v
    return OrientationApplication(
        profile_key=profile.profile_key,
        matrix_hash=profile.matrix_hash(),
        input_vector=(float(v[0]), float(v[1]), float(v[2])),
        output_vector=(float(out[0]), float(out[1]), float(out[2])),
    )


def invert_orientation(
    vector_ecef: Tuple[float, float, float], profile: OrientationProfile,
) -> Tuple[float, float, float]:
    """Inverse of :func:`apply_orientation` (rotation transpose)."""
    v = np.asarray(vector_ecef, dtype=float)
    if v.shape != (3,) or not np.all(np.isfinite(v)):
        raise OrientationError("vector_ecef must be three finite floats")
    out = profile.rotation_matrix().T @ v
    return (float(out[0]), float(out[1]), float(out[2]))


def earth_frame_report() -> dict:
    """What this module claims -- and what it refuses to claim."""
    return {
        "module": "cwatlas.earth_frame",
        "phase_id": "P11",
        "body_id": BODY_ID,
        "profiles": sorted(ORIENTATION_PROFILES),
        "claim_class": claims.ClaimClass.CANONICAL_ROUND_TRIP.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "note": (
            "the body-fixed root fixes geocentre/axis/prime-meridian "
            "conventions; switching orientation profile changes the ECEF "
            "mapping deterministically and is recorded. The mapping is a "
            "pure rotation and is exactly reversible."),
        "verdict": "EARTH_BODY_FIXED_ROOT_VERSIONED_ORIENTATION_DETERMINISTIC",
    }
