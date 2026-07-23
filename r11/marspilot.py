"""P13 — the Mars frame pilot: the frame completes, the root does not.

This module ports the P03 pipeline from Earth to Mars and stops, on
purpose, one stage early::

    areographic / areocentric (lat, lon, h)
      -> IAU Mars body-fixed frame, east-positive longitude DECLARED
      -> body-fixed Cartesian on the Mars reference ellipsoid
      -> the SAME South-Up PROPER rotation  R = diag(1, -1, -1)
      -> areocentric ray
      -> the SAME frozen canonical icosahedron face
      -> ray-face intersection (SET-VALUED on edges and vertices)
      -> [ magnetic root ]                          <-- REFUSED

Everything above the dashed line is arithmetic and completes. The
ellipsoid conversion is closed form and checkable: ``lat=0, lon=0, h=0``
lands at ``x = a`` and the pole lands at ``z = b``, where ``a`` and ``b``
are the published IAU/MOLA equatorial and polar radii and the flattening
is *derived* from them rather than invented. The South-Up view and the
icosahedron are not re-derived here at all -- they are imported from
:mod:`r11.earthface` and reused, because a second, Mars-flavoured copy of
a frozen solid is a second solid, and two solids can be quietly rotated
against each other until a site lands where someone wanted it. The
imported solid is the same object; ``refuse_rotate_after_load`` still
applies to it, unchanged.

**Why the pilot stops short of a magnetic root.** Mars is classed
``CRUSTAL_REMANENT_FIELD`` in :mod:`r11.planetroot`: it has **no global
dynamo**. What it has is strong remanent magnetisation frozen into
ancient southern highland crust -- patches of old rock, not a coherent
internally generated field. So the Earth recipe does not transfer. "The
strongest radial expression of the dynamo" is a definite description on
Earth and an equivocation on Mars, where the same arithmetic names
whichever patch of crust happens to be most magnetised at whatever
altitude and epoch the map was built for.

Even setting the equivocation aside, a root here would need **five**
things frozen *before* any point is reported, and independently of it:

1. a **numerical MAG/ER vector field grid** -- an actual gridded product,
   not a synthetic lobe and not a description of one;
2. the **altitude** it is evaluated at, because crustal anomalies
   attenuate steeply with height and the ranking of patches changes;
3. the **epoch** and data version of that grid;
4. the **gradient scalar** the extremum is taken of;
5. the **sign rule** that turns a line into an arrow.

:class:`MarsRootPrerequisites` carries those five and defaults every one
of them to ``UNFROZEN``. :func:`magnetic_root` refuses while any is
missing -- and, because **no numerical MAG/ER vector grid is present in
this repository** (``GRID_STATUS = "BLOCKED_MISSING_DATA"``), it returns
a labelled ``ROOT_CANDIDATE_REQUIRES_REAL_GRID`` even when all five are
frozen. It never returns an identified root.
:func:`refuse_magnetic_root_identification` always raises.

The landing sites tabulated here are real, published coordinates for
completed and ongoing missions. They are ``CONTROL_SITE`` entries: they
exist to exercise the frame end to end on points that are not chosen by
this work, and :func:`refuse_site_as_target` refuses to let any of them
be read as a destination, a decode, or a target.

Nothing here is measured. No magnetometer was read, no orbit was flown,
no surface was visited. The standing verdict is that the Mars **frame**
pilot completes and the magnetic **root** is not identified.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

import numpy as np

from r11 import earthface, planetroot
from r11.earthface import (
    CANONICAL_ICOSAHEDRON,
    EDGE_TOLERANCE,
    SOUTH_UP_ROTATION,
    EarthFaceError,
    Icosahedron,
    is_proper_rotation,
    refuse_mirror_view,
    south_up,
)


class MarsPilotError(RuntimeError):
    """Raised when the Mars pilot is asked to claim more than a frame."""


# --- typed evidence vocabulary (shared with the rest of R11) -----------

ScientificType = planetroot.ScientificType

EVIDENCE_CLASS = ScientificType.ANALYTIC_MODEL.value
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"
VERDICT = "MARS_FRAME_PILOT_COMPLETE_MAGNETIC_ROOT_NOT_IDENTIFIED"

#: Mars' field class, taken from the P02 body taxonomy rather than
#: restated here. CRUSTAL_REMANENT_FIELD: no global dynamo.
MARS_BODY = planetroot.BODIES["MARS"]
MARS_FIELD_CLASS = MARS_BODY.field_class

#: No numerical MAG/ER vector grid is bundled in this repository.
GRID_STATUS = ScientificType.BLOCKED_MISSING_DATA.value


# --- part 1a: the Mars reference ellipsoid -----------------------------

#: IAU / MOLA reference ellipsoid radii, metres (ESTABLISHED_SOURCE).
MARS_EQUATORIAL_RADIUS_M = 3396190.0      # 3396.19 km
MARS_POLAR_RADIUS_M = 3376200.0           # 3376.20 km

#: Derived from the two published radii. Not an independent constant.
MARS_A = MARS_EQUATORIAL_RADIUS_M
MARS_B = MARS_POLAR_RADIUS_M
MARS_F = (MARS_A - MARS_B) / MARS_A
MARS_E2 = MARS_F * (2.0 - MARS_F)
MARS_INVERSE_FLATTENING = 1.0 / MARS_F

MARS_BODY_FIXED_FRAME = MARS_BODY.body_fixed_frame       # MARS_BODY_FIXED_IAU
MARS_REFERENCE_SURFACE = MARS_BODY.reference_level       # AREOID_REFERENCE_SURFACE
MARS_SHAPE_MODEL = "IAU_MOLA_BIAXIAL_ELLIPSOID_3396190_3376200_M"


# --- part 1b: the conventions, carried as types ------------------------

class LongitudeConvention(Enum):
    """Which way longitude counts. The IAU Mars frame is east-positive.

    Both conventions are in the literature for Mars -- east-positive
    planetocentric is the IAU body-fixed standard, and west-positive
    appears in older areographic usage. A number carrying neither label
    is not a longitude, it is a magnitude, and mixing the two silently
    reflects a site to the far side of the planet.
    """

    EAST_POSITIVE = "EAST_POSITIVE"
    WEST_POSITIVE = "WEST_POSITIVE"


class LatitudeConvention(Enum):
    """Planetocentric (from the centre) or planetographic (ellipsoid normal).

    They differ by up to about a fifth of a degree on Mars, which is
    small, non-zero, and exactly the size of error that survives a
    review because it looks like rounding.
    """

    PLANETOCENTRIC = "PLANETOCENTRIC"
    PLANETOGRAPHIC = "PLANETOGRAPHIC"


#: The IAU Mars body-fixed frame convention pair, declared once.
IAU_MARS_LONGITUDE = LongitudeConvention.EAST_POSITIVE
IAU_MARS_LATITUDE = LatitudeConvention.PLANETOCENTRIC


def refuse_mixed_longitude_convention(
        declared: LongitudeConvention,
        used: LongitudeConvention,
        context: str = "") -> LongitudeConvention:
    """Return the shared convention, or refuse a silent mixture.

    An east-positive longitude read as west-positive (or the reverse)
    places the point at ``360 - lon``: still a legal longitude, still on
    the planet, and wrong by up to half a circumference. Because the
    result is never out of range, nothing downstream can catch it. So
    the two conventions must agree explicitly, here, or the pipeline
    stops.
    """
    if not isinstance(declared, LongitudeConvention) or \
            not isinstance(used, LongitudeConvention):
        raise MarsPilotError(
            "longitude conventions must be LongitudeConvention members; "
            "an unlabelled longitude is not a longitude")
    if declared is not used:
        tail = f" ({context})" if context else ""
        raise MarsPilotError(
            f"refused: longitude declared {declared.value} but used as "
            f"{used.value}{tail}. The two differ by a reflection, "
            f"lon_east = 360 - lon_west, so a site silently moves to the "
            f"far side of Mars while remaining a perfectly legal "
            f"longitude that no range check can reject. The IAU Mars "
            f"body-fixed frame is {IAU_MARS_LONGITUDE.value}; convert "
            f"explicitly with to_east_longitude() or declare the other "
            f"convention and keep it.")
    return declared


def to_east_longitude(longitude_deg: float,
                      convention: LongitudeConvention = IAU_MARS_LONGITUDE
                      ) -> float:
    """Normalise a longitude to IAU east-positive degrees in [0, 360)."""
    if not isinstance(convention, LongitudeConvention):
        raise MarsPilotError("convention must be a LongitudeConvention")
    lon = float(longitude_deg)
    if not -360.0 <= lon <= 360.0:
        raise MarsPilotError(f"longitude {lon} out of range [-360, 360]")
    if convention is LongitudeConvention.WEST_POSITIVE:
        lon = -lon
    return lon % 360.0


def planetocentric_to_planetographic(latitude_deg: float) -> float:
    """Centre-referenced latitude -> ellipsoid-normal latitude, on Mars."""
    lat = _check_latitude(latitude_deg)
    if abs(lat) == 90.0:
        return lat
    return math.degrees(math.atan(math.tan(math.radians(lat))
                                  / (1.0 - MARS_F) ** 2))


def planetographic_to_planetocentric(latitude_deg: float) -> float:
    """Ellipsoid-normal latitude -> centre-referenced latitude, on Mars."""
    lat = _check_latitude(latitude_deg)
    if abs(lat) == 90.0:
        return lat
    return math.degrees(math.atan((1.0 - MARS_F) ** 2
                                  * math.tan(math.radians(lat))))


def _check_latitude(latitude_deg: float) -> float:
    lat = float(latitude_deg)
    if not -90.0 <= lat <= 90.0:
        raise MarsPilotError(f"latitude {lat} out of range [-90, 90]")
    return lat


def _as_planetographic(latitude_deg: float,
                       convention: LatitudeConvention) -> float:
    if not isinstance(convention, LatitudeConvention):
        raise MarsPilotError("convention must be a LatitudeConvention")
    lat = _check_latitude(latitude_deg)
    if convention is LatitudeConvention.PLANETOCENTRIC:
        return planetocentric_to_planetographic(lat)
    return lat


def _as_planetocentric(latitude_deg: float,
                       convention: LatitudeConvention) -> float:
    if not isinstance(convention, LatitudeConvention):
        raise MarsPilotError("convention must be a LatitudeConvention")
    lat = _check_latitude(latitude_deg)
    if convention is LatitudeConvention.PLANETOGRAPHIC:
        return planetographic_to_planetocentric(lat)
    return lat


# --- part 1c: geodetic -> Mars body-fixed Cartesian --------------------

def mars_geodetic_to_body_fixed(
        latitude_deg: float,
        longitude_deg: float,
        height_m: float = 0.0,
        *,
        longitude_convention: LongitudeConvention = IAU_MARS_LONGITUDE,
        latitude_convention: LatitudeConvention
        = LatitudeConvention.PLANETOGRAPHIC) -> np.ndarray:
    """Mars geodetic (lat, lon, h) -> IAU body-fixed Cartesian metres.

    The same closed form as the Earth conversion in
    :mod:`r11.earthface`, evaluated on the Mars ellipsoid instead of
    WGS-84. DERIVED_ARITHMETIC: ``lat=0, lon=0, h=0`` gives ``(a, 0, 0)``
    with ``a`` the published equatorial radius, and the north pole gives
    ``(0, 0, b)`` with ``b`` the published polar radius, because
    ``a * sqrt(1 - e^2) = b`` identically when ``e^2`` is derived from
    ``a`` and ``b``.

    Latitude is taken as PLANETOGRAPHIC by default -- that is the
    latitude the ellipsoid-normal formula is written in. Pass
    ``latitude_convention=PLANETOCENTRIC`` to have it converted first
    rather than reinterpreted silently.
    """
    lat = _as_planetographic(latitude_deg, latitude_convention)
    lon = to_east_longitude(longitude_deg, longitude_convention)
    h = float(height_m)
    phi = math.radians(lat)
    lam = math.radians(lon)
    s = math.sin(phi)
    n = MARS_A / math.sqrt(1.0 - MARS_E2 * s * s)
    x = (n + h) * math.cos(phi) * math.cos(lam)
    y = (n + h) * math.cos(phi) * math.sin(lam)
    z = (n * (1.0 - MARS_E2) + h) * s
    return np.array([x, y, z], dtype=float)


# --- part 1d: the reused South-Up view and the reused frozen solid -----

#: Imported, not redefined. ``diag(1, -1, -1)``, det = +1.
MARS_SOUTH_UP_ROTATION = SOUTH_UP_ROTATION

#: Imported, not rebuilt. The SAME object the Earth pipeline uses.
MARS_ICOSAHEDRON = CANONICAL_ICOSAHEDRON


def verify_reused_south_up() -> dict:
    """Confirm the imported view is the proper rotation, not a mirror."""
    refuse_mirror_view(MARS_SOUTH_UP_ROTATION)
    R = np.asarray(MARS_SOUTH_UP_ROTATION, dtype=float)
    return {
        "matrix": tuple(tuple(float(v) for v in row) for row in R),
        "determinant": float(np.linalg.det(R)),
        "is_proper_rotation": bool(is_proper_rotation(R)),
        "is_the_earthface_object": MARS_SOUTH_UP_ROTATION
        is earthface.SOUTH_UP_ROTATION,
        "reused_not_redefined": True,
    }


def verify_reused_icosahedron() -> dict:
    """Confirm the frozen solid is the Earth pipeline's, unmodified."""
    ico = MARS_ICOSAHEDRON
    return {
        "is_the_earthface_object": ico is earthface.CANONICAL_ICOSAHEDRON,
        "n_vertices": int(ico.vertices.shape[0]),
        "n_faces": len(ico.faces),
        "provenance": ico.provenance,
        "vertices_read_only": not ico.vertices.flags.writeable,
        "rotated_for_mars": False,
    }


