"""P02 — body-specific planetary magnetic roots, and the refusal of a
universal anomaly circle.

A magnetic "root" is a candidate origin point for an address frame,
chosen from a body's magnetic field. The whole discipline of this module
is that such a root is **BODY-SPECIFIC** and **EPOCH-SPECIFIC**, and that
neither adjective is decorative.

**Body-specific.** The six bodies modelled here do not share one physics.
Earth has an active core dynamo with crustal anomalies on top of it; Mars
has no current global dynamo at all, only strong remanent magnetisation
frozen into ancient southern crust; the Moon likewise has no global field
and only localised crustal anomalies; Jupiter has a strongly multipolar
dynamo with no solid surface to stand on; Mercury has a weak,
north-offset intrinsic field; Venus has no intrinsic global field, only
an induced interaction with the solar wind. A construction rule that
means "the dynamo's strongest radial expression" on Earth means
"whichever patch of old crust happens to be most magnetised" on Mars.
Carrying the Earth recipe across is not generalisation, it is equivocation,
and :func:`refuse_earth_method_on_non_dynamo_body` refuses it. There is
**no verified universal anomaly circle** — no demonstrated ring, of any
radius, that appears on every body's field and could serve as a shared
origin. That claim is carried here as ``UNSUPPORTED``, not as a premise.

**Epoch-specific.** Every one of these fields moves. Earth's dip poles
migrate and its non-dipole field drifts; Jupiter's Great Blue Spot is a
travelling feature; crustal remanence is fixed to the rock but the model
that describes it has a data epoch and an error budget. **A root that
drifts cannot be a timeless address.** So a certificate with no
``magnetic_model_epoch``, or one whose feature is known to drift, is
refused the word "timeless" by :func:`refuse_timeless_root`. What this
module will certify is an *epoch-bound* address: valid for a stated
model, at a stated epoch, with a stated uncertainty, and no longer.

Two further disciplines are enforced because they are the usual way this
kind of work goes wrong. A fitted contour may **not** be called a circle
until it passes a preregistered circularity test (:func:`circularity`,
with a tolerance fixed before any data is seen), and the construction
method may **not** be picked after looking at the target
(:func:`refuse_target_dependent_selection`) — choosing the rule that
lands nearest the answer you wanted is the look-elsewhere sin, not a
result.

Seven competing constructions are implemented and dispatched side by
side, including a **null control** (method 7) that builds a root from the
spin axis and prime meridian alone, using no magnetic data whatsoever.
If a magnetic construction cannot beat that, the magnetism was not doing
the work.

Nothing here is measured. The body parameters are conventional
literature knowledge (``ESTABLISHED_SOURCE``); the constructions are
``ANALYTIC_MODEL`` evaluated on synthetic or supplied grids; real
spherical-harmonic coefficient sets are a declared
``BLOCKED_MISSING_DATA`` receipt. No root is asserted to be physical.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

import numpy as np


class PlanetRootError(RuntimeError):
    """Raised on a malformed root construction or a refused overclaim."""


# --- typed evidence vocabulary -----------------------------------------

class ScientificType(Enum):
    """How a statement in this module is entitled to be believed."""

    ESTABLISHED_SOURCE = "ESTABLISHED_SOURCE"
    DERIVED_ARITHMETIC = "DERIVED_ARITHMETIC"
    ANALYTIC_MODEL = "ANALYTIC_MODEL"
    NUMERICAL_SIMULATION = "NUMERICAL_SIMULATION"
    SOURCE_CLAIM = "SOURCE_CLAIM"
    CANDIDATE_HYPOTHESIS = "CANDIDATE_HYPOTHESIS"
    UNSUPPORTED = "UNSUPPORTED"
    BLOCKED_MISSING_DATA = "BLOCKED_MISSING_DATA"


#: Public neutral alias for the candidate root referenced by this work.
PLANETARY_ROOT_CANDIDATE_A = "PLANETARY_ROOT_CANDIDATE_A"


# --- field-class taxonomy ----------------------------------------------

class FieldClass(Enum):
    """What kind of magnetic field a body actually has."""

    INTRINSIC_DYNAMO_FIELD = "INTRINSIC_DYNAMO_FIELD"
    OFFSET_OR_MULTIPOLE_DYNAMO = "OFFSET_OR_MULTIPOLE_DYNAMO"
    CRUSTAL_REMANENT_FIELD = "CRUSTAL_REMANENT_FIELD"
    INDUCED_SOLAR_WIND_FIELD = "INDUCED_SOLAR_WIND_FIELD"
    NO_RESOLVED_FIELD_MODEL = "NO_RESOLVED_FIELD_MODEL"


#: Classes that have an internally generated (dynamo) global field.
DYNAMO_FIELD_CLASSES = frozenset({
    FieldClass.INTRINSIC_DYNAMO_FIELD,
    FieldClass.OFFSET_OR_MULTIPOLE_DYNAMO,
})


@dataclass(frozen=True)
class BodyFieldModel:
    """One body's field class and frame conventions, from literature."""

    body_id: str
    field_class: FieldClass
    has_global_dynamo: bool
    has_solid_surface: bool
    body_fixed_frame: str
    reference_level: str
    drifting_features: tuple[str, ...]
    evidence_class: str
    note: str

    def __post_init__(self) -> None:
        if not self.body_id:
            raise PlanetRootError("a body model requires a body_id")
        dynamo = self.field_class in DYNAMO_FIELD_CLASSES
        if dynamo != self.has_global_dynamo:
            raise PlanetRootError(
                f"{self.body_id}: field_class {self.field_class.value} and "
                f"has_global_dynamo={self.has_global_dynamo} disagree")


