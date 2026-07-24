"""P11 — avoided crossings in a two-level system, as an analytic model.

Two bare levels ``E1(x)`` and ``E2(x)`` cross at some tuning ``x0`` when
they are uncoupled. Turn on a coupling ``g`` and they no longer touch:
the eigenvalues of

    H(x) = [[E1(x), g], [conj(g), E2(x)]]

are ``E±(x) = mean(x) ± sqrt(delta(x)**2 + |g|**2)`` with
``delta = (E1 - E2)/2``, and the split branches repel. Everything this
module states is a consequence of that one radical:

* **The gap is 2|g|.** The branch separation ``E+ - E-`` is
  ``2*sqrt(delta**2 + |g|**2)``, minimised at the degeneracy point
  ``delta = 0`` where it equals ``2*|g|`` exactly. With ``g == 0`` the
  radical is ``2*|delta|`` and the levels cross cleanly (gap 0). This is
  the same closed form the R11 coupled-mode lane uses; here it is stated
  for a general two-level Hamiltonian.
* **The eigenvectors swap character.** As ``x`` sweeps through ``x0`` the
  upper branch that was mostly level 1 becomes mostly level 2. The
  *adiabatic* labelling (by eigenvalue order) stays continuous, while the
  *diabatic* character crosses over, so the far-side overlap
  ``|<psi_+(x << x0)|psi_+(x >> x0)>|`` is small.
* **Landau-Zener sets the crossing probability.** Sweeping through the
  anticrossing at finite rate, the diabatic transition probability is
  ``P = exp(-2*pi*|g|**2 / (hbar * |dDelta/dt|))``: a fast sweep is
  diabatic (``P -> 1``, the system jumps the gap and keeps its
  character), a slow sweep is adiabatic (``P -> 0``, it follows the
  branch around the gap).

The firewall: :func:`refuse_model_crossing_as_measured` refuses to read
an anticrossing computed here as an observed mode repulsion. A minimum
gap in a *model* spectrum is arithmetic on a declared Hamiltonian; a
repulsion between two real modes is a bench observation with a measured
splitting, a calibrated tuning axis, and a linewidth. Nothing here is
measured: no two-level system exists, no level is tuned, and every
number is a closed form on chosen inputs.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

import numpy as np

# --- verdict, claim class, constants -------------------------------------

#: The standing verdict for this module.
DEFAULT_VERDICT = "AVOIDED_CROSSING_MODEL_ANALYTIC"

#: What this module's output is: closed-form algebra on a declared model
#: Hamiltonian. Not a simulation, not a measurement.
CLAIM_CLASS = "ANALYTIC_MODEL"

MEASURED_HERE = "nothing"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: Reduced Planck constant, SI (CODATA). Used only to give the
#: Landau-Zener exponent its units; no energy here is measured.
HBAR_J_S = 1.054571817e-34

#: Tolerance on a closed form compared with a numerical eigendecomposition.
GAP_TOL = 1e-10


class AvoidedError(RuntimeError):
    """Raised when an avoided-crossing claim exceeds what the model licenses.

    Covers the structural refusals (a non-finite level or coupling, a
    non-Hermitian 2x2, a non-physical sweep) and the load-bearing
    firewall :func:`refuse_model_crossing_as_measured`, which refuses to
    read a modelled anticrossing as an observed mode repulsion.
    """


def _finite(value: float, what: str) -> float:
    """Coerce to float and refuse anything non-finite."""
    x = float(value)
    if not math.isfinite(x):
        raise AvoidedError(f"{what} must be finite")
    return x


def _finite_complex(value: complex, what: str) -> complex:
    """Coerce to complex and refuse anything non-finite."""
    z = complex(value)
    if not (math.isfinite(z.real) and math.isfinite(z.imag)):
        raise AvoidedError(f"{what} must be finite")
    return z


# --- the two-level Hamiltonian and its spectrum --------------------------

def avoided_gap(g: complex) -> float:
    """``2*|g|``: the minimum branch separation of the anticrossing.

    At the degeneracy point ``delta == 0`` the eigenvalue separation
    ``2*sqrt(delta**2 + |g|**2)`` collapses to ``2*|g|``, which is zero if
    and only if the coupling is zero. This is the gap the split branches
    never fall below.
    """
    return 2.0 * abs(_finite_complex(g, "the coupling g"))


def two_level_hamiltonian(e1: float, e2: float, g: complex) -> np.ndarray:
    """The 2x2 Hermitian Hamiltonian ``[[E1, g], [conj(g), E2]]``."""
    a = _finite(e1, "E1")
    b = _finite(e2, "E2")
    k = _finite_complex(g, "the coupling g")
    return np.array([[a, k], [np.conj(k), b]], dtype=complex)


@dataclass(frozen=True)
class TwoLevelSpectrum:
    """The eigenvalues and eigenvectors of one two-level Hamiltonian.

    ``lower`` and ``upper`` are the eigenvalues (ascending), ``gap`` their
    separation, and the two eigenvectors are the columns of ``vectors``
    in the same order. Every quantity is in the caller's energy units; the
    class has no opinion about what they are.
    """

    e1: float
    e2: float
    g: complex
    lower: float
    upper: float
    vectors: np.ndarray

    @property
    def delta(self) -> float:
        """``(E1 - E2)/2``: the half-detuning of the bare levels."""
        return 0.5 * (self.e1 - self.e2)

    @property
    def mean(self) -> float:
        """``(E1 + E2)/2``: the centre the branches straddle."""
        return 0.5 * (self.e1 + self.e2)

    @property
    def gap(self) -> float:
        """``upper - lower == 2*sqrt(delta**2 + |g|**2)``."""
        return self.upper - self.lower

    def lower_vector(self) -> np.ndarray:
        return self.vectors[:, 0]

    def upper_vector(self) -> np.ndarray:
        return self.vectors[:, 1]

    def as_dict(self) -> dict:
        return {
            "e1": self.e1,
            "e2": self.e2,
            "coupling_magnitude": abs(self.g),
            "delta": self.delta,
            "mean": self.mean,
            "lower": self.lower,
            "upper": self.upper,
            "gap": self.gap,
            "measured_here": MEASURED_HERE,
        }


def two_level_spectrum(e1: float, e2: float, g: complex) -> TwoLevelSpectrum:
    """Diagonalise the two-level Hamiltonian, eigenvalues ascending.

    Uses the closed form for the eigenvalues,

        ``lower, upper = mean -/+ sqrt(delta**2 + |g|**2)``

    and a Hermitian eigendecomposition for the eigenvectors, so both the
    gap and the branch characters are available.
    """
    matrix = two_level_hamiltonian(e1, e2, g)
    values, vectors = np.linalg.eigh(matrix)
    return TwoLevelSpectrum(
        e1=_finite(e1, "E1"), e2=_finite(e2, "E2"),
        g=_finite_complex(g, "the coupling g"),
        lower=float(np.real(values[0])), upper=float(np.real(values[1])),
        vectors=vectors)


def avoided_crossing_sweep(e1_of_x, e2_of_x, g: complex,
                           xs=None, n_points: int = 201,
                           x0: float = 0.0, span: float = 1.0) -> dict:
    """Sweep a tuning parameter through the crossing and watch the repulsion.

    ``e1_of_x`` and ``e2_of_x`` are callables giving the bare levels as a
    function of the tuning ``x``. The default grid is built symmetrically
    about ``x0`` so the minimum is evaluated, not interpolated. The
    reported minimum gap is compared against ``2*|g|``.
    """
    k = _finite_complex(g, "the coupling g")
    if xs is None:
        if n_points < 3 or n_points % 2 == 0:
            raise AvoidedError("a sweep needs an odd n_points of at least 3")
        width = _finite(span, "the sweep span")
        if width <= 0.0:
            raise AvoidedError("the sweep span must be positive")
        centre = _finite(x0, "x0")
        half = (int(n_points) - 1) // 2
        positive = np.linspace(0.0, width, half + 1)[1:]
        grid = np.concatenate([-positive[::-1], [0.0], positive]) + centre
    else:
        grid = np.asarray(list(xs), dtype=float)
        if grid.size < 3:
            raise AvoidedError("a sweep needs at least three tuning points")
        if not np.all(np.isfinite(grid)):
            raise AvoidedError("every tuning point must be finite")

    spectra = [two_level_spectrum(float(e1_of_x(x)), float(e2_of_x(x)), k)
               for x in grid]
    lower = np.array([s.lower for s in spectra])
    upper = np.array([s.upper for s in spectra])
    gaps = upper - lower
    j = int(np.argmin(gaps))
    expected = avoided_gap(k)
    scale = max(1.0, abs(expected))
    never_cross = bool(k != 0 and np.all(gaps > 0.0))
    return {
        "x": grid.tolist(),
        "lower": lower.tolist(),
        "upper": upper.tolist(),
        "gap": gaps.tolist(),
        "minimum_gap": float(gaps[j]),
        "expected_minimum_gap": expected,
        "x_at_minimum": float(grid[j]),
        "coupling_magnitude": abs(k),
        "minimum_matches_twice_the_coupling": bool(
            abs(float(gaps[j]) - expected) <= GAP_TOL * scale),
        "gap_never_below_twice_the_coupling": bool(
            np.all(gaps >= expected - GAP_TOL * scale)),
        "branches_never_cross": never_cross,
        "note": ("as the bare levels are tuned through each other the "
                 "branches repel; the closest approach is 2*|g|, and it is "
                 "zero only when the coupling is zero"),
        "verdict": DEFAULT_VERDICT,
        "measured_here": MEASURED_HERE,
    }


def diabatic_adiabatic_swap(e1_of_x, e2_of_x, g: complex,
                            x_low: float, x_high: float) -> dict:
    """How the branch characters map across the crossing.

    The *adiabatic* branches are labelled by eigenvalue order, and that
    labelling is continuous through the sweep. The *diabatic* characters
    (which bare level each branch is made of) exchange, so the overlap of
    the upper branch far below the crossing with the upper branch far
    above it is small. Returns both the far-side overlap and the local
    continuity, which are not in tension: one is about character, the
    other about ordering.
    """
    if x_low >= x_high:
        raise AvoidedError("x_low must lie below x_high")
    k = _finite_complex(g, "the coupling g")
    lo = two_level_spectrum(float(e1_of_x(x_low)), float(e2_of_x(x_low)), k)
    hi = two_level_spectrum(float(e1_of_x(x_high)), float(e2_of_x(x_high)), k)
    xm = 0.5 * (x_low + x_high)
    mid = two_level_spectrum(float(e1_of_x(xm)), float(e2_of_x(xm)), k)
    eps = 1e-6 * max(1.0, abs(x_high - x_low))
    mid_next = two_level_spectrum(float(e1_of_x(xm + eps)),
                                  float(e2_of_x(xm + eps)), k)

    far_overlap = abs(complex(np.vdot(lo.upper_vector(), hi.upper_vector())))
    # Local continuity of the adiabatic (eigenvalue-ordered) upper branch.
    local_overlap = abs(complex(np.vdot(mid.upper_vector(),
                                        mid_next.upper_vector())))
    return {
        "x_low": float(x_low),
        "x_high": float(x_high),
        "far_side_upper_overlap": float(far_overlap),
        "characters_swap": bool(far_overlap < 0.5),
        "adiabatic_labelling_is_continuous": bool(local_overlap > 0.99),
        "note": ("the diabatic characters exchange across the crossing, so "
                 "the far-side overlap is small, while the adiabatic "
                 "labelling by eigenvalue order stays continuous"),
        "verdict": DEFAULT_VERDICT,
        "measured_here": MEASURED_HERE,
    }


# --- Landau-Zener transition probability ---------------------------------

def landau_zener_probability(g: complex, sweep_rate: float,
                             hbar: float = HBAR_J_S) -> float:
    """``P = exp(-2*pi*|g|**2 / (hbar * |dDelta/dt|))``.

    The diabatic transition probability for a linear sweep through the
    anticrossing at rate ``sweep_rate = |dDelta/dt|`` (the rate of change
    of the level separation). Limits:

    * ``sweep_rate -> inf`` gives ``P -> 1`` — a fast (sudden) sweep is
      diabatic: the system jumps the gap and keeps its bare character.
    * ``sweep_rate -> 0`` gives ``P -> 0`` — a slow sweep is adiabatic:
      the system follows the eigenvalue branch around the gap.

    ``g == 0`` gives ``P == 1`` for any positive rate: with no gap there
    is nothing to follow.
    """
    gmag = abs(_finite_complex(g, "the coupling g"))
    rate = _finite(sweep_rate, "the sweep rate")
    h = _finite(hbar, "hbar")
    if rate < 0.0:
        raise AvoidedError("the sweep rate is a magnitude and cannot be "
                           "negative")
    if h <= 0.0:
        raise AvoidedError("hbar must be positive")
    if rate == 0.0:
        # Perfectly adiabatic limit: the exponent diverges, P -> 0.
        return 0.0
    exponent = -2.0 * math.pi * gmag ** 2 / (h * rate)
    return float(math.exp(exponent))


def landau_zener_limits(g: complex = 1.0, hbar: float = 1.0) -> dict:
    """The two limits of :func:`landau_zener_probability`, stated together.

    A fast sweep is diabatic and a slow sweep is adiabatic; the crossover
    rate ``2*pi*|g|**2/hbar`` is where the exponent is order one. The two
    reported rates straddle it by six decades, so the fast one is
    essentially diabatic and the slow one essentially adiabatic. Stated in
    natural units (``g = hbar = 1``) by default so the limits are legible;
    the physics depends only on the dimensionless ratio.
    """
    gmag = abs(_finite_complex(g, "the coupling g"))
    h = _finite(hbar, "hbar")
    if h <= 0.0:
        raise AvoidedError("hbar must be positive")
    if gmag <= 0.0:
        raise AvoidedError("the limits need a non-zero coupling")
    crossover = 2.0 * math.pi * gmag ** 2 / h
    fast = landau_zener_probability(gmag, crossover * 1e6, h)
    slow = landau_zener_probability(gmag, crossover * 1e-6, h)
    return {
        "coupling_magnitude": gmag,
        "crossover_rate": crossover,
        "fast_sweep_probability": fast,
        "slow_sweep_probability": slow,
        "fast_is_diabatic": bool(fast > 0.99),
        "slow_is_adiabatic": bool(slow < 0.01),
        "note": ("a fast sweep jumps the gap (P -> 1, diabatic); a slow "
                 "sweep follows the branch (P -> 0, adiabatic)"),
        "verdict": DEFAULT_VERDICT,
        "measured_here": MEASURED_HERE,
    }


# --- the load-bearing refusal --------------------------------------------

def refuse_model_crossing_as_measured(
        minimum_gap: float | None = None,
        claim: str = "the modelled anticrossing is an observed mode "
                     "repulsion") -> None:
    """Refuse reading a modelled anticrossing as a measured mode repulsion.

    Always raises. A minimum gap computed here is arithmetic on a declared
    2x2 Hamiltonian: it has no linewidth, no calibrated tuning axis, no
    apparatus and no uncertainty budget. An observed mode repulsion is a
    bench result — two real modes tuned through each other, a measured
    splitting resolved above the linewidth, and a coupling extracted from
    the data. The one does not become the other by sharing a formula.
    """
    said = f" Claim: {claim!r}." if claim else ""
    where = "" if minimum_gap is None else f" (minimum gap {minimum_gap})"
    raise AvoidedError(
        f"refusing to read a modelled avoided crossing{where} as an "
        f"observed mode repulsion.{said} The gap here is a closed form on "
        f"a declared two-level Hamiltonian — an ANALYTIC_MODEL — with no "
        f"resonator, no tuned levels, no measured splitting, no linewidth "
        f"and no calibration. A real anticrossing is a BENCH_MEASUREMENT: "
        f"two physical modes swept through resonance, a splitting resolved "
        f"above the linewidth, and a coupling fitted to the data. Shared "
        f"algebra is not a shared observation, and nothing here is "
        f"measured.")


# --- report --------------------------------------------------------------

def avoided_report(verdict: str = DEFAULT_VERDICT) -> dict:
    """One statement of what this module computes and, loudly, disclaims."""
    demo = avoided_crossing_sweep(lambda x: x, lambda x: -x, 0.05,
                                  n_points=201, span=1.0)
    limits = landau_zener_limits()
    return {
        "claim_class": CLAIM_CLASS,
        "what_this_is": (
            "the closed-form theory of an avoided crossing in a two-level "
            "system: the 2x2 Hamiltonian H = [[E1, g], [conj(g), E2]], its "
            "eigenvalues mean -/+ sqrt(delta**2 + |g|**2), the minimum gap "
            "2*|g|, the eigenvector swap across the crossing, and the "
            "Landau-Zener transition probability"),
        "the_gap": {
            "formula": "gap = 2*sqrt(delta**2 + |g|**2)",
            "minimum": "2*|g|, at delta = 0",
            "crosses_only_when_uncoupled": "gap = 0 iff g = 0",
        },
        "the_sweep": {
            "coupling_magnitude": demo["coupling_magnitude"],
            "minimum_gap": demo["minimum_gap"],
            "expected_minimum_gap": demo["expected_minimum_gap"],
            "minimum_matches_twice_the_coupling":
                demo["minimum_matches_twice_the_coupling"],
            "branches_never_cross": demo["branches_never_cross"],
        },
        "landau_zener": limits,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "what_this_does_not_say": (
            "It does not say any two-level system, resonator or pair of "
            "modes exists, that any level was tuned, or that any gap, "
            "splitting, coupling or transition probability was measured. "
            "Every level, coupling and sweep is a declared input, and the "
            "spectrum is a closed form on it. It does not say that a "
            "minimum gap in this model spectrum is an observed mode "
            "repulsion — that is a bench measurement with a linewidth and "
            "a calibrated tuning axis, and refuse_model_crossing_as_"
            "measured refuses the identification. It does not say the "
            "Landau-Zener formula was verified against any dynamics; it is "
            "the standard analytic result, stated, not simulated."),
        "verdict": verdict,
    }


__all__ = [
    "DEFAULT_VERDICT", "CLAIM_CLASS", "MEASURED_HERE", "PHYSICAL_VALIDATION",
    "HBAR_J_S", "GAP_TOL",
    "AvoidedError",
    "avoided_gap", "two_level_hamiltonian", "TwoLevelSpectrum",
    "two_level_spectrum", "avoided_crossing_sweep",
    "diabatic_adiabatic_swap",
    "landau_zener_probability", "landau_zener_limits",
    "refuse_model_crossing_as_measured",
    "avoided_report",
]
