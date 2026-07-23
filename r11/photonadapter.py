"""R11 P08b — the truncated-photon source equations, registered, plus a
classical reduced-order analogue of the fidelity.

This module is the *adapter* between a specific published treatment of a
photon meeting a dielectric slab that is removed mid-flight and what this
repository is actually able to compute. It extends the discipline of
:mod:`r11.dynboundary` (a switched boundary is a Bogoliubov
transformation, the instantaneous limit diverges, the switching agent
pays for the photons) and does not repeat it.

**What the source says.** A thin dielectric slab of integrated
permittivity ``kappa_0`` is removed over a time ``T`` while a single
photon is passing. The state left behind is *not* another photon and
*not* a mixture of a photon and vacuum: it is a superposition and mixture
of photon numbers running up to infinity. It is nevertheless *locally*
equivalent to a single photon on one side of a narrow transition region
and to vacuum on the other. Removing the slab instantaneously gives a
divergent photon number; removing it gradually over ``T`` bounds the
number (Eq. 29). Energy is not conserved because time-translation
invariance is broken — the switching boundary supplies it, which is the
dynamical-Casimir accounting already booked in :mod:`r11.dynboundary`.

**Why only a CLASSICAL reduced-order analogue is implemented here.**
There is no quantum-field-theory solver in this repository. Nothing here
constructs a Fock space, a mode expansion, a Bogoliubov kernel over a
continuum, a density operator ``rho_xi``, or the expectation value in
Eq. 21. Consequently:

* Eq. 21, 22, 28, 29, 30 and 31 are **registered as ESTABLISHED_SOURCE**
  — cited with their paper equation numbers and the verified SHA-256 of
  the source PDF. They are *not* re-derived here, and registering them is
  not evidence for them.
* :func:`photon_number_bound` and :func:`transmissivity` are direct
  arithmetic evaluations of two registered closed forms. Arithmetic on a
  cited formula is bookkeeping, not a field-theoretic computation.
* :func:`fidelity_fraction_left` is an **ANALYTIC_MODEL**: a purely
  classical reduced-order stand-in for Eq. 28. It computes the fraction
  of a normalized envelope's *power* lying at ``x < 0``. Eq. 28 says the
  quantum fidelity equals the fraction of the photon located at ``x < 0``
  in the regime ``<n> << 1``; the classical energy fraction has the same
  functional shape and **is not that result**. Outside ``<n> << 1`` the
  identification fails outright, and even inside it the classical number
  carries no quantum state behind it.

Nothing here is measured and nothing here is bench-validated. The
standing verdict is ``QUANTUM_TRUNCATION_NOT_BENCH_VALIDATED``:
the truncation physics is a registered result of the cited literature,
this repository reproduces none of it numerically, and the classical
analogue may not be promoted into a quantum claim.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from r11.sources import SourceKind

# --- public neutral names ------------------------------------------------

#: Neutral handle for the source claim about a photon "cut" by a
#: disappearing boundary. Shared with :mod:`r11.dynboundary`; the two
#: modules address the same reference from different directions.
TRUNCATED_PHOTON_REFERENCE_A = "TRUNCATED_PHOTON_REFERENCE_A"

DEFAULT_VERDICT = "QUANTUM_TRUNCATION_NOT_BENCH_VALIDATED"

VERDICTS = (
    DEFAULT_VERDICT,
    "SOURCE_EQUATIONS_REGISTERED_NOT_REDERIVED",
    "CLASSICAL_ANALOGUE_IS_NOT_THE_QUANTUM_RESULT",
    "PHYSICAL_VALIDATION_NOT_CLAIMED",
)


class PhotonAdapterError(RuntimeError):
    """Raised when a truncated-photon claim exceeds what this module licenses."""


# --- (1) the source paper, by citation and by hash -----------------------

#: SHA-256 of the source PDF, verified by the operator against the file.
#: The hash is the provenance anchor: the equations below are registered
#: against *this* document and no other.
SOURCE_PAPER_SHA256 = (
    "b9e54ac8b1f7a4f7a1d00f98d540d1941684f3483bc4b96648337a6693f6472e")


@dataclass(frozen=True)
class SourcePaper:
    """The cited document. A citation and a hash, never a file path."""

    title: str
    authors: str
    institution: str
    identifier: str
    dated: str
    sha256: str

    def __post_init__(self) -> None:
        if len(self.sha256) != 64 or any(
                c not in "0123456789abcdef" for c in self.sha256):
            raise PhotonAdapterError(
                "a source paper must carry a full lowercase hex SHA-256")


SOURCE_PAPER = SourcePaper(
    title="A truncated photon",
    authors="Rukan, Gulla & Skaar",
    institution="University of Oslo",
    identifier="arXiv:2510.21636v2",
    dated="26 May 2026",
    sha256=SOURCE_PAPER_SHA256,
)


# --- (2) the registered equations ----------------------------------------

@dataclass(frozen=True)
class SourceEquation:
    """One equation taken from the source, registered rather than derived.

    ``kind`` is :attr:`SourceKind.ESTABLISHED_SOURCE` throughout: these
    are the cited author's results. Implementing the arithmetic of a
    registered closed form does not upgrade it to a result of this
    repository, and no equation here is independently verified.
    """

    equation_id: str
    paper_eq_number: int
    text: str
    meaning: str
    kind: SourceKind = SourceKind.ESTABLISHED_SOURCE
    source_sha256: str = SOURCE_PAPER_SHA256
    rederived_here: bool = False
    bench_validated: bool = False

    def __post_init__(self) -> None:
        if self.source_sha256 != SOURCE_PAPER_SHA256:
            raise PhotonAdapterError(
                f"{self.equation_id} is registered against a document whose "
                f"hash does not match the verified source paper")
        if self.rederived_here or self.bench_validated:
            raise PhotonAdapterError(
                f"{self.equation_id} may not be marked re-derived or "
                f"bench-validated: no QFT solver and no apparatus exists "
                f"here. {DEFAULT_VERDICT}")


SOURCE_EQUATIONS: tuple[SourceEquation, ...] = (
    SourceEquation(
        "EQ21_FIDELITY_DEFINITION", 21,
        "F_xi**2 = <0| a_xi rho_xi a_xi^dagger |0>",
        "the fidelity of the truncated state against a single photon in "
        "mode xi, defined as the vacuum matrix element of the annihilated "
        "density operator; requires a Fock-space object rho_xi, which this "
        "repository does not construct"),
    SourceEquation(
        "EQ22_EXPECTED_PHOTON_NUMBER", 22,
        "<n> = sum_xi ( ||xi_-||**2 + ||xi_+||**2 )",
        "the expected photon number after truncation, summed over modes "
        "with left- and right-going contributions; the sum runs over "
        "photon-number sectors up to infinity, not over a fraction"),
    SourceEquation(
        "EQ28_FIDELITY_SMALL_N", 28,
        "F_xi = | integral dx theta(-x) conj(xi_bar(x)) xi(x) |",
        "for <n> << 1 the fidelity is the fraction of the photon located "
        "at x < 0 — the overlap of the truncated envelope with the "
        "reference envelope restricted to the left half-line"),
    SourceEquation(
        "EQ29_PHOTON_NUMBER_BOUND", 29,
        "<n> <= kappa_0/(4*T) + kappa_0**2/(16*T**2)",
        "the photon-number bound for GRADUAL removal of the slab over a "
        "time T; kappa_0 is the integrated permittivity of the thin "
        "dielectric slab. Divergent as T -> 0, decreasing in T"),
    SourceEquation(
        "EQ30_TRANSMISSIVITY", 30,
        "|T(omega)|**2 = 1 / (1 + (omega*kappa_0)**2 / 4)",
        "the slab transmissivity: unity at zero frequency and falling "
        "monotonically with omega*kappa_0, so a slab opaque enough to "
        "truncate an optical photon fixes kappa_0"),
    SourceEquation(
        "EQ31_VALIDITY_CONDITION", 31,
        "1/omega_0 << kappa_0 <~ T",
        "the regime in which the treatment holds: the slab response time "
        "must be long against an optical cycle and no longer than the "
        "removal time"),
)

_BY_EQ_ID = {e.equation_id: e for e in SOURCE_EQUATIONS}
_BY_EQ_NUMBER = {e.paper_eq_number: e for e in SOURCE_EQUATIONS}


def get_equation(equation_id: str) -> SourceEquation:
    """Look up a registered source equation by its id."""
    if equation_id not in _BY_EQ_ID:
        raise PhotonAdapterError(
            f"unregistered source equation {equation_id!r}; every equation "
            f"used here must be registered with its paper equation number "
            f"and the verified source hash")
    return _BY_EQ_ID[equation_id]


def get_equation_by_number(paper_eq_number: int) -> SourceEquation:
    """Look up a registered source equation by its number in the paper."""
    if paper_eq_number not in _BY_EQ_NUMBER:
        raise PhotonAdapterError(
            f"equation {paper_eq_number} of the source paper is not "
            f"registered in this module")
    return _BY_EQ_NUMBER[paper_eq_number]


# --- (3) the qualitative claims, typed -----------------------------------

@dataclass(frozen=True)
class SourceClaim:
    """A qualitative statement of the source, recorded as a claim.

    A registered claim is a *citation of what the authors say*. It is
    never a finding of this repository, and ``verified_here`` is False by
    construction.
    """

    claim_id: str
    statement: str
    where: str
    kind: SourceKind = SourceKind.SOURCE_CLAIM
    verified_here: bool = False

    def __post_init__(self) -> None:
        if self.verified_here:
            raise PhotonAdapterError(
                f"{self.claim_id} cannot be marked verified here; this "
                f"module registers the source, it does not check it. "
                f"{DEFAULT_VERDICT}")


SOURCE_CLAIMS: tuple[SourceClaim, ...] = (
    SourceClaim(
        "CLAIM_NOT_A_PHOTON_NOR_A_MIX_WITH_VACUUM",
        "a truncated photon is neither another photon nor a mix of a "
        "photon and a vacuum; it is a superposition and mixture of photon "
        "numbers up to infinity",
        "abstract and conclusions"),
    SourceClaim(
        "CLAIM_LOCAL_EQUIVALENCE",
        "the truncated state is locally equivalent to a single photon to "
        "the left, and to vacuum to the right, of a narrow transition "
        "region",
        "abstract and conclusions"),
    SourceClaim(
        "CLAIM_INSTANTANEOUS_DIVERGES_GRADUAL_BOUNDED",
        "instantaneous removal of the slab gives a divergent photon "
        "number; gradual removal over a time T bounds it, by Eq. 29",
        "Eq. 29 and surrounding discussion"),
    SourceClaim(
        "CLAIM_SWITCHING_BOUNDARY_SUPPLIES_THE_ENERGY",
        "energy is not conserved because time-translation invariance is "
        "broken; the switching boundary supplies the energy, which is the "
        "ordinary dynamical-Casimir accounting",
        "conclusions"),
    SourceClaim(
        "CLAIM_OPTICAL_SCALE_EXAMPLE",
        "for an optical photon with omega_0/2pi = 1e15 Hz and "
        "|T(omega_0)|**2 = 1e-4, the removal time T can be as small as "
        "about 1e-14 s before <n> becomes comparable to 1",
        "numerical example accompanying Eqs. 29-31"),
)

_BY_CLAIM_ID = {c.claim_id: c for c in SOURCE_CLAIMS}


def get_claim(claim_id: str) -> SourceClaim:
    if claim_id not in _BY_CLAIM_ID:
        raise PhotonAdapterError(f"unregistered source claim {claim_id!r}")
    return _BY_CLAIM_ID[claim_id]


# --- (4) Eq. 29: the photon-number bound ---------------------------------

def photon_number_bound(kappa_0: float, T: float) -> float:
    """Eq. 29 exactly: ``<n> <= kappa_0/(4*T) + kappa_0**2/(16*T**2)``.

    ``kappa_0`` is the integrated permittivity of the thin slab and ``T``
    the removal time; both have dimensions of time in the units the
    source uses, so ``kappa_0/T`` is dimensionless.

    The bound **decreases monotonically in ``T``** and **diverges as
    ``T -> 0``**. ``T <= 0`` therefore has no finite value to return and
    raises: instantaneous removal is the divergent idealization already
    refused in :mod:`r11.dynboundary`, not a configuration.

    Returning the right-hand side is arithmetic on a registered closed
    form. It is not a derivation of the bound and not a measurement of
    ``<n>``.
    """
    if kappa_0 < 0.0:
        raise PhotonAdapterError(
            "the integrated permittivity kappa_0 cannot be negative")
    if T < 0.0:
        raise PhotonAdapterError("the removal time T cannot be negative")
    if T == 0.0:
        raise PhotonAdapterError(
            "T == 0 is instantaneous removal of the slab: the Eq. 29 bound "
            "kappa_0/(4T) + kappa_0**2/(16 T**2) DIVERGES, which is the "
            "source's own statement that an instantaneous removal produces "
            "an unbounded photon number. Supply T > 0. "
            "INSTANTANEOUS_LIMIT_IS_UNPHYSICAL_IDEALIZATION")
    return kappa_0 / (4.0 * T) + kappa_0 ** 2 / (16.0 * T * T)


def removal_time_for_bound(kappa_0: float, n_bound: float = 1.0) -> float:
    """Invert Eq. 29 for ``T`` at a given bound value.

    With ``u = kappa_0/(4T)`` the bound is ``u + u**2``, so
    ``u = (sqrt(1 + 4*n) - 1)/2`` and ``T = kappa_0/(4*u)``. Used to say
    how fast the slab may be removed before ``<n>`` reaches order unity.
    """
    if kappa_0 <= 0.0:
        raise PhotonAdapterError("kappa_0 must be positive to invert Eq. 29")
    if n_bound <= 0.0:
        raise PhotonAdapterError("the target bound must be positive")
    u = (math.sqrt(1.0 + 4.0 * n_bound) - 1.0) / 2.0
    return kappa_0 / (4.0 * u)


def bound_sweep(kappa_0: float,
                removal_times: "np.ndarray | list[float]") -> dict:
    """Eq. 29 across a sweep of removal times, with monotonicity recorded."""
    t = np.asarray(list(removal_times), dtype=float)
    if t.size < 2:
        raise PhotonAdapterError("a sweep needs at least two removal times")
    n = np.array([photon_number_bound(kappa_0, float(x)) for x in t])
    order = np.argsort(t)
    ordered = n[order]
    return {
        "equation": get_equation("EQ29_PHOTON_NUMBER_BOUND").text,
        "paper_eq_number": 29,
        "kappa_0": float(kappa_0),
        "removal_time": t.tolist(),
        "photon_number_bound": n.tolist(),
        "all_finite": bool(np.all(np.isfinite(n))),
        "monotone_decreasing_in_T": bool(np.all(np.diff(ordered) < 0.0)),
        "diverges_as_T_to_zero": True,
        "evidence_class": SourceKind.ESTABLISHED_SOURCE.value,
        "measured_here": "nothing",
    }


# --- (5) Eq. 30: the transmissivity --------------------------------------

def transmissivity(omega: float | np.ndarray,
                   kappa_0: float) -> float | np.ndarray:
    """Eq. 30 exactly: ``|T(omega)|**2 = 1 / (1 + (omega*kappa_0)**2 / 4)``.

    Unity at ``omega == 0``, strictly decreasing in ``|omega|``, and
    always in ``(0, 1]``. The slab is transparent to a static field and
    progressively opaque as ``omega*kappa_0`` grows.
    """
    if kappa_0 < 0.0:
        raise PhotonAdapterError(
            "the integrated permittivity kappa_0 cannot be negative")
    w = np.asarray(omega, dtype=float)
    out = 1.0 / (1.0 + (w * kappa_0) ** 2 / 4.0)
    return float(out) if np.ndim(omega) == 0 else out


def kappa_0_from_transmissivity(omega: float, t_squared: float) -> float:
    """Invert Eq. 30: ``kappa_0 = (2/omega) * sqrt(1/|T|**2 - 1)``.

    Given the frequency and the transmissivity the slab must have, this
    fixes the integrated permittivity — the route the source's numerical
    example takes.
    """
    if omega <= 0.0:
        raise PhotonAdapterError("omega must be positive to invert Eq. 30")
    if not 0.0 < t_squared <= 1.0:
        raise PhotonAdapterError(
            "|T(omega)|**2 must lie in (0, 1]; Eq. 30 admits no other value")
    return (2.0 / omega) * math.sqrt(1.0 / t_squared - 1.0)


# --- (6) Eq. 31: the validity condition ----------------------------------

#: How much larger than ``1/omega_0`` the slab response must be before
#: ``1/omega_0 << kappa_0`` is treated as satisfied. A declared reading of
#: a "<<" written in prose, not a value taken from the source.
STRONG_INEQUALITY_FACTOR = 10.0


def validity_condition(omega_0: float, kappa_0: float, T: float) -> dict:
    """Eq. 31: ``1/omega_0 << kappa_0 <~ T``, evaluated and reported.

    ``<<`` and ``<~`` are prose. They are read here as a declared factor
    (:data:`STRONG_INEQUALITY_FACTOR`) and as "not much larger than",
    and both readings are reported alongside the raw ratios so a reader
    can apply their own.
    """
    if omega_0 <= 0.0:
        raise PhotonAdapterError("omega_0 must be positive")
    if kappa_0 <= 0.0:
        raise PhotonAdapterError("kappa_0 must be positive")
    if T <= 0.0:
        raise PhotonAdapterError("the removal time T must be positive")
    lower_ratio = kappa_0 * omega_0           # kappa_0 / (1/omega_0)
    upper_ratio = kappa_0 / T
    lower_ok = lower_ratio >= STRONG_INEQUALITY_FACTOR
    upper_ok = upper_ratio <= 1.0
    upper_marginal = 1.0 < upper_ratio <= STRONG_INEQUALITY_FACTOR
    return {
        "equation": get_equation("EQ31_VALIDITY_CONDITION").text,
        "paper_eq_number": 31,
        "omega_0": float(omega_0),
        "kappa_0": float(kappa_0),
        "removal_time": float(T),
        "kappa_0_over_optical_period": float(lower_ratio),
        "kappa_0_over_T": float(upper_ratio),
        "lower_inequality_satisfied": bool(lower_ok),
        "upper_inequality_satisfied": bool(upper_ok),
        "upper_inequality_marginal": bool(upper_marginal),
        "strong_inequality_factor": STRONG_INEQUALITY_FACTOR,
        "in_declared_regime": bool(lower_ok and (upper_ok or upper_marginal)),
        "note": ("'<<' and '<~' are prose; the factor used to read them is "
                 "declared here, not taken from the source, and the raw "
                 "ratios are reported so another reading can be applied"),
        "measured_here": "nothing",
    }


# --- (7) the source's optical example, recomputed ------------------------

#: The source's stated optical example: omega_0/2pi = 1e15 Hz, slab
#: transmissivity 1e-4 at that frequency, removal time about 1e-14 s.
EXAMPLE_OMEGA_0_RAD_S = 2.0 * math.pi * 1e15
EXAMPLE_TRANSMISSIVITY = 1e-4
EXAMPLE_REMOVAL_TIME_S = 1e-14


def optical_example(omega_0: float = EXAMPLE_OMEGA_0_RAD_S,
                    t_squared: float = EXAMPLE_TRANSMISSIVITY,
                    removal_time: float = EXAMPLE_REMOVAL_TIME_S) -> dict:
    """Recompute the source's optical example from Eqs. 29, 30 and 31.

    Fix ``kappa_0`` from Eq. 30 at the stated transmissivity, then
    evaluate the Eq. 29 bound at the stated removal time and solve for
    the removal time at which the bound reaches unity. The point of the
    function is to state the numbers, including any disagreement with the
    source's stated order of magnitude, rather than to assert agreement.
    """
    kappa_0 = kappa_0_from_transmissivity(omega_0, t_squared)
    bound = photon_number_bound(kappa_0, removal_time)
    t_unit = removal_time_for_bound(kappa_0, 1.0)
    linear_term = kappa_0 / (4.0 * removal_time)
    quadratic_term = kappa_0 ** 2 / (16.0 * removal_time ** 2)
    validity = validity_condition(omega_0, kappa_0, removal_time)
    same_order = 0.1 <= bound <= 10.0
    return {
        "omega_0_rad_s": float(omega_0),
        "omega_0_over_2pi_hz": float(omega_0 / (2.0 * math.pi)),
        "target_transmissivity": float(t_squared),
        "kappa_0_s": float(kappa_0),
        "transmissivity_check": float(transmissivity(omega_0, kappa_0)),
        "removal_time_s": float(removal_time),
        "photon_number_bound": float(bound),
        "bound_linear_term": float(linear_term),
        "bound_quadratic_term": float(quadratic_term),
        "removal_time_for_unit_bound_s": float(t_unit),
        "bound_is_order_unity": bool(same_order),
        "validity": validity,
        "agreement_with_source_example": (
            "CONSISTENT" if same_order else "DISAGREES"),
        "honest_note": (
            "kappa_0 is fixed by Eq. 30 at the stated transmissivity, and "
            "the Eq. 29 bound at the stated removal time is reported as "
            "computed. Where the validity condition Eq. 31 is only "
            "marginally met, that is reported rather than smoothed: see "
            "validity.upper_inequality_marginal"),
        "evidence_class": SourceKind.ESTABLISHED_SOURCE.value,
        "measured_here": "nothing",
        "bench_validated": False,
    }


# --- (8) the CLASSICAL reduced-order analogue of Eq. 28 ------------------

def _trapezoid(y: np.ndarray, x: np.ndarray) -> float:
    """Trapezoidal integral, tolerant of the numpy 1.x/2.x rename."""
    fn = getattr(np, "trapezoid", None) or np.trapz
    return float(fn(y, x))


def fidelity_fraction_left(xi_values: "np.ndarray | list[complex]",
                           x_grid: "np.ndarray | list[float]") -> float:
    """CLASSICAL analogue of Eq. 28: the power fraction at ``x < 0``.

    Eq. 28 states that, for ``<n> << 1``, the fidelity is the fraction of
    the photon located at ``x < 0``. This function computes the
    corresponding **classical** quantity: given a complex envelope
    sampled on an ascending grid, the fraction of ``|xi|**2`` integrated
    over ``x < 0`` relative to the whole grid. The split at ``x == 0`` is
    interpolated so that the answer does not depend on whether the grid
    happens to contain the origin.

    An envelope entirely at ``x < 0`` gives 1.0, one entirely at
    ``x > 0`` gives 0.0, and a symmetric one gives 0.5.

    **This is not the quantum fidelity.** It is a reduced-order
    stand-in with the same functional shape and no state behind it:
    there is no ``rho_xi``, no ``a_xi``, and no Fock space in this
    repository. Promoting the returned number to a statement about the
    quantum fidelity is refused by
    :func:`refuse_quantum_claim_from_classical_analogue`.
    """
    x = np.asarray(x_grid, dtype=float)
    xi = np.asarray(xi_values)
    if x.ndim != 1 or xi.ndim != 1:
        raise PhotonAdapterError("the envelope and the grid must be 1-D")
    if x.size != xi.size:
        raise PhotonAdapterError(
            f"envelope of size {xi.size} does not match a grid of size "
            f"{x.size}")
    if x.size < 2:
        raise PhotonAdapterError("at least two grid points are required")
    if not np.all(np.diff(x) > 0.0):
        raise PhotonAdapterError("the grid must be strictly ascending")
    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(xi)):
        raise PhotonAdapterError("non-finite envelope or grid values")

    power = np.abs(xi) ** 2
    total = _trapezoid(power, x)
    if total <= 0.0:
        raise PhotonAdapterError(
            "an envelope with zero total power has no fraction to report")

    n_left = int(np.count_nonzero(x <= 0.0))
    if n_left == 0:
        return 0.0
    if n_left == x.size:
        return 1.0
    xl = x[:n_left]
    pl = power[:n_left]
    if xl[-1] < 0.0:
        # interpolate the envelope power onto x == 0 and close the segment
        x0, x1 = xl[-1], x[n_left]
        p0, p1 = pl[-1], power[n_left]
        w = (0.0 - x0) / (x1 - x0)
        xl = np.append(xl, 0.0)
        pl = np.append(pl, p0 + w * (p1 - p0))
    if xl.size < 2:
        return 0.0
    left = _trapezoid(pl, xl)
    return float(min(max(left / total, 0.0), 1.0))


def classical_analogue_report(xi_values: "np.ndarray | list[complex]",
                              x_grid: "np.ndarray | list[float]") -> dict:
    """The classical fraction, wrapped in what it does not say."""
    fraction = fidelity_fraction_left(xi_values, x_grid)
    return {
        "analogue_of": get_equation("EQ28_FIDELITY_SMALL_N").text,
        "paper_eq_number": 28,
        "classical_power_fraction_left": fraction,
        "evidence_class": SourceKind.ANALYTIC_MODEL.value,
        "is_the_quantum_fidelity": False,
        "regime_of_the_source_result": "<n> << 1",
        "what_this_does_not_say": (
            "the returned number is a classical energy fraction of a "
            "declared envelope. It is not <0| a_xi rho_xi a_xi^dagger |0>, "
            "no density operator was constructed, and outside <n> << 1 the "
            "source's own identification of fidelity with the left-hand "
            "fraction does not hold"),
        "measured_here": "nothing",
        "verdict": "CLASSICAL_ANALOGUE_IS_NOT_THE_QUANTUM_RESULT",
    }


# --- (9) the refusals ----------------------------------------------------

def refuse_quantum_claim_from_classical_analogue(
        claimed_quantity: str = "the quantum fidelity F_xi",
        classical_value: float = 0.5) -> None:
    """Refuse promotion of the classical power fraction to a quantum result."""
    raise PhotonAdapterError(
        f"a classical power fraction of {classical_value:g} may not be "
        f"reported as {claimed_quantity!r}. Eq. 28 identifies the fidelity "
        f"with the fraction of the photon at x < 0 only in the regime "
        f"<n> << 1, and the identification is a statement about a quantum "
        f"state that this repository never constructs: there is no Fock "
        f"space, no density operator rho_xi and no annihilation operator "
        f"a_xi here. The classical number shares the functional form and "
        f"nothing else. {DEFAULT_VERDICT}")


def refuse_bench_validation(claimed_result: str = "the Eq. 29 bound",
                            apparatus: str = "an optical bench") -> None:
    """Refuse any bench-validation claim. Nothing here is bench-validated."""
    raise PhotonAdapterError(
        f"{claimed_result!r} is not bench-validated by {apparatus!r} or by "
        f"anything else in this repository. No slab has been removed, no "
        f"photon has been counted, no transmissivity has been measured and "
        f"no fidelity has been reconstructed. Every number this module "
        f"returns is arithmetic on a cited closed form or on a declared "
        f"classical envelope. {DEFAULT_VERDICT}")


def refuse_qft_solver_claim(claimed_capability: str = "a QFT solver") -> None:
    """Refuse the claim that evaluating these formulas is a QFT computation."""
    raise PhotonAdapterError(
        f"{claimed_capability!r} does not exist in this repository. "
        f"Evaluating Eq. 29 or Eq. 28 numerically is REGISTRATION of a "
        f"cited closed form plus a classical reduced-order analogue; it is "
        f"not a quantum-field computation. A quantum-field computation "
        f"would need a mode expansion over the continuum, a Bogoliubov "
        f"kernel for the time-dependent slab, and expectation values in a "
        f"Fock space — none of which is built here, and none of which is "
        f"replaced by arithmetic. {DEFAULT_VERDICT}")


def refuse_fractional_photon(fraction: float = 0.6) -> None:
    """Refuse the "truncated photon is a fraction of a photon" reading.

    Consistent with :func:`r11.dynboundary.refuse_fractional_photon`, and
    with the source's own statement: the truncated state is neither
    another photon nor a mix of a photon and a vacuum, it is a
    superposition and mixture of photon numbers up to infinity.
    """
    raise PhotonAdapterError(
        f"a truncated photon is not {fraction:g} of a photon. The source's "
        f"own conclusion is that the truncated state is NEITHER another "
        f"photon NOR a mix of a photon and a vacuum: it is a superposition "
        f"and mixture of photon numbers running up to infinity, locally "
        f"equivalent to one photon to the left and to vacuum to the right "
        f"of a narrow transition region. Eq. 22 sums integer sectors; the "
        f"photon-number operator has integer eigenvalues, and a mean "
        f"occupation of {fraction:g} is an expectation over integer "
        f"outcomes. {DEFAULT_VERDICT}")


# --- report --------------------------------------------------------------

def photonadapter_report() -> dict:
    return {
        "reference": TRUNCATED_PHOTON_REFERENCE_A,
        "what_this_is": (
            "an adapter that registers the truncated-photon source "
            "equations against a hashed document, evaluates the two "
            "registered closed forms that are pure arithmetic (Eq. 29 and "
            "Eq. 30), and supplies a CLASSICAL reduced-order analogue of "
            "the Eq. 28 fidelity"),
        "source_paper": {
            "title": SOURCE_PAPER.title,
            "authors": SOURCE_PAPER.authors,
            "institution": SOURCE_PAPER.institution,
            "identifier": SOURCE_PAPER.identifier,
            "dated": SOURCE_PAPER.dated,
            "sha256": SOURCE_PAPER.sha256,
            "hash_verified": True,
        },
        "registered_equations": [
            {"equation_id": e.equation_id,
             "paper_eq_number": e.paper_eq_number,
             "text": e.text,
             "meaning": e.meaning,
             "evidence_class": e.kind.value,
             "rederived_here": e.rederived_here,
             "bench_validated": e.bench_validated}
            for e in SOURCE_EQUATIONS],
        "registered_equation_count": len(SOURCE_EQUATIONS),
        "registered_claims": [
            {"claim_id": c.claim_id, "statement": c.statement,
             "where": c.where, "evidence_class": c.kind.value,
             "verified_here": c.verified_here}
            for c in SOURCE_CLAIMS],
        "registered_claim_count": len(SOURCE_CLAIMS),
        "optical_example": optical_example(),
        "classical_analogue": {
            "function": "fidelity_fraction_left",
            "analogue_of_paper_eq_number": 28,
            "evidence_class": SourceKind.ANALYTIC_MODEL.value,
            "is_the_quantum_fidelity": False,
            "what_it_computes": (
                "the fraction of a declared classical envelope's power "
                "lying at x < 0"),
        },
        "relationship_to_dynboundary": (
            "r11.dynboundary carries the Bogoliubov treatment, the "
            "switching-time divergence and the energy ledger; this module "
            "does not repeat them. It adds the source's own registered "
            "equations, the hashed provenance, and the classical fidelity "
            "analogue"),
        "firewalls": [
            "registered equations are cited, not re-derived",
            "the classical power fraction is not the quantum fidelity",
            "no QFT solver exists here, so no quantum truncation result is "
            "numerically reproduced",
            "nothing here is bench-validated",
            "the truncated photon is not a fraction of a photon",
        ],
        "verdicts": list(VERDICTS),
        "evidence_class": "ESTABLISHED_SOURCE and ANALYTIC_MODEL",
        "evidence_class_breakdown": {
            "registered_source_equations":
                SourceKind.ESTABLISHED_SOURCE.value,
            "registered_source_claims": SourceKind.SOURCE_CLAIM.value,
            "classical_fidelity_analogue": SourceKind.ANALYTIC_MODEL.value,
        },
        "hardware_status": "DEFERRED — no apparatus has been built",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "what_this_does_not_say": (
            "It does not say the source's results were re-derived, checked "
            "or reproduced here: they are registered against a verified "
            "document hash and evaluated arithmetically where they are "
            "closed forms. It does not say any quantum truncation result "
            "is bench-validated — no slab was removed, no photon counted, "
            "no transmissivity measured and no fidelity reconstructed. It "
            "does not say the classical power fraction at x < 0 is the "
            "quantum fidelity of Eq. 21 or Eq. 28; there is no Fock space, "
            "density operator or QFT solver in this repository. And it "
            "does not say a photon can be cut into a fraction of a "
            "photon — the source itself says the truncated state is a "
            "superposition and mixture of photon numbers up to infinity."),
        "verdict": DEFAULT_VERDICT,
    }
