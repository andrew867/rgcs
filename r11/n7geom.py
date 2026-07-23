"""A03 — exact N=7 acoustic geometry, and the one-seventh phase identity.

The centrepiece of R11.1 is a single identity, and it is worth being
precise about why it is *exact* and what that exactness is worth.

Under the scalar design model a half-wave-stacked resonator of order ``N``
driven at ``f`` in a medium of wave speed ``v`` has

    L = v / (2 N f)

so the round-trip acoustic transit time is

    2L/v = 1/(N f)

and the drive phase accumulated during that round trip is

    f * 2L/v = 1/N turn.

For ``N = 7`` that is **exactly 1/7 turn = 360/7 degrees**. The velocity
``v`` and the frequency ``f`` cancel identically -- they never appear in
the answer. That is why this is an ``EXACT_IDENTITY`` and why it is tested
here with :class:`fractions.Fraction`, independent of floating point.

**And that is also precisely why it is not evidence of anything.** The
identity is a restatement of the definition of ``L``: we *chose* L so that
the round trip would take 1/(Nf), so of course the phase is 1/N. It holds
for every ``N``, every ``f`` and every ``v``. It carries no information
about quartz, about 4096 Hz, or about any physical specimen. A relation
that cannot fail is a definition, not a discovery, and
:func:`refuse_identity_as_evidence` says so.

The numeric geometry (lambda, L, transit times) *does* depend on v and f,
and those are `REPOSITORY_COMPUTATIONAL_RESULT` values under a declared
scalar model -- a control to be compared against anisotropic elasticity,
not a prediction about a real crystal.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction


class N7GeomError(RuntimeError):
    """Raised on a unit-category mix or an over-read of the identity."""


class Unit(Enum):
    """Dimensions carried explicitly. Bare numbers are never compared."""

    METRE = "m"
    MILLIMETRE = "mm"
    SECOND = "s"
    MICROSECOND = "us"
    HERTZ = "Hz"
    METRE_PER_SECOND = "m/s"
    TURN = "turn"
    DEGREE = "deg"
    RADIAN = "rad"


#: Which units may be compared/added with which. Anything else is a
#: category error -- microseconds are never compared with hertz.
_COMPATIBLE: dict[Unit, set[Unit]] = {
    Unit.METRE: {Unit.METRE, Unit.MILLIMETRE},
    Unit.MILLIMETRE: {Unit.METRE, Unit.MILLIMETRE},
    Unit.SECOND: {Unit.SECOND, Unit.MICROSECOND},
    Unit.MICROSECOND: {Unit.SECOND, Unit.MICROSECOND},
    Unit.HERTZ: {Unit.HERTZ},
    Unit.METRE_PER_SECOND: {Unit.METRE_PER_SECOND},
    Unit.TURN: {Unit.TURN, Unit.DEGREE, Unit.RADIAN},
    Unit.DEGREE: {Unit.TURN, Unit.DEGREE, Unit.RADIAN},
    Unit.RADIAN: {Unit.TURN, Unit.DEGREE, Unit.RADIAN},
}


@dataclass(frozen=True)
class Quantity:
    """An exact value with a declared dimension."""

    value: Fraction
    unit: Unit

    def __post_init__(self) -> None:
        if not isinstance(self.value, Fraction):
            raise N7GeomError(
                "n7geom carries exact rationals; pass a Fraction so the "
                "identity is provable rather than merely close")


def refuse_unit_comparison(a: Quantity, b: Quantity) -> Unit:
    """Refuse to compare two quantities of incompatible dimension."""
    if b.unit not in _COMPATIBLE[a.unit]:
        raise N7GeomError(
            f"refused: {a.unit.value!r} and {b.unit.value!r} are different "
            f"kinds of quantity and may not be compared or added by number "
            f"alone. Microseconds are not hertz and degrees are not "
            f"millimetres.")
    return a.unit


# --- the scalar design model -------------------------------------------

def wavelength(v_m_s: Fraction, f_hz: Fraction) -> Quantity:
    """lambda = v / f."""
    return Quantity(Fraction(v_m_s) / Fraction(f_hz), Unit.METRE)


def half_wave_length(v_m_s: Fraction, f_hz: Fraction, n: int) -> Quantity:
    """L = lambda / (2N) = v / (2 N f)."""
    if n < 1:
        raise N7GeomError("N must be a positive integer")
    return Quantity(Fraction(v_m_s) / (2 * n * Fraction(f_hz)), Unit.METRE)


def frequency_from_length(v_m_s: Fraction, length_m: Fraction,
                          n: int) -> Quantity:
    """f = v / (2 N L) -- the inverse of :func:`half_wave_length`."""
    if length_m <= 0:
        raise N7GeomError("length must be positive")
    return Quantity(Fraction(v_m_s) / (2 * n * Fraction(length_m)), Unit.HERTZ)


def one_way_time(v_m_s: Fraction, f_hz: Fraction, n: int) -> Quantity:
    """t = L / v."""
    return Quantity(half_wave_length(v_m_s, f_hz, n).value / Fraction(v_m_s),
                    Unit.SECOND)


def round_trip_time(v_m_s: Fraction, f_hz: Fraction, n: int) -> Quantity:
    """t = 2L / v, which equals 1/(N f) identically."""
    return Quantity(2 * one_way_time(v_m_s, f_hz, n).value, Unit.SECOND)


# --- THE IDENTITY -------------------------------------------------------

def round_trip_phase_turns(v_m_s: Fraction, f_hz: Fraction,
                           n: int) -> Fraction:
    """The drive phase accumulated in one acoustic round trip, in turns.

    Returns **exactly** ``Fraction(1, n)`` for every positive ``v`` and
    ``f``: the two cancel. This is the R11.1 critical identity.
    """
    t = round_trip_time(v_m_s, f_hz, n).value
    return Fraction(f_hz) * t


def round_trip_phase_degrees(n: int) -> Fraction:
    """360/N degrees exactly. For N=7 this is 360/7 = 51.428571..."""
    if n < 1:
        raise N7GeomError("N must be a positive integer")
    return Fraction(360, n)


def identity_holds(v_m_s: Fraction, f_hz: Fraction, n: int) -> bool:
    """True iff the accumulated phase is exactly 1/N turn."""
    return round_trip_phase_turns(v_m_s, f_hz, n) == Fraction(1, n)


def refuse_identity_as_evidence(*_args, **_kwargs) -> None:
    """Refuse to read the 1/N identity as a physical result.

    ``f * 2L/v = 1/N`` holds because ``L`` was *defined* as ``v/(2Nf)``.
    It is true for every N, every f and every v, so no measurement could
    contradict it. It says nothing about quartz, about 4096 Hz, or about
    any specimen.
    """
    raise N7GeomError(
        "refused: f * 2L/v = 1/N turn is an EXACT_IDENTITY that follows "
        "from the definition L = v/(2Nf). It holds for every N, f and v "
        "and cannot fail, so it is a definition rather than a discovery "
        "and is not evidence about any physical specimen.")


def refuse_scalar_model_as_specimen_prediction(*_args, **_kwargs) -> None:
    """The scalar model is a control, not a prediction about a crystal."""
    raise N7GeomError(
        "refused: the scalar half-wave model ignores anisotropic "
        "elasticity, piezoelectric stiffening, taper, terminations, "
        "support and electrode loading, and temperature. Its lengths are "
        "a CONTROL to compare against an anisotropic solution, not a "
        "prediction for a real specimen.")


# --- the frozen R11.1 configuration ------------------------------------

#: Scalar velocity proxy (m/s) and key frequency (Hz), as frozen by the
#: pack. The velocity is a PROXY: quartz is anisotropic and its wave speed
#: depends on direction, cut and mode.
V_PROXY_M_S = Fraction(6310)
F_KEY_HZ = Fraction(4096)
N_SEVEN = 7


def n7_geometry() -> dict:
    """The frozen N=7 numbers, exact where exact."""
    lam = wavelength(V_PROXY_M_S, F_KEY_HZ)
    L = half_wave_length(V_PROXY_M_S, F_KEY_HZ, N_SEVEN)
    t1 = one_way_time(V_PROXY_M_S, F_KEY_HZ, N_SEVEN)
    t2 = round_trip_time(V_PROXY_M_S, F_KEY_HZ, N_SEVEN)
    return {
        "N": N_SEVEN,
        "v_m_s": str(V_PROXY_M_S),
        "f_hz": str(F_KEY_HZ),
        "wavelength_m_exact": str(lam.value),
        "wavelength_m": float(lam.value),
        "length_mm": float(L.value * 1000),
        "length_m_exact": str(L.value),
        "one_way_us": float(t1.value * 10**6),
        "round_trip_us": float(t2.value * 10**6),
        "round_trip_turns_exact": str(round_trip_phase_turns(
            V_PROXY_M_S, F_KEY_HZ, N_SEVEN)),
        "round_trip_degrees_exact": str(round_trip_phase_degrees(N_SEVEN)),
        "round_trip_degrees": float(round_trip_phase_degrees(N_SEVEN)),
        "identity_holds": identity_holds(V_PROXY_M_S, F_KEY_HZ, N_SEVEN),
        "velocity_is_a_proxy": True,
        "claim_class": "EXACT_IDENTITY (phase) / "
                       "REPOSITORY_COMPUTATIONAL_RESULT (lengths)",
    }


def geometry_sweep(n_values=range(1, 25),
                   f_values=(8, 16, 32, 64, 128, 256, 512, 1024, 2048,
                             4096, 8192, 16384, 32768)) -> list[dict]:
    """Exact lengths across the N and frequency ladders.

    The phase identity is invariant across the whole sweep -- that
    invariance is the point, and it is why the identity carries no
    specimen information.
    """
    out = []
    for n in n_values:
        for f in f_values:
            L = half_wave_length(V_PROXY_M_S, Fraction(f), n)
            out.append({
                "N": n, "f_hz": f,
                "length_mm": float(L.value * 1000),
                "phase_turns": str(round_trip_phase_turns(
                    V_PROXY_M_S, Fraction(f), n)),
                "identity_holds": identity_holds(
                    V_PROXY_M_S, Fraction(f), n),
            })
    return out


def n7geom_report() -> dict:
    return {
        "what_this_is": (
            "exact unit-safe scalar acoustic geometry and the "
            "one-seventh round-trip phase identity"),
        "identity": "f * 2L/v = 1/N turn, exactly, for L = v/(2Nf)",
        "n7_degrees": "360/7 = 51.428571428571...",
        "geometry": n7_geometry(),
        "claim_class": "EXACT_IDENTITY",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": "N7_PHASE_IDENTITY_EXACT_BY_CONSTRUCTION",
        "what_this_does_not_say": (
            "The 1/N identity is a consequence of the definition of L and "
            "holds for every N, f and v, so it cannot fail and is not "
            "evidence about quartz, about 4096 Hz, or about any specimen. "
            "The lengths come from a scalar model with a proxy velocity "
            "and are a control, not a prediction. Nothing was measured."),
    }
