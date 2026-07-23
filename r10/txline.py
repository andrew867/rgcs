"""P11 — transmission lines, reflection/standing waves, and a grounding
policy whose safety cannot be traded away.

Two things live here, and they are kept apart on purpose.

**The electromagnetics is ordinary and model-only.** A uniform line of
characteristic impedance ``Z0`` terminated in a load ``ZL`` reflects a
fraction of the incident wave; the reflection coefficient is
``Gamma = (ZL - Z0) / (ZL + Z0)`` (complex in general) and the standing
wave ratio is ``SWR = (1 + |Gamma|) / (1 - |Gamma|)``. A matched load
(``ZL == Z0``) gives ``Gamma = 0`` and ``SWR = 1``; an open or a short
give ``|Gamma| = 1`` and an infinite SWR. The one-way propagation delay
is ``length / (velocity_factor * c)``, and an unterminated line looks
resonant at its quarter-wave frequencies -- which is exactly why the
source note that "long unterminated transmission lines are interferers"
is just textbook antenna behaviour, not a discovery. All of it is
:data:`DERIVED_MATHEMATICS`. **Nothing here is measured**, no cable is
on a bench, and the default verdict is therefore ``TXLINE_MODEL_ONLY``.

**The grounding is a safety firewall, and it does not defer to anything.**
The source material carried "grounding language" -- talk of removing
ground loops and quieting common-mode noise. EMI mitigation is a real
engineering goal, but it is *never* a licence to compromise electrical
safety. This module refuses, as hard typed errors, the two moves that
kill people: defeating protective earth (PE) or an RCD/GFCI to break a
ground loop (:func:`refuse_defeat_protective_earth`), and bonding a
person to mains earth or an improvised ground
(:func:`refuse_body_to_earth`). A line configuration flagged as
defeating PE is rejected at construction. The only ground-loop cures
this module will name are the safe ones -- single-point bonding,
galvanic isolation (isolation transformer / opto / transformer-coupled
or differential signalling) -- returned by
:func:`safe_ground_loop_mitigations`. This is the load-bearing part:
model verdicts are model-only, but the safety refusal is not a model
and is not negotiable.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum

# --- provenance ---------------------------------------------------------

C_M_PER_S = 299_792_458          # exact, SI definition of the metre

EVIDENCE_CLASS = "DERIVED_MATHEMATICS"
DEFAULT_VERDICT = "TXLINE_MODEL_ONLY"


# --- typed errors -------------------------------------------------------

class TxLineError(RuntimeError):
    """Raised for an ill-posed transmission-line model (bad geometry,
    impossible parameters). A modelling error, not a safety one."""


class SafetyViolation(RuntimeError):
    """Raised when an operation would compromise electrical safety.

    This is the firewall. It fires whether or not the caller thinks the
    move is 'just for EMI': protective earth and human isolation are not
    tunable parameters of a grounding model.
    """


# --- enumerated roles ---------------------------------------------------

class Geometry(Enum):
    COAX = "coax"
    TWISTED_PAIR = "twisted_pair"
    MICROSTRIP = "microstrip"
    STRIPLINE = "stripline"
    PARALLEL_WIRE = "parallel_wire"
    UNKNOWN = "unknown"


class Termination(Enum):
    MATCHED = "matched"          # ZL == Z0, no reflection
    OPEN = "open"                # |Gamma| = 1
    SHORT = "short"              # |Gamma| = 1
    RESISTIVE = "resistive"      # real ZL != Z0
    COMPLEX = "complex"          # complex ZL


class Shielding(Enum):
    UNSHIELDED = "unshielded"
    SHIELD_BONDED_ONE_END = "shield_bonded_one_end"     # avoids a shield loop
    SHIELD_BONDED_BOTH_ENDS = "shield_bonded_both_ends"
    SHIELD_HYBRID = "shield_hybrid_bond"                # DC one end, RF both


class SafetyClass(Enum):
    """How the installation stays safe. The last value is the one the
    module exists to reject: it is only defined so a configuration can be
    *named* as forbidden and then refused at construction."""

    PROTECTIVE_EARTH_INTACT = "protective_earth_intact"
    DOUBLE_INSULATED = "double_insulated"
    GALVANICALLY_ISOLATED = "galvanically_isolated"
    DEFEATS_PROTECTIVE_EARTH = "defeats_protective_earth"   # FORBIDDEN


#: The safety classes a constructed line may declare. Anything outside
#: this set is a safety refusal, not a modelling choice.
ALLOWED_SAFETY_CLASSES = frozenset({
    SafetyClass.PROTECTIVE_EARTH_INTACT,
    SafetyClass.DOUBLE_INSULATED,
    SafetyClass.GALVANICALLY_ISOLATED,
})


# --- the physics, as free functions ------------------------------------

def reflection_coefficient(z0: complex, zl: complex) -> complex:
    """Gamma = (ZL - Z0) / (ZL + Z0). Complex impedances allowed.

    ``z0`` must be non-zero (a real line has a defined characteristic
    impedance). If ``ZL + Z0 == 0`` the load is the negative of the line
    impedance -- unphysical for passive components -- and that is a
    model error, not a safety one.
    """
    z0 = complex(z0)
    zl = complex(zl)
    if z0 == 0:
        raise TxLineError("characteristic impedance Z0 must be non-zero")
    denom = zl + z0
    if denom == 0:
        raise TxLineError(
            "ZL + Z0 == 0 (load is -Z0); reflection is undefined for a "
            "passive line")
    return (zl - z0) / denom


def gamma_for_termination(z0: complex, termination: Termination,
                          zl: complex | None = None) -> complex:
    """Reflection coefficient keyed on the termination kind.

    OPEN gives ``+1`` and SHORT gives ``-1`` exactly (the two ends of
    ``|Gamma| = 1``); MATCHED gives ``0``; the resistive/complex cases
    fall through to :func:`reflection_coefficient` on the given ``zl``.
    """
    if termination is Termination.OPEN:
        return 1 + 0j
    if termination is Termination.SHORT:
        return -1 + 0j
    if termination is Termination.MATCHED:
        return 0 + 0j
    if zl is None:
        raise TxLineError(f"{termination.value} termination needs a load ZL")
    return reflection_coefficient(z0, zl)


def swr_from_gamma(gamma: complex) -> float:
    """SWR = (1 + |Gamma|) / (1 - |Gamma|).

    ``|Gamma| == 0`` -> 1 (matched). ``|Gamma| -> 1`` -> infinity
    (open/short). ``|Gamma| > 1`` is unphysical for a passive load and
    is refused as a model error.
    """
    mag = abs(complex(gamma))
    if mag > 1 + 1e-12:
        raise TxLineError(f"|Gamma| = {mag:g} > 1 is unphysical for a "
                          f"passive load")
    if mag >= 1.0:
        return math.inf
    return (1.0 + mag) / (1.0 - mag)


def one_way_delay(length_m: float, velocity_factor: float,
                  c: float = C_M_PER_S) -> float:
    """Delay = length / (velocity_factor * c), in seconds."""
    if length_m < 0:
        raise TxLineError("length cannot be negative")
    if not (0 < velocity_factor <= 1):
        raise TxLineError("velocity factor must be in (0, 1]")
    return length_m / (velocity_factor * c)


def lowest_quarter_wave_frequency(length_m: float, velocity_factor: float,
                                  c: float = C_M_PER_S) -> float:
    """Lowest frequency at which an open line looks a quarter-wave long:
    ``f = velocity_factor * c / (4 * L)``.

    An unterminated (open) line of length ``L`` presents a resonance
    whenever ``L = (2k+1) * lambda / 4``; the ``k = 0`` term is the
    lowest such frequency. This is the ordinary quarter-wave resonance
    that makes a long unterminated line an efficient interferer.
    """
    if length_m <= 0:
        raise TxLineError("length must be positive for a resonance")
    if not (0 < velocity_factor <= 1):
        raise TxLineError("velocity factor must be in (0, 1]")
    return velocity_factor * c / (4.0 * length_m)


def quarter_wave_frequencies(length_m: float, velocity_factor: float,
                             count: int = 3,
                             c: float = C_M_PER_S) -> list[float]:
    """The first ``count`` quarter-wave resonances: odd multiples
    ``(2k+1)`` of the lowest quarter-wave frequency."""
    if count < 1:
        raise TxLineError("count must be at least 1")
    f0 = lowest_quarter_wave_frequency(length_m, velocity_factor, c)
    return [(2 * k + 1) * f0 for k in range(count)]


def differential_vs_common_mode_note() -> dict:
    """The distinction the grounding language keeps blurring."""
    return {
        "differential_mode": (
            "the wanted signal: equal-and-opposite currents on the two "
            "conductors; rejected by neither and carried by the line"),
        "common_mode": (
            "currents flowing the same direction on both conductors, "
            "returning through ground; this is what a ground loop drives "
            "and what shielding/bonding and isolation address"),
        "the_confusion": (
            "'remove the ground loop' is a common-mode problem; the fix "
            "is to break the common-mode return safely, never to remove "
            "the protective-earth path that keeps a fault current from "
            "flowing through a person"),
    }


# --- the SAFETY FIREWALL ------------------------------------------------

def safe_ground_loop_mitigations() -> list[str]:
    """The only ground-loop cures this module will name. Every one of
    them leaves protective earth intact.

    A ground loop is broken by removing the *unwanted common-mode return*
    or the *low-impedance signal-ground bond*, never by removing the
    *safety* earth. These are the safe ways to do it.
    """
    return [
        "single-point (star) grounding: one bonding point for signal "
        "grounds, so no low-impedance loop is formed",
        "galvanic isolation of the signal: isolation transformer, "
        "opto-isolator, or transformer/differential coupling breaks the "
        "loop without touching protective earth",
        "balanced/differential signalling with good common-mode "
        "rejection, so common-mode current does not become signal",
        "shield bonded at one end only (or a hybrid DC-one-end / "
        "RF-both-ends bond) to stop a shield-current loop",
        "common-mode chokes / ferrites to raise the impedance of the "
        "common-mode path",
        "a mains isolation transformer to break the mains-side loop "
        "while the equipment keeps its own protective earth",
    ]


def refuse_defeat_protective_earth(reason: str = "") -> None:
    """Refuse to defeat protective earth or an RCD/GFCI to quiet a loop.

    Lifting the earth pin, cutting the PE conductor, or disabling a
    residual-current device does silence a ground loop -- by removing the
    path that carries fault current safely away and trips the breaker.
    The next fault then finds earth through a person. There is no EMI
    benefit that licenses this, so it is refused unconditionally.
    """
    raise SafetyViolation(
        "refusing to defeat protective earth or an RCD/GFCI to reduce a "
        "ground loop" + (f" ({reason})" if reason else "") + ". Removing "
        "the protective-earth path or disabling residual-current "
        "protection turns a nuisance hum into an electrocution hazard: "
        "the earth conductor exists to carry fault current and trip the "
        "breaker, not to be lifted for quiet. Use a safe mitigation "
        "instead (see safe_ground_loop_mitigations).")


def refuse_body_to_earth(reason: str = "") -> None:
    """Refuse to connect a person to mains earth or an improvised ground.

    Grounding-language sometimes drifts toward connecting a body to
    'earth'. Deliberately bonding a person to mains protective earth, a
    building ground, a water pipe, or any improvised ground places them
    across a potential difference and makes them a fault-current path.
    Refused unconditionally.
    """
    raise SafetyViolation(
        "refusing to connect a person to mains earth or an improvised "
        "ground" + (f" ({reason})" if reason else "") + ". A human body "
        "is not a grounding conductor; bonding a person to earth makes "
        "them a path for fault current. This module models cables, not "
        "people, and will not describe or endorse any body-to-earth "
        "connection.")


# --- the line schema ----------------------------------------------------

@dataclass(frozen=True)
class TransmissionLine:
    """A modelled transmission line. Derived electrical quantities
    (reflection coefficient, SWR, one-way delay) are computed at
    construction; the safety class is checked at construction and a
    configuration that defeats protective earth is rejected outright.
    """

    line_id: str
    geometry: Geometry
    length: float                       # metres
    termination: Termination
    source_impedance: complex
    load_impedance: complex | None      # None == open (infinite)
    velocity_factor: float
    frequency_range: tuple[float, float] | None = None
    common_mode_path: str = "unspecified"
    shielding: Shielding = Shielding.UNSHIELDED
    safety_class: SafetyClass = SafetyClass.PROTECTIVE_EARTH_INTACT
    status: str = DEFAULT_VERDICT

    # derived, filled in __post_init__
    delay: float = field(init=False)
    reflection_coefficient: complex = field(init=False)
    SWR: float = field(init=False)

    def __post_init__(self) -> None:
        # --- SAFETY GATE first: a forbidden class never constructs ------
        if self.safety_class not in ALLOWED_SAFETY_CLASSES:
            raise SafetyViolation(
                f"line {self.line_id!r} declares safety_class "
                f"{self.safety_class.value!r}: a configuration that "
                f"defeats protective earth is refused at construction. "
                f"Ground-loop mitigation never overrides electrical "
                f"safety.")

        # --- model validation -------------------------------------------
        z0 = complex(self.source_impedance)
        gamma = gamma_for_termination(z0, self.termination,
                                      self.load_impedance)
        swr = swr_from_gamma(gamma)
        delay = one_way_delay(self.length, self.velocity_factor)

        object.__setattr__(self, "reflection_coefficient", gamma)
        object.__setattr__(self, "SWR", swr)
        object.__setattr__(self, "delay", delay)

    @property
    def is_matched(self) -> bool:
        return abs(self.reflection_coefficient) < 1e-12

    def lowest_quarter_wave_frequency(self) -> float:
        return lowest_quarter_wave_frequency(self.length,
                                             self.velocity_factor)


# --- report -------------------------------------------------------------

def txline_report() -> dict:
    return {
        "what_this_is": (
            "an ordinary model of transmission-line reflection and "
            "standing waves, plus a non-negotiable grounding-safety "
            "firewall"),
        "the_model": (
            "Gamma = (ZL - Z0)/(ZL + Z0); SWR = (1+|Gamma|)/(1-|Gamma|); "
            "matched load gives SWR 1, open/short give SWR infinity; "
            "one-way delay = length/(velocity_factor*c); an unterminated "
            "line resonates at its quarter-wave frequencies, which is why "
            "a long unterminated line is an efficient interferer"),
        "the_firewall": (
            "EMI/ground-loop mitigation never overrides electrical "
            "safety: protective earth and RCD/GFCI protection are never "
            "defeated, and a person is never bonded to earth"),
        "safe_ground_loop_mitigations": safe_ground_loop_mitigations(),
        "common_vs_differential": differential_vs_common_mode_note(),
        "evidence_class": EVIDENCE_CLASS,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": DEFAULT_VERDICT,
        "what_this_does_not_say": (
            "It does not say any cable was built, terminated, or "
            "measured; the reflection coefficients, SWRs, delays and "
            "resonances are computed from parameters, not from a bench. "
            "It does not endorse defeating protective earth, disabling an "
            "RCD/GFCI, or connecting a person to earth to reduce a ground "
            "loop -- those are refused as safety violations, not offered "
            "as options, and no model verdict softens that refusal."),
    }
