"""P38 -- Batch GeoJSON / KML import and export of points.

A pure-Python (no shapely, no GDAL) importer/exporter that moves a batch of
*declared* points between three interchange formats and the CW address stack:

* **GeoJSON** -- a ``FeatureCollection`` of ``Point`` features. Coordinates are
  ``[longitude, latitude, height?]`` (RFC 7946 axis order, CRS84 by default).
* **KML** -- a set of ``<Placemark>`` elements each with a ``<Point>`` whose
  ``<coordinates>`` are ``lon,lat[,alt]``.
* **CSV** -- one row per point with an explicit, self-describing header.

Every point is typed as a :class:`TypedPoint` carrying its own ``body``,
``frame`` (CRS) and ``epoch``, so no export ever ships a coordinate without the
CRS + epoch receipt (System Contract invariant 9). Ordering is preserved
end-to-end, so ``points -> GeoJSON -> points`` is a byte-stable round-trip.

Malformed input -- bad JSON/XML, a non-Point geometry, missing or non-finite
coordinates, a missing CRS/epoch -- is a typed :class:`GeoIoError`, never a
silent guess. Private tokens in any label are refused via
:func:`cwatlas.privacy.refuse_private_in_public`.

Encoding a point to a CW vector reuses CW-GEO-1 (:mod:`cwatlas.codec_geo1`); the
round-trip fact remains a property of the codec.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED
"""

from __future__ import annotations

import io
import json
import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence

from cwatlas import claims, privacy
from cwatlas.canonical import CanonicalCoordinate
from cwatlas.codec_geo1 import CWGeo1Codec

MODULE_PHASE = "P38"

#: Default CRS for GeoJSON per RFC 7946 (WGS84 lon/lat). Recorded explicitly on
#: every point so nothing relies on a hidden default.
DEFAULT_FRAME = "CRS84"
DEFAULT_BODY = "EARTH"

#: KML documents live in this XML namespace; parsing tolerates its presence or
#: absence (some exporters omit it).
_KML_NS = "http://www.opengis.net/kml/2.2"


class GeoIoError(ValueError):
    """Raised on malformed GeoJSON/KML/CSV or an underdetermined point."""


@dataclass(frozen=True)
class TypedPoint:
    """A declared point carrying its own CRS + epoch receipt.

    ``label`` is an optional synthetic name; it is privacy-scanned on
    construction so a private token can never enter an export.
    """

    latitude_deg: float
    longitude_deg: float
    body: str = DEFAULT_BODY
    frame: str = DEFAULT_FRAME
    epoch: str = "2020.0"
    height_m: float = 0.0
    label: Optional[str] = None

    def __post_init__(self) -> None:
        for name, value in (
            ("latitude_deg", self.latitude_deg),
            ("longitude_deg", self.longitude_deg),
            ("height_m", self.height_m),
        ):
            if not isinstance(value, (int, float)) or not math.isfinite(value):
                raise GeoIoError(f"{name} must be finite, got {value!r}")
        if not (-90.0 <= self.latitude_deg <= 90.0):
            raise GeoIoError(
                f"latitude_deg must be in [-90, 90], got {self.latitude_deg!r}")
        if not (-180.0 <= self.longitude_deg <= 180.0):
            raise GeoIoError(
                f"longitude_deg must be in [-180, 180], got "
                f"{self.longitude_deg!r}")
        if not self.body or not self.frame or not self.epoch:
            raise GeoIoError(
                "a point must declare a non-empty body, frame (CRS), and epoch")
        if self.label is not None:
            privacy.refuse_private_in_public(str(self.label))

    def to_coordinate(self) -> CanonicalCoordinate:
        """Project to a :class:`CanonicalCoordinate` (frame + epoch enforced)."""
        return CanonicalCoordinate(
            body_id=self.body,
            frame_id=self.frame,
            epoch=self.epoch,
            latitude_deg=self.latitude_deg,
            longitude_deg=self.longitude_deg,
            height_m=self.height_m,
        )