#: Features known from literature to move; an address built on one of
#: these is epoch-bound by construction.
KNOWN_DRIFTING_FEATURES = frozenset({
    "GREAT_BLUE_SPOT",
    "NORTH_MAGNETIC_DIP_POLE",
    "SOUTH_MAGNETIC_DIP_POLE",
    "SOUTH_ATLANTIC_ANOMALY",
    "ECCENTRIC_DIPOLE_CENTRE",
    "NON_DIPOLE_WESTWARD_DRIFT_FEATURE",
})


BODIES: dict[str, BodyFieldModel] = {
    "EARTH": BodyFieldModel(
        "EARTH", FieldClass.INTRINSIC_DYNAMO_FIELD, True, True,
        "EARTH_BODY_FIXED_IAU", "REFERENCE_ELLIPSOID",
        ("NORTH_MAGNETIC_DIP_POLE", "SOUTH_MAGNETIC_DIP_POLE",
         "SOUTH_ATLANTIC_ANOMALY", "NON_DIPOLE_WESTWARD_DRIFT_FEATURE"),
        ScientificType.ESTABLISHED_SOURCE.value,
        "active core dynamo, dominantly dipolar, with crustal anomalies "
        "superposed; strong secular variation"),
    "MARS": BodyFieldModel(
        "MARS", FieldClass.CRUSTAL_REMANENT_FIELD, False, True,
        "MARS_BODY_FIXED_IAU", "AREOID_REFERENCE_SURFACE",
        (),
        ScientificType.ESTABLISHED_SOURCE.value,
        "no current global dynamo; strong remanent magnetisation in "
        "ancient southern highland crust"),
    "MOON": BodyFieldModel(
        "MOON", FieldClass.CRUSTAL_REMANENT_FIELD, False, True,
        "MOON_BODY_FIXED_IAU", "MEAN_RADIUS_SPHERE",
        (),
        ScientificType.ESTABLISHED_SOURCE.value,
        "no global field; localised crustal magnetic anomalies only"),
    "JUPITER": BodyFieldModel(
        "JUPITER", FieldClass.OFFSET_OR_MULTIPOLE_DYNAMO, True, False,
        "JUPITER_BODY_FIXED_SYSTEM_III", "ONE_BAR_PRESSURE_LEVEL",
        ("GREAT_BLUE_SPOT",),
        ScientificType.ESTABLISHED_SOURCE.value,
        "strong, markedly multipolar dynamo; no solid surface, so the "
        "reference is a pressure level; the Great Blue Spot drifts"),
    "MERCURY": BodyFieldModel(
        "MERCURY", FieldClass.OFFSET_OR_MULTIPOLE_DYNAMO, True, True,
        "MERCURY_BODY_FIXED_IAU", "MEAN_RADIUS_SPHERE",
        ("ECCENTRIC_DIPOLE_CENTRE",),
        ScientificType.ESTABLISHED_SOURCE.value,
        "weak intrinsic field whose dipole is offset north of the "
        "planetary centre"),
    "VENUS": BodyFieldModel(
        "VENUS", FieldClass.INDUCED_SOLAR_WIND_FIELD, False, True,
        "VENUS_BODY_FIXED_IAU", "MEAN_RADIUS_SPHERE",
        (),
        ScientificType.ESTABLISHED_SOURCE.value,
        "no detected intrinsic global field; the observed magnetosphere "
        "is induced by the solar-wind interaction with the ionosphere"),
}


def unmodelled_body(body_id: str) -> BodyFieldModel:
    """A body whose field model is simply not resolved. Representable."""
    return BodyFieldModel(
        body_id, FieldClass.NO_RESOLVED_FIELD_MODEL, False, True,
        f"{body_id}_BODY_FIXED_UNDECLARED", "UNDECLARED", (),
        ScientificType.BLOCKED_MISSING_DATA.value,
        "no resolved field model; no magnetic root may be constructed")


def resolve_body(body: str | BodyFieldModel) -> BodyFieldModel:
    if isinstance(body, BodyFieldModel):
        return body
    key = str(body).upper()
    if key not in BODIES:
        raise PlanetRootError(
            f"{body!r} has no modelled field class here; use "
            f"unmodelled_body() to state NO_RESOLVED_FIELD_MODEL "
            f"explicitly rather than assuming an Earth-like field")
    return BODIES[key]


def field_class_of(body: str | BodyFieldModel) -> FieldClass:
    return resolve_body(body).field_class


# --- the root certificate ----------------------------------------------

@dataclass(frozen=True)
class PlanetaryRootCertificate:
    """Everything that must be declared before a root means anything.

    Every field is required. A root with any of these left implicit is
    not an address, it is a gesture at one.
    """

    body_id: str
    body_fixed_frame: str
    rotation_axis: tuple
    prime_meridian: str
    shape_model: str
    reference_surface_or_pressure_level: str
    magnetic_model: str
    magnetic_model_epoch: str | None
    field_class: FieldClass
    altitude: float
    scalar_or_vector_feature: str
    critical_point_or_contour_rule: str
    zero_direction: str
    handedness: str
    uncertainty: float
    temporal_stability: str


#: Declared temporal-stability vocabulary. Anything that admits motion
#: makes the certificate epoch-bound, which is the honest default.
DRIFTING_STABILITY = frozenset({
    "DRIFTS", "DRIFTS_SECULAR", "DRIFTS_UNQUANTIFIED", "UNKNOWN",
})


