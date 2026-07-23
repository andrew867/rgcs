"""P10 — a hybrid toothed rotor, as a parametric MODEL and nothing else.

The lore keeps describing a spinning toothed wheel as if describing it
were the same as having one. It is not. This module writes down what
such a rotor *would* be specified by -- a tooth count, a shaft speed, a
diameter, conductive tabs, ferromagnetic inserts, signed pickup
channels, a balance grade and a containment class -- and works the
arithmetic that follows from those numbers. **A parametric rotor model
is not a built rotor.** Nothing here is machined, printed, deburred,
pressed, wired, balanced, mounted, guarded or spun. No apparatus exists,
no shaft turns, and no number below was obtained by observing anything.

**The exact tooth-rate arithmetic.** A toothed carrier passing a fixed
pickup generates one signal event per tooth, so the passage rate is
``teeth * rpm / 60`` -- a rational identity, kept exact with
``fractions.Fraction`` so nothing rounds at a claim boundary. The
reference case is exact and reproduces::

    192 * 1280 / 60 = 245760 / 60 = 4096     (exactly 4096 Hz)

and it inverts exactly: 4096 tooth passages per second on a 192-tooth
carrier is 1280 rpm, with no residue. Because it is exact, a *rounded*
or floating restatement of it is a different claim, and
:func:`refuse_approximate_rate` refuses to let an approximation stand in
for the exact design rate.

**Two signed channels, or no direction.** This is the R11 lesson
restated in mechanics. A single pickup channel produces the same signal
whichever way the rotor turns: the tooth passes, the channel pulses, and
the pulse carries no sign. Direction lives in the *relative phase* of
two channels, which is why the second pickup is placed a quarter tooth
pitch away -- ``360/(4*teeth)`` mechanical degrees, which maps to
exactly 90 electrical degrees because one tooth pitch is one full
electrical cycle. :func:`direction_from_quadrature` reads the sign off
the two signed channels, and it reverses when the channels are swapped;
:func:`refuse_direction_from_single_channel` refuses the one-channel
version outright.

**Conductive tabs and ferromagnetic inserts are different things.**
A conductive tab is sensed by eddy-current or capacitive coupling: it
loads a driven field because it *conducts*. A ferromagnetic insert is
sensed by variable reluctance: it changes a magnetic circuit because it
is *permeable*. Different physics, different excitation, different
front-end electronics. They are typed separately here and
:func:`refuse_transduction_equivalence` refuses the claim that fitting
one gives you the other.

**Balance and containment are safety arithmetic, not permission.**
Residual unbalance force is ``m * e * omega^2``, so it grows with the
*square* of shaft speed: doubling the rpm quadruples the force at the
bearings. An unreinforced printed-polymer rotor has a low safe rim
speed, and :func:`refuse_uncontained_operation` raises
:class:`SafetyViolation` when no containment class is declared or the
rim speed exceeds the declared limit. Above all,
:func:`refuse_spin_authorization` **always** raises: no apparatus exists
here, no one is authorised to spin anything from this module, and no
part of it may be read as clearance to do so.

Everything below is an ``ANALYTIC_MODEL``. The exact quantities are
rational arithmetic; the mechanical quantities (rim speed, unbalance
force) are floating-point estimates from declared formulae. Nothing is
measured. The verdict is ``HYBRID_ROTOR_MODEL_IMPLEMENTED``, and
"implemented" means the model is implemented -- not the rotor.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from fractions import Fraction

# --- standing labels ----------------------------------------------------

DEFAULT_VERDICT = "HYBRID_ROTOR_MODEL_IMPLEMENTED"
EVIDENCE_CLASS = "ANALYTIC_MODEL"
MEASURED_HERE = "nothing"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"
MODEL_ONLY = "MODEL_ONLY"

#: One full turn, in degrees. Exact.
DEGREES_PER_TURN = 360
#: Seconds per minute. Exact, and the only reason rpm needs converting.
SECONDS_PER_MINUTE = 60

#: The verified reference case. A 192-tooth printed carrier at 1280 rpm
#: gives exactly 4096 tooth passages per second: 192*1280 = 245760, and
#: 245760/60 = 4096 with no remainder.
REFERENCE_TEETH = 192
REFERENCE_RPM = Fraction(1280)
REFERENCE_RATE_HZ = Fraction(4096)

#: A representative carrier diameter for the reference spec, in
#: millimetres. A design target, not a measured part.
REFERENCE_DIAMETER_MM = 120.0

#: Conservative safe rim speeds, in m/s, for the rotor materials this
#: model knows about. These are declared design limits carried as model
#: parameters, not measured burst speeds of any part.
MATERIAL_RIM_SPEED_LIMIT_M_PER_S: dict[str, float] = {
    "printed polymer": 20.0,
    "machined polymer": 30.0,
    "aluminium": 100.0,
}

#: The default material. An unreinforced printed polymer rotor is the
#: weakest case here, and it is the default on purpose.
DEFAULT_MATERIAL = "printed polymer"


class RotorError(ValueError):
    """Raised when a rotor claim exceeds what the model supports:
    an approximate rate passed off as the exact design rate, direction
    read from a single unsigned channel, or one transduction path
    claimed to imply the other."""


class SafetyViolation(RuntimeError):
    """Raised for a containment or balance breach, and for any attempt to
    obtain spin authorisation from this module. Deliberately NOT a
    subclass of :class:`RotorError`: an arithmetic refusal and a safety
    refusal are different categories and must not be caught together."""


# --- exactness discipline -----------------------------------------------

def _exact(value: int | Fraction | str, what: str) -> Fraction:
    """Coerce to an exact Fraction, refusing floats.

    Floats are fine for mechanical estimates (rim speed, unbalance
    force) and are used there. They are not fine for the tooth-rate
    identity, which is exact rational arithmetic and stays exact.
    """
    if isinstance(value, float):
        raise RotorError(
            f"{what} was given as the float {value!r}. The tooth-rate "
            f"arithmetic is exact rational arithmetic; a float has already "
            f"rounded and cannot be un-rounded. Pass an int, a Fraction, or "
            f"a decimal string.")
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, str):
        try:
            return Fraction(value)
        except (ValueError, ZeroDivisionError) as exc:
            raise RotorError(f"{what}: {value!r} is not an exact "
                             f"rational") from exc
    raise RotorError(
        f"{what} must be an int, a Fraction or a decimal string; got "
        f"{type(value).__name__}")


# --- the exact tooth-rate identity --------------------------------------

def tooth_passage_rate_hz(teeth: int, rpm: int | Fraction | str) -> Fraction:
    """Tooth passages per second: ``teeth * rpm / 60``, exactly.

    One tooth passing one fixed pickup is one signal event, so the rate
    is the tooth count times the revolution rate. The reference case is
    exact::

        192 * 1280 / 60 = 245760 / 60 = 4096

    The return type is :class:`~fractions.Fraction` and stays exact for
    every input, whether or not the division happens to close.
    """
    if not isinstance(teeth, int) or isinstance(teeth, bool):
        raise RotorError("teeth must be an integer count")
    if teeth < 1:
        raise RotorError(
            "teeth must be at least 1; a carrier with no teeth passes "
            "nothing and has no passage rate")
    r = _exact(rpm, "rpm")
    if r < 0:
        raise RotorError("rpm must be non-negative; direction is carried by "
                         "the quadrature channels, not by a negative speed")
    return Fraction(teeth) * r / SECONDS_PER_MINUTE


def rpm_for_rate(teeth: int, rate_hz: int | Fraction | str) -> Fraction:
    """Invert the identity: ``rpm = rate * 60 / teeth``, exactly.

    For (192, 4096) this returns exactly ``Fraction(1280)`` -- the
    inversion closes with no residue, which is the whole point of doing
    it in rationals.
    """
    if not isinstance(teeth, int) or isinstance(teeth, bool):
        raise RotorError("teeth must be an integer count")
    if teeth < 1:
        raise RotorError("teeth must be at least 1")
    r = _exact(rate_hz, "rate_hz")
    if r < 0:
        raise RotorError("a passage rate must be non-negative")
    return r * SECONDS_PER_MINUTE / Fraction(teeth)


def refuse_approximate_rate(rate_hz,
                            teeth: int = REFERENCE_TEETH,
                            rpm: int | Fraction | str = REFERENCE_RPM
                            ) -> Fraction:
    """Refuse an approximate rate presented as the exact design rate.

    The design rate is a rational identity. A float restatement of it
    (``4096.0``) has already passed through binary rounding, and a
    rounded restatement (``4096.1``, ``4100``) is simply a different
    number. Either way it is not the exact design rate and must not be
    reported as one. Returns the exact rate when -- and only when -- the
    presented value is exact and equal.
    """
    exact = tooth_passage_rate_hz(teeth, rpm)
    if isinstance(rate_hz, float):
        raise RotorError(
            f"{rate_hz!r} is a float presented as the exact design rate. "
            f"{teeth} teeth at {rpm} rpm is exactly {exact} Hz by rational "
            f"arithmetic; a float carries binary rounding and cannot state "
            f"an exact design rate. Pass Fraction({exact}).")
    presented = _exact(rate_hz, "rate_hz")
    if presented != exact:
        raise RotorError(
            f"{presented} Hz is not the exact design rate for {teeth} teeth "
            f"at {rpm} rpm, which is exactly {exact} Hz. A rounded or "
            f"nearby value is a different claim and may not be reported as "
            f"the design rate.")
    return exact


# --- quadrature: geometry, electrical angle, and the sign rule ----------

def tooth_pitch_deg(teeth: int) -> Fraction:
    """One tooth pitch in mechanical degrees: ``360/teeth``, exactly."""
    if not isinstance(teeth, int) or isinstance(teeth, bool) or teeth < 1:
        raise RotorError("teeth must be an integer count of at least 1")
    return Fraction(DEGREES_PER_TURN, teeth)


def quadrature_offset_deg(teeth: int) -> Fraction:
    """Pickup separation for quadrature: ``360/(4*teeth)`` mechanical deg.

    Two pickups a quarter tooth pitch apart see the same tooth train a
    quarter cycle apart. For 192 teeth this is ``360/768 = 15/32``
    mechanical degrees -- a small mechanical angle that is nonetheless a
    full quarter of an electrical cycle.
    """
    if not isinstance(teeth, int) or isinstance(teeth, bool) or teeth < 1:
        raise RotorError("teeth must be an integer count of at least 1")
    return Fraction(DEGREES_PER_TURN, 4 * teeth)


def electrical_deg(mechanical_deg: int | Fraction | str,
                   teeth: int) -> Fraction:
    """Mechanical angle to electrical angle: ``mech * teeth``, exactly.

    One tooth pitch is one full electrical cycle, so ``360/teeth``
    mechanical degrees is 360 electrical degrees and the conversion is
    multiplication by the tooth count.
    """
    if not isinstance(teeth, int) or isinstance(teeth, bool) or teeth < 1:
        raise RotorError("teeth must be an integer count of at least 1")
    return _exact(mechanical_deg, "mechanical_deg") * teeth


def quadrature_offset_electrical_deg(teeth: int) -> Fraction:
    """The quadrature offset in electrical degrees: exactly 90, always.

    ``(360/(4*teeth)) * teeth == 90`` for every tooth count, which is why
    "a quarter tooth pitch" and "90 degrees electrical" are the same
    instruction.
    """
    return electrical_deg(quadrature_offset_deg(teeth), teeth)


class Direction(Enum):
    """The sign of rotation, as read from two signed channels."""

    FORWARD = "forward"
    REVERSE = "reverse"
    INDETERMINATE = "indeterminate"

    @property
    def sign(self) -> int:
        return {"forward": 1, "reverse": -1, "indeterminate": 0}[self.value]


def _as_signed_samples(channel, name: str) -> list[float]:
    """Coerce a channel to at least two consecutive signed samples."""
    if isinstance(channel, (int, float, Fraction)):
        raise RotorError(
            f"{name} is a single scalar sample. Direction is a property of "
            f"how the two channels ADVANCE, so each channel needs at least "
            f"two consecutive signed samples (previous, current).")
    try:
        samples = [float(x) for x in channel]
    except TypeError as exc:
        raise RotorError(
            f"{name} must be a sequence of signed samples") from exc
    if len(samples) < 2:
        raise RotorError(
            f"{name} has {len(samples)} sample(s); at least two consecutive "
            f"samples are needed to see the phase advance")
    return samples


def direction_from_quadrature(a, b) -> Direction:
    """Read rotation direction from two SIGNED quadrature channels.

    ``a`` and ``b`` are the two pickup channels, each a sequence of at
    least two consecutive signed samples. The rule is the signed area
    swept by the quadrature pair::

        cross = sum_i ( a[i]*b[i+1] - a[i+1]*b[i] )

    For an ideal pair ``a = cos(phi)``, ``b = sin(phi)`` this evaluates
    to ``sin(delta_phi)``, so its sign is the sign of the phase advance:
    positive is :attr:`Direction.FORWARD`, negative is
    :attr:`Direction.REVERSE`, and zero is
    :attr:`Direction.INDETERMINATE` (no advance, or a degenerate pair
    that is not actually in quadrature). The rule is antisymmetric, so
    swapping the two channels reverses the reported direction -- which is
    exactly the physical statement that "which channel leads" *is* the
    direction.
    """
    sa = _as_signed_samples(a, "channel a")
    sb = _as_signed_samples(b, "channel b")
    if len(sa) != len(sb):
        raise RotorError(
            "the two channels must be sampled together: got "
            f"{len(sa)} and {len(sb)} samples")
    cross = sum(sa[i] * sb[i + 1] - sa[i + 1] * sb[i]
                for i in range(len(sa) - 1))
    if cross > 0:
        return Direction.FORWARD
    if cross < 0:
        return Direction.REVERSE
    return Direction.INDETERMINATE


def refuse_direction_from_single_channel(
        channel_id: str = "A",
        samples: int | None = None) -> None:
    """A single channel cannot give direction. This always raises.

    The R11 lesson, restated in mechanics: one channel produces the same
    pulse train whichever way the rotor turns. No amount of sampling,
    filtering, thresholding or edge-counting on that one channel recovers
    the sign, because the sign was never encoded in it. Direction lives
    in the *relative phase* of two signed channels, and a second channel
    derived from the first (its inverse, its envelope, its square) is the
    same channel written differently, not an independent one.
    """
    raise RotorError(
        f"direction cannot be read from the single channel {channel_id!r}"
        + (f" ({samples} samples)" if samples is not None else "")
        + ". A lone pickup pulses once per tooth in both directions, so the "
        "pulse train is identical forwards and backwards and carries no "
        "sign. TWO SIGNED CHANNELS ARE REQUIRED, separated by a quarter "
        "tooth pitch (90 electrical degrees); direction is the sign of "
        "their relative phase. An inverted, squared or rectified copy of "
        "the same channel is not a second channel.")


# --- transduction paths: typed apart, and kept apart --------------------

class Transduction(Enum):
    """How a rotor feature is sensed. These are different physics.

    ``EDDY_CURRENT_CAPACITIVE`` needs an electrically CONDUCTIVE feature
    and a driven field it can load. ``VARIABLE_RELUCTANCE`` needs a
    magnetically PERMEABLE feature and a magnetic circuit it can alter.
    A conductive tab that is not ferromagnetic is invisible to a
    reluctance pickup; a ferrite insert that is not conductive is
    invisible to an eddy-current pickup.
    """

    EDDY_CURRENT_CAPACITIVE = "eddy_current_capacitive"
    VARIABLE_RELUCTANCE = "variable_reluctance"


@dataclass(frozen=True)
class ConductiveTab:
    """A conductive tab on the rotor. Sensed by eddy current / capacitance.

    Placement is an exact mechanical angle in degrees. The transduction
    path is fixed at construction and cannot be reassigned to the
    reluctance path.
    """

    index: int
    angle_deg: Fraction
    material: str = "conductive tab (non-ferromagnetic)"
    transduction: Transduction = Transduction.EDDY_CURRENT_CAPACITIVE
    status: str = MODEL_ONLY

    def __post_init__(self) -> None:
        if self.transduction is not Transduction.EDDY_CURRENT_CAPACITIVE:
            raise RotorError(
                "a conductive tab is sensed by eddy-current or capacitive "
                "coupling; it does not become a reluctance feature by being "
                "labelled one")
        object.__setattr__(self, "angle_deg",
                           _exact(self.angle_deg, "angle_deg"))


@dataclass(frozen=True)
class FerromagneticInsert:
    """A ferromagnetic insert. Sensed by variable reluctance.

    A separate type from :class:`ConductiveTab` on purpose: the two are
    not interchangeable and fitting one says nothing about the other.
    """

    index: int
    angle_deg: Fraction
    material: str = "ferromagnetic insert (permeable)"
    transduction: Transduction = Transduction.VARIABLE_RELUCTANCE
    status: str = MODEL_ONLY

    def __post_init__(self) -> None:
        if self.transduction is not Transduction.VARIABLE_RELUCTANCE:
            raise RotorError(
                "a ferromagnetic insert is sensed by variable reluctance; it "
                "does not become an eddy-current feature by being labelled "
                "one")
        object.__setattr__(self, "angle_deg",
                           _exact(self.angle_deg, "angle_deg"))


def place_conductive_tabs(count: int) -> tuple[ConductiveTab, ...]:
    """``count`` conductive tabs, evenly spaced, at exact angles."""
    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
        raise RotorError("tab count must be a non-negative integer")
    step = Fraction(DEGREES_PER_TURN, count) if count else Fraction(0)
    return tuple(ConductiveTab(i, step * i) for i in range(count))


def place_ferromagnetic_inserts(count: int) -> tuple[FerromagneticInsert, ...]:
    """``count`` ferromagnetic inserts, evenly spaced, at exact angles."""
    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
        raise RotorError("insert count must be a non-negative integer")
    step = Fraction(DEGREES_PER_TURN, count) if count else Fraction(0)
    return tuple(FerromagneticInsert(i, step * i) for i in range(count))


def refuse_transduction_equivalence(
        have: Transduction = Transduction.EDDY_CURRENT_CAPACITIVE,
        claimed: Transduction = Transduction.VARIABLE_RELUCTANCE) -> None:
    """Refuse the claim that one transduction path implies the other."""
    raise RotorError(
        f"fitting {have.value!r} features does not deliver {claimed.value!r} "
        f"sensing. Eddy-current/capacitive sensing needs an electrically "
        f"CONDUCTIVE feature loading a driven field; variable-reluctance "
        f"sensing needs a magnetically PERMEABLE feature altering a magnetic "
        f"circuit. Different material property, different excitation, "
        f"different front end. Neither path substitutes for the other, and "
        f"a rotor carrying both carries two independent sensing systems, "
        f"not one system described twice.")


# --- pickup channels ----------------------------------------------------

@dataclass(frozen=True)
class PickupChannel:
    """One pickup channel: where it sits, how it senses, and whether it
    is signed. An unsigned channel cannot contribute to direction."""

    channel_id: str
    transduction: Transduction
    offset_deg: Fraction = Fraction(0)
    signed: bool = True
    status: str = MODEL_ONLY

    def __post_init__(self) -> None:
        if not self.channel_id:
            raise RotorError("a pickup channel needs an identifier")
        if not isinstance(self.transduction, Transduction):
            raise RotorError(
                "a pickup channel must declare a typed Transduction path")
        object.__setattr__(self, "offset_deg",
                           _exact(self.offset_deg, "offset_deg"))


def quadrature_channel_pair(
        teeth: int = REFERENCE_TEETH,
        transduction: Transduction = Transduction.VARIABLE_RELUCTANCE
        ) -> tuple[PickupChannel, PickupChannel]:
    """Two signed channels, a quarter tooth pitch apart. The minimum."""
    off = quadrature_offset_deg(teeth)
    return (PickupChannel("A", transduction, Fraction(0), True),
            PickupChannel("B", transduction, off, True))


def refuse_unsigned_direction_pair(
        channels: tuple[PickupChannel, ...]) -> None:
    """Refuse a channel set that cannot carry direction.

    Fewer than two channels, or any unsigned channel in the pair, and the
    sign of the relative phase is unavailable.
    """
    if len(channels) < 2:
        raise RotorError(
            f"{len(channels)} pickup channel(s) declared; TWO SIGNED "
            f"CHANNELS ARE REQUIRED for direction")
    unsigned = [c.channel_id for c in channels[:2] if not c.signed]
    if unsigned:
        raise RotorError(
            f"pickup channel(s) {unsigned} are unsigned. An unsigned "
            f"(rectified, intensity-only) channel has already discarded the "
            f"sign that direction is encoded in; two of them are still no "
            f"direction.")


# --- balance: forces that grow as rpm squared ---------------------------

def angular_velocity_rad_per_s(rpm: float | int | Fraction) -> float:
    """``omega = 2*pi*rpm/60``. A mechanical estimate, so float."""
    r = float(rpm)
    if r < 0:
        raise RotorError("rpm must be non-negative")
    return 2.0 * math.pi * r / SECONDS_PER_MINUTE


def residual_unbalance_force_N(mass_kg: float, eccentricity_m: float,
                               rpm: float | int | Fraction) -> float:
    """Rotating unbalance force ``F = m * e * omega^2``, in newtons.

    The load-bearing property is the exponent: the force scales as the
    SQUARE of shaft speed, so doubling the rpm quadruples the force the
    bearings and the rotor rim have to carry. A balance that is adequate
    at one speed is not thereby adequate at twice that speed.
    """
    if mass_kg < 0:
        raise RotorError("mass must be non-negative")
    if eccentricity_m < 0:
        raise RotorError(
            "eccentricity must be non-negative; it is a distance")
    omega = angular_velocity_rad_per_s(rpm)
    return float(mass_kg) * float(eccentricity_m) * omega * omega


def permissible_eccentricity_m(grade_mm_per_s: float,
                               rpm: float | int | Fraction) -> float:
    """ISO-style permissible eccentricity for a balance grade G.

    The grade is defined as ``G = e_per * omega`` with ``e_per`` in
    millimetres, so ``e_per[m] = (G/1000) / omega``. The permissible
    eccentricity falls as speed rises: the same grade is a tighter
    tolerance at higher rpm.
    """
    if grade_mm_per_s <= 0:
        raise RotorError("a balance grade must be positive")
    omega = angular_velocity_rad_per_s(rpm)
    if omega <= 0:
        raise RotorError(
            "a balance grade has no meaning at zero speed; G = e*omega")
    return (float(grade_mm_per_s) / 1000.0) / omega


def balance_ok(grade_mm_per_s: float, rpm: float | int | Fraction,
               eccentricity_m: float) -> bool:
    """Does the residual eccentricity meet the declared balance grade?"""
    if eccentricity_m < 0:
        raise RotorError("eccentricity must be non-negative")
    return float(eccentricity_m) <= permissible_eccentricity_m(
        grade_mm_per_s, rpm)


# --- containment: rim speed, margin, and refusals -----------------------

def rim_speed_m_per_s(diameter_mm: float,
                      rpm: float | int | Fraction) -> float:
    """Rim speed ``v = pi * D * rpm / 60``, with D in metres.

    Monotonically increasing in both diameter and speed: a bigger wheel
    at the same rpm, or the same wheel faster, puts more energy in the
    rim and raises the hoop stress that decides whether it stays whole.
    """
    if diameter_mm <= 0:
        raise RotorError("diameter must be positive")
    r = float(rpm)
    if r < 0:
        raise RotorError("rpm must be non-negative")
    return math.pi * (float(diameter_mm) / 1000.0) * r / SECONDS_PER_MINUTE


def material_rim_speed_limit(material: str = DEFAULT_MATERIAL) -> float:
    """The declared safe rim speed for a material, in m/s."""
    try:
        return MATERIAL_RIM_SPEED_LIMIT_M_PER_S[material]
    except KeyError as exc:
        raise RotorError(
            f"no declared rim-speed limit for material {material!r}; an "
            f"undeclared limit is not an unlimited one") from exc


def burst_margin(diameter_mm: float, rpm: float | int | Fraction,
                 material: str = DEFAULT_MATERIAL) -> float:
    """Declared limit divided by rim speed. Below 1.0 is over the limit."""
    v = rim_speed_m_per_s(diameter_mm, rpm)
    limit = material_rim_speed_limit(material)
    if v == 0.0:
        return float("inf")
    return limit / v


# --- the rotor specification --------------------------------------------

@dataclass(frozen=True)
class RotorSpec:
    """The specification schema for a hybrid toothed rotor.

    Every field is a *specification*, not a measurement, and ``status``
    is pinned to ``MODEL_ONLY``. The two feature families are typed
    separately (:class:`ConductiveTab` vs :class:`FerromagneticInsert`)
    because they are sensed by different physics; the pickup channels
    declare which path each of them reads and whether it is signed.
    ``containment_class`` may be ``None``, and ``None`` means no
    containment has been declared -- which is a refusal condition, not a
    default-safe state.
    """

    teeth: int = REFERENCE_TEETH
    rpm: Fraction = REFERENCE_RPM
    diameter_mm: float = REFERENCE_DIAMETER_MM
    material: str = DEFAULT_MATERIAL
    conductive_tabs: tuple[ConductiveTab, ...] = ()
    ferromagnetic_inserts: tuple[FerromagneticInsert, ...] = ()
    pickup_channels: tuple[PickupChannel, ...] = field(default_factory=tuple)
    balance_grade: float | None = None
    containment_class: str | None = None
    status: str = MODEL_ONLY

    def __post_init__(self) -> None:
        if not isinstance(self.teeth, int) or isinstance(self.teeth, bool):
            raise RotorError("teeth must be an integer count")
        if self.teeth < 1:
            raise RotorError("teeth must be at least 1")
        object.__setattr__(self, "rpm", _exact(self.rpm, "rpm"))
        if self.rpm < 0:
            raise RotorError("rpm must be non-negative")
        if self.diameter_mm <= 0:
            raise RotorError("diameter must be positive")
        if self.status != MODEL_ONLY:
            raise RotorError(
                f"status {self.status!r} is refused: this schema describes "
                f"an UNBUILT rotor and its status is {MODEL_ONLY!r}. Nothing "
                f"here is printed, assembled, balanced or spun.")

    # -- exact quantities --
    @property
    def tooth_rate_hz(self) -> Fraction:
        """Exact tooth passages per second at the specified speed."""
        return tooth_passage_rate_hz(self.teeth, self.rpm)

    @property
    def tooth_pitch_deg(self) -> Fraction:
        return tooth_pitch_deg(self.teeth)

    @property
    def quadrature_offset_deg(self) -> Fraction:
        return quadrature_offset_deg(self.teeth)

    # -- counts --
    @property
    def n_conductive_tabs(self) -> int:
        return len(self.conductive_tabs)

    @property
    def n_ferromagnetic_inserts(self) -> int:
        return len(self.ferromagnetic_inserts)

    def transduction_paths(self) -> tuple[Transduction, ...]:
        """The distinct sensing paths this rotor's features would need."""
        paths: list[Transduction] = []
        if self.conductive_tabs:
            paths.append(Transduction.EDDY_CURRENT_CAPACITIVE)
        if self.ferromagnetic_inserts:
            paths.append(Transduction.VARIABLE_RELUCTANCE)
        return tuple(paths)

    # -- mechanical estimates (float) --
    @property
    def rim_speed_m_per_s(self) -> float:
        return rim_speed_m_per_s(self.diameter_mm, self.rpm)

    def burst_margin(self) -> float:
        return burst_margin(self.diameter_mm, self.rpm, self.material)


