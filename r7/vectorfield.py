"""P06 — directional field-pair geometry, command compilation, and the
force null.

The source supplies drawings of paired 45-degree field components
mirrored about a desired axis, with the observation that the
perpendicular parts cancel and the wanted parts add. That observation
is correct. It is also completely uninformative, and saying so
precisely is the entire purpose of this module.

For unit vectors placed at +/-theta about ``d_hat``,

    v_+ + v_- = 2 cos(theta) d_hat

for **every** theta. At 45 degrees this reads sqrt(2) d_hat, which is
the source's figure. At 30 degrees it reads sqrt(3) d_hat, at 60
degrees it reads exactly d_hat, and at 90 degrees it reads zero. None
of those is more or less remarkable than any other: they are all the
same statement about adding two unit vectors, and the perpendicular
components cancel at every angle by the mirror symmetry that was
assumed when the pair was constructed. :func:`vector_sum_significance`
tabulates the general result so that 45 degrees is visibly not
special.

The second half of the module is the refusal. A commanded field
direction is a *setting*. A measured field direction is a
*measurement of a field*. Neither is a force, and no arrangement of
either becomes thrust, pinch, gravity or motion without a force or
acceleration measurement that survives controls. At the power levels
this programme could reach, every historical claim of anomalous thrust
has been accounted for by thermal convection, radiometric or
electrostatic effects, or by the suspension itself.
:func:`refuse_thrust_label` refuses the label and
:func:`force_null_design` states what would have to be built instead.

Nothing in this module is bench data. No channel has been calibrated,
no field mapped, no force measured. Every amplitude, phase error and
confound magnitude below is a catalogue-class or literature-class
estimate, labelled as such, used to size a design rather than to
report a result.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, asdict

from . import FORBIDDEN_COLLAPSES

#: Declared numerical tolerance. Every classification and every
#: "cancels exactly" claim in this module is an assertion about
#: agreement to within this figure, not about bit-identical floats.
#: It is stated once, here, so that no function can quietly choose a
#: looser one.
TOL = 1e-9

#: Rotation states of the two-channel basis (core/06). Switched and
#: stepped rotation are separate control modes, not states of this
#: basis, and are deliberately absent.
ROTATION_STATES = (
    "CIRCULAR",
    "ELLIPTICAL",
    "LINEAR",
    "DEGENERATE",
)


class VectorFieldRefused(RuntimeError):
    """Raised when a geometric result is asked to carry a physical
    label it has not earned."""


# --------------------------------------------------------------------
# Minimal vector helpers (pure stdlib, dimension-agnostic)
# --------------------------------------------------------------------

Vec = tuple[float, ...]


def _check_same_dim(a: Vec, b: Vec) -> None:
    if len(a) != len(b):
        raise ValueError(f"dimension mismatch: {len(a)} vs {len(b)}")


def add(a: Vec, b: Vec) -> Vec:
    _check_same_dim(a, b)
    return tuple(x + y for x, y in zip(a, b))


def sub(a: Vec, b: Vec) -> Vec:
    _check_same_dim(a, b)
    return tuple(x - y for x, y in zip(a, b))


def scale(a: Vec, k: float) -> Vec:
    return tuple(k * x for x in a)


def dot(a: Vec, b: Vec) -> float:
    _check_same_dim(a, b)
    return math.fsum(x * y for x, y in zip(a, b))


def norm(a: Vec) -> float:
    return math.sqrt(dot(a, a))


def unit(a: Vec, *, tol: float = TOL) -> Vec:
    n = norm(a)
    if n <= tol:
        raise ValueError("cannot normalize a vector of zero length")
    return scale(a, 1.0 / n)


def is_unit(a: Vec, *, tol: float = TOL) -> bool:
    return abs(norm(a) - 1.0) <= tol


def are_orthogonal(a: Vec, b: Vec, *, tol: float = TOL) -> bool:
    return abs(dot(a, b)) <= tol


def angle_between_deg(a: Vec, b: Vec) -> float:
    """Angle in degrees, clamped against floating-point overshoot."""
    na, nb = norm(a), norm(b)
    if na == 0.0 or nb == 0.0:
        raise ValueError("angle undefined for a zero vector")
    c = dot(a, b) / (na * nb)
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


# --------------------------------------------------------------------
# 1. The rotating basis
# --------------------------------------------------------------------

def basis_sample(Ax: float, Ay: float, phi_deg: float,
                 omega: float, t: float) -> tuple[float, float]:
    """One sample of ``u_x = Ax cos(wt)``, ``u_y = Ay cos(wt + phi)``.

    This is the two-channel drive of core/06 evaluated at a time, and
    it is a *command* waveform. Nothing here has been applied to any
    coil, and no channel has been calibrated.
    """
    wt = omega * t
    return (Ax * math.cos(wt),
            Ay * math.cos(wt + math.radians(phi_deg)))


@dataclass(frozen=True)
class RotationReport:
    """Classification of the two-channel basis, with the reason."""

    amplitude_x: float
    amplitude_y: float
    phase_deg: float
    tolerance: float
    amplitudes_matched: bool
    quadrature: bool
    state: str
    reason: str

    def as_record(self) -> dict:
        return asdict(self)


def rotation_state(Ax: float, Ay: float, phi_deg: float, *,
                   tol: float = TOL) -> RotationReport:
    """Classify the rotating basis as CIRCULAR/ELLIPTICAL/LINEAR/DEGENERATE.

    Circular rotation requires **both** matched amplitudes and
    ``phi = +/-90`` degrees (core/06). The two conditions are reported
    separately, because failing either one alone gives an ellipse and
    the failure modes look nothing like each other on a scope: an
    amplitude mismatch tilts nothing and squashes the circle onto an
    axis, while a phase error at matched amplitude squashes it onto a
    45-degree diagonal.

    Tests are exact comparisons against :data:`TOL`, which is declared
    rather than chosen per call site.

    :param phi_deg: phase of the y channel relative to x, in degrees.
        Wrapped into (-180, 180]; +90 and -90 both give circular
        motion, differing only in handedness, which this classifier
        does not distinguish.
    """
    if tol <= 0:
        raise ValueError("tolerance must be positive")

    # Wrap into (-180, 180] so that 270 and -90 classify identically.
    phi = ((phi_deg + 180.0) % 360.0) - 180.0
    rad = math.radians(phi)
    sin_phi, cos_phi = math.sin(rad), math.cos(rad)

    matched = abs(Ax - Ay) <= tol
    # Quadrature means cos(phi) == 0, i.e. phi = +/-90 exactly.
    quad = abs(cos_phi) <= tol

    if abs(Ax) <= tol and abs(Ay) <= tol:
        state = "DEGENERATE"
        reason = ("both channel amplitudes are zero within tolerance; "
                  "there is no trajectory to classify")
    elif abs(Ax) <= tol or abs(Ay) <= tol:
        state = "DEGENERATE"
        reason = ("one channel amplitude is zero within tolerance; the "
                  "trajectory collapses onto the surviving axis and "
                  "carries no rotation sense")
    elif abs(sin_phi) <= tol:
        state = "LINEAR"
        reason = (f"phase {phi:g} deg is 0 or 180 within tolerance, so "
                  f"the two channels are proportional at all times and "
                  f"the locus is a line segment")
    elif matched and quad:
        state = "CIRCULAR"
        reason = (f"amplitudes matched to within {tol:g} and phase "
                  f"{phi:g} deg is quadrature; both conditions hold")
    else:
        state = "ELLIPTICAL"
        if matched:
            reason = (f"amplitudes match but phase {phi:g} deg is not "
                      f"+/-90; quadrature fails, so the locus is an "
                      f"ellipse with axes on the diagonals")
        elif quad:
            reason = (f"phase is quadrature but amplitudes differ by "
                      f"{abs(Ax - Ay):g}; the locus is an "
                      f"axis-aligned ellipse")
        else:
            reason = ("neither matched amplitudes nor quadrature; the "
                      "locus is a general ellipse")

    assert state in ROTATION_STATES
    return RotationReport(
        amplitude_x=Ax, amplitude_y=Ay, phase_deg=phi, tolerance=tol,
        amplitudes_matched=matched, quadrature=quad, state=state,
        reason=reason)


# --------------------------------------------------------------------
# 2. The symmetric pair
# --------------------------------------------------------------------

@dataclass(frozen=True)
class SymmetricPair:
    """A mirrored pair about ``d_hat``, and what its sum actually is."""

    angle_deg: float
    d_hat: Vec
    n_hat: Vec
    v_plus: Vec
    v_minus: Vec
    sum_vector: Vec
    #: Component of the sum along the desired axis: 2 cos(theta).
    parallel_component: float
    #: Component along the perpendicular axis. Zero by construction.
    perpendicular_component: float
    perpendicular_cancels: bool
    predicted_parallel: float
    tolerance: float
    note: str

    def as_record(self) -> dict:
        d = asdict(self)
        for k in ("d_hat", "n_hat", "v_plus", "v_minus", "sum_vector"):
            d[k] = list(getattr(self, k))
        return d


def symmetric_pair(d_hat: Vec, n_hat: Vec, angle_deg: float = 45.0, *,
                   tol: float = TOL) -> SymmetricPair:
    """Build ``v_+- = cos(theta) d_hat +/- sin(theta) n_hat`` and sum them.

    The default 45 degrees reproduces the source drawing and its
    sqrt(2) result. The angle is a free parameter precisely so that a
    reader can watch the "result" move continuously with it; see
    :func:`vector_sum_significance`.

    ``d_hat`` and ``n_hat`` must be unit and mutually orthogonal, since
    the cancellation being demonstrated is a consequence of that
    assumed mirror symmetry and of nothing else.
    """
    if not is_unit(d_hat, tol=tol):
        raise ValueError("d_hat must be a unit vector")
    if not is_unit(n_hat, tol=tol):
        raise ValueError("n_hat must be a unit vector")
    if not are_orthogonal(d_hat, n_hat, tol=tol):
        raise ValueError("d_hat and n_hat must be orthogonal")

    th = math.radians(angle_deg)
    c, s = math.cos(th), math.sin(th)

    v_plus = add(scale(d_hat, c), scale(n_hat, s))
    v_minus = sub(scale(d_hat, c), scale(n_hat, s))
    total = add(v_plus, v_minus)

    par = dot(total, d_hat)
    perp = dot(total, n_hat)

    return SymmetricPair(
        angle_deg=angle_deg, d_hat=tuple(d_hat), n_hat=tuple(n_hat),
        v_plus=v_plus, v_minus=v_minus, sum_vector=total,
        parallel_component=par, perpendicular_component=perp,
        perpendicular_cancels=abs(perp) <= tol,
        predicted_parallel=2.0 * c, tolerance=tol,
        note=("the sum is 2 cos(theta) along d_hat and zero along "
              "n_hat, for every theta. The perpendicular cancellation "
              "follows from the mirror symmetry assumed when the pair "
              "was constructed, so it is a restatement of the "
              "construction rather than a property of any field."))


# --------------------------------------------------------------------
# 3. The honest framing
# --------------------------------------------------------------------

#: Angles tabulated by :func:`vector_sum_significance`. 45 degrees is
#: in the middle of the list rather than at the head of it, on purpose.
SIGNIFICANCE_ANGLES = (0.0, 15.0, 30.0, 45.0, 60.0, 75.0, 90.0)


def vector_sum_significance(angles_deg: tuple[float, ...] =
                            SIGNIFICANCE_ANGLES) -> dict:
    """Show that the 45-degree result is elementary vector addition.

    The source's figure — two 45-degree components summing to sqrt(2)
    along the bisector — is true, and is true in the same way that
    2 + 2 = 4 is true. It follows from the definition of the vectors
    that were drawn. It is not a measurement, not a property of any
    field, and not a statement about force. This function exists so
    that the claim cannot be quoted without the general result
    standing next to it.
    """
    e_x: Vec = (1.0, 0.0)
    e_y: Vec = (0.0, 1.0)
    rows = []
    for a in angles_deg:
        p = symmetric_pair(e_x, e_y, a)
        rows.append({
            "angle_deg": a,
            "parallel_component": p.parallel_component,
            "closed_form_2cos_theta": 2.0 * math.cos(math.radians(a)),
            "perpendicular_component": p.perpendicular_component,
            "perpendicular_cancels": p.perpendicular_cancels,
        })
    at45 = next(r for r in rows if r["angle_deg"] == 45.0)
    return {
        "closed_form": "v_+ + v_- = 2 cos(theta) d_hat, for all theta",
        "table": rows,
        "value_at_45_deg": at45["parallel_component"],
        "sqrt2": math.sqrt(2.0),
        "value_at_30_deg": 2.0 * math.cos(math.radians(30.0)),
        "value_at_60_deg": 2.0 * math.cos(math.radians(60.0)),
        "value_at_90_deg": 2.0 * math.cos(math.radians(90.0)),
        "is_45_degrees_special": False,
        "why_not_special": (
            "2 cos(45 deg) = sqrt(2) is one entry in a smooth family. "
            "30 degrees gives sqrt(3), which is larger; 60 degrees "
            "gives exactly 1; 90 degrees gives 0. If sqrt(2) were "
            "evidence of anything, sqrt(3) would be stronger evidence "
            "of it, which shows the quantity is carrying no evidential "
            "weight at all."),
        "what_it_is": (
            "a statement about adding two unit vectors that are "
            "mirrored about a common axis. The perpendicular parts "
            "cancel because the construction made them equal and "
            "opposite."),
        "what_it_is_not": (
            "It is not a discovery about fields: no field quantity "
            "enters the derivation. It is not a statement about force: "
            "no mass, charge, current, gradient or momentum enters "
            "either. Superposing two commanded field directions "
            "produces a third commanded field direction and nothing "
            "else."),
        "collapse_refused": FORBIDDEN_COLLAPSES["VECTOR_SUM_IS_THRUST"],
    }


# --------------------------------------------------------------------
# 4. The command compiler
# --------------------------------------------------------------------

@dataclass(frozen=True)
class VectorCommand:
    """One weighted directional command.

    ``direction`` is normalized on construction; ``weight`` may be
    negative, which is how an opposing command is expressed.
    """

    label: str
    direction: Vec
    weight: float = 1.0

    def __post_init__(self):
        object.__setattr__(self, "direction", unit(tuple(
            float(x) for x in self.direction)))
        object.__setattr__(self, "weight", float(self.weight))

    @property
    def contribution(self) -> Vec:
        return scale(self.direction, self.weight)

    def as_record(self) -> dict:
        d = asdict(self)
        d["direction"] = list(self.direction)
        d["contribution"] = list(self.contribution)
        return d


@dataclass(frozen=True)
class ChannelError:
    """Per-channel amplitude and phase error of the drive electronics.

    Catalogue-class estimates for a competently built two- or
    three-channel amplifier chain with independent output stages, NOT
    measured values: this programme owns no amplifier and has
    calibrated no channel.

    ``amplitude_fraction`` is a gain error (0.02 = 2 percent).
    ``phase_deg`` is the residual phase offset between channels after
    whatever alignment the operator performed. A phase offset scales
    the coherent, in-phase projection of a channel by ``cos(phase)``,
    which is why a small phase error costs little amplitude but a
    large one costs a great deal.
    """

    amplitude_fraction: float = 0.02
    phase_deg: float = 1.5
    source: str = ("catalogue-class estimate for a general-purpose "
                   "multi-channel drive chain; not measured")

    def channel_gain(self, index: int) -> float:
        """Deterministic per-channel gain, alternating in sign.

        Alternating signs are used rather than a random draw so that
        the compiler is reproducible without seeding anything, and so
        that the errors do not conveniently cancel. No Python ``hash``
        is involved.
        """
        sign = 1.0 if index % 2 == 0 else -1.0
        return 1.0 + sign * self.amplitude_fraction

    def channel_phase_factor(self, index: int) -> float:
        """Coherent-projection factor ``cos(phase)`` for a channel.

        Channel 0 is taken as the phase reference and is exact; every
        other channel carries the declared offset. That is the honest
        arrangement, because phase is only ever measured relative to
        something.
        """
        if index == 0:
            return 1.0
        return math.cos(math.radians(self.phase_deg))


#: The error assumed when a caller does not supply one. Declared here
#: so that "requested equals realized" can never happen by silent
#: default.
DEFAULT_CHANNEL_ERROR = ChannelError()

#: A perfect chain, provided only so tests and derivations can isolate
#: the ideal arithmetic. It does not describe any real hardware.
IDEAL_CHANNEL_ERROR = ChannelError(
    amplitude_fraction=0.0, phase_deg=0.0,
    source="idealization; no such chain exists")


@dataclass(frozen=True)
class CompiledField:
    """REQUESTED versus REALIZED, kept apart on purpose.

    The requested vector is what the command set asks for. The
    realized vector is what a drive chain with the declared per-channel
    errors would actually produce. They differ in general, and the
    module refuses to report only one of them, because reporting only
    the requested vector is how a *setting* gets mistaken for a
    *measurement*.
    """

    commands: tuple[VectorCommand, ...]
    requested: Vec
    realized: Vec
    requested_magnitude: float
    realized_magnitude: float
    magnitude_error_fraction: float
    direction_error_deg: float
    channel_error: ChannelError
    exact: bool
    note: str

    def as_record(self) -> dict:
        return {
            "commands": [c.as_record() for c in self.commands],
            "requested": list(self.requested),
            "realized": list(self.realized),
            "requested_magnitude": self.requested_magnitude,
            "realized_magnitude": self.realized_magnitude,
            "magnitude_error_fraction": self.magnitude_error_fraction,
            "direction_error_deg": self.direction_error_deg,
            "channel_error": asdict(self.channel_error),
            "exact": self.exact,
            "note": self.note,
        }


def requested_sum(commands: tuple[VectorCommand, ...] | list) -> Vec:
    """``sum_i w_i v_i`` — the ideal superposition, with no errors."""
    cmds = tuple(commands)
    if not cmds:
        raise ValueError("no commands supplied")
    dim = len(cmds[0].direction)
    total = tuple(0.0 for _ in range(dim))
    for c in cmds:
        if len(c.direction) != dim:
            raise ValueError(
                "all commands must have the same dimension")
        total = add(total, c.contribution)
    return total


def compile_commands(commands: tuple[VectorCommand, ...] | list, *,
                     channel_error: ChannelError = DEFAULT_CHANNEL_ERROR,
                     tol: float = TOL) -> CompiledField:
    """Compile a command set into a realized field direction.

    The realized vector applies, per spatial channel, the declared gain
    error and the coherent-projection loss from the declared phase
    error. Both are catalogue-class estimates for the electronics, not
    measurements of any apparatus.

    The direction error is reported in degrees and is the number that
    matters: an amplitude error is usually calibrated out, while a
    residual inter-channel phase error steers the realized vector away
    from the requested one and is much harder to remove.
    """
    req = requested_sum(commands)
    realized = tuple(
        v * channel_error.channel_gain(i)
        * channel_error.channel_phase_factor(i)
        for i, v in enumerate(req))

    rq_mag, rz_mag = norm(req), norm(realized)
    if rq_mag <= tol:
        # A null command set: direction is undefined, and saying so is
        # more useful than reporting an angle between noise vectors.
        mag_err = 0.0 if rz_mag <= tol else math.inf
        dir_err = 0.0
        note = ("the requested vector is null within tolerance, so no "
                "direction is defined; see stationary_state")
    else:
        mag_err = (rz_mag - rq_mag) / rq_mag
        dir_err = (angle_between_deg(req, realized)
                   if rz_mag > tol else 180.0)
        note = ("realized differs from requested by construction: a "
                "declared per-channel gain and phase error is applied. "
                "This is a model of a drive chain, not a reading from "
                "one.")

    # Exactness is judged componentwise, NOT from the reported angle.
    # ``angle_between_deg`` goes through acos, which loses roughly half
    # the available precision near zero angle: two genuinely identical
    # vectors come back about 1e-6 degrees apart, which is a thousand
    # times the declared tolerance. Reporting that angle is fine;
    # deciding equality with it is not.
    same = all(abs(a - b) <= tol * max(1.0, abs(b))
               for a, b in zip(realized, req))
    if same:
        dir_err = 0.0
        if rq_mag > tol:
            note = ("realized equals requested only because an "
                    "idealized error-free chain was supplied. No such "
                    "chain exists; this is an arithmetic check, not a "
                    "description of hardware.")
    exact = same
    return CompiledField(
        commands=tuple(commands), requested=req, realized=realized,
        requested_magnitude=rq_mag, realized_magnitude=rz_mag,
        magnitude_error_fraction=mag_err, direction_error_deg=dir_err,
        channel_error=channel_error, exact=exact, note=note)


# --------------------------------------------------------------------
# 5. The stationary state
# --------------------------------------------------------------------

@dataclass(frozen=True)
class StationaryReport:
    residual: Vec
    residual_norm: float
    largest_contribution_norm: float
    relative_residual: float
    tolerance: float
    balanced: bool
    note: str

    def as_record(self) -> dict:
        d = asdict(self)
        d["residual"] = list(self.residual)
        return d


def stationary_state(commands: tuple[VectorCommand, ...] | list, *,
                     tol: float = TOL) -> StationaryReport:
    """Test the balanced condition ``sum_i w_i v_i == 0`` (core/06).

    Balance is judged on the residual *relative* to the largest single
    contribution, because an absolute threshold would call any set of
    very small commands balanced. A stationary state means the
    commands cancel, and it means nothing more than that: a stationary
    command set applied to a real apparatus still deposits power,
    still warms the mount, and still radiates.
    """
    cmds = tuple(commands)
    res = requested_sum(cmds)
    rn = norm(res)
    largest = max(norm(c.contribution) for c in cmds)
    # Divide by the largest contribution whenever there is one. Using
    # the tolerance as the guard here would be a bug: it would declare
    # any set of very small commands balanced regardless of whether
    # they cancel, which is the exact failure this relative test exists
    # to avoid. Only an all-zero command set is trivially balanced.
    rel = rn / largest if largest > 0.0 else 0.0
    balanced = rel <= tol
    return StationaryReport(
        residual=res, residual_norm=rn,
        largest_contribution_norm=largest, relative_residual=rel,
        tolerance=tol, balanced=balanced,
        note=("balanced commands sum to zero; the apparatus is not "
              "thereby inert, since a null vector sum says nothing "
              "about deposited power, heating or emission"
              if balanced else
              "commands do not cancel; a net commanded direction "
              "remains"))


# --------------------------------------------------------------------
# 6. The refusal
# --------------------------------------------------------------------

#: Ordinary effects that produce a real, measurable force on a small
#: object in a laboratory, each of which must be excluded before any
#: residual could be called anomalous. Magnitudes are literature-class
#: order-of-magnitude figures for a gram-scale object under a watt-scale
#: drive in air; they are not measurements.
THRUST_CONFOUNDS = {
    "SHAM_DRIVE": {
        "control": "identical power dissipated into a dummy load with "
                   "no field geometry, same duty cycle, same cabling",
        "why": "separates 'a powered thing is present' from 'this "
               "geometry is present'; if the sham reproduces the "
               "signal, the geometry is irrelevant",
        "expected_magnitude_n": None,
        "note": "a control, not a confound magnitude",
    },
    "REVERSED_GEOMETRY": {
        "control": "reverse the field geometry and require the sign of "
                   "the effect to flip",
        "why": "thermal, convective and buoyancy artifacts are tied to "
               "where the heat is, not to the field direction, so they "
               "usually fail to reverse; a genuine directional effect "
               "must",
        "expected_magnitude_n": None,
        "note": "a control, not a confound magnitude",
    },
    "THERMAL_CONVECTION": {
        "control": "vacuum operation below about 1e-3 Pa, or matched "
                   "thermal load with no geometry, plus thermal "
                   "imaging of the apparatus and mount",
        "why": "a warm object in air drives a convective plume and "
               "recoils; this is a real force and it is large",
        "expected_magnitude_n": 1e-6,
        "note": "order 1 uN per watt dissipated in air is a routine "
                "figure for gram-scale objects; this alone exceeds "
                "most claimed anomalous effects",
    },
    "RADIOMETRIC": {
        "control": "operate either at atmospheric pressure or below "
                   "1e-3 Pa, never in the intermediate regime where "
                   "the radiometric force peaks",
        "why": "a temperature gradient across a surface in a rarefied "
               "gas produces a force that peaks at intermediate "
               "pressure and is easily mistaken for a field effect",
        "expected_magnitude_n": 1e-7,
        "note": "peaks near the mean-free-path-matched pressure",
    },
    "ELECTROSTATIC_ATTRACTION": {
        "control": "grounded conductive shield around the apparatus, "
                   "surface-potential survey, humidity control, and a "
                   "charged-but-unpowered null",
        "why": "any charged or polarized object attracts a nearby "
               "surface; kilovolt drives on a bench guarantee stray "
               "charge",
        "expected_magnitude_n": 1e-6,
        "note": "a kilovolt across a centimetre gap on square "
                "centimetre areas gives microNewton-scale attraction; "
                "historically the single most common false positive",
    },
    "MAGNETIC_MOUNT_INTERACTION": {
        "control": "non-magnetic mount and fasteners, magnetic survey "
                   "of the fixture, and a swapped-mount repeat",
        "why": "steel fasteners and stage components attract any coil "
               "carrying current",
        "expected_magnitude_n": 1e-5,
        "note": "can dominate everything else if a single steel screw "
                "is present",
    },
    "EARTH_FIELD_TORQUE": {
        "control": "three-axis magnetometer log, mu-metal shield or "
                   "Helmholtz compensation, and repeats at rotated "
                   "azimuths",
        "why": "a current loop has a magnetic moment and Earth's field "
               "exerts a torque on it that rotates with the apparatus",
        "expected_magnitude_n": 1e-7,
        "note": "about 50 uT acting on a small loop moment; shows up "
                "as a torque, which a torsion balance measures "
                "directly",
    },
    "TETHER_STIFFNESS": {
        "control": "the lightest practical leads routed along the "
                   "suspension axis, a dummy-lead repeat, and a "
                   "power-off mechanical disturbance test",
        "why": "cables stiffen, creep and pull thermally as they warm; "
               "the suspension then moves for reasons that have "
               "nothing to do with the apparatus",
        "expected_magnitude_n": 1e-6,
        "note": "creep is slow and drifts in the same direction as a "
                "hoped-for signal, which is what makes it dangerous",
    },
    "BUOYANCY_FROM_HEATING": {
        "control": "sealed enclosure, ambient logging, and a matched "
                   "thermal null",
        "why": "warming the air inside or around the apparatus changes "
               "its density and therefore the buoyant force",
        "expected_magnitude_n": 1e-7,
        "note": "small but systematic and correlated with drive power",
    },
    "VIBRATION_AND_ACOUSTIC": {
        "control": "isolation table, acoustic enclosure, accelerometer "
                   "log, and a speaker-driven injection test",
        "why": "a driven apparatus radiates sound and vibration that "
               "couples into the suspension",
        "expected_magnitude_n": 1e-7,
        "note": "usually oscillatory but rectifies into a DC offset at "
                "a nonlinear suspension",
    },
}


def refuse_thrust_label(*args, **kwargs):
    """Always refuses. A field vector sum is not a force.

    This refusal applies to a *commanded* vector sum and equally to a
    *measured* one. Mapping a real field with a real magnetometer and
    finding the direction the geometry predicted would confirm that
    the coils are wired as drawn. It would not produce a newton.
    """
    controls = ", ".join(sorted(THRUST_CONFOUNDS))
    raise VectorFieldRefused(
        "a field vector sum may not be labelled thrust, pinch, "
        "gravity or motion. "
        f"r7 FORBIDDEN_COLLAPSES[VECTOR_SUM_IS_THRUST]: "
        f"{FORBIDDEN_COLLAPSES['VECTOR_SUM_IS_THRUST']}. "
        "The label requires a force or acceleration measurement that "
        "survives controls, not a geometric superposition. Required "
        f"controls: {controls}. In plain terms: a sham drive at the "
        "same power with no field geometry; a reversed geometry whose "
        "sign must flip; a thermal and convection null, because a warm "
        "object in air produces a measurable force; exclusion of "
        "electrostatic attraction to nearby surfaces; exclusion of "
        "magnetic interaction with the mount and with Earth's field; "
        "exclusion of tether and cable stiffness; and exclusion of "
        "buoyancy from heating. Until all of those are closed, the "
        "honest description is 'a commanded field direction' "
        "(core/06).")


def force_null_design() -> dict:
    """The experiment that would be required to earn the force label.

    This is a design, not a result. No balance has been built, no
    fibre hung, no reading taken. Costs and instrument specifications
    appear in :mod:`r7.benchr7` and are catalogue-class estimates.
    """
    total_floor = math.sqrt(math.fsum(
        (v["expected_magnitude_n"] or 0.0) ** 2
        for v in THRUST_CONFOUNDS.values()))
    return {
        "apparatus": (
            "a torsion balance: the apparatus on one arm, a mass-and-"
            "area-matched dummy on the other, hung on a fine fibre "
            "inside an evacuated, grounded, thermally lagged chamber, "
            "read out optically through a window with no mechanical "
            "contact. A simple pendulum is the cheaper fallback and is "
            "far more susceptible to tilt and to air currents."),
        "why_torsion": (
            "a torsion fibre is soft in the one coordinate being "
            "measured and stiff in the five that are not, so it "
            "rejects tilt, vertical drift and buoyancy far better "
            "than a pendulum does. It also measures torque directly, "
            "which is what an Earth-field interaction produces."),
        "readout": (
            "optical lever or interferometric angle readout, "
            "calibrated in situ against a known electrostatic torque "
            "so the scale factor is traceable rather than assumed"),
        "environment": (
            "vacuum below 1e-3 Pa to remove convection and to stay off "
            "the radiometric peak; grounded conductive shield; "
            "temperature logged at the arm, the mount and the chamber "
            "wall; three-axis magnetometer log; accelerometer log"),
        "blinding": (
            "drive sequence randomized and applied by a controller "
            "that does not report which condition is live until "
            "analysis is frozen; sham and reversed conditions "
            "interleaved rather than blocked, so drift cannot "
            "masquerade as an effect"),
        "confounds": THRUST_CONFOUNDS,
        "quadrature_confound_floor_n": total_floor,
        "confound_floor_note": (
            f"adding the tabulated confound magnitudes in quadrature "
            f"gives roughly {total_floor:.1e} N of systematic budget "
            f"before any signal is discussed. A claimed effect must "
            f"be resolved against that, not against the fibre's "
            f"thermal noise. These are order-of-magnitude "
            f"literature-class figures for a gram-scale object at "
            f"watt-scale drive, not measurements."),
        "acceptance": (
            "a residual that (a) exceeds the quadrature confound "
            "budget with a preregistered statistical threshold, "
            "(b) changes sign under reversed geometry, (c) is absent "
            "in the sham drive at identical power, and (d) is "
            "reproduced after the apparatus is dismounted and "
            "rebuilt. Failing any one of the four means no label."),
        "historical_note": (
            "Thermal and convective artifacts and electrostatic "
            "attraction to nearby surfaces have accounted for every "
            "claimed anomalous-thrust result at these power levels "
            "that has been examined carefully. That is the prior this "
            "design must beat: the first hypothesis for any observed "
            "deflection is that the apparatus is warm, charged, or "
            "attached to something."),
        "status_if_built": (
            "the best available outcome is a bounded null: 'no force "
            "above X newtons under these conditions'. A bounded null "
            "is a publishable result and is the outcome this "
            "programme expects."),
        "built": False,
        "measurements_taken": 0,
    }


__all__ = [
    "TOL",
    "ROTATION_STATES",
    "VectorFieldRefused",
    "add", "sub", "scale", "dot", "norm", "unit", "is_unit",
    "are_orthogonal", "angle_between_deg",
    "basis_sample", "RotationReport", "rotation_state",
    "SymmetricPair", "symmetric_pair",
    "SIGNIFICANCE_ANGLES", "vector_sum_significance",
    "VectorCommand", "ChannelError", "DEFAULT_CHANNEL_ERROR",
    "IDEAL_CHANNEL_ERROR", "CompiledField", "requested_sum",
    "compile_commands",
    "StationaryReport", "stationary_state",
    "THRUST_CONFOUNDS", "refuse_thrust_label", "force_null_design",
]