def certify_root(cert: PlanetaryRootCertificate) -> dict:
    """Validate a certificate as an EPOCH-BOUND address, never a timeless one."""
    if not isinstance(cert, PlanetaryRootCertificate):
        raise PlanetRootError("certify_root needs a PlanetaryRootCertificate")
    for name in ("body_id", "body_fixed_frame", "prime_meridian",
                 "shape_model", "reference_surface_or_pressure_level",
                 "magnetic_model", "scalar_or_vector_feature",
                 "critical_point_or_contour_rule", "zero_direction",
                 "temporal_stability"):
        if not getattr(cert, name):
            raise PlanetRootError(
                f"{cert.body_id or '<unnamed>'}: certificate field "
                f"{name!r} is empty; an undeclared convention is not a "
                f"default, it is a hole")
    if cert.handedness not in ("RIGHT", "LEFT"):
        raise PlanetRootError("handedness must be RIGHT or LEFT")
    if not (cert.uncertainty > 0):
        raise PlanetRootError(
            "uncertainty must be positive; a root with zero stated "
            "uncertainty is claiming an exactness nothing supports")
    axis = np.asarray(cert.rotation_axis, float)
    if axis.shape != (3,) or np.linalg.norm(axis) == 0:
        raise PlanetRootError("rotation_axis must be a non-zero 3-vector")
    if not isinstance(cert.field_class, FieldClass):
        raise PlanetRootError("field_class must be a FieldClass member")
    if cert.field_class is FieldClass.NO_RESOLVED_FIELD_MODEL:
        raise PlanetRootError(
            f"{cert.body_id}: NO_RESOLVED_FIELD_MODEL — there is no field "
            f"model to root against. BLOCKED_MISSING_DATA.")
    if not cert.magnetic_model_epoch:
        refuse_timeless_root(cert)
    if cert.scalar_or_vector_feature.upper() in KNOWN_DRIFTING_FEATURES:
        refuse_timeless_root(cert)
    if cert.temporal_stability.upper() in DRIFTING_STABILITY:
        refuse_timeless_root(cert)
    return {
        "body_id": cert.body_id,
        "field_class": cert.field_class.value,
        "magnetic_model": cert.magnetic_model,
        "epoch": cert.magnetic_model_epoch,
        "timeless": False,
        "epoch_bound": True,
        "valid_only_for": (
            f"{cert.magnetic_model} at {cert.magnetic_model_epoch}, "
            f"altitude {cert.altitude}, uncertainty {cert.uncertainty}"),
        "scientific_type": ScientificType.ANALYTIC_MODEL.value,
    }


# --- competing root constructions --------------------------------------

class RootMethod(Enum):
    """Seven competing constructions, evaluated side by side."""

    RADIAL_FIELD_EXTREMUM = 1
    HORIZONTAL_GRADIENT_EXTREMUM = 2
    STABLE_CLOSED_CONTOUR = 3
    NULL_SADDLE_NETWORK = 4
    HARMONIC_PRINCIPAL_AXIS = 5
    CRUSTAL_ANOMALY_CENTROID = 6
    SPIN_AXIS_NULL_CONTROL = 7


_ALL_CLASSES = frozenset(FieldClass) - {FieldClass.NO_RESOLVED_FIELD_MODEL}

#: Which field classes each construction is even meaningful on, plus
#: what data it consumes. Fixed here, before any target is looked at.
METHOD_SPEC: dict[RootMethod, dict] = {
    RootMethod.RADIAL_FIELD_EXTREMUM: {
        "description": "strongest radial-field extremum",
        "applicable": frozenset(DYNAMO_FIELD_CLASSES),
        "uses_magnetic_data": True,
        "is_control": False,
        "scientific_type": ScientificType.ANALYTIC_MODEL.value,
    },
    RootMethod.HORIZONTAL_GRADIENT_EXTREMUM: {
        "description": "strongest horizontal-gradient extremum",
        "applicable": frozenset(DYNAMO_FIELD_CLASSES),
        "uses_magnetic_data": True,
        "is_control": False,
        "scientific_type": ScientificType.ANALYTIC_MODEL.value,
    },
    RootMethod.STABLE_CLOSED_CONTOUR: {
        "description": "stable closed contour around an extremum",
        "applicable": frozenset(DYNAMO_FIELD_CLASSES
                                | {FieldClass.CRUSTAL_REMANENT_FIELD}),
        "uses_magnetic_data": True,
        "is_control": False,
        "scientific_type": ScientificType.ANALYTIC_MODEL.value,
    },
    RootMethod.NULL_SADDLE_NETWORK: {
        "description": "magnetic null / saddle network",
        "applicable": frozenset(DYNAMO_FIELD_CLASSES
                                | {FieldClass.CRUSTAL_REMANENT_FIELD}),
        "uses_magnetic_data": True,
        "is_control": False,
        "scientific_type": ScientificType.ANALYTIC_MODEL.value,
    },
    RootMethod.HARMONIC_PRINCIPAL_AXIS: {
        "description": ("principal-axis decomposition of low-degree "
                        "spherical harmonics"),
        "applicable": frozenset(DYNAMO_FIELD_CLASSES),
        "uses_magnetic_data": True,
        "is_control": False,
        "scientific_type": ScientificType.ANALYTIC_MODEL.value,
    },
    RootMethod.CRUSTAL_ANOMALY_CENTROID: {
        "description": ("crustal-anomaly centroid, for bodies with no "
                        "global dynamo"),
        "applicable": frozenset({FieldClass.CRUSTAL_REMANENT_FIELD}),
        "uses_magnetic_data": True,
        "is_control": False,
        "scientific_type": ScientificType.ANALYTIC_MODEL.value,
    },
    RootMethod.SPIN_AXIS_NULL_CONTROL: {
        "description": ("NULL CONTROL: spin axis + prime meridian only, "
                        "no magnetic data at all"),
        "applicable": _ALL_CLASSES | {FieldClass.NO_RESOLVED_FIELD_MODEL},
        "uses_magnetic_data": False,
        "is_control": True,
        "scientific_type": ScientificType.ANALYTIC_MODEL.value,
    },
}

