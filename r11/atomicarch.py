"""P09 — atomic-clock architecture: Rabi, Ramsey, maser, quartz flywheel.

The lore around this project keeps reaching for "the atomic clock" as if
naming it explained a mechanism. It does not. What an atomic frequency
standard actually is, is a **functional chain**: a source of atoms, a
magnetic state selector, one or two interaction regions with an applied
field, a free-evolution drift, an analyzer, a detector, an error signal,
a servo, and a **flywheel** that carries the phase between corrections.
This module builds that chain as a typed graph, implements the two pieces
of physics that make it work (Rabi flopping and the Ramsey separated
oscillatory field), models the hydrogen maser's specific error budget
from conventional literature, and refuses the two substitutions the lore
keeps trying to make.

**A quartz STORAGE BULB is not a quartz OSCILLATOR.** In a hydrogen
maser the atoms are confined in a fused-quartz bulb whose inner wall is
coated with Teflon, so that a hydrogen atom can bounce many thousands of
times without its hyperfine phase being destroyed. That bulb is a
*container*: its job is long confinement with a small, slowly varying
wall shift. A quartz *oscillator* is a completely different object -- a
piezoelectric resonator, cut and electroded, driven by a sustaining
amplifier, that produces a frequency of its own as the servo's flywheel.
Same material, different physics, different position in the chain. The
bulb stores atoms; the oscillator stores phase.
:func:`refuse_bulb_as_oscillator` refuses to let one stand in for the
other.

**Two macroscopic coils do NOT duplicate atomic state-selection
magnets.** A state selector is a strong multipole (six-pole, in the
maser) whose *field gradient* exerts a state-dependent force and sorts
the atoms spatially by their quantum state before they ever reach the
cavity. A pair of coils -- Helmholtz or otherwise -- produces a
deliberately *uniform* field over its working volume; uniformity is the
whole design goal, and a uniform field exerts no sorting force at all.
Adding a second coil does not manufacture a multipole gradient, a
beam-defining geometry, or a state-selected population.
:func:`refuse_coils_as_state_selector` refuses that equation.

**The physics is real and testable.** :func:`rabi_probability` gives the
generalized (detuned) Rabi formula, so a pi-pulse on resonance inverts
the population and any detuning caps the achievable peak below one.
:func:`ramsey_fringe` gives the two-pulse interference pattern, and
:func:`ramsey_central_fringe_width` *measures* its width numerically
from a sweep: the width falls like ``1/T`` in the free-evolution time.
That is the whole reason Ramsey's separated-field method beats a single
long Rabi pulse. :func:`cavity_pulling` gives the standard first-order
pull of the oscillation frequency toward the cavity resonance.

Nothing here is measured. Every maser number is either an analytic model
or a conventional literature value, carried as such. The default verdict
is ``ATOMIC_ARCHITECTURE_MODEL_ONLY``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum

import numpy as np

DEFAULT_VERDICT = "ATOMIC_ARCHITECTURE_MODEL_ONLY"
EVIDENCE_CLASS = "CONVENTIONAL_LITERATURE"
ANALYTIC = "ANALYTIC_MODEL"
LITERATURE = "CONVENTIONAL_LITERATURE"
NOT_MEASURED = "NOT_MEASURED_HERE"

#: The hydrogen ground-state hyperfine transition, as a CONVENTIONAL
#: LITERATURE value (the 21 cm line). Quoted, never measured here.
H_HYPERFINE_HZ: float = 1_420_405_751.768

#: Public references. Conventional metrology/physics literature, not
#: project results and not source-corpus claims.
PRIMARY_SOURCES: tuple[str, ...] = (
    "I. I. Rabi et al., the molecular-beam magnetic-resonance method "
    "(resonance in a single oscillating-field region)",
    "N. F. Ramsey, the separated oscillatory fields method (two "
    "interaction regions with free evolution between them)",
    "H. M. Goldenberg, D. Kleppner and N. F. Ramsey, the atomic hydrogen "
    "maser (six-pole state focuser, coated storage bulb, tuned cavity)",
    "D. Kleppner et al., hydrogen-maser systematics: wall shift, "
    "magnetic inhomogeneity, cavity pulling, Doppler and transient terms",
    "IEEE Std 1139: definitions of physical quantities for fundamental "
    "frequency and time metrology",
)


class AtomicArchError(ValueError):
    """Raised when an atomic-clock architecture claim is misrepresented."""


# --- the functional graph -----------------------------------------------

class Stage(Enum):
    """A typed node in the atomic-standard functional chain."""

    SOURCE = "source"
    STATE_SELECTOR_MAGNET = "state_selector_magnet"
    FIRST_INTERACTION_REGION = "first_interaction_region"
    FREE_EVOLUTION = "free_evolution"
    SECOND_INTERACTION_REGION = "second_interaction_region"
    ANALYZER_MAGNET = "analyzer_magnet"
    DETECTOR = "detector"
    ERROR_SIGNAL = "error_signal"
    SERVO = "servo"
    FLYWHEEL = "flywheel"


class FlywheelKind(Enum):
    """What carries the phase between servo corrections.

    A *quartz oscillator* is a piezoelectric frequency reference that is
    steered by the servo. A *self-oscillating maser cavity* needs no
    external flywheel at all: above threshold the ensemble sustains the
    oscillation itself. Both are flywheels; neither is a storage bulb.
    """

    QUARTZ_OSCILLATOR = "quartz_oscillator"
    SELF_OSCILLATING_MASER_CAVITY = "self_oscillating_maser_cavity"


#: The canonical ordered chain. Order is load-bearing: state selection
#: must precede interaction, interaction must precede analysis, and the
#: servo cannot act before there is an error signal to act on.
CANONICAL_CHAIN: tuple[Stage, ...] = (
    Stage.SOURCE,
    Stage.STATE_SELECTOR_MAGNET,
    Stage.FIRST_INTERACTION_REGION,
    Stage.FREE_EVOLUTION,
    Stage.SECOND_INTERACTION_REGION,
    Stage.ANALYZER_MAGNET,
    Stage.DETECTOR,
    Stage.ERROR_SIGNAL,
    Stage.SERVO,
    Stage.FLYWHEEL,
)

#: What each node does, in one line. Descriptions, not measurements.
STAGE_ROLES: dict[Stage, str] = {
    Stage.SOURCE:
        "produces the atoms (beam oven or dissociator); no state "
        "selection has happened yet",
    Stage.STATE_SELECTOR_MAGNET:
        "a MULTIPOLE FIELD GRADIENT that sorts atoms spatially by "
        "quantum state; a uniform field cannot do this",
    Stage.FIRST_INTERACTION_REGION:
        "the first applied-field region; a pi/2 pulse puts the atom in "
        "a superposition",
    Stage.FREE_EVOLUTION:
        "the atom evolves with no applied field for a time T; the "
        "accumulated phase is delta*T",
    Stage.SECOND_INTERACTION_REGION:
        "the second pi/2 pulse, phase-coherent with the first; it "
        "converts accumulated phase into population",
    Stage.ANALYZER_MAGNET:
        "sorts the output states so the detector sees a "
        "state-dependent signal",
    Stage.DETECTOR:
        "counts atoms (or reads the emitted field) to give the fringe "
        "amplitude",
    Stage.ERROR_SIGNAL:
        "the discriminant derived from the fringe: how far the drive "
        "sits from line centre, with sign",
    Stage.SERVO:
        "the loop that steers the flywheel to null the error signal",
    Stage.FLYWHEEL:
        "carries phase between corrections: a quartz OSCILLATOR, or a "
        "self-oscillating maser cavity",
}


@dataclass(frozen=True)
class FunctionalGraph:
    """A typed node list with ordered edges. Nodes are :class:`Stage`."""

    nodes: tuple[Stage, ...]
    edges: tuple[tuple[Stage, Stage], ...]
    flywheel_kind: FlywheelKind
    evidence_class: str = ANALYTIC
    measured_here: str = "nothing"

    def __iter__(self):
        return iter(self.nodes)

    def __len__(self) -> int:
        return len(self.nodes)

    def __getitem__(self, i):
        return self.nodes[i]

    def role(self, stage: Stage) -> str:
        return STAGE_ROLES[stage]

    def is_connected(self) -> bool:
        """Every consecutive pair of nodes has an edge, in order."""
        if len(self.nodes) < 2:
            return False
        expected = tuple(zip(self.nodes, self.nodes[1:]))
        return self.edges == expected


def build_graph(flywheel: FlywheelKind = FlywheelKind.QUARTZ_OSCILLATOR
                ) -> FunctionalGraph:
    """Build the canonical ordered chain with its ordered edges."""
    if not isinstance(flywheel, FlywheelKind):
        raise AtomicArchError(
            "flywheel must be a FlywheelKind (a quartz OSCILLATOR or a "
            "self-oscillating maser cavity)")
    nodes = CANONICAL_CHAIN
    edges = tuple(zip(nodes, nodes[1:]))
    return FunctionalGraph(nodes=nodes, edges=edges, flywheel_kind=flywheel)


def refuse_invalid_chain(chain) -> None:
    """Validate a chain; refuse a missing, duplicated or reordered stage.

    Returns ``None`` for the canonical chain and raises
    :class:`AtomicArchError` for anything else. The order is physics, not
    bookkeeping: an analyzer before the interaction region measures a
    state that has not been prepared, and a servo before the error signal
    has nothing to steer on.
    """
    try:
        given = tuple(chain)
    except TypeError as exc:                       # not iterable at all
        raise AtomicArchError(
            "a functional chain must be an ordered sequence of Stage "
            "nodes") from exc
    bad = [n for n in given if not isinstance(n, Stage)]
    if bad:
        raise AtomicArchError(
            f"chain contains non-Stage nodes: {bad!r}; nodes are typed")
    missing = [s for s in CANONICAL_CHAIN if s not in given]
    if missing:
        raise AtomicArchError(
            f"chain is missing required stage(s): "
            f"{[s.value for s in missing]}. A standard without a state "
            f"selector, an interaction region, an error signal or a "
            f"flywheel is not a standard -- it is a subset with the "
            f"load-bearing part removed")
    if len(given) != len(set(given)):
        raise AtomicArchError(
            "chain repeats a stage; each functional node appears once "
            "(the two interaction regions are distinct typed nodes)")
    extra = [n for n in given if n not in CANONICAL_CHAIN]
    if extra:
        raise AtomicArchError(
            f"chain contains unknown stage(s): {[n for n in extra]!r}")
    if given != CANONICAL_CHAIN:
        first = next(i for i, (a, b) in enumerate(zip(given, CANONICAL_CHAIN))
                     if a is not b)
        raise AtomicArchError(
            f"chain is out of order at position {first}: found "
            f"{given[first].value!r} where {CANONICAL_CHAIN[first].value!r} "
            f"is required. State selection precedes interaction, "
            f"interaction precedes analysis, and the servo cannot act "
            f"before an error signal exists")
    return None


# --- Rabi ---------------------------------------------------------------

def rabi_probability(omega_rabi: float, t: float,
                     detuning: float = 0.0) -> float:
    """Generalized Rabi transition probability.

    On resonance (``detuning == 0``)::

        P(t) = sin^2(Omega t / 2)

    and in general, with ``Omega_eff = sqrt(Omega^2 + delta^2)``::

        P(t) = (Omega^2 / Omega_eff^2) * sin^2(Omega_eff t / 2)

    ``omega_rabi`` and ``detuning`` are angular frequencies (rad/s); ``t``
    is a time in seconds. The prefactor is why detuning caps the
    achievable population transfer: no pulse length recovers it.
    """
    if omega_rabi < 0:
        raise AtomicArchError("the Rabi rate Omega must be non-negative")
    if t < 0:
        raise AtomicArchError("pulse duration t must be non-negative")
    omega_eff_sq = omega_rabi * omega_rabi + detuning * detuning
    if omega_eff_sq == 0.0:
        return 0.0                                  # no drive, no transfer
    omega_eff = math.sqrt(omega_eff_sq)
    s = math.sin(0.5 * omega_eff * t)
    return (omega_rabi * omega_rabi / omega_eff_sq) * s * s


def rabi_peak_probability(omega_rabi: float, detuning: float = 0.0) -> float:
    """The maximum of :func:`rabi_probability` over all pulse durations.

    ``Omega^2 / (Omega^2 + delta^2)`` -- exactly 1 on resonance, strictly
    less than 1 for any non-zero detuning.
    """
    if omega_rabi < 0:
        raise AtomicArchError("the Rabi rate Omega must be non-negative")
    denom = omega_rabi * omega_rabi + detuning * detuning
    if denom == 0.0:
        return 0.0
    return omega_rabi * omega_rabi / denom


def pi_pulse_duration(omega_rabi: float) -> float:
    """The on-resonance pulse length that inverts the population."""
    if omega_rabi <= 0:
        raise AtomicArchError(
            "a pi-pulse needs a positive Rabi rate; with no drive there "
            "is no pulse area")
    return math.pi / omega_rabi


def half_pi_pulse_duration(omega_rabi: float) -> float:
    """The on-resonance pulse length used for each Ramsey interaction."""
    return 0.5 * pi_pulse_duration(omega_rabi)


def rabi_sweep(omega_rabi: float, times, detuning: float = 0.0) -> np.ndarray:
    """``P(t)`` over a sequence of pulse durations."""
    return np.array([rabi_probability(omega_rabi, float(t), detuning)
                     for t in np.asarray(times, dtype=float)])


# --- Ramsey -------------------------------------------------------------

def ramsey_fringe(detuning: float, free_evolution_T: float,
                  phi: float = 0.0) -> float:
    """Ramsey fringe from two pi/2 pulses separated by ``T``.

    ``P(delta) = 0.5 * (1 + cos(delta*T + phi))`` (sign/phase convention
    absorbed into ``phi``). The fringe period in ``delta`` is ``2*pi/T``,
    so the pattern narrows as the free-evolution time grows. That is the
    entire advantage of separated oscillatory fields over a single Rabi
    pulse: the linewidth is set by how long the atom is left alone, not
    by how long the field is applied.
    """
    if free_evolution_T <= 0:
        raise AtomicArchError(
            "the free-evolution time T must be positive; with T = 0 the "
            "two pulses merge and there is no Ramsey fringe")
    return 0.5 * (1.0 + math.cos(detuning * free_evolution_T + phi))


def ramsey_sweep(detunings, free_evolution_T: float,
                 phi: float = 0.0) -> np.ndarray:
    """``P(delta)`` over a sequence of detunings."""
    return np.array([ramsey_fringe(float(d), free_evolution_T, phi)
                     for d in np.asarray(detunings, dtype=float)])


def ramsey_fringe_period(free_evolution_T: float) -> float:
    """Analytic fringe period in detuning: ``2*pi/T``."""
    if free_evolution_T <= 0:
        raise AtomicArchError("the free-evolution time T must be positive")
    return 2.0 * math.pi / free_evolution_T


def ramsey_central_fringe_width(free_evolution_T: float,
                                n_points: int = 40_001) -> float:
    """MEASURE the central fringe's full width at half maximum.

    Not an algebraic restatement: this sweeps ``P(delta)`` on a fine grid
    from the ``delta = 0`` maximum outwards, finds the first crossing of
    the half-maximum level by linear interpolation, and doubles it. For
    the ideal fringe the answer is ``pi/T``, which the sweep recovers.
    """
    if free_evolution_T <= 0:
        raise AtomicArchError("the free-evolution time T must be positive")
    if n_points < 3:
        raise AtomicArchError("need at least 3 sweep points")
    span = ramsey_fringe_period(free_evolution_T) / 2.0    # to the first null
    deltas = np.linspace(0.0, span, n_points)
    p = ramsey_sweep(deltas, free_evolution_T)
    below = np.nonzero(p <= 0.5)[0]
    if below.size == 0:
        raise AtomicArchError(
            "the sweep never reached half maximum; widen the span")
    k = int(below[0])
    if k == 0:
        return 0.0
    p_hi, p_lo = p[k - 1], p[k]
    d_hi, d_lo = deltas[k - 1], deltas[k]
    if p_hi == p_lo:
        half = float(d_lo)
    else:
        half = float(d_hi + (p_hi - 0.5) * (d_lo - d_hi) / (p_hi - p_lo))
    return 2.0 * half


# --- cavity pulling -----------------------------------------------------

def cavity_pulling(f_atomic: float, f_cavity: float,
                   Q_cavity: float, Q_line: float) -> float:
    """First-order cavity pulling of the oscillation frequency.

    ``f_out = f_atomic + (Q_cavity / Q_line) * (f_cavity - f_atomic)``

    The oscillation is dragged toward the cavity resonance in proportion
    to the ratio of the cavity's loaded Q to the atomic line Q. It
    vanishes exactly when the cavity is tuned to the atomic line, which
    is why a maser's cavity is servoed and why cavity pulling is one of
    the named terms in its error budget.
    """
    if Q_line <= 0:
        raise AtomicArchError(
            "the atomic line Q must be positive; without a linewidth "
            "there is no pulling ratio to form")
    if Q_cavity < 0:
        raise AtomicArchError("the cavity Q must be non-negative")
    return f_atomic + (Q_cavity / Q_line) * (f_cavity - f_atomic)


# --- the hydrogen maser -------------------------------------------------

#: The named systematic terms in a hydrogen-maser error budget. Naming
#: them is the point: an undeclared term is a hidden one.
MASER_ERROR_TERM_NAMES: tuple[str, ...] = (
    "wall_shift",
    "magnetic_inhomogeneity",
    "cavity_pulling",
    "doppler_first_order",
    "doppler_second_order",
    "transient_response",
)


@dataclass(frozen=True)
class MaserErrorTerm:
    """One named systematic, with whether it has been declared."""

    name: str
    description: str
    declared: bool
    status: str = NOT_MEASURED
    evidence_class: str = LITERATURE

    def __post_init__(self) -> None:
        if not self.name:
            raise AtomicArchError("an error term needs a name")
        if not self.description:
            raise AtomicArchError(
                f"{self.name}: an error term needs a description; a bare "
                f"label is not a budget entry")


def default_maser_error_terms() -> tuple[MaserErrorTerm, ...]:
    """The six named terms, all declared, none measured."""
    return (
        MaserErrorTerm(
            "wall_shift",
            "phase shift per collision with the Teflon-coated quartz "
            "storage bulb wall, scaling with bulb surface-to-volume and "
            "with temperature; the maser's characteristic systematic",
            True),
        MaserErrorTerm(
            "magnetic_inhomogeneity",
            "second-order Zeeman shift plus a spatial average over an "
            "imperfectly uniform C-field across the bulb volume",
            True),
        MaserErrorTerm(
            "cavity_pulling",
            "the oscillation is pulled toward the cavity resonance by "
            "(Q_cavity / Q_line) * (f_cavity - f_atomic)",
            True),
        MaserErrorTerm(
            "doppler_first_order",
            "first-order Doppler, suppressed to first order by confining "
            "the atoms in a bulb small compared with the wavelength "
            "(Dicke narrowing), not eliminated by assumption",
            True),
        MaserErrorTerm(
            "doppler_second_order",
            "relativistic time dilation, set by the mean-square atomic "
            "velocity and therefore by the bulb temperature",
            True),
        MaserErrorTerm(
            "transient_response",
            "settling of the oscillation after a step in flux, cavity "
            "tuning or temperature; a transient is not a steady-state "
            "frequency",
            True),
    )


@dataclass(frozen=True)
class MaserErrorBudget:
    """The named systematics of a hydrogen maser, each flagged.

    Construction refuses a budget that omits any of the six named terms:
    a budget that does not list wall shift, magnetic inhomogeneity,
    cavity pulling, both Doppler orders and the transient response is not
    a maser error budget.
    """

    terms: tuple[MaserErrorTerm, ...] = field(
        default_factory=default_maser_error_terms)
    evidence_class: str = LITERATURE
    measured_here: str = "nothing"

    def __post_init__(self) -> None:
        names = [t.name for t in self.terms]
        missing = [n for n in MASER_ERROR_TERM_NAMES if n not in names]
        if missing:
            raise AtomicArchError(
                f"maser error budget omits named term(s): {missing}. Every "
                f"named systematic is listed, declared or not; an omitted "
                f"term is a hidden one")
        if len(names) != len(set(names)):
            raise AtomicArchError("maser error budget repeats a term name")

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(t.name for t in self.terms)

    def undeclared(self) -> tuple[str, ...]:
        """Names of terms that are listed but NOT declared."""
        return tuple(t.name for t in self.terms if not t.declared)

    def all_declared(self) -> bool:
        return not self.undeclared()

    def flags(self) -> dict:
        return {t.name: {"declared": t.declared, "status": t.status,
                         "evidence_class": t.evidence_class}
                for t in self.terms}


@dataclass(frozen=True)
class HydrogenMaserModel:
    """The maser's distinguishing parts, as typed fields.

    Every value is an ``ANALYTIC_MODEL`` description or a
    ``CONVENTIONAL_LITERATURE`` quotation. None of it is measured here.
    """

    state_focuser: str = (
        "six-pole (hexapole) magnetic state focuser: a MULTIPOLE FIELD "
        "GRADIENT that focuses the upper hyperfine state into the bulb "
        "and rejects the lower")
    storage_bulb: str = (
        "fused-quartz STORAGE BULB with a Teflon (FEP/PTFE) inner "
        "coating: a CONTAINER for atoms, allowing many thousands of "
        "wall collisions with small phase loss")
    storage_bulb_is_a_quartz_oscillator: bool = False
    cavity: str = (
        "tuned RF cavity resonant at the hyperfine transition, servoed "
        "because its detuning pulls the oscillation frequency")
    interaction_time_regime: str = (
        "LONG: the interaction time is set by confinement in the bulb "
        "(order of a second), not by transit through a beam region")
    linewidth_regime: str = (
        "narrow: linewidth ~ 1/(pi * T2), with T2 limited by wall "
        "relaxation, spin exchange and bulb escape")
    transition_reference_hz: float = H_HYPERFINE_HZ
    transition_evidence_class: str = LITERATURE
    flywheel_kind: FlywheelKind = FlywheelKind.SELF_OSCILLATING_MASER_CAVITY
    error_budget: MaserErrorBudget = field(default_factory=MaserErrorBudget)
    evidence_class: str = LITERATURE
    measured_here: str = "nothing"
    status: str = NOT_MEASURED


HYDROGEN_MASER = HydrogenMaserModel()


# --- load-bearing refusals ----------------------------------------------

def refuse_bulb_as_oscillator(component: str = "quartz storage bulb",
                              claimed_role: str = "frequency reference"
                              ) -> None:
    """A quartz STORAGE BULB is not a quartz OSCILLATOR.

    The bulb is a coated container whose function is long atomic
    confinement with a small wall shift; it has no piezoelectric drive,
    no electrodes, no sustaining amplifier, and produces no frequency of
    its own. The oscillator is a piezoelectric resonator that the servo
    steers. Sharing the word "quartz" is a material coincidence, not a
    functional identity.
    """
    raise AtomicArchError(
        f"{component!r} cannot be read as {claimed_role!r}: a quartz "
        f"STORAGE BULB is a Teflon-coated CONTAINER that holds atoms for "
        f"a long coherent interaction time, contributing a WALL SHIFT to "
        f"the error budget. A quartz OSCILLATOR is a piezoelectric "
        f"resonator with electrodes and a sustaining amplifier that acts "
        f"as the servo's FLYWHEEL. Different mechanism, different node in "
        f"the chain (storage vs. FLYWHEEL). The shared material does not "
        f"transfer the function.")


def refuse_coils_as_state_selector(n_coils: int = 2,
                                   geometry: str = "macroscopic coil pair"
                                   ) -> None:
    """Two macroscopic coils do not duplicate a state-selection magnet.

    A state selector is a strong multipole whose *gradient* applies a
    state-dependent force and sorts atoms spatially before the
    interaction region. A coil pair is designed for field *uniformity*;
    a uniform field applies no sorting force, and counting coils does not
    create a multipole.
    """
    raise AtomicArchError(
        f"{n_coils} coils in a {geometry} do NOT duplicate an atomic "
        f"state-selection magnet. State selection needs a MULTIPOLE FIELD "
        f"GRADIENT (six-pole in a hydrogen maser) that exerts a "
        f"state-dependent force and spatially sorts quantum states, plus "
        f"a beam geometry and an aperture that discard the rejected "
        f"state. A macroscopic coil pair is built for field UNIFORMITY, "
        f"and a uniform field exerts no sorting force at all. Adding "
        f"coils changes the field's shape, not its category: no "
        f"state-selected population is produced, so "
        f"{Stage.STATE_SELECTOR_MAGNET.value} is not satisfied.")


def refuse_measured_claim(quantity: str = "any value in this module") -> None:
    """Nothing in this module is measured."""
    raise AtomicArchError(
        f"{quantity!r} is not measured here. Every number in this module "
        f"is either an ANALYTIC_MODEL evaluation (Rabi, Ramsey, cavity "
        f"pulling) or a CONVENTIONAL_LITERATURE quotation (the hydrogen "
        f"hyperfine reference, the named systematics). No atoms are "
        f"prepared, no cavity is tuned, no fringe is recorded and no "
        f"frequency is compared against a standard. "
        f"PHYSICAL_VALIDATION_NOT_CLAIMED.")


# --- the neutral crystal analogue ---------------------------------------

#: Where the analogy stops. Stated up front, not buried.
CRYSTAL_ANALOGUE_FAILURE_BOUNDARIES: tuple[str, ...] = (
    "it does not claim atomic state selection: a two-channel drive has "
    "no multipole gradient and sorts no quantum states",
    "it does not claim a coherence time: the model has no relaxation "
    "mechanism, no T1, no T2 and no wall-collision physics",
    "it does not claim clock performance: no accuracy, no stability, no "
    "Allan deviation and no frequency uncertainty follow from it",
    "it does not claim a hyperfine transition, a population inversion or "
    "maser action of any kind",
    "it is an analogy for SIGNAL STRUCTURE ONLY -- how two coherent "
    "channels combine -- and a structural resemblance is not a "
    "mechanism",
    "no crystal, material, device or specimen is measured, identified "
    "or implicated",
)


def crystal_analogue(channel_relation: str = "orthogonal",
                     phase_offset: float = 0.0) -> dict:
    """A neutral two-channel drive model, with explicit failure boundaries.

    Two drives are applied to one element. If they are ``"orthogonal"``
    the powers add and the combined amplitude goes like
    ``sqrt(a^2 + b^2)``; if they are ``"phase_coherent"`` the amplitudes
    add with a relative phase, giving
    ``sqrt(a^2 + b^2 + 2ab cos(phi))``. That is all this says. It is an
    ANALOGY for signal structure, offered because the arithmetic is
    unambiguous, and it is bounded by
    :data:`CRYSTAL_ANALOGUE_FAILURE_BOUNDARIES`.
    """
    if channel_relation not in ("orthogonal", "phase_coherent"):
        raise AtomicArchError(
            "channel_relation must be 'orthogonal' or 'phase_coherent'; "
            "an unspecified relation has no combining rule")
    a = b = 1.0
    if channel_relation == "orthogonal":
        amplitude = math.sqrt(a * a + b * b)
        rule = "sqrt(a^2 + b^2)  (powers add; no interference term)"
    else:
        amplitude = math.sqrt(
            a * a + b * b + 2.0 * a * b * math.cos(phase_offset))
        rule = "sqrt(a^2 + b^2 + 2ab cos(phi))  (amplitudes interfere)"
    return {
        "what_this_is": (
            "a neutral two-channel drive model: two coherent inputs to a "
            "single element, combined by a stated rule"),
        "channel_relation": channel_relation,
        "phase_offset_rad": phase_offset,
        "combining_rule": rule,
        "combined_amplitude_unit_inputs": amplitude,
        "evidence_class": "ANALOGY_ONLY",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "claims_atomic_state_selection": False,
        "claims_coherence_time": False,
        "claims_clock_performance": False,
        "failure_boundaries": list(CRYSTAL_ANALOGUE_FAILURE_BOUNDARIES),
        "verdict": "ANALOGY_ONLY_NO_MECHANISM_CLAIMED",
    }


# --- report -------------------------------------------------------------

def atomicarch_report() -> dict:
    graph = build_graph()
    budget = HYDROGEN_MASER.error_budget
    return {
        "what_this_is": (
            "the functional architecture of an atomic frequency standard "
            "as a typed graph, with the Rabi and Ramsey physics that "
            "make it work, a hydrogen-maser error budget from "
            "conventional literature, and a neutral two-channel analogy "
            "with stated failure boundaries"),
        "chain": [s.value for s in graph.nodes],
        "edges": [[a.value, b.value] for a, b in graph.edges],
        "chain_connected": graph.is_connected(),
        "stage_roles": {s.value: STAGE_ROLES[s] for s in graph.nodes},
        "flywheel_kinds": [k.value for k in FlywheelKind],
        "hydrogen_maser": {
            "state_focuser": HYDROGEN_MASER.state_focuser,
            "storage_bulb": HYDROGEN_MASER.storage_bulb,
            "storage_bulb_is_a_quartz_oscillator":
                HYDROGEN_MASER.storage_bulb_is_a_quartz_oscillator,
            "cavity": HYDROGEN_MASER.cavity,
            "interaction_time_regime":
                HYDROGEN_MASER.interaction_time_regime,
            "linewidth_regime": HYDROGEN_MASER.linewidth_regime,
            "transition_reference_hz":
                HYDROGEN_MASER.transition_reference_hz,
            "transition_evidence_class":
                HYDROGEN_MASER.transition_evidence_class,
            "flywheel_kind": HYDROGEN_MASER.flywheel_kind.value,
            "status": HYDROGEN_MASER.status,
        },
        "maser_error_budget": {
            "named_terms": list(MASER_ERROR_TERM_NAMES),
            "listed": list(budget.names),
            "flags": budget.flags(),
            "undeclared": list(budget.undeclared()),
            "all_declared": budget.all_declared(),
        },
        "crystal_analogue": crystal_analogue(),
        "distinctions_enforced": [
            "a quartz STORAGE BULB (a Teflon-coated container for atoms, "
            "contributing a wall shift) is NOT a quartz OSCILLATOR (a "
            "piezoelectric frequency reference acting as the servo's "
            "flywheel) -- refuse_bulb_as_oscillator",
            "two macroscopic coils do NOT duplicate an atomic "
            "state-selection magnet: state selection needs a multipole "
            "field GRADIENT that spatially sorts quantum states, and a "
            "coil pair is built for field uniformity -- "
            "refuse_coils_as_state_selector",
            "nothing here is measured -- refuse_measured_claim",
            "the chain order is physics: state selection before "
            "interaction, interaction before analysis, error signal "
            "before servo -- refuse_invalid_chain",
        ],
        "primary_sources": list(PRIMARY_SOURCES),
        "verdict": DEFAULT_VERDICT,
        "evidence_class": EVIDENCE_CLASS,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "what_this_does_not_say": (
            "It does not build, tune, run or measure any clock. It does "
            "not claim a frequency, a linewidth, a coherence time, a wall "
            "shift, an Allan deviation or an uncertainty budget for any "
            "real hardware. The Rabi and Ramsey results are analytic "
            "model evaluations; the hydrogen-maser parts and systematics "
            "are conventional literature descriptions. It does not say "
            "that a quartz storage bulb is a quartz oscillator, that two "
            "coils constitute a state-selection magnet, or that the "
            "neutral two-channel analogy implies atomic state selection, "
            "a coherence time or any clock performance. "
            "PHYSICAL_VALIDATION_NOT_CLAIMED."),
    }
