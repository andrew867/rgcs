"""P21 — Forward source geocoder: source vector -> pin, cell, region, alias set.

R10.8.1 stopped a source-vector map at a single bare refusal. R10.8.2's forward
geocoder decodes **every eligible source vector** under the frozen candidate
ensemble into one of the locked result classes — a
``CANDIDATE_CALIBRATED_POINT`` when the calibration selects a single family, a
``CANDIDATE_ALIAS_SET`` when several families remain admissible, a
``CANDIDATE_REGION`` when no calibration is available, and ``UNDERDETERMINED``
(a bounded heatmap region) when the candidate set is too diffuse to enumerate.

The app **always** produces pins or regions — never a bare refusal — but never
invents precision: every candidate carries an uncertainty footprint derived from
the terminal-cell quantization of the source codec, and an ambiguous decode
becomes a bounded region or alias set rather than a false-exact pin.

The pipeline reuses the Wave-1 engine end to end:
``route_core`` (five-token base-100 parse) -> ``spatialization`` /
``local_coord`` (family -> terminal-cell centroid) -> the frozen orientation ->
a body location -> ``result_states`` (the seven-class state machine).

**Body scope.** Only Earth / Terra source vectors are decoded here. A
foreign-body vector is *typed as out of scope* and is **not** force-decoded — no
pin is invented for a body this root does not describe.

**Frozen ensemble (dependency injection).** The retained families and the fitted
orientation come from the FROZEN calibration profile produced by tranche T05. So
this module never hard-depends on T05's build timing, the frozen profile is
passed in (``frozen_profile=``); T05 modules, if present, are imported lazily.
A deterministic public :class:`FrozenProfileStub` stands in for tests.

A geocoded pin is at most a ``CALIBRATED_CANDIDATE`` — a software result under a
declared calibration. It is never a measured fact and validates no source
origin. See :mod:`cwatlas.r1082.claims`.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from typing import Optional, Sequence

import numpy as np

from cwatlas.addressing import encode_path
from cwatlas.icosahedron import build_icosahedron
from cwatlas.r1082 import claims as _claims
from cwatlas.r1082 import local_coord, result_states, spatialization
from cwatlas.r1082.claims import ResultClass
from cwatlas.r1082.route_core import RouteError, parse_five_token
from cwatlas.r1082.semantic_expand import (
    DEFAULT_CONVENTIONAL_EPOCH,
    SHELL_MAX,
    SHELL_MIN,
    resolve_shell_radius_m,
)
from cwatlas.uncertainty import propagate_circle

MODULE_CODEC_ID = "CW-R1082-GEOCODE-FWD"
MODULE_CODEC_VERSION = "1.0.0"

#: The bodies this locked Earth root describes. A vector for any other body is
#: typed out of scope, never force-decoded.
BODY_IN_SCOPE = frozenset({"EARTH", "TERRA"})

#: The profile id used when no frozen calibration is supplied (a region-only
#: uncalibrated ensemble, never a calibrated pin).
UNCALIBRATED_PROFILE_ID = "UNCALIBRATED_ENSEMBLE_V0"

#: A reference radius (m) used only to give a shell-0 (closure) footprint a
#: non-zero ground scale, so an ambiguous decode never collapses to a point.
_REFERENCE_RADIUS_M = 6.371e6

#: Rounding (decimal degrees) used to count *distinct* candidate locations.
_DISTINCT_DECIMALS = 6


# -- frozen-profile handle (dependency injection) ---------------------------

@dataclass(frozen=True)
class FrozenProfileStub:
    """A deterministic, public stand-in for a frozen T05 calibration profile.

    TEST AID / PUBLIC STUB — **not** the real frozen profile. It exposes the
    same shape the geocoder consumes so tests run standalone regardless of when
    tranche T05 lands: a ``profile_id``, the retained spatialization families
    (by name), a fitted ``orientation`` (an orthonormal 3x3 mapping the
    candidate cell frame into the root frame), and ``anchor_hashes``.

    The real frozen profile (``cwatlas.r1082.calibration_freeze`` /
    ``candidate_ensemble``) is duck-typed with the same attributes and may be
    injected in its place.
    """

    profile_id: str
    retained_family_names: tuple[str, ...]
    orientation: tuple[tuple[float, float, float], ...]
    anchor_hashes: dict
    is_stub: bool = True

    def orientation_matrix(self) -> np.ndarray:
        return np.asarray(self.orientation, dtype=np.float64)

    def retained_families(self) -> tuple[spatialization.SpatializationFamily, ...]:
        return tuple(spatialization.get_family(n)
                     for n in self.retained_family_names)


def _identity_orientation() -> tuple[tuple[float, float, float], ...]:
    return ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


def default_frozen_stub() -> FrozenProfileStub:
    """A stub that retains ALL four families (an ambiguous, un-narrowed ensemble).

    A source vector decoded under this stub generally yields several distinct
    candidate locations, so the geocoder returns an alias set or region — never
    a false single pin.
    """
    names = tuple(f.name for f in spatialization.FAMILIES)
    return FrozenProfileStub(
        profile_id="EARTH_ROOT_D_V1:STUB_ALL_FAMILIES",
        retained_family_names=names,
        orientation=_identity_orientation(),
        anchor_hashes={"note": "synthetic public stub; no sealed anchors"},
    )


def single_family_stub(family_name: str = "F1_CANONICAL_DIRECT_BE"
                       ) -> FrozenProfileStub:
    """A stub whose calibration retained a SINGLE family (a calibrated pin).

    A source vector decoded under this stub yields one candidate location, so
    the geocoder returns a ``CANDIDATE_CALIBRATED_POINT`` (still a software
    candidate under a declared calibration, never a measured fact).
    """
    spatialization.get_family(family_name)  # refuse an unknown family
    return FrozenProfileStub(
        profile_id=f"EARTH_ROOT_D_V1:STUB_{family_name}",
        retained_family_names=(family_name,),
        orientation=_identity_orientation(),
        anchor_hashes={"note": "synthetic public stub; no sealed anchors"},
    )


def load_frozen_profile():
    """Return a real frozen T05 profile if importable, else the default stub.

    T05 modules are imported **lazily** and guarded — this module never breaks
    when the sibling tranche has not landed yet. When they are present, the real
    frozen calibration (``fit_all`` -> ``freeze_calibration``) is injected.
    """
    try:
        from cwatlas.r1082 import calibration_fit, calibration_freeze

        # An explicit factory takes precedence if T05 provides one.
        for name in ("load_frozen_profile", "frozen_profile",
                     "default_frozen_profile"):
            fn = getattr(calibration_freeze, name, None)
            if callable(fn):
                return fn()
        fit = calibration_fit.fit_all()
        return calibration_freeze.freeze_calibration(fit)
    except Exception:  # noqa: BLE001 - T05 absent or mid-build: fall back cleanly
        return default_frozen_stub()


def _frozen_family_names(fp) -> tuple[str, ...]:
    """Duck-type the retained family names from a frozen profile or stub."""
    for attr in ("retained_family_names", "family_names", "retained_families"):
        val = getattr(fp, attr, None)
        if callable(val):
            val = val()
        if val:
            return tuple(getattr(x, "name", x) for x in val)
    # Fall back to the full ensemble if the handle does not narrow it.
    return tuple(f.name for f in spatialization.FAMILIES)


def _frozen_orientation(fp) -> np.ndarray:
    """Duck-type the fitted orientation (3x3) from a frozen profile or stub."""
    for attr in ("orientation_matrix", "orientation", "fitted_orientation"):
        val = getattr(fp, attr, None)
        if callable(val):
            val = val()
        if val is not None:
            m = np.asarray(val, dtype=np.float64)
            if m.shape == (3, 3):
                return m
    return np.eye(3, dtype=np.float64)


def _frozen_profile_id(fp) -> str:
    for attr in ("profile_id", "receipt_id", "freeze_hash"):
        val = getattr(fp, attr, None)
        if val:
            return str(val)
    return "FROZEN_PROFILE"


def _rot_z(theta_rad: float) -> np.ndarray:
    """Rotation about +Z, matching ``calibration_fit._rot_z`` exactly.

    The two-anchor fit solves a single azimuth about +Z per family; applying
    the identical rotation here is what makes the frozen calibration
    *non-cosmetic* (the fitted orientation actually places the candidate).
    """
    c, s = math.cos(theta_rad), math.sin(theta_rad)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]],
                    dtype=np.float64)


def _frozen_orientation_by_family(fp) -> dict:
    """Per-family fitted rotations, duck-typed from a frozen profile.

    Returns ``{family_name: 3x3}``. The real T05 ``FrozenCalibration`` seals one
    azimuth per family (``fitted_parameters['orientation_theta_deg_by_family']``
    or an explicit ``orientation_matrix_by_family``); the public stub carries
    neither, so this returns ``{}`` and the caller falls back to the single
    global orientation (identity) — the pre-wiring behaviour, unchanged.
    """
    for attr in ("orientation_matrix_by_family", "orientation_by_family"):
        val = getattr(fp, attr, None)
        if callable(val):
            val = val()
        if val:
            out = {}
            for k, m in dict(val).items():
                a = np.asarray(m, dtype=np.float64)
                if a.shape == (3, 3):
                    out[str(k)] = a
            if out:
                return out
    params = getattr(fp, "fitted_parameters", None)
    if isinstance(params, dict):
        thetas = params.get("orientation_theta_deg_by_family")
        if isinstance(thetas, dict) and thetas:
            return {str(k): _rot_z(math.radians(float(v)))
                    for k, v in thetas.items()}
    return {}


# -- geometry helpers -------------------------------------------------------

def _unit(vec) -> np.ndarray:
    v = np.asarray(vec, dtype=np.float64).reshape(-1)
    n = float(np.linalg.norm(v))
    if n < 1e-15:
        raise ValueError("direction must be non-zero")
    return v / n


def unit_to_geocentric_latlon(vec) -> tuple[float, float]:
    """Geocentric spherical ``(lat_deg, lon_deg)`` of a direction (reversible)."""
    v = _unit(vec)
    lat = math.degrees(math.asin(max(-1.0, min(1.0, float(v[2])))))
    lon = math.degrees(math.atan2(float(v[1]), float(v[0])))
    lon = ((lon + 180.0) % 360.0) - 180.0
    return lat, lon


def geocentric_latlon_to_unit(lat_deg: float, lon_deg: float) -> np.ndarray:
    """Direction of a geocentric spherical ``(lat, lon)`` (inverse of above)."""
    lat, lon = math.radians(lat_deg), math.radians(lon_deg)
    cos_lat = math.cos(lat)
    return np.array([cos_lat * math.cos(lon), cos_lat * math.sin(lon),
                     math.sin(lat)], dtype=np.float64)


def _cell_ground_sigma_m(sp: spatialization.Spatialization,
                         radius_m: float) -> float:
    """Terminal-cell angular half-size scaled to a ground distance (metres).

    This is the source codec's quantization footprint: the point IS the cell
    centroid, so the honest uncertainty is half a terminal cell, never zero.
    """
    centroid = _unit(sp.centroid)
    scale = radius_m if radius_m > 0.0 else _REFERENCE_RADIUS_M
    ang = 0.0
    for corner in sp.polygon:
        c = _unit(corner)
        ang = max(ang, math.acos(max(-1.0, min(1.0, float(np.dot(centroid, c))))))
    # Guard a genuinely tiny cell so the region never collapses to a point.
    return max(ang * scale, 1.0)


@dataclass(frozen=True)
class SafeInverse:
    """A point->route inverse that never raises (clamped to the addressable set).

    The five-token source codec carries ``100**5 = 10**10`` states, but the
    depth-10 address space of a family is ``20 * 8**10`` — larger — so more than
    half of each face's terminal cells are **unaddressable** by any source
    vector. For a query in such a cell there is no exact route; ``in_route_space``
    is then ``False`` and the route is clamped into the addressable set. The
    reported ``residual`` is the true chord distance, so exactness is never
    falsely claimed and no precision is invented.
    """

    route: tuple[int, ...]
    nearest_point: np.ndarray
    residual: float
    exact: bool
    in_route_space: bool


def safe_family_inverse(point, family, *, ico=None) -> SafeInverse:
    """Invert a direction to a five-token route without ever raising.

    Reuses :func:`cwatlas.r1082.local_coord.inverse` when the query's terminal
    cell is addressable; otherwise it clamps the family address into the route
    space and reports the honest (larger) residual to the nearest constructible
    encodable centroid — the codec simply cannot address that region exactly.
    """
    fam = spatialization.get_family(family) if isinstance(family, str) else family
    if ico is None:
        ico = build_icosahedron()
    p = _unit(point)
    try:
        inv = local_coord.inverse(p, fam, ico=ico)
        return SafeInverse(route=inv.route, nearest_point=inv.nearest_point,
                           residual=inv.residual, exact=inv.exact,
                           in_route_space=True)
    except spatialization.SpatializationError:
        addr = encode_path(ico, p, spatialization.PATH_DEPTH)
        face_raw = fam._invert_face_entry(int(addr.face_id))
        q = fam._path_to_quotient(addr.path)
        n = q * spatialization.FACE_COUNT + face_raw
        max_n = spatialization.TOKEN_BASE ** spatialization.ROUTE_TOKENS - 1
        n = max(0, min(n, max_n))
        route = fam.int_to_route(n)
        nearest = fam.map_route(route, ico=ico).centroid
        residual = float(np.linalg.norm(p - nearest))
        return SafeInverse(route=route, nearest_point=nearest,
                           residual=residual,
                           exact=residual <= local_coord._EXACT_TOL,
                           in_route_space=False)


# -- candidate + result types ----------------------------------------------

@dataclass(frozen=True)
class GeocodeCandidate:
    """One decoded candidate location under one retained family."""

    family_name: str
    route: tuple[int, ...]
    latitude_deg: float
    longitude_deg: float
    shell: int
    radius_m: float
    ground_sigma_m: float
    cell_face_id: int
    cell_point: tuple[float, float, float]
    root_point: tuple[float, float, float]

    def to_dict(self) -> dict:
        return {
            "family_name": self.family_name,
            "route": list(self.route),
            "latitude_deg": self.latitude_deg,
            "longitude_deg": self.longitude_deg,
            "shell": self.shell,
            "radius_m": self.radius_m,
            "ground_sigma_m": self.ground_sigma_m,
            "cell_face_id": self.cell_face_id,
        }


@dataclass(frozen=True)
class ForwardGeocode:
    """A typed forward-geocode outcome (one of the seven result classes)."""

    result_type: str
    profile_id: str
    body: str
    in_scope: bool
    source_vector: str
    route: Optional[tuple[int, ...]]
    shell: int
    radius_m: Optional[float]
    epoch_year: Optional[float]
    calibration_available: bool
    candidates: tuple[GeocodeCandidate, ...]
    region: Optional[dict]
    map_result: Optional[result_states.MapResult]
    reason: str = ""
    receipt: dict = field(default_factory=dict)

    def is_candidate(self) -> bool:
        return self.result_type in {r.value for r in
                                    result_states.CANDIDATE_RESULT_CLASSES}

    def assert_not_measured(self) -> None:
        """A candidate pin is a software result, never a measured fact."""
        if self.is_candidate():
            _claims.refuse_candidate_as_measured(self.result_type)

    def _geometry(self):
        if not self.candidates:
            return None
        if self.result_type == ResultClass.CANDIDATE_CALIBRATED_POINT.value:
            c = self.candidates[0]
            return {"type": "POINT",
                    "latitude_deg": c.latitude_deg,
                    "longitude_deg": c.longitude_deg,
                    "shell": c.shell, "radius_m": c.radius_m}
        return [c.to_dict() for c in self.candidates]

    def to_serializable(self, *, as_measured: bool = False) -> dict:
        """Serialize to ``candidate_map_result.schema.json`` (never as measured)."""
        if as_measured:
            self.assert_not_measured()
        return {
            "result_type": self.result_type,
            "profile_id": self.profile_id,
            "input": {
                "source_vector": self.source_vector,
                "body": self.body,
                "shell": self.shell,
                "epoch_year": self.epoch_year,
                "in_scope": self.in_scope,
            },
            "geometry": self._geometry(),
            "uncertainty": self.region,
            "receipt": self.receipt,
        }


def _mean_latlon(cands: Sequence[GeocodeCandidate]) -> tuple[float, float]:
    """Direction-averaged centre of a candidate set (stable across the sphere)."""
    acc = np.zeros(3, dtype=np.float64)
    for c in cands:
        acc += geocentric_latlon_to_unit(c.latitude_deg, c.longitude_deg)
    return unit_to_geocentric_latlon(acc)


def _region_from_candidates(cands: Sequence[GeocodeCandidate],
                            justification: str) -> dict:
    """A bounded circular error region covering a candidate set (never a point)."""
    if len(cands) == 1:
        lat, lon = cands[0].latitude_deg, cands[0].longitude_deg
        sigma = cands[0].ground_sigma_m
    else:
        lat, lon = _mean_latlon(cands)
        centre = geocentric_latlon_to_unit(lat, lon)
        spread = 0.0
        for c in cands:
            d = geocentric_latlon_to_unit(c.latitude_deg, c.longitude_deg)
            ang = math.acos(max(-1.0, min(1.0, float(np.dot(centre, d)))))
            spread = max(spread, ang)
        radius = max((c.radius_m for c in cands), default=_REFERENCE_RADIUS_M)
        scale = radius if radius > 0.0 else _REFERENCE_RADIUS_M
        sigma = max(spread * scale,
                    max(c.ground_sigma_m for c in cands))
    region = propagate_circle(
        center=(lat, lon), input_sigma_m=sigma, quantization_m=0.0,
        cell_size_m=1.0e3, justification=justification)
    return {
        "kind": region.kind.value,
        "center": [region.center[0], region.center[1]],
        "radius_m": region.radius_m,
        "area_m2": region.area_m2,
        "search_space_count": region.search_space_count,
        "combined_sigma_m": region.combined_sigma_m,
        "justification": region.justification,
    }


def _receipt(*, profile_id: str, result_type: str, body: str, in_scope: bool,
             candidate_count: int, calibration_available: bool,
             route, shell, epoch_year, extra: dict) -> dict:
    payload = {"profile_id": profile_id, "result_type": result_type,
               "route": list(route) if route else None,
               "shell": shell, "epoch_year": epoch_year}
    receipt_hash = "sha256:" + hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=float).encode()).hexdigest()
    out = {
        "codec_id": MODULE_CODEC_ID,
        "codec_version": MODULE_CODEC_VERSION,
        "profile_id": profile_id,
        "result_type": result_type,
        "body": body,
        "in_scope": in_scope,
        "candidate_count": candidate_count,
        "calibration_available": calibration_available,
        "max_evidence": _claims.MAX_CANDIDATE_EVIDENCE.value,
        "receipt_hash": receipt_hash,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
        "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
    }
    out.update(extra)
    return out


def _out_of_scope(source_vector: str, body: str, shell: int,
                  epoch_year) -> ForwardGeocode:
    reason = (f"FOREIGN_BODY_OUT_OF_SCOPE: body {body!r} is not described by the "
              f"EARTH_ROOT_D_V1 locked root ({sorted(BODY_IN_SCOPE)}); the "
              f"vector is typed out of scope and NOT force-decoded.")
    return ForwardGeocode(
        result_type=ResultClass.INVALID.value,
        profile_id="EARTH_ROOT_D_V1",
        body=body, in_scope=False, source_vector=source_vector,
        route=None, shell=shell, radius_m=None, epoch_year=epoch_year,
        calibration_available=False, candidates=(), region=None,
        map_result=None, reason=reason,
        receipt=_receipt(
            profile_id="EARTH_ROOT_D_V1",
            result_type=ResultClass.INVALID.value, body=body, in_scope=False,
            candidate_count=0, calibration_available=False, route=None,
            shell=shell, epoch_year=epoch_year,
            extra={"body_scope": "FOREIGN_BODY_OUT_OF_SCOPE",
                   "force_decoded": False, "reason": reason}),
    )


def geocode(source_vector: str, frozen_profile=None, *,
            shell: int = 3, epoch_year: Optional[float] = 2020.0,
            body: str = "EARTH", conventional_epoch: Optional[dict] = None,
            ico=None, alias_max: int = result_states.DEFAULT_ALIAS_MAX
            ) -> ForwardGeocode:
    """Decode a source vector into a pin, cell, region, or alias set.

    ``frozen_profile`` (a T05 frozen profile or a :class:`FrozenProfileStub`)
    supplies the retained families and the fitted orientation; ``None`` means no
    calibration is available, so a lone candidate falls to a
    ``CANDIDATE_REGION`` rather than a false pin. The shell supplies the radius
    (never "altitude missing"). Foreign-body vectors are typed out of scope and
    not decoded. Earth/Terra vectors ALWAYS yield pins or regions — never a bare
    refusal, never invented precision.
    """
    if conventional_epoch is None:
        conventional_epoch = DEFAULT_CONVENTIONAL_EPOCH
    body_norm = str(body).upper()

    if not SHELL_MIN <= shell <= SHELL_MAX:
        raise RouteError(
            f"shell {shell} out of range [{SHELL_MIN}, {SHELL_MAX}].")

    if body_norm not in BODY_IN_SCOPE:
        return _out_of_scope(source_vector, body_norm, shell, epoch_year)

    # Parse the source vector exactly; a malformed vector is a typed INVALID
    # (still not a bare refusal — a classified state with an explanation).
    try:
        route_core = parse_five_token(source_vector)
    except RouteError as exc:
        mr = result_states.classify(
            valid=False, candidate_count=0, calibration_available=False)
        return ForwardGeocode(
            result_type=ResultClass.INVALID.value,
            profile_id="EARTH_ROOT_D_V1", body=body_norm, in_scope=True,
            source_vector=source_vector, route=None, shell=shell,
            radius_m=resolve_shell_radius_m(shell), epoch_year=epoch_year,
            calibration_available=False, candidates=(), region=None,
            map_result=mr, reason=f"INVALID_SOURCE_VECTOR: {exc}",
            receipt=_receipt(
                profile_id="EARTH_ROOT_D_V1",
                result_type=ResultClass.INVALID.value, body=body_norm,
                in_scope=True, candidate_count=0, calibration_available=False,
                route=None, shell=shell, epoch_year=epoch_year,
                extra={"reason": f"INVALID_SOURCE_VECTOR: {exc}"}))

    route = route_core.tokens
    if ico is None:
        ico = build_icosahedron()

    calibration_available = frozen_profile is not None
    if frozen_profile is None:
        profile_id = UNCALIBRATED_PROFILE_ID
        family_names = tuple(f.name for f in spatialization.FAMILIES)
        orientation = np.eye(3, dtype=np.float64)
    else:
        profile_id = _frozen_profile_id(frozen_profile)
        family_names = _frozen_family_names(frozen_profile)
        orientation = _frozen_orientation(frozen_profile)

    # Per-family fitted azimuths, when the frozen profile carries them. The
    # calibration is thereby applied, not merely declared: each retained family
    # is placed by its own fitted rotation. Absent (public stub / uncalibrated),
    # this is empty and the single global orientation is used unchanged.
    orient_by_family = (_frozen_orientation_by_family(frozen_profile)
                        if frozen_profile is not None else {})

    radius_m = resolve_shell_radius_m(shell)  # shell supplies the radius

    # Decode the vector under every retained family.
    candidates: list[GeocodeCandidate] = []
    for name in family_names:
        fam = spatialization.get_family(name)
        sp = fam.map_route(route, ico=ico)
        cell_point = _unit(sp.centroid)
        orient = orient_by_family.get(name, orientation)
        root_point = _unit(orient @ cell_point)
        lat, lon = unit_to_geocentric_latlon(root_point)
        candidates.append(GeocodeCandidate(
            family_name=name, route=route,
            latitude_deg=lat, longitude_deg=lon,
            shell=shell, radius_m=radius_m,
            ground_sigma_m=_cell_ground_sigma_m(sp, radius_m),
            cell_face_id=sp.face_id,
            cell_point=(float(cell_point[0]), float(cell_point[1]),
                        float(cell_point[2])),
            root_point=(float(root_point[0]), float(root_point[1]),
                        float(root_point[2])),
        ))

    # Count DISTINCT candidate locations (families can agree on a cell).
    seen: dict[tuple, GeocodeCandidate] = {}
    for c in candidates:
        key = (round(c.latitude_deg, _DISTINCT_DECIMALS),
               round(c.longitude_deg, _DISTINCT_DECIMALS))
        seen.setdefault(key, c)
    distinct = tuple(seen.values())

    mr = result_states.classify(
        valid=True, candidate_count=len(distinct),
        calibration_available=calibration_available,
        crs=profile_id, epoch=epoch_year, alias_max=alias_max)

    # Assemble the geometry: a lone calibrated candidate is a point (with its
    # cell footprint); everything else is a bounded region / alias set.
    if mr.result_class is ResultClass.CANDIDATE_CALIBRATED_POINT:
        out_candidates = (distinct[0],)
        region = _region_from_candidates(
            out_candidates, "source-codec terminal-cell quantization")
    elif mr.result_class is ResultClass.CANDIDATE_ALIAS_SET:
        out_candidates = distinct
        region = _region_from_candidates(
            distinct, "bounded alias set over retained families")
    elif mr.result_class is ResultClass.CANDIDATE_REGION:
        out_candidates = (distinct[0],)
        region = _region_from_candidates(
            out_candidates, "uncalibrated single candidate: region not a pin")
    elif mr.result_class is ResultClass.UNDERDETERMINED:
        out_candidates = distinct
        region = (_region_from_candidates(
            distinct, "diffuse candidate set: bounded heatmap region")
            if distinct else None)
    else:  # CALIBRATION_REQUIRED (epoch/crs missing)
        out_candidates = distinct
        region = None

    return ForwardGeocode(
        result_type=mr.result_class.value, profile_id=profile_id,
        body=body_norm, in_scope=True, source_vector=source_vector,
        route=route, shell=shell, radius_m=radius_m, epoch_year=epoch_year,
        calibration_available=calibration_available,
        candidates=out_candidates, region=region, map_result=mr,
        reason=mr.explanation,
        receipt=_receipt(
            profile_id=profile_id, result_type=mr.result_class.value,
            body=body_norm, in_scope=True, candidate_count=len(out_candidates),
            calibration_available=calibration_available, route=route,
            shell=shell, epoch_year=epoch_year,
            extra={
                "wire_source_vector": route_core.to_wire(),
                "retained_families": list(family_names),
                "distinct_candidate_count": len(distinct),
                "api_code": mr.api_code,
                "result_class_explanation": mr.explanation,
                "shell_supplies_radius": True,
                "altitude_missing": False,
            }),
    )


def geocode_forward_report() -> dict:
    """P21 declaration receipt. Always a pin/region; never measured, never bare."""
    return {
        "phase_id": "P21",
        "tranche": "T06",
        "what_this_is": (
            "the forward source geocoder: it decodes every eligible Earth/Terra "
            "source vector under the frozen candidate ensemble into a "
            "CANDIDATE_CALIBRATED_POINT, CANDIDATE_REGION, CANDIDATE_ALIAS_SET, "
            "UNDERDETERMINED region, or CALIBRATION_REQUIRED — always a pin or "
            "region, never a bare refusal, never invented precision."),
        "codec_id": MODULE_CODEC_ID,
        "codec_version": MODULE_CODEC_VERSION,
        "bodies_in_scope": sorted(BODY_IN_SCOPE),
        "foreign_body_force_decoded": False,
        "reused_engine": (
            "cwatlas.r1082.route_core -> spatialization / local_coord -> "
            "result_states; cwatlas.icosahedron / uncertainty (NOT reimplemented)"),
        "frozen_profile_injected": True,
        "t05_imported_lazily": True,
        "evidence_class": _claims.EvidenceClass.CALIBRATED_CANDIDATE.value,
        "max_evidence": _claims.MAX_CANDIDATE_EVIDENCE.value,
        "result_classes": [r.value for r in ResultClass],
        "shell_supplies_radius": True,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
        "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
        "verdict": "R1082_FORWARD_GEOCODER_PIN_CELL_REGION_OR_ALIAS_NEVER_BARE",
        "what_this_does_not_say": (
            "A geocoded pin is a CALIBRATED_CANDIDATE under a declared, frozen "
            "calibration — a software result, not a measured fact. It validates "
            "no source origin and asserts no physical effect."),
    }