#: Constructions that presuppose a coherent internally generated field,
#: i.e. the Earth-style recipes.
EARTH_DYNAMO_METHODS = frozenset(
    m for m, s in METHOD_SPEC.items()
    if s["uses_magnetic_data"] and s["applicable"] <= DYNAMO_FIELD_CLASSES)


# --- a sampled field ---------------------------------------------------

@dataclass(frozen=True, eq=False)
class FieldGrid:
    """A scalar magnetic feature sampled on a lat/lon grid, at altitude."""

    latitudes: np.ndarray
    longitudes: np.ndarray
    values: np.ndarray
    altitude_km: float
    quantity: str = "RADIAL_COMPONENT_NT"
    model_epoch: str = "SYNTHETIC_NO_EPOCH"

    def __post_init__(self) -> None:
        la = np.asarray(self.latitudes, float)
        lo = np.asarray(self.longitudes, float)
        v = np.asarray(self.values, float)
        if la.ndim != 1 or lo.ndim != 1:
            raise PlanetRootError("latitudes and longitudes must be 1-D")
        if v.shape != (la.size, lo.size):
            raise PlanetRootError(
                f"values shape {v.shape} does not match grid "
                f"({la.size}, {lo.size})")
        if np.any(np.diff(la) <= 0) or np.any(np.diff(lo) <= 0):
            raise PlanetRootError("grid axes must be strictly ascending")
        if self.altitude_km < 0:
            raise PlanetRootError("altitude must be non-negative")


def synthetic_anomaly_grid(anomalies, *, altitude_km: float = 0.0,
                           lat_step: float = 1.0, lon_step: float = 1.0,
                           quantity: str = "RADIAL_COMPONENT_NT"
                           ) -> FieldGrid:
    """A NUMERICAL_SIMULATION grid built from planted Gaussian lobes.

    Each anomaly is ``(lat, lon, amplitude, width_deg[, aspect])``. The
    lobe is circular in the local equal-scale projection when
    ``aspect == 1`` and elongated otherwise, which is what lets the
    circularity test be exercised in both directions.
    """
    lats = np.arange(-89.0, 89.0 + lat_step / 2, lat_step)
    lons = np.arange(-180.0, 180.0 + lon_step / 2, lon_step)
    vals = np.zeros((lats.size, lons.size))
    LA, LO = np.meshgrid(lats, lons, indexing="ij")
    for a in anomalies:
        lat0, lon0, amp, width = a[0], a[1], a[2], a[3]
        aspect = a[4] if len(a) > 4 else 1.0
        if width <= 0 or aspect <= 0:
            raise PlanetRootError("anomaly width and aspect must be > 0")
        scale = math.cos(math.radians(lat0))
        x = (LO - lon0) * scale
        y = LA - lat0
        d2 = (x / aspect) ** 2 + y ** 2
        vals += amp * np.exp(-d2 / (2.0 * width ** 2))
    return FieldGrid(lats, lons, vals, altitude_km, quantity)


def synthetic_dipole_grid(axis, *, amplitude: float = 30000.0,
                          altitude_km: float = 0.0,
                          lat_step: float = 2.0,
                          lon_step: float = 2.0) -> FieldGrid:
    """Radial component of an axial dipole about ``axis`` (simulation)."""
    u = np.asarray(axis, float)
    n = np.linalg.norm(u)
    if n == 0:
        raise PlanetRootError("dipole axis must be non-zero")
    u = u / n
    lats = np.arange(-89.0, 89.0 + lat_step / 2, lat_step)
    lons = np.arange(-180.0, 180.0 + lon_step / 2, lon_step)
    LA, LO = np.meshgrid(lats, lons, indexing="ij")
    c = np.cos(np.radians(LA))
    xyz = np.stack([c * np.cos(np.radians(LO)),
                    c * np.sin(np.radians(LO)),
                    np.sin(np.radians(LA))], axis=-1)
    vals = amplitude * (xyz @ u)
    return FieldGrid(lats, lons, vals, altitude_km)


def _bilinear(grid: FieldGrid, lat: float, lon: float) -> float:
    la, lo = np.asarray(grid.latitudes), np.asarray(grid.longitudes)
    if lat < la[0] or lat > la[-1] or lon < lo[0] or lon > lo[-1]:
        raise PlanetRootError("sample point falls outside the grid")
    i = int(np.clip(np.searchsorted(la, lat) - 1, 0, la.size - 2))
    j = int(np.clip(np.searchsorted(lo, lon) - 1, 0, lo.size - 2))
    t = (lat - la[i]) / (la[i + 1] - la[i])
    s = (lon - lo[j]) / (lo[j + 1] - lo[j])
    v = grid.values
    return float((1 - t) * ((1 - s) * v[i, j] + s * v[i, j + 1])
                 + t * ((1 - s) * v[i + 1, j] + s * v[i + 1, j + 1]))


def _peak_of(grid: FieldGrid) -> tuple[float, float, float]:
    idx = int(np.argmax(np.abs(grid.values)))
    i, j = np.unravel_index(idx, grid.values.shape)
    return (float(grid.latitudes[i]), float(grid.longitudes[j]),
            float(grid.values[i, j]))


