"""P09 -- WGS84 geodetic <-> ECEF core (CW-GEO-1 geodetic baseline).

Exact, reversible transforms between WGS84 geodetic coordinates
(latitude, longitude, ellipsoidal height) and Earth-Centred, Earth-Fixed
(ECEF) Cartesian coordinates. Forward is the closed-form ellipsoid
projection; inverse is a Bowring-seeded fixed-point refinement that stays
stable at the poles, across the dateline (+/-180 deg), and at negative
(sub-ellipsoid) heights.

This is arithmetic on a *declared* geodetic convention. It says nothing
about what any operator-reported source vector meant, and it validates
nothing physical. The reversible round-trip is a property of the codec
(``CANONICAL_ROUND_TRIP``), not evidence about the world.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED

All values are explicit-unit floats: latitude/longitude in degrees,
heights and Cartesian components in metres. Nothing here reads a
wall-clock; every input is passed in.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple

import numpy as np

from cwatlas import claims

# -- WGS84 defining constants (exact symbolic forms kept beside decimals) ----

#: Semi-major axis, metres (WGS84 defining constant).
WGS84_A = 6378137.0
#: Inverse flattening (WGS84 defining constant): f = 1 / 298.257223563.
WGS84_INV_F = 298.257223563
#: Flattening f = 1 / 298.257223563.
WGS84_F = 1.0 / WGS84_INV_F
#: Semi-minor axis b = a (1 - f), metres.
WGS84_B = WGS84_A * (1.0 - WGS84_F)
#: First eccentricity squared e^2 = f (2 - f).
WGS84_E2 = WGS84_F * (2.0 - WGS84_F)
#: Second eccentricity squared e'^2 = (a^2 - b^2) / b^2.
WGS84_EP2 = (WGS84_A * WGS84_A - WGS84_B * WGS84_B) / (WGS84_B * WGS84_B)

#: The coordinate reference system these transforms are declared against.
CRS_ID = "WGS84"
#: Codec identity for the geodetic baseline (see architecture spec).
CODEC_ID = "CW-GEO-1"
CODEC_VERSION = "1.0.0"
#: Height convention: ellipsoidal height above the WGS84 ellipsoid.
HEIGHT_CONVENTION = "ELLIPSOIDAL_HEIGHT_ABOVE_WGS84"


class GeodesyError(ValueError):
    """Raised on an invalid, non-finite, or out-of-range coordinate.

    Underdetermined inputs (e.g. the exact geocentre, where longitude is
    undefined) fail here rather than returning a silent guess.
    """


@dataclass(frozen=True)
class GeodeticPoint:
    """A WGS84 geodetic coordinate carrying its CRS (contract invariant 9).

    Longitude is normalised to the half-open interval (-180, 180]; +/-180
    both denote the dateline and normalise to +180.
    """

    latitude_deg: float
    longitude_deg: float
    height_m: float
    crs: str = CRS_ID
    height_convention: str = HEIGHT_CONVENTION

    def __post_init__(self) -> None:
        for name, value in (
            ("latitude_deg", self.latitude_deg),
            ("longitude_deg", self.longitude_deg),
            ("height_m", self.height_m),
        ):
            if not math.isfinite(value):
                raise GeodesyError(f"{name} must be finite, got {value!r}")
        if not (-90.0 <= self.latitude_deg <= 90.0):
            raise GeodesyError(
                f"latitude_deg must be in [-90, 90], got {self.latitude_deg!r}")
        object.__setattr__(
            self, "longitude_deg", _normalize_longitude(self.longitude_deg))


@dataclass(frozen=True)
class EcefPoint:
    """An ECEF Cartesian coordinate in metres, tied to a CRS."""

    x_m: float
    y_m: float
    z_m: float
    crs: str = CRS_ID

    def __post_init__(self) -> None:
        for name, value in (
            ("x_m", self.x_m), ("y_m", self.y_m), ("z_m", self.z_m),
        ):
            if not math.isfinite(value):
                raise GeodesyError(f"{name} must be finite, got {value!r}")

    def as_array(self) -> np.ndarray:
        return np.array([self.x_m, self.y_m, self.z_m], dtype=float)


def _normalize_longitude(lon_deg: float) -> float:
    """Fold longitude into (-180, 180]; both +/-180 map to +180 (dateline)."""
    lon = math.remainder(lon_deg, 360.0)  # -> [-180, 180]
    if lon <= -180.0:
        lon += 360.0
    return lon


def prime_vertical_radius(latitude_deg: float) -> float:
    """Radius of curvature in the prime vertical, N(phi), in metres."""
    sin_lat = math.sin(math.radians(latitude_deg))
    return WGS84_A / math.sqrt(1.0 - WGS84_E2 * sin_lat * sin_lat)


def geodetic_to_ecef(
    latitude_deg: float, longitude_deg: float, height_m: float,
) -> Tuple[float, float, float]:
    """Closed-form WGS84 geodetic -> ECEF. Returns (x, y, z) in metres."""
    point = GeodeticPoint(latitude_deg, longitude_deg, height_m)
    lat = math.radians(point.latitude_deg)
    lon = math.radians(point.longitude_deg)
    sin_lat, cos_lat = math.sin(lat), math.cos(lat)
    sin_lon, cos_lon = math.sin(lon), math.cos(lon)
    n = WGS84_A / math.sqrt(1.0 - WGS84_E2 * sin_lat * sin_lat)
    x = (n + point.height_m) * cos_lat * cos_lon
    y = (n + point.height_m) * cos_lat * sin_lon
    z = (n * (1.0 - WGS84_E2) + point.height_m) * sin_lat
    return (x, y, z)


def ecef_to_geodetic(
    x_m: float, y_m: float, z_m: float,
) -> Tuple[float, float, float]:
    """WGS84 ECEF -> geodetic. Returns (lat_deg, lon_deg, height_m).

    Uses a Bowring seed refined by fixed-point iteration. Stable at the
    poles (where longitude is conventionally 0) and for negative heights.
    The exact geocentre is underdetermined and raises :class:`GeodesyError`.
    """
    for name, value in (("x_m", x_m), ("y_m", y_m), ("z_m", z_m)):
        if not math.isfinite(value):
            raise GeodesyError(f"{name} must be finite, got {value!r}")

    p = math.hypot(x_m, y_m)
    if p < 1e-9 and abs(z_m) < 1e-9:
        raise GeodesyError(
            "the exact geocentre (0, 0, 0) has no defined latitude or "
            "longitude; refusing to invent a coordinate")

    lon = math.atan2(y_m, x_m)

    # Bowring seed.
    theta = math.atan2(z_m * WGS84_A, p * WGS84_B)
    sin_t, cos_t = math.sin(theta), math.cos(theta)
    lat = math.atan2(
        z_m + WGS84_EP2 * WGS84_B * sin_t ** 3,
        p - WGS84_E2 * WGS84_A * cos_t ** 3,
    )

    # Fixed-point refinement to sub-nanometre convergence.
    for _ in range(12):
        sin_lat = math.sin(lat)
        n = WGS84_A / math.sqrt(1.0 - WGS84_E2 * sin_lat * sin_lat)
        new_lat = math.atan2(z_m, p * (1.0 - WGS84_E2 * n / (n + _height(
            p, z_m, lat, n))))
        if abs(new_lat - lat) < 1e-15:
            lat = new_lat
            break
        lat = new_lat

    sin_lat = math.sin(lat)
    n = WGS84_A / math.sqrt(1.0 - WGS84_E2 * sin_lat * sin_lat)
    height = _height(p, z_m, lat, n)
    return (math.degrees(lat), math.degrees(_normalize_lon_rad(lon)), height)


def _normalize_lon_rad(lon_rad: float) -> float:
    deg = _normalize_longitude(math.degrees(lon_rad))
    return math.radians(deg)


def _height(p: float, z: float, lat: float, n: float) -> float:
    """Height, using the numerically stable branch for the latitude band."""
    if abs(lat) < math.pi / 4.0:
        return p / math.cos(lat) - n
    return z / math.sin(lat) - n * (1.0 - WGS84_E2)


def geodetic_point_to_ecef(point: GeodeticPoint) -> EcefPoint:
    x, y, z = geodetic_to_ecef(
        point.latitude_deg, point.longitude_deg, point.height_m)
    return EcefPoint(x, y, z, crs=point.crs)


def ecef_point_to_geodetic(point: EcefPoint) -> GeodeticPoint:
    lat, lon, h = ecef_to_geodetic(point.x_m, point.y_m, point.z_m)
    return GeodeticPoint(lat, lon, h, crs=point.crs)


def geodesy_report() -> dict:
    """What this module claims -- and, deliberately, what it does not."""
    return {
        "module": "cwatlas.geodesy",
        "phase_id": "P09",
        "codec_id": CODEC_ID,
        "codec_version": CODEC_VERSION,
        "crs": CRS_ID,
        "ellipsoid": {
            "a_m": WGS84_A,
            "inv_f": WGS84_INV_F,
            "b_m": WGS84_B,
            "e2": WGS84_E2,
        },
        "height_convention": HEIGHT_CONVENTION,
        "claim_class": claims.ClaimClass.CANONICAL_ROUND_TRIP.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "round_trip_tolerance_m": 1e-6,
        "verdict": "WGS84_GEODETIC_ECEF_REVERSIBLE_ROUND_TRIP",
    }
