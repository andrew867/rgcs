"""P01 — the fractional phase alphabet, exact, and what one channel loses.

A supplied set of four rationals -- 2/3, 3/4, 5/6 and 7/2 -- is read here
as *phases*, i.e. as fractions of one turn. The arithmetic is kept exact
(``Fraction``) so nothing rounds at a claim boundary, and floating point
appears only where trigonometry forces it.

Two distinctions are load-bearing, and this module exists mostly to hold
them apart.

**(a) A supplied rational 7/2 is NOT the Cs-133 nuclear spin I = 7/2.**
Reduced mod one turn, 7/2 turns is 1/2 turn -- 180 degrees. That
reduction is the interesting arithmetic fact about the symbol. The
nuclear spin quantum number of Cs-133 is also written 7/2, and the two
are *numerically equal and categorically different*: a phase is an
angular turn, a spin is a quantum number labelling an angular-momentum
representation. Turning one into the other is not a decoding, it is a
pun. The most that numerical equality supports is a
``CANDIDATE_CORRESPONDENCE``, and
:func:`refuse_spin_phase_conflation` refuses to go further.

**(b) A single quadratic channel cannot distinguish all four symbols.**
This is the headline negative result and it is arithmetic, not opinion.
The four phases land at 240, 270, 300 and 180 degrees. A quadratic
observable -- ``cos^2(theta)``, the shape a quadratic Zeeman projection
or any intensity-only detector has -- maps 240 and 300 degrees to the
*same* value, 0.25, because cos(240) = -1/2 and cos(300) = +1/2 and the
square destroys the sign. So the alphabet has four symbols and a single
quadratic channel has at most three outputs for them. Pairing it with
``sin^2`` does not help: ``sin^2 = 1 - cos^2`` is the same channel
written backwards, not a second independent one. Recovering all four
symbols requires a *signed*, phase-sensitive measurement -- two signed
quadratures, two orthogonal field axes, in-phase/quadrature microwave
channels, or a Ramsey pair with a scanned relative phase.

A third, quieter discipline: frequency and angular frequency are carried
separately and never mixed. ``omega = 2*pi*f`` and ``f = omega/(2*pi)``;
every quantity declares its unit, and combining two quantities of
different unit kinds by number alone is refused.

Everything here is arithmetic over supplied rationals. No field is
applied, no atom is interrogated, nothing is measured.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction

#: One full turn, in degrees, and the 24-fold sector lattice it carries.
DEGREES_PER_TURN = 360
SECTOR_COUNT = 24
SECTOR_DEGREES = Fraction(DEGREES_PER_TURN, SECTOR_COUNT)      # 15 exactly

#: The scaling carried alongside each symbol from the reference table.
TIMES_BASE = 192

#: Floating trigonometry is rounded here, and only here, so that exact
#: quarter-turn values compare cleanly. The rationals stay exact.
PROJECTION_DECIMALS = 12

#: The standing verdict for this module.
VERDICT = "FRACTIONAL_PHASE_ALPHABET_SPECIFIABLE"

EVIDENCE_CLASS = "DERIVED_MATHEMATICS from SOURCE_CLAIM rationals"
MEASURED_HERE = "nothing"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: The strongest status a numerical coincidence can earn.
CANDIDATE_CORRESPONDENCE = "CANDIDATE_CORRESPONDENCE"


class PhaseAlphaError(ValueError):
    """Raised when a phase is conflated with a spin quantum number, when
    a single quadratic channel is claimed to preserve every symbol, or
    when quantities of different unit kinds are combined by number."""


# --- units: frequency and angular frequency are not the same thing -----

class Unit(Enum):
    CYCLES_PER_SECOND = "CYCLES_PER_SECOND"
    RADIANS_PER_SECOND = "RADIANS_PER_SECOND"
    DEGREES = "DEGREES"
    TURNS = "TURNS"


@dataclass(frozen=True)
class Quantity:
    """A number that knows what kind of thing it is."""

    value: float
    unit: Unit


def angular_frequency(f: Quantity) -> Quantity:
    """omega = 2*pi*f. Input must be in cycles per second."""
    if f.unit is not Unit.CYCLES_PER_SECOND:
        raise PhaseAlphaError(
            f"angular_frequency expects {Unit.CYCLES_PER_SECOND.value}, "
            f"got {f.unit.value}. omega = 2*pi*f only holds when f is a "
            f"frequency in cycles per second.")
    return Quantity(2 * math.pi * f.value, Unit.RADIANS_PER_SECOND)


def ordinary_frequency(omega: Quantity) -> Quantity:
    """f = omega/(2*pi). Input must be in radians per second."""
    if omega.unit is not Unit.RADIANS_PER_SECOND:
        raise PhaseAlphaError(
            f"ordinary_frequency expects "
            f"{Unit.RADIANS_PER_SECOND.value}, got {omega.unit.value}. "
            f"f = omega/(2*pi) only holds when omega is an angular "
            f"frequency in radians per second.")
    return Quantity(omega.value / (2 * math.pi), Unit.CYCLES_PER_SECOND)


def refuse_unit_confusion(a: Quantity, b: Quantity) -> Unit:
    """Refuse to combine two quantities of different unit kinds.

    Returns the shared unit when the two agree, so callers can use it as
    a guard. Raises when they do not: a factor of 2*pi, or of 360, is
    not a rounding detail, and a number that has lost its unit has lost
    the only thing that made it a physical statement.
    """
    if a.unit is b.unit:
        return a.unit
    raise PhaseAlphaError(
        f"refusing to combine {a.value} {a.unit.value} with {b.value} "
        f"{b.unit.value} by number alone. These are different unit "
        f"kinds; frequency and angular frequency differ by 2*pi, and "
        f"turns and degrees by 360. Convert explicitly "
        f"(angular_frequency / ordinary_frequency / degrees_of) or do "
        f"not combine them.")


# --- the alphabet, exact ------------------------------------------------

def phase_mod_turn(literal: Fraction | int | str) -> Fraction:
    """Reduce a literal rational to a phase in [0, 1) turns, exactly."""
    return Fraction(literal) % 1


def degrees_of(phase_turns: Fraction) -> Fraction:
    """Turns to degrees, exactly: phase * 360."""
    return Fraction(phase_turns) * DEGREES_PER_TURN


def sector_15deg(degrees: Fraction) -> int:
    """Index on the 24-fold, 15-degree lattice. Must land exactly."""
    idx = Fraction(degrees) / SECTOR_DEGREES
    if idx.denominator != 1:
        raise PhaseAlphaError(
            f"{degrees} degrees is not on the {SECTOR_DEGREES}-degree "
            f"lattice (index {idx} is not an integer); it has no sector.")
    return int(idx)


def times_192(value: Fraction) -> Fraction:
    """The reference scaling, exact. 192 * value."""
    return Fraction(value) * TIMES_BASE


@dataclass(frozen=True)
class PhaseSymbol:
    """One symbol of the alphabet. Every field is exact."""

    pair: str                    # the two-digit label, e.g. "72"
    literal: Fraction            # as supplied, e.g. 7/2
    phase_turns: Fraction        # reduced mod one turn, e.g. 1/2
    degrees: Fraction            # phase * 360, e.g. 180
    sector: int                  # 15-degree lattice index, e.g. 12
    literal_times_192: Fraction  # 192 * literal, e.g. 672
    phase_times_192: Fraction    # 192 * phase, e.g. 96

    @property
    def reduces(self) -> bool:
        """True when the literal is not already a phase in [0, 1)."""
        return self.literal != self.phase_turns

    @property
    def radians(self) -> float:
        """The phase angle in radians. Float, because pi is irrational."""
        return math.radians(float(self.degrees))


def make_symbol(pair: str, literal: Fraction | int | str) -> PhaseSymbol:
    """Build one symbol from its literal rational, exactly."""
    lit = Fraction(literal)
    phase = phase_mod_turn(lit)
    deg = degrees_of(phase)
    return PhaseSymbol(
        pair=pair,
        literal=lit,
        phase_turns=phase,
        degrees=deg,
        sector=sector_15deg(deg),
        literal_times_192=times_192(lit),
        phase_times_192=times_192(phase),
    )


#: The alphabet. Public, neutral name.
PHASE_ALPHABET_A: tuple[PhaseSymbol, ...] = (
    make_symbol("23", Fraction(2, 3)),
    make_symbol("34", Fraction(3, 4)),
    make_symbol("56", Fraction(5, 6)),
    make_symbol("72", Fraction(7, 2)),   # reduces to 1/2 turn -> 180 deg
)

SYMBOLS_BY_PAIR = {s.pair: s for s in PHASE_ALPHABET_A}


def symbol(pair: str) -> PhaseSymbol:
    try:
        return SYMBOLS_BY_PAIR[pair]
    except KeyError:
        raise PhaseAlphaError(
            f"{pair!r} is not a symbol of the alphabet "
            f"({', '.join(SYMBOLS_BY_PAIR)})") from None


def alphabet_table() -> list[dict]:
    """The alphabet as a readable table; exact values kept as strings."""
    return [
        {
            "pair": s.pair,
            "literal": str(s.literal),
            "phase_turns": str(s.phase_turns),
            "degrees": float(s.degrees),
            "sector_15deg": s.sector,
            "literal_times_192": str(s.literal_times_192),
            "phase_times_192": str(s.phase_times_192),
            "literal_and_phase_scalings_agree": (
                s.literal_times_192 == s.phase_times_192),
            "reduces_mod_one_turn": s.reduces,
            "cos2_sin2": quadratic_projections(s),
        }
        for s in PHASE_ALPHABET_A
    ]


def on_15_degree_lattice() -> bool:
    """All four symbols land exactly on the 24-fold sector lattice."""
    return all(Fraction(s.degrees) % SECTOR_DEGREES == 0
               for s in PHASE_ALPHABET_A)


# --- the two meanings of 7/2, kept apart -------------------------------

#: 7/2 as a supplied rational phase/multiplier, and 7/2 as the Cs-133
#: nuclear spin quantum number. Numerically equal, categorically not.
SEVEN_HALVES = Fraction(7, 2)

SEVEN_HALVES_MEANINGS = {
    "RATIONAL_PHASE": {
        "value": str(SEVEN_HALVES),
        "kind": "angular turn (dimensionless fraction of one turn)",
        "reduces_mod_one_turn_to": str(phase_mod_turn(SEVEN_HALVES)),
        "degrees": float(degrees_of(phase_mod_turn(SEVEN_HALVES))),
    },
    "NUCLEAR_SPIN_I": {
        "value": str(SEVEN_HALVES),
        "kind": "quantum number labelling an angular-momentum "
                "representation (Cs-133 ground-state nuclear spin)",
        "reduces_mod_one_turn_to": None,
        "degrees": None,
    },
}


def seven_halves_correspondence() -> dict:
    """The numerical coincidence, stated as a candidate and no more."""
    return {
        "meanings": SEVEN_HALVES_MEANINGS,
        "numerically_equal": True,
        "same_kind_of_quantity": False,
        "status": CANDIDATE_CORRESPONDENCE,
        "note": (
            "a spin quantum number does not reduce mod one turn and "
            "has no degree measure; a phase does and has. Equality of "
            "the numeral 7/2 in the two contexts is a coincidence of "
            "notation until an independent mechanism links them"),
    }


def refuse_spin_phase_conflation(rational: Fraction | str = SEVEN_HALVES,
                                 context: str = "") -> None:
    """Refuse to read a supplied rational phase as a nuclear spin.

    Raises unconditionally. Numerical equality between a supplied 7/2
    and the Cs-133 nuclear spin I = 7/2 is a CANDIDATE_CORRESPONDENCE
    only.
    """
    val = Fraction(rational)
    where = f" ({context})" if context else ""
    raise PhaseAlphaError(
        f"refusing to identify the supplied rational {val} with the "
        f"Cs-133 nuclear spin I = {val}{where}. A nuclear spin is a "
        f"quantum number labelling an angular-momentum representation; "
        f"it is not an angular turn, does not reduce mod one turn, and "
        f"has no degree measure. As a phase, {val} reduces to "
        f"{phase_mod_turn(val)} turn "
        f"({float(degrees_of(phase_mod_turn(val)))} degrees) -- which "
        f"is exactly the arithmetic a spin quantum number does not do. "
        f"The equality of the numeral is a {CANDIDATE_CORRESPONDENCE} "
        f"and nothing stronger.")


# --- two-channel models, implemented separately ------------------------

class ChannelModel(Enum):
    SIGNED_QUADRATURE = "SIGNED_QUADRATURE"
    ORTHOGONAL_FIELD_AXES = "TWO_ORTHOGONAL_MAGNETIC_FIELD_AXES"
    IQ_MICROWAVE = "IN_PHASE_AND_QUADRATURE_MICROWAVE"
    RAMSEY_ZONES = "RAMSEY_ZONES_WITH_RELATIVE_PHASE"
    QUADRATIC_ZEEMAN = "SINGLE_QUADRATIC_ZEEMAN_PROJECTION"


#: Convenience alias for the one model that loses symbols.
SINGLE_QUADRATIC_CHANNEL = ChannelModel.QUADRATIC_ZEEMAN


@dataclass(frozen=True)
class ChannelReading:
    """What one channel model reports for one symbol."""

    pair: str
    model: str
    channel_names: tuple[str, str]
    values: tuple[float, float]
    phase_sensitive: bool
    note: str = ""


def _r(x: float) -> float:
    """Round trigonometric output so exact quarter turns compare cleanly."""
    return round(x, PROJECTION_DECIMALS) + 0.0     # normalise -0.0


def signed_quadrature(sym: PhaseSymbol) -> ChannelReading:
    """Model 1: signed cos(theta), sin(theta). Phase-sensitive."""
    th = sym.radians
    return ChannelReading(
        sym.pair, ChannelModel.SIGNED_QUADRATURE.value,
        ("cos_theta", "sin_theta"),
        (_r(math.cos(th)), _r(math.sin(th))),
        phase_sensitive=True,
        note="the sign is retained, so the full turn is resolved")


def orthogonal_field_axes(sym: PhaseSymbol) -> ChannelReading:
    """Model 2: projections on two physical orthogonal magnetic-field axes.

    Two real axes, each reporting a signed projection of the same
    direction. Arithmetically the same content as signed quadrature; the
    difference is that these are two separate physical measurements.
    """
    th = sym.radians
    return ChannelReading(
        sym.pair, ChannelModel.ORTHOGONAL_FIELD_AXES.value,
        ("axis_x_projection", "axis_y_projection"),
        (_r(math.cos(th)), _r(math.sin(th))),
        phase_sensitive=True,
        note="two physically distinct axes, each signed; the pair fixes "
             "the quadrant")


def iq_microwave(sym: PhaseSymbol) -> ChannelReading:
    """Model 3: in-phase and quadrature microwave channels.

    A demodulator referenced to a local oscillator: I = cos(theta),
    Q = sin(theta) relative to that reference. Phase-sensitive because
    the reference supplies the sign.
    """
    th = sym.radians
    return ChannelReading(
        sym.pair, ChannelModel.IQ_MICROWAVE.value,
        ("in_phase_I", "quadrature_Q"),
        (_r(math.cos(th)), _r(math.sin(th))),
        phase_sensitive=True,
        note="signs are relative to the local-oscillator reference; "
             "without that reference the channel is not phase-sensitive")


def ramsey_zones(sym: PhaseSymbol,
                 relative_phase_deg: Fraction | int = 0) -> ChannelReading:
    """Model 4: two Ramsey interaction zones with a relative phase.

    The fringe is P(phi) = (1 + cos(theta - phi)) / 2. One setting of
    phi is one number; the pair of settings phi = 0 and phi = 90 degrees
    recovers both signed components, so a *scanned* relative phase is
    phase-sensitive. The default setting is reported alongside.
    """
    th = sym.radians
    phi = math.radians(float(Fraction(relative_phase_deg)))
    p0 = (1 + math.cos(th - phi)) / 2
    p90 = (1 + math.cos(th - phi - math.pi / 2)) / 2
    return ChannelReading(
        sym.pair, ChannelModel.RAMSEY_ZONES.value,
        ("fringe_at_phi", "fringe_at_phi_plus_90"),
        (_r(p0), _r(p90)),
        phase_sensitive=True,
        note="one fringe setting is ambiguous; scanning the relative "
             "phase over two settings resolves the sign")


def quadratic_zeeman(sym: PhaseSymbol) -> ChannelReading:
    """Model 5: quadratic projections cos^2(theta), sin^2(theta).

    NOT two independent channels: sin^2 = 1 - cos^2, so the pair carries
    exactly one quadratic number. The square discards the sign, and with
    it the difference between 240 and 300 degrees.
    """
    th = sym.radians
    return ChannelReading(
        sym.pair, ChannelModel.QUADRATIC_ZEEMAN.value,
        ("cos_squared", "sin_squared"),
        (_r(math.cos(th) ** 2), _r(math.sin(th) ** 2)),
        phase_sensitive=False,
        note="sin^2 = 1 - cos^2, so this is a single quadratic channel "
             "written twice; the sign of cos(theta) is not recoverable")


CHANNEL_MODELS = {
    ChannelModel.SIGNED_QUADRATURE: signed_quadrature,
    ChannelModel.ORTHOGONAL_FIELD_AXES: orthogonal_field_axes,
    ChannelModel.IQ_MICROWAVE: iq_microwave,
    ChannelModel.RAMSEY_ZONES: ramsey_zones,
    ChannelModel.QUADRATIC_ZEEMAN: quadratic_zeeman,
}


def _as_model(channel_model: ChannelModel | str) -> ChannelModel:
    if isinstance(channel_model, ChannelModel):
        return channel_model
    try:
        return ChannelModel(channel_model)
    except ValueError:
        raise PhaseAlphaError(
            f"unknown channel model {channel_model!r}; known models are "
            f"{', '.join(m.value for m in ChannelModel)}") from None


def read_channel(channel_model: ChannelModel | str,
                 sym: PhaseSymbol) -> ChannelReading:
    """Read one symbol through one channel model."""
    return CHANNEL_MODELS[_as_model(channel_model)](sym)


def quadratic_projections(sym: PhaseSymbol) -> tuple[float, float]:
    """(cos^2, sin^2) of the phase angle, rounded for comparison."""
    return quadratic_zeeman(sym).values


# --- the required negative result --------------------------------------

def quadratic_channel_degeneracy() -> dict:
    """The collision a single quadratic channel cannot avoid.

    cos^2(240) == cos^2(300) == 0.25, so symbols 23 and 56 are the same
    number on a quadratic channel. Four symbols in, three values out.
    """
    seen: dict[float, list[PhaseSymbol]] = {}
    for s in PHASE_ALPHABET_A:
        seen.setdefault(quadratic_projections(s)[0], []).append(s)
    collisions = [(v, group) for v, group in seen.items() if len(group) > 1]
    first_value, first_group = collisions[0]
    return {
        "colliding_pair": tuple(s.pair for s in first_group),
        "colliding_degrees": tuple(float(s.degrees) for s in first_group),
        "shared_cos_squared": first_value,
        "all_collisions": [
            {"cos_squared": v, "pairs": tuple(s.pair for s in g)}
            for v, g in collisions],
        "symbols_in": len(PHASE_ALPHABET_A),
        "distinct_values_out": len(seen),
        "cause": (
            "cos(240) = -1/2 and cos(300) = +1/2; squaring discards the "
            "sign, so both land on 0.25. sin^2 = 1 - cos^2 repeats the "
            "same collision, so pairing the two quadratic projections "
            "adds no information"),
        "verdict": "SINGLE_QUADRATIC_CHANNEL_INSUFFICIENT",
    }


def channel_values(channel_model: ChannelModel | str) -> list[tuple]:
    """The channel's readings for the whole alphabet, in order."""
    model = _as_model(channel_model)
    return [read_channel(model, s).values for s in PHASE_ALPHABET_A]