def horizontal_gradient_extremum(grid: FieldGrid) -> dict:
    """Location of the largest horizontal gradient of the feature."""
    dlat = float(grid.latitudes[1] - grid.latitudes[0])
    dlon = float(grid.longitudes[1] - grid.longitudes[0])
    gy, gx = np.gradient(grid.values, dlat, dlon)
    scale = np.cos(np.radians(grid.latitudes))[:, None]
    mag = np.hypot(gy, gx / np.clip(scale, 1e-6, None))
    idx = int(np.argmax(mag))
    i, j = np.unravel_index(idx, mag.shape)
    return {"lat_deg": float(grid.latitudes[i]),
            "lon_deg": float(grid.longitudes[j]),
            "gradient": float(mag[i, j])}


def closed_contour(grid: FieldGrid, centre_lat: float, centre_lon: float,
                   level: float, *, n_azimuth: int = 36,
                   max_radius_deg: float = 40.0,
                   step_deg: float = 0.25) -> np.ndarray:
    """Trace a closed contour at ``level`` around a centre.

    Returns (n_azimuth, 2) local planar offsets in degrees, x eastward
    (scaled by cos(lat)) and y northward. Raises if any ray fails to
    cross the level, i.e. the contour is not closed.
    """
    if n_azimuth < 8:
        raise PlanetRootError("a contour needs at least 8 azimuths")
    if level <= 0:
        raise PlanetRootError("contour level must be positive")
    scale = max(math.cos(math.radians(centre_lat)), 1e-6)
    pts = []
    for k in range(n_azimuth):
        az = 2.0 * math.pi * k / n_azimuth
        prev_r = 0.0
        prev_v = abs(_bilinear(grid, centre_lat, centre_lon))
        hit = None
        r = step_deg
        while r <= max_radius_deg:
            lat = centre_lat + r * math.sin(az)
            lon = centre_lon + r * math.cos(az) / scale
            try:
                v = abs(_bilinear(grid, lat, lon))
            except PlanetRootError:
                break
            if (prev_v - level) * (v - level) <= 0 and prev_v != v:
                frac = (prev_v - level) / (prev_v - v)
                hit = prev_r + frac * (r - prev_r)
                break
            prev_r, prev_v = r, v
            r += step_deg
        if hit is None:
            raise PlanetRootError(
                f"contour at level {level} is not closed: no crossing "
                f"along azimuth {math.degrees(az):.0f} deg within "
                f"{max_radius_deg} deg. An open contour is not a root.")
        pts.append((hit * math.cos(az), hit * math.sin(az)))
    return np.asarray(pts, float)


def magnetic_nulls(grid: FieldGrid, *, threshold: float | None = None
                   ) -> np.ndarray:
    """Grid points where the feature vanishes through a sign change."""
    v = grid.values
    peak = float(np.max(np.abs(v)))
    if peak == 0:
        raise PlanetRootError("field is identically zero; no nulls to find")
    thr = 0.02 * peak if threshold is None else float(threshold)
    tiny = 1e-6 * peak
    inner = v[1:-1, 1:-1]
    neigh = np.stack([v[:-2, 1:-1], v[2:, 1:-1],
                      v[1:-1, :-2], v[1:-1, 2:]], axis=0)
    sign_change = (np.any(neigh > tiny, axis=0)
                   & np.any(neigh < -tiny, axis=0))
    mask = (np.abs(inner) <= thr) & sign_change
    ii, jj = np.nonzero(mask)
    if ii.size == 0:
        return np.zeros((0, 2))
    return np.column_stack([grid.latitudes[ii + 1], grid.longitudes[jj + 1]])


def harmonic_principal_axis(grid: FieldGrid) -> dict:
    """Degree-1 principal axis of the sampled feature (ANALYTIC_MODEL)."""
    LA, LO = np.meshgrid(grid.latitudes, grid.longitudes, indexing="ij")
    c = np.cos(np.radians(LA))
    xyz = np.stack([c * np.cos(np.radians(LO)),
                    c * np.sin(np.radians(LO)),
                    np.sin(np.radians(LA))], axis=-1)
    w = c[..., None]
    vec = (grid.values[..., None] * xyz * w).sum(axis=(0, 1))
    n = float(np.linalg.norm(vec))
    if n == 0:
        raise PlanetRootError(
            "degree-1 projection vanishes; no principal axis is defined")
    u = vec / n
    return {"axis": u,
            "lat_deg": float(np.degrees(np.arcsin(np.clip(u[2], -1, 1)))),
            "lon_deg": float(np.degrees(np.arctan2(u[1], u[0]))),
            "power": n}


def anomaly_centroid(anomalies) -> dict:
    """Weighted centroid direction of crustal anomalies (lat, lon, weight)."""
    a = np.asarray(anomalies, float)
    if a.ndim != 2 or a.shape[1] != 3:
        raise PlanetRootError("anomalies must be an (N,3) lat/lon/weight array")
    if np.any(a[:, 2] < 0):
        raise PlanetRootError("anomaly weights must be non-negative")
    lat, lon, w = np.radians(a[:, 0]), np.radians(a[:, 1]), a[:, 2]
    u = np.stack([np.cos(lat) * np.cos(lon),
                  np.cos(lat) * np.sin(lon),
                  np.sin(lat)], axis=-1)
    s = (w[:, None] * u).sum(axis=0)
    n = float(np.linalg.norm(s))
    if n == 0:
        raise PlanetRootError("anomaly centroid is undefined (vectors cancel)")
    c = s / n
    return {"lat_deg": float(np.degrees(np.arcsin(np.clip(c[2], -1, 1)))),
            "lon_deg": float(np.degrees(np.arctan2(c[1], c[0]))),
            "resultant_length": float(n / w.sum()),
            "n_anomalies": int(a.shape[0])}


