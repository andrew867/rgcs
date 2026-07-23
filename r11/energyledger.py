"""R11 P15 — where the energy went: a closing ledger with an unmeasured residual.

Interrupt a driven resonator and the energy has to be somewhere. This
module does the accounting, in two layers that are deliberately kept
apart.

**Layer one: mechanical modes, and what a basis switch really does.**
A classical mode carries ``E_i = 0.5*m*qdot**2 + 0.5*k*q**2``, and under
light damping that energy decays as ``E_i(t) = E_i(0)*exp(-omega_i*t/Q_i)``.
The convention matters and is stated rather than assumed: this is the
**energy** decay, so the **amplitude** decays at *half* that rate,
``a(t) = a(0)*exp(-omega*t/(2Q))``. :func:`damping_convention` documents
it and the factor of two is computed, not asserted -- if the two rates
were ever written with the same exponent, the ledger would lose half its
energy on a change of variable.

When a boundary condition switches, the modal *basis* moves. The physical
displacement ``u`` and momentum ``p = M v`` are continuous through the
switch; the eigenbasis is not. :func:`switch_basis` therefore preserves
``u`` and ``p``, solves for the post-switch velocity, projects into the
post-switch eigenbasis and reports the energy of **every** resulting
mode. Two red-team attacks live exactly here:

* **energy that moved is not energy that was lost.** A mode whose
  occupation fell after the switch has usually handed its energy to its
  neighbours, and calling that a loss double-counts it as both gone and
  available. :func:`refuse_transferred_energy_as_loss` refuses.
* **energy cannot be hidden in a discarded basis.** If the reported modal
  fractions do not sum to one, some of the projection was thrown away and
  the remainder was renormalised over what was kept.
  :func:`refuse_hidden_basis_energy` checks the sum and refuses.

**Layer two: the electromagnetic ledger.** With ``E_input = integral of
V*I dt`` on one side, and the field-energy change, Joule heating,
mechanical energy, acoustic radiation, radiated electromagnetic energy,
recovered energy and the **switching work** on the other,

    E_unclosed = E_input - (dE_field + E_Joule + E_mech + E_acoustic
                            + E_radiated + E_recovered + W_switching)

:func:`ledger` returns every term with its own status and its own sigma,
propagates the sigmas in quadrature, and reports ``E_unclosed`` **as an
interval**, never as a number. That is the whole discipline of this
layer, because:

* **the residual here is UNMEASURED.** No voltage, current, temperature
  or acoustic power has been recorded in this repository, so every term
  defaults to ``BLOCKED_MISSING_DATA`` with an unbounded sigma and the
  interval on ``E_unclosed`` trivially includes zero. A residual whose
  interval spans zero is a statement about calibration, not a discovery,
  and :func:`refuse_unknown_channel_claim` refuses the promotion.
* **boundary and switching work is a ledger term, not a footnote.**
  Omitting it leaves a residual exactly equal to it, which is how the
  term is shown to have teeth; :func:`refuse_ignored_switching_work`
  refuses a ledger written without it.

The modal machinery is reused from :mod:`r11.mechboundary` rather than
rebuilt: the same mass-normalised projection, the same continuity rule at
a sudden change, the same closed-form boundary work. Nothing here is
measured.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

import numpy as np

from r11.mechboundary import (
    MechBoundaryError,
    MechSystem,
    Modes,
    Snapshot,
    State,
    apply_sudden,
    energy,
    modes,
    project,
    work_done_by_boundary,
)

# --- verdict, claim vocabulary, tolerances --------------------------------

#: The standing verdict for this module.
VERDICT = "ENERGY_LEDGER_CLOSES_RESIDUAL_UNMEASURED"

#: The typed claim vocabulary, exact strings, shared across R11.
CLAIM_CLASSES: tuple[str, ...] = (
    "EXACT_IDENTITY",
    "SOURCE_ESTABLISHED_PHYSICS",
    "REPOSITORY_COMPUTATIONAL_RESULT",
    "ENGINEERING_CANDIDATE",
    "RETROSPECTIVE_NUMERIC_MATCH",
    "PROSPECTIVE_PREDICTION",
    "BENCH_MEASUREMENT",
    "UNSUPPORTED",
    "BLOCKED_MISSING_DATA",
)

SOURCE_ESTABLISHED_PHYSICS = "SOURCE_ESTABLISHED_PHYSICS"
REPOSITORY_COMPUTATIONAL_RESULT = "REPOSITORY_COMPUTATIONAL_RESULT"
BLOCKED_MISSING_DATA = "BLOCKED_MISSING_DATA"

#: The claim class of this module as a whole: arithmetic on declared
#: models, with a residual that no bench has bounded.
CLAIM_CLASS = REPOSITORY_COMPUTATIONAL_RESULT

MEASURED_HERE = "nothing"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: Tolerance on ``sum(modal fractions) == 1``.
FRACTION_TOL = 1e-9

#: Relative tolerance on the mechanical energy identities.
ENERGY_TOL = 1e-9

#: Default coverage factor for the reported residual interval (2 sigma).
DEFAULT_K_SIGMA = 2.0

#: A sigma of ``None`` means the term is not calibrated at all: its
#: uncertainty is unbounded, not zero.
UNBOUNDED = None


class EnergyLedgerError(RuntimeError):
    """Raised when an energy statement exceeds what the accounting licenses.

    Covers the structural guards (a non-positive Q, mismatched matrices),
    the two basis attacks (:func:`refuse_transferred_energy_as_loss`,
    :func:`refuse_hidden_basis_energy`) and the two ledger attacks
    (:func:`refuse_unknown_channel_claim`,
    :func:`refuse_ignored_switching_work`).
    """


# --- (1) classical mode energy and the damping convention -----------------

def mode_omega(m: float, k: float) -> float:
    """``omega = sqrt(k/m)`` for one mode. Both must be positive."""
    if float(m) <= 0.0:
        raise EnergyLedgerError("modal mass must be positive")
    if float(k) <= 0.0:
        raise EnergyLedgerError("modal stiffness must be positive")
    return math.sqrt(float(k) / float(m))


def mode_energy(m: float, qdot: float, k: float, q: float) -> float:
    """``E_i = 0.5*m*qdot**2 + 0.5*k*q**2``.

    Kinetic plus potential for one mode, in its own coordinate. At the
    turning point (``qdot == 0``) this is ``0.5*k*q**2``, and because
    ``k = m*omega**2`` it is also ``0.5*m*(omega*q)**2`` -- the same
    number by two routes, which is what makes the modal energy a
    coordinate-independent statement about the mode rather than about the
    normalisation.
    """
    if float(m) <= 0.0:
        raise EnergyLedgerError("modal mass must be positive")
    if float(k) < 0.0:
        raise EnergyLedgerError("modal stiffness cannot be negative")
    return float(0.5 * float(m) * float(qdot) ** 2
                 + 0.5 * float(k) * float(q) ** 2)


def _check_decay(omega: float, q_factor: float, t: float) -> tuple[float, ...]:
    w, q, time = float(omega), float(q_factor), float(t)
    if w <= 0.0:
        raise EnergyLedgerError("omega must be positive")
    if q <= 0.0:
        raise EnergyLedgerError(
            "the quality factor must be positive; Q <= 0 is not a lossy "
            "oscillator, it is a source")
    if time < 0.0:
        raise EnergyLedgerError("time cannot be negative")
    return (w, q, time)


def energy_decay_rate(omega: float, q_factor: float) -> float:
    """``omega/Q``: the exponential rate at which *energy* decays."""
    w, q, _ = _check_decay(omega, q_factor, 0.0)
    return w / q


def amplitude_decay_rate(omega: float, q_factor: float) -> float:
    """``omega/(2Q)``: the exponential rate at which *amplitude* decays."""
    w, q, _ = _check_decay(omega, q_factor, 0.0)
    return w / (2.0 * q)


def decay_rate_ratio(omega: float = 1.0, q_factor: float = 100.0) -> float:
    """Energy decay rate divided by amplitude decay rate. Computed.

    It is 2 for every positive ``omega`` and ``Q``, because energy is
    quadratic in amplitude. The value is divided out here rather than
    written down, so a change to either formula shows up as a change to
    this number.
    """
    return (energy_decay_rate(omega, q_factor)
            / amplitude_decay_rate(omega, q_factor))


def damped_mode_energy(e0: float, omega: float, q_factor: float,
                       t: float) -> float:
    """``E_i(t) = E_i(0) * exp(-omega*t/Q)``. The ENERGY decay."""
    w, q, time = _check_decay(omega, q_factor, t)
    if float(e0) < 0.0:
        raise EnergyLedgerError("a mode cannot start with negative energy")
    return float(e0) * math.exp(-w * time / q)


def damped_amplitude(a0: float, omega: float, q_factor: float,
                     t: float) -> float:
    """``a(t) = a(0) * exp(-omega*t/(2Q))``. The AMPLITUDE decay.

    Half the exponent of :func:`damped_mode_energy`, because energy goes
    as amplitude squared. Squaring this ratio reproduces the energy ratio
    identically, which is the check :func:`damping_convention` reports.
    """
    w, q, time = _check_decay(omega, q_factor, t)
    return float(a0) * math.exp(-w * time / (2.0 * q))


#: Below this Q the "lightly damped" reading of Q as omega/(decay rate)
#: stops being the standard one: Q = 1/2 is critical damping, and there
#: is no oscillation left to have a ringdown.
LIGHT_DAMPING_MIN_Q = 0.5


def damping_convention(omega: float = 1.0, q_factor: float = 100.0,
                       t: float = 1.0) -> dict:
    """State the damping convention explicitly, and check it numerically.

    The convention carried throughout this module:

    * ``E(t) = E0 * exp(-omega*t/Q)`` -- energy, decay rate ``omega/Q``,
      time constant ``Q/omega``;
    * ``a(t) = a0 * exp(-omega*t/(2Q))`` -- amplitude, decay rate
      ``omega/(2Q)``, time constant ``2Q/omega``;
    * therefore ``E(t)/E0 == (a(t)/a0)**2`` identically, and the two
      decay **rates differ by a factor of exactly 2**.

    This is the lightly damped convention (``Q >> 1/2``), in which
    ``1/Q`` is the loss angle and the fractional energy lost per radian
    of oscillation. It is *not* interchangeable with a convention that
    puts ``exp(-omega*t/Q)`` on the amplitude: that one loses energy
    twice as fast, and quoting a ringdown constant from one convention
    into the other is a factor-of-two error in every energy in the
    ledger.
    """
    w, q, time = _check_decay(omega, q_factor, t)
    e_ratio = damped_mode_energy(1.0, w, q, time)
    a_ratio = damped_amplitude(1.0, w, q, time)
    return {
        "energy_law": "E(t) = E0 * exp(-omega*t/Q)",
        "amplitude_law": "a(t) = a0 * exp(-omega*t/(2*Q))",
        "energy_decay_rate": energy_decay_rate(w, q),
        "amplitude_decay_rate": amplitude_decay_rate(w, q),
        "rate_ratio_energy_over_amplitude": decay_rate_ratio(w, q),
        "rate_ratio_is_two": abs(decay_rate_ratio(w, q) - 2.0) <= ENERGY_TOL,
        "energy_time_constant_s": q / w,
        "amplitude_time_constant_s": 2.0 * q / w,
        "energy_ratio_at_t": e_ratio,
        "amplitude_ratio_at_t": a_ratio,
        "energy_is_amplitude_squared":
            abs(e_ratio - a_ratio ** 2) <= ENERGY_TOL,
        "lightly_damped": q > LIGHT_DAMPING_MIN_Q,
        "critical_damping_q": LIGHT_DAMPING_MIN_Q,
        "one_over_q_is": "the loss angle; the fractional energy lost per "
                         "radian of oscillation",
        "not_interchangeable_with":
            "a convention placing exp(-omega*t/Q) on the AMPLITUDE, which "
            "decays energy twice as fast; mixing the two is a factor-of-2 "
            "error in every energy in the ledger",
        "claim_class": SOURCE_ESTABLISHED_PHYSICS,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
    }


# --- (2) basis switching --------------------------------------------------

def make_system(M: np.ndarray, K: np.ndarray,
                C: np.ndarray | None = None) -> MechSystem:
    """A :class:`r11.mechboundary.MechSystem` from bare matrices."""
    mass = np.asarray(M, dtype=float)
    stiff = np.asarray(K, dtype=float)
    if mass.ndim != 2 or mass.shape[0] != mass.shape[1]:
        raise EnergyLedgerError("M must be a square matrix")
    if stiff.shape != mass.shape:
        raise EnergyLedgerError("K must have the same shape as M")
    damp = (np.zeros_like(mass) if C is None
            else np.asarray(C, dtype=float))
    if damp.shape != mass.shape:
        raise EnergyLedgerError("C must have the same shape as M")
    return MechSystem(mass, stiff, damp)


def system_basis(system: MechSystem) -> Modes:
    """Mass-normalised modes of a system, via :mod:`r11.mechboundary`."""
    try:
        return modes(system.M, system.K)
    except MechBoundaryError as exc:
        raise EnergyLedgerError(str(exc)) from exc


def modal_fractions(energies: np.ndarray) -> np.ndarray:
    """Per-mode share of the total modal energy. Sums to one by construction."""
    e = np.asarray(energies, dtype=float)
    if e.ndim != 1 or e.size == 0:
        raise EnergyLedgerError("modal energies must be a non-empty vector")
    if np.any(e < -ENERGY_TOL):
        raise EnergyLedgerError("a mode cannot carry negative energy")
    total = float(np.sum(e))
    if total <= 0.0:
        raise EnergyLedgerError(
            "a state with no energy has no modal energy fractions")
    return e / total


@dataclass(frozen=True)
class BasisSwitch:
    """What one basis switch did to the energy, mode by mode.

    ``energy_before`` and ``energy_after`` are physical energies in nodal
    coordinates; ``modal_energies`` is the same post-switch state read in
    the post-switch eigenbasis, and it sums to ``energy_after`` because
    the basis is mass-normalised. ``switching_work`` is evaluated from
    the parameter change itself -- not as a residual -- so
    ``energy_before + switching_work == energy_after`` is a check rather
    than a definition.
    """

    omega_before: np.ndarray
    omega_after: np.ndarray
    energy_before: float
    energy_after: float
    switching_work: float
    modal_energies: np.ndarray
    state_after: State

    @property
    def fractions(self) -> np.ndarray:
        return modal_fractions(self.modal_energies)

    @property
    def modal_total(self) -> float:
        return float(np.sum(self.modal_energies))

    @property
    def projection_defect(self) -> float:
        """``|sum(modal energies) - E_after|``, relative. Zero if nothing hid."""
        scale = max(1.0, abs(self.energy_after))
        return abs(self.modal_total - self.energy_after) / scale

    @property
    def closes(self) -> bool:
        """``E_after == E_before + W_switching`` to tolerance."""
        scale = max(1.0, abs(self.energy_before), abs(self.energy_after))
        residual = self.energy_after - (self.energy_before
                                        + self.switching_work)
        return abs(residual) <= ENERGY_TOL * scale

    def as_dict(self) -> dict:
        return {
            "omega_before": self.omega_before.tolist(),
            "omega_after": self.omega_after.tolist(),
            "energy_before": self.energy_before,
            "energy_after": self.energy_after,
            "switching_work": self.switching_work,
            "modal_energies": self.modal_energies.tolist(),
            "modal_fractions": self.fractions.tolist(),
            "modal_fractions_sum": float(np.sum(self.fractions)),
            "modal_total": self.modal_total,
            "projection_defect": self.projection_defect,
            "mechanical_identity": "E_after == E_before + W_switching",
            "closes": self.closes,
            "claim_class": REPOSITORY_COMPUTATIONAL_RESULT,
            "measured_here": MEASURED_HERE,
        }


def switch_basis(state: State, before: MechSystem,
                 after: MechSystem) -> BasisSwitch:
    """Switch the basis at an instant and account for every resulting mode.

    Displacement ``u`` is continuous and so is momentum ``p = M v``: the
    forces stay bounded through the switch, so no impulse is delivered.
    When the mass matrix changes the velocity therefore jumps, and the
    kinetic energy jumps with it -- that jump is work done by whatever
    performed the switch, and it is booked, not absorbed.

    The post-switch state is then projected into the post-switch
    eigenbasis. Because that basis is mass-normalised, the per-mode
    energies sum to the physical energy exactly; a shortfall would mean a
    mode was dropped, which is the attack
    :func:`refuse_hidden_basis_energy` exists to catch.
    """
    if not isinstance(state, State):
        raise EnergyLedgerError("state must be a mechboundary.State")
    basis_before = system_basis(before)
    basis_after = system_basis(after)
    if basis_before.n != basis_after.n:
        raise EnergyLedgerError(
            "the two systems have different dimensions; a basis switch "
            "does not add or remove degrees of freedom")
    try:
        end = apply_sudden(state, before, after)
        e_before = energy(state, before.M, before.K)
        e_after = energy(end, after.M, after.K)
        work = work_done_by_boundary(Snapshot(before, state),
                                     Snapshot(after, end))
        modal = project(end, basis_after)
    except MechBoundaryError as exc:
        raise EnergyLedgerError(str(exc)) from exc
    return BasisSwitch(
        omega_before=basis_before.omega,
        omega_after=basis_after.omega,
        energy_before=float(e_before),
        energy_after=float(e_after),
        switching_work=float(work),
        modal_energies=np.asarray(modal.energies, dtype=float),
        state_after=end,
    )


def refuse_transferred_energy_as_loss(
        from_mode: int = 0, to_modes: object = None,
        transferred: float = 0.0,
        claim: str = "the mode lost this energy") -> None:
    """Refuse energy that moved between modes being booked as loss.

    Always raises. When the basis moves, a mode that was carrying the
    whole state is re-expressed over several modes of the new system.
    Its own occupation falls, and every joule of the difference is
    sitting in its neighbours -- still mechanical, still in the same
    structure, still available. Calling that a loss counts it twice: once
    as dissipated and once as present, which is how an apparent deficit
    is manufactured and then attributed to an unknown channel.

    Loss has a different signature entirely: it is the work done against
    the dashpots, ``integral of v^T C v dt``, and it lowers the *total*
    over all modes, not the share of one.
    """
    where = "" if to_modes is None else f" (it is in modes {to_modes})"
    raise EnergyLedgerError(
        f"refused: {claim!r} for mode {from_mode} with "
        f"{float(transferred):g} J of transfer{where}. Energy moved to "
        f"another mode of the same structure is NOT loss: the modal basis "
        f"changed, the state was re-expressed over it, and the total over "
        f"all modes is unchanged by the projection. Booking a transfer as "
        f"a loss counts the same joules twice -- once as gone and once as "
        f"still ringing -- and the deficit that produces is arithmetic, "
        f"not a channel. Dissipation is integral(v^T C v dt) and it "
        f"reduces the TOTAL; check sum(modal_energies) before calling "
        f"anything lost. {VERDICT}")


def refuse_hidden_basis_energy(fractions: object,
                               tol: float = FRACTION_TOL,
                               context: str = "") -> float:
    """Refuse modal fractions that do not sum to one.

    Returns the sum when it is one to within ``tol``, so callers can use
    it as a guard. Raises otherwise: a fraction set that sums to less
    than one has discarded part of the projection, and one that sums to
    more has renormalised over a subset while still calling the entries
    fractions of the whole. Either way the missing share is available to
    be re-described later as a deficit, which is exactly the move this
    refusal blocks.
    """
    f = np.asarray(list(fractions), dtype=float)
    if f.ndim != 1 or f.size == 0:
        raise EnergyLedgerError("modal fractions must be a non-empty vector")
    if float(tol) <= 0.0:
        raise EnergyLedgerError("tolerance must be positive")
    if np.any(f < -float(tol)):
        raise EnergyLedgerError(
            "a modal energy fraction cannot be negative; a negative share "
            "of a positive total is a projection error, not a physical "
            "state")
    total = float(np.sum(f))
    if abs(total - 1.0) > float(tol):
        where = f" ({context})" if context else ""
        raise EnergyLedgerError(
            f"refused: {f.size} modal fractions sum to {total!r}, not 1 "
            f"(deficit {1.0 - total!r}, tolerance {float(tol)!r}){where}. "
            f"The post-switch eigenbasis is complete and mass-normalised, "
            f"so the fractions of a fully projected state sum to one by "
            f"construction. A shortfall means modes were dropped from the "
            f"report and their energy is sitting in a discarded basis, "
            f"where it can later be re-described as a missing channel. "
            f"Project onto the whole basis or do not call the entries "
            f"fractions. {VERDICT}")
    return total


# --- (3) the electromagnetic ledger ---------------------------------------

class LedgerRole(Enum):
    """Which side of the ledger a term sits on."""

    INPUT = "INPUT"
    OUTPUT = "OUTPUT"


#: Every output term, in the order they are reported. ``switching_work``
#: is last because it is the one most often left out.
OUTPUT_TERMS: tuple[str, ...] = (
    "delta_e_field",
    "e_joule",
    "e_mechanical",
    "e_acoustic",
    "e_radiated",
    "e_recovered",
    "switching_work",
)

LEDGER_TERMS: tuple[str, ...] = ("e_input",) + OUTPUT_TERMS

TERM_MEANINGS: dict[str, str] = {
    "e_input": "integral of V*I dt at the drive terminals: everything the "
               "supply delivered",
    "delta_e_field": "change in stored electromagnetic field energy, "
                     "coil and electrode, between the two instants",
    "e_joule": "resistive dissipation in windings, leads, electrodes and "
               "switch, measured as heat or inferred from I^2 R",
    "e_mechanical": "energy stored in the resonator's mechanical modes, "
                    "summed over the WHOLE basis",
    "e_acoustic": "energy radiated acoustically into mounts, leads and "
                  "the surrounding medium",
    "e_radiated": "electromagnetic energy radiated away, including the "
                  "broadband content of the switching transient",
    "e_recovered": "energy returned to the supply or to a snubber rather "
                   "than dissipated",
    "switching_work": "work done by the agent that performed the "
                      "interruption, on the field and on the structure; "
                      "a term, not a footnote",
}


@dataclass(frozen=True)
class LedgerTerm:
    """One line of the ledger: a value, a sigma, a status and a role.

    ``sigma is None`` means the term is **not calibrated**: its
    uncertainty is unbounded rather than zero, and a ledger containing
    one cannot bound its residual at all.
    """

    name: str
    value: float
    sigma: float | None = UNBOUNDED
    status: str = BLOCKED_MISSING_DATA
    role: LedgerRole = LedgerRole.OUTPUT

    def __post_init__(self) -> None:
        if self.name not in LEDGER_TERMS:
            raise EnergyLedgerError(f"{self.name!r} is not a ledger term")
        if not math.isfinite(float(self.value)):
            raise EnergyLedgerError(f"{self.name}: value must be finite")
        if self.sigma is not None:
            s = float(self.sigma)
            if not math.isfinite(s) or s < 0.0:
                raise EnergyLedgerError(
                    f"{self.name}: sigma must be finite and non-negative, "
                    f"or None for an uncalibrated term")
        if self.status not in CLAIM_CLASSES:
            raise EnergyLedgerError(
                f"{self.name}: {self.status!r} is not a declared claim class")

    @property
    def calibrated(self) -> bool:
        return self.sigma is not None

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "meaning": TERM_MEANINGS[self.name],
            "value_j": float(self.value),
            "sigma_j": None if self.sigma is None else float(self.sigma),
            "calibrated": self.calibrated,
            "status": self.status,
            "role": self.role.value,
        }


def electrical_input_energy(voltage: object, current: object,
                            dt: float | None = None,
                            times: object = None) -> float:
    """``E_input = integral of V*I dt``, by the trapezoid rule.

    Either a uniform ``dt`` or an explicit ``times`` array must be given.
    For constant ``V`` and ``I`` over a duration ``T`` this returns
    ``V*I*T`` exactly, which is the check that the quadrature is the
    integral and not a sum.
    """
    v = np.asarray(voltage, dtype=float).ravel()
    i = np.asarray(current, dtype=float).ravel()
    if v.size != i.size:
        raise EnergyLedgerError(
            "voltage and current must be sampled together")
    if v.size < 2:
        raise EnergyLedgerError(
            "an integral needs at least two samples")
    power = v * i
    if times is not None:
        t = np.asarray(times, dtype=float).ravel()
        if t.size != v.size:
            raise EnergyLedgerError(
                "times must have one entry per sample")
        if np.any(np.diff(t) <= 0.0):
            raise EnergyLedgerError("times must ascend strictly")
        widths = np.diff(t)
    else:
        if dt is None:
            raise EnergyLedgerError("give either dt or times")
        step = float(dt)
        if not math.isfinite(step) or step <= 0.0:
            raise EnergyLedgerError("dt must be finite and positive")
        widths = np.full(v.size - 1, step)
    return float(np.sum(0.5 * (power[:-1] + power[1:]) * widths))


def ledger(e_input: float = 0.0, *,
           delta_e_field: float = 0.0,
           e_joule: float = 0.0,
           e_mechanical: float = 0.0,
           e_acoustic: float = 0.0,
           e_radiated: float = 0.0,
           e_recovered: float = 0.0,
           switching_work: float = 0.0,
           sigmas: dict | None = None,
           include_switching_work: bool = True,
           k_sigma: float = DEFAULT_K_SIGMA,
           calibrated_status: str = REPOSITORY_COMPUTATIONAL_RESULT) -> dict:
    """The electromagnetic ledger, with an interval on the residual.

    ``E_unclosed = E_input - sum(calibrated outputs)``, where the outputs
    are the field-energy change, Joule heating, mechanical energy,
    acoustic radiation, radiated electromagnetic energy, recovered energy
    and the switching work.

    Every term carries its own sigma. A term whose sigma is ``None`` is
    **uncalibrated**: its uncertainty is unbounded, so the interval on
    ``E_unclosed`` is unbounded too and the ledger's closure is vacuous.
    That is the default here, because no bench data exists in this
    repository -- every term then has status ``BLOCKED_MISSING_DATA``.
    With sigmas supplied, they are propagated in quadrature and the
    residual is reported as ``E_unclosed +/- k_sigma * sigma``.

    ``include_switching_work=False`` is the deliberate omission: drop the
    term that pays for the interruption and the residual becomes exactly
    that work, which is how the term is shown to be load-bearing rather
    than decorative.
    """
    if float(k_sigma) <= 0.0:
        raise EnergyLedgerError("the coverage factor must be positive")
    if calibrated_status not in CLAIM_CLASSES:
        raise EnergyLedgerError(
            f"{calibrated_status!r} is not a declared claim class")
    values = {
        "e_input": float(e_input),
        "delta_e_field": float(delta_e_field),
        "e_joule": float(e_joule),
        "e_mechanical": float(e_mechanical),
        "e_acoustic": float(e_acoustic),
        "e_radiated": float(e_radiated),
        "e_recovered": float(e_recovered),
        "switching_work": float(switching_work),
    }
    supplied = dict(sigmas or {})
    unknown = set(supplied) - set(LEDGER_TERMS)
    if unknown:
        raise EnergyLedgerError(
            f"unknown ledger term(s) in sigmas: {sorted(unknown)}")

    terms: list[LedgerTerm] = []
    for name in LEDGER_TERMS:
        sigma = supplied.get(name, UNBOUNDED)
        status = (BLOCKED_MISSING_DATA if sigma is None
                  else calibrated_status)
        role = (LedgerRole.INPUT if name == "e_input"
                else LedgerRole.OUTPUT)
        terms.append(LedgerTerm(name, values[name], sigma, status, role))

    included = [t for t in terms
                if include_switching_work or t.name != "switching_work"]
    outputs_total = sum(t.value for t in included
                        if t.role is LedgerRole.OUTPUT)
    e_unclosed = values["e_input"] - outputs_total

    uncalibrated = [t.name for t in included if not t.calibrated]
    if uncalibrated:
        sigma_unclosed: float | None = None
        lo, hi = (-math.inf, math.inf)
    else:
        sigma_unclosed = math.sqrt(sum(float(t.sigma) ** 2   # type: ignore[arg-type]
                                       for t in included))
        half = float(k_sigma) * sigma_unclosed
        lo, hi = (e_unclosed - half, e_unclosed + half)

    includes_zero = bool(lo <= 0.0 <= hi)
    return {
        "identity": ("E_unclosed = E_input - (delta_E_field + E_Joule + "
                     "E_mechanical + E_acoustic + E_radiated + "
                     "E_recovered + W_switching)"),
        "terms": [t.as_dict() for t in terms],
        "term_names": list(LEDGER_TERMS),
        "e_input_j": values["e_input"],
        "outputs_total_j": float(outputs_total),
        "e_unclosed_j": float(e_unclosed),
        "sigma_unclosed_j": sigma_unclosed,
        "k_sigma": float(k_sigma),
        "e_unclosed_interval_j": (lo, hi),
        "interval_includes_zero": includes_zero,
        "closes": includes_zero,
        "closure_is_vacuous": bool(uncalibrated),
        "uncalibrated_terms": uncalibrated,
        "all_terms_blocked": all(
            t.status == BLOCKED_MISSING_DATA for t in terms),
        "switching_work_included": bool(include_switching_work),
        "switching_work_j": values["switching_work"],
        "residual_is_evidence_of_unknown_channel": False,
        "residual_status": (BLOCKED_MISSING_DATA if uncalibrated
                            else calibrated_status),
        "claim_class": (BLOCKED_MISSING_DATA if uncalibrated
                        else calibrated_status),
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "note": (
            "E_unclosed is reported as an interval. An interval that "
            "spans zero is a statement about how well the terms are "
            "calibrated, not a discovery of a channel; an interval that "
            "excludes zero with every term calibrated and the switching "
            "work included is a calibration fault until proven otherwise"),
        "verdict": VERDICT,
    }


def blocked_ledger() -> dict:
    """The ledger as it actually stands here: every term missing data.

    No voltage, current, temperature, acoustic power or radiated power
    has been recorded, so every term is ``BLOCKED_MISSING_DATA`` with an
    unbounded sigma. ``E_unclosed`` is zero over an unbounded interval,
    which trivially includes zero -- and says nothing at all, which is the
    honest reading.
    """
    return ledger()


def refuse_unknown_channel_claim(e_unclosed: float = 0.0,
                                 interval: tuple = (-math.inf, math.inf),
                                 claimed_channel: str = "an unknown channel",
                                 ) -> None:
    """Refuse a residual being promoted to a discovery. Always raises.

    A non-zero ``E_unclosed`` whose interval spans zero is consistent
    with zero, and "consistent with zero" is a calibration statement.
    Promoting it to a channel requires the opposite of what is available
    here: every term calibrated, the switching work included, the
    interval excluding zero by a stated margin, and the excess surviving
    the controls that would produce the same residual from an
    uncalibrated shunt, an unlogged thermal path or a missing radiated
    term.
    """
    lo, hi = (float(interval[0]), float(interval[1]))
    spans = lo <= 0.0 <= hi
    raise EnergyLedgerError(
        f"refused: attributing E_unclosed = {float(e_unclosed):g} J to "
        f"{claimed_channel!r}. The reported interval is [{lo:g}, {hi:g}], "
        f"which {'includes' if spans else 'excludes'} zero. A residual is "
        f"the part of the ledger the calibration does not yet account "
        f"for; it becomes evidence only when every term is calibrated, "
        f"the switching work is included, the interval excludes zero by a "
        f"stated margin, and an uncalibrated shunt, an unlogged thermal "
        f"path and a missing radiated term have each been ruled out. "
        f"None of that holds here: every ledger term in this repository "
        f"is {BLOCKED_MISSING_DATA}, so the residual is UNMEASURED and "
        f"cannot be a discovery. {VERDICT}")


def refuse_ignored_switching_work(
        ledger_result: dict | None = None,
        claim: str = "the ledger closes without switching work") -> None:
    """Refuse a ledger written without the switching-work term. Always raises.

    Interrupting a driven resonator is not free. Collapsing a coil field,
    opening a switch against a current, and changing a boundary condition
    while the structure is moving all do work, and that work appears in
    the accounts on the output side. Leave it out and the residual is
    exactly its size -- a deficit produced by the bookkeeping, ready to be
    re-described as an unknown channel.
    """
    missing = ""
    if isinstance(ledger_result, dict):
        w = ledger_result.get("switching_work_j")
        r = ledger_result.get("e_unclosed_j")
        included = ledger_result.get("switching_work_included")
        missing = (f" The supplied ledger reports W_switching = {w!r} J, "
                   f"included = {included!r}, residual = {r!r} J.")
    raise EnergyLedgerError(
        f"refused: {claim!r}. Switching and boundary work is a ledger "
        f"TERM, not a footnote: collapsing a coil field, opening a switch "
        f"against a current, and changing a boundary condition while the "
        f"structure is moving all do work on the system, and that work "
        f"has to appear on the output side.{missing} Omit it and the "
        f"residual is exactly its size -- a deficit manufactured by the "
        f"bookkeeping and then available to be called a channel. "
        f"Include switching_work, or do not call the result a ledger. "
        f"{VERDICT}")


# --- (4) the power control ------------------------------------------------

#: A synthetic ledger whose terms are chosen so the books close exactly.
#: Every number is a model value in joules, not a measurement. The values
#: are dyadic rationals, so the closure is exact in binary64 rather than
#: exact to within a tolerance -- a ledger that closes "to 1e-12" cannot
#: distinguish a missing term of 1e-12 from arithmetic.
SYNTHETIC_TERMS: dict[str, float] = {
    "delta_e_field": 1.25,
    "e_joule": 3.50,
    "e_mechanical": 2.00,
    "e_acoustic": 0.75,
    "e_radiated": 0.25,
    "e_recovered": 1.25,
    "switching_work": 1.00,
}

SYNTHETIC_INPUT = float(sum(SYNTHETIC_TERMS.values()))     # 10.00 J exactly


def synthetic_ledger(include_switching_work: bool = True,
                     sigma: float = 0.0) -> dict:
    """A ledger with known terms, for the power control.

    With every sigma zero and the switching work included, the residual
    is exactly zero. Omit the switching work and the residual is exactly
    the switching work -- neither approximately, nor to a tolerance. That
    is the point of the control: the ledger has teeth, and the missing
    term is the whole of the deficit.
    """
    if float(sigma) < 0.0:
        raise EnergyLedgerError("sigma cannot be negative")
    sigmas = {name: float(sigma) for name in LEDGER_TERMS}
    return ledger(SYNTHETIC_INPUT, sigmas=sigmas,
                  include_switching_work=include_switching_work,
                  **SYNTHETIC_TERMS)


def power_check() -> dict:
    """Run the power control both ways and report what each leaves."""
    closed = synthetic_ledger(True)
    omitted = synthetic_ledger(False)
    return {
        "synthetic_input_j": SYNTHETIC_INPUT,
        "synthetic_terms_j": dict(SYNTHETIC_TERMS),
        "closed_residual_j": closed["e_unclosed_j"],
        "closed_closes": closed["closes"],
        "closed_is_vacuous": closed["closure_is_vacuous"],
        "omitted_residual_j": omitted["e_unclosed_j"],
        "omitted_closes": omitted["closes"],
        "omitted_residual_equals_switching_work":
            omitted["e_unclosed_j"] == SYNTHETIC_TERMS["switching_work"],
        "claim_class": REPOSITORY_COMPUTATIONAL_RESULT,
        "note": ("the ledger closes exactly when every term is present, "
                 "and omitting the switching work leaves a residual "
                 "exactly equal to it; the detector is therefore sensitive "
                 "to a missing term of that size"),
        "measured_here": MEASURED_HERE,
    }


# --- (5) report ------------------------------------------------------------

def energyledger_report() -> dict:
    """The standing statement of what this module is and is not."""
    blocked = blocked_ledger()
    return {
        "what_this_is": (
            "energy accounting for interrupted phonon and photon-like "
            "states: classical modal energy with an explicit damping "
            "convention, a basis switch that preserves displacement and "
            "momentum and accounts for every resulting mode, and an "
            "electromagnetic ledger that reports its residual as an "
            "interval"),
        "damping_convention": damping_convention(),
        "mechanical_identity": "E_after == E_before + W_switching",
        "ledger_identity": blocked["identity"],
        "ledger_terms": {name: TERM_MEANINGS[name] for name in LEDGER_TERMS},
        "ledger_as_it_stands": {
            "e_unclosed_j": blocked["e_unclosed_j"],
            "sigma_unclosed_j": blocked["sigma_unclosed_j"],
            "e_unclosed_interval_j": blocked["e_unclosed_interval_j"],
            "interval_includes_zero": blocked["interval_includes_zero"],
            "closure_is_vacuous": blocked["closure_is_vacuous"],
            "all_terms_blocked": blocked["all_terms_blocked"],
            "residual_status": blocked["residual_status"],
        },
        "power_control": power_check(),
        "reused_from_mechboundary": [
            "modes", "project", "apply_sudden", "work_done_by_boundary",
            "State", "MechSystem", "Snapshot"],
        "refusals": [
            "refuse_transferred_energy_as_loss",
            "refuse_hidden_basis_energy",
            "refuse_unknown_channel_claim",
            "refuse_ignored_switching_work",
        ],
        "firewalls": [
            "energy moved to another mode is not energy lost",
            "modal fractions that do not sum to one have hidden energy "
            "in a discarded basis",
            "switching and boundary work is a ledger term, and omitting "
            "it manufactures exactly its own size of deficit",
            "a residual whose interval spans zero is a calibration "
            "statement, not a channel",
            "the energy decay rate is omega/Q and the amplitude decay "
            "rate is omega/(2Q); they differ by exactly two",
        ],
        "hardware_status": (
            "BLOCKED_MISSING_DATA - no voltage, current, temperature, "
            "acoustic power or radiated power has been recorded"),
        "claim_class": CLAIM_CLASS,
        "claim_classes": list(CLAIM_CLASSES),
        "evidence_class": "NUMERICAL_SIMULATION",
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "what_would_change_this": (
            "logged V and I at the drive terminals, calorimetry or a "
            "calibrated thermal model for the Joule term, an acoustic "
            "power measurement, a radiated-field measurement, and a "
            "stated sigma on each -- at which point E_unclosed acquires "
            "a bounded interval and the question of whether it excludes "
            "zero becomes answerable"),
        "what_this_does_not_say": (
            "It does not say any energy was measured. Every term of the "
            "electromagnetic ledger is BLOCKED_MISSING_DATA with an "
            "unbounded uncertainty, so E_unclosed is an interval that "
            "includes zero and the ledger's closure is vacuous -- it "
            "closes because nothing constrains it, which is not the same "
            "as closing because it was checked. It does not say a "
            "residual exists, that any channel is missing, or that any "
            "energy is unaccounted for; the only ledgers that close here "
            "numerically are synthetic ones built from declared model "
            "values. It does not say a mode lost energy when a basis "
            "switch moved that energy to its neighbours, and it does not "
            "permit a modal report whose fractions fail to sum to one. "
            "No resonator was driven, interrupted, or rung down."),
        "verdict": VERDICT,
    }


__all__ = [
    "VERDICT", "CLAIM_CLASS", "CLAIM_CLASSES", "BLOCKED_MISSING_DATA",
    "SOURCE_ESTABLISHED_PHYSICS", "REPOSITORY_COMPUTATIONAL_RESULT",
    "MEASURED_HERE", "PHYSICAL_VALIDATION", "FRACTION_TOL", "ENERGY_TOL",
    "DEFAULT_K_SIGMA", "UNBOUNDED", "LIGHT_DAMPING_MIN_Q",
    "EnergyLedgerError",
    "mode_omega", "mode_energy", "energy_decay_rate",
    "amplitude_decay_rate", "decay_rate_ratio", "damped_mode_energy",
    "damped_amplitude", "damping_convention",
    "make_system", "system_basis", "modal_fractions", "BasisSwitch",
    "switch_basis", "refuse_transferred_energy_as_loss",
    "refuse_hidden_basis_energy",
    "LedgerRole", "OUTPUT_TERMS", "LEDGER_TERMS", "TERM_MEANINGS",
    "LedgerTerm", "electrical_input_energy", "ledger", "blocked_ledger",
    "refuse_unknown_channel_claim", "refuse_ignored_switching_work",
    "SYNTHETIC_TERMS", "SYNTHETIC_INPUT", "synthetic_ledger",
    "power_check", "energyledger_report",
]
