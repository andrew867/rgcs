"""P03 — Earth South root, city face, and a magnetic zero that is a set.

This module walks one explicit pipeline and refuses to pretend it is
shorter than it is::

    geodetic (lat, lon, h)
      -> ITRF at a DECLARED epoch
      -> ECEF on the WGS-84 ellipsoid
      -> South-Up PROPER rotation  R = diag(1, -1, -1)
      -> city geocentric ray
      -> frozen canonical icosahedron face
      -> ray-face intersection (SET-VALUED on edges and vertices)
      -> local face frame
      -> horizontal magnetic-gradient direction (candidate zero)

Two things in that chain are arithmetic and two are choices.

**The arithmetic.** The geodetic-to-ECEF conversion is closed-form and
checkable against known values (``lat=0, lon=0, h=0`` lands at ``x = a``;
the pole lands at ``z = b``). The South-Up view ``R = diag(1, -1, -1)``
is a *proper* rotation -- its determinant is ``(+1)(-1)(-1) = +1`` and
``R R^T = I`` -- so looking at the planet from the south is a change of
viewpoint, not a reflection. A mirror (``det = -1``) would silently swap
handedness and is refused. The icosahedron is frozen before any target
data is loaded, and rotating it afterwards is refused, because a
polyhedron that is free to spin can be made to point anywhere.

**The choices.** The last step is not one answer. "The horizontal
magnetic-gradient zero" is only a direction once four things are fixed
independently of the result:

1. **which scalar** the gradient is taken of -- total intensity,
   horizontal intensity, vertical component, declination, inclination,
   or the scalar potential;
2. **which sign** of the resulting direction is meant -- a zero
   direction is a line, and ``+d`` and ``-d`` are both on it;
3. **which altitude** the field is evaluated at;
4. **which epoch** the field model is evaluated for.

Fix none of them and the honest output is an **alias set**: every
combination is an equally licensed "the zero". This module returns that
set, keeps **both** vector signs unless a sign is fixed on independent
grounds, and refuses -- via :func:`refuse_single_zero_direction` -- to
hand back one unique direction while any of the four is unspecified.

The field itself is a declared, tilted-dipole ANALYTIC_MODEL in
dimensionless model units. No magnetometer was read, no survey was made,
no site was visited. ``SEDONA_FACE_CONTROL`` is a public **control**
location used to exercise the pipeline and nothing more; naming it makes
no claim about it. The standing verdict is that a local zero is
*specifiable* -- with aliases -- and that specifiable is not measured.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from itertools import combinations

import numpy as np


class EarthFaceError(ValueError):
    """Raised when the face pipeline is asked to over-claim."""


class ScientificType(Enum):
    """The evidence classes this module is allowed to emit."""

    ESTABLISHED_SOURCE = "ESTABLISHED_SOURCE"
    DERIVED_ARITHMETIC = "DERIVED_ARITHMETIC"
    ANALYTIC_MODEL = "ANALYTIC_MODEL"
    NUMERICAL_SIMULATION = "NUMERICAL_SIMULATION"
    SOURCE_CLAIM = "SOURCE_CLAIM"
    CANDIDATE_HYPOTHESIS = "CANDIDATE_HYPOTHESIS"
    UNSUPPORTED = "UNSUPPORTED"
    BLOCKED_MISSING_DATA = "BLOCKED_MISSING_DATA"


EVIDENCE_CLASS = ScientificType.ANALYTIC_MODEL.value
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"
VERDICT = "EARTH_FACE_LOCAL_ZERO_SPECIFIABLE_WITH_ALIASES"

MODEL_UNITS = "DIMENSIONLESS_MODEL_UNITS"


# --- stage 1: geodetic -> ECEF on WGS-84 --------------------------------

#: WGS-84 defining parameters (ESTABLISHED_SOURCE).
WGS84_A = 6378137.0                      # semi-major axis, metres
WGS84_F = 1.0 / 298.257223563            # flattening
WGS84_B = WGS84_A * (1.0 - WGS84_F)      # semi-minor axis, metres
WGS84_E2 = WGS84_F * (2.0 - WGS84_F)     # first eccentricity squared


def geodetic_to_ecef(latitude_deg: float,
                     longitude_deg: float,
                     height_m: float = 0.0) -> np.ndarray:
    """Geodetic (lat, lon, h) -> ECEF metres on the WGS-84 ellipsoid.

    Closed form, DERIVED_ARITHMETIC. ``lat=0, lon=0, h=0`` gives
    ``(a, 0, 0)``; the north pole gives ``(0, 0, b)``.
    """
    lat = float(latitude_deg)
    lon = float(longitude_deg)
    h = float(height_m)
    if not -90.0 <= lat <= 90.0:
        raise EarthFaceError(f"latitude {lat} out of range [-90, 90]")
    if not -360.0 <= lon <= 360.0:
        raise EarthFaceError(f"longitude {lon} out of range [-360, 360]")
    phi = math.radians(lat)
    lam = math.radians(lon)
    s = math.sin(phi)
    n = WGS84_A / math.sqrt(1.0 - WGS84_E2 * s * s)
    x = (n + h) * math.cos(phi) * math.cos(lam)
    y = (n + h) * math.cos(phi) * math.sin(lam)
    z = (n * (1.0 - WGS84_E2) + h) * s
    return np.array([x, y, z], dtype=float)


@dataclass(frozen=True)
class GeodeticPoint:
    """A location with its reference frame and epoch DECLARED.

    An undeclared epoch is refused: an ITRF coordinate without an epoch
    is not a coordinate, because the plate it sits on moves.
    """

    site_id: str
    latitude_deg: float
    longitude_deg: float
    height_m: float
    frame: str
    epoch: str
    role: str = "CONTROL"

    def __post_init__(self) -> None:
        if not self.frame:
            raise EarthFaceError(
                f"{self.site_id}: no reference frame declared")
        if not self.epoch:
            raise EarthFaceError(
                f"{self.site_id}: no epoch declared. An ITRF position "
                f"without an epoch is underdetermined; the crust moves.")
        # validates the angles
        geodetic_to_ecef(self.latitude_deg, self.longitude_deg,
                         self.height_m)

    def ecef(self) -> np.ndarray:
        return geodetic_to_ecef(self.latitude_deg, self.longitude_deg,
                                self.height_m)


#: Public, neutral CONTROL location. Sedona is used here only to
#: exercise the pipeline; naming it asserts nothing about the place.
SEDONA_FACE_CONTROL = GeodeticPoint(
    site_id="SEDONA_FACE_CONTROL",
    latitude_deg=34.8697,
    longitude_deg=-111.7610,
    height_m=1372.0,
    frame="ITRF2020",
    epoch="2026.0",
    role="CONTROL",
)


# --- stage 2: the South-Up view is a rotation, not a mirror -------------

#: Look at the planet from the south. det = (+1)(-1)(-1) = +1.
SOUTH_UP_ROTATION = np.diag([1.0, -1.0, -1.0])


def is_proper_rotation(R: np.ndarray, tol: float = 1e-12) -> bool:
    """True when ``R`` is orthogonal with determinant ``+1``."""
    M = np.asarray(R, dtype=float)
    if M.shape != (3, 3):
        return False
    if not np.allclose(M @ M.T, np.eye(3), atol=tol):
        return False
    return abs(float(np.linalg.det(M)) - 1.0) <= 1e-9


def refuse_mirror_view(R: np.ndarray) -> np.ndarray:
    """Return ``R`` if it is a proper rotation; refuse a reflection.

    ``diag(1, -1, -1)`` passes -- two sign flips are a half-turn about
    x, a change of viewpoint. ``diag(1, 1, -1)`` has ``det = -1``; it
    reverses handedness and would quietly turn every subsequent cross
    product, face normal and gradient sign inside out.
    """
    M = np.asarray(R, dtype=float)
    if M.shape != (3, 3):
        raise EarthFaceError("view must be a 3x3 matrix")
    if not np.allclose(M @ M.T, np.eye(3), atol=1e-12):
        raise EarthFaceError(
            "view matrix is not orthogonal; it is not a rigid view")
    det = float(np.linalg.det(M))
    if det < 0:
        raise EarthFaceError(
            f"det = {det:+.1f}: this view is a MIRROR, not a rotation. "
            f"A reflection reverses handedness, so every face normal, "
            f"cross product and gradient sign downstream would flip "
            f"without warning. South-Up must be the PROPER rotation "
            f"diag(1, -1, -1), whose determinant is +1.")
    return M


def south_up(vector: np.ndarray) -> np.ndarray:
    """Apply the South-Up proper rotation."""
    return refuse_mirror_view(SOUTH_UP_ROTATION) @ np.asarray(
        vector, dtype=float)


def city_ray(point: GeodeticPoint) -> np.ndarray:
    """Unit geocentric ray to the site, seen South-Up."""
    v = south_up(point.ecef())
    n = float(np.linalg.norm(v))
    if n == 0.0:
        raise EarthFaceError("geocentre has no ray")
    return v / n


# --- stage 3: the frozen canonical icosahedron --------------------------

PHI = (1.0 + math.sqrt(5.0)) / 2.0


@dataclass(frozen=True, eq=False)
class Icosahedron:
    """12 unit vertices, 20 outward-oriented triangular faces. FROZEN."""

    vertices: np.ndarray
    faces: tuple[tuple[int, int, int], ...]
    provenance: str = "CANONICAL_GOLDEN_RATIO_FROZEN_BEFORE_TARGET_DATA"

    def triangle(self, face_index: int) -> np.ndarray:
        i, j, k = self.faces[self._check(face_index)]
        return np.array([self.vertices[i], self.vertices[j],
                         self.vertices[k]])

    def centroid(self, face_index: int) -> np.ndarray:
        c = self.triangle(face_index).mean(axis=0)
        return c / float(np.linalg.norm(c))

    def normal(self, face_index: int) -> np.ndarray:
        a, b, c = self.triangle(face_index)
        n = np.cross(b - a, c - a)
        return n / float(np.linalg.norm(n))

    def _check(self, face_index: int) -> int:
        if not 0 <= face_index < len(self.faces):
            raise EarthFaceError(f"no face {face_index}")
        return face_index


def _build_canonical_icosahedron() -> Icosahedron:
    raw = []
    for s1 in (1.0, -1.0):
        for s2 in (1.0, -1.0):
            raw.append((0.0, s1 * 1.0, s2 * PHI))
            raw.append((s1 * 1.0, s2 * PHI, 0.0))
            raw.append((s2 * PHI, 0.0, s1 * 1.0))
    V = np.array(raw, dtype=float)
    V = V / np.linalg.norm(V, axis=1, keepdims=True)
    if V.shape != (12, 3):
        raise EarthFaceError("icosahedron must have 12 vertices")

    d = np.linalg.norm(V[:, None, :] - V[None, :, :], axis=-1)
    edge = float(np.min(d[d > 1e-9]))
    faces: list[tuple[int, int, int]] = []
    for i, j, k in combinations(range(12), 3):
        if (abs(d[i, j] - edge) < 1e-9 and abs(d[j, k] - edge) < 1e-9
                and abs(d[i, k] - edge) < 1e-9):
            tri = (i, j, k)
            a, b, c = V[i], V[j], V[k]
            if np.dot(np.cross(b - a, c - a), a + b + c) < 0:
                tri = (i, k, j)
            faces.append(tri)
    if len(faces) != 20:
        raise EarthFaceError(
            f"icosahedron must have 20 faces, built {len(faces)}")

    V.setflags(write=False)
    return Icosahedron(vertices=V, faces=tuple(faces))


#: Frozen before any target data is loaded. Never rotated afterwards.
CANONICAL_ICOSAHEDRON = _build_canonical_icosahedron()


def refuse_rotate_after_load(reason: str = "") -> None:
    """Rotating the frozen solid after target data is loaded is refused."""
    tail = f" ({reason})" if reason else ""
    raise EarthFaceError(
        f"the canonical icosahedron is FROZEN{tail}. Rotating it after "
        f"target data is loaded lets any site be moved onto any face, "
        f"which turns a geometric result into a fitted one. The solid "
        f"is fixed by the golden ratio before the data; if a different "
        f"orientation is wanted it must be declared in advance, as a "
        f"separate named hypothesis, and tested on its own.")


# --- stage 4: ray-face intersection, set-valued on edges ---------------

#: Barycentric slack. Inside this, an edge or vertex hit is ambiguous
#: and the answer is a SET of faces, not one face.
EDGE_TOLERANCE = 1e-9


def _unit(v: np.ndarray) -> np.ndarray:
    a = np.asarray(v, dtype=float)
    n = float(np.linalg.norm(a))
    if n == 0.0:
        raise EarthFaceError("zero-length direction")
    return a / n


def nearest_face_by_centroid(direction: np.ndarray,
                             ico: Icosahedron = CANONICAL_ICOSAHEDRON
                             ) -> int:
    """Face whose centroid has the maximum dot product with the ray."""
    d = _unit(direction)
    dots = [float(np.dot(d, ico.centroid(i))) for i in range(len(ico.faces))]
    return int(np.argmax(dots))


def ray_triangle_barycentric(direction: np.ndarray,
                             v0: np.ndarray, v1: np.ndarray,
                             v2: np.ndarray) -> tuple | None:
    """Moller-Trumbore from the origin: ``(t, u, v, w)`` or ``None``."""
    d = _unit(direction)
    e1 = v1 - v0
    e2 = v2 - v0
    p = np.cross(d, e2)
    det = float(np.dot(e1, p))
    if abs(det) < 1e-15:
        return None
    inv = 1.0 / det
    tvec = -np.asarray(v0, dtype=float)          # origin is the geocentre
    u = float(np.dot(tvec, p)) * inv
    q = np.cross(tvec, e1)
    v = float(np.dot(d, q)) * inv
    t = float(np.dot(e2, q)) * inv
    return t, u, v, 1.0 - u - v


def ray_face_intersection(direction: np.ndarray,
                          ico: Icosahedron = CANONICAL_ICOSAHEDRON,
                          tol: float = EDGE_TOLERANCE) -> frozenset[int]:
    """Which face does the ray pierce? Possibly more than one.

    The centroid with the largest dot product is the guess; every face
    is then verified by ray-triangle intersection. A ray through a face
    interior returns exactly one index. A ray within ``tol`` of a
    shared edge returns both faces; a ray through a vertex returns all
    five. That set is the honest answer -- collapsing it to one face
    would be a tie broken by index order, not by geometry.
    """
    d = _unit(direction)
    guess = nearest_face_by_centroid(d, ico)
    hits: set[int] = set()
    for i in range(len(ico.faces)):
        a, b, c = ico.triangle(i)
        bary = ray_triangle_barycentric(d, a, b, c)
        if bary is None:
            continue
        t, u, v, w = bary
        if t <= 0.0:
            continue
        if u >= -tol and v >= -tol and w >= -tol:
            hits.add(i)
    if not hits:
        raise EarthFaceError("ray pierces no face of the frozen solid")
    if guess not in hits:
        raise EarthFaceError(
            "centroid heuristic and ray-triangle verification disagree; "
            "the face assignment is not trustworthy")
    return frozenset(hits)


def face_hit_point(direction: np.ndarray, face_index: int,
                   ico: Icosahedron = CANONICAL_ICOSAHEDRON) -> np.ndarray:
    """Where the ray meets the plane of the given face."""
    d = _unit(direction)
    a, b, c = ico.triangle(face_index)
    bary = ray_triangle_barycentric(d, a, b, c)
    if bary is None or bary[0] <= 0.0:
        raise EarthFaceError(f"ray does not reach face {face_index}")
    return d * bary[0]


# --- stage 5: the local face frame -------------------------------------

@dataclass(frozen=True, eq=False)
class FaceFrame:
    """An orthonormal frame on one icosahedral face."""

    face_index: int
    origin: tuple
    normal: tuple
    tangent_u: tuple
    tangent_v: tuple

    def matrix(self) -> np.ndarray:
        """Columns ``[u, v, n]``; a proper rotation by construction."""
        return np.column_stack([np.array(self.tangent_u),
                                np.array(self.tangent_v),
                                np.array(self.normal)])

    def is_orthonormal(self, tol: float = 1e-12) -> bool:
        return is_proper_rotation(self.matrix(), tol=tol)


def local_face_frame(direction: np.ndarray, face_index: int,
                     ico: Icosahedron = CANONICAL_ICOSAHEDRON) -> FaceFrame:
    """Normal plus two tangents at the ray's hit point on a face."""
    n = ico.normal(face_index)
    origin = face_hit_point(direction, face_index, ico)
    a, b, _c = ico.triangle(face_index)
    u = _unit(b - a - np.dot(b - a, n) * n)
    v = np.cross(n, u)
    return FaceFrame(face_index=face_index,
                     origin=tuple(float(x) for x in origin),
                     normal=tuple(float(x) for x in n),
                     tangent_u=tuple(float(x) for x in u),
                     tangent_v=tuple(float(x) for x in v))