def spin_axis_null_root(rotation_axis, prime_meridian_lon: float) -> dict:
    """NULL CONTROL: a root from geometry alone, no magnetic data."""
    u = np.asarray(rotation_axis, float)
    if u.shape != (3,) or np.linalg.norm(u) == 0:
        raise PlanetRootError("rotation_axis must be a non-zero 3-vector")
    u = u / np.linalg.norm(u)
    pole_lat = float(np.degrees(np.arcsin(np.clip(u[2], -1, 1))))
    return {"lat_deg": 0.0,
            "lon_deg": float(prime_meridian_lon),
            "pole_lat_deg": pole_lat,
            "rule": "equator crossed with the declared prime meridian",
            "uses_magnetic_data": False}


# --- dispatch ----------------------------------------------------------

def construct_root(method: RootMethod, body: str | BodyFieldModel, *,
                   grid: FieldGrid | None = None,
                   anomalies=None,
                   rotation_axis=(0.0, 0.0, 1.0),
                   prime_meridian_lon: float = 0.0,
                   reference_level: str | None = None,
                   contour_level_fraction: float = 0.5,
                   null_threshold: float | None = None) -> dict:
    """Build a candidate root by one declared construction, with guards."""
    if not isinstance(method, RootMethod):
        raise PlanetRootError("method must be a RootMethod member")
    b = resolve_body(body)
    spec = METHOD_SPEC[method]

    if b.field_class not in spec["applicable"]:
        if method in EARTH_DYNAMO_METHODS:
            refuse_earth_method_on_non_dynamo_body(b, method)
        raise PlanetRootError(
            f"{b.body_id}: construction {method.name} is not defined for "
            f"field class {b.field_class.value}")

    level_declared = reference_level or b.reference_level
    if not b.has_solid_surface and "SURFACE" in level_declared.upper():
        refuse_surface_assumption_for_gas_giant(b)

    if spec["uses_magnetic_data"]:
        if method is RootMethod.CRUSTAL_ANOMALY_CENTROID:
            if anomalies is None:
                raise PlanetRootError(
                    f"{b.body_id}: {method.name} needs an anomaly list. "
                    f"BLOCKED_MISSING_DATA.")
        elif grid is None:
            raise PlanetRootError(
                f"{b.body_id}: {method.name} needs a sampled magnetic "
                f"field and none was supplied. BLOCKED_MISSING_DATA.")

    out: dict = {
        "method": method.name,
        "method_number": method.value,
        "description": spec["description"],
        "body_id": b.body_id,
        "field_class": b.field_class.value,
        "uses_magnetic_data": spec["uses_magnetic_data"],
        "is_control": spec["is_control"],
        "scientific_type": spec["scientific_type"],
        "reference_level": level_declared,
        "altitude_km": (grid.altitude_km if grid is not None else 0.0),
        "candidate_alias": PLANETARY_ROOT_CANDIDATE_A,
    }

    if method is RootMethod.RADIAL_FIELD_EXTREMUM:
        lat, lon, val = _peak_of(grid)
        out.update({"lat_deg": lat, "lon_deg": lon, "feature_value": val})
    elif method is RootMethod.HORIZONTAL_GRADIENT_EXTREMUM:
        out.update(horizontal_gradient_extremum(grid))
    elif method is RootMethod.STABLE_CLOSED_CONTOUR:
        lat, lon, val = _peak_of(grid)
        if not 0.0 < contour_level_fraction < 1.0:
            raise PlanetRootError("contour_level_fraction must be in (0,1)")
        level = abs(val) * contour_level_fraction
        pts = closed_contour(grid, lat, lon, level)
        out.update({"lat_deg": lat, "lon_deg": lon,
                    "contour_level": level,
                    "contour_points": pts,
                    "contour_closed": True,
                    "shape_named": "CLOSED_CONTOUR_NOT_CIRCLE"})
    elif method is RootMethod.NULL_SADDLE_NETWORK:
        nulls = magnetic_nulls(grid, threshold=null_threshold)
        if nulls.shape[0] == 0:
            raise PlanetRootError(
                f"{b.body_id}: no magnetic nulls found; this construction "
                f"yields no root on this field")
        out.update({"lat_deg": float(np.mean(nulls[:, 0])),
                    "lon_deg": float(np.mean(nulls[:, 1])),
                    "nulls": nulls, "n_nulls": int(nulls.shape[0])})
    elif method is RootMethod.HARMONIC_PRINCIPAL_AXIS:
        r = harmonic_principal_axis(grid)
        out.update({"lat_deg": r["lat_deg"], "lon_deg": r["lon_deg"],
                    "axis": r["axis"], "power": r["power"]})
    elif method is RootMethod.CRUSTAL_ANOMALY_CENTROID:
        out.update(anomaly_centroid(anomalies))
    elif method is RootMethod.SPIN_AXIS_NULL_CONTROL:
        out.update(spin_axis_null_root(rotation_axis, prime_meridian_lon))
        out["control_label"] = "NULL_CONTROL_NO_MAGNETIC_DATA"
    else:                                        # pragma: no cover
        raise PlanetRootError(f"unhandled construction {method!r}")
    return out


def compare_constructions(body: str | BodyFieldModel, **kwargs) -> list[dict]:
    """Run every construction that is defined for this body, side by side."""
    b = resolve_body(body)
    results = []
    for method in RootMethod:
        if b.field_class not in METHOD_SPEC[method]["applicable"]:
            continue
        try:
            results.append(construct_root(method, b, **kwargs))
        except PlanetRootError as exc:
            results.append({"method": method.name, "body_id": b.body_id,
                            "refused": str(exc)})
    return results


# --- the preregistered circularity test --------------------------------

