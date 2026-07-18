"""P02 — dual-helical coil digital twin.

A geometric and magnetostatic model of two helical windings (the
source names copper and silver) wound on a cylindrical crystal former,
"interwoven at approximately 45 degrees to each other".

    NO COIL HAS BEEN WOUND. No crystal has been driven, no current has
    been passed, no field has been measured. Every number this module
    returns comes from a declared geometry and a filament magnetostatic
    model. Nothing here is bench data and nothing here is physical
    evidence.

What the model actually is
--------------------------

Each winding is discretised into straight current filaments and the
exact finite-segment Biot-Savart contribution is summed. That is a
*magnetostatic filament* model, and it carries four approximations
that are stated here rather than hidden:

1. **Filament, not conductor.** The wire has zero cross-section. The
   field inside the physical conductor is wrong by construction, so
   :func:`biot_savart_field` REFUSES evaluation points closer to the
   path than the wire radius instead of returning a large number.
2. **Magnetostatic.** No displacement current, no retardation, no skin
   or proximity effect. Valid while the drive wavelength is much
   longer than the coil (at 1496 Hz, lambda ~ 200 km, so this holds
   comfortably for a benchtop coil).
3. **No material response.** The quartz former is treated as vacuum;
   mu_r = 1. Quartz is diamagnetic at the 1e-5 level, which is below
   the discretisation error of this model.
4. **Polygonal discretisation.** An N-sided inscribed polygon
   overestimates the on-axis field of a circular turn by roughly
   pi^2/(3 N^2). This is the dominant numeric error and it is why
   :func:`validate_against_solenoid` exists.

The correctness anchor is :func:`validate_against_solenoid`: the
numeric sum over a long single helix is compared against the analytic
infinite-solenoid limit mu0*n*I. A solver that cannot reproduce a
result everyone already agrees on is not permitted to be used on a
result nobody agrees on.

Claim R6-C-002 enters through
:func:`common_differential_decomposition` and
:func:`decompose_pulse_trains`: the source's alternating drive is
decomposed into common and differential modes, and both are reported.
The decomposition names a drive structure; it does not measure a
"torsion field", for which R6 has no instrument.

Units: SI throughout. Lengths metre, currents ampere, flux density
tesla, angles radian unless a name ends in ``_deg``, inductance henry.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, asdict

#: Vacuum permeability (H/m). The pre-2019 exact value 4e-7*pi is used
#: as specified by the programme brief. The CODATA measured value
#: differs in the 10th significant figure, far below this model's
#: discretisation error.
MU0 = 4e-7 * math.pi

HANDEDNESS = ("RIGHT", "LEFT")

#: Nothing in this module is measurement.
EVIDENCE_CLASS = "SYNTHETIC_MODEL"

Vec3 = tuple[float, float, float]


class GeometryError(ValueError):
    """Raised when a declared coil geometry is not physically buildable."""


class SingularEvaluationError(ValueError):
    """Raised when a field point lies on or inside the current filament.

    The filament model has no finite answer there, so the model refuses
    rather than returning a large number that a reader might mistake
    for a prediction.
    """


# --------------------------------------------------------------------
# Small vector helpers (kept local so the module has no dependencies)
# --------------------------------------------------------------------

def _sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _scale(a: Vec3, s: float) -> Vec3:
    return (a[0] * s, a[1] * s, a[2] * s)


def _dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a: Vec3, b: Vec3) -> Vec3:
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _norm(a: Vec3) -> float:
    return math.sqrt(_dot(a, a))


def _unit(a: Vec3) -> Vec3:
    n = _norm(a)
    if n == 0.0:
        raise GeometryError("cannot normalise a zero-length vector")
    return _scale(a, 1.0 / n)


def _point_segment_distance(p: Vec3, a: Vec3, b: Vec3) -> float:
    """Shortest distance (m) from point ``p`` to segment ``a``->``b``."""
    ab = _sub(b, a)
    ab2 = _dot(ab, ab)
    if ab2 == 0.0:
        return _norm(_sub(p, a))
    t = _dot(_sub(p, a), ab) / ab2
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    return _norm(_sub(p, _add(a, _scale(ab, t))))


# --------------------------------------------------------------------
# Geometry
# --------------------------------------------------------------------

@dataclass(frozen=True)
class HelixGeometry:
    """One helical winding on a cylinder about the +z axis.

    Units
    -----
    radius_m         : m, cylinder radius the wire centreline follows
    pitch_m          : m, axial advance per full turn
    turns            : dimensionless count (may be fractional, > 0)
    handedness       : "RIGHT" or "LEFT"; sets the sign of the
                       azimuthal advance with increasing z
    start_phase_rad  : rad, azimuth of the first point
    wire_diameter_m  : m, conductor diameter (used only for the
                       refusal radius and the winding-feasibility check)
    label            : free text, e.g. "copper" / "silver"
    """

    radius_m: float
    pitch_m: float
    turns: float
    handedness: str = "RIGHT"
    start_phase_rad: float = 0.0
    wire_diameter_m: float = 1.0e-3
    label: str = ""

    def __post_init__(self) -> None:
        for name in ("radius_m", "pitch_m", "wire_diameter_m"):
            v = getattr(self, name)
            if not math.isfinite(v) or v <= 0.0:
                raise GeometryError(
                    f"{name} must be a finite positive length, got {v!r}")
        if not math.isfinite(self.turns) or self.turns <= 0:
            raise GeometryError(
                f"turns must be > 0, got {self.turns!r}; a coil with no "
                "turns is not a coil")
        if self.handedness not in HANDEDNESS:
            raise GeometryError(
                f"handedness must be one of {HANDEDNESS}, got "
                f"{self.handedness!r}")
        if not math.isfinite(self.start_phase_rad):
            raise GeometryError("start_phase_rad must be finite")
        if self.pitch_m < self.wire_diameter_m:
            raise GeometryError(
                f"pitch {self.pitch_m} m is smaller than the wire "
                f"diameter {self.wire_diameter_m} m: adjacent turns "
                "would overlap and this winding cannot be wound")

    # -- derived quantities ------------------------------------------

    @property
    def sense(self) -> int:
        """+1 for RIGHT-handed, -1 for LEFT-handed azimuthal advance."""
        return 1 if self.handedness == "RIGHT" else -1

    @property
    def length_m(self) -> float:
        """Axial length of the winding (m)."""
        return self.pitch_m * self.turns

    @property
    def turns_per_m(self) -> float:
        """Turn density n (1/m)."""
        return 1.0 / self.pitch_m

    @property
    def pitch_angle_rad(self) -> float:
        """Angle (rad) between the wire and the azimuthal plane.

        ``atan(pitch / (2*pi*radius))``. Zero for a stack of rings.
        """
        return math.atan2(self.pitch_m, 2.0 * math.pi * self.radius_m)

    @property
    def wire_length_m(self) -> float:
        """Length of conductor required (m), exact for an ideal helix."""
        circ = 2.0 * math.pi * self.radius_m
        return self.turns * math.hypot(circ, self.pitch_m)

    def points(self, n_per_turn: int = 24) -> list[Vec3]:
        """Sample the centreline: list of (x, y, z) in metres.

        ``n_per_turn`` samples per full turn; the returned list has
        ``round(turns * n_per_turn) + 1`` points so that consecutive
        pairs form the segments of the discretisation.

        Handedness enters as the sign of the azimuthal advance, so a
        LEFT helix is the mirror image of a RIGHT helix with the same
        pitch: x is shared, y is negated (for ``start_phase_rad`` 0).
        """
        if n_per_turn < 3:
            raise GeometryError(
                f"n_per_turn must be >= 3 to enclose area, got {n_per_turn}")
        n_seg = int(round(self.turns * n_per_turn))
        if n_seg < 1:
            raise GeometryError(
                "discretisation produced no segments; raise n_per_turn")
        out: list[Vec3] = []
        for i in range(n_seg + 1):
            frac = i / n_per_turn                      # turns completed
            theta = self.start_phase_rad + self.sense * 2.0 * math.pi * frac
            out.append((self.radius_m * math.cos(theta),
                        self.radius_m * math.sin(theta),
                        self.pitch_m * frac))
        return out

    def tangent(self, turn_fraction: float = 0.0) -> Vec3:
        """Unit tangent (dimensionless) at a given number of turns in.

        Points in the direction of increasing parameter, i.e. the
        direction of positive current.
        """
        theta = (self.start_phase_rad
                 + self.sense * 2.0 * math.pi * turn_fraction)
        return self.tangent_at_azimuth(theta)

    def tangent_at_azimuth(self, theta_rad: float) -> Vec3:
        """Unit tangent (dimensionless) where the wire is at azimuth
        ``theta_rad``.

        Two windings physically cross at a shared point, which means a
        shared azimuth — not a shared curve parameter. Crossing angles
        must therefore be taken from this method, not from
        :meth:`tangent`, whose parameter includes the start phase.
        """
        two_pi_r = 2.0 * math.pi * self.radius_m
        v = (-self.sense * two_pi_r * math.sin(theta_rad),
             self.sense * two_pi_r * math.cos(theta_rad),
             self.pitch_m)
        return _unit(v)

    def as_record(self) -> dict:
        d = asdict(self)
        d.update(
            length_m=self.length_m,
            turns_per_m=self.turns_per_m,
            pitch_angle_rad=self.pitch_angle_rad,
            pitch_angle_deg=math.degrees(self.pitch_angle_rad),
            wire_length_m=self.wire_length_m,
            units={
                "radius_m": "m", "pitch_m": "m", "turns": "1",
                "start_phase_rad": "rad", "wire_diameter_m": "m",
                "length_m": "m", "turns_per_m": "1/m",
                "pitch_angle_rad": "rad", "wire_length_m": "m",
            },
            evidence_class=EVIDENCE_CLASS,
        )
        return d


def pitch_for_crossing_angle(radius_m: float, crossing_angle_deg: float,
                             opposed_handedness: bool = True) -> float:
    """Pitch (m) giving a declared wire-to-wire crossing angle.

    The source says the two windings are "interwoven at approximately
    45 degrees to each other". For two helices of the same radius and
    pitch:

    - opposite handedness: the tangents differ by ``2 * pitch_angle``,
      so a 45 deg crossing needs a pitch angle of 22.5 deg;
    - same handedness: the tangents are parallel everywhere and the
      crossing angle is identically 0, so the request is refused.

    Returns ``2*pi*radius * tan(crossing/2)``.
    """
    if not opposed_handedness:
        raise GeometryError(
            "two co-handed helices of equal pitch have parallel tangents "
            "everywhere; a non-zero crossing angle requires opposite "
            "handedness or unequal pitch")
    if not (0.0 < crossing_angle_deg <= 90.0):
        raise GeometryError(
            f"crossing angle must be in (0, 90] deg, got "
            f"{crossing_angle_deg!r}. Wires are undirected lines, so the "
            "crossing angle is the acute angle; 120 deg between lines is "
            "60 deg.")
    half = math.radians(crossing_angle_deg) / 2.0
    return 2.0 * math.pi * radius_m * math.tan(half)


@dataclass(frozen=True)
class DualHelix:
    """Two windings on a shared former with a declared angular offset.

    Units
    -----
    angular_offset_rad : rad, added to helix ``b``'s start phase. This
                         is the azimuthal separation of the two wire
                         entry points, NOT the crossing angle.

    The *crossing angle* between the two wires is a property of the
    pitches and handedness, not of the offset; read it from
    :attr:`crossing_angle_rad` and set it with
    :func:`pitch_for_crossing_angle`.
    """

    a: HelixGeometry
    b: HelixGeometry
    angular_offset_rad: float = math.pi

    def __post_init__(self) -> None:
        if not math.isfinite(self.angular_offset_rad):
            raise GeometryError("angular_offset_rad must be finite")
        if not isinstance(self.a, HelixGeometry) or \
                not isinstance(self.b, HelixGeometry):
            raise GeometryError("both windings must be HelixGeometry")

    @property
    def b_offset(self) -> HelixGeometry:
        """Winding ``b`` with the declared angular offset applied."""
        return HelixGeometry(
            radius_m=self.b.radius_m,
            pitch_m=self.b.pitch_m,
            turns=self.b.turns,
            handedness=self.b.handedness,
            start_phase_rad=self.b.start_phase_rad + self.angular_offset_rad,
            wire_diameter_m=self.b.wire_diameter_m,
            label=self.b.label,
        )

    @property
    def crossing_angle_rad(self) -> float:
        """Acute angle (rad, in [0, pi/2]) between the two wire lines
        where they cross.

        Taken at a shared azimuth, because that is where the wires
        actually cross; the angular offset shifts *where* along the
        former the crossings occur, not the angle at which they occur.

        Wires are undirected lines: the sign of the current is a wiring
        convention, so the reported angle is folded into [0, 90] deg.
        Two counter-wound helices of pitch angle ``alpha`` cross at
        ``2*alpha``; two co-handed helices of equal pitch never cross at
        all and report 0.

        For helices of unequal pitch the angle varies with radius-scaled
        geometry; this property is exact for equal radii.
        """
        ta = self.a.tangent_at_azimuth(0.0)
        tb = self.b.tangent_at_azimuth(0.0)
        c = max(-1.0, min(1.0, abs(_dot(ta, tb))))
        return math.acos(c)

    @property
    def crossing_angle_deg(self) -> float:
        return math.degrees(self.crossing_angle_rad)

    @property
    def co_handed(self) -> bool:
        return self.a.handedness == self.b.handedness

    def as_record(self) -> dict:
        return {
            "a": self.a.as_record(),
            "b": self.b.as_record(),
            "angular_offset_rad": self.angular_offset_rad,
            "crossing_angle_rad": self.crossing_angle_rad,
            "crossing_angle_deg": self.crossing_angle_deg,
            "co_handed": self.co_handed,
            "units": {"angular_offset_rad": "rad",
                      "crossing_angle_rad": "rad",
                      "crossing_angle_deg": "deg"},
            "evidence_class": EVIDENCE_CLASS,
            "note": "declared geometry only; no coil has been wound",
        }


def dual_helix_at_crossing_angle(radius_m: float, turns: float,
                                 crossing_angle_deg: float = 45.0,
                                 wire_diameter_m: float = 1.0e-3,
                                 angular_offset_rad: float = math.pi,
                                 labels: tuple[str, str] = ("copper",
                                                            "silver"),
                                 ) -> DualHelix:
    """Build the source's configuration: two counter-wound helices whose
    wires cross at ``crossing_angle_deg`` (source says ~45 deg).

    Units: metres, dimensionless turns, degrees for the crossing angle.
    """
    pitch = pitch_for_crossing_angle(radius_m, crossing_angle_deg, True)
    a = HelixGeometry(radius_m, pitch, turns, "RIGHT", 0.0,
                      wire_diameter_m, labels[0])
    b = HelixGeometry(radius_m, pitch, turns, "LEFT", 0.0,
                      wire_diameter_m, labels[1])
    return DualHelix(a, b, angular_offset_rad)


# --------------------------------------------------------------------
# Magnetostatics
# --------------------------------------------------------------------

def _segment_field(a: Vec3, b: Vec3, current_a: float, p: Vec3) -> Vec3:
    """Exact field (T) at ``p`` from a straight filament ``a``->``b``.

    Closed form for a finite straight segment:

        B = (mu0 I / 4pi) * (r1 x r2)(|r1| + |r2|)
                          / (|r1||r2| (|r1||r2| + r1.r2))

    with r1 = p - a and r2 = p - b, current flowing a -> b. Caller is
    responsible for having excluded singular points.
    """
    r1 = _sub(p, a)
    r2 = _sub(p, b)
    n1 = _norm(r1)
    n2 = _norm(r2)
    cr = _cross(r1, r2)
    denom = n1 * n2 * (n1 * n2 + _dot(r1, r2))
    if denom == 0.0:
        raise SingularEvaluationError(
            "field point is collinear with a current segment; the "
            "filament model has no finite value there")
    k = MU0 * current_a / (4.0 * math.pi) * (n1 + n2) / denom
    return _scale(cr, k)


def _path_field(pts: list[Vec3], current_a: float, p: Vec3,
                min_distance_m: float) -> Vec3:
    total = (0.0, 0.0, 0.0)
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        if _point_segment_distance(p, a, b) < min_distance_m:
            raise SingularEvaluationError(
                f"field point {p} lies within {min_distance_m} m of "
                f"segment {i} ({a} -> {b}). This model is a zero-radius "
                "filament: inside the conductor its answer is wrong, not "
                "merely imprecise, so it is refused rather than returned.")
        total = _add(total, _segment_field(a, b, current_a, p))
    return total


def biot_savart_field(dual: DualHelix, current_a, point: Vec3,
                      n_per_turn: int = 24,
                      min_distance_m: float | None = None) -> Vec3:
    """Flux density (Bx, By, Bz) in tesla at ``point`` (metres).

    Parameters
    ----------
    dual : DualHelix
    current_a : float, or (i_a, i_b) in amperes. A scalar drives both
        windings with the same current; a pair drives them separately,
        which is what the alternating programme of claim R6-C-002
        requires.
    point : (x, y, z) in metres.
    n_per_turn : segments per turn of the discretisation.
    min_distance_m : refusal radius in metres. Defaults to the larger
        wire radius of the two windings, because inside the physical
        conductor a filament model is wrong rather than imprecise.

    Raises
    ------
    SingularEvaluationError
        If ``point`` is closer than ``min_distance_m`` to either path.
    """
    if isinstance(current_a, (tuple, list)):
        if len(current_a) != 2:
            raise ValueError(
                "current_a as a sequence must be exactly (i_a, i_b) A")
        i_a, i_b = float(current_a[0]), float(current_a[1])
    else:
        i_a = i_b = float(current_a)
    if not (math.isfinite(i_a) and math.isfinite(i_b)):
        raise ValueError("currents must be finite amperes")
    if len(point) != 3 or not all(math.isfinite(c) for c in point):
        raise ValueError("point must be a finite (x, y, z) in metres")

    if min_distance_m is None:
        min_distance_m = max(dual.a.wire_diameter_m,
                             dual.b.wire_diameter_m) / 2.0
    if min_distance_m <= 0.0:
        raise ValueError("min_distance_m must be > 0 m")

    p = (float(point[0]), float(point[1]), float(point[2]))
    total = (0.0, 0.0, 0.0)
    if i_a != 0.0:
        total = _add(total, _path_field(dual.a.points(n_per_turn), i_a, p,
                                        min_distance_m))
    else:
        # Still check the geometry so a zero-current call cannot be used
        # to sneak an on-conductor evaluation past the refusal.
        _path_field(dual.a.points(n_per_turn), 0.0, p, min_distance_m)
    if i_b != 0.0:
        total = _add(total, _path_field(dual.b_offset.points(n_per_turn),
                                        i_b, p, min_distance_m))
    else:
        _path_field(dual.b_offset.points(n_per_turn), 0.0, p,
                    min_distance_m)
    return total


def helix_field(geom: HelixGeometry, current_a: float, point: Vec3,
                n_per_turn: int = 24,
                min_distance_m: float | None = None) -> Vec3:
    """Flux density (T) at ``point`` (m) from a single winding."""
    if min_distance_m is None:
        min_distance_m = geom.wire_diameter_m / 2.0
    p = (float(point[0]), float(point[1]), float(point[2]))
    return _path_field(geom.points(n_per_turn), float(current_a), p,
                       min_distance_m)


# --------------------------------------------------------------------
# Analytic anchor
# --------------------------------------------------------------------

def axial_field_analytic(radius_m: float, turns_per_m: float,
                         current_a: float) -> float:
    """Infinite-solenoid axial flux density B = mu0 * n * I, in tesla.

    Units: radius m (accepted for interface symmetry and validity
    checking only — it does not appear in the infinite-solenoid
    result), turns_per_m 1/m, current A. Returns T.

    Validity: exact only in the limit length >> radius, zero pitch
    angle, and on the axis. A real finite solenoid of length L is lower
    by the factor L / sqrt(L^2 + 4 r^2) at its centre; see
    :func:`axial_field_finite_solenoid`.
    """
    if not (math.isfinite(radius_m) and radius_m > 0.0):
        raise GeometryError("radius_m must be a finite positive length")
    if not (math.isfinite(turns_per_m) and turns_per_m > 0.0):
        raise GeometryError("turns_per_m must be finite and positive")
    if not math.isfinite(current_a):
        raise ValueError("current_a must be finite")
    return MU0 * turns_per_m * current_a


def axial_field_finite_solenoid(radius_m: float, length_m: float,
                                turns_per_m: float,
                                current_a: float) -> float:
    """Centre axial flux density (T) of a finite ideal solenoid.

    ``mu0 n I * L / sqrt(L^2 + 4 r^2)``. Still ignores the pitch angle
    (the helix's net axial current), which is a first-order-small
    correction for length >> pitch.
    """
    if not (math.isfinite(length_m) and length_m > 0.0):
        raise GeometryError("length_m must be a finite positive length")
    inf = axial_field_analytic(radius_m, turns_per_m, current_a)
    return inf * length_m / math.sqrt(length_m ** 2 + 4.0 * radius_m ** 2)


def validate_against_solenoid(radius_m: float = 0.005,
                              turns: int = 300,
                              pitch_m: float = 0.002,
                              current_a: float = 1.0,
                              n_per_turn: int = 36,
                              handedness: str = "RIGHT") -> dict:
    """Correctness anchor: numeric Biot-Savart vs the analytic limit.

    Sums the discretised finite-segment field of one long helix at its
    axial centre and compares it against ``mu0 * n * I``.

    Returns a dict (units in the ``units`` key):

    ``numeric_bz_t``            summed Bz on axis at the centre, T
    ``analytic_infinite_bz_t``  mu0 n I, T
    ``analytic_finite_bz_t``    finite-length corrected, T
    ``relative_error_infinite`` |numeric - infinite| / infinite
    ``relative_error_finite``   |numeric - finite| / finite
    ``aspect_ratio``            length / radius
    ``transverse_bx_t``, ``transverse_by_t``  off-axis leakage, should
                                be ~0 on axis and is reported so that a
                                bookkeeping error cannot hide

    The ``relative_error_finite`` figure is the meaningful one: it
    compares like with like. ``relative_error_infinite`` also includes
    the physical finite-length shortfall, which is not a solver error —
    at the defaults it converges to 2r^2/L^2 = 1.4e-4, exactly the
    expected shortfall, and so it does NOT fall with ``n_per_turn``.
    Only ``relative_error_finite`` is a discretisation diagnostic.
    """
    geom = HelixGeometry(radius_m, pitch_m, turns, handedness,
                         0.0, min(pitch_m, 1.0e-3))
    centre = (0.0, 0.0, geom.length_m / 2.0)
    bx, by, bz = helix_field(geom, current_a, centre, n_per_turn)
    inf = axial_field_analytic(radius_m, geom.turns_per_m, current_a)
    fin = axial_field_finite_solenoid(radius_m, geom.length_m,
                                      geom.turns_per_m, current_a)
    sign = geom.sense
    return {
        "numeric_bz_t": bz,
        "analytic_infinite_bz_t": sign * inf,
        "analytic_finite_bz_t": sign * fin,
        "relative_error_infinite": abs(bz - sign * inf) / abs(inf),
        "relative_error_finite": abs(bz - sign * fin) / abs(fin),
        "transverse_bx_t": bx,
        "transverse_by_t": by,
        "aspect_ratio": geom.length_m / radius_m,
        "segments": int(round(turns * n_per_turn)),
        # Upper bound only: pi^2/(3N^2) is the polygon overestimate for a
        # SINGLE ring evaluated at its own centre. In a long solenoid the
        # centre field is dominated by distant turns, for which the
        # polygon error is far smaller, so the observed error is one to
        # three orders of magnitude below this bound. Reported as a
        # bound, not as a prediction.
        "single_turn_polygon_error_bound":
            math.pi ** 2 / (3.0 * n_per_turn ** 2),
        "units": {"numeric_bz_t": "T", "analytic_infinite_bz_t": "T",
                  "analytic_finite_bz_t": "T",
                  "relative_error_infinite": "1",
                  "relative_error_finite": "1", "aspect_ratio": "1"},
        "evidence_class": EVIDENCE_CLASS,
        "note": ("numeric model validated against a textbook analytic "
                 "limit; this validates the solver, not any claim"),
    }


# --------------------------------------------------------------------
# Claim R6-C-002: common / differential decomposition
# --------------------------------------------------------------------

def common_differential_decomposition(i1: float, i2: float) -> dict:
    """Split a two-winding drive into common and differential modes.

    Units: ``i1``, ``i2`` and both outputs in amperes.

        common       = (i1 + i2) / 2      drives a net axial field
        differential = (i1 - i2) / 2      drives the counter-circulating
                                          component

    Implements the translation of claim R6-C-002. The decomposition is
    a statement about the drive, not about any field observable that
    the source names.
    """
    if not (math.isfinite(i1) and math.isfinite(i2)):
        raise ValueError("currents must be finite amperes")
    common = (i1 + i2) / 2.0
    differential = (i1 - i2) / 2.0
    total = abs(common) + abs(differential)
    return {
        "i1_a": i1,
        "i2_a": i2,
        "common_mode_a": common,
        "differential_mode_a": differential,
        "differential_ratio": (abs(differential) / total
                               if total > 0.0 else 0.0),
        "purely_differential": common == 0.0 and differential != 0.0,
        "purely_common": differential == 0.0 and common != 0.0,
        "units": {"i1_a": "A", "i2_a": "A", "common_mode_a": "A",
                  "differential_mode_a": "A",
                  "differential_ratio": "1"},
        "claim": "R6-C-002",
        "evidence_class": EVIDENCE_CLASS,
    }


def decompose_pulse_trains(train1, train2, amplitude_a: float = 1.0,
                           bipolar: bool = False) -> dict:
    """Decompose two 0/1 pulse trains slot by slot.

    ``train1`` and ``train2`` are equal-length sequences of 0 and 1 —
    the source's copper ``1-0-1-0-1-0`` and silver ``0-1-0-1-0-1``.

    Parameters
    ----------
    amplitude_a : ampere value of a "1" slot.
    bipolar : if False (default) a slot is driven at 0 A or
        ``amplitude_a``; if True, "0" maps to ``-amplitude_a``.

    An honest result worth stating plainly
    --------------------------------------
    With the unipolar mapping the source actually describes, the
    alternating programme is NOT purely differential: every active slot
    carries an equal common-mode component of ``amplitude_a / 2``. The
    ``purely_differential_fraction`` is therefore 0.0 for the source
    trains, while ``antiphase_fraction`` (the slots where the two
    windings differ at all) is 1.0.

    Only under the bipolar mapping, where "0" means "driven the other
    way" rather than "off", does the programme become purely
    differential. R6 reports both rather than choosing the flattering
    one. The distinction is physical: a unipolar alternating drive
    produces a net axial field at half amplitude, a bipolar one does
    not.

    Units: all current fields in amperes.
    """
    t1 = [int(x) for x in train1]
    t2 = [int(x) for x in train2]
    if len(t1) != len(t2):
        raise ValueError(
            f"pulse trains must be the same length, got {len(t1)} and "
            f"{len(t2)}")
    if not t1:
        raise ValueError("pulse trains must have at least one slot")
    for seq, name in ((t1, "train1"), (t2, "train2")):
        for v in seq:
            if v not in (0, 1):
                raise ValueError(
                    f"{name} must contain only 0 and 1, found {v!r}")
    if not math.isfinite(amplitude_a) or amplitude_a <= 0.0:
        raise ValueError("amplitude_a must be a finite positive current")

    def level(bit: int) -> float:
        if bit == 1:
            return amplitude_a
        return -amplitude_a if bipolar else 0.0

    slots = []
    n_pure_diff = 0
    n_antiphase = 0
    for k, (a, b) in enumerate(zip(t1, t2)):
        d = common_differential_decomposition(level(a), level(b))
        d["slot"] = k
        slots.append(d)
        if d["purely_differential"]:
            n_pure_diff += 1
        if a != b:
            n_antiphase += 1

    n = len(slots)
    return {
        "slots": slots,
        "n_slots": n,
        "bipolar": bipolar,
        "amplitude_a": amplitude_a,
        "purely_differential_fraction": n_pure_diff / n,
        "antiphase_fraction": n_antiphase / n,
        "mean_common_mode_a": sum(s["common_mode_a"] for s in slots) / n,
        "mean_abs_differential_a":
            sum(abs(s["differential_mode_a"]) for s in slots) / n,
        "units": {"amplitude_a": "A", "mean_common_mode_a": "A",
                  "mean_abs_differential_a": "A",
                  "purely_differential_fraction": "1",
                  "antiphase_fraction": "1"},
        "claim": "R6-C-002",
        "evidence_class": EVIDENCE_CLASS,
        "note": ("unipolar 0/1 alternation carries an equal common-mode "
                 "component and is not purely differential; only the "
                 "bipolar mapping is"
                 if not bipolar else
                 "bipolar mapping: 0 means driven negative, not off"),
    }


#: The source's programme, verbatim in structure.
SOURCE_TRAIN_COPPER = (1, 0, 1, 0, 1, 0)
SOURCE_TRAIN_SILVER = (0, 1, 0, 1, 0, 1)


# --------------------------------------------------------------------
# Coupling
# --------------------------------------------------------------------

def mutual_inductance_estimate(dual: DualHelix,
                               overlap_length_m: float | None = None
                               ) -> dict:
    """Mutual inductance estimate (H) for the two windings.

    APPROXIMATION USED
    ------------------
    The long-solenoid (uniform interior field) approximation:

        M ~= s * mu0 * n1 * n2 * A_min * L_overlap
        L_self_i ~= mu0 * n_i^2 * A_i * length_i

    where ``A_min`` is the cross-section of the smaller winding, and
    ``s`` is +1 when the two windings are co-handed and -1 when they
    are counter-wound (their axial fields oppose). Coupling
    coefficient ``k = M / sqrt(L1 * L2)``.

    VALIDITY RANGE — read before quoting a number
    ---------------------------------------------
    - Requires both windings long compared with their radius. The
      returned ``valid`` flag is True only when both aspect ratios
      (length / radius) are >= 10; below that the end-field leakage
      this formula ignores is tens of percent.
    - Requires coaxial windings and treats the overlap as complete and
      uniform.
    - Assumes mu_r = 1: the quartz former is non-magnetic, so this is
      good, but any ferrous fixture invalidates it.
    - **It is independent of ``angular_offset_rad`` and of the crossing
      angle except through the sign.** In the uniform-interior limit
      the azimuthal phase of a winding does not change the flux it
      links. So this estimate cannot, even in principle, test the
      source's "45 degrees to each other" or claim R6-C-001's
      orientation dependence. Doing that requires a numeric flux
      integral over the discretised geometry, which this function does
      not perform and does not pretend to.
    - Ignores the pitch angle's net axial current, wire cross-section,
      and all frequency-dependent effects (skin, proximity, self
      capacitance). It is a DC/low-frequency geometric estimate only.

    Units: all inductances henry, lengths metre, area square metre.
    """
    a, b = dual.a, dual.b
    len_a, len_b = a.length_m, b.length_m
    if overlap_length_m is None:
        overlap_length_m = min(len_a, len_b)
    if not math.isfinite(overlap_length_m) or overlap_length_m <= 0.0:
        raise GeometryError("overlap_length_m must be finite and positive")
    if overlap_length_m > min(len_a, len_b):
        raise GeometryError(
            f"overlap {overlap_length_m} m exceeds the shorter winding "
            f"({min(len_a, len_b)} m)")

    area_a = math.pi * a.radius_m ** 2
    area_b = math.pi * b.radius_m ** 2
    area_min = min(area_a, area_b)
    n_a, n_b = a.turns_per_m, b.turns_per_m
    sign = 1.0 if dual.co_handed else -1.0

    m = sign * MU0 * n_a * n_b * area_min * overlap_length_m
    l_a = MU0 * n_a ** 2 * area_a * len_a
    l_b = MU0 * n_b ** 2 * area_b * len_b
    k = m / math.sqrt(l_a * l_b) if l_a > 0 and l_b > 0 else 0.0

    aspect_a = len_a / a.radius_m
    aspect_b = len_b / b.radius_m
    valid = aspect_a >= 10.0 and aspect_b >= 10.0

    return {
        "mutual_inductance_h": m,
        "self_inductance_a_h": l_a,
        "self_inductance_b_h": l_b,
        "coupling_coefficient": k,
        "sign_reason": ("co-handed windings: axial fields add"
                        if dual.co_handed else
                        "counter-wound windings: axial fields oppose, "
                        "so M is negative"),
        "overlap_length_m": overlap_length_m,
        "aspect_ratio_a": aspect_a,
        "aspect_ratio_b": aspect_b,
        "valid": valid,
        "approximation": (
            "long-solenoid uniform-interior limit, mu_r = 1, coaxial, "
            "complete uniform overlap, DC"),
        "validity_range": (
            "aspect ratio (length/radius) >= 10 for both windings; "
            "non-magnetic surroundings; low frequency. Independent of "
            "the angular offset and of the crossing angle except for "
            "the handedness sign, so it cannot test any "
            "orientation-dependence claim."),
        "validity_note": (
            "aspect ratios satisfy the long-solenoid condition"
            if valid else
            f"NOT VALID: aspect ratios {aspect_a:.2f} and {aspect_b:.2f} "
            "are below 10; end effects this formula omits are large"),
        "units": {"mutual_inductance_h": "H", "self_inductance_a_h": "H",
                  "self_inductance_b_h": "H",
                  "coupling_coefficient": "1", "overlap_length_m": "m",
                  "aspect_ratio_a": "1", "aspect_ratio_b": "1"},
        "evidence_class": EVIDENCE_CLASS,
        "note": "no coil has been wound; this is a geometric estimate",
    }


__all__ = [
    "MU0",
    "HANDEDNESS",
    "EVIDENCE_CLASS",
    "GeometryError",
    "SingularEvaluationError",
    "HelixGeometry",
    "DualHelix",
    "pitch_for_crossing_angle",
    "dual_helix_at_crossing_angle",
    "biot_savart_field",
    "helix_field",
    "axial_field_analytic",
    "axial_field_finite_solenoid",
    "validate_against_solenoid",
    "common_differential_decomposition",
    "decompose_pulse_trains",
    "SOURCE_TRAIN_COPPER",
    "SOURCE_TRAIN_SILVER",
    "mutual_inductance_estimate",
]
