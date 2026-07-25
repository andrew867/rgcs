"""P12 — Mars IAU body-fixed frame and portable body model.

This module gives the CW Atlas a *declared* Mars body-fixed coordinate frame
and a small, portable :class:`BodyModel` abstraction so Earth and Mars share
one API and differ only by constants (System Contract invariant 7: "Mars uses
a declared IAU body-fixed convention").

What it provides:

* :class:`BodyModel` — an oblate-spheroid body with a declared IAU convention,
  a declared height convention, and its ellipsoid constants.
* :data:`EARTH`, :data:`MARS` — the two reference bodies. Mars uses the IAU
  reference ellipsoid (equatorial radius a ~ 3396190 m, polar radius
  b ~ 3376200 m).
* forward and inverse maps between declared geodetic (ellipsoid-normal)
  coordinates and body-fixed Cartesian coordinates, with an exact round-trip
  within a declared quantization.
* the **areoid vs ellipsoid** height distinction, declared explicitly and never
  assumed: a :class:`BodyModel` carries a declared :class:`HeightConvention`,
  and mixing an areoid height into ellipsoid math without a declared separation
  model is a typed refusal.

This is pure arithmetic. Nothing here measures anything, and nothing here says
a source-reported vector identifies a real Martian (or terrestrial) location.
Under the claim taxonomy (:mod:`cwatlas.claims`) a frame conversion is at most
a ``MATHEMATICAL_TRANSLATION``.

The module is intentionally self-contained: it depends only on NumPy and
``cwatlas.claims``. A richer ``cwatlas.geodesy`` may exist elsewhere, but P12
carries its own ellipsoid math so it stands alone.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np

from cwatlas.claims import ClaimClass


class FrameError(ValueError):
    """Raised on an invalid, ambiguous, or underdetermined frame input.

    An explicit result state, never a silent guess.
    """


class HeightConvention(Enum):
    """A declared vertical datum. The atlas never assumes one."""

    #: Height measured along the ellipsoid normal, above the reference
    #: ellipsoid. This is the datum the Cartesian transforms operate in.
    ELLIPSOIDAL = "ELLIPSOIDAL"
    #: Earth geoid (mean-sea-level equipotential). Converting to/from
    #: ellipsoidal height needs a declared geoid-separation model.
    GEOID = "GEOID"
    #: Mars areoid (the equipotential surface used as the Mars vertical
    #: datum). Converting to/from ellipsoidal height needs a declared
    #: areoid-separation model; it is *not* the reference ellipsoid.
    AREOID = "AREOID"


class LatitudeConvention(Enum):
    """A declared latitude convention (relevant to the IAU Mars products)."""

    #: Angle between the ellipsoid normal and the equatorial plane. This is
    #: the geodetic latitude the Cartesian transforms use.
    PLANETOGRAPHIC = "PLANETOGRAPHIC"
    #: Angle between the body-centre radius and the equatorial plane.
    PLANETOCENTRIC = "PLANETOCENTRIC"


@dataclass(frozen=True)
class BodyModel:
    """An oblate-spheroid reference body with a *declared* IAU convention.

    Portability is the point: Earth and Mars are the same dataclass with
    different constants and a different declared convention string. Invariant
    7 requires the IAU (or geodetic) convention to be declared, so an empty
    ``iau_convention`` is refused at construction.
    """

    body_id: str
    frame_id: str
    #: Equatorial radius a, metres.
    semi_major_axis_m: float
    #: Polar radius b, metres.
    semi_minor_axis_m: float
    #: The declared convention string. Required (invariant 7).
    iau_convention: str
    #: The declared vertical datum for coordinates expressed in this body.
    height_convention: HeightConvention = HeightConvention.ELLIPSOIDAL
    #: The declared latitude convention for geodetic coordinates.
    latitude_convention: LatitudeConvention = LatitudeConvention.PLANETOGRAPHIC
    #: The prime-meridian datum name, for the receipt.
    prime_meridian: str = "UNSPECIFIED"

    def __post_init__(self) -> None:
        if not self.iau_convention:
            raise FrameError(
                "invariant 7: a body must declare its IAU / geodetic "
                "convention; none was given.")
        if not (self.semi_major_axis_m > 0.0 and self.semi_minor_axis_m > 0.0):
            raise FrameError("ellipsoid radii must be positive and finite.")
        if self.semi_minor_axis_m > self.semi_major_axis_m:
            raise FrameError(
                "polar radius exceeds equatorial radius; the reference body "
                "must be an oblate (or spherical) ellipsoid.")

    @property
    def flattening(self) -> float:
        """f = (a - b) / a."""
        return (self.semi_major_axis_m - self.semi_minor_axis_m) / self.semi_major_axis_m

    @property
    def eccentricity_sq(self) -> float:
        """First eccentricity squared, e^2 = 1 - b^2 / a^2."""
        a = self.semi_major_axis_m
        b = self.semi_minor_axis_m
        return 1.0 - (b * b) / (a * a)

    def prime_vertical_radius(self, lat_rad: float) -> float:
        """Radius of curvature in the prime vertical, N(lat)."""
        s = np.sin(lat_rad)
        return self.semi_major_axis_m / np.sqrt(1.0 - self.eccentricity_sq * s * s)

    def report(self) -> dict:
        """A declaration receipt for this body (invariant 2 fields)."""
        return {
            "body_id": self.body_id,
            "frame_id": self.frame_id,
            "semi_major_axis_m": self.semi_major_axis_m,
            "semi_minor_axis_m": self.semi_minor_axis_m,
            "flattening": self.flattening,
            "eccentricity_sq": self.eccentricity_sq,
            "iau_convention": self.iau_convention,
            "height_convention": self.height_convention.value,
            "latitude_convention": self.latitude_convention.value,
            "prime_meridian": self.prime_meridian,
        }


@dataclass(frozen=True)
class GeodeticPoint:
    """A declared geodetic coordinate on a specific body."""

    latitude_deg: float
    longitude_deg: float
    height_m: float
    body_id: str
    height_convention: HeightConvention


@dataclass(frozen=True)
class BodyFixedPoint:
    """A body-fixed Cartesian coordinate (metres) in a declared frame."""

    x_m: float
    y_m: float
    z_m: float
    body_id: str
    frame_id: str


# --- The two reference bodies -------------------------------------------------

#: Earth, declared geodetic convention (WGS84 ellipsoid constants).
EARTH = BodyModel(
    body_id="EARTH",
    frame_id="IAU_EARTH_BODY_FIXED",
    semi_major_axis_m=6378137.0,
    semi_minor_axis_m=6356752.314245,
    iau_convention=(
        "WGS84 ellipsoid; geodetic (ellipsoid-normal) latitude; longitude "
        "east-positive from the IERS reference meridian."),
    height_convention=HeightConvention.ELLIPSOIDAL,
    latitude_convention=LatitudeConvention.PLANETOGRAPHIC,
    prime_meridian="IERS_REFERENCE_MERIDIAN",
)

#: Mars, declared IAU body-fixed convention. Equatorial radius a and polar
#: radius b are the IAU Mars reference ellipsoid values.
MARS = BodyModel(
    body_id="MARS",
    frame_id="IAU_MARS_BODY_FIXED",
    semi_major_axis_m=3396190.0,
    semi_minor_axis_m=3376200.0,
    iau_convention=(
        "IAU Mars reference ellipsoid; geodetic (planetographic, "
        "ellipsoid-normal) latitude; longitude east-positive; prime meridian "
        "at the Airy-0 crater datum. Vertical datum declared separately "
        "(ellipsoid vs areoid) and never assumed."),
    height_convention=HeightConvention.ELLIPSOIDAL,
    latitude_convention=LatitudeConvention.PLANETOGRAPHIC,
    prime_meridian="AIRY-0",
)

#: Body registry, keyed by body id.
BODIES: dict[str, BodyModel] = {EARTH.body_id: EARTH, MARS.body_id: MARS}


def get_body(body_id: str) -> BodyModel:
    """Look up a reference body, or refuse an unknown id."""
    try:
        return BODIES[body_id]
    except KeyError:
        raise FrameError(
            f"unknown body {body_id!r}; declared bodies are "
            f"{sorted(BODIES)}.") from None


# --- Validation ---------------------------------------------------------------

def _require_finite(name: str, value: float) -> float:
    v = float(value)
    if not np.isfinite(v):
        raise FrameError(f"{name} must be finite, got {value!r}.")
    return v


def _check_height_convention(body: BodyModel, convention: HeightConvention) -> None:
    """Refuse ellipsoid math on a non-ellipsoidal height with no separation.

    The areoid (or geoid) is not the reference ellipsoid. Feeding an areoid
    height straight into ellipsoid Cartesian math would silently assume a zero
    separation, which the atlas must not do.
    """
    if convention is not HeightConvention.ELLIPSOIDAL:
        raise FrameError(
            f"height convention {convention.value} is not ELLIPSOIDAL; the "
            f"body-fixed Cartesian transform operates on ellipsoidal height. "
            f"Converting a {convention.value} height requires a declared "
            f"separation model for {body.body_id}; none was provided. This is "
            f"an explicit refusal, not a silent zero-separation assumption.")


# --- Forward / inverse transforms ---------------------------------------------

def geodetic_to_bodyfixed(
    body: BodyModel,
    latitude_deg: float,
    longitude_deg: float,
    height_m: float,
    height_convention: HeightConvention = HeightConvention.ELLIPSOIDAL,
) -> BodyFixedPoint:
    """Geodetic (ellipsoid-normal) coordinate -> body-fixed Cartesian metres.

    ``height_convention`` must be ``ELLIPSOIDAL``; any other convention is a
    typed refusal until a separation model is declared.
    """
    _check_height_convention(body, height_convention)
    lat = _require_finite("latitude_deg", latitude_deg)
    lon = _require_finite("longitude_deg", longitude_deg)
    h = _require_finite("height_m", height_m)
    if not -90.0 <= lat <= 90.0:
        raise FrameError(f"latitude_deg must be in [-90, 90], got {lat}.")

    lat_r = np.radians(lat)
    lon_r = np.radians(lon)
    n = body.prime_vertical_radius(lat_r)
    e2 = body.eccentricity_sq
    cos_lat = np.cos(lat_r)
    x = (n + h) * cos_lat * np.cos(lon_r)
    y = (n + h) * cos_lat * np.sin(lon_r)
    z = (n * (1.0 - e2) + h) * np.sin(lat_r)
    return BodyFixedPoint(
        x_m=float(x), y_m=float(y), z_m=float(z),
        body_id=body.body_id, frame_id=body.frame_id)


def bodyfixed_to_geodetic(
    body: BodyModel,
    x_m: float,
    y_m: float,
    z_m: float,
    max_iter: int = 12,
    tol_rad: float = 1e-15,
) -> GeodeticPoint:
    """Body-fixed Cartesian metres -> geodetic coordinate (ellipsoidal height).

    Uses a stable fixed-point iteration on latitude and handles the polar
    singularity explicitly.
    """
    x = _require_finite("x_m", x_m)
    y = _require_finite("y_m", y_m)
    z = _require_finite("z_m", z_m)

    a = body.semi_major_axis_m
    b = body.semi_minor_axis_m
    e2 = body.eccentricity_sq
    lon_r = np.arctan2(y, x)
    p = np.hypot(x, y)

    if p < 1e-9:  # on the spin axis: a pole
        sign = 1.0 if z >= 0.0 else -1.0
        lat_r = sign * (np.pi / 2.0)
        height = abs(z) - b
        return GeodeticPoint(
            latitude_deg=float(np.degrees(lat_r)),
            longitude_deg=float(np.degrees(lon_r)),
            height_m=float(height),
            body_id=body.body_id,
            height_convention=HeightConvention.ELLIPSOIDAL)

    lat_r = np.arctan2(z, p * (1.0 - e2))  # first guess
    for _ in range(max_iter):
        s = np.sin(lat_r)
        n = a / np.sqrt(1.0 - e2 * s * s)
        height = p / np.cos(lat_r) - n
        new_lat = np.arctan2(z, p * (1.0 - e2 * n / (n + height)))
        if abs(new_lat - lat_r) < tol_rad:
            lat_r = new_lat
            break
        lat_r = new_lat

    s = np.sin(lat_r)
    n = a / np.sqrt(1.0 - e2 * s * s)
    height = p / np.cos(lat_r) - n
    return GeodeticPoint(
        latitude_deg=float(np.degrees(lat_r)),
        longitude_deg=float(np.degrees(lon_r)),
        height_m=float(height),
        body_id=body.body_id,
        height_convention=HeightConvention.ELLIPSOIDAL)


# --- Latitude convention helpers (planetographic <-> planetocentric) ---------

def planetographic_to_planetocentric_deg(body: BodyModel, lat_deg: float) -> float:
    """Convert a geodetic (planetographic) latitude to planetocentric.

    tan(phi_c) = (b^2 / a^2) tan(phi_g). Pure ellipsoid geometry.
    """
    lat = _require_finite("lat_deg", lat_deg)
    if not -90.0 <= lat <= 90.0:
        raise FrameError(f"lat_deg must be in [-90, 90], got {lat}.")
    a = body.semi_major_axis_m
    b = body.semi_minor_axis_m
    ratio = (b * b) / (a * a)
    return float(np.degrees(np.arctan(ratio * np.tan(np.radians(lat)))))


def planetocentric_to_planetographic_deg(body: BodyModel, lat_deg: float) -> float:
    """Convert a planetocentric latitude to geodetic (planetographic)."""
    lat = _require_finite("lat_deg", lat_deg)
    if not -90.0 <= lat <= 90.0:
        raise FrameError(f"lat_deg must be in [-90, 90], got {lat}.")
    a = body.semi_major_axis_m
    b = body.semi_minor_axis_m
    ratio = (a * a) / (b * b)
    return float(np.degrees(np.arctan(ratio * np.tan(np.radians(lat)))))


# --- Governance report --------------------------------------------------------

def mars_frame_report() -> dict:
    """P12 declaration receipt. Claims nothing physical or geographic."""
    return {
        "phase_id": "P12",
        "what_this_is": (
            "a declared Mars IAU body-fixed frame, a portable BodyModel for "
            "Earth and Mars, ellipsoidal <-> body-fixed Cartesian transforms "
            "with an exact round-trip, and an explicitly declared areoid-vs-"
            "ellipsoid height convention."),
        "claim_class": ClaimClass.MATHEMATICAL_TRANSLATION.value,
        "bodies": {bid: b.report() for bid, b in BODIES.items()},
        "height_conventions": [c.value for c in HeightConvention],
        "latitude_conventions": [c.value for c in LatitudeConvention],
        "declared_iau_convention_required": True,
        "areoid_vs_ellipsoid": (
            "the areoid is an equipotential vertical datum and is NOT the "
            "reference ellipsoid; converting an areoid height into ellipsoid "
            "math without a declared separation model is refused."),
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": (
            "SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED"),
        "verdict": "MARS_IAU_BODY_FIXED_FRAME_DECLARED_NO_PHYSICAL_CLAIM",
    }
