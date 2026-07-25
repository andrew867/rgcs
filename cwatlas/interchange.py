"""P61 -- import, export, and interchange packages.

A single :class:`InterchangeBundle` round-trips a batch of *declared* points
across five interchange forms and back to the same points:

* **JSON** -- a self-describing package (provenance + fully typed points). The
  lossless canonical form.
* **GeoJSON** -- an RFC 7946 ``FeatureCollection`` of ``Point`` features
  (reuses :mod:`cwatlas.io_geo`).
* **KML** -- ``<Placemark>``/``<Point>`` elements (reuses
  :mod:`cwatlas.io_geo`).
* **CSV** -- one self-describing row per point (reuses
  :func:`cwatlas.io_geo.to_csv`; a matching reader lives here).
* **CW-URI** -- one ``cw://`` link per point, each carrying its CRS + epoch
  (reuses :mod:`cwatlas.io_geo` for the CW-GEO-1 vector and
  :mod:`cwatlas.share` for the URI). Coordinate-bearing; per-point labels are
  not carried in a URI.

Every point carries its own body, frame (CRS) and epoch, so no export ever
ships a coordinate without the CRS + epoch receipt (invariant 9). Ordering is
preserved end to end. A bundle records **provenance** (source, software commit,
point count, and a content hash binding the points) and is **privacy-scanned**
on build, export, and import: a private token in any label or serialized text is
a typed refusal (:func:`cwatlas.privacy.refuse_private_in_public`). Public
fixtures are synthetic only.

Encoding a point to a CW vector reuses CW-GEO-1; the round-trip fact stays a
property of the codec.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED

Deterministic; epochs are decimal-year strings passed in. No wall-clock.
"""

from __future__ import annotations

import hashlib
import io
import json
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Sequence, Tuple

from cwatlas import claims, privacy, share
from cwatlas import io_geo
from cwatlas.address_to_vector import vector_to_address
from cwatlas.io_geo import (
    CSV_HEADER,
    DEFAULT_BODY,
    DEFAULT_FRAME,
    GeoIoError,
    TypedPoint,
)

#: Phase identity.
PHASE_ID = "P61"
TRANCHE = "T08"

#: The CW-URI namespace and codec used when exporting points as links.
_URI_NAMESPACE = "rgcs-cw-atlas"
_URI_CODEC = "CW-GEO-1"


class InterchangeError(ValueError):
    """Raised on a malformed bundle, format, or interchange package."""


class Format(Enum):
    """The interchange formats a bundle round-trips through."""

    JSON = "JSON"
    GEOJSON = "GeoJSON"
    KML = "KML"
    CSV = "CSV"
    CW_URI = "CW-URI"


#: Formats that carry per-point labels through a round-trip. CW-URI does not.
LABEL_PRESERVING = frozenset({Format.JSON, Format.GEOJSON, Format.KML, Format.CSV})


@dataclass(frozen=True)
class Provenance:
    """Provenance recorded on a bundle: what it is and what binds it.

    ``content_hash`` is a SHA-256 over the canonical JSON of the points, so a
    bundle whose points were altered no longer matches its recorded hash.
    """

    source: str
    software_commit: Optional[str]
    epoch: str
    point_count: int
    content_hash: str

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "software_commit": self.software_commit,
            "epoch": self.epoch,
            "point_count": self.point_count,
            "content_hash": self.content_hash,
        }


def _point_dict(p: TypedPoint) -> dict:
    """A fully typed, JSON-safe projection of a point (all fields explicit)."""
    return {
        "latitude_deg": p.latitude_deg,
        "longitude_deg": p.longitude_deg,
        "height_m": p.height_m,
        "body": p.body,
        "frame": p.frame,
        "epoch": p.epoch,
        "label": p.label,
    }


