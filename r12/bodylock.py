"""R12 — a South-referenced body frame that does not force an inversion.

"South-referenced" sounds like one operation. It is at least four, and
they are not interchangeable::

    1. a PROPER rotation      diag(1, -1, -1),  det = +1
    2. a MIRROR / improper    diag(1,  1, -1),  det = -1
    3. a latitude sign flip   lat -> -lat        (a reflection, det = -1)
    4. an axis relabel        swap "north"/"south" naming (det = +1)

The first is a genuine change of viewpoint: looking at the planet from
the south is a half-turn about x, and its determinant ``(+1)(-1)(-1)``
is ``+1``, so handedness -- and therefore every downstream cross
product, normal and gradient sign -- is preserved. The second is a
reflection: it reverses handedness. The third, ``lat -> -lat``, is a
coordinate relabel written as a reflection across the equatorial plane,
so it too reverses handedness. The fourth renames which pole is called
north and changes no geometry at all.

**The audit (headline).** Applying TWO handedness-changing operations
returns the original handedness -- a double inversion is a no-op on
chirality. This is exactly how a "south-referenced" convention silently
cancels itself: a pipeline applies an improper operation *and* a
latitude sign flip, announces that it has "inverted to the southern
hemisphere", and in fact leaves handedness untouched while a reader
believes a flip occurred. :func:`net_handedness` reports the product of
the determinant signs, :func:`double_inversion_audit` reports whether a
double inversion has occurred, and :func:`refuse_forced_inversion`
raises when a pipeline pairs an improper operation with a latitude sign
flip, restores the original handedness, and still claims to have
inverted. A single improper op flips handedness; two restore it; the
audit catches the second case.

**The frame itself.** :func:`south_referenced_frame` runs the honest
pipeline: geodetic -> ECEF on WGS-84 (reusing
:func:`r11.earthface.geodetic_to_ecef`), then the PROPER South-Up
rotation only (reusing :data:`r11.earthface.SOUTH_UP_ROTATION`), and it
records the resulting handedness *explicitly*. The rotation is asserted
to have ``det == +1`` and to satisfy ``R @ R.T == I``.
:func:`refuse_undeclared_handedness` raises, because a frame whose
handedness is not declared is not a frame -- it is a basis whose
orientation the next stage will guess.

Nothing here is measured. No magnetometer was read, no site was
visited; every operation is exact linear algebra on published WGS-84
constants and on the imported, frozen South-Up rotation. The standing
verdict is that a South-referenced frame is *specifiable without forcing
a hemisphere inversion*, and that a forced double inversion is refused.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np

from r11.earthface import (
    SOUTH_UP_ROTATION,
    WGS84_A,
    WGS84_B,
    geodetic_to_ecef,
    is_proper_rotation,
)


class BodyLockError(ValueError):
    """Raised when a South-referenced frame is asked to over-claim: a
    forced double inversion, an undeclared handedness, or a radius from a
    handedness that was never fixed."""


# --- typed claim vocabulary (the repository-wide set) ------------------

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


CLAIM_CLASS = ClaimClass.REPOSITORY_COMPUTATIONAL_RESULT.value
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"
VERDICT = "SOUTH_REFERENCED_FRAME_NO_FORCED_INVERSION"

#: Handedness labels. A frame carries one of these explicitly, or it is
#: not a frame.
RIGHT_HANDED = "RIGHT_HANDED"
LEFT_HANDED = "LEFT_HANDED"
UNDECLARED_HANDEDNESS = "UNDECLARED_HANDEDNESS"


# --- the four things "south-referenced" can mean -----------------------

class SouthOperation(Enum):
    """The distinct operations a "south-referenced" convention conflates.

    Each is a different kind of object. Treating them as interchangeable
    is precisely what double-inverts.
    """

    #: diag(1, -1, -1). det = +1. A genuine rotation (half-turn about x).
    #: Reverses the sense of y and z but is NOT a reflection.
    PROPER_ROTATION = "PROPER_ROTATION"
    #: diag(1, 1, -1). det = -1. A reflection; flips handedness.
    MIRROR_IMPROPER = "MIRROR_IMPROPER"
    #: lat -> -lat. A coordinate relabel written as a reflection across
    #: the equatorial plane; det = -1, so it flips handedness.
    LATITUDE_SIGN_FLIP = "LATITUDE_SIGN_FLIP"
    #: Swap which pole is called "north". A naming change; det = +1 and
    #: no geometry moves.
    AXIS_RELABEL = "AXIS_RELABEL"


#: The determinant sign each operation carries. +1 preserves handedness,
#: -1 reverses it. This is the whole content of the audit.
_DETERMINANT_SIGN: dict[SouthOperation, int] = {
    SouthOperation.PROPER_ROTATION: +1,
    SouthOperation.MIRROR_IMPROPER: -1,
    SouthOperation.LATITUDE_SIGN_FLIP: -1,
    SouthOperation.AXIS_RELABEL: +1,
}

#: Which operations are reflections rather than rotations. Kept separate
#: from the sign so the reason is legible, not just the arithmetic.
_IS_REFLECTION: dict[SouthOperation, bool] = {
    SouthOperation.PROPER_ROTATION: False,
    SouthOperation.MIRROR_IMPROPER: True,
    SouthOperation.LATITUDE_SIGN_FLIP: True,
    SouthOperation.AXIS_RELABEL: False,
}


def _check_op(op: SouthOperation) -> SouthOperation:
    if not isinstance(op, SouthOperation):
        raise BodyLockError(
            f"{op!r} is not a SouthOperation; an unlabelled 'south' "
            f"operation is not an operation, it is an ambiguity")
    return op


def determinant_sign(op: SouthOperation) -> int:
    """The determinant sign (+1 or -1) of one operation."""
    return _DETERMINANT_SIGN[_check_op(op)]


def is_proper(op: SouthOperation) -> bool:
    """True iff the operation is orientation-preserving (det = +1).

    ``PROPER_ROTATION`` and ``AXIS_RELABEL`` are proper -- the first is a
    rotation, the second moves nothing. ``MIRROR_IMPROPER`` and
    ``LATITUDE_SIGN_FLIP`` are reflections and are not proper.
    """
    return _DETERMINANT_SIGN[_check_op(op)] > 0


def changes_handedness(op: SouthOperation) -> bool:
    """True iff the operation reverses handedness (det = -1)."""
    return _DETERMINANT_SIGN[_check_op(op)] < 0


def is_reflection(op: SouthOperation) -> bool:
    """True iff the operation is a reflection rather than a rotation."""
    return _IS_REFLECTION[_check_op(op)]


# --- the double-inversion audit ----------------------------------------

def net_handedness(ops) -> int:
    """Product of the determinant signs of a sequence of operations.

    ``+1`` means the composed pipeline preserves handedness; ``-1``
    means it reverses it. Two handedness-changing operations multiply to
    ``(-1)(-1) = +1``: a double inversion is a no-op on chirality, and
    this function is how that cancellation becomes visible instead of
    silent.
    """
    seq = tuple(ops)
    net = 1
    for op in seq:
        net *= _DETERMINANT_SIGN[_check_op(op)]
    return net


def double_inversion_audit(ops) -> dict:
    """Report whether a sequence of operations double-inverts.

    A double inversion is the specific failure this module exists to
    catch: two (or any even number of) handedness-changing operations
    that together restore the original handedness while each one, read on
    its own, looks like a flip. The dict names the count, the net
    handedness, and whether the pipeline is a double inversion.
    """
    seq = tuple(_check_op(op) for op in ops)
    flippers = tuple(op for op in seq if changes_handedness(op))
    net = net_handedness(seq)
    n_flip = len(flippers)
    return {
        "operations": tuple(op.value for op in seq),
        "handedness_changing_operations": tuple(op.value for op in flippers),
        "n_handedness_changing": n_flip,
        "net_handedness": net,
        "handedness_preserved": net == +1,
        "is_double_inversion": n_flip >= 2 and net == +1,
        "single_flip_reverses": n_flip == 1 and net == -1,
        "note": (
            "two handedness-changing operations restore the original "
            "handedness: a double inversion is a no-op on chirality, "
            "which is how a 'south-referenced' convention cancels itself "
            "while claiming to have flipped"),
    }


def refuse_forced_inversion(ops, claims_inversion: bool = True) -> dict:
    """Refuse a pipeline that pairs an improper op with a latitude flip,
    restores the original handedness, and still claims to have inverted.

    The classic double-inversion bug: apply a mirror (or any improper
    operation) *and* a latitude sign flip, announce a hemisphere flip,
    and in fact leave handedness exactly as it was. A single clean
    proper rotation does not trip this -- it changes viewpoint without
    changing handedness and claims nothing about inverting -- and a
    single improper op that genuinely reverses handedness does not trip
    it either, because its claim is honest. Only the cancelling pair,
    dressed as an inversion, is refused.

    Returns an audit dict when the pipeline is clean; raises
    :class:`BodyLockError` when it is the forced double inversion.
    """
    seq = tuple(_check_op(op) for op in ops)
    audit = double_inversion_audit(seq)
    has_improper = any(op is SouthOperation.MIRROR_IMPROPER
                       or (changes_handedness(op)
                           and op is not SouthOperation.LATITUDE_SIGN_FLIP)
                       for op in seq)
    has_lat_flip = any(op is SouthOperation.LATITUDE_SIGN_FLIP for op in seq)
    if (has_improper and has_lat_flip and audit["handedness_preserved"]
            and claims_inversion):
        raise BodyLockError(
            "refused: this pipeline applies an improper operation AND a "
            "latitude sign flip -- two handedness-changing operations -- "
            "so their determinant signs multiply to (-1)(-1) = +1 and the "
            "original handedness is RESTORED, not inverted. Claiming a "
            "hemisphere inversion here is false: the double inversion "
            "cancels, every downstream cross product and gradient sign is "
            "left exactly as it started, and a reader who trusts the "
            "'inverted' label reads the wrong chirality. Apply the PROPER "
            "South-Up rotation diag(1,-1,-1) alone, which changes "
            "viewpoint without touching handedness, or declare -- and "
            "own -- a single genuine reflection.")
    return audit


# --- the frame itself --------------------------------------------------

@dataclass(frozen=True)
class BodyFrame:
    """A South-referenced body-fixed frame with handedness DECLARED.

    ``rotation`` is the proper South-Up rotation that was applied.
    ``handedness`` is not optional: a frame that does not say whether it
    is right- or left-handed is a basis whose orientation the next stage
    will silently assume.
    """

    site_latitude_deg: float
    site_longitude_deg: float
    site_height_m: float
    ecef_m: tuple
    body_position_m: tuple
    rotation: tuple
    handedness: str
    determinant: float
    reference: str = "SOUTH_REFERENCED_PROPER_ROTATION"

    def __post_init__(self) -> None:
        if self.handedness not in (RIGHT_HANDED, LEFT_HANDED):
            raise BodyLockError(
                f"{self.handedness!r} is not a declared handedness; a "
                f"frame without a declared handedness is not a frame")

    def matrix(self) -> np.ndarray:
        return np.array(self.rotation, dtype=float)

    def is_orthonormal_proper(self, tol: float = 1e-12) -> bool:
        return is_proper_rotation(self.matrix(), tol=tol)


def south_referenced_frame(latitude_deg: float,
                           longitude_deg: float,
                           height_m: float = 0.0) -> BodyFrame:
    """Geodetic -> ECEF -> PROPER South-Up rotation, handedness recorded.

    Reuses :func:`r11.earthface.geodetic_to_ecef` for the ellipsoid
    conversion and :data:`r11.earthface.SOUTH_UP_ROTATION` for the view.
    The rotation is the proper one only -- no mirror, no latitude sign
    flip -- so handedness is preserved and recorded as ``RIGHT_HANDED``.
    Asserts ``det == +1`` and ``R @ R.T == I`` before returning; a frame
    that fails either is not returned at all.
    """
    ecef = geodetic_to_ecef(latitude_deg, longitude_deg, height_m)
    R = np.asarray(SOUTH_UP_ROTATION, dtype=float)
    det = float(np.linalg.det(R))
    if not np.allclose(R @ R.T, np.eye(3), atol=1e-12):
        raise BodyLockError(
            "the South-Up rotation is not orthonormal; R @ R.T != I, so "
            "it is not a rigid frame")
    if abs(det - 1.0) > 1e-9:
        raise BodyLockError(
            f"det = {det:+.3f}: the South-Up view must be a PROPER "
            f"rotation with determinant +1. A negative determinant would "
            f"reverse handedness and force an inversion this frame "
            f"refuses to force.")
    body = R @ ecef
    return BodyFrame(
        site_latitude_deg=float(latitude_deg),
        site_longitude_deg=float(longitude_deg),
        site_height_m=float(height_m),
        ecef_m=tuple(float(x) for x in ecef),
        body_position_m=tuple(float(x) for x in body),
        rotation=tuple(tuple(float(v) for v in row) for row in R),
        handedness=RIGHT_HANDED,
        determinant=det,
    )


def refuse_undeclared_handedness(handedness: str | None) -> str:
    """Return the handedness if declared; refuse an undeclared one.

    A frame reports orientation-dependent quantities -- cross products,
    face normals, gradient directions -- and every one of them changes
    sign under a handedness flip. A frame that does not say which
    handedness it uses cannot have any of those read from it without a
    guess, so an undeclared handedness is refused rather than defaulted.
    """
    if handedness is None or handedness in ("", UNDECLARED_HANDEDNESS):
        raise BodyLockError(
            "refused: no handedness declared. A body frame reports "
            "orientation-dependent quantities -- cross products, normals, "
            "gradient directions -- and each of them reverses sign under a "
            "handedness flip. Without a declared handedness the frame is a "
            "basis whose orientation the next stage will silently assume, "
            "which is exactly the ambiguity the double-inversion audit "
            "exists to close. Declare RIGHT_HANDED or LEFT_HANDED.")
    if handedness not in (RIGHT_HANDED, LEFT_HANDED):
        raise BodyLockError(
            f"{handedness!r} is not a recognised handedness label; use "
            f"{RIGHT_HANDED!r} or {LEFT_HANDED!r}")
    return handedness


# --- the report --------------------------------------------------------

def bodylock_report() -> dict:
    return {
        "what_this_is": (
            "a South-referenced body-fixed frame that applies only the "
            "PROPER South-Up rotation diag(1,-1,-1), records its "
            "handedness explicitly, and audits pipelines for a forced "
            "double inversion"),
        "operations": {op.value: {
            "determinant_sign": determinant_sign(op),
            "is_proper": is_proper(op),
            "changes_handedness": changes_handedness(op),
            "is_reflection": is_reflection(op),
        } for op in SouthOperation},
        "proper_rotation_det": +1,
        "mirror_det": -1,
        "double_inversion_is_a_noop_on_chirality": True,
        "south_up_reused_from_earthface": True,
        "wgs84_semi_major_m": WGS84_A,
        "wgs84_semi_minor_m": WGS84_B,
        "refusals": [
            "refuse_forced_inversion",
            "refuse_undeclared_handedness",
        ],
        "claim_class": CLAIM_CLASS,
        "measured_here": "nothing",
        "physical_validation": PHYSICAL_VALIDATION,
        "what_this_does_not_say": (
            "It does not say that any hemisphere is privileged, that a "
            "south-referenced frame reveals anything about the Earth, or "
            "that a magnetic or physical inversion has been detected. No "
            "magnetometer was read and no site was visited; every step is "
            "exact linear algebra on published WGS-84 constants and on the "
            "imported frozen South-Up rotation. It says a PROPER rotation "
            "changes viewpoint without changing handedness, that pairing "
            "an improper operation with a latitude sign flip RESTORES the "
            "original handedness rather than inverting it, and that "
            "claiming an inversion in that cancelling case is refused. A "
            "frame without a declared handedness is refused as well."),
        "verdict": VERDICT,
    }


__all__ = [
    "BodyLockError", "ClaimClass", "CLAIM_CLASS", "PHYSICAL_VALIDATION",
    "VERDICT", "RIGHT_HANDED", "LEFT_HANDED", "UNDECLARED_HANDEDNESS",
    "SouthOperation", "determinant_sign", "is_proper", "changes_handedness",
    "is_reflection", "net_handedness", "double_inversion_audit",
    "refuse_forced_inversion", "BodyFrame", "south_referenced_frame",
    "refuse_undeclared_handedness", "bodylock_report",
]