def refuse_rotate_after_load(reason: str = "") -> None:
    """The frozen solid is not re-oriented for Mars. Reuses P03's refusal.

    Re-freezing a "Mars icosahedron" at some other orientation would be
    the same fitting move as rotating the Earth one, with an extra step
    of indirection to hide it.
    """
    try:
        earthface.refuse_rotate_after_load(
            reason or "the Mars frame pilot reuses the Earth solid")
    except EarthFaceError as exc:
        raise MarsPilotError(str(exc)) from exc


def areocentric_ray(latitude_deg: float, longitude_deg: float, *,
                    longitude_convention: LongitudeConvention
                    = IAU_MARS_LONGITUDE,
                    latitude_convention: LatitudeConvention
                    = IAU_MARS_LATITUDE) -> np.ndarray:
    """Unit ray from the Mars centre to (lat, lon), seen South-Up.

    The ray is built from the PLANETOCENTRIC latitude, because that is
    what a ray from the centre means; a planetographic input is
    converted first rather than reused as if it were the same angle.
    """
    lat = _as_planetocentric(latitude_deg, latitude_convention)
    lon = to_east_longitude(longitude_deg, longitude_convention)
    phi = math.radians(lat)
    lam = math.radians(lon)
    u = np.array([math.cos(phi) * math.cos(lam),
                  math.cos(phi) * math.sin(lam),
                  math.sin(phi)], dtype=float)
    return south_up(u)