# --- stage 6: the magnetic gradient, and why it is a set ---------------

class MagneticScalar(Enum):
    """Candidate scalars a "magnetic gradient" could be taken of.

    Nothing in the source fixes which one is meant, so all of them are
    carried as candidates.
    """

    TOTAL_INTENSITY = "TOTAL_INTENSITY"
    HORIZONTAL_INTENSITY = "HORIZONTAL_INTENSITY"
    VERTICAL_COMPONENT = "VERTICAL_COMPONENT"
    DECLINATION = "DECLINATION"
    INCLINATION = "INCLINATION"
    POTENTIAL = "POTENTIAL"


#: Declared toy field model. A tilted centred dipole in dimensionless
#: units: enough structure for the six scalars to differ, and far too
#: little to be a field value anywhere.
DIPOLE_TILT_DEG = 11.0
DIPOLE_LON_2020_DEG = -72.0
DIPOLE_DRIFT_DEG_PER_YEAR = 0.2
FIELD_MODEL = "TILTED_CENTRED_DIPOLE_DECLARED_TOY_MODEL"

#: Default choices that are only defaults -- each is an alias axis.
DEFAULT_ALTITUDES_M = (0.0, 1000.0)
DEFAULT_EPOCHS = ("2020.0", "2026.0")
DEFAULT_SIGNS = (1, -1)

