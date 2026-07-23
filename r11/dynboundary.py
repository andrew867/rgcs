"""R11 P08 — a time-dependent boundary, and what it actually does to light.

The source picture is a photon that meets a mirror which vanishes
mid-flight, so the photon is "cut", leaving a truncated piece that is no
longer a whole photon and is therefore something new. The field theory
says otherwise, and it says it cleanly.

**A moving or switching boundary applies a Bogoliubov transformation.**
A boundary condition that changes in time mixes the positive- and
negative-frequency parts of the field:

    a_out = alpha * a_in + beta * conj(a_in_dagger),
    |alpha|**2 - |beta|**2 == 1.

That mixing is the whole story. It does not divide a quantum into a
fraction of a quantum; there is no operator that takes a one-photon
state to a state of 0.6 photons. What it does produce is a **multimode
state** whose photon-number sectors run from zero upward: with the input
in vacuum the output is a multimode squeezed vacuum with mean occupation
``<n> = |beta|**2 = sinh(r)**2`` per mode, i.e. real photons appear in
pairs. This is the dynamical Casimir effect, and it has been seen in
superconducting-circuit analogues. A photon incident on such a boundary
is scattered into that same multimode structure — spectrally reshaped,
correlated, sideband-bearing — and the number operator still has integer
eigenvalues.

**Where the energy comes from.** The created photons are not free. The
agent that moves or switches the boundary does work against the field;
:func:`switching_energy_input` books it, and
:func:`refuse_energy_from_nothing` refuses the alternative.

**The divergence is the headline, and it is an idealization.** An
*instantaneous* removal of a perfect boundary has no spectral cutoff, so
it excites arbitrarily high frequencies and the expected photon number
diverges. Model the switching with a finite time ``tau`` and the
spectrum acquires a smooth cutoff: the integral is finite for every
``tau > 0`` and grows without bound as ``tau -> 0``. Slower switching
means fewer photons. The divergence at ``tau == 0`` is therefore a
statement about an impossible boundary, not a supply of free energy —
:func:`refuse_infinite_free_energy` says so.

**The competing mechanisms are modelled separately.** A static mirror or
beamsplitter, ordinary destructive interference, pulse gating, a
time-dependent dielectric, the dynamical Casimir effect proper,
wavepacket truncation, classical spectral broadening and detector
artifacts all produce "the light changed" and are not the same claim.
Static destructive interference in particular **redistributes**
detection probability and energy; it leaves no exotic remainder.

Nothing here is measured. No apparatus exists. The required observables
are listed with status UNMEASURED, and the standing verdict is that a
time-dependent boundary yields an electromagnetic quantum-field state,
not a new particle species.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

import numpy as np

# --- neutral public names ------------------------------------------------

#: Neutral handle for the source claim about a photon "cut" by a
#: disappearing boundary. Used instead of any narrative label.
TRUNCATED_PHOTON_REFERENCE_A = "TRUNCATED_PHOTON_REFERENCE_A"

#: The only name under which a placeholder exotic-particle proposal is
#: exposed. It names a *candidate electromagnetic field state*, not a
#: particle species, and carries no claim that the state is exotic.
DYNAMIC_BOUNDARY_MULTIMODE_STATE_CANDIDATE = (
    "DYNAMIC_BOUNDARY_MULTIMODE_STATE_CANDIDATE")

DEFAULT_VERDICT = "TRUNCATED_PHOTON_IS_MULTIMODE_EM_STATE_NOT_NEW_PARTICLE"

VERDICTS = (
    DEFAULT_VERDICT,
    "SWITCHING_ENERGY_REQUIRED",
    "INSTANTANEOUS_LIMIT_IS_UNPHYSICAL_IDEALIZATION",
    "PHYSICAL_VALIDATION_NOT_CLAIMED",
)

#: Tolerance on the Bogoliubov identity |alpha|**2 - |beta|**2 == 1.
BOGOLIUBOV_TOL = 1e-9

#: Reduced Planck constant, SI (CODATA, exact by the 2019 SI definition
#: of the kilogram via h = 6.62607015e-34 J s).
HBAR_J_S = 6.62607015e-34 / (2.0 * math.pi)


class DynBoundaryError(RuntimeError):
    """Raised when a dynamic-boundary claim exceeds what the model licenses."""


# --- (1) the Bogoliubov transformation ----------------------------------

def bogoliubov_defect(alpha: complex, beta: complex) -> float:
    """``|alpha|**2 - |beta|**2 - 1``: zero for a valid transformation."""
    return float(abs(alpha) ** 2 - abs(beta) ** 2 - 1.0)


def check_bogoliubov(alpha: complex, beta: complex) -> None:
    """Assert the Bogoliubov identity ``|alpha|**2 - |beta|**2 == 1``.

    The identity is canonical-commutator preservation: it is what makes
    ``a_out`` an annihilation operator at all. A pair that violates it
    is not a mode transformation, and no photon-number statement derived
    from it means anything.
    """
    defect = bogoliubov_defect(alpha, beta)
    if abs(defect) > BOGOLIUBOV_TOL:
        raise DynBoundaryError(
            f"|alpha|**2 - |beta|**2 == {1.0 + defect:.12g}, not 1. The "
            f"Bogoliubov identity is the preservation of the canonical "
            f"commutator; without it a_out is not an annihilation "
            f"operator and <n> = |beta|**2 is meaningless.")


def transform_amplitude(alpha: complex, beta: complex,
                        a_in: complex, a_in_dagger: complex) -> complex:
    """``a_out = alpha*a_in + beta*conj(a_in_dagger)``.

    Evaluated on c-number stand-ins for the input mode operators, which
    is enough to exhibit the mixing of positive- and negative-frequency
    parts. The identity is checked first.
    """
    check_bogoliubov(alpha, beta)
    return alpha * a_in + beta * np.conj(a_in_dagger)


def created_photons(beta: complex) -> float:
    """Mean photons created per mode from vacuum: ``<n> = |beta|**2``.

    Zero when ``beta == 0`` (a static boundary creates nothing) and
    positive whenever the boundary mixes frequencies.
    """
    return float(abs(beta) ** 2)


def squeezing_alpha_beta(r: float) -> tuple[float, float]:
    """``(alpha, beta) = (cosh r, sinh r)`` for squeezing parameter ``r``."""
    return (math.cosh(r), math.sinh(r))


def squeezing_photon_number(r: float) -> float:
    """``<n> = sinh(r)**2``: the squeezed-vacuum mean occupation."""
    return math.sinh(r) ** 2


def squeezing_from_photon_number(n: float) -> float:
    """Invert ``<n> = sinh(r)**2`` for ``r >= 0``."""
    if n < 0.0:
        raise DynBoundaryError("mean photon number cannot be negative")
    return math.asinh(math.sqrt(n))


@dataclass(frozen=True)
class BogoliubovMode:
    """One output mode of a switched boundary.

    ``alpha`` and ``beta`` obey the Bogoliubov identity; the constructor
    refuses any pair that does not.
    """

    alpha: complex
    beta: complex

    def __post_init__(self) -> None:
        check_bogoliubov(self.alpha, self.beta)

    @classmethod
    def from_squeezing(cls, r: float) -> "BogoliubovMode":
        alpha, beta = squeezing_alpha_beta(r)
        return cls(alpha, beta)

    @property
    def mean_photon_number(self) -> float:
        return created_photons(self.beta)

    @property
    def squeezing_parameter(self) -> float:
        return squeezing_from_photon_number(self.mean_photon_number)

    def out_amplitude(self, a_in: complex, a_in_dagger: complex) -> complex:
        return transform_amplitude(self.alpha, self.beta, a_in, a_in_dagger)


def photon_number_distribution(r: float, max_pairs: int = 40) -> dict:
    """Photon-number sectors of a single-mode squeezed vacuum.

    ``P(2n) = (2n)! / (4**n (n!)**2) * tanh(r)**(2n) / cosh(r)``, and
    ``P(2n+1) = 0``: the population runs from the zero-photon sector
    upward in *pairs*, with integer occupation throughout. There is no
    fractional-photon sector, which is the point.
    """
    if r < 0.0:
        raise DynBoundaryError("squeezing parameter must be non-negative")
    t = math.tanh(r)
    c = math.cosh(r)
    probs: dict[int, float] = {}
    for n in range(max_pairs + 1):
        weight = math.comb(2 * n, n) / (4.0 ** n)
        probs[2 * n] = weight * (t ** (2 * n)) / c
    return {
        "squeezing_parameter": r,
        "sectors": probs,
        "odd_sectors_are_zero": True,
        "total_probability": float(sum(probs.values())),
        "mean_photon_number": squeezing_photon_number(r),
        "fractional_sectors": {},
        "note": ("photon number is an integer-eigenvalue observable; the "
                 "sectors run 0, 2, 4, ... and none of them is a fraction "
                 "of a photon"),
    }


# --- (2) the divergence, and what a finite switching time does ----------

#: Spectral model. The pair-creation amplitude for a boundary switched
#: over a time ``tau`` is taken as
#: ``beta(omega) = sqrt(coupling * omega) * exp(-omega * tau)``:
#: a mode-density factor times the smooth cutoff that a finite switching
#: time imposes. The functional form is a modelling choice; the
#: tau-dependence of the *conclusion* is not.
DEFAULT_COUPLING = 1.0


def beta_spectrum(omega: float | np.ndarray, tau: float,
                  coupling: float = DEFAULT_COUPLING) -> float | np.ndarray:
    """``beta(omega) = sqrt(coupling*omega) * exp(-omega*tau)``.

    At ``tau == 0`` the cutoff is gone and ``|beta|**2`` grows without
    bound with frequency — that is the instantaneous idealization.
    """
    if tau < 0.0:
        raise DynBoundaryError("switching time cannot be negative")
    if coupling < 0.0:
        raise DynBoundaryError("coupling cannot be negative")
    w = np.asarray(omega, dtype=float)
    if np.any(w < 0.0):
        raise DynBoundaryError("frequency must be non-negative")
    out = np.sqrt(coupling * w) * np.exp(-w * tau)
    return float(out) if np.ndim(omega) == 0 else out


def expected_photon_number(tau: float, omega_max: float | None = None,
                           coupling: float = DEFAULT_COUPLING) -> float:
    """Total expected photons ``\\int |beta(omega)|**2 domega``.

    With the model spectrum this is, over the full band,

        ``<N> = coupling / (4 * tau**2)``,

    which is **finite for every ``tau > 0``**, **decreases monotonically
    as ``tau`` increases** (slower switching, fewer photons), and
    **diverges as ``tau -> 0``**.

    ``tau == 0`` raises :class:`DynBoundaryError`: the instantaneous
    limit has no answer to return. Imposing ``omega_max`` at ``tau == 0``
    would only move the divergence into an arbitrary cutoff parameter,
    so it is refused there too.
    """
    if tau < 0.0:
        raise DynBoundaryError("switching time cannot be negative")
    if coupling < 0.0:
        raise DynBoundaryError("coupling cannot be negative")
    if tau == 0.0:
        raise DynBoundaryError(
            "tau == 0 is an instantaneous boundary change: the spectrum "
            "has no cutoff, arbitrarily high frequencies are excited, and "
            "the expected photon number diverges. The divergence is a "
            "property of an unphysical idealization — no boundary can be "
            "removed in zero time — and a hard omega_max would hide it "
            "behind an arbitrary parameter rather than resolve it. "
            "Supply tau > 0. "
            "INSTANTANEOUS_LIMIT_IS_UNPHYSICAL_IDEALIZATION")
    total = coupling / (4.0 * tau * tau)
    if omega_max is None:
        return float(total)
    if omega_max < 0.0:
        raise DynBoundaryError("omega_max cannot be negative")
    x = 2.0 * tau * omega_max
    return float(total * (1.0 - (1.0 + x) * math.exp(-x)))


def switching_time_sweep(taus: "np.ndarray | list[float]",
                         coupling: float = DEFAULT_COUPLING) -> dict:
    """Expected photon number across a sweep of switching times."""
    t = np.asarray(list(taus), dtype=float)
    if t.size < 2:
        raise DynBoundaryError("a sweep needs at least two switching times")
    n = np.array([expected_photon_number(float(x), coupling=coupling)
                  for x in t])
    order = np.argsort(t)
    ordered = n[order]
    return {
        "tau": t.tolist(),
        "expected_photon_number": n.tolist(),
        "all_finite": bool(np.all(np.isfinite(n))),
        "monotone_decreasing_in_tau": bool(np.all(np.diff(ordered) < 0.0)),
        "note": ("slower switching excites less of the spectrum, so the "
                 "created photon number falls; the instantaneous limit is "
                 "the divergent end of this curve"),
        "measured_here": "nothing",
    }


def divergence_report(tau_small: float = 1e-6,
                      coupling: float = DEFAULT_COUPLING) -> dict:
    """The headline: finite for tau > 0, divergent as tau -> 0."""
    if tau_small <= 0.0:
        raise DynBoundaryError("tau_small must be positive")
    ladder = [tau_small * (10.0 ** k) for k in range(4)]
    return {
        "instantaneous_limit": "DIVERGENT",
        "finite_switching_limit": "FINITE",
        "ladder_tau": ladder,
        "ladder_expected_photons": [
            expected_photon_number(t, coupling=coupling) for t in ladder],
        "scaling": "<N> = coupling / (4 * tau**2)",
        "verdict": "INSTANTANEOUS_LIMIT_IS_UNPHYSICAL_IDEALIZATION",
        "measured_here": "nothing",
    }


def refuse_infinite_free_energy(tau: float = 0.0,
                                claimed_output: str = "unbounded energy",
                                ) -> None:
    """Refuse the divergence as an energy source.

    The ``tau -> 0`` divergence says the model has been pushed outside
    its domain — a boundary that changes in literally zero time does not
    exist, and the field-theoretic idealization that permits it also
    ignores the finite plasma frequency, finite conductivity and finite
    mechanical response of any real mirror. An infinity produced by an
    impossible boundary is not a power supply.
    """
    raise DynBoundaryError(
        f"a claim of {claimed_output!r} from the tau == {tau:g} "
        f"instantaneous-switching divergence is refused. The divergence "
        f"is an UNPHYSICAL IDEALIZATION: it is what the model returns "
        f"when asked about a boundary that changes in zero time, which "
        f"no material can do. Every finite tau gives a finite photon "
        f"number and a finite energy, and that energy is paid for by the "
        f"agent doing the switching. "
        f"INSTANTANEOUS_LIMIT_IS_UNPHYSICAL_IDEALIZATION")


# --- (3) energy accounting ----------------------------------------------

def switching_energy_input(tau: float, coupling: float = DEFAULT_COUPLING,
                           hbar: float = HBAR_J_S) -> dict:
    """Energy the switching agent must supply, ``\\int hbar*omega*|beta|**2``.

    With the model spectrum this is ``hbar * coupling / (4 * tau**3)``:
    finite for every ``tau > 0``, and larger the faster the boundary is
    switched. The created photons carry exactly this energy, and it is
    work done by whatever moves or switches the boundary — a piston, a
    SQUID bias, a pump beam. Nothing is created from nothing.
    """
    if tau <= 0.0:
        raise DynBoundaryError(
            "energy accounting requires a finite switching time; tau <= 0 "
            "is the divergent idealization, not a bench configuration")
    if coupling < 0.0:
        raise DynBoundaryError("coupling cannot be negative")
    photons = expected_photon_number(tau, coupling=coupling)
    energy = hbar * coupling / (4.0 * tau ** 3)
    return {
        "switching_time_s": tau,
        "expected_photon_number": photons,
        "field_energy_j": energy,
        "energy_source": (
            "work done by the agent that moves or switches the boundary"),
        "balance": "field energy gained == work done on the boundary",
        "net_gain_available": False,
        "verdict": "SWITCHING_ENERGY_REQUIRED",
        "measured_here": "nothing",
    }


def refuse_energy_from_nothing(claimed_source: str = "the vacuum") -> None:
    """Refuse photon creation without a payer."""
    raise DynBoundaryError(
        f"photons created at a time-dependent boundary cannot be charged "
        f"to {claimed_source!r}. The dynamical Casimir effect converts "
        f"work done on the boundary into field excitations; the boundary "
        f"experiences a back-action force and the agent driving it does "
        f"the work. A ledger with created photons on one side and no "
        f"input on the other is not an energy balance. "
        f"SWITCHING_ENERGY_REQUIRED")


# --- (4) competing mechanisms, modelled separately -----------------------

class Mechanism(Enum):
    """Distinct physical routes to "the light changed". Not interchangeable."""

    STATIC_MIRROR_OR_BEAMSPLITTER = "static_mirror_or_beamsplitter"
    ORDINARY_DESTRUCTIVE_INTERFERENCE = "ordinary_destructive_interference"
    PULSE_GATING = "pulse_gating"
    TIME_DEPENDENT_DIELECTRIC = "time_dependent_dielectric"
    DYNAMICAL_CASIMIR = "dynamical_casimir"
    WAVEPACKET_TRUNCATION = "wavepacket_truncation"
    CLASSICAL_SPECTRAL_BROADENING = "classical_spectral_broadening"
    DETECTOR_ARTIFACT = "detector_artifact"


@dataclass(frozen=True)
class MechanismModel:
    """What a mechanism does, and what it does not license."""

    mechanism: Mechanism
    creates_photons: bool
    needs_time_dependence: bool
    description: str
    does_not_license: str


MECHANISM_MODELS: dict[Mechanism, MechanismModel] = {
    Mechanism.STATIC_MIRROR_OR_BEAMSPLITTER: MechanismModel(
        Mechanism.STATIC_MIRROR_OR_BEAMSPLITTER, False, False,
        "a unitary two-port that splits amplitude between output modes; "
        "photon number is conserved and single photons stay single",
        "any claim that a photon was divided; a beamsplitter puts one "
        "photon in a superposition of paths, not half a photon in each"),
    Mechanism.ORDINARY_DESTRUCTIVE_INTERFERENCE: MechanismModel(
        Mechanism.ORDINARY_DESTRUCTIVE_INTERFERENCE, False, False,
        "a dark fringe: detection probability and energy are moved to the "
        "bright fringes, and the total is unchanged",
        "an exotic remainder at the dark port; nothing is left over"),
    Mechanism.PULSE_GATING: MechanismModel(
        Mechanism.PULSE_GATING, False, True,
        "a shutter or modulator that transmits part of a classical pulse "
        "envelope; the transmitted field is a shorter classical pulse",
        "photon truncation; gating an attenuated beam removes whole "
        "photons probabilistically, it does not shorten one"),
    Mechanism.TIME_DEPENDENT_DIELECTRIC: MechanismModel(
        Mechanism.TIME_DEPENDENT_DIELECTRIC, True, True,
        "a refractive index modulated in time; produces sidebands and, "
        "in the quantum treatment, pair creation from vacuum",
        "a new particle; the output is photons in shifted modes"),
    Mechanism.DYNAMICAL_CASIMIR: MechanismModel(
        Mechanism.DYNAMICAL_CASIMIR, True, True,
        "a boundary condition moved or switched in time; a Bogoliubov "
        "transformation producing correlated photon pairs from vacuum",
        "free energy; the photon energy is supplied by the boundary"),
    Mechanism.WAVEPACKET_TRUNCATION: MechanismModel(
        Mechanism.WAVEPACKET_TRUNCATION, False, True,
        "the single-photon amplitude is cut in time, which broadens its "
        "spectrum and reduces the probability of detecting the photon",
        "a fractional photon; the state is a superposition of one photon "
        "in a reshaped mode and vacuum"),
    Mechanism.CLASSICAL_SPECTRAL_BROADENING: MechanismModel(
        Mechanism.CLASSICAL_SPECTRAL_BROADENING, False, True,
        "any fast amplitude or phase modulation widens the spectrum; "
        "entirely classical Fourier bookkeeping",
        "quantum pair creation; broadening alone is not photon creation"),
    Mechanism.DETECTOR_ARTIFACT: MechanismModel(
        Mechanism.DETECTOR_ARTIFACT, False, False,
        "afterpulsing, dark counts, timing jitter, saturation, or gate "
        "transients that mimic an anomalous count distribution",
        "anything about the field at all"),
}


def mechanism_model(mechanism: Mechanism) -> MechanismModel:
    if mechanism not in MECHANISM_MODELS:
        raise DynBoundaryError(f"no model for {mechanism!r}")
    return MECHANISM_MODELS[mechanism]


def refuse_fractional_photon(fraction: float = 0.6) -> None:
    """Refuse the "photon cut into a fraction of a photon" reading."""
    raise DynBoundaryError(
        f"a state of {fraction:g} photons is refused. The photon number "
        f"operator has integer eigenvalues; truncating a wavepacket in "
        f"time reshapes the mode and reduces the *probability* of "
        f"detecting the photon, leaving a superposition of one photon in "
        f"a new mode and vacuum. A mean occupation of {fraction:g} is an "
        f"expectation value over integer outcomes, not a fractional "
        f"quantum. {DEFAULT_VERDICT}")


def refuse_interference_as_broken_photon(port: str = "the dark port") -> None:
    """Refuse "destructive interference leaves a broken photon" ."""
    raise DynBoundaryError(
        f"a missing count at {port} is not an exotic remainder. Static "
        f"destructive interference REDISTRIBUTES detection probability "
        f"and energy to the bright fringes; the sum over all ports is "
        f"conserved and nothing is left over to be a new object. This is "
        f"{Mechanism.ORDINARY_DESTRUCTIVE_INTERFERENCE.value}, and it is "
        f"a control, not a discovery. {DEFAULT_VERDICT}")


def refuse_new_particle_claim(
        proposed_name: str = DYNAMIC_BOUNDARY_MULTIMODE_STATE_CANDIDATE,
) -> None:
    """Refuse the new-particle interpretation of a boundary-scattered field."""
    raise DynBoundaryError(
        f"{proposed_name!r} is not established as a particle species. What "
        f"a time-dependent boundary produces is a state of the "
        f"electromagnetic quantum field — a multimode squeezed/scattered "
        f"state built from ordinary photons, with integer photon number "
        f"and no new quantum numbers, no new mass, no new coupling and no "
        f"new conservation law. Establishing a species needs a dispersion "
        f"relation, a production and decay channel, and a null against "
        f"every mechanism in Mechanism. None exists here. "
        f"{DEFAULT_VERDICT}")


# --- (5) the observables that would be needed ---------------------------

@dataclass(frozen=True)
class Observable:
    """A measurement that would bear on the claim. None is performed here."""

    name: str
    why_it_matters: str
    status: str = "UNMEASURED"


REQUIRED_OBSERVABLES: tuple[Observable, ...] = (
    Observable(
        "photon_number_distribution",
        "distinguishes a squeezed/thermal pair-created state (even "
        "sectors, super-Poissonian) from a coherent or single-photon one"),
    Observable(
        "squeezing_correlations",
        "quadrature variance below shot noise is the signature of the "
        "Bogoliubov beta term; its absence kills the pair-creation reading"),
    Observable(
        "sideband_spectrum",
        "a boundary switched at a rate sets the sideband positions; a "
        "static boundary produces none"),
    Observable(
        "forward_backward_correlations",
        "dynamical Casimir photons are created in correlated pairs "
        "emitted in opposite directions"),
    Observable(
        "switching_energy_input",
        "closes the energy ledger: the work done on the boundary must "
        "match the field energy created"),
    Observable(
        "transition_region_energy_density",
        "where the created energy sits while the boundary is changing; "
        "separates real excitation from bookkeeping"),
    Observable(
        "dependence_on_switching_time",
        "the model's own falsifiable prediction: photon number falls as "
        "tau grows, and diverges only in the impossible tau -> 0 limit"),
    Observable(
        "nulls_with_static_boundaries_and_classical_pulses",
        "the controls: a static mirror and a classical gated pulse must "
        "produce nothing, or the effect is an artifact"),
)


def observables_report() -> dict:
    return {
        "observables": [
            {"name": o.name, "why_it_matters": o.why_it_matters,
             "status": o.status} for o in REQUIRED_OBSERVABLES],
        "count": len(REQUIRED_OBSERVABLES),
        "any_measured": any(o.status != "UNMEASURED"
                            for o in REQUIRED_OBSERVABLES),
        "measured_here": "nothing",
    }


# --- (6) accessibility, and why it settles nothing -----------------------

def accessibility_vs_neutrino() -> dict:
    """Compare experimental accessibility with a neutrino lane.

    Returns *both* statements, deliberately: the accessibility point is
    real and the caveat is load-bearing, and quoting either alone
    misrepresents the position.
    """
    return {
        "accessibility_statement": (
            "the dynamic-boundary lane is far more experimentally "
            "accessible than neutrino interaction: it runs at optical and "
            "microwave frequencies on a bench or in a dilution "
            "refrigerator, with photon counters, homodyne detection and "
            "GHz-rate boundary modulation that already exist, and the "
            "dynamical Casimir effect has been observed in "
            "superconducting-circuit analogues. Neutrino work needs "
            "kiloton targets, deep underground sites and years of "
            "exposure for comparable statistics"),
        "does_not_establish_statement": (
            "accessibility does not establish the exotic interpretation. "
            "Being easy to test says nothing about what the test will "
            "show; it makes the claim cheap to falsify, not more likely "
            "to be true. The accessible measurements listed here are "
            "consistent with ordinary quantum optics, and every "
            "conventional mechanism in Mechanism must be nulled before "
            "any exotic reading is on the table"),
        "both_statements_are_required": True,
        "verdict": DEFAULT_VERDICT,
        "measured_here": "nothing",
    }


# --- report --------------------------------------------------------------

def dynboundary_report() -> dict:
    return {
        "reference": TRUNCATED_PHOTON_REFERENCE_A,
        "candidate_label": DYNAMIC_BOUNDARY_MULTIMODE_STATE_CANDIDATE,
        "what_this_is": (
            "a Bogoliubov treatment of a boundary condition that changes "
            "in time: a_out = alpha*a_in + beta*conj(a_in_dagger) with "
            "|alpha|**2 - |beta|**2 == 1, giving a multimode state whose "
            "photon-number sectors run from zero upward, including a "
            "multimode squeezed-vacuum component with mean occupation "
            "<n> = |beta|**2 = sinh(r)**2 per mode"),
        "the_real_result": (
            "a time-dependent reflector does not cut a photon into a "
            "fraction; it scatters and creates photons, and the created "
            "energy is supplied by the agent that switches the boundary "
            "(dynamical Casimir). No new particle is required or implied"),
        "the_divergence": divergence_report(),
        "competing_mechanisms": [m.name for m in Mechanism],
        "required_observables": observables_report(),
        "accessibility": accessibility_vs_neutrino(),
        "firewalls": [
            "a photon is not divided into a fractional photon",
            "static destructive interference redistributes energy and "
            "leaves no exotic remainder",
            "the instantaneous-switching divergence is an unphysical "
            "idealization, not usable infinite free energy",
            "created photons are paid for by work on the boundary",
            "an electromagnetic field state is not a new particle species",
        ],
        "verdicts": list(VERDICTS),
        "evidence_class": "DERIVED_MATHEMATICS",
        "hardware_status": "DEFERRED — no apparatus has been built",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "what_this_does_not_say": (
            "It does not say a boundary was switched, that any photon was "
            "counted, that squeezing or sidebands were observed, or that "
            "a dynamical Casimir signal was produced on a bench. It does "
            "not say a photon can be truncated into a fraction of a "
            "quantum, that a dark interference port hides a remainder, or "
            "that the tau -> 0 divergence is an energy source. It does "
            "not identify a new particle: the output of a time-dependent "
            "boundary is an electromagnetic quantum-field state, and "
            "every number here is arithmetic on a declared model."),
        "verdict": DEFAULT_VERDICT,
    }