def _content_hash(points: Sequence[TypedPoint]) -> str:
    """A deterministic SHA-256 binding the ordered points."""
    canonical = json.dumps([_point_dict(p) for p in points],
                           sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class InterchangeBundle:
    """A privacy-scanned, provenance-stamped batch of declared points."""

    points: Tuple[TypedPoint, ...]
    provenance: Provenance

    def __len__(self) -> int:
        return len(self.points)

    def to_vectors(self) -> List[str]:
        """Encode the points to CW-GEO-1 vectors (reuses :mod:`cwatlas.io_geo`)."""
        return io_geo.points_to_vectors(self.points)

    def to_dict(self) -> dict:
        return {
            "what_this_is": "a CW Atlas interchange bundle of declared points",
            "provenance": self.provenance.to_dict(),
            "points": [_point_dict(p) for p in self.points],
            "claim_class": claims.ClaimClass.MATHEMATICAL_TRANSLATION.value,
            "measured_here": "nothing",
            "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
            "source_vector_geographic_semantics": "NOT_CLAIMED",
        }

    def verify_content_hash(self) -> bool:
        """``True`` iff the recorded content hash still binds the points."""
        return self.provenance.content_hash == _content_hash(self.points)


def build_bundle(
    points: Sequence[TypedPoint],
    *,
    source: str = "synthetic",
    software_commit: Optional[str] = None,
    epoch: str = "2020.0",
) -> InterchangeBundle:
    """Assemble a provenance-stamped, privacy-scanned interchange bundle.

    Each point's label is privacy-scanned at :class:`~cwatlas.io_geo.TypedPoint`
    construction; the bundle re-scans defensively and records provenance binding
    the ordered points.
    """
    if not isinstance(points, (list, tuple)) or not points:
        raise InterchangeError("a bundle needs a non-empty sequence of points")
    pts: List[TypedPoint] = []
    for i, p in enumerate(points):
        if not isinstance(p, TypedPoint):
            raise InterchangeError(f"point {i} must be a TypedPoint")
        if p.label is not None:
            privacy.refuse_private_in_public(str(p.label))
        pts.append(p)
    provenance = Provenance(
        source=source,
        software_commit=software_commit,
        epoch=epoch,
        point_count=len(pts),
        content_hash=_content_hash(pts),
    )
    return InterchangeBundle(points=tuple(pts), provenance=provenance)


# --- export -----------------------------------------------------------------

def _export_json(bundle: InterchangeBundle) -> str:
    text = json.dumps(bundle.to_dict(), sort_keys=True, separators=(",", ":"))
    privacy.refuse_private_in_public(text)
    return text


def _export_cw_uri(bundle: InterchangeBundle) -> str:
    vectors = bundle.to_vectors()
    lines = []
    for p, vec in zip(bundle.points, vectors):
        uri = share.CwUri(
            namespace=_URI_NAMESPACE,
            codec=_URI_CODEC,
            vector=vec,
            frame=p.frame,
            epoch=p.epoch,
        )
        lines.append(share.format_cw_uri(uri))  # privacy-scans each URI
    text = "\n".join(lines)
    privacy.refuse_private_in_public(text)
    return text


def export_package(bundle: InterchangeBundle, fmt: Format) -> str:
    """Serialize a bundle to one interchange format (privacy-scanned text)."""
    if not isinstance(bundle, InterchangeBundle):
        raise InterchangeError("expected an InterchangeBundle")
    if not isinstance(fmt, Format):
        raise InterchangeError(f"fmt must be a Format, got {fmt!r}")
    if fmt is Format.JSON:
        return _export_json(bundle)
    if fmt is Format.GEOJSON:
        return io_geo.to_geojson(bundle.points, as_text=True)
    if fmt is Format.KML:
        return io_geo.to_kml(bundle.points)
    if fmt is Format.CSV:
        return io_geo.to_csv(bundle.points)
    if fmt is Format.CW_URI:
        return _export_cw_uri(bundle)
    raise InterchangeError(f"unsupported format {fmt!r}")  # pragma: no cover


# --- import -----------------------------------------------------------------

def _import_json(text: str) -> Tuple[List[TypedPoint], Optional[dict]]:
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError) as exc:
        raise InterchangeError(f"malformed interchange JSON: {exc}") from exc
    if not isinstance(data, dict) or "points" not in data:
        raise InterchangeError("interchange JSON must be an object with 'points'")
    raw_points = data.get("points")
    if not isinstance(raw_points, list):
        raise InterchangeError("interchange JSON 'points' must be a list")
    points: List[TypedPoint] = []
    for i, rp in enumerate(raw_points):
        if not isinstance(rp, dict):
            raise InterchangeError(f"point {i} must be an object")
        try:
            points.append(TypedPoint(
                latitude_deg=float(rp["latitude_deg"]),
                longitude_deg=float(rp["longitude_deg"]),
                height_m=float(rp.get("height_m", 0.0)),
                body=str(rp.get("body", DEFAULT_BODY)),
                frame=str(rp.get("frame", DEFAULT_FRAME)),
                epoch=str(rp.get("epoch", "2020.0")),
                label=rp.get("label"),
            ))
        except (KeyError, GeoIoError, ValueError) as exc:
            raise InterchangeError(f"point {i} is malformed: {exc}") from exc
    return points, data.get("provenance")


def _import_csv(text: str, *, body: str, frame: str, epoch: str
                ) -> List[TypedPoint]:
    import csv
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        raise InterchangeError("CSV is empty")
    header = tuple(rows[0])
    if header != CSV_HEADER:
        raise InterchangeError(
            f"CSV header must be {list(CSV_HEADER)}, got {list(header)}")
    idx = {name: i for i, name in enumerate(CSV_HEADER)}
    points: List[TypedPoint] = []
    for r, row in enumerate(rows[1:], start=1):
        if not row:
            continue
        if len(row) != len(CSV_HEADER):
            raise InterchangeError(f"CSV row {r} has {len(row)} fields")
        try:
            label = row[idx["label"]]
            points.append(TypedPoint(
                latitude_deg=float(row[idx["latitude_deg"]]),
                longitude_deg=float(row[idx["longitude_deg"]]),
                height_m=float(row[idx["height_m"]]),
                body=row[idx["body"]] or body,
                frame=row[idx["frame"]] or frame,
                epoch=row[idx["epoch"]] or epoch,
                label=label if label != "" else None,
            ))
        except (GeoIoError, ValueError) as exc:
            raise InterchangeError(f"CSV row {r} is malformed: {exc}") from exc
    return points


