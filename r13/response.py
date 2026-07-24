"""P05 — one linear-response core, with typed domain adapters.

Linear response is written the same way everywhere: a system driven at a
frequency answers through a complex response function, and four
apparently different objects are the same object seen from four sides.

* A **damped oscillator** answers a drive through its Green function
  ``G(w) = 1/(w0**2 - w**2 - i*gamma*w)``. Its magnitude peaks at
  resonance and the full width at half maximum of ``|G|**2`` is, in the
  weakly damped limit, the damping rate ``gamma`` itself.
* A **susceptibility** ``chi(w)`` has a real and an imaginary part that
  are not independent: causality ties them by the Kramers-Kronig
  relation, and for a Lorentzian the real part reconstructed from the
  imaginary part by the Hilbert transform matches the analytic real part.
  That identity is the load-bearing test of this module.
* A **lossless scatterer** is a unitary ``S`` matrix: ``S^dagger S = I``,
  so ``|out|**2 == |in|**2`` and no energy is created or destroyed at the
  junction.
* A **state-space** system ``(A, B, C, D)`` has the transfer function
  ``H(s) = C (sI - A)^-1 B + D``, which for a single real pole is exactly
  ``1/(s + a)``.

All four are gathered behind a common :class:`LinearSystem` interface with
``response(omega)``, and three typed adapters — MECHANICAL, ELECTRICAL_BVD
and OPTICAL — each build a ``green_oscillator``-style response in their own
units.

**A shared response function is not a shared mechanism.** That an optical
cavity, a mass on a spring, and a quartz motional branch all answer
through the same Lorentzian is a fact about the mathematics of linear
response, not a licence to carry a number from one to another.
:func:`refuse_cross_domain_without_certificate` refuses any such transfer;
the certificate that could license it lives in the bridge module, not
here. :func:`refuse_simulation_as_measurement` refuses to read any number
this module computes as a bench result.

Nothing here is measured. Every response function is evaluated on a
declared model; no oscillator, cavity, scatterer or circuit exists.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

import numpy as np

# --- verdict, claim class, tolerances ------------------------------------

DEFAULT_VERDICT = "LINEAR_RESPONSE_CORE_IMPLEMENTED"

#: What this module's own output is: an analytic model evaluated in this
#: repository. The individual adapters name established physics as their
#: source, but the numbers here are model evaluations, not measurements.
CLAIM_CLASS = "ANALYTIC_MODEL"

#: The claim classes an adapter or a result may declare.
CLAIM_CLASSES = (
    "EXACT_IDENTITY",
    "SOURCE_ESTABLISHED_PHYSICS",
    "CONVENTIONAL_LITERATURE",
    "DERIVED_ARITHMETIC",
    "ANALYTIC_MODEL",
    "NUMERICAL_SIMULATION",
    "REPOSITORY_COMPUTATIONAL_RESULT",
    "ENGINEERING_CANDIDATE",
    "SOURCE_CLAIM",
    "RETROSPECTIVE_NUMERIC_MATCH",
    "PROSPECTIVE_PREDICTION",
    "BENCH_MEASUREMENT",
    "UNSUPPORTED",
    "BLOCKED_MISSING_INPUT",
)

#: Tolerance on the unitarity of a scattering matrix.
UNITARY_TOL = 1e-12


class ResponseError(RuntimeError):
    """Raised when a linear-response claim exceeds what the algebra licenses.

    Covers the structural refusals (a non-finite frequency, a non-uniform
    Kramers-Kronig grid, a non-square state matrix) and the two
    load-bearing governance refusals:
    :func:`refuse_cross_domain_without_certificate` and
    :func:`refuse_simulation_as_measurement`.
    """


def _finite(value: float, what: str) -> float:
    """Coerce to float and refuse anything non-finite."""
    x = float(value)
    if not math.isfinite(x):
        raise ResponseError(f"{what} must be finite")
    return x


# --- (1) the damped-oscillator Green function ----------------------------

def green_oscillator(w, w0: float, gamma: float):
    """``G(w) = 1/(w0**2 - w**2 - i*gamma*w)``, the driven-oscillator response.

    Accepts a scalar or an array of drive frequencies ``w`` and returns a
    complex response of the same shape. ``|G|`` peaks near the resonance
    ``w0``; at ``w == w0`` the response is purely imaginary,
    ``i/(gamma*w0)``, so its magnitude there is ``1/(gamma*w0)``.
    """
    w0f = _finite(w0, "the resonance frequency w0")
    gf = _finite(gamma, "the damping rate gamma")
    if w0f <= 0.0:
        raise ResponseError("the resonance frequency w0 must be positive")
    if gf <= 0.0:
        raise ResponseError(
            "the damping rate gamma must be positive: a lossless "
            "oscillator has a pole on the real axis and no finite response "
            "at resonance")
    wf = np.asarray(w, dtype=float)
    denom = (w0f ** 2 - wf ** 2) - 1j * gf * wf
    return 1.0 / denom


def half_width_of_power(w, w0: float, gamma: float) -> float:
    """The FWHM of ``|G(w)|**2`` measured on a supplied frequency grid.

    ``w`` must be a fine, sorted grid straddling the resonance. The peak
    value of ``|G|**2`` is found on the grid and the two frequencies where
    ``|G|**2`` falls to half that value are located by linear
    interpolation; their separation is returned. In the weakly damped
    limit this equals ``gamma``.
    """
    grid = np.asarray(w, dtype=float)
    if grid.ndim != 1 or grid.size < 8:
        raise ResponseError("a FWHM needs a 1-D grid of at least eight points")
    if not np.all(np.diff(grid) > 0.0):
        raise ResponseError("the FWHM grid must be strictly increasing")
    power = np.abs(green_oscillator(grid, w0, gamma)) ** 2
    peak = int(np.argmax(power))
    half = 0.5 * power[peak]

    def _cross(lo: int, hi: int) -> float:
        # linear interpolation of the grid point where power == half
        p_lo, p_hi = power[lo], power[hi]
        if p_hi == p_lo:
            return float(grid[lo])
        frac = (half - p_lo) / (p_hi - p_lo)
        return float(grid[lo] + frac * (grid[hi] - grid[lo]))

    left = None
    for i in range(peak, 0, -1):
        if power[i] >= half >= power[i - 1]:
            left = _cross(i - 1, i)
            break
    right = None
    for i in range(peak, grid.size - 1):
        if power[i] >= half >= power[i + 1]:
            right = _cross(i, i + 1)
            break
    if left is None or right is None:
        raise ResponseError(
            "the grid does not bracket both half-maximum crossings; widen "
            "the frequency window around the resonance")
    return right - left


# --- (2) susceptibility and the Kramers-Kronig identity ------------------

def lorentzian_chi(w, w0: float, gamma: float):
    """A Lorentzian susceptibility ``chi(w) = 1/(w0**2 - w**2 - i*gamma*w)``.

    Identical in form to :func:`green_oscillator`; named separately because
    here it is read as a susceptibility whose real and imaginary parts are
    tied by causality. Its imaginary part is ``gamma*w/D`` and its real
    part is ``(w0**2 - w**2)/D`` with ``D = (w0**2 - w**2)**2 + gamma**2 w**2``.
    """
    return green_oscillator(w, w0, gamma)


def kramers_kronig_real_from_imag(imag, w):
    """Reconstruct ``Re chi(w)`` from ``Im chi(w)`` by the Hilbert transform.

    Implements the Kramers-Kronig relation

        ``Re chi(w) = (1/pi) P integral Im chi(w') / (w' - w) dw'``

    on a uniform frequency grid ``w`` by the principal-value rectangle
    rule that omits the singular sample. It is the numerical statement that
    the real and imaginary parts of a causal response are not independent:
    for a susceptibility that vanishes at infinity, one determines the
    other. Returns an array the same shape as ``imag``.
    """
    im = np.asarray(imag, dtype=float)
    grid = np.asarray(w, dtype=float)
    if im.shape != grid.shape or im.ndim != 1:
        raise ResponseError(
            "the imaginary part and the frequency grid must be 1-D and the "
            "same length")
    if grid.size < 16:
        raise ResponseError("the Kramers-Kronig grid is too coarse")
    steps = np.diff(grid)
    dw = float(steps[0])
    if dw <= 0.0 or not np.allclose(steps, dw, rtol=1e-9, atol=0.0):
        raise ResponseError(
            "the Kramers-Kronig relation is discretised here on a uniform "
            "grid; supply an evenly spaced, increasing frequency array")
    real = np.empty_like(im)
    for i in range(grid.size):
        diff = grid - grid[i]
        diff[i] = 1.0                      # placeholder; the term is zeroed
        contrib = im / diff
        contrib[i] = 0.0                   # omit the singular sample (PV)
        real[i] = float(np.sum(contrib)) * dw / math.pi
    return real


# --- (3) the lossless 2x2 scatterer --------------------------------------

def smatrix_beamsplitter(theta: float, phi: float = 0.0) -> np.ndarray:
    """A lossless 2x2 beamsplitter scattering matrix, exactly unitary.

        ``S = [[cos t, -exp(-i phi) sin t], [exp(i phi) sin t, cos t]]``

    for splitting angle ``t = theta`` and relative phase ``phi``. Every
    such ``S`` satisfies ``S^dagger S = I`` identically, so it conserves
    energy: for any input ``x``, ``|S x|**2 == |x|**2``.
    """
    t = _finite(theta, "the splitting angle theta")
    p = _finite(phi, "the phase phi")
    c, s = math.cos(t), math.sin(t)
    e = complex(math.cos(p), math.sin(p))
    return np.array([[c, -s / e], [s * e, c]], dtype=complex)


def is_unitary(matrix, tol: float = UNITARY_TOL) -> bool:
    """True iff ``S^dagger S`` equals the identity within ``tol``."""
    m = np.asarray(matrix, dtype=complex)
    if m.ndim != 2 or m.shape[0] != m.shape[1]:
        raise ResponseError("unitarity is defined only for a square matrix")
    return bool(np.allclose(m.conj().T @ m, np.eye(m.shape[0]),
                            atol=tol, rtol=0.0))


def scatter(matrix, amplitudes) -> np.ndarray:
    """Apply a scattering matrix to input amplitudes: ``out = S @ in``."""
    m = np.asarray(matrix, dtype=complex)
    x = np.asarray(amplitudes, dtype=complex)
    if m.shape[1] != x.shape[0]:
        raise ResponseError("the input dimension does not match the matrix")
    return m @ x


# --- (4) state-space to transfer function --------------------------------

def statespace_transfer(A, B, C, D, s: complex) -> complex:
    """``H(s) = C (sI - A)^-1 B + D`` for a state-space system, at ``s``.

    For a single real pole ``A = [[-a]]``, ``B = [[1]]``, ``C = [[1]]``,
    ``D = [[0]]`` this is exactly ``1/(s + a)``. Returns a scalar for a
    single-input single-output system, otherwise the corresponding entry
    of the transfer matrix collapsed to a Python complex when it is 1x1.
    """
    Am = np.asarray(A, dtype=complex)
    Bm = np.atleast_2d(np.asarray(B, dtype=complex))
    Cm = np.atleast_2d(np.asarray(C, dtype=complex))
    Dm = np.atleast_2d(np.asarray(D, dtype=complex))
    if Am.ndim != 2 or Am.shape[0] != Am.shape[1]:
        raise ResponseError("the state matrix A must be square")
    n = Am.shape[0]
    if Bm.shape[0] != n:
        Bm = Bm.reshape(n, -1)
    if Cm.shape[1] != n:
        Cm = Cm.reshape(-1, n)
    sc = complex(s)
    resolvent = np.linalg.inv(sc * np.eye(n) - Am)
    H = Cm @ resolvent @ Bm + Dm
    if H.shape == (1, 1):
        return complex(H[0, 0])
    return H


# --- (5) the common interface and the typed domain adapters --------------

class ResponseDomain(Enum):
    """Three domains that share the linear-response core, not a mechanism."""

    MECHANICAL = "MECHANICAL"
    ELECTRICAL_BVD = "ELECTRICAL_BVD"
    OPTICAL = "OPTICAL"


@runtime_checkable
class LinearSystem(Protocol):
    """Anything that answers a drive frequency with a complex response."""

    def response(self, omega) -> complex:  # pragma: no cover - protocol
        ...


@dataclass(frozen=True)
class DampedOscillatorSystem:
    """A single-resonance linear system, in one domain's units.

    ``w0`` and ``gamma`` carry whatever units the adapter that built the
    system works in; the class does not know what they are, which is
    exactly why a response computed here does not transfer to another
    domain — see :func:`refuse_cross_domain_without_certificate`.
    """

    w0: float
    gamma: float
    domain: ResponseDomain
    units: str
    source: str
    source_class: str = "SOURCE_ESTABLISHED_PHYSICS"

    def __post_init__(self) -> None:
        if not isinstance(self.domain, ResponseDomain):
            raise ResponseError("a system must name a ResponseDomain member")
        if _finite(self.w0, "w0") <= 0.0 or _finite(self.gamma, "gamma") <= 0.0:
            raise ResponseError("w0 and gamma must be positive")
        for name in ("units", "source"):
            if not str(getattr(self, name)).strip():
                raise ResponseError(f"a system must declare a non-empty {name}")
        if self.source_class not in CLAIM_CLASSES:
            raise ResponseError(
                f"{self.source_class!r} is not a declared claim class")

    def response(self, omega) -> complex:
        """The Green-function response at drive frequency ``omega``."""
        g = green_oscillator(omega, self.w0, self.gamma)
        return complex(g) if np.ndim(g) == 0 else g

    @property
    def resonance_magnitude(self) -> float:
        """``|G(w0)| = 1/(gamma*w0)``, the on-resonance response magnitude."""
        return 1.0 / (self.gamma * self.w0)

    def as_dict(self) -> dict:
        return {
            "domain": self.domain.value,
            "w0": self.w0,
            "gamma": self.gamma,
            "units": self.units,
            "source": self.source,
            "source_class": self.source_class,
            "resonance_magnitude": self.resonance_magnitude,
            "measured_here": "nothing",
        }


def mechanical_oscillator(w0: float = 6.2831853e3, gamma: float = 5.0
                          ) -> DampedOscillatorSystem:
    """A mass-spring-damper resonance, angular frequency and rate in rad/s."""
    return DampedOscillatorSystem(
        w0=w0, gamma=gamma, domain=ResponseDomain.MECHANICAL,
        units="rad/s for w0 and gamma; the response is metres per newton",
        source=("the driven damped harmonic oscillator "
                "m x'' + c x' + k x = F, standard mechanics"))


def electrical_bvd_oscillator(w0: float = 8.1681e7, gamma: float = 2.0e3
                              ) -> DampedOscillatorSystem:
    """A Butterworth-Van Dyke motional branch, rad/s; the response is an admittance."""
    return DampedOscillatorSystem(
        w0=w0, gamma=gamma, domain=ResponseDomain.ELECTRICAL_BVD,
        units="rad/s for w0 and gamma; the response is an admittance in siemens",
        source=("the motional branch R1-L1-C1 of the Butterworth-Van Dyke "
                "equivalent circuit, a series RLC resonance"))


def optical_cavity_oscillator(w0: float = 1.77e15, gamma: float = 1.0e10
                              ) -> DampedOscillatorSystem:
    """An optical-cavity mode as a damped resonance, rad/s; a field response."""
    return DampedOscillatorSystem(
        w0=w0, gamma=gamma, domain=ResponseDomain.OPTICAL,
        units="rad/s for w0 and gamma; the response is a field amplitude ratio",
        source=("a single longitudinal cavity mode treated as a damped "
                "resonance, the Lorentzian line of a Fabry-Perot cavity"))


ADAPTERS = {
    ResponseDomain.MECHANICAL: mechanical_oscillator,
    ResponseDomain.ELECTRICAL_BVD: electrical_bvd_oscillator,
    ResponseDomain.OPTICAL: optical_cavity_oscillator,
}


# --- (6) the two governance refusals -------------------------------------

def refuse_cross_domain_without_certificate(a_domain: ResponseDomain,
                                            b_domain: ResponseDomain) -> None:
    """Refuse to carry a response between domains without a certificate.

    A shared response function is not a shared mechanism. That a mechanical
    resonance, an electrical motional branch and an optical cavity all
    answer through the same Lorentzian is a fact about linear response, not
    permission to read one domain's number in another's units. Such a
    transfer is licensed only by a typed coupling certificate, and that
    certificate lives in the bridge module — never implicitly here.
    """
    if not (isinstance(a_domain, ResponseDomain)
            and isinstance(b_domain, ResponseDomain)):
        raise ResponseError("both arguments must be ResponseDomain members")
    raise ResponseError(
        f"refused: a response computed in the {a_domain.value} domain may "
        f"not be transferred to the {b_domain.value} domain on the strength "
        f"of a shared Lorentzian. A common response function is not a "
        f"common mechanism; the transfer needs a typed cross-domain "
        f"coupling certificate, which is defined in the bridge module and "
        f"is a licence to model, not a measurement.")


def refuse_simulation_as_measurement(*_a, **_k) -> None:
    """A response function evaluated here is a model, never a bench result."""
    raise ResponseError(
        "refused: an ANALYTIC_MODEL or REPOSITORY_COMPUTATIONAL_RESULT "
        "evaluated in this module is not a BENCH_MEASUREMENT. No "
        "oscillator, cavity, scatterer or circuit was operated; every "
        "number is a model evaluation.")


# --- (7) the report ------------------------------------------------------

def response_report() -> dict:
    return {
        "what_this_is": (
            "one linear-response core — Green function, Kramers-Kronig "
            "susceptibility, unitary S-matrix, state-space transfer "
            "function — behind a common LinearSystem interface with three "
            "typed domain adapters"),
        "domains": [d.value for d in ResponseDomain],
        "load_bearing_identity": (
            "Kramers-Kronig: the real part of a Lorentzian susceptibility "
            "reconstructed from its imaginary part by the Hilbert transform "
            "matches the analytic real part"),
        "claim_class": CLAIM_CLASS,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": DEFAULT_VERDICT,
        "what_this_does_not_say": (
            "It does not say a mechanical resonance, an electrical motional "
            "branch and an optical cavity are the same physics because they "
            "share a Lorentzian, nor that any response computed here was "
            "measured. A shared response function is not a shared mechanism, "
            "a cross-domain transfer needs the bridge-module certificate, "
            "and no apparatus was operated."),
    }