def mars_face(latitude_deg: float, longitude_deg: float, *,
              longitude_convention: LongitudeConvention
              = IAU_MARS_LONGITUDE,
              latitude_convention: LatitudeConvention = IAU_MARS_LATITUDE,
              tol: float = EDGE_TOLERANCE) -> frozenset[int]:
    """Which frozen icosahedron face(s) the areocentric ray pierces.

    SET-VALUED, exactly as on Earth. A ray through a face interior
    returns one index; a ray within ``tol`` of a shared edge returns
    both faces; a ray through a vertex returns all five. Collapsing that
    set to one face would be a tie broken by index order rather than by
    geometry, on Mars as on Earth.
    """
    ray = areocentric_ray(
        latitude_deg, longitude_deg,
        longitude_convention=longitude_convention,
        latitude_convention=latitude_convention)
    try:
        return earthface.ray_face_intersection(ray, MARS_ICOSAHEDRON, tol)
    except EarthFaceError as exc:
        raise MarsPilotError(str(exc)) from exc


# --- part 2: published landing sites, as CONTROLS ONLY -----------------

CONTROL_ROLE = "CONTROL_SITE"


@dataclass(frozen=True)
class MarsControlSite:
    """A published landing site, carried as a CONTROL and nothing else.

    The coordinates are conventional literature values for completed and
    ongoing missions. They are here to exercise the frame on points this
    work did not choose. They are not destinations, decodes or targets,
    and :func:`refuse_site_as_target` says so in code.
    """

    site_id: str
    mission: str
    region: str
    planetocentric_latitude_deg: float
    east_longitude_deg: float
    role: str = CONTROL_ROLE
    longitude_convention: LongitudeConvention = LongitudeConvention.EAST_POSITIVE
    latitude_convention: LatitudeConvention = LatitudeConvention.PLANETOCENTRIC
    evidence_class: str = ScientificType.ESTABLISHED_SOURCE.value

    def __post_init__(self) -> None:
        if self.role != CONTROL_ROLE:
            raise MarsPilotError(
                f"{self.site_id}: a landing site may only be carried with "
                f"role {CONTROL_ROLE!r}")
        _check_latitude(self.planetocentric_latitude_deg)
        to_east_longitude(self.east_longitude_deg,
                          self.longitude_convention)

    def ray(self) -> np.ndarray:
        return areocentric_ray(
            self.planetocentric_latitude_deg, self.east_longitude_deg,
            longitude_convention=self.longitude_convention,
            latitude_convention=self.latitude_convention)

    def faces(self) -> frozenset[int]:
        return mars_face(
            self.planetocentric_latitude_deg, self.east_longitude_deg,
            longitude_convention=self.longitude_convention,
            latitude_convention=self.latitude_convention)

    def body_fixed(self, height_m: float = 0.0) -> np.ndarray:
        return mars_geodetic_to_body_fixed(
            self.planetocentric_latitude_deg, self.east_longitude_deg,
            height_m,
            longitude_convention=self.longitude_convention,
            latitude_convention=self.latitude_convention)