_GRADIENT_STEP_M = 1.0e3


def _epoch_year(epoch: str) -> float:
    try:
        return float(str(epoch).strip())
    except (TypeError, ValueError) as exc:
        raise EarthFaceError(
            f"epoch {epoch!r} is not a decimal year; a field model "
            f"without a declared epoch has no value") from exc


def dipole_axis(epoch: str) -> np.ndarray:
    """Model dipole axis at a declared epoch (unit vector)."""
    years = _epoch_year(epoch) - 2020.0
    tilt = math.radians(DIPOLE_TILT_DEG)
    lon = math.radians(DIPOLE_LON_2020_DEG
                       + DIPOLE_DRIFT_DEG_PER_YEAR * years)
    return np.array([math.sin(tilt) * math.cos(lon),
                     math.sin(tilt) * math.sin(lon),
                     -math.cos(tilt)], dtype=float)


def _dipole_field(position: np.ndarray, epoch: str) -> np.ndarray:
    r = np.asarray(position, dtype=float)
    dist = float(np.linalg.norm(r))
    if dist == 0.0:
        raise EarthFaceError("dipole field is singular at the centre")
    rhat = r / dist
    m = dipole_axis(epoch)
    return (3.0 * float(np.dot(m, rhat)) * rhat - m) / dist ** 3