def _import_cw_uri(text: str, *, body: str) -> List[TypedPoint]:
    points: List[TypedPoint] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            uri = share.parse_cw_uri(line)
            address = vector_to_address(uri.vector)
        except Exception as exc:  # ShareError, AddressVectorError, ...
            raise InterchangeError(f"malformed CW-URI: {exc}") from exc
        points.append(TypedPoint(
            latitude_deg=address.latitude_deg,
            longitude_deg=address.longitude_deg,
            height_m=0.0 if address.height_m is None else address.height_m,
            body=address.body_id,
            frame=uri.frame,
            epoch=uri.epoch,
            label=None,
        ))
    return points


def import_package(
    text: str,
    fmt: Format,
    *,
    body: str = DEFAULT_BODY,
    frame: str = DEFAULT_FRAME,
    epoch: str = "2020.0",
    source: str = "imported",
    software_commit: Optional[str] = None,
) -> InterchangeBundle:
    """Parse an interchange package back into a privacy-scanned bundle.

    ``body``/``frame``/``epoch`` supply the CRS + epoch for formats that do not
    carry them per-point (KML, CW-URI). Malformed input is a typed refusal, and
    the raw text is privacy-scanned before parsing so a private token can never
    enter a bundle.
    """
    if not isinstance(text, str):
        raise InterchangeError("interchange text must be a string")
    if not isinstance(fmt, Format):
        raise InterchangeError(f"fmt must be a Format, got {fmt!r}")
    privacy.refuse_private_in_public(text)

    if fmt is Format.JSON:
        points, _prov = _import_json(text)
    elif fmt is Format.GEOJSON:
        try:
            points = io_geo.parse_geojson(text, body=body, frame=frame, epoch=epoch)
        except GeoIoError as exc:
            raise InterchangeError(str(exc)) from exc
    elif fmt is Format.KML:
        try:
            points = io_geo.parse_kml(text, body=body, frame=frame, epoch=epoch)
        except GeoIoError as exc:
            raise InterchangeError(str(exc)) from exc
    elif fmt is Format.CSV:
        points = _import_csv(text, body=body, frame=frame, epoch=epoch)
    elif fmt is Format.CW_URI:
        points = _import_cw_uri(text, body=body)
    else:  # pragma: no cover
        raise InterchangeError(f"unsupported format {fmt!r}")

    if not points:
        raise InterchangeError("interchange package contained no points")
    return build_bundle(points, source=source, software_commit=software_commit,
                        epoch=epoch)


def round_trip(
    bundle: InterchangeBundle,
    fmt: Format,
    *,
    software_commit: Optional[str] = None,
) -> InterchangeBundle:
    """Export a bundle to ``fmt`` and import it back (a round-trip helper).

    For a label-preserving format the imported points equal the originals
    field-for-field. CW-URI preserves coordinates + CRS + epoch but not labels.
    """
    text = export_package(bundle, fmt)
    # KML / CW-URI need the batch CRS + epoch supplied on import.
    body = bundle.points[0].body
    frame = bundle.points[0].frame
    epoch = bundle.points[0].epoch
    return import_package(text, fmt, body=body, frame=frame, epoch=epoch,
                          source="round_trip", software_commit=software_commit)


def points_equal(a: Sequence[TypedPoint], b: Sequence[TypedPoint],
                 *, compare_labels: bool = True) -> bool:
    """Structural equality over ordered points (labels optionally ignored)."""
    if len(a) != len(b):
        return False
    for pa, pb in zip(a, b):
        if (pa.latitude_deg != pb.latitude_deg
                or pa.longitude_deg != pb.longitude_deg
                or pa.height_m != pb.height_m
                or pa.body != pb.body
                or pa.frame != pb.frame
                or pa.epoch != pb.epoch):
            return False
        if compare_labels and pa.label != pb.label:
            return False
    return True


def interchange_report() -> dict:
    """P61 declaration receipt. What the interchange layer is -- and is not."""
    return {
        "module": "cwatlas.interchange",
        "phase_id": PHASE_ID,
        "tranche": TRANCHE,
        "formats": [f.value for f in Format],
        "label_preserving_formats": sorted(f.value for f in LABEL_PRESERVING),
        "crs_epoch_carried": True,
        "provenance_recorded": True,
        "privacy_scanned": True,
        "pure_python": True,
        "claim_class": claims.ClaimClass.MATHEMATICAL_TRANSLATION.value,
        "level": "SOFTWARE",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "CW_ATLAS_INTERCHANGE_BUNDLE_ROUND_TRIP_PROVENANCE_NO_PRIVATE",
        "what_this_does_not_say": (
            "An interchange bundle moves declared points between formats and "
            "re-expresses them as CW vectors. It attaches no geographic meaning "
            "to any operator-reported source vector and embeds no private data."),
    }