#: Real, published landing coordinates. CONTROLS. Nothing is decoded to
#: any of them; they exercise the frame and stop there.
CONTROL_SITES: tuple[MarsControlSite, ...] = (
    MarsControlSite("VIKING_1_CONTROL", "Viking 1", "Chryse Planitia",
                    22.27, 312.05),
    MarsControlSite("VIKING_2_CONTROL", "Viking 2", "Utopia Planitia",
                    47.64, 134.29),
    MarsControlSite("PATHFINDER_CONTROL", "Mars Pathfinder",
                    "Ares Vallis", 19.13, 326.75),
    MarsControlSite("OPPORTUNITY_CONTROL", "Opportunity",
                    "Meridiani Planum", -1.95, 354.47),
    MarsControlSite("CURIOSITY_CONTROL", "Curiosity", "Gale crater",
                    -4.59, 137.44),
    MarsControlSite("INSIGHT_CONTROL", "InSight", "Elysium Planitia",
                    4.50, 135.62),
    MarsControlSite("PERSEVERANCE_CONTROL", "Perseverance",
                    "Jezero crater", 18.44, 77.45),
)

CONTROL_SITES_BY_ID: dict[str, MarsControlSite] = {
    s.site_id: s for s in CONTROL_SITES}


def control_site(site_id: str) -> MarsControlSite:
    key = str(site_id).upper()
    if key not in CONTROL_SITES_BY_ID:
        raise MarsPilotError(f"{site_id!r} is not a declared control site")
    return CONTROL_SITES_BY_ID[key]