#: Fixed before any contour was fitted: a contour counts as circular only
#: if its RMS radial residual is within this fraction of its radius.
PREREGISTERED_CIRCULARITY = {
    "tolerance_normalised_rms": 0.05,
    "min_points": 8,
    "registered_before_seeing_data": True,
    "statistic": "rms radial residual / fitted radius",
}
CIRCULARITY_TOLERANCE = PREREGISTERED_CIRCULARITY["tolerance_normalised_rms"]


def circularity(points, *, tolerance: float = CIRCULARITY_TOLERANCE) -> dict:
    """Least-squares circle fit and the preregistered circularity verdict."""
    p = np.asarray(points, float)
    if p.ndim != 2 or p.shape[1] != 2:
        raise PlanetRootError("points must be an (N,2) array")
    if p.shape[0] < PREREGISTERED_CIRCULARITY["min_points"]:
        raise PlanetRootError(
            f"circularity needs at least "
            f"{PREREGISTERED_CIRCULARITY['min_points']} points")
    x, y = p[:, 0], p[:, 1]
    A = np.column_stack([x, y, np.ones_like(x)])
    rhs = x ** 2 + y ** 2
    sol, *_ = np.linalg.lstsq(A, rhs, rcond=None)
    cx, cy = sol[0] / 2.0, sol[1] / 2.0
    r2 = sol[2] + cx ** 2 + cy ** 2
    if r2 <= 0:
        raise PlanetRootError("circle fit is degenerate; no radius")
    radius = math.sqrt(r2)
    resid = np.hypot(x - cx, y - cy) - radius
    rms = float(np.sqrt(np.mean(resid ** 2)))
    norm = rms / radius
    return {"centre": (float(cx), float(cy)),
            "radius": float(radius),
            "rms_residual": rms,
            "normalised_rms": float(norm),
            "tolerance": float(tolerance),
            "n_points": int(p.shape[0]),
            "circular": bool(norm <= tolerance),
            "tested": True,
            "preregistered": True,
            "scientific_type": ScientificType.ANALYTIC_MODEL.value}


def declare_circle(fit: dict | None) -> dict:
    """Name a fitted contour a circle only if the test says so."""
    if not isinstance(fit, dict) or not fit.get("tested") \
            or not fit.get("preregistered") or not fit.get("circular"):
        refuse_circle_without_test(fit)
    return {"shape": "CIRCLE",
            "normalised_rms": fit["normalised_rms"],
            "tolerance": fit["tolerance"],
            "scientific_type": ScientificType.ANALYTIC_MODEL.value}


# --- altitude attenuation ----------------------------------------------

def dipole_feature_strength(altitude_km: float, *,
                            colatitude_deg: float = 0.0,
                            body_radius_km: float = 6371.2,
                            surface_moment_nT: float = 30000.0) -> float:
    """|B| of an axial dipole at altitude: the r^-3 fall-off, explicitly."""
    if altitude_km < 0:
        raise PlanetRootError("altitude must be non-negative")
    if body_radius_km <= 0:
        raise PlanetRootError("body radius must be positive")
    r = (body_radius_km + altitude_km) / body_radius_km
    ct = math.cos(math.radians(colatitude_deg))
    return surface_moment_nT * math.sqrt(1.0 + 3.0 * ct * ct) / r ** 3


def altitude_attenuation(altitudes_km, **kwargs) -> dict:
    """Feature strength against altitude, with a monotonicity verdict."""
    alts = [float(a) for a in altitudes_km]
    if len(alts) < 2:
        raise PlanetRootError("need at least two altitudes")
    if any(b <= a for a, b in zip(alts, alts[1:])):
        raise PlanetRootError("altitudes must be strictly increasing")
    s = [dipole_feature_strength(a, **kwargs) for a in alts]
    return {"altitudes_km": alts,
            "strengths_nT": s,
            "monotone_decreasing": all(b < a for a, b in zip(s, s[1:])),
            "ratio_first_to_last": float(s[0] / s[-1]),
            "scientific_type": ScientificType.ANALYTIC_MODEL.value}


# --- preregistered method selection ------------------------------------

def select_method(method: RootMethod, *, preregistration_id: str,
                  target_inspected: bool) -> dict:
    """Register a construction choice. Refuses post-hoc selection."""
    if not isinstance(method, RootMethod):
        raise PlanetRootError("method must be a RootMethod member")
    if not preregistration_id:
        raise PlanetRootError("a method choice needs a preregistration id")
    if target_inspected:
        refuse_target_dependent_selection(
            method, reason="target inspected before the method was fixed")
    return {"method": method.name,
            "preregistration_id": preregistration_id,
            "target_inspected_first": False,
            "scientific_type": ScientificType.ANALYTIC_MODEL.value}


# --- load-bearing refusals ---------------------------------------------

def refuse_earth_method_on_non_dynamo_body(body, method) -> None:
    """Earth's dynamo recipe does not transfer to a non-dynamo body."""
    name = getattr(body, "body_id", body)
    cls = getattr(getattr(body, "field_class", None), "value", "UNKNOWN")
    mname = getattr(method, "name", method)
    raise PlanetRootError(
        f"refused: {mname} is an Earth-style dynamo construction and "
        f"{name} is classed {cls}. On a CRUSTAL_REMANENT, "
        f"INDUCED_SOLAR_WIND or NO_RESOLVED body the same arithmetic "
        f"names a different physical thing -- a patch of ancient "
        f"magnetised crust, or an induced draping of the solar wind -- "
        f"so the transferred rule is an equivocation, not a "
        f"generalisation. Magnetic-root logic is BODY_SPECIFIC.")