def symbols_recoverable(channel_model: ChannelModel | str) -> bool:
    """Does this channel model keep all four symbols distinguishable?

    Computed, not asserted: the readings are taken and counted. A single
    quadratic channel yields three values for four symbols, so False;
    any signed, phase-sensitive pair yields four, so True.
    """
    values = channel_values(channel_model)
    return len(set(values)) == len(PHASE_ALPHABET_A)


def recoverability_table() -> dict:
    return {m.value: symbols_recoverable(m) for m in ChannelModel}


def refuse_single_quadratic_channel(claim: str = "") -> None:
    """Refuse the claim that one quadratic channel preserves the alphabet.

    Raises unconditionally.
    """
    d = quadratic_channel_degeneracy()
    a, b = d["colliding_pair"]
    da, db = d["colliding_degrees"]
    said = f" Claim: {claim!r}." if claim else ""
    raise PhaseAlphaError(
        f"refusing the claim that all {d['symbols_in']} symbols survive "
        f"a single quadratic channel.{said} cos^2 maps {da} degrees "
        f"(symbol {a}) and {db} degrees (symbol {b}) to the same value "
        f"{d['shared_cos_squared']}, giving {d['distinct_values_out']} "
        f"distinct outputs for {d['symbols_in']} symbols. Pairing cos^2 "
        f"with sin^2 does not help, because sin^2 = 1 - cos^2. "
        f"Recovering the alphabet needs a signed, phase-sensitive "
        f"measurement.")