def refuse_site_as_target(site: MarsControlSite | str | None = None,
                          reason: str = "") -> None:
    """A control site may not be read as a destination or a decode.

    Always raises. The sites are published facts about spacecraft that
    landed; using one as the answer to a decode would let a coordinate
    that was already in the literature come back out of this pipeline
    dressed as a finding.
    """
    name = getattr(site, "site_id", site) or "a control site"
    tail = f" ({reason})" if reason else ""
    raise MarsPilotError(
        f"refused: {name} is a {CONTROL_ROLE}, not a target{tail}. The "
        f"landing coordinates in this module are published values for "
        f"missions that have already flown; they are carried to exercise "
        f"the frame on points this work did not choose. Treating one as a "
        f"destination, a decoded location, or a predicted site would "
        f"return known literature as though the pipeline had produced it. "
        f"No site here is decoded to, and no site here is a claim.")


# --- part 3: the magnetic root, refused --------------------------------

UNFROZEN = "UNFROZEN"

#: All five must be frozen, independently of any candidate point, before
#: a magnetic root on Mars means anything at all.
REQUIRED_ROOT_PREREQUISITES: tuple[str, ...] = (
    "numerical_MAG_ER_vector_grid",
    "altitude",
    "epoch",
    "gradient_scalar",
    "sign_rule",
)

PREREQUISITE_REASONS: dict[str, str] = {
    "numerical_MAG_ER_vector_grid": (
        "a gridded MAG/ER vector product; without numbers there is "
        "nothing to take an extremum of, and a synthetic lobe is not a "
        "stand-in for one"),
    "altitude": (
        "crustal remanent anomalies attenuate steeply with height, so "
        "which patch is strongest depends on the altitude the map was "
        "built at"),
    "epoch": (
        "the data epoch and model version; the rock does not move but "
        "the model of it is revised"),
    "gradient_scalar": (
        "which scalar the gradient is taken of -- total intensity, a "
        "component, or the potential; they peak in different places"),
    "sign_rule": (
        "a zero or gradient direction is a line, and nothing in the "
        "geometry picks an arrow along it"),
}

ROOT_CANDIDATE_STATUS = "ROOT_CANDIDATE_REQUIRES_REAL_GRID"


