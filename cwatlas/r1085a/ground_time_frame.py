"""R10.8.5A §5 — GroundTimeFrame: epoch and ground-reference binding.

The address must remain synchronized with the rotating, evolving planet
below. **Time** selects the gravity state, magnetic state, shell
geometry and long-term frame state; **ground reference** selects the
rotational phase and body-fixed alignment. A projection without both
is refused — that is the whole point of this type.

Two alignment modes are declared:

``SEALED_R1082``
    The sealed R10.8.2 CALFREEZE orientation, reused exactly as frozen.
    No parameter of it is touched here.

``TRAINING_EQUALITY_R1085A``
    The sealed orientation composed with the **minimal rotation** that
    carries the decoded training-anchor cell direction onto the actual
    training-anchor direction. Solved from the Stonehenge training
    equality ONLY, then sealed; the roll degree of freedom about the
    aligned axis is left explicitly UNDETERMINED and recorded as such
    (it is one of the reasons the projection is underdetermined, not a
    hidden knob).

South-Up handedness is carried as a declared flag on the frame, per the
corpus convention, and does not silently flip any axis: the rendering
layer must consume it explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from cwatlas.claims import ClaimError

ALIGNMENT_MODES = ("SEALED_R1082", "TRAINING_EQUALITY_R1085A")


@dataclass(frozen=True)
class GroundTimeFrame:
    """Epoch + ground reference + body-fixed alignment, all explicit."""

    epoch_year: float
    ground_reference_id: str
    alignment_mode: str
    rotation: tuple  # 3x3 row tuples, mesh-frame -> Earth-frame
    rotational_phase_deg: float
    south_up: bool
    undetermined_dof: tuple[str, ...] = ()
    training_note: str = ""

    def __post_init__(self) -> None:
        if self.alignment_mode not in ALIGNMENT_MODES:
            raise ClaimError(
                f"unknown alignment mode {self.alignment_mode!r}; "
                f"declared: {ALIGNMENT_MODES}")
        if not self.ground_reference_id:
            raise ClaimError(
                "a GroundTimeFrame must declare a ground_reference_id; "
                "an address with no ground reference is not synchronized "
                "with the surface and cannot be projected.")
        r = self.matrix()
        if not np.allclose(r @ r.T, np.eye(3), atol=1e-9):
            raise ClaimError("frame rotation is not orthonormal")

    def matrix(self) -> np.ndarray:
        return np.array(self.rotation, dtype=float)

    def to_earth(self, mesh_vec: np.ndarray) -> np.ndarray:
        return self.matrix() @ np.asarray(mesh_vec, dtype=float)

    def to_mesh(self, earth_vec: np.ndarray) -> np.ndarray:
        return self.matrix().T @ np.asarray(earth_vec, dtype=float)


def minimal_rotation(from_vec: np.ndarray, to_vec: np.ndarray) -> np.ndarray:
    """The unique smallest rotation carrying one unit vector to another.

    Rodrigues construction about ``from x to``. This is the 2-DOF
    alignment; the third (roll about ``to_vec``) is deliberately NOT
    chosen here — callers must record it as undetermined.
    """
    a = np.asarray(from_vec, dtype=float)
    b = np.asarray(to_vec, dtype=float)
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    v = np.cross(a, b)
    c = float(np.dot(a, b))
    if np.linalg.norm(v) < 1e-15:
        if c > 0:
            return np.eye(3)
        raise ClaimError("antipodal alignment has no unique minimal "
                         "rotation; refuse rather than pick one silently")
    vx = np.array([[0.0, -v[2], v[1]],
                   [v[2], 0.0, -v[0]],
                   [-v[1], v[0], 0.0]])
    return np.eye(3) + vx + vx @ vx * (1.0 / (1.0 + c))


def rotation_angle_deg(r: np.ndarray) -> float:
    c = 0.5 * (float(np.trace(r)) - 1.0)
    return float(np.degrees(np.arccos(np.clip(c, -1.0, 1.0))))


def refuse_frame_without_epoch(*_a, **_k) -> None:
    raise ClaimError(
        "refused: a projection without an epoch is not synchronized with "
        "the evolving gravity, magnetic and shell state. Declare "
        "epoch_year on a GroundTimeFrame.")


def refuse_frame_without_ground_reference(*_a, **_k) -> None:
    raise ClaimError(
        "refused: a projection without a ground reference has no "
        "rotational phase or body-fixed alignment. Declare "
        "ground_reference_id on a GroundTimeFrame.")
