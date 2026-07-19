"""P17 — the quantum heat-engine energy ledger and the energy ontology.

The claim this module exists to block is a substitution, and it is
almost always made in one step:

    "there is energy in the reservoir"  ->  "energy can be extracted"

Both halves can be true and the arrow between them is still false.
A litre of seawater at 290 K contains of order 10^11 J of internal
energy relative to absolute zero. None of it is available to a ship
floating in 290 K seawater, because availability is not a property of
an energy quantity -- it is a property of a *pair* of reservoirs at
different temperatures. The Kelvin-Planck statement of the second law
says exactly this: no cyclic process takes heat from a single
reservoir and converts it entirely into work.

The same substitution appears in resonator and vacuum-energy claims,
where "the zero-point field has enormous energy density" is offered as
if it were "the zero-point field can drive something". It cannot, for
the ordinary reason: the ground state is the ground state, there is no
lower state to relax into, and a Casimir force is a force and not a
fuel.

So this module makes the five quantities involved into five distinct
*types*::

    HEAT               energy in transit across a boundary by
                       temperature difference
    WORK               energy in transit that could, in principle,
                       raise a weight
    RESERVOIR_ENERGY   energy resident in a thermal bath; a state
                       quantity, not a transit quantity
    STORED_ENERGY      energy resident in a system's own degrees of
                       freedom (a compressed spring, a charged
                       capacitor, a driven mode)
    DISSIPATION        energy that has left the work channel
                       irreversibly

These cannot be added with ``+``. Attempting it raises
``EnergyCategoryError``. There is exactly one licensed cross-category
operation, ``first_law_residual``, and it must be called by name with
each term labelled, so that a category crossing is always a visible
line of code rather than an accident of arithmetic.

All ledger arithmetic uses ``fractions.Fraction``. The first-law
balance is checked for *exact* equality, not to a tolerance, because a
tolerance is where a small unexplained term hides. If a fixture does
not balance exactly, the residual is reported as an exact rational
rather than absorbed.

Nothing here is a measurement. This programme owns no heat engine, no
calorimeter and no cryostat. The literature engine table records what
other groups have published, with sources named, and is not used to
support any claim about this apparatus.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from fractions import Fraction
from typing import Iterable, Mapping

# --- the ontology -------------------------------------------------------


class EnergyKind(str, Enum):
    """The five energy categories, kept apart by construction.

    The split that matters most is HEAT/WORK (transit quantities,
    path-dependent) versus RESERVOIR_ENERGY/STORED_ENERGY (state
    quantities). Adding a state quantity to a transit quantity is the
    laundering step: it turns "how much is there" into "how much can
    be taken", which is precisely the inference the second law
    forbids.
    """

    HEAT = "HEAT"
    WORK = "WORK"
    RESERVOIR_ENERGY = "RESERVOIR_ENERGY"
    STORED_ENERGY = "STORED_ENERGY"
    DISSIPATION = "DISSIPATION"


#: Categories that describe energy *in transit* across a boundary.
#: Only these appear in a cycle's first-law balance.
TRANSIT_KINDS = frozenset({
    EnergyKind.HEAT, EnergyKind.WORK, EnergyKind.DISSIPATION})

#: Categories that describe energy *resident* in a system or bath.
#: A state quantity is never by itself evidence of availability.
STATE_KINDS = frozenset({
    EnergyKind.RESERVOIR_ENERGY, EnergyKind.STORED_ENERGY})


class EnergyCategoryError(TypeError):
    """Raised when two energy categories are combined illegitimately."""


class FirstLawViolation(ArithmeticError):
    """Raised when an energy ledger does not balance exactly."""


class CarnotBoundExceeded(ValueError):
    """Raised when a claimed efficiency exceeds the Carnot bound."""


class ExtractionRefused(RuntimeError):
    """Raised for a claim that reservoir energy is available as work."""


# --- literature constants, each with its provenance --------------------

#: Boltzmann constant, J/K. Exact by SI definition since the 2019
#: redefinition of the kelvin (CODATA; SI Brochure, 9th ed.).
BOLTZMANN_J_PER_K = 1.380_649e-23

#: Reduced Planck constant, J s. Derived from the exact SI value
#: h = 6.626_070_15e-34 J s divided by 2*pi (CODATA 2018/2022).
HBAR_J_S = 1.054_571_817e-34

#: Kelvin-Planck statement of the second law. Quoted in substance,
#: not verbatim; see e.g. Callen, *Thermodynamics and an Introduction
#: to Thermostatistics*, 2nd ed. (1985), ch. 4, or Zemansky & Dittman,
#: *Heat and Thermodynamics*, 7th ed., ch. 6.
KELVIN_PLANCK = (
    "No cyclic process exists whose sole result is the absorption of "
    "heat from a single reservoir and the conversion of that heat "
    "entirely into work. A single reservoir, however large its "
    "internal energy, yields zero work in a cycle."
)

#: Carnot's bound, 1 - Tc/Th, on the efficiency of any cyclic engine
#: operating between two thermal reservoirs. Carnot (1824),
#: *Reflexions sur la puissance motrice du feu*; modern statement in
#: any thermodynamics text.
CARNOT_SOURCE = (
    "Carnot (1824). The bound 1 - Tc/Th holds for any cyclic engine "
    "between two reservoirs in thermal equilibrium, independent of "
    "working substance, and holds for quantum working substances too."
)

#: The bound has a scope, and ignoring the scope is how "beyond
#: Carnot" headlines are generated. A *squeezed* thermal reservoir is
#: not a thermal reservoir: it carries a nonzero free-energy resource
#: beyond its temperature, so the standard two-temperature bound is
#: simply not the applicable bound. Klaers, Faelt, Imamoglu &
#: Togan, Phys. Rev. X 7, 031044 (2017) is the canonical example.
#: This is not a violation of the second law and was never claimed to
#: be one by its authors.
CARNOT_BOUND_SCOPE = (
    "1 - Tc/Th applies when both reservoirs are ordinary thermal "
    "states characterised by a temperature alone. Engines run against "
    "squeezed, coherent or otherwise non-thermal reservoirs can exceed "
    "it because the reservoir supplies a resource beyond its "
    "temperature; the generalised bound accounts for that resource. "
    "Exceeding the *standard* bound is evidence that the reservoir was "
    "not thermal, never that the second law failed."
)


# --- typed energy quantities -------------------------------------------


@dataclass(frozen=True)
class Energy:
    """A quantity of energy in joules, tagged with its category.

    ``joules`` is a ``Fraction`` so that a ledger balances exactly or
    reports an exact residual. Passing a float is accepted and
    converted exactly (``Fraction(float)`` is lossless), but a float
    literal such as ``0.1`` is not the decimal 0.1, so exact-balance
    fixtures should be built from integers and ``Fraction``.
    """

    kind: EnergyKind
    joules: Fraction
    label: str = ""
    #: Temperature of the bath this quantity is associated with, K.
    #: Required for RESERVOIR_ENERGY: a reservoir energy without a
    #: temperature cannot be assessed for availability at all, and an
    #: unassessable quantity is exactly what gets laundered.
    temperature_k: Fraction | None = None
    provenance: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", EnergyKind(self.kind))
        object.__setattr__(self, "joules", Fraction(self.joules))
        if self.temperature_k is not None:
            t = Fraction(self.temperature_k)
            if t <= 0:
                raise ValueError(
                    f"temperature must be positive kelvin, got {t}")
            object.__setattr__(self, "temperature_k", t)
        if self.joules < 0:
            raise ValueError(
                "energy quantities are non-negative magnitudes; "
                "direction is carried by the category and by which "
                "term of the balance it occupies, not by a sign")
        if (self.kind is EnergyKind.RESERVOIR_ENERGY
                and self.temperature_k is None):
            raise ValueError(
                "RESERVOIR_ENERGY requires temperature_k. Reservoir "
                "energy without a temperature cannot be tested for "
                "availability, and an untestable quantity is the one "
                "that gets treated as free.")

    # -- the load-bearing part: category-preserving arithmetic ----------

    def __add__(self, other: "Energy") -> "Energy":
        if not isinstance(other, Energy):
            return NotImplemented
        if other.kind is not self.kind:
            raise EnergyCategoryError(
                f"refusing to add {self.kind.value} to "
                f"{other.kind.value}. These are different physical "
                f"categories: a sum of them is not a quantity of "
                f"anything. If a genuine cross-category relation is "
                f"intended, state it explicitly with "
                f"first_law_residual().")
        return Energy(self.kind, self.joules + other.joules,
                      label=f"{self.label}+{other.label}".strip("+"),
                      temperature_k=(self.temperature_k
                                     if self.temperature_k
                                     == other.temperature_k else None),
                      provenance="sum")

    def __sub__(self, other: "Energy") -> "Energy":
        if not isinstance(other, Energy):
            return NotImplemented
        if other.kind is not self.kind:
            raise EnergyCategoryError(
                f"refusing to subtract {other.kind.value} from "
                f"{self.kind.value}: different physical categories")
        if other.joules > self.joules:
            raise ValueError("energy magnitudes cannot go negative")
        return Energy(self.kind, self.joules - other.joules,
                      temperature_k=self.temperature_k,
                      provenance="difference")

    def as_work(self) -> "Energy":
        """Assert that this quantity is work. Refuses if it is not.

        There is no conversion here and that is deliberate. This is a
        checked cast, so a call site that wants work from a reservoir
        has to say so and be refused, rather than quietly relabelling.
        """
        if self.kind is EnergyKind.WORK:
            return self
        raise EnergyCategoryError(
            f"{self.kind.value} is not WORK and cannot be relabelled "
            f"as WORK. For RESERVOIR_ENERGY the available fraction is "
            f"bounded by the Carnot factor against a colder sink; use "
            f"available_work_bound() and supply the sink temperature.")

    def is_state_quantity(self) -> bool:
        return self.kind in STATE_KINDS


def joules(kind: EnergyKind | str, numerator: int, denominator: int = 1,
           **kw) -> Energy:
    """Convenience constructor for an exact rational energy."""
    return Energy(EnergyKind(kind), Fraction(numerator, denominator), **kw)


def total(quantities: Iterable[Energy]) -> Energy:
    """Sum quantities of a single category. Refuses a mixed iterable."""
    qs = list(quantities)
    if not qs:
        raise ValueError("cannot total an empty set: the category "
                         "would be undetermined")
    out = qs[0]
    for q in qs[1:]:
        out = out + q
    return out


# --- the Carnot bound ---------------------------------------------------


def carnot_efficiency(t_cold_k: Fraction, t_hot_k: Fraction) -> Fraction:
    """Exact 1 - Tc/Th for two thermal reservoirs.

    Returns a ``Fraction``, so a bound comparison is never decided by
    a floating-point tie.
    """
    tc, th = Fraction(t_cold_k), Fraction(t_hot_k)
    if tc <= 0 or th <= 0:
        raise ValueError("reservoir temperatures must be positive kelvin")
    if tc > th:
        raise ValueError(
            f"cold reservoir {tc} K is hotter than the hot reservoir "
            f"{th} K; relabel them")
    return 1 - tc / th


def check_efficiency_claim(claimed: Fraction, t_cold_k: Fraction,
                           t_hot_k: Fraction, *,
                           reservoirs_are_thermal: bool = True) -> Fraction:
    """Refuse a claimed efficiency above the Carnot bound.

    ``reservoirs_are_thermal=False`` does not lift the refusal; it
    changes the message, because a super-Carnot number obtained
    against a non-thermal reservoir is a statement that the wrong
    bound was quoted, not that this bound was beaten
    (``CARNOT_BOUND_SCOPE``).
    """
    claimed = Fraction(claimed)
    if claimed < 0:
        raise ValueError("efficiency cannot be negative")
    bound = carnot_efficiency(t_cold_k, t_hot_k)
    if claimed > bound:
        if reservoirs_are_thermal:
            raise CarnotBoundExceeded(
                f"claimed efficiency {float(claimed):.6g} exceeds the "
                f"Carnot bound {float(bound):.6g} for Tc={t_cold_k} K, "
                f"Th={t_hot_k} K. {CARNOT_SOURCE}")
        raise CarnotBoundExceeded(
            f"claimed efficiency {float(claimed):.6g} exceeds "
            f"{float(bound):.6g}, but the reservoirs were declared "
            f"non-thermal, so 1 - Tc/Th is not the applicable bound "
            f"and no comparison here is meaningful. "
            f"{CARNOT_BOUND_SCOPE}")
    return bound


def available_work_bound(reservoir: Energy,
                         sink_temperature_k: Fraction) -> Energy:
    """The most work extractable from a reservoir against a sink.

    This is the only route from RESERVOIR_ENERGY to WORK in the
    module, and it requires a sink temperature as an argument, so the
    temperature difference can never be omitted by accident. When the
    sink is at the reservoir temperature the answer is exactly zero
    joules of work -- not a small number, zero -- which is the
    Kelvin-Planck statement expressed as a return value.
    """
    if reservoir.kind is not EnergyKind.RESERVOIR_ENERGY:
        raise EnergyCategoryError(
            f"available_work_bound() applies to RESERVOIR_ENERGY, not "
            f"{reservoir.kind.value}")
    assert reservoir.temperature_k is not None  # enforced in __post_init__
    tc = Fraction(sink_temperature_k)
    th = reservoir.temperature_k
    if tc <= 0:
        raise ValueError("sink temperature must be positive kelvin")
    if tc > th:
        raise ValueError(
            f"sink at {tc} K is hotter than the reservoir at {th} K; "
            f"heat flows the other way and this reservoir is the sink")
    eta = carnot_efficiency(tc, th)
    return Energy(
        EnergyKind.WORK, reservoir.joules * eta,
        label=f"upper bound on work from {reservoir.label or 'reservoir'}",
        provenance=(
            f"Carnot factor {eta} against a {tc} K sink; an upper "
            f"bound only, unattained by any real cycle"))


def refuse_extraction_without_gradient(reservoir: Energy,
                                       sink_temperature_k: Fraction
                                       ) -> None:
    """Refuse "there is energy in it, so energy can be taken out".

    Raises when reservoir and sink are at the same temperature, which
    is the isothermal case the claim always turns out to be.
    """
    if reservoir.kind is not EnergyKind.RESERVOIR_ENERGY:
        raise EnergyCategoryError(
            f"expected RESERVOIR_ENERGY, got {reservoir.kind.value}")
    assert reservoir.temperature_k is not None
    tc = Fraction(sink_temperature_k)
    if tc == reservoir.temperature_k:
        raise ExtractionRefused(
            f"the reservoir holds {float(reservoir.joules):.6g} J at "
            f"{reservoir.temperature_k} K and the sink is at the same "
            f"temperature, so the extractable work is exactly zero. "
            f"Energy being present is not energy being available: "
            f"availability is a property of a temperature *difference*, "
            f"not of an energy magnitude. {KELVIN_PLANCK}")


def refuse_vacuum_energy_as_source(*args, **kwargs):
    """Always refuses. Zero-point energy is not a fuel.

    Kept as a named function rather than a comment because the claim
    recurs in resonator contexts and deserves a call site that fails.
    """
    raise ExtractionRefused(
        "zero-point / vacuum energy is refused as an energy source. "
        "The zero-point energy is the energy of the ground state: "
        "there is no lower state for a system to relax into, so there "
        "is no cycle that nets work from it. Casimir and related "
        "effects are forces arising from boundary-dependent mode "
        "structure -- a force is not a fuel, and moving the boundaries "
        "back costs at least what was gained. Large vacuum energy "
        "densities quoted from field theory are state quantities in "
        "this module's ontology (RESERVOIR_ENERGY / STORED_ENERGY) and "
        "carry no availability claim whatsoever.")


# --- the first law, as the one licensed category crossing --------------


@dataclass(frozen=True)
class CycleLedger:
    """One complete cycle of an engine, term by term.

    Every term is typed, and the balance is stated once, explicitly::

        heat_in = work_out + heat_rejected + dissipation

    Over a complete cycle the working substance returns to its initial
    state, so its internal energy change is zero and the balance has
    no residual term to absorb error into. That is why the check can
    be exact.
    """

    label: str
    heat_in: Energy
    work_out: Energy
    heat_rejected: Energy
    dissipation: Energy
    t_hot_k: Fraction
    t_cold_k: Fraction
    provenance: str = ""
    notes: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        expect = {
            "heat_in": EnergyKind.HEAT,
            "work_out": EnergyKind.WORK,
            "heat_rejected": EnergyKind.HEAT,
            "dissipation": EnergyKind.DISSIPATION,
        }
        for name, kind in expect.items():
            q = getattr(self, name)
            if not isinstance(q, Energy):
                raise TypeError(f"{name} must be an Energy")
            if q.kind is not kind:
                raise EnergyCategoryError(
                    f"{name} must be {kind.value}, got {q.kind.value}. "
                    f"A cycle balance over transit quantities cannot "
                    f"take a state quantity as a term: that is the "
                    f"laundering step this ledger exists to block.")
        object.__setattr__(self, "t_hot_k", Fraction(self.t_hot_k))
        object.__setattr__(self, "t_cold_k", Fraction(self.t_cold_k))
        if not 0 < self.t_cold_k <= self.t_hot_k:
            raise ValueError("require 0 < t_cold_k <= t_hot_k")

    # -- balance --------------------------------------------------------

    def first_law_residual(self) -> Fraction:
        """heat_in - (work_out + heat_rejected + dissipation), exact.

        The single licensed crossing between energy categories in this
        module. It is a function with a name, not an operator, so that
        every crossing is greppable.
        """
        return (self.heat_in.joules
                - self.work_out.joules
                - self.heat_rejected.joules
                - self.dissipation.joules)

    def check_first_law(self) -> Fraction:
        """Raise unless the cycle balances to exactly zero."""
        r = self.first_law_residual()
        if r != 0:
            raise FirstLawViolation(
                f"cycle {self.label!r} does not balance: residual "
                f"{r} J ({float(r):.6g} J). Energy in was "
                f"{float(self.heat_in.joules):.6g} J; the accounted "
                f"outputs total "
                f"{float(self.heat_in.joules - r):.6g} J. A residual "
                f"is not a rounding artefact here -- the arithmetic is "
                f"exact rational -- so it is an unaccounted term.")
        return r

    # -- efficiency -----------------------------------------------------

    def efficiency(self) -> Fraction:
        """W_out / Q_in, exact."""
        if self.heat_in.joules == 0:
            raise ZeroDivisionError(
                "no heat in: efficiency is undefined, not infinite")
        return self.work_out.joules / self.heat_in.joules

    def carnot_bound(self) -> Fraction:
        return carnot_efficiency(self.t_cold_k, self.t_hot_k)

    def check_carnot(self, *, reservoirs_are_thermal: bool = True
                     ) -> Fraction:
        return check_efficiency_claim(
            self.efficiency(), self.t_cold_k, self.t_hot_k,
            reservoirs_are_thermal=reservoirs_are_thermal)

    def dissipated_fraction(self) -> Fraction:
        return self.dissipation.joules / self.heat_in.joules

    def certify(self) -> dict:
        """Run both gates and emit the fixture record."""
        residual = self.check_first_law()
        bound = self.check_carnot()
        eta = self.efficiency()
        return {
            "label": self.label,
            "heat_in_j": self.heat_in.joules,
            "work_out_j": self.work_out.joules,
            "heat_rejected_j": self.heat_rejected.joules,
            "dissipation_j": self.dissipation.joules,
            "first_law_residual_j": residual,
            "first_law_exact": residual == 0,
            "efficiency": eta,
            "carnot_bound": bound,
            "carnot_margin": bound - eta,
            "dissipated_fraction": self.dissipated_fraction(),
            "t_hot_k": self.t_hot_k,
            "t_cold_k": self.t_cold_k,
            "provenance": self.provenance,
            "evidence_class": "ARITHMETIC_ON_A_SYNTHETIC_FIXTURE",
            "measured_here": "nothing",
            "what_this_does_not_say": (
                "This fixture demonstrates that the ledger's own "
                "arithmetic is consistent and bounded. It is not a "
                "measurement of any engine, it does not show that a "
                "quantum working substance beats a classical one, and "
                "it says nothing about whether any resonator in this "
                "programme moves energy in any of these categories."),
        }


#: The P17 fixture. A quantum Otto cycle expressed in exact zeptojoule
#: rationals, so the first law closes with residual exactly 0.
#:
#: The numbers are synthetic and chosen for exactness, not taken from
#: any experiment. Their job is to exercise the ledger, including the
#: dissipation term that a two-term "heat in = work + heat out"
#: statement silently drops.
_ZJ = Fraction(1, 10 ** 21)


def quantum_otto_fixture() -> CycleLedger:
    """A balanced four-stroke fixture: 1000 zJ in, 120 zJ out as work.

    Efficiency 12%, against a Carnot bound of 1/3 for the stated
    reservoir temperatures. 85% of the input is rejected as heat and
    3% is dissipated; the dissipation term exists because dropping it
    is the commonest way a fixture appears to close when it does not.
    """
    return CycleLedger(
        label="synthetic quantum Otto cycle (P17 fixture)",
        heat_in=Energy(EnergyKind.HEAT, 1000 * _ZJ,
                       label="absorbed from the hot reservoir",
                       temperature_k=Fraction(300)),
        work_out=Energy(EnergyKind.WORK, 120 * _ZJ,
                        label="net work per cycle"),
        heat_rejected=Energy(EnergyKind.HEAT, 850 * _ZJ,
                             label="rejected to the cold reservoir",
                             temperature_k=Fraction(200)),
        dissipation=Energy(EnergyKind.DISSIPATION, 30 * _ZJ,
                           label="irreversible losses (friction, "
                                 "non-adiabatic transitions)"),
        t_hot_k=Fraction(300),
        t_cold_k=Fraction(200),
        provenance=(
            "synthetic; exact rational values chosen so the first law "
            "closes with zero residual. Not derived from and not "
            "compared against any published engine."),
        notes={
            "why_exact": (
                "the balance is checked as exact rational equality, so "
                "a missing term cannot hide inside a tolerance"),
            "why_dissipation_is_separate": (
                "lumping dissipation into rejected heat makes the "
                "ledger close while concealing where the availability "
                "went; they are different categories here"),
        },
    )


# --- what other people have actually built ------------------------------


@dataclass(frozen=True)
class LiteratureEngine:
    """A published engine. A source is mandatory."""

    label: str
    platform: str
    cycle: str
    reported_efficiency: float | None
    source: str
    precision: str
    note: str = ""

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError(
                f"{self.label!r}: a literature entry without a source "
                f"is an invented number. Refused.")
        if not self.precision.strip():
            raise ValueError(
                f"{self.label!r}: state the precision of the quoted "
                f"figure. 'approximately' and 'as published' are "
                f"different claims.")
        if self.reported_efficiency is not None:
            if not 0.0 <= self.reported_efficiency < 1.0:
                raise ValueError(
                    f"{self.label!r}: reported efficiency "
                    f"{self.reported_efficiency} is outside [0, 1); an "
                    f"engine efficiency at or above unity is a "
                    f"transcription error, not a result")


#: Published quantum/nanoscale heat engines, recorded for orientation
#: only. Efficiencies are quoted at the precision stated in each
#: entry and are NOT used to support any claim in this repository;
#: the ledger's own gates run on the synthetic fixture.
LITERATURE_ENGINES = (
    LiteratureEngine(
        label="single-atom heat engine",
        platform="single Ca-40 ion in a tapered linear Paul trap",
        cycle="Otto",
        reported_efficiency=0.0028,
        source=("Rossnagel, Dawkins, Tolazzi, Abah, Lutz, "
                "Schmidt-Kaler & Singer, Science 352, 325 (2016)"),
        precision=("order-of-magnitude; ~0.3% efficiency at sub-zJ "
                   "per cycle. Verify the exact figure against the "
                   "paper before citing it anywhere load-bearing."),
        note=("the useful point is not the efficiency but that a "
              "single-particle working substance obeys the same "
              "bookkeeping as a steam engine"),
    ),
    LiteratureEngine(
        label="nanobeam engine with a squeezed reservoir",
        platform="nanomechanical membrane, electrically driven baths",
        cycle="Stirling-like",
        reported_efficiency=None,
        source=("Klaers, Faelt, Imamoglu & Togan, "
                "Phys. Rev. X 7, 031044 (2017)"),
        precision=("no single efficiency quoted here deliberately; the "
                   "reported operation exceeds the standard "
                   "two-temperature Carnot bound"),
        note=CARNOT_BOUND_SCOPE,
    ),
    LiteratureEngine(
        label="spin quantum Otto engine",
        platform="nuclear spins in a liquid-state NMR sample",
        cycle="Otto",
        reported_efficiency=0.42,
        source=("Peterson, Batalhao, Herrera, Souza, Sarthour, "
                "Oliveira & Serra, Phys. Rev. Lett. 123, 240601 "
                "(2019)"),
        precision=("approximate; ~42% as summarised. Verify against "
                   "the paper before citing it load-bearingly."),
    ),
)


# --- the headline ledger ------------------------------------------------


def energy_ontology() -> dict:
    """The P17 headline: five categories and what each does not permit."""
    return {
        "kinds": [k.value for k in EnergyKind],
        "transit_kinds": sorted(k.value for k in TRANSIT_KINDS),
        "state_kinds": sorted(k.value for k in STATE_KINDS),
        "rule": (
            "state quantities and transit quantities are different "
            "types and do not add. The only licensed crossing is "
            "CycleLedger.first_law_residual(), which must be called by "
            "name with every term labelled."),
        "kelvin_planck": KELVIN_PLANCK,
        "carnot": CARNOT_SOURCE,
        "carnot_scope": CARNOT_BOUND_SCOPE,
        "fixture": quantum_otto_fixture().certify(),
        "literature_engines": [e.label for e in LITERATURE_ENGINES],
        "evidence_class": "ONTOLOGY_AND_EXACT_ARITHMETIC",
        "measured_here": "nothing",
        "what_this_does_not_say": (
            "The module does not claim that any RGCS resonator is a "
            "heat engine, that any measured quantity in this "
            "programme belongs to any of these categories, or that a "
            "quantum working substance offers an advantage. It claims "
            "only that if such quantities are ever accounted, they "
            "must be accounted separately, and that a reservoir "
            "energy is not a work budget."),
    }