@dataclass(frozen=True)
class MarsRootPrerequisites:
    """The five things that must be frozen before a Mars root is defined.

    Every field defaults to ``None`` and is read as ``UNFROZEN``. An
    empty string or the literal ``"UNFROZEN"`` counts as unfrozen too,
    so a placeholder cannot be mistaken for a declaration.
    """

    numerical_MAG_ER_vector_grid: object | None = None
    altitude: object | None = None
    epoch: object | None = None
    gradient_scalar: object | None = None
    sign_rule: object | None = None

    @staticmethod
    def _is_frozen(value: object | None) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            text = value.strip()
            return bool(text) and text.upper() != UNFROZEN
        return True

    def unfrozen(self) -> tuple[str, ...]:
        """Names of the prerequisites still not frozen, in fixed order."""
        return tuple(name for name in REQUIRED_ROOT_PREREQUISITES
                     if not self._is_frozen(getattr(self, name)))

    def frozen(self) -> tuple[str, ...]:
        return tuple(name for name in REQUIRED_ROOT_PREREQUISITES
                     if self._is_frozen(getattr(self, name)))

    def all_frozen(self) -> bool:
        return not self.unfrozen()

    def as_dict(self) -> dict:
        return {name: (getattr(self, name)
                       if self._is_frozen(getattr(self, name)) else UNFROZEN)
                for name in REQUIRED_ROOT_PREREQUISITES}


def magnetic_root(prereqs: MarsRootPrerequisites) -> dict:
    """Refuse a Mars magnetic root; at best, return a labelled CANDIDATE.

    With any of the five prerequisites unfrozen this raises, naming the
    missing ones and why each is load-bearing. With all five frozen it
    still does **not** return a root: it returns a candidate whose status
    is ``ROOT_CANDIDATE_REQUIRES_REAL_GRID``, because freezing the
    *declaration* of a MAG/ER grid is not the same as having one, and
    this repository has none (``GRID_STATUS`` is
    ``BLOCKED_MISSING_DATA``). The pilot completes the frame; the root
    stays unidentified.
    """
    if not isinstance(prereqs, MarsRootPrerequisites):
        raise MarsPilotError(
            "magnetic_root needs a MarsRootPrerequisites; the five "
            "prerequisites are not optional keyword decoration")
    missing = prereqs.unfrozen()
    if missing:
        why = "; ".join(f"{name}: {PREREQUISITE_REASONS[name]}"
                        for name in missing)
        raise MarsPilotError(
            f"refused: Mars is classed {MARS_FIELD_CLASS.value} -- no "
            f"global dynamo, only crustal remanent magnetisation -- and "
            f"{len(missing)} of {len(REQUIRED_ROOT_PREREQUISITES)} "
            f"prerequisites are UNFROZEN: {', '.join(missing)}. {why}. "
            f"All five must be fixed before any point is reported and "
            f"independently of that point; a prerequisite chosen after "
            f"the candidate is a free parameter wearing a label.")
    return {
        "body_id": MARS_BODY.body_id,
        "field_class": MARS_FIELD_CLASS.value,
        "has_global_dynamo": MARS_BODY.has_global_dynamo,
        "body_fixed_frame": MARS_BODY_FIXED_FRAME,
        "longitude_convention": IAU_MARS_LONGITUDE.value,
        "shape_model": MARS_SHAPE_MODEL,
        "prerequisites": prereqs.as_dict(),
        "prerequisites_frozen": list(REQUIRED_ROOT_PREREQUISITES),
        "status": ROOT_CANDIDATE_STATUS,
        "grid_status": GRID_STATUS,
        "root_identified": False,
        "latitude_deg": None,
        "longitude_deg": None,
        "scientific_type": ScientificType.CANDIDATE_HYPOTHESIS.value,
        "why_not_a_root": (
            "no numerical MAG/ER vector grid is present in this "
            "repository, so the five frozen prerequisites describe a "
            "computation that cannot be run here. A declaration of which "
            "grid would be used is a specification, not data."),
        "verdict": VERDICT,
    }


def refuse_earth_dynamo_method_on_mars(method: object = None,
                                       reason: str = "") -> None:
    """Earth's dynamo recipe does not transfer to Mars. Always raises.

    Reuses the P02 reasoning verbatim rather than restating it: the same
    arithmetic names a different physical thing on a body whose field is
    remanent crust rather than a live dynamo.
    """
    try:
        planetroot.refuse_earth_method_on_non_dynamo_body(MARS_BODY, method)
    except planetroot.PlanetRootError as exc:
        tail = f" ({reason})" if reason else ""
        raise MarsPilotError(f"{exc}{tail}") from exc
    raise MarsPilotError(                                  # pragma: no cover
        "refused: Earth dynamo methods do not transfer to Mars")


