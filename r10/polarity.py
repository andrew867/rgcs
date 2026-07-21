"""P15/P17 — a polarity quadrature pulse compiler, and its firewall.

This module compiles drive waveforms for a ring of spatial poles and
computes the field vector they produce. It is signal and geometry
mathematics: currents in, a field locus out. Nothing here is measured,
and no coil has been built (hardware is deferred by the pack).

Two things it is careful about.

**A spatial pole is not a charge polarity.** Four coils placed at
0/90/180/270 degrees and fed ordinary alternating current produce a
*rotating field*, exactly as a two-phase induction motor does. That is
a geometric arrangement of ordinary AC. It asserts nothing about a sign
of charge, and it does not create four kinds of charge. The temptation
to read "four poles" as "four charge polarities" is the whole reason
:func:`refuse_four_charge_polarities` exists and raises loudly.

**The exact parts are kept exact.** Phase offsets (90*k and 60*k
degrees) are integers; the canonical sign patterns are integers; the
balanced-drive "net current sums to zero" identity is proven with
:class:`fractions.Fraction`, not asserted with a float tolerance. Only
the field-locus geometry, which involves cos and sin of those exact
angles, is evaluated in floating point.

P15 builds the four-channel quadrature drive and its waveform families
(sinusoidal quadrature, pulse-stepped, overlap, PWM). P17 extends the
ring to six poles and compares three ways of driving it: true
six-phase, dual three-phase, and alternating triads. The first two
produce the same rotating field for balanced sinusoids; the third does
not, and :func:`compare_six_pole_schemes` measures the difference
instead of asserting it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction

# --- geometry: spatial poles are coil positions, nothing more ----------

#: The four quadrature pole positions, in degrees. These are *places to
#: put a coil*, not signs of charge.
FOUR_POLE_ANGLES_DEG = (0, 90, 180, 270)

#: The six pole positions at 60-degree intervals.
SIX_POLE_ANGLES_DEG = (0, 60, 120, 180, 240, 300)

HARDWARE_STATUS = "DEFERRED — no coil has been built; nothing is measured"
EVIDENCE_CLASS = "DERIVED_MATHEMATICS"

#: The waveform families for the four-channel quadrature drive.
FOUR_POLE_FAMILIES = (
    "SINUSOIDAL_QUADRATURE",
    "PULSE_STEPPED",
    "OVERLAP",
    "PWM",
)

#: The three six-pole drive schemes P17 compares.
SIX_POLE_SCHEMES = (
    "TRUE_SIX_PHASE",
    "DUAL_THREE_PHASE",
    "ALTERNATING_TRIADS",
)


class ChargePolarityConflation(RuntimeError):
    """Raised when spatial poles are read as charge polarities."""


class WaveformError(ValueError):
    """Raised for an unknown or malformed waveform request."""


def pole_angles_deg(n_poles: int) -> tuple[int, ...]:
    """The exact integer pole angles for a ring of ``n_poles``.

    360 is divisible by both 4 and 6, so the spacing is an exact
    integer number of degrees. Any other pole count that does not
    divide 360 evenly is refused rather than rounded.
    """
    if n_poles <= 0:
        raise WaveformError("n_poles must be positive")
    if 360 % n_poles:
        raise WaveformError(
            f"{n_poles} poles do not divide 360 degrees evenly; this "
            f"module only builds rings with an integer degree spacing")
    return tuple((360 * k) // n_poles for k in range(n_poles))


def phase_offsets_deg(n_poles: int) -> tuple[int, ...]:
    """Per-channel phase offsets, in exact integer degrees.

    Channel k is driven with a phase offset of 360*k/n degrees, so that
    the drive advances in step with the pole geometry. For four poles
    this is 0/90/180/270; for six it is 0/60/120/180/240/300. The
    offset equals the pole angle here by construction, which is what
    makes the field rotate.
    """
    return pole_angles_deg(n_poles)


def _unit_vectors(angles_deg: tuple[int, ...]) -> list[tuple[float, float]]:
    return [(math.cos(math.radians(a)), math.sin(math.radians(a)))
            for a in angles_deg]


# --- P15: the four waveform families -----------------------------------

def _sign(x: float) -> int:
    return (x > 0) - (x < 0)


def _triangle(phase_rad: float) -> float:
    """A unit triangle carrier in [-1, 1], period 2*pi."""
    frac = (phase_rad / (2 * math.pi)) % 1.0
    # rises -1 -> +1 over the first half, falls back over the second
    return 4 * abs(frac - 0.5) - 1.0


def channel_currents(family: str, phase_rad: float, *,
                     n_poles: int = 4, amplitude: float = 1.0,
                     overlap_gain: float = 1.4,
                     carrier_ratio: int = 21) -> list[float]:
    """Instantaneous current in each channel at drive phase ``phase_rad``.

    The families differ in *shape*, not in the phase schedule: every
    channel k is evaluated at ``phase_rad - offset_k``, where offset_k
    is the exact geometric offset. The shapes are

    ``SINUSOIDAL_QUADRATURE``
        a pure cosine; the reference against which the rest are ripple.
    ``PULSE_STEPPED``
        a square wave (the sign of the cosine); the field steps between
        a small number of discrete states.
    ``OVERLAP``
        a clipped cosine, so that adjacent channels conduct at full
        amplitude over overlapping windows.
    ``PWM``
        a bipolar naturally-sampled pulse train whose *average* over a
        carrier period tracks the cosine reference. The instantaneous
        value is +/- amplitude; the sinusoid lives in the duty cycle.
    """
    if family not in FOUR_POLE_FAMILIES:
        raise WaveformError(
            f"unknown four-pole family {family!r}; "
            f"expected one of {FOUR_POLE_FAMILIES}")
    offsets = [math.radians(o) for o in phase_offsets_deg(n_poles)]
    out: list[float] = []
    for off in offsets:
        theta = phase_rad - off
        ref = math.cos(theta)
        if family == "SINUSOIDAL_QUADRATURE":
            val = ref
        elif family == "PULSE_STEPPED":
            val = float(_sign(ref))
        elif family == "OVERLAP":
            val = max(-1.0, min(1.0, overlap_gain * ref))
        else:  # PWM
            if carrier_ratio < 2:
                raise WaveformError("carrier_ratio must be >= 2")
            carrier = _triangle(carrier_ratio * phase_rad)
            val = 1.0 if ref >= carrier else -1.0
        out.append(amplitude * val)
    return out


def field_vector(currents: list[float],
                 angles_deg: tuple[int, ...]) -> tuple[float, float]:
    """Sum the channel unit vectors weighted by their currents.

    This is the resultant magnetomotive direction: each pole pushes the
    field toward its own position with a strength equal to its current,
    and the poles add as vectors. It is the one quantity that actually
    matters, because two different drive schemes are "the same" exactly
    when this locus is the same.
    """
    if len(currents) != len(angles_deg):
        raise WaveformError("currents and angles length mismatch")
    fx = sum(i * math.cos(math.radians(a))
             for i, a in zip(currents, angles_deg))
    fy = sum(i * math.sin(math.radians(a))
             for i, a in zip(currents, angles_deg))
    return (fx, fy)


def rotating_field_magnitudes(family: str = "SINUSOIDAL_QUADRATURE", *,
                              n_poles: int = 4, amplitude: float = 1.0,
                              samples: int = 720,
                              **params) -> list[float]:
    """The field magnitude sampled once per equal step of drive phase."""
    angles = pole_angles_deg(n_poles)
    mags = []
    for s in range(samples):
        phase = 2 * math.pi * s / samples
        cur = channel_currents(family, phase, n_poles=n_poles,
                               amplitude=amplitude, **params)
        fx, fy = field_vector(cur, angles)
        mags.append(math.hypot(fx, fy))
    return mags


def rotating_field_report(amplitude: float = 1.0,
                          samples: int = 720) -> dict:
    """Verify the rotating-field property for ideal sinusoidal quadrature.

    For a balanced sinusoidal quadrature drive the four channels reduce
    to F = (i0 - i2, i1 - i3) = (2A cos, 2A sin): a vector of constant
    magnitude 2A that rotates once per drive cycle. This function
    samples it and reports the constancy directly, so the claim is a
    measured-in-software number, not a bare assertion.
    """
    mags = rotating_field_magnitudes(
        "SINUSOIDAL_QUADRATURE", n_poles=4, amplitude=amplitude,
        samples=samples)
    mean = sum(mags) / len(mags)
    spread = (max(mags) - min(mags))
    return {
        "family": "SINUSOIDAL_QUADRATURE",
        "poles": 4,
        "expected_magnitude": 2 * amplitude,
        "mean_magnitude": mean,
        "peak_to_peak_ripple": spread,
        "relative_ripple": spread / mean if mean else math.inf,
        "is_constant_magnitude": spread / mean < 1e-9 if mean else False,
        "what_this_shows": (
            "opposite channels are driven 180 degrees apart, so the "
            "ring reduces to a two-phase quadrature pair and the "
            "resultant traces a circle at constant speed. This is "
            "ordinary rotating-field theory."),
        "what_this_does_not_say": (
            "that anything rotates physically, that a coil exists, or "
            "that the four poles are four charge polarities. It is the "
            "geometry of four AC currents added as vectors."),
    }


# --- P15 item 4: THE FIREWALL ------------------------------------------

def refuse_four_charge_polarities(*args, **kwargs) -> None:
    """Four spatial poles are NOT four charge polarities. This refuses.

    A spatial pole at 0, 90, 180, or 270 degrees is a *coil position*.
    A charge polarity is a *sign of charge*. There are two signs of
    electric charge; arranging four coils in a ring and feeding them
    quadrature AC produces a rotating field and does not invent two
    more.

    The rotating field is exactly what an ordinary two-phase or
    four-lead induction motor produces from mains AC. It is a geometric
    fact about vector addition of currents. Reading "four poles" as
    "four polarities of charge" confuses a position with a sign, and
    this module refuses to license that read.
    """
    raise ChargePolarityConflation(
        "four spatial poles at 0/90/180/270 degrees are four coil "
        "POSITIONS, not four polarities of charge. Feeding them "
        "quadrature AC yields a rotating field -- the same effect a "
        "two-phase induction motor gets from ordinary mains current -- "
        "which is geometry, not a new sign of charge. Electric charge "
        "has two signs; this arrangement does not create a third or a "
        "fourth, and nothing here measures charge at all.")


# --- P15 item 5: signed current states, and the zero-sum identity ------

def canonical_sign_patterns() -> list[dict]:
    """Enumerate the four-channel sign patterns of a rotating field.

    Because opposite channels are driven 180 degrees apart, channel k+2
    is always the negative of channel k (i2 = -i0, i3 = -i1). As the
    field sweeps a full turn the sign quadruple therefore steps through
    four states, one per quadrant. Each is given here with a *balanced*
    integer current realisation whose four entries sum to exactly zero
    -- a Kirchhoff-friendly drive draws no net current from the common
    node at any instant.

    The magnitudes 2 and 1 are arbitrary positive integers chosen only
    to make the signs concrete and the sum exact; the zero comes from
    the pairing, not from the choice.
    """
    a, b = Fraction(2), Fraction(1)   # arbitrary unequal positive magnitudes
    quadrant_states = [
        (a, b),      # i0>0, i1>0
        (-a, b),     # i0<0, i1>0
        (-a, -b),    # i0<0, i1<0
        (a, -b),     # i0>0, i1<0
    ]
    patterns = []
    for i0, i1 in quadrant_states:
        i2, i3 = -i0, -i1            # 180-degree pairing, exact
        currents = (i0, i1, i2, i3)
        patterns.append({
            "signs": tuple(_sign(float(c)) for c in currents),
            "currents": currents,
            "net_current": sum(currents),          # exact Fraction
            "sums_to_zero": sum(currents) == 0,
            "pairing_holds": i2 == -i0 and i3 == -i1,
        })
    return patterns


def cardinal_current_states(amplitude: Fraction = Fraction(1)) -> list[dict]:
    """The four-channel states at the cardinal drive phases 0/90/180/270.

    At these phases the ideal sinusoidal quadrature currents are exact:
    two channels sit at +/-A and the other two at 0. Every state sums to
    exactly zero, which is why the sum is carried as a
    :class:`~fractions.Fraction` and compared to an integer, not to a
    float tolerance.
    """
    A = Fraction(amplitude)
    states = [
        (A, Fraction(0), -A, Fraction(0)),     # phase 0
        (Fraction(0), A, Fraction(0), -A),     # phase 90
        (-A, Fraction(0), A, Fraction(0)),     # phase 180
        (Fraction(0), -A, Fraction(0), A),     # phase 270
    ]
    return [{
        "phase_deg": 90 * m,
        "currents": s,
        "net_current": sum(s),
        "sums_to_zero": sum(s) == 0,
    } for m, s in enumerate(states)]


# --- P17: three ways to drive six poles --------------------------------

def true_six_phase_currents(phase_rad: float,
                            amplitude: float = 1.0) -> list[float]:
    """Six phases at 60-degree increments: i_k = A cos(phase - 60k)."""
    return [amplitude * math.cos(phase_rad - math.radians(60 * k))
            for k in range(6)]


def dual_three_phase_currents(phase_rad: float,
                              amplitude: float = 1.0) -> list[float]:
    """Two wye sets 180 degrees apart, assembled independently.

    Set one drives the poles at 0/120/240 (indices 0, 2, 4) as a
    balanced three-phase system. Set two drives their antipodes at
    180/300/60 (indices 3, 5, 1) with currents shifted a further 180
    degrees. An antipodal pole carries the negated current *and* points
    the opposite way, so its contribution to the field coincides with
    its partner's -- which is why this reproduces the true six-phase
    field despite being built from two separate three-phase drives.

    The assembly here is deliberately routed through the two sets rather
    than short-cut to the six-phase formula, so that the equality with
    :func:`true_six_phase_currents` is a result, not a tautology.
    """
    A = amplitude
    currents = [0.0] * 6
    set1_poles = (0, 2, 4)              # spatial 0, 120, 240
    set2_poles = (3, 5, 1)              # antipodes: spatial 180, 300, 60
    for j, pole in enumerate(set1_poles):
        currents[pole] = A * math.cos(phase_rad - math.radians(120 * j))
    for j, pole in enumerate(set2_poles):
        currents[pole] = A * math.cos(
            phase_rad - math.radians(120 * j) - math.pi)
    return currents


def alternating_triads_currents(phase_rad: float,
                                amplitude: float = 1.0) -> list[float]:
    """Two triads driven at full current in alternation -> a stepped field.

    Each pole conducts at +A over the half cycle centred on its own
    position and -A over the other half (the sign of its cosine). At any
    instant three poles push one way and three the other, and the pair
    that dominates switches every 60 degrees, so the resultant does not
    glide round a circle -- it jumps between a fixed set of directions.
    That is the qualitative difference from the two sinusoidal schemes,
    and :func:`compare_six_pole_schemes` turns it into numbers.
    """
    return [amplitude * float(_sign(math.cos(phase_rad - math.radians(60 * k))))
            for k in range(6)]


_SIX_POLE_DRIVERS = {
    "TRUE_SIX_PHASE": true_six_phase_currents,
    "DUAL_THREE_PHASE": dual_three_phase_currents,
    "ALTERNATING_TRIADS": alternating_triads_currents,
}


def six_pole_currents(scheme: str, phase_rad: float,
                      amplitude: float = 1.0) -> list[float]:
    if scheme not in _SIX_POLE_DRIVERS:
        raise WaveformError(
            f"unknown six-pole scheme {scheme!r}; "
            f"expected one of {SIX_POLE_SCHEMES}")
    return _SIX_POLE_DRIVERS[scheme](phase_rad, amplitude)


# --- a self-contained harmonic analysis, for the distinguishing test ---

def _harmonic_amplitude(samples: list[float], h: int) -> float:
    """Amplitude of the h-th harmonic of a periodic sample sequence."""
    n = len(samples)
    re = sum(s * math.cos(2 * math.pi * h * k / n)
             for k, s in enumerate(samples))
    im = sum(s * math.sin(2 * math.pi * h * k / n)
             for k, s in enumerate(samples))
    return 2.0 * math.hypot(re, im) / n


def total_harmonic_distortion(samples: list[float],
                              max_harmonic: int | None = None) -> float:
    """THD = (RMS of harmonics 2..H) / (amplitude of the fundamental).

    Zero for a pure sinusoid; positive for anything with corners or
    steps. This is the measurable that separates a smoothly rotating
    field from a stepped one.
    """
    n = len(samples)
    max_harmonic = max_harmonic or (n // 2 - 1)
    fundamental = _harmonic_amplitude(samples, 1)
    if fundamental == 0:
        return math.inf
    harmonics = math.sqrt(sum(_harmonic_amplitude(samples, h) ** 2
                              for h in range(2, max_harmonic + 1)))
    return harmonics / fundamental


def compare_six_pole_schemes(amplitude: float = 1.0,
                             samples: int = 720) -> dict:
    """Measure how the three six-pole schemes differ, per scheme.

    For each scheme the field x-component is sampled over a full drive
    cycle and three measurables are computed:

    * ``thd_fx`` -- total harmonic distortion of the field waveform. A
      smoothly rotating field has a pure-sinusoid component (THD ~ 0); a
      stepped field carries harmonics (THD well above zero).
    * ``distinct_field_directions`` -- how many distinct directions the
      resultant points in over the cycle. A continuous rotation visits
      as many as it is sampled; a stepped field visits only a handful.
    * ``magnitude`` mean and ripple.

    True six-phase and dual three-phase come out identical; alternating
    triads is clearly separated on both THD and direction count.
    """
    angles = SIX_POLE_ANGLES_DEG
    result: dict = {"samples": samples, "schemes": {}}
    loci: dict[str, list[tuple[float, float]]] = {}
    for scheme in SIX_POLE_SCHEMES:
        fx_series, mags, directions = [], [], set()
        locus = []
        for s in range(samples):
            phase = 2 * math.pi * s / samples
            cur = six_pole_currents(scheme, phase, amplitude)
            fx, fy = field_vector(cur, angles)
            fx_series.append(fx)
            mags.append(math.hypot(fx, fy))
            locus.append((fx, fy))
            if math.hypot(fx, fy) > 1e-9:
                directions.add(round(math.atan2(fy, fx), 6))
        loci[scheme] = locus
        mean = sum(mags) / len(mags)
        result["schemes"][scheme] = {
            "thd_fx": total_harmonic_distortion(fx_series),
            "distinct_field_directions": len(directions),
            "mean_magnitude": mean,
            "magnitude_ripple": (max(mags) - min(mags)),
            "relative_magnitude_ripple": (
                (max(mags) - min(mags)) / mean if mean else math.inf),
        }
    # where they agree and differ, measured as the max field-vector gap
    def max_gap(p: str, q: str) -> float:
        return max(math.hypot(ax - bx, ay - by)
                   for (ax, ay), (bx, by) in zip(loci[p], loci[q]))

    result["agreement"] = {
        "six_phase_vs_dual_max_field_gap":
            max_gap("TRUE_SIX_PHASE", "DUAL_THREE_PHASE"),
        "six_phase_vs_alternating_max_field_gap":
            max_gap("TRUE_SIX_PHASE", "ALTERNATING_TRIADS"),
        "reading": (
            "true six-phase and dual three-phase trace the same locus "
            "(gap ~ 0): two three-phase sets 180 degrees apart are the "
            "six-phase drive rewritten. Alternating triads does not "
            "(large gap): it steps the field instead of rotating it."),
    }
    result["what_this_does_not_say"] = (
        "nothing here is a coil, a torque, or a measurement. The field "
        "is a vector sum of assumed currents; the schemes are compared "
        "as signal geometry only.")
    return result


# --- the report ---------------------------------------------------------

@dataclass(frozen=True)
class DriverLimits:
    """Driver constraints, carried as PARAMETERS, never as measurements.

    These are the numbers a bench driver would be configured to respect
    -- a current ceiling, a supply rail, an energy budget per pulse.
    They bound a hypothetical drive; they are not readings from one,
    because no drive has been built.
    """

    max_current_a: float
    supply_voltage_v: float
    energy_budget_j: float
    calibration_id: str = "UNCALIBRATED_NO_HARDWARE"

    def __post_init__(self) -> None:
        if self.max_current_a <= 0 or self.supply_voltage_v <= 0:
            raise ValueError("current and voltage limits must be positive")
        if self.energy_budget_j < 0:
            raise ValueError("energy budget cannot be negative")


def polarity_report(amplitude: float = 1.0) -> dict:
    """A single summary of what this module computes and disclaims."""
    return {
        "four_pole_angles_deg": FOUR_POLE_ANGLES_DEG,
        "six_pole_angles_deg": SIX_POLE_ANGLES_DEG,
        "four_pole_families": FOUR_POLE_FAMILIES,
        "six_pole_schemes": SIX_POLE_SCHEMES,
        "rotating_field": rotating_field_report(amplitude),
        "canonical_sign_patterns": canonical_sign_patterns(),
        "six_pole_comparison": compare_six_pole_schemes(amplitude),
        "hardware_status": HARDWARE_STATUS,
        "evidence_class": EVIDENCE_CLASS,
        "measured_here": "nothing",
        "the_firewall": (
            "four spatial poles are not four charge polarities; see "
            "refuse_four_charge_polarities()"),
        "what_this_is": (
            "a compiler from a pole ring and a waveform choice to a "
            "field-vector locus, with exact phase and sign arithmetic "
            "and a self-contained harmonic analysis."),
        "what_this_is_not": (
            "evidence of any physical field, torque, propulsion, "
            "gateway, or new sign of charge. A rotating field from AC "
            "in a coil ring is ordinary electrical engineering, and "
            "none of it has been built or measured."),
    }