def reference_rotor(containment_class: str | None = None) -> RotorSpec:
    """The verified reference case: 192 teeth, 1280 rpm, exactly 4096 Hz.

    Carries four conductive tabs and two ferromagnetic inserts -- two
    independent transduction paths, deliberately -- and a signed
    quadrature pickup pair on the reluctance path. Containment is
    undeclared by default, because undeclared is the honest default.
    """
    return RotorSpec(
        teeth=REFERENCE_TEETH,
        rpm=REFERENCE_RPM,
        diameter_mm=REFERENCE_DIAMETER_MM,
        material=DEFAULT_MATERIAL,
        conductive_tabs=place_conductive_tabs(4),
        ferromagnetic_inserts=place_ferromagnetic_inserts(2),
        pickup_channels=quadrature_channel_pair(REFERENCE_TEETH),
        balance_grade=6.3,
        containment_class=containment_class,
    )


# --- safety refusals ----------------------------------------------------

def refuse_uncontained_operation(spec: RotorSpec) -> dict:
    """Refuse operation without containment, or above the rim-speed limit.

    Raises :class:`SafetyViolation` when no containment class is declared
    (absence is not permission) or when the specified rim speed exceeds
    the declared limit for the rotor material. Returns the margin figures
    otherwise -- which is a statement about the MODEL's numbers and still
    not authorisation to spin anything; see
    :func:`refuse_spin_authorization`.
    """
    if not isinstance(spec, RotorSpec):
        raise RotorError("a RotorSpec is required")
    v = spec.rim_speed_m_per_s
    limit = material_rim_speed_limit(spec.material)
    if not spec.containment_class:
        raise SafetyViolation(
            f"no containment class is declared for this rotor "
            f"({spec.teeth} teeth, {spec.diameter_mm} mm, {spec.rpm} rpm, "
            f"rim speed {v:.3f} m/s). An undeclared containment class is not "
            f"an unnecessary one: a rotor with no declared burst enclosure "
            f"is refused, and no spin condition may be modelled as safe "
            f"without one.")
    if v > limit:
        raise SafetyViolation(
            f"rim speed {v:.3f} m/s exceeds the declared limit {limit:.3f} "
            f"m/s for material {spec.material!r} (containment class "
            f"{spec.containment_class!r}). An unreinforced printed-polymer "
            f"rotor has a low safe rim speed and layer adhesion is its weak "
            f"axis; exceeding the declared limit is refused regardless of "
            f"what enclosure is claimed.")
    return {
        "rim_speed_m_per_s": v,
        "declared_limit_m_per_s": limit,
        "burst_margin": limit / v if v else float("inf"),
        "containment_class": spec.containment_class,
        "note": ("margins on a model's own declared numbers; not a "
                 "containment test and not authorisation to spin"),
    }