def refuse_magnetic_root_identification(candidate: object = None,
                                        reason: str = "") -> None:
    """Always raises. The pilot completes the FRAME, not the root."""
    tail = f" ({reason})" if reason else ""
    named = f" for {candidate}" if candidate else ""
    raise MarsPilotError(
        f"refused: no magnetic root is identified on Mars{named}{tail}. "
        f"Mars is {MARS_FIELD_CLASS.value}: there is no global dynamo to "
        f"root against, only patches of ancient magnetised crust whose "
        f"ranking changes with altitude, with the scalar chosen, and with "
        f"the model version. The five prerequisites "
        f"({', '.join(REQUIRED_ROOT_PREREQUISITES)}) would all have to be "
        f"frozen first, and even then no numerical MAG/ER vector grid is "
        f"present here ({GRID_STATUS}), so the best available output is a "
        f"{ROOT_CANDIDATE_STATUS}. This module completes the Mars FRAME "
        f"and stops. {VERDICT}")


# --- the pilot, end to end ---------------------------------------------

def mars_frame_pilot() -> dict:
    """Run the frame on every control site and report where it stops."""
    verify_reused_south_up()
    sites = []
    for s in CONTROL_SITES:
        faces = s.faces()
        sites.append({
            "site_id": s.site_id,
            "mission": s.mission,
            "region": s.region,
            "role": s.role,
            "planetocentric_latitude_deg": s.planetocentric_latitude_deg,
            "east_longitude_deg": s.east_longitude_deg,
            "candidate_faces": tuple(sorted(faces)),
            "face_assignment_is_unique": len(faces) == 1,
        })
    return {
        "body_id": MARS_BODY.body_id,
        "field_class": MARS_FIELD_CLASS.value,
        "body_fixed_frame": MARS_BODY_FIXED_FRAME,
        "longitude_convention": IAU_MARS_LONGITUDE.value,
        "latitude_convention": IAU_MARS_LATITUDE.value,
        "equatorial_radius_m": MARS_EQUATORIAL_RADIUS_M,
        "polar_radius_m": MARS_POLAR_RADIUS_M,
        "flattening": MARS_F,
        "inverse_flattening": MARS_INVERSE_FLATTENING,
        "flattening_is_derived": True,
        "south_up": verify_reused_south_up(),
        "icosahedron": verify_reused_icosahedron(),
        "control_sites": tuple(sites),
        "n_control_sites": len(sites),
        "frame_complete": True,
        "magnetic_root_identified": False,
        "grid_status": GRID_STATUS,
        "verdict": VERDICT,
    }