def magnetic_scalar(position: np.ndarray, scalar: MagneticScalar,
                    epoch: str) -> float:
    """One scalar of the declared toy dipole, in model units."""
    r = np.asarray(position, dtype=float)
    dist = float(np.linalg.norm(r))
    rhat = r / dist
    B = _dipole_field(r, epoch)
    spin = np.array([0.0, 0.0, 1.0])
    east = np.cross(spin, rhat)
    ne = float(np.linalg.norm(east))
    if ne < 1e-9:
        raise EarthFaceError(
            "local north/east are degenerate on the spin axis")
    east = east / ne
    north = np.cross(rhat, east)
    x = float(np.dot(B, north))
    y = float(np.dot(B, east))
    z = -float(np.dot(B, rhat))          # down-positive
    h = math.hypot(x, y)
    if scalar is MagneticScalar.TOTAL_INTENSITY:
        return float(np.linalg.norm(B))
    if scalar is MagneticScalar.HORIZONTAL_INTENSITY:
        return h
    if scalar is MagneticScalar.VERTICAL_COMPONENT:
        return z
    if scalar is MagneticScalar.DECLINATION:
        return math.atan2(y, x)
    if scalar is MagneticScalar.INCLINATION:
        return math.atan2(z, h)
    if scalar is MagneticScalar.POTENTIAL:
        return float(np.dot(dipole_axis(epoch), rhat)) / dist ** 2
    raise EarthFaceError(f"unknown scalar {scalar!r}")