def _finite_number(value, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise GeoIoError(f"{name} must be a number, got {value!r}")
    f = float(value)
    if not math.isfinite(f):
        raise GeoIoError(f"{name} must be finite, got {value!r}")
    return f


# --- GeoJSON ----------------------------------------------------------------

def parse_geojson(
    source, *, body: str = DEFAULT_BODY, frame: str = DEFAULT_FRAME,
    epoch: str = "2020.0",
) -> List[TypedPoint]:
    """Parse a GeoJSON ``FeatureCollection`` of ``Point`` features.

    ``source`` may be a JSON string or an already-parsed mapping. Per-feature
    ``properties`` may override ``body``/``frame``/``epoch``/``label``; otherwise
    the batch defaults apply. Any non-Point geometry or malformed structure is
    a refusal.
    """
    if isinstance(source, (dict,)):
        data = source
    else:
        if not isinstance(source, str):
            raise GeoIoError("GeoJSON source must be a str or a mapping")
        try:
            data = json.loads(source)
        except (json.JSONDecodeError, ValueError) as exc:
            raise GeoIoError(f"malformed GeoJSON: {exc}") from exc
    if not isinstance(data, dict) or data.get("type") != "FeatureCollection":
        raise GeoIoError("GeoJSON root must be a FeatureCollection")
    features = data.get("features")
    if not isinstance(features, list):
        raise GeoIoError("FeatureCollection.features must be a list")
    points: List[TypedPoint] = []
    for i, feat in enumerate(features):
        if not isinstance(feat, dict) or feat.get("type") != "Feature":
            raise GeoIoError(f"feature {i} is not a GeoJSON Feature")
        geom = feat.get("geometry")
        if not isinstance(geom, dict):
            raise GeoIoError(f"feature {i} has no geometry object")
        if geom.get("type") != "Point":
            raise GeoIoError(
                f"feature {i} geometry is {geom.get('type')!r}; only Point is "
                f"supported by this importer")
        coords = geom.get("coordinates")
        if not isinstance(coords, (list, tuple)) or len(coords) < 2:
            raise GeoIoError(f"feature {i} Point needs [lon, lat] coordinates")
        lon = _finite_number(coords[0], f"feature {i} longitude")
        lat = _finite_number(coords[1], f"feature {i} latitude")
        height = _finite_number(coords[2], f"feature {i} height") \
            if len(coords) >= 3 else 0.0
        props = feat.get("properties") or {}
        if not isinstance(props, dict):
            raise GeoIoError(f"feature {i} properties must be an object")
        points.append(TypedPoint(
            latitude_deg=lat,
            longitude_deg=lon,
            height_m=height,
            body=str(props.get("body", body)),
            frame=str(props.get("frame", frame)),
            epoch=str(props.get("epoch", epoch)),
            label=props.get("name"),
        ))
    return points


def to_geojson(points: Sequence[TypedPoint], *, as_text: bool = False):
    """Export points to a GeoJSON ``FeatureCollection`` (dict or JSON text).

    Each feature records ``body``, ``frame`` (CRS), and ``epoch`` in its
    properties, so the CRS + epoch receipt travels with every point. Output is
    privacy-scanned before it is returned.
    """
    features = []
    for p in points:
        coords = [p.longitude_deg, p.latitude_deg]
        if p.height_m:
            coords.append(p.height_m)
        props = {"body": p.body, "frame": p.frame, "epoch": p.epoch}
        if p.label is not None:
            props["name"] = p.label
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": coords},
            "properties": props,
        })
    fc = {"type": "FeatureCollection", "features": features}
    text = json.dumps(fc, sort_keys=True, separators=(",", ":"))
    privacy.refuse_private_in_public(text)
    return text if as_text else fc


# --- KML --------------------------------------------------------------------