# --- report -------------------------------------------------------------

def phasealpha_report(verdict: str = VERDICT) -> dict:
    """One summary of what this module computes and, loudly, disclaims."""
    return {
        "alphabet": alphabet_table(),
        "on_15_degree_lattice": on_15_degree_lattice(),
        "sector_degrees": float(SECTOR_DEGREES),
        "sector_count": SECTOR_COUNT,
        "seven_halves": seven_halves_correspondence(),
        "quadratic_degeneracy": quadratic_channel_degeneracy(),
        "recoverability": recoverability_table(),
        "unit_discipline": {
            "units": [u.value for u in Unit],
            "omega_from_f": "omega = 2*pi*f",
            "f_from_omega": "f = omega/(2*pi)",
            "mixing_refused_by": "refuse_unit_confusion",
        },
        "evidence_class": EVIDENCE_CLASS,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "what_this_does_not_say": (
            "It does not say the four rationals are a code, that they "
            "were transmitted, or that anything physical selects them. "
            "It does not say the supplied 7/2 is the Cs-133 nuclear "
            "spin I = 7/2 -- the numerals match and the kinds of "
            "quantity do not, which is a CANDIDATE_CORRESPONDENCE and "
            "nothing stronger. It does not say any apparatus exists, "
            "that any channel was built, or that any symbol was ever "
            "read out; the channel models are arithmetic sketches, and "
            "the one firm result among them is negative -- a single "
            "quadratic channel cannot preserve all four symbols."),
        "verdict": verdict,
    }