def horizontal_gradient(position: np.ndarray, frame: FaceFrame,
                        scalar: MagneticScalar, epoch: str,
                        altitude_m: float = 0.0) -> np.ndarray:
    """Gradient of one scalar projected into the face tangent plane."""
    p = np.asarray(position, dtype=float)
    p = p + float(altitude_m) * _unit(p)
    u = np.array(frame.tangent_u)
    v = np.array(frame.tangent_v)
    step = _GRADIENT_STEP_M
    gu = (magnetic_scalar(p + step * u, scalar, epoch)
          - magnetic_scalar(p - step * u, scalar, epoch)) / (2.0 * step)
    gv = (magnetic_scalar(p + step * v, scalar, epoch)
          - magnetic_scalar(p - step * v, scalar, epoch)) / (2.0 * step)
    return gu * u + gv * v


@dataclass(frozen=True)
class GradientZeroAlias:
    """One candidate zero direction, with every choice it depended on."""

    scalar: MagneticScalar
    sign: int
    altitude_m: float
    epoch: str
    direction: tuple
    field_model: str = FIELD_MODEL
    units: str = MODEL_UNITS
    evidence_class: str = ScientificType.ANALYTIC_MODEL.value


def _zero_direction(position: np.ndarray, frame: FaceFrame,
                    scalar: MagneticScalar, epoch: str,
                    altitude_m: float, sign: int) -> tuple:
    g = horizontal_gradient(position, frame, scalar, epoch, altitude_m)
    if float(np.linalg.norm(g)) < 1e-30:
        raise EarthFaceError(
            f"{scalar.value}: the horizontal gradient vanishes at this "
            f"point in the declared model, so no zero direction is "
            f"defined; the answer is BLOCKED_MISSING_DATA, not a guess")
    n = np.array(frame.normal)
    d = _unit(np.cross(n, g)) * (1 if int(sign) >= 0 else -1)
    return tuple(float(x) for x in d)