def _localname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_kml(
    source: str, *, body: str = DEFAULT_BODY, frame: str = DEFAULT_FRAME,
    epoch: str = "2020.0",
) -> List[TypedPoint]:
    """Parse a KML document's ``<Placemark>``/``<Point>`` set into points.

    KML ``<coordinates>`` are ``lon,lat[,alt]``. A Placemark with no Point, or
    malformed coordinates, is a refusal. Tolerant of the KML XML namespace
    being present or omitted.
    """
    if not isinstance(source, str):
        raise GeoIoError("KML source must be a string")
    try:
        root = ET.fromstring(source)
    except ET.ParseError as exc:
        raise GeoIoError(f"malformed KML XML: {exc}") from exc
    placemarks = [el for el in root.iter() if _localname(el.tag) == "Placemark"]
    if not placemarks:
        raise GeoIoError("KML contains no Placemark elements")
    points: List[TypedPoint] = []
    for i, pm in enumerate(placemarks):
        point_el = next(
            (el for el in pm.iter() if _localname(el.tag) == "Point"), None)
        if point_el is None:
            raise GeoIoError(f"Placemark {i} has no Point geometry")
        coord_el = next(
            (el for el in point_el.iter()
             if _localname(el.tag) == "coordinates"), None)
        if coord_el is None or not (coord_el.text or "").strip():
            raise GeoIoError(f"Placemark {i} Point has no coordinates")
        tokens = coord_el.text.strip().split(",")
        if len(tokens) < 2:
            raise GeoIoError(
                f"Placemark {i} coordinates must be 'lon,lat[,alt]'")
        try:
            lon = _finite_number(float(tokens[0]), f"Placemark {i} longitude")
            lat = _finite_number(float(tokens[1]), f"Placemark {i} latitude")
            height = _finite_number(float(tokens[2]), f"Placemark {i} height") \
                if len(tokens) >= 3 and tokens[2] != "" else 0.0
        except ValueError as exc:
            raise GeoIoError(
                f"Placemark {i} has non-numeric coordinates: {exc}") from exc
        name_el = next(
            (el for el in pm if _localname(el.tag) == "name"), None)
        label = (name_el.text.strip()
                 if name_el is not None and name_el.text else None)
        points.append(TypedPoint(
            latitude_deg=lat, longitude_deg=lon, height_m=height,
            body=body, frame=frame, epoch=epoch, label=label))
    return points


def to_kml(points: Sequence[TypedPoint]) -> str:
    """Export points to a KML document string (privacy-scanned)."""
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<kml xmlns="{_KML_NS}"><Document>',
    ]
    for p in points:
        alt = p.height_m
        coord = f"{p.longitude_deg!r},{p.latitude_deg!r},{alt!r}"
        name = f"<name>{p.label}</name>" if p.label is not None else ""
        desc = (f"<description>body={p.body};frame={p.frame};"
                f"epoch={p.epoch}</description>")
        parts.append(
            f"<Placemark>{name}{desc}<Point>"
            f"<coordinates>{coord}</coordinates></Point></Placemark>")
    parts.append("</Document></kml>")
    text = "".join(parts)
    privacy.refuse_private_in_public(text)
    return text


# --- CSV --------------------------------------------------------------------

CSV_HEADER = ("latitude_deg", "longitude_deg", "height_m", "body", "frame",
              "epoch", "label")


def to_csv(points: Sequence[TypedPoint]) -> str:
    """Export points to CSV with an explicit, self-describing header.

    Uses :mod:`csv` for correct quoting. Every row carries the CRS + epoch.
    """
    import csv
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(CSV_HEADER)
    for p in points:
        writer.writerow([
            repr(p.latitude_deg), repr(p.longitude_deg), repr(p.height_m),
            p.body, p.frame, p.epoch, "" if p.label is None else p.label,
        ])
    text = buf.getvalue()
    privacy.refuse_private_in_public(text)
    return text


# --- CW vector encoding -----------------------------------------------------

def points_to_vectors(
    points: Iterable[TypedPoint], *, codec: Optional[CWGeo1Codec] = None,
) -> List[str]:
    """Encode each point to a CW-GEO-1 vector, preserving order.

    A batch bridge from imported geometry to the canonical codec. The result is
    a ``CANONICAL_ROUND_TRIP`` fact about CW-GEO-1, nothing more.
    """
    codec = codec or CWGeo1Codec()
    return [codec.encode(p.to_coordinate()) for p in points]


def io_geo_report() -> dict:
    """Governance report: what this module is and, emphatically, is not."""
    return {
        "module": "cwatlas.io_geo",
        "phase_id": MODULE_PHASE,
        "formats": ["GeoJSON", "KML", "CSV"],
        "geometry_supported": "Point",
        "default_frame": DEFAULT_FRAME,
        "default_body": DEFAULT_BODY,
        "crs_epoch_carried": True,
        "pure_python": True,
        "claim_class": claims.ClaimClass.MATHEMATICAL_TRANSLATION.value,
        "level": "SOFTWARE",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "CW_ATLAS_IO_GEO_POINT_ROUND_TRIP_CRS_EPOCH_CARRIED",
        "what_this_does_not_say": (
            "Importing a point from GeoJSON or KML and encoding it with "
            "CW-GEO-1 is a coordinate re-expression. It attaches no geographic "
            "meaning to any operator-reported source vector."),
    }