def refuse_unbalanced_operation(spec: RotorSpec, mass_kg: float,
                                eccentricity_m: float) -> dict:
    """Refuse operation with no balance grade, or outside the declared one."""
    if not isinstance(spec, RotorSpec):
        raise RotorError("a RotorSpec is required")
    if spec.balance_grade is None:
        raise SafetyViolation(
            "no balance grade is declared for this rotor. An unbalanced "
            "rotor loads its bearings with m*e*omega^2, which grows as the "
            "SQUARE of speed; an undeclared grade is an unbounded force.")
    force = residual_unbalance_force_N(mass_kg, eccentricity_m, spec.rpm)
    if not balance_ok(spec.balance_grade, spec.rpm, eccentricity_m):
        permitted = permissible_eccentricity_m(spec.balance_grade, spec.rpm)
        raise SafetyViolation(
            f"residual eccentricity {eccentricity_m:g} m exceeds the "
            f"permissible {permitted:g} m for grade G{spec.balance_grade} at "
            f"{spec.rpm} rpm; the residual unbalance force would be "
            f"{force:.3f} N at that speed, and it rises with the square of "
            f"any further speed increase.")
    return {
        "balance_grade": spec.balance_grade,
        "permissible_eccentricity_m": permissible_eccentricity_m(
            spec.balance_grade, spec.rpm),
        "eccentricity_m": eccentricity_m,
        "residual_unbalance_force_N": force,
        "note": ("arithmetic on declared model parameters; no rotor was "
                 "balanced, and no balancing machine exists here"),
    }