def gradient_zero_alias_set(position: np.ndarray, frame: FaceFrame,
                            scalars: tuple | None = None,
                            altitudes_m: tuple = DEFAULT_ALTITUDES_M,
                            epochs: tuple = DEFAULT_EPOCHS,
                            signs: tuple = DEFAULT_SIGNS
                            ) -> frozenset[GradientZeroAlias]:
    """Every candidate zero direction the unfixed choices allow.

    The product runs over scalar x altitude x epoch x sign. **Both**
    vector signs are kept: a zero direction is a line, and nothing in
    the pipeline picks an arrow along it. Fixing a sign requires an
    independent reason, not a preference.
    """
    chosen = tuple(scalars) if scalars else tuple(MagneticScalar)
    if len(chosen) < 2:
        raise EarthFaceError(
            "an alias set over fewer than two scalars is not an alias "
            "set; it is a choice already made")
    aliases: set[GradientZeroAlias] = set()
    for scalar in chosen:
        for alt in altitudes_m:
            for epoch in epochs:
                for sign in signs:
                    d = _zero_direction(position, frame, scalar, epoch,
                                        float(alt), int(sign))
                    aliases.add(GradientZeroAlias(
                        scalar=scalar, sign=int(sign),
                        altitude_m=float(alt), epoch=str(epoch),
                        direction=d))
    return frozenset(aliases)