def marspilot_report() -> dict:
    return {
        "what_this_is": (
            "a pilot port of the South-Up icosahedral face frame from "
            "Earth to Mars, on the published IAU/MOLA reference "
            "ellipsoid, exercised on seven published landing sites as "
            "controls, which completes the FRAME and refuses the "
            "magnetic ROOT"),
        "pipeline": [
            "Mars geodetic (lat, lon, h)",
            "IAU Mars body-fixed frame, east-positive longitude declared",
            "body-fixed Cartesian on the 3396.19 / 3376.20 km ellipsoid",
            "the SAME South-Up proper rotation diag(1,-1,-1), imported",
            "areocentric ray",
            "the SAME frozen canonical icosahedron, imported",
            "ray-face intersection (set-valued on edges/vertices)",
            "[ magnetic root ] -- REFUSED"],
        "reference_ellipsoid": {
            "equatorial_radius_km": MARS_EQUATORIAL_RADIUS_M / 1000.0,
            "polar_radius_km": MARS_POLAR_RADIUS_M / 1000.0,
            "flattening": MARS_F,
            "inverse_flattening": MARS_INVERSE_FLATTENING,
            "derived_not_invented": True,
            "shape_model": MARS_SHAPE_MODEL,
            "source_class": ScientificType.ESTABLISHED_SOURCE.value,
        },
        "conventions": {
            "longitude": [c.value for c in LongitudeConvention],
            "latitude": [c.value for c in LatitudeConvention],
            "iau_longitude": IAU_MARS_LONGITUDE.value,
            "iau_latitude": IAU_MARS_LATITUDE.value,
            "mixing_refused_by": "refuse_mixed_longitude_convention",
        },
        "reused_from_earthface": [
            "SOUTH_UP_ROTATION", "CANONICAL_ICOSAHEDRON",
            "ray_face_intersection", "refuse_rotate_after_load"],
        "reused_objects_are_identical": (
            MARS_SOUTH_UP_ROTATION is earthface.SOUTH_UP_ROTATION
            and MARS_ICOSAHEDRON is earthface.CANONICAL_ICOSAHEDRON),
        "icosahedron_rotated_for_mars": False,
        "control_sites": [
            {"site_id": s.site_id, "mission": s.mission,
             "region": s.region, "role": s.role}
            for s in CONTROL_SITES],
        "control_sites_are_not_targets": True,
        "field_class": MARS_FIELD_CLASS.value,
        "has_global_dynamo": MARS_BODY.has_global_dynamo,
        "root_prerequisites": {
            name: PREREQUISITE_REASONS[name]
            for name in REQUIRED_ROOT_PREREQUISITES},
        "root_prerequisites_default": UNFROZEN,
        "root_status": ROOT_CANDIDATE_STATUS,
        "grid_status": GRID_STATUS,
        "refusals": [
            "refuse_mixed_longitude_convention",
            "refuse_rotate_after_load",
            "refuse_site_as_target",
            "refuse_earth_dynamo_method_on_mars",
            "refuse_magnetic_root_identification"],
        "evidence_class": EVIDENCE_CLASS,
        "measured_here": "nothing",
        "physical_validation": PHYSICAL_VALIDATION,
        "what_would_change_this": (
            "a real numerical MAG/ER vector field grid at a stated "
            "altitude and epoch, a gradient scalar and a sign rule fixed "
            "before any candidate point is computed, and a construction "
            "that beats the geometry-only null control"),
        "what_this_does_not_say": (
            "It does not identify a magnetic root on Mars, and it does "
            "not claim one exists. Mars has no global dynamo -- it is "
            "CRUSTAL_REMANENT_FIELD, ancient magnetised southern crust -- "
            "so the Earth dynamo recipe is refused rather than "
            "transferred. No numerical MAG/ER vector grid is present in "
            "this repository, so even with all five prerequisites frozen "
            "the output is a labelled candidate, not a root. It does not "
            "say the icosahedron is a feature of Mars, that any landing "
            "site sits on a meaningful face, or that any site is a "
            "target: the seven landing coordinates are published control "
            "values used to exercise the frame and are refused as "
            "destinations. No magnetometer was read, no orbit was flown "
            "and no surface was visited."),
        "verdict": VERDICT,
    }


__all__ = [
    "MarsPilotError", "ScientificType", "EVIDENCE_CLASS",
    "PHYSICAL_VALIDATION", "VERDICT", "GRID_STATUS",
    "MARS_BODY", "MARS_FIELD_CLASS",
    "MARS_EQUATORIAL_RADIUS_M", "MARS_POLAR_RADIUS_M",
    "MARS_A", "MARS_B", "MARS_F", "MARS_E2", "MARS_INVERSE_FLATTENING",
    "MARS_BODY_FIXED_FRAME", "MARS_REFERENCE_SURFACE", "MARS_SHAPE_MODEL",
    "LongitudeConvention", "LatitudeConvention",
    "IAU_MARS_LONGITUDE", "IAU_MARS_LATITUDE",
    "refuse_mixed_longitude_convention", "to_east_longitude",
    "planetocentric_to_planetographic", "planetographic_to_planetocentric",
    "mars_geodetic_to_body_fixed",
    "MARS_SOUTH_UP_ROTATION", "MARS_ICOSAHEDRON",
    "Icosahedron", "is_proper_rotation", "south_up",
    "verify_reused_south_up", "verify_reused_icosahedron",
    "refuse_rotate_after_load", "areocentric_ray", "mars_face",
    "CONTROL_ROLE", "MarsControlSite", "CONTROL_SITES",
    "CONTROL_SITES_BY_ID", "control_site", "refuse_site_as_target",
    "UNFROZEN", "REQUIRED_ROOT_PREREQUISITES", "PREREQUISITE_REASONS",
    "ROOT_CANDIDATE_STATUS", "MarsRootPrerequisites", "magnetic_root",
    "refuse_earth_dynamo_method_on_mars",
    "refuse_magnetic_root_identification",
    "mars_frame_pilot", "marspilot_report",
]
