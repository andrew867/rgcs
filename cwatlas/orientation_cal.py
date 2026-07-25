"""P30 — Root orientation calibration (Kabsch / Wahba).

Given a set of control points sampled in a body-fixed root frame and their
images in an orientation-profile-realized frame, this solves the best-fit
proper rotation aligning the two — the classic Kabsch / Wahba problem — and
freezes it. The frozen rotation then scores *holdout* control points without
retuning.

The solve uses **only the control points**. It never reads the orientation
profile's own rotation matrix to choose the fit — the profile is recorded for
provenance (which ``OrientationProfile`` and version the anchors sample), never
consulted during the solve. This preserves the calibration discipline: no known
destination is used to pick the transform (System Contract invariant 5).

Because the fit is a proper rotation recovered from planted synthetic control
points, it recovers the planted rotation exactly, up to the intrinsic ambiguity
of a degenerate (collinear or coincident) control configuration — which is
refused rather than guessed.

Pure arithmetic on NumPy. Nothing here measures anything; every input (control
points, profile) is passed in. No wall-clock is read.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np

from cwatlas.claims import ClaimClass
from cwatlas.earth_frame import OrientationProfile

#: Minimum control points for a determined 3-D rotation fit.
MIN_CONTROL_POINTS = 3
#: Tolerance below which a control configuration is treated as degenerate
#: (rank-deficient), in the same units as the control points.
DEGENERACY_TOL = 1e-9


class CalibrationError(ValueError):
    """Raised on an invalid, underdetermined, or degenerate calibration input.

    An explicit result state, never a silent guess.
    """


@dataclass(frozen=True)
class OrientationCalibration:
    """A frozen best-fit rotation with its provenance and training residual.

    ``rotation`` is stored as a nested tuple (row-major 3x3) so the frozen
    dataclass stays hashable; use :meth:`as_matrix` for the NumPy form. The
    ``profile_key`` / ``profile_version`` record which orientation profile the
    control anchors sample — for the receipt, not for the solve.
    """

    rotation: Tuple[Tuple[float, float, float], ...]
    profile_key: str
    profile_version: str
    n_train: int
    rmsd_train: float

    def as_matrix(self) -> np.ndarray:
        return np.asarray(self.rotation, dtype=float)


def _as_points(name: str, points) -> np.ndarray:
    arr = np.asarray(points, dtype=float)
    if arr.ndim != 2 or arr.shape[1] != 3:
        raise CalibrationError(f"{name} must be an (N, 3) array of points.")
    if not np.all(np.isfinite(arr)):
        raise CalibrationError(f"{name} must be finite.")
    return arr


def _check_nondegenerate(source: np.ndarray) -> None:
    """Refuse a control configuration that cannot determine a 3-D rotation."""
    centered = source - source.mean(axis=0)
    # Rank of the centered control cloud: needs to span 3-D (rank 3) to fix a
    # full rotation without ambiguity.
    rank = int(np.linalg.matrix_rank(centered, tol=DEGENERACY_TOL))
    if rank < 3:
        raise CalibrationError(
            "control points are degenerate (collinear or coplanar): they span "
            f"rank {rank} < 3 and cannot determine a full 3-D rotation without "
            "intrinsic ambiguity; refusing to guess. Provide non-coplanar "
            "control points.")


def solve_rotation(source, target) -> np.ndarray:
    """Kabsch solve: the proper rotation R minimizing ||R @ sourceᵀ − targetᵀ||.

    ``source`` and ``target`` are ``(N, 3)`` arrays of corresponding points.
    Returns a proper (det = +1) 3x3 rotation. Requires at least
    :data:`MIN_CONTROL_POINTS` non-degenerate points.
    """
    s = _as_points("source", source)
    t = _as_points("target", target)
    if s.shape != t.shape:
        raise CalibrationError(
            f"source {s.shape} and target {t.shape} must have equal shape.")
    if s.shape[0] < MIN_CONTROL_POINTS:
        raise CalibrationError(
            f"need at least {MIN_CONTROL_POINTS} control points to determine a "
            f"rotation, got {s.shape[0]}.")
    _check_nondegenerate(s)

    # Center both clouds (pure rotation about the centroid).
    s_c = s - s.mean(axis=0)
    t_c = t - t.mean(axis=0)
    # Cross-covariance and its SVD.
    h = s_c.T @ t_c
    u, _s_vals, vt = np.linalg.svd(h)
    d = np.sign(np.linalg.det(vt.T @ u.T))
    correction = np.diag([1.0, 1.0, d])
    r = vt.T @ correction @ u.T
    return r


def _rmsd(r: np.ndarray, source: np.ndarray, target: np.ndarray) -> float:
    s_c = source - source.mean(axis=0)
    t_c = target - target.mean(axis=0)
    resid = (r @ s_c.T).T - t_c
    return float(np.sqrt(np.mean(np.sum(resid * resid, axis=1))))


def calibrate_orientation(
    control_source, control_target, profile: OrientationProfile,
) -> OrientationCalibration:
    """Fit and freeze a rotation from training control points.

    The solve uses only the points. ``profile`` is recorded (its key and
    version) as the orientation profile the anchors sample; it is *not* read to
    choose the fit.
    """
    if not isinstance(profile, OrientationProfile):
        raise CalibrationError(
            "profile must be an OrientationProfile for provenance recording.")
    s = _as_points("control_source", control_source)
    t = _as_points("control_target", control_target)
    r = solve_rotation(s, t)
    rmsd = _rmsd(r, s, t)
    return OrientationCalibration(
        rotation=tuple(tuple(float(v) for v in row) for row in r),
        profile_key=profile.profile_key,
        profile_version=profile.version,
        n_train=int(s.shape[0]),
        rmsd_train=rmsd,
    )


def score_holdout(
    calibration: OrientationCalibration, source, target,
) -> float:
    """Score a frozen calibration on holdout points (no retuning).

    Returns the RMSD of the frozen rotation applied to the holdout source
    against the holdout target.
    """
    s = _as_points("source", source)
    t = _as_points("target", target)
    if s.shape != t.shape:
        raise CalibrationError(
            f"holdout source {s.shape} and target {t.shape} must match.")
    return _rmsd(calibration.as_matrix(), s, t)


def orientation_cal_report() -> dict:
    """P30 declaration receipt. Records the calibration discipline."""
    return {
        "phase_id": "P30",
        "what_this_is": (
            "a Kabsch/Wahba best-fit proper-rotation calibration of a "
            "body-fixed root against an orientation profile, solved from "
            "control points only, frozen, and scored on holdouts without "
            "retuning; the orientation profile is recorded for provenance and "
            "never consulted during the solve."),
        "claim_class": ClaimClass.CANONICAL_ROUND_TRIP.value,
        "min_control_points": MIN_CONTROL_POINTS,
        "degeneracy_tol": DEGENERACY_TOL,
        "recovers_planted_rotation": True,
        "intrinsic_ambiguity": (
            "a degenerate (collinear/coplanar) control configuration cannot fix "
            "a full 3-D rotation and is refused, not guessed."),
        "known_destination_used_to_choose_transform": False,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "ORIENTATION_CALIBRATION_KABSCH_PLANTED_ROTATION_RECOVERED",
    }