def refuse_surface_assumption_for_gas_giant(body) -> None:
    """A gas giant has no solid surface to put a root on."""
    name = getattr(body, "body_id", body)
    raise PlanetRootError(
        f"refused: {name} has no solid surface, so 'surface' is not a "
        f"defined reference here. A reference PRESSURE LEVEL (for "
        f"example the 1 bar level) must be declared instead, together "
        f"with the shape model and the rotation system used to fix "
        f"longitude.")


def refuse_timeless_root(cert) -> None:
    """A root that drifts is not a timeless address."""
    name = getattr(cert, "body_id", cert)
    epoch = getattr(cert, "magnetic_model_epoch", None)
    feature = getattr(cert, "scalar_or_vector_feature", "")
    why = []
    if not epoch:
        why.append("no magnetic_model_epoch is declared")
    if str(feature).upper() in KNOWN_DRIFTING_FEATURES:
        why.append(f"the feature {feature!r} is known to drift")
    stability = str(getattr(cert, "temporal_stability", "")).upper()
    if stability in DRIFTING_STABILITY:
        why.append(f"temporal_stability is {stability!r}")
    if not why:
        why.append("timelessness was asserted without support")
    raise PlanetRootError(
        f"refused: {name} may not be called a timeless address because "
        + "; ".join(why) + ". Every field here moves -- secular "
        "variation, drifting spots, revised models -- so a root is "
        "valid only for a stated model at a stated epoch with a stated "
        "uncertainty. Magnetic-root logic is EPOCH_SPECIFIC.")


def refuse_circle_without_test(fit=None) -> None:
    """A contour is not a circle until the preregistered test passes."""
    got = ""
    if isinstance(fit, dict) and "normalised_rms" in fit:
        got = (f" (normalised rms {fit['normalised_rms']:.4f} against "
               f"tolerance {fit.get('tolerance')})")
    raise PlanetRootError(
        "refused: a fitted contour may not be called a 'circle' until it "
        "passes the preregistered circularity test"
        f"{got}. The tolerance "
        f"({CIRCULARITY_TOLERANCE}) was fixed before any contour was "
        f"fitted; naming a shape by eye is how an ellipse, an arc, or a "
        f"blob becomes a 'circle' in a later retelling. There is no "
        f"verified universal anomaly circle.")


def refuse_target_dependent_selection(method=None, target=None, *,
                                      reason: str = "") -> None:
    """The construction may not be chosen after seeing the target."""
    mname = getattr(method, "name", method)
    raise PlanetRootError(
        f"refused: construction {mname} may not be selected after "
        f"inspecting the target"
        + (f" ({target})" if target else "")
        + (f": {reason}" if reason else "")
        + ". Seven constructions are implemented precisely because they "
          "disagree; picking the one that lands nearest a desired point "
          "converts a free parameter into a finding. The method, the "
          "tolerance, and the null control are fixed first.")


# --- standing status ---------------------------------------------------

UNIVERSAL_ANOMALY_CIRCLE_STATUS = {
    "claim": ("a single anomaly circle, of some shared radius, appears on "
              "every body and can serve as a universal root"),
    "status": ScientificType.UNSUPPORTED.value,
    "why": ("no such circle has been demonstrated on any two bodies here, "
            "let alone all of them; the field classes differ, the "
            "features differ, and the epochs differ. The claim is "
            "recorded so it can be tested, not assumed"),
}

REAL_MODEL_STATUS = {
    "status": ScientificType.BLOCKED_MISSING_DATA.value,
    "why": ("published spherical-harmonic coefficient sets and crustal "
            "anomaly maps for these bodies are not bundled in this "
            "environment, so every grid used here is synthetic and "
            "labelled NUMERICAL_SIMULATION"),
    "not_faked": ("no result from a real magnetic model is reported, and "
                  "no root is claimed as physical"),
}


def planetroot_report() -> dict:
    return {
        "what_this_is": (
            "a body-specific, epoch-specific framework for constructing "
            "and comparing candidate planetary magnetic roots, with "
            "seven competing constructions, a null control, a "
            "preregistered circularity test, and five load-bearing "
            "refusals"),
        "bodies": {k: v.field_class.value for k, v in BODIES.items()},
        "field_classes": [c.value for c in FieldClass],
        "constructions": {m.name: METHOD_SPEC[m]["description"]
                          for m in RootMethod},
        "null_control": RootMethod.SPIN_AXIS_NULL_CONTROL.name,
        "candidate_alias": PLANETARY_ROOT_CANDIDATE_A,
        "candidate_status": ScientificType.CANDIDATE_HYPOTHESIS.value,
        "preregistered_circularity": dict(PREREGISTERED_CIRCULARITY),
        "universal_anomaly_circle": UNIVERSAL_ANOMALY_CIRCLE_STATUS,
        "real_magnetic_models": REAL_MODEL_STATUS,
        "evidence_class": (
            f"{ScientificType.ESTABLISHED_SOURCE.value} body parameters, "
            f"{ScientificType.ANALYTIC_MODEL.value} constructions, "
            f"{ScientificType.NUMERICAL_SIMULATION.value} test grids"),
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "what_this_does_not_say": (
            "It does not locate any body's magnetic root, does not claim "
            "that any constructed point is physical, and does not claim "
            "a universal anomaly circle -- that remains UNSUPPORTED. It "
            "does not license carrying an Earth dynamo recipe to Mars, "
            "the Moon, or Venus; it does not place a root on a gas "
            "giant's non-existent surface; and it does not call any root "
            "timeless, because every field modelled here drifts and an "
            "address that drifts is an address only for its epoch."),
        "verdict": "PLANETARY_ROOT_FRAMEWORK_SPECIFIABLE",
    }