def refuse_spin_authorization(spec: RotorSpec | None = None,
                              requested_rpm=None,
                              operator: str | None = None,
                              containment_class: str | None = None) -> None:
    """ALWAYS raises. Nothing may be declared safe to spin from here.

    There is no rotor, no shaft, no drive, no enclosure, no interlock and
    no test cell. Every margin in this module is arithmetic on the
    model's own declared parameters, and arithmetic on declared
    parameters is not a containment test, a spin test, a balance
    certificate or an authorisation. The arguments exist only to name
    what a real authorisation would require, and supplying all of them
    changes nothing.
    """
    raise SafetyViolation(
        "spin authorisation is refused unconditionally. This module is a "
        "parametric MODEL: nothing is machined, printed, assembled, "
        "balanced, guarded, instrumented or spun, no apparatus exists, and "
        "no one is authorised by anything here to spin anything. A declared "
        "containment class, a declared balance grade and a computed burst "
        "margin are parameters of a model, not a proof-tested enclosure, a "
        "balancing certificate or a signed-off test procedure. "
        "PHYSICAL_VALIDATION_NOT_CLAIMED.")


# --- the report ---------------------------------------------------------

def rotor_report() -> dict:
    spec = reference_rotor(containment_class="ENCLOSURE_CLASS_DECLARED_MODEL")
    exact_rate = tooth_passage_rate_hz(REFERENCE_TEETH, REFERENCE_RPM)
    return {
        "what_this_is": (
            "a parametric model of a hybrid toothed rotor: exact tooth-rate "
            "arithmetic, quadrature pickup geometry with a signed direction "
            "rule, two separately typed transduction paths, and balance and "
            "containment arithmetic -- for a rotor that does not exist"),
        "a_model_is_not_a_rotor": (
            "nothing here is machined, printed, deburred, pressed, wired, "
            "balanced, mounted, guarded or spun; no apparatus exists"),
        "reference_case": {
            "teeth": REFERENCE_TEETH,
            "rpm": str(REFERENCE_RPM),
            "tooth_passage_rate_hz_exact": str(exact_rate),
            "arithmetic": "192 * 1280 / 60 = 245760 / 60 = 4096 (exact)",
            "is_exact_integer": exact_rate.denominator == 1,
            "inverts_exactly":
                rpm_for_rate(REFERENCE_TEETH, REFERENCE_RATE_HZ)
                == REFERENCE_RPM,
        },
        "quadrature": {
            "mechanical_offset_deg_exact":
                str(quadrature_offset_deg(REFERENCE_TEETH)),
            "mechanical_offset_rule": "360/(4*teeth)",
            "electrical_offset_deg_exact":
                str(quadrature_offset_electrical_deg(REFERENCE_TEETH)),
            "electrical_rule":
                "one tooth pitch is one electrical cycle, so electrical = "
                "mechanical * teeth; a quarter pitch is 90 electrical deg "
                "for every tooth count",
            "direction_rule":
                "sign of sum(a[i]*b[i+1] - a[i+1]*b[i]) over the two signed "
                "channels; antisymmetric, so swapping the channels reverses "
                "the reported direction",
            "two_signed_channels_required": True,
        },
        "transduction_paths": {
            "conductive_tabs": {
                "count": spec.n_conductive_tabs,
                "path": Transduction.EDDY_CURRENT_CAPACITIVE.value,
                "requires": "an electrically conductive feature loading a "
                            "driven field",
            },
            "ferromagnetic_inserts": {
                "count": spec.n_ferromagnetic_inserts,
                "path": Transduction.VARIABLE_RELUCTANCE.value,
                "requires": "a magnetically permeable feature altering a "
                            "magnetic circuit",
            },
            "paths_are_distinct": True,
        },
        "balance": {
            "force_law": "F = m * e * omega^2, omega = 2*pi*rpm/60",
            "scaling": "force grows as the SQUARE of shaft speed",
            "grade_rule": "ISO-style G = e_permissible * omega (mm/s)",
            "declared_grade": spec.balance_grade,
        },
        "containment": {
            "rim_speed_rule": "v = pi * D * rpm / 60",
            "rim_speed_m_per_s": spec.rim_speed_m_per_s,
            "declared_limit_m_per_s":
                material_rim_speed_limit(spec.material),
            "burst_margin": spec.burst_margin(),
            "material": spec.material,
            "note": ("declared design limits carried as model parameters; "
                     "no burst speed of any part was measured"),
        },
        "refusals": [
            "an approximate or floating rate presented as the exact design "
            "rate is refused -- refuse_approximate_rate",
            "direction from a single channel is refused; two signed channels "
            "are required -- refuse_direction_from_single_channel",
            "one transduction path does not imply the other -- "
            "refuse_transduction_equivalence",
            "operation without a declared containment class, or above the "
            "declared rim-speed limit, is refused -- "
            "refuse_uncontained_operation",
            "operation without a declared balance grade, or outside it, is "
            "refused -- refuse_unbalanced_operation",
            "spin authorisation is refused unconditionally and always -- "
            "refuse_spin_authorization",
        ],
        "status": spec.status,
        "evidence_class": EVIDENCE_CLASS,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "verdict": DEFAULT_VERDICT,
        "what_this_does_not_say": (
            "It does not say a rotor exists, was printed, machined, "
            "assembled, balanced, enclosed, instrumented or spun. It does "
            "not say any tooth rate, direction, rim speed, unbalance force "
            "or burst margin was observed: the exact quantities are rational "
            "arithmetic on declared parameters and the mechanical quantities "
            "are floating-point estimates from stated formulae. It does not "
            "say conductive tabs give reluctance sensing or that "
            "ferromagnetic inserts give eddy-current sensing. It does not "
            "say a single pickup channel can give direction. Above all it "
            "does not authorise spinning anything: no apparatus exists, no "
            "containment was proof-tested, no rotor was balanced, and "
            "'HYBRID_ROTOR_MODEL_IMPLEMENTED' means the MODEL is "
            "implemented, not the rotor. "
            "PHYSICAL_VALIDATION_NOT_CLAIMED."),
    }