def refuse_single_zero_direction(scalar: MagneticScalar | None = None,
                                 sign: int | None = None,
                                 altitude_m: float | None = None,
                                 epoch: str | None = None,
                                 position: np.ndarray | None = None,
                                 frame: FaceFrame | None = None) -> tuple:
    """Refuse "the" zero unless scalar, sign, altitude and epoch are set.

    With all four independently fixed this returns that one direction --
    which is still one member of the alias set, labelled by the choices
    that produced it. With any of them unfixed it raises, because the
    output would be an arbitrary element presented as a result.
    """
    missing = [name for name, value in (("scalar", scalar), ("sign", sign),
                                        ("altitude_m", altitude_m),
                                        ("epoch", epoch))
               if value is None]
    if missing:
        raise EarthFaceError(
            f"cannot report one magnetic-gradient zero direction while "
            f"{', '.join(missing)} {'is' if len(missing) == 1 else 'are'} "
            f"unfixed. The zero is a line, not an arrow, and it moves "
            f"with the scalar, the altitude and the epoch. Unfixed "
            f"choices produce an ALIAS SET; use "
            f"gradient_zero_alias_set() and report all of it.")
    if position is None or frame is None:
        raise EarthFaceError(
            "a zero direction needs a position and a face frame")
    return _zero_direction(position, frame, scalar, str(epoch),
                           float(altitude_m), int(sign))


# --- the whole pipeline, and what it does not say ----------------------

def earth_face_pipeline(point: GeodeticPoint = SEDONA_FACE_CONTROL) -> dict:
    """Run every stage and report it, aliases included."""
    ecef = point.ecef()
    refuse_mirror_view(SOUTH_UP_ROTATION)
    ray = city_ray(point)
    faces = ray_face_intersection(ray)
    face_index = nearest_face_by_centroid(ray)
    frame = local_face_frame(ray, face_index)
    position = south_up(ecef)
    aliases = gradient_zero_alias_set(position, frame)
    return {
        "site_id": point.site_id,
        "role": point.role,
        "frame": point.frame,
        "epoch_declared": point.epoch,
        "ecef_m": tuple(float(x) for x in ecef),
        "south_up_is_proper_rotation": is_proper_rotation(
            SOUTH_UP_ROTATION),
        "city_ray": tuple(float(x) for x in ray),
        "candidate_faces": tuple(sorted(faces)),
        "face_assignment_is_unique": len(faces) == 1,
        "face_frame_orthonormal": frame.is_orthonormal(),
        "icosahedron_frozen": True,
        "alias_count": len(aliases),
        "alias_scalars": tuple(sorted(a.scalar.value for a in aliases)),
        "field_model": FIELD_MODEL,
        "units": MODEL_UNITS,
        "verdict": VERDICT,
    }


def earthface_report() -> dict:
    return {
        "pipeline": [
            "geodetic(lat, lon, h)", "ITRF at a declared epoch",
            "ECEF on WGS-84", "South-Up proper rotation diag(1,-1,-1)",
            "city geocentric ray", "frozen canonical icosahedron face",
            "ray-face intersection (set-valued on edges/vertices)",
            "local face frame",
            "horizontal magnetic-gradient direction (candidate zero)"],
        "arithmetic_stages": [
            "geodetic_to_ecef", "south_up", "ray_face_intersection",
            "local_face_frame"],
        "choice_axes": ["scalar", "sign", "altitude", "epoch"],
        "scalars_unresolved": [s.value for s in MagneticScalar],
        "both_signs_preserved": True,
        "field_model": FIELD_MODEL,
        "units": MODEL_UNITS,
        "control_location": SEDONA_FACE_CONTROL.site_id,
        "evidence_class": EVIDENCE_CLASS,
        "measured_here": "nothing",
        "physical_validation": PHYSICAL_VALIDATION,
        "what_this_does_not_say": (
            "It does not say that a magnetic zero exists at any site, "
            "that any site sits on a meaningful face, or that the "
            "icosahedron is a feature of the Earth. No magnetometer was "
            "read, no survey was made and no location was visited; the "
            "field here is a declared toy dipole in dimensionless model "
            "units, not a field value. The control location is a "
            "control and nothing more. Because the scalar, the sign, "
            "the altitude and the epoch are all unfixed, the output is "
            "an ALIAS SET of candidate directions rather than a "
            "direction, and a specifiable zero is not a detected one."),
        "verdict": VERDICT,
    }
