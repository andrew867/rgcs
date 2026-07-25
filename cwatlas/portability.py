"""P31 — Cross-body scale portability.

The same addressing / codec API works on Earth and Mars: the caller passes a
:class:`cwatlas.mars_frame.BodyModel` (different constants, different declared
IAU convention) and gets the same operations. A scale factor maps a cell size
between bodies (a body's larger radius makes the same angular cell subtend a
larger metric cell).

The governance rule (System Contract invariant 7, plus the body-fixed
discipline): **a coordinate carries its ``body_id`` and is never silently
reused across bodies.** Two coordinates on different bodies may not be combined,
and a coordinate may only cross to another body through an *explicit* conversion
that records the crossing — never a silent relabel. The explicit conversion is a
``MATHEMATICAL_TRANSLATION`` and asserts nothing geographic.

Pure arithmetic on the portable :class:`BodyModel`. Nothing here measures
anything; every input is passed in.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from cwatlas.claims import ClaimClass
from cwatlas.mars_frame import (
    BodyFixedPoint,
    BodyModel,
    HeightConvention,
    geodetic_to_bodyfixed,
    get_body,
)


class PortabilityError(ValueError):
    """Raised on an invalid coordinate or an illegal cross-body operation.

    An explicit result state, never a silent guess.
    """


@dataclass(frozen=True)
class BodyBoundCoordinate:
    """A geodetic coordinate that *carries its body*.

    The ``body_id`` is part of the coordinate's identity; it cannot be dropped
    or silently swapped. Operations that combine coordinates require matching
    ``body_id`` values.
    """

    body_id: str
    latitude_deg: float
    longitude_deg: float
    height_m: float
    height_convention: HeightConvention = HeightConvention.ELLIPSOIDAL

    def __post_init__(self) -> None:
        if not self.body_id:
            raise PortabilityError("a coordinate must declare a body_id.")
        for name, value in (
            ("latitude_deg", self.latitude_deg),
            ("longitude_deg", self.longitude_deg),
            ("height_m", self.height_m),
        ):
            if not math.isfinite(value):
                raise PortabilityError(f"{name} must be finite, got {value!r}.")
        if not (-90.0 <= self.latitude_deg <= 90.0):
            raise PortabilityError(
                f"latitude_deg must be in [-90, 90], got {self.latitude_deg}.")


def address_on_body(
    body: BodyModel,
    latitude_deg: float,
    longitude_deg: float,
    height_m: float,
    height_convention: HeightConvention = HeightConvention.ELLIPSOIDAL,
) -> BodyBoundCoordinate:
    """The same addressing API for any body — Earth or Mars.

    Binds the coordinate to ``body.body_id``.
    """
    if not isinstance(body, BodyModel):
        raise PortabilityError("body must be a BodyModel.")
    return BodyBoundCoordinate(
        body_id=body.body_id,
        latitude_deg=latitude_deg,
        longitude_deg=longitude_deg,
        height_m=height_m,
        height_convention=height_convention,
    )


def to_bodyfixed(coord: BodyBoundCoordinate, body: BodyModel) -> BodyFixedPoint:
    """Convert a body-bound coordinate to body-fixed Cartesian on ``body``.

    Refuses if the coordinate's ``body_id`` does not match ``body`` — the codec
    is the same, but the body must be explicit and consistent.
    """
    require_same_body_id(coord.body_id, body.body_id, op="to_bodyfixed")
    return geodetic_to_bodyfixed(
        body,
        coord.latitude_deg,
        coord.longitude_deg,
        coord.height_m,
        height_convention=coord.height_convention,
    )


def cell_scale_factor(from_body: BodyModel, to_body: BodyModel) -> float:
    """Scale factor mapping a metric cell size from ``from_body`` to ``to_body``.

    The same angular cell subtends a metric size proportional to the body's
    equatorial radius, so the factor is ``to.a / from.a``.
    """
    if not (isinstance(from_body, BodyModel) and isinstance(to_body, BodyModel)):
        raise PortabilityError("from_body and to_body must be BodyModel.")
    return to_body.semi_major_axis_m / from_body.semi_major_axis_m


def scale_cell_size_m(
    cell_size_m: float, from_body: BodyModel, to_body: BodyModel,
) -> float:
    """Map a metric cell size from one body to another via :func:`cell_scale_factor`."""
    if not math.isfinite(cell_size_m) or cell_size_m <= 0.0:
        raise PortabilityError("cell_size_m must be positive and finite.")
    return cell_size_m * cell_scale_factor(from_body, to_body)


def require_same_body_id(a_body_id: str, b_body_id: str, op: str = "operation") -> None:
    """Refuse combining two operands from different bodies."""
    if a_body_id != b_body_id:
        raise PortabilityError(
            f"refused: {op} mixes body {a_body_id!r} and body {b_body_id!r}. A "
            f"coordinate carries its body and is never silently reused across "
            f"bodies; use convert_coordinate_to_body() for an explicit, "
            f"recorded crossing.")


def refuse_cross_body_mixing(
    a: BodyBoundCoordinate, b: BodyBoundCoordinate, op: str = "operation",
) -> None:
    """Refuse an operation on two coordinates from different bodies."""
    require_same_body_id(a.body_id, b.body_id, op=op)


@dataclass(frozen=True)
class BodyCrossing:
    """A recorded, explicit crossing of a coordinate from one body to another.

    The crossing is a numeric relabel of the geodetic tuple onto a different
    body. It is a ``MATHEMATICAL_TRANSLATION`` and asserts nothing geographic:
    the same lat/lon/height numbers on a different body are a different place,
    and this records that the caller *chose* to reuse the numbers.
    """

    from_body_id: str
    to_body_id: str
    result: BodyBoundCoordinate
    claim_class: ClaimClass = ClaimClass.MATHEMATICAL_TRANSLATION


def convert_coordinate_to_body(
    coord: BodyBoundCoordinate, to_body: BodyModel,
) -> BodyCrossing:
    """Explicitly cross a coordinate to another body, recording the crossing.

    This is the *only* sanctioned way to move a coordinate between bodies. It
    never happens silently. It reuses the geodetic numbers on ``to_body`` and
    records the crossing as a MATHEMATICAL_TRANSLATION — no geographic identity
    is claimed across the crossing.
    """
    if not isinstance(to_body, BodyModel):
        raise PortabilityError("to_body must be a BodyModel.")
    get_body(coord.body_id)  # refuses if the source body is unknown
    result = BodyBoundCoordinate(
        body_id=to_body.body_id,
        latitude_deg=coord.latitude_deg,
        longitude_deg=coord.longitude_deg,
        height_m=coord.height_m,
        height_convention=coord.height_convention,
    )
    return BodyCrossing(
        from_body_id=coord.body_id,
        to_body_id=to_body.body_id,
        result=result,
    )


def portability_report() -> dict:
    """P31 declaration receipt. Records the cross-body discipline."""
    return {
        "phase_id": "P31",
        "what_this_is": (
            "the same addressing/codec API on Earth and Mars via BodyModel "
            "(different constants), a cell-size scale factor between bodies, "
            "and a coordinate that carries its body_id and is never silently "
            "reused across bodies; cross-body mixing is refused and crossing "
            "requires an explicit recorded conversion."),
        "claim_class": ClaimClass.MATHEMATICAL_TRANSLATION.value,
        "cross_body_mixing_refused": True,
        "explicit_conversion_required": True,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "CROSS_BODY_PORTABLE_API_NO_SILENT_BODY_REUSE",
    }