__all__ = [
    "DEGREES_PER_TURN", "SECTOR_COUNT", "SECTOR_DEGREES", "TIMES_BASE",
    "PROJECTION_DECIMALS", "VERDICT", "EVIDENCE_CLASS", "MEASURED_HERE",
    "PHYSICAL_VALIDATION", "CANDIDATE_CORRESPONDENCE",
    "PhaseAlphaError",
    "Unit", "Quantity", "angular_frequency", "ordinary_frequency",
    "refuse_unit_confusion",
    "phase_mod_turn", "degrees_of", "sector_15deg", "times_192",
    "PhaseSymbol", "make_symbol", "PHASE_ALPHABET_A", "SYMBOLS_BY_PAIR",
    "symbol", "alphabet_table", "on_15_degree_lattice",
    "SEVEN_HALVES", "SEVEN_HALVES_MEANINGS", "seven_halves_correspondence",
    "refuse_spin_phase_conflation",
    "ChannelModel", "SINGLE_QUADRATIC_CHANNEL", "ChannelReading",
    "signed_quadrature", "orthogonal_field_axes", "iq_microwave",
    "ramsey_zones", "quadratic_zeeman", "CHANNEL_MODELS", "read_channel",
    "quadratic_projections", "quadratic_channel_degeneracy",
    "channel_values", "symbols_recoverable", "recoverability_table",
    "refuse_single_quadratic_channel",
    "phasealpha_report",
]
