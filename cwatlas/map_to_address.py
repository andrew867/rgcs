"""P33 -- Map/globe click to a frame-and-epoch-certified geospatial address.

This is the entry point of the forward geocoder (map -> vector). A click on a
map or globe is turned into a typed :class:`GeospatialAddress` conforming to
``geospatial_address.schema.json`` and carrying every field the architecture
requires to be explicit: the body, the coordinate-reference-system (frame),
and the epoch. Two click forms are supported:

* a **direct** geodetic click -- the operator (or an interactive globe) already
  resolved the click to a ``(latitude, longitude)`` on a named body; and
* a **pixel** click on an equirectangular viewport -- a pixel plus the
  viewport's declared geographic extent is projected to a ``(lat, lon)``.

The governance rule that shapes the design (System Contract invariant 9):
**a pin/address may not exist without a declared CRS and an epoch.** An address
built without a frame or an epoch is a typed refusal
(:func:`cwatlas.claims.refuse_pin_without_crs_epoch`), never a silent guess. No
hidden defaults: the uncertainty of a direct click is a required, explicit
input; the uncertainty of a pixel click is computed from the pixel footprint,
not invented.

Producing a typed address asserts nothing geographic about any source vector.
Turning a click into a coordinate is arithmetic on a *declared* convention.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED

Nothing here reads a wall-clock; the epoch is a decimal-year string passed in.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from cwatlas import claims
from cwatlas.mars_frame import BODIES, FrameError, get_body

#: Phase identity.
PHASE_ID = "P33"
TRANCHE = "T05"


class MapClickError(ValueError):
    """Raised on an invalid click, viewport, or under-specified address."""


def _normalize_longitude(lon_deg: float) -> float:
    """Fold longitude into (-180, 180]; both +/-180 map to +180 (dateline).

    Matches :func:`cwatlas.geodesy._normalize_longitude` so the map stack and
    the geodesy core agree on the dateline convention.
    """
    lon = math.remainder(float(lon_deg), 360.0)
    if lon <= -180.0:
        lon += 360.0
    return lon


@dataclass(frozen=True)
class GeospatialAddress:
    """A typed, frame-and-epoch-certified address (``geospatial_address.schema``).

    ``frame_id`` (the CRS) and ``epoch`` are both mandatory: an address that
    cannot name its CRS and epoch is refused at construction (invariant 9).
    ``coordinate_convention`` defaults to the frame id when not given, an
    explicit echo -- not a hidden assumption.
    """

    body_id: str
    frame_id: str
    epoch: str
    latitude_deg: float
    longitude_deg: float
    uncertainty_m: float
    height_m: Optional[float] = None
    shell_state: Optional[int] = None
    coordinate_convention: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.body_id:
            raise MapClickError("body_id must be a non-empty string")
        # Validate the body is a declared reference body (EARTH / MARS).
        try:
            get_body(self.body_id)
        except FrameError as exc:
            raise MapClickError(str(exc)) from exc
        # Invariant 9: no address without a declared CRS (frame) and epoch.
        claims.refuse_pin_without_crs_epoch(
            crs=self.frame_id, epoch=(self.epoch or None))
        for name, value in (
            ("latitude_deg", self.latitude_deg),
            ("longitude_deg", self.longitude_deg),
            ("uncertainty_m", self.uncertainty_m),
        ):
            if not isinstance(value, (int, float)) or not math.isfinite(value):
                raise MapClickError(f"{name} must be finite, got {value!r}")
        if not (-90.0 <= self.latitude_deg <= 90.0):
            raise MapClickError(
                f"latitude_deg must be in [-90, 90], got {self.latitude_deg!r}")
        if self.uncertainty_m < 0.0:
            raise MapClickError(
                f"uncertainty_m must be non-negative, got {self.uncertainty_m!r}")
        object.__setattr__(
            self, "latitude_deg", float(self.latitude_deg))
        object.__setattr__(
            self, "longitude_deg", _normalize_longitude(self.longitude_deg))
        object.__setattr__(self, "uncertainty_m", float(self.uncertainty_m))
        if self.height_m is not None:
            if not math.isfinite(float(self.height_m)):
                raise MapClickError(
                    f"height_m must be finite or None, got {self.height_m!r}")
            object.__setattr__(self, "height_m", float(self.height_m))
        if self.shell_state is not None:
            if not isinstance(self.shell_state, int) or isinstance(
                    self.shell_state, bool):
                raise MapClickError(
                    f"shell_state must be an int or None, got "
                    f"{self.shell_state!r}")
            if not (0 <= self.shell_state <= 8):
                raise MapClickError(
                    f"shell_state must be in [0, 8], got {self.shell_state!r}")
        if self.coordinate_convention is None:
            object.__setattr__(self, "coordinate_convention", self.frame_id)

    def to_dict(self) -> dict:
        """Project to a ``geospatial_address.schema.json``-conforming mapping."""
        return {
            "body_id": self.body_id,
            "frame_id": self.frame_id,
            "epoch": self.epoch,
            "latitude_deg": self.latitude_deg,
            "longitude_deg": self.longitude_deg,
            "height_m": self.height_m,
            "shell_state": self.shell_state,
            "uncertainty_m": self.uncertainty_m,
            "coordinate_convention": self.coordinate_convention,
        }


@dataclass(frozen=True)
class Viewport:
    """A declared equirectangular map viewport, for pixel -> lon/lat clicks.

    The viewport spans a rectangular geographic extent; the top-left pixel
    ``(0, 0)`` maps to ``(lat_max, lon_min)`` and pixel ``(width, height)`` to
    ``(lat_min, lon_max)``, the usual screen convention (y grows downward). The
    extent is a *declared* projection of the display, not a measurement.
    """

    width_px: int
    height_px: int
    lon_min_deg: float
    lon_max_deg: float
    lat_min_deg: float
    lat_max_deg: float

    def __post_init__(self) -> None:
        for name in ("width_px", "height_px"):
            v = getattr(self, name)
            if not isinstance(v, int) or isinstance(v, bool) or v <= 0:
                raise MapClickError(f"{name} must be a positive int, got {v!r}")
        for name in ("lon_min_deg", "lon_max_deg", "lat_min_deg", "lat_max_deg"):
            v = getattr(self, name)
            if not math.isfinite(v):
                raise MapClickError(f"{name} must be finite, got {v!r}")
        if not (self.lon_min_deg < self.lon_max_deg):
            raise MapClickError("lon_min_deg must be < lon_max_deg")
        if not (self.lat_min_deg < self.lat_max_deg):
            raise MapClickError("lat_min_deg must be < lat_max_deg")
        if not (-180.0 <= self.lon_min_deg and self.lon_max_deg <= 180.0):
            raise MapClickError("longitude extent must lie within [-180, 180]")
        if not (-90.0 <= self.lat_min_deg and self.lat_max_deg <= 90.0):
            raise MapClickError("latitude extent must lie within [-90, 90]")

    @property
    def lon_span_deg(self) -> float:
        return self.lon_max_deg - self.lon_min_deg

    @property
    def lat_span_deg(self) -> float:
        return self.lat_max_deg - self.lat_min_deg

    def pixel_to_lonlat(self, px: float, py: float) -> tuple[float, float]:
        """Project a pixel ``(px, py)`` to a ``(latitude, longitude)`` in degrees.

        A pixel outside ``[0, width] x [0, height]`` is a refusal, not a
        wrapped or clamped guess.
        """
        px = float(px)
        py = float(py)
        if not (math.isfinite(px) and math.isfinite(py)):
            raise MapClickError("pixel coordinates must be finite")
        if not (0.0 <= px <= self.width_px):
            raise MapClickError(
                f"px {px} outside viewport width [0, {self.width_px}]")
        if not (0.0 <= py <= self.height_px):
            raise MapClickError(
                f"py {py} outside viewport height [0, {self.height_px}]")
        lon = self.lon_min_deg + (px / self.width_px) * self.lon_span_deg
        lat = self.lat_max_deg - (py / self.height_px) * self.lat_span_deg
        return (lat, lon)

    def lonlat_to_pixel(self, latitude_deg: float, longitude_deg: float
                        ) -> tuple[float, float]:
        """Inverse of :meth:`pixel_to_lonlat` (for round-trip verification)."""
        px = (longitude_deg - self.lon_min_deg) / self.lon_span_deg * self.width_px
        py = (self.lat_max_deg - latitude_deg) / self.lat_span_deg * self.height_px
        return (px, py)

    def pixel_footprint_m(self, latitude_deg: float, body_id: str) -> float:
        """Metres subtended by the larger of one pixel's two edges at ``latitude``.

        A computed (not invented) uncertainty floor for a pixel click: the
        ground size of a single pixel on the declared body ellipsoid.
        """
        body = get_body(body_id)
        m_per_deg_lat = math.radians(1.0) * body.semi_minor_axis_m
        m_per_deg_lon = (math.radians(1.0) * body.semi_major_axis_m
                         * math.cos(math.radians(latitude_deg)))
        dlat = self.lat_span_deg / self.height_px
        dlon = self.lon_span_deg / self.width_px
        return max(dlat * m_per_deg_lat, dlon * m_per_deg_lon)


def map_click_to_address(
    *,
    body_id: str,
    frame_id: str,
    epoch: str,
    latitude_deg: float,
    longitude_deg: float,
    uncertainty_m: float,
    height_m: Optional[float] = None,
    shell_state: Optional[int] = None,
    coordinate_convention: Optional[str] = None,
) -> GeospatialAddress:
    """Turn a direct geodetic click into a typed :class:`GeospatialAddress`.

    ``frame_id`` (CRS) and ``epoch`` are mandatory; ``uncertainty_m`` is a
    required explicit input (no hidden precision default). An address that
    cannot name its CRS and epoch is refused (invariant 9).
    """
    return GeospatialAddress(
        body_id=body_id,
        frame_id=frame_id,
        epoch=epoch,
        latitude_deg=latitude_deg,
        longitude_deg=longitude_deg,
        uncertainty_m=uncertainty_m,
        height_m=height_m,
        shell_state=shell_state,
        coordinate_convention=coordinate_convention,
    )


def pixel_click_to_address(
    viewport: Viewport,
    px: float,
    py: float,
    *,
    body_id: str,
    frame_id: str,
    epoch: str,
    height_m: Optional[float] = None,
    shell_state: Optional[int] = None,
    uncertainty_m: Optional[float] = None,
    coordinate_convention: Optional[str] = None,
) -> GeospatialAddress:
    """Project a pixel click through ``viewport`` into a :class:`GeospatialAddress`.

    When ``uncertainty_m`` is not supplied it is *computed* from the pixel
    footprint on the declared body -- a derived value, not a hidden default.
    """
    if not isinstance(viewport, Viewport):
        raise MapClickError("viewport must be a Viewport")
    latitude_deg, longitude_deg = viewport.pixel_to_lonlat(px, py)
    if uncertainty_m is None:
        uncertainty_m = viewport.pixel_footprint_m(latitude_deg, body_id)
    return map_click_to_address(
        body_id=body_id,
        frame_id=frame_id,
        epoch=epoch,
        latitude_deg=latitude_deg,
        longitude_deg=longitude_deg,
        uncertainty_m=uncertainty_m,
        height_m=height_m,
        shell_state=shell_state,
        coordinate_convention=coordinate_convention,
    )


def map_to_address_report() -> dict:
    """What this module claims -- and, deliberately, what it does not."""
    return {
        "module": "cwatlas.map_to_address",
        "phase_id": PHASE_ID,
        "tranche": TRANCHE,
        "bodies": sorted(BODIES),
        "click_forms": ["direct_geodetic", "pixel_equirectangular"],
        "crs_and_epoch_required": True,
        "hidden_defaults": "none (uncertainty is explicit or computed)",
        "claim_class": claims.ClaimClass.CANONICAL_ROUND_TRIP.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "MAP_CLICK_TO_GEOSPATIAL_ADDRESS_CRS_EPOCH_CERTIFIED",
        "what_this_does_not_say": (
            "A typed geospatial address is a declared coordinate carrying its "
            "CRS and epoch. Building one asserts nothing geographic about any "
            "operator-reported source vector."),
    }
