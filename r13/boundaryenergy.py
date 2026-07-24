"""P17 — abrupt and finite-time boundary changes, with the energy books kept.

A boundary can change suddenly or over a ramp, and it can be mechanical,
electrical or optical. In every case changing it while the system holds
energy does **work** on the system, and that work has to appear in the
accounts. This module does the accounting for all three domains in one
unified ledger, and refuses every route by which a boundary change is
made to look like a source of energy.

**Three boundary domains**, each with its own conserved coordinate that
stays continuous across the change and its own stiffness-like parameter
that the boundary moves:

* ``MECHANICAL`` -- a stiffness or support changing at a displaced,
  moving resonator (cf. :mod:`r11.mechboundary`, whose modal projection
  and closed-form boundary work this reuses conceptually);
* ``ELECTRICAL`` -- a load or electrode changing the elastance seen by a
  stored charge;
* ``OPTICAL`` -- a reflector or dielectric changing the modal stiffness
  seen by a stored field amplitude (the quantum lane of a switched
  optical boundary is :mod:`r11.dynboundary`, kept separate).

For each, :func:`abrupt_change` treats a sudden change (the coordinate is
continuous, nothing is dissipated or radiated in zero time, and the whole
ledger is the boundary work) and :func:`finite_time_change` treats a ramp
over a time ``tau`` (during which the model books a radiated and a
dissipated term as well).

**The unified ledger.** With ``E`` the stored energy,

    E_after = E_before + W_boundary - E_dissipated - E_radiated,

and :func:`energy_ledger` returns every term with its own sigma,
propagates the sigmas in quadrature, and reports ``E_unclosed`` **as an
interval**. No bench data exist in this repository, so every term
defaults to ``BLOCKED_MISSING_INPUT`` with an unbounded sigma and the
interval trivially includes zero -- a residual that says nothing, which
is the honest reading.

**The load-bearing refusals.**
:func:`refuse_unclosed_as_new_energy` refuses a residual whose interval
spans zero being called a new energy channel;
:func:`refuse_ignored_boundary_work` refuses a ledger written without the
work that pays for the change; :func:`refuse_transferred_energy_as_loss`
refuses energy that merely moved to another mode being booked as loss;
and :func:`refuse_infinite_free_energy` refuses the instantaneous-switch
divergence -- the ``tau -> 0`` idealization -- being read as free energy.

Nothing here is measured. No boundary was switched, no energy was
recorded, and every number is arithmetic on a declared model.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

import numpy as np

# --- verdict, claim vocabulary, tolerances --------------------------------

#: The standing verdict for this module.
VERDICT = "DYNAMIC_BOUNDARY_ENERGY_LEDGER_CLOSES_NO_NEW_ENERGY"

#: The typed claim vocabulary, exact strings, from the R13 claim ladder.
CLAIM_CLASSES: tuple[str, ...] = (
    "EXACT_IDENTITY",
    "SOURCE_ESTABLISHED_PHYSICS",
    "CONVENTIONAL_LITERATURE",
    "DERIVED_ARITHMETIC",
    "ANALYTIC_MODEL",
    "NUMERICAL_SIMULATION",
    "REPOSITORY_COMPUTATIONAL_RESULT",
    "ENGINEERING_CANDIDATE",
    "BENCH_MEASUREMENT",
    "INDEPENDENTLY_REPLICATED",
    "UNSUPPORTED",
    "BLOCKED_MISSING_INPUT",
)

REPOSITORY_COMPUTATIONAL_RESULT = "REPOSITORY_COMPUTATIONAL_RESULT"

#: What every real energy term is here: no bench has supplied a value.
BLOCKED_MISSING_INPUT = "BLOCKED_MISSING_INPUT"

MEASURED_HERE = "nothing"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: A sigma of ``None`` means the term is not calibrated at all: its
#: uncertainty is unbounded, not zero.
UNBOUNDED = None

#: Default coverage factor for the reported residual interval (2 sigma).
DEFAULT_K_SIGMA = 2.0

#: Relative tolerance on the model energy identities.
ENERGY_TOL = 1e-12


class BoundaryEnergyError(RuntimeError):
    """Raised when a boundary-energy claim exceeds what the accounting licenses.

    Covers the structural guards (a non-positive parameter, a
    non-positive ramp time, an unknown ledger term) and the four
    refusals: :func:`refuse_unclosed_as_new_energy`,
    :func:`refuse_ignored_boundary_work`,
    :func:`refuse_transferred_energy_as_loss`,
    :func:`refuse_infinite_free_energy`.
    """


# --- (1) the three boundary domains ---------------------------------------

class BoundaryDomain(Enum):
    """The three boundary domains, each an independently typed change.

    * ``MECHANICAL`` -- a stiffness or support at a displaced resonator;
      the conserved coordinate is displacement, the parameter a stiffness.
    * ``ELECTRICAL`` -- a load or electrode; the conserved coordinate is
      charge, the parameter an elastance (inverse capacitance).
    * ``OPTICAL`` -- a reflector or dielectric; the conserved coordinate
      is the modal field amplitude, the parameter a modal stiffness.
    """

    MECHANICAL = "MECHANICAL"
    ELECTRICAL = "ELECTRICAL"
    OPTICAL = "OPTICAL"


#: The conserved coordinate that is continuous across a boundary change,
#: and the stiffness-like parameter the boundary moves, per domain.
DOMAIN_COORDINATE: dict[BoundaryDomain, str] = {
    BoundaryDomain.MECHANICAL: "displacement",
    BoundaryDomain.ELECTRICAL: "charge",
    BoundaryDomain.OPTICAL: "field_amplitude",
}

DOMAIN_PARAMETER: dict[BoundaryDomain, str] = {
    BoundaryDomain.MECHANICAL: "stiffness",
    BoundaryDomain.ELECTRICAL: "elastance",
    BoundaryDomain.OPTICAL: "modal_stiffness",
}

DOMAIN_BOUNDARY: dict[BoundaryDomain, str] = {
    BoundaryDomain.MECHANICAL: "stiffness/support",
    BoundaryDomain.ELECTRICAL: "load/electrode",
    BoundaryDomain.OPTICAL: "reflector/dielectric",
}


@dataclass(frozen=True)
class BoundaryChange:
    """One boundary change in one domain: a parameter moved at a coordinate.

    ``param_before`` and ``param_after`` are the stiffness-like parameter
    of the domain before and after the change; ``coordinate`` is the
    conserved coordinate amplitude (displacement, charge or field), which
    is continuous through the change. The stored energy is
    ``E = 0.5 * parameter * coordinate**2`` in the domain's own basis.
    Every value is a model number in arbitrary consistent units; none is
    a measurement.
    """

    domain: BoundaryDomain
    param_before: float
    param_after: float
    coordinate: float = 1.0

    def __post_init__(self) -> None:
        if not isinstance(self.domain, BoundaryDomain):
            raise BoundaryEnergyError("domain must be a BoundaryDomain")
        if self.param_before <= 0.0 or self.param_after <= 0.0:
            raise BoundaryEnergyError(
                "a stiffness-like parameter must be positive; a "
                "non-positive parameter has no stored-energy basis")
        for value in (self.param_before, self.param_after, self.coordinate):
            if not math.isfinite(float(value)):
                raise BoundaryEnergyError("every value must be finite")

    def energy_before(self) -> float:
        """``0.5 * param_before * coordinate**2`` in the domain basis."""
        return 0.5 * float(self.param_before) * float(self.coordinate) ** 2

    def boundary_work(self) -> float:
        """Work done by the boundary on the stored coordinate.

        ``W = 0.5 * (param_after - param_before) * coordinate**2`` -- the
        work of stiffening or relaxing the domain at a fixed, continuous
        coordinate. Supplied by whatever moved the boundary (an actuator,
        a bias supply, a modulator); the boundary is the route, not the
        source.
        """
        return (0.5 * (float(self.param_after) - float(self.param_before))
                * float(self.coordinate) ** 2)


# --- (2) abrupt and finite-time changes -----------------------------------

@dataclass(frozen=True)
class ChangeResult:
    """What one boundary change did to the stored energy, with the ledger."""

    domain: BoundaryDomain
    profile: str
    tau: float
    energy_before: float
    energy_after: float
    boundary_work: float
    dissipated: float
    radiated: float

    def ledger(self, k_sigma: float = DEFAULT_K_SIGMA,
               include_boundary_work: bool = True) -> dict:
        """The model ledger for this change, closed as arithmetic.

        The model terms are exact numbers, so their sigmas are zero and
        the residual interval collapses to a point: the ledger closes at
        ``E_unclosed == 0`` when every term is present. This is the
        arithmetic of the model, not a measurement -- for real values
        every term is ``BLOCKED_MISSING_INPUT`` (see :func:`blocked_ledger`).
        """
        sigmas = {name: 0.0 for name in LEDGER_TERMS}
        return energy_ledger(
            self.energy_before, self.energy_after, self.boundary_work,
            dissipated=self.dissipated, radiated=self.radiated,
            sigmas=sigmas, include_boundary_work=include_boundary_work,
            k_sigma=k_sigma)

    def as_dict(self) -> dict:
        return {
            "domain": self.domain.value,
            "boundary": DOMAIN_BOUNDARY[self.domain],
            "coordinate": DOMAIN_COORDINATE[self.domain],
            "parameter": DOMAIN_PARAMETER[self.domain],
            "profile": self.profile,
            "tau": self.tau,
            "energy_before": self.energy_before,
            "energy_after": self.energy_after,
            "boundary_work": self.boundary_work,
            "dissipated": self.dissipated,
            "radiated": self.radiated,
            "identity": ("E_after == E_before + W_boundary - E_dissipated "
                         "- E_radiated"),
            "ledger": self.ledger(),
            "measured_here": MEASURED_HERE,
        }


def abrupt_change(change: BoundaryChange) -> ChangeResult:
    """A sudden boundary change: the coordinate is continuous, nothing lost.

    The conserved coordinate is continuous through an instantaneous
    change, so the energy jumps by exactly the boundary work and nothing
    is dissipated or radiated in zero time. The ledger is therefore the
    whole of the boundary work: ``E_after == E_before + W_boundary``.
    """
    e_before = change.energy_before()
    work = change.boundary_work()
    return ChangeResult(
        domain=change.domain, profile="ABRUPT", tau=0.0,
        energy_before=e_before, energy_after=e_before + work,
        boundary_work=work, dissipated=0.0, radiated=0.0)


#: Model couplings for the finite-time loss channels. Radiated energy
#: grows as the ramp gets faster (a broadband transient), dissipated
#: energy grows with the time spent ramping (a viscous/resistive path).
#: Both are model numbers; the tau-dependence is the modelling choice,
#: the ledger identity is not.
RADIATION_COUPLING = 0.125
DISSIPATION_COUPLING = 0.0625


def finite_time_change(change: BoundaryChange, tau: float,
                       radiation_coupling: float = RADIATION_COUPLING,
                       dissipation_coupling: float = DISSIPATION_COUPLING,
                       ) -> ChangeResult:
    """A boundary change ramped over a time ``tau > 0``.

    The boundary work is the same quasi-static quantity as the abrupt
    case, but part of it is now radiated (a term that *grows as ``tau``
    shrinks*, the broadband transient of a fast switch) and part
    dissipated (a term that grows with the ramp duration). The stored
    energy after the change is the boundary work less those two losses,
    so ``E_after == E_before + W_boundary - E_dissipated - E_radiated``
    holds by construction and :meth:`ChangeResult.ledger` closes.

    ``tau <= 0`` is refused: it is the instantaneous idealization whose
    radiated term diverges, not a finite ramp (see
    :func:`refuse_infinite_free_energy`).
    """
    if tau <= 0.0:
        raise BoundaryEnergyError(
            "a finite-time change needs tau > 0; tau <= 0 is the "
            "instantaneous idealization whose radiated term diverges, not "
            "a bench ramp. Use abrupt_change for the sudden limit and see "
            "refuse_infinite_free_energy")
    if radiation_coupling < 0.0 or dissipation_coupling < 0.0:
        raise BoundaryEnergyError("loss couplings cannot be negative")
    work = change.boundary_work()
    scale = abs(work)
    radiated = float(radiation_coupling) * scale / float(tau)
    dissipated = float(dissipation_coupling) * scale * float(tau)
    e_before = change.energy_before()
    e_after = e_before + work - dissipated - radiated
    return ChangeResult(
        domain=change.domain, profile="FINITE_TIME", tau=float(tau),
        energy_before=e_before, energy_after=e_after,
        boundary_work=work, dissipated=dissipated, radiated=radiated)


# --- (3) the unified ledger -----------------------------------------------

#: Every ledger term, in report order. ``boundary_work`` is the one most
#: often left out, so the omission control targets it by name.
LEDGER_TERMS: tuple[str, ...] = (
    "energy_before",
    "boundary_work",
    "energy_dissipated",
    "energy_radiated",
    "energy_after",
)

TERM_MEANINGS: dict[str, str] = {
    "energy_before": "stored energy in the domain basis before the change",
    "boundary_work": "work done on the system by whatever moved the "
                     "boundary; a term, not a footnote",
    "energy_dissipated": "energy lost to resistive or viscous paths during "
                         "the change",
    "energy_radiated": "energy radiated away, including the broadband "
                       "content of a fast switch",
    "energy_after": "stored energy in the domain basis after the change",
}


@dataclass(frozen=True)
class LedgerTerm:
    """One line of the ledger: a value, a sigma and a status.

    ``sigma is None`` means the term is **not calibrated**: its
    uncertainty is unbounded rather than zero, and its status is
    ``BLOCKED_MISSING_INPUT``.
    """

    name: str
    value: float
    sigma: float | None = UNBOUNDED

    def __post_init__(self) -> None:
        if self.name not in LEDGER_TERMS:
            raise BoundaryEnergyError(f"{self.name!r} is not a ledger term")
        if not math.isfinite(float(self.value)):
            raise BoundaryEnergyError(f"{self.name}: value must be finite")
        if self.sigma is not None:
            s = float(self.sigma)
            if not math.isfinite(s) or s < 0.0:
                raise BoundaryEnergyError(
                    f"{self.name}: sigma must be finite and non-negative, "
                    f"or None for an uncalibrated term")

    @property
    def calibrated(self) -> bool:
        return self.sigma is not None

    @property
    def status(self) -> str:
        return (REPOSITORY_COMPUTATIONAL_RESULT if self.calibrated
                else BLOCKED_MISSING_INPUT)

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "meaning": TERM_MEANINGS[self.name],
            "value": float(self.value),
            "sigma": None if self.sigma is None else float(self.sigma),
            "calibrated": self.calibrated,
            "status": self.status,
        }


def energy_ledger(energy_before: float, energy_after: float,
                  boundary_work: float, *,
                  dissipated: float = 0.0, radiated: float = 0.0,
                  sigmas: dict | None = None,
                  include_boundary_work: bool = True,
                  k_sigma: float = DEFAULT_K_SIGMA) -> dict:
    """The unified boundary-energy ledger, with an interval on the residual.

    ``E_unclosed = (E_before + W_boundary) - (E_after + E_dissipated +
    E_radiated)``: the input side is the stored energy plus the boundary
    work, the output side is the stored energy after plus what was
    dissipated and radiated. The identity closes when ``E_unclosed`` is
    zero.

    Every term carries its own sigma. A term whose sigma is ``None`` is
    **uncalibrated**: its uncertainty is unbounded, so the interval on
    ``E_unclosed`` is unbounded too and includes zero vacuously. That is
    the default here -- no bench data exist -- and every term then has
    status ``BLOCKED_MISSING_INPUT``. With sigmas supplied they are
    propagated in quadrature and the residual is
    ``E_unclosed +/- k_sigma * sigma``.

    ``include_boundary_work=False`` is the deliberate omission: drop the
    term that pays for the change and the residual becomes exactly minus
    that work, which is how the term is shown to be load-bearing.
    """
    if float(k_sigma) <= 0.0:
        raise BoundaryEnergyError("the coverage factor must be positive")
    values = {
        "energy_before": float(energy_before),
        "boundary_work": float(boundary_work),
        "energy_dissipated": float(dissipated),
        "energy_radiated": float(radiated),
        "energy_after": float(energy_after),
    }
    supplied = dict(sigmas or {})
    unknown = set(supplied) - set(LEDGER_TERMS)
    if unknown:
        raise BoundaryEnergyError(
            f"unknown ledger term(s) in sigmas: {sorted(unknown)}")

    terms = [LedgerTerm(name, values[name], supplied.get(name, UNBOUNDED))
             for name in LEDGER_TERMS]

    work_in = values["boundary_work"] if include_boundary_work else 0.0
    input_side = values["energy_before"] + work_in
    output_side = (values["energy_after"] + values["energy_dissipated"]
                   + values["energy_radiated"])
    e_unclosed = input_side - output_side

    # Terms that actually enter the residual: the boundary-work term drops
    # out of the propagation exactly when it is omitted.
    included = [t for t in terms
                if include_boundary_work or t.name != "boundary_work"]
    uncalibrated = [t.name for t in included if not t.calibrated]
    if uncalibrated:
        sigma_unclosed: float | None = None
        lo, hi = (-math.inf, math.inf)
    else:
        sigma_unclosed = float(np.sqrt(
            np.sum([float(t.sigma) ** 2 for t in included])))
        half = float(k_sigma) * sigma_unclosed
        lo, hi = (e_unclosed - half, e_unclosed + half)

    includes_zero = bool(lo <= 0.0 <= hi)
    return {
        "identity": ("E_unclosed = (E_before + W_boundary) - (E_after + "
                     "E_dissipated + E_radiated)"),
        "terms": [t.as_dict() for t in terms],
        "term_names": list(LEDGER_TERMS),
        "input_side": float(input_side),
        "output_side": float(output_side),
        "e_unclosed": float(e_unclosed),
        "sigma_unclosed": sigma_unclosed,
        "k_sigma": float(k_sigma),
        "e_unclosed_interval": (lo, hi),
        "interval_includes_zero": includes_zero,
        "closes": includes_zero,
        "closure_is_vacuous": bool(uncalibrated),
        "uncalibrated_terms": uncalibrated,
        "all_terms_blocked": all(
            t.status == BLOCKED_MISSING_INPUT for t in terms),
        "boundary_work_included": bool(include_boundary_work),
        "boundary_work": values["boundary_work"],
        "residual_is_new_energy": False,
        "claim_class": (BLOCKED_MISSING_INPUT if uncalibrated
                        else REPOSITORY_COMPUTATIONAL_RESULT),
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "note": (
            "E_unclosed is an interval. An interval that spans zero is a "
            "statement about how well the terms are calibrated, not a "
            "discovery of a channel. Every term here is uncalibrated "
            "unless a sigma is supplied, and none has been measured"),
        "verdict": VERDICT,
    }


def blocked_ledger() -> dict:
    """The ledger as it actually stands here: every term missing input.

    No displacement, charge, field, work, dissipation or radiation has
    been recorded, so every term is ``BLOCKED_MISSING_INPUT`` with an
    unbounded sigma. ``E_unclosed`` is zero over an unbounded interval
    that trivially includes zero, and says nothing at all.
    """
    return energy_ledger(0.0, 0.0, 0.0)


# --- (4) the power control ------------------------------------------------

#: A synthetic ledger whose terms are chosen so the books close exactly.
#: The values are dyadic rationals, so ``E_after == E_before + W - D - R``
#: is exact in binary64 rather than exact only to a tolerance.
SYNTHETIC_TERMS: dict[str, float] = {
    "energy_before": 4.0,
    "boundary_work": 2.0,
    "energy_dissipated": 1.5,
    "energy_radiated": 0.5,
}

#: E_after = 4.0 + 2.0 - 1.5 - 0.5 = 4.0 exactly.
SYNTHETIC_ENERGY_AFTER = float(
    SYNTHETIC_TERMS["energy_before"] + SYNTHETIC_TERMS["boundary_work"]
    - SYNTHETIC_TERMS["energy_dissipated"] - SYNTHETIC_TERMS["energy_radiated"])


def synthetic_ledger(include_boundary_work: bool = True,
                     sigma: float = 0.0) -> dict:
    """A ledger with known terms, for the power control.

    With every sigma zero and the boundary work included, the residual is
    exactly zero. Omit the boundary work and the residual is exactly
    minus that work -- neither approximately nor to a tolerance. That is
    the point of the control: the ledger has teeth, and the missing term
    is the whole of the deficit.
    """
    if float(sigma) < 0.0:
        raise BoundaryEnergyError("sigma cannot be negative")
    sigmas = {name: float(sigma) for name in LEDGER_TERMS}
    return energy_ledger(
        SYNTHETIC_TERMS["energy_before"], SYNTHETIC_ENERGY_AFTER,
        SYNTHETIC_TERMS["boundary_work"],
        dissipated=SYNTHETIC_TERMS["energy_dissipated"],
        radiated=SYNTHETIC_TERMS["energy_radiated"],
        sigmas=sigmas, include_boundary_work=include_boundary_work)


def power_check() -> dict:
    """Run the power control both ways and report what each leaves."""
    closed = synthetic_ledger(True)
    omitted = synthetic_ledger(False)
    work = SYNTHETIC_TERMS["boundary_work"]
    return {
        "synthetic_terms": dict(SYNTHETIC_TERMS),
        "synthetic_energy_after": SYNTHETIC_ENERGY_AFTER,
        "closed_residual": closed["e_unclosed"],
        "closed_closes": closed["closes"],
        "closed_is_vacuous": closed["closure_is_vacuous"],
        "closed_residual_is_zero": closed["e_unclosed"] == 0.0,
        "omitted_residual": omitted["e_unclosed"],
        "omitted_closes": omitted["closes"],
        "omitted_residual_magnitude_equals_work":
            abs(omitted["e_unclosed"]) == work,
        "boundary_work": work,
        "claim_class": REPOSITORY_COMPUTATIONAL_RESULT,
        "note": ("the ledger closes exactly when every term is present, "
                 "and omitting the boundary work leaves a residual whose "
                 "magnitude is exactly that work; the detector is "
                 "therefore sensitive to a missing term of that size"),
        "measured_here": MEASURED_HERE,
    }


# --- (5) the refusals -----------------------------------------------------

def refuse_unclosed_as_new_energy(residual: float = 0.0,
                                  interval: tuple = (-math.inf, math.inf),
                                  claimed_channel: str = "a new energy channel",
                                  ) -> None:
    """Refuse a residual whose interval spans zero as new energy. Always raises.

    A non-zero ``E_unclosed`` whose interval includes zero is consistent
    with zero, and "consistent with zero" is a calibration statement, not
    a channel. Promoting it requires the opposite of what is available
    here: every term calibrated, the boundary work included, and the
    interval excluding zero by a stated margin. None of that holds while
    every term is ``BLOCKED_MISSING_INPUT``.
    """
    lo, hi = (float(interval[0]), float(interval[1]))
    spans = lo <= 0.0 <= hi
    raise BoundaryEnergyError(
        f"refused: attributing E_unclosed = {float(residual):g} to "
        f"{claimed_channel!r}. The reported interval is [{lo:g}, {hi:g}], "
        f"which {'includes' if spans else 'excludes'} zero. A residual is "
        f"the part of the ledger the calibration does not yet account "
        f"for; it becomes evidence of a channel only when every term is "
        f"calibrated, the boundary work is included, and the interval "
        f"excludes zero by a stated margin. Here every term is "
        f"{BLOCKED_MISSING_INPUT}, so the residual is UNMEASURED and "
        f"cannot be new energy. {VERDICT}")


def refuse_ignored_boundary_work(
        ledger_result: dict | None = None,
        claim: str = "the ledger closes without boundary work") -> None:
    """Refuse a ledger written without the boundary-work term. Always raises.

    Changing a stiffness, a load or a reflector while the system holds
    energy does work on it, and that work is a ledger TERM. Leave it out
    and the residual is exactly its size -- a deficit manufactured by the
    bookkeeping, ready to be re-described as an unknown channel.
    """
    missing = ""
    if isinstance(ledger_result, dict):
        w = ledger_result.get("boundary_work")
        r = ledger_result.get("e_unclosed")
        included = ledger_result.get("boundary_work_included")
        missing = (f" The supplied ledger reports W_boundary = {w!r}, "
                   f"included = {included!r}, residual = {r!r}.")
    raise BoundaryEnergyError(
        f"refused: {claim!r}. Boundary work is a ledger TERM, not a "
        f"footnote: moving a mechanical stiffness, an electrical load or "
        f"an optical reflector while the system holds energy does work on "
        f"it, and that work has to appear on the input side.{missing} "
        f"Omit it and the residual is exactly its size, a deficit "
        f"manufactured by the bookkeeping. Include boundary_work, or do "
        f"not call the result a ledger. {VERDICT}")


def refuse_transferred_energy_as_loss(
        from_mode: int = 0, to_modes: object = None,
        transferred: float = 0.0,
        claim: str = "the mode lost this energy") -> None:
    """Refuse energy that moved to another mode being booked as loss. Raises.

    When a boundary changes, the basis moves and a mode that carried the
    state is re-expressed over several modes of the new system. Its own
    occupation falls, and every unit of the difference sits in its
    neighbours -- still in the same system, still available. Calling that
    a loss counts it twice, once as gone and once as present, and
    manufactures a deficit. Loss lowers the TOTAL over all modes; a
    transfer does not.
    """
    where = "" if to_modes is None else f" (it is in modes {to_modes})"
    raise BoundaryEnergyError(
        f"refused: {claim!r} for mode {from_mode} with "
        f"{float(transferred):g} of transfer{where}. Energy moved to "
        f"another mode of the same system is NOT loss: the basis changed, "
        f"the state was re-expressed over it, and the total over all modes "
        f"is unchanged by the projection. Booking a transfer as a loss "
        f"counts the same energy twice, and the deficit that produces is "
        f"arithmetic, not a channel. Dissipation lowers the TOTAL; check "
        f"the sum over modes before calling anything lost. {VERDICT}")


def refuse_infinite_free_energy(tau: float = 0.0,
                                claimed_output: str = "unbounded energy",
                                ) -> None:
    """Refuse the instantaneous-switch divergence as free energy. Always raises.

    Ramp a boundary over a finite time ``tau`` and every energy term is
    finite. Take ``tau -> 0`` and the radiated term diverges, because an
    instantaneous change has no spectral cutoff and excites arbitrarily
    high frequencies. That divergence is a statement about an impossible
    boundary -- no mechanical support, electrode or reflector changes in
    zero time -- not a supply of free energy.
    """
    raise BoundaryEnergyError(
        f"a claim of {claimed_output!r} from the tau == {float(tau):g} "
        f"instantaneous-switch divergence is refused. The divergence is an "
        f"UNPHYSICAL IDEALIZATION: it is what the model returns when asked "
        f"about a boundary that changes in zero time, which no material "
        f"can do. Every finite tau gives a finite radiated energy and a "
        f"finite ledger, and that energy is paid for by the agent doing "
        f"the switching. {VERDICT}")


# --- (6) the report -------------------------------------------------------

def boundaryenergy_report() -> dict:
    """The standing statement of what this module is and is not."""
    blocked = blocked_ledger()
    return {
        "what_this_is": (
            "a unified energy ledger for abrupt and finite-time changes of "
            "mechanical, electrical and optical boundaries: for each "
            "domain the stored energy before and after and the work done "
            "by the boundary, with a residual reported as an interval"),
        "domains": [d.value for d in BoundaryDomain],
        "boundaries": {d.value: DOMAIN_BOUNDARY[d] for d in BoundaryDomain},
        "coordinates": {d.value: DOMAIN_COORDINATE[d] for d in BoundaryDomain},
        "profiles": ["ABRUPT", "FINITE_TIME"],
        "identity": blocked["identity"],
        "ledger_terms": {name: TERM_MEANINGS[name] for name in LEDGER_TERMS},
        "ledger_as_it_stands": {
            "e_unclosed": blocked["e_unclosed"],
            "sigma_unclosed": blocked["sigma_unclosed"],
            "e_unclosed_interval": blocked["e_unclosed_interval"],
            "interval_includes_zero": blocked["interval_includes_zero"],
            "closure_is_vacuous": blocked["closure_is_vacuous"],
            "all_terms_blocked": blocked["all_terms_blocked"],
            "claim_class": blocked["claim_class"],
        },
        "power_control": power_check(),
        "reused_conceptually": [
            "r11.mechboundary (modal projection and closed-form boundary "
            "work)",
            "r11.dynboundary (the finite-switching-time cutoff and its "
            "tau -> 0 divergence)",
        ],
        "refusals": [
            "refuse_unclosed_as_new_energy",
            "refuse_ignored_boundary_work",
            "refuse_transferred_energy_as_loss",
            "refuse_infinite_free_energy",
        ],
        "firewalls": [
            "a residual whose interval spans zero is a calibration "
            "statement, not a new energy channel",
            "boundary work is a ledger term; omitting it manufactures "
            "exactly its own size of deficit",
            "energy moved to another mode is not energy lost",
            "the tau -> 0 divergence is an unphysical idealization, not "
            "usable free energy",
        ],
        "hardware_status": (
            "BLOCKED_MISSING_INPUT - no boundary has been switched and no "
            "energy has been recorded"),
        "claim_class": REPOSITORY_COMPUTATIONAL_RESULT,
        "claim_classes": list(CLAIM_CLASSES),
        "evidence_class": "NUMERICAL_SIMULATION",
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "verdict": VERDICT,
        "what_this_does_not_say": (
            "It does not say any boundary was switched, that any energy, "
            "work, dissipation or radiation was measured, or that the "
            "domain parameters describe a real support, electrode or "
            "reflector: they are model numbers in arbitrary consistent "
            "units. It does not say the ledger closes because it was "
            "checked against a bench -- every real term is "
            "BLOCKED_MISSING_INPUT and E_unclosed is an interval that "
            "includes zero vacuously; the only ledgers that close "
            "numerically here are synthetic ones built from declared model "
            "values. It does not say a boundary is a source of energy, "
            "that a residual is a new channel, that transferred energy is "
            "lost, or that the instantaneous-switch divergence is free "
            "energy. No apparatus was operated."),
    }
