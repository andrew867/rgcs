"""R11 P12 — multiscale mode mixing: one algebra, five typed domains.

Two oscillators that talk to each other hybridise. Write the coupling as
a Hermitian matrix ``[[w1, k], [k, w2]]`` and everything follows from two
lines of algebra: the eigenvalues split by ``sqrt((w1-w2)**2 + 4*k**2)``,
they **repel** rather than cross, the minimum splitting as the bare modes
are tuned through each other is exactly ``2*|k|``, and the mixing angle
``theta = 0.5*atan2(2k, w1-w2)`` passes through 45 degrees at zero
detuning, where each hybrid is half one bare mode and half the other.

That algebra is domain-free, and this module implements it once, in
:class:`CoupledModeSystem`, :func:`eigen_split`, :func:`avoided_crossing`
and :func:`participation`. Five physically different mixing problems then
**reuse** it:

* ``ATOMIC_LATTICE_PHONON`` — a two-atom basis with unequal ionic masses:
  acoustic and optical branches, wavevector-dependent coupling, rad/s
  against rad/m.
* ``MACROSCOPIC_QUARTZ_ELASTIC`` — thickness-shear against flexure, twist
  and spurious anharmonics on a contoured plate: Hz, mode shapes, modal
  strain and kinetic energy fractions, bevel-dependent frequency, energy
  trapping.
* ``BVD_ELECTRICAL`` — the Butterworth-Van Dyke motional branch
  ``(R1, L1, C1)`` across a static ``C0``: ohms, henries, farads, Hz.
* ``OPTICAL_CAVITY_TRANSVERSE`` — transverse modes mixed by mirror
  misalignment and non-spherical figure: mode indices, metres, Hz.
* ``DYNAMIC_BOUNDARY`` — the Bogoliubov lane of ``r11/dynboundary.py``:
  photon number, and a mixing that is *hyperbolic*, not a rotation.

**The firewall is the point of the module.** Shared matrix mathematics
does not make the mechanisms physically interchangeable. Every adapter
carries its own units, its own source, and its own
``does_not_license`` string, and four refusals are load-bearing:

* :func:`refuse_cross_domain_transfer` raises for *any* ordered pair of
  different domains. The canonical case is a III-V atomic-lattice result
  quoted at an alpha-quartz macroscopic plate: alpha quartz is a
  different lattice — trigonal, three SiO2 formula units per primitive
  cell, its own force constants, its own eigenvectors, piezoelectric,
  with LO-TO splitting a diatomic chain has no term for — and a plate
  mode at megahertz is separated from a phonon branch at terahertz by
  the entire continuum limit.
* :func:`refuse_shared_math_as_shared_mechanism` raises because identical
  eigenvalue algebra is evidence about algebra, not about physics. The
  ``DYNAMIC_BOUNDARY`` adapter makes the point concrete: its
  photon-number-conserving part *is* a rotation, and its Bogoliubov part
  is a squeeze preserving ``|alpha|**2 - |beta|**2`` rather than a sum of
  squares. Same 2x2 shape, different invariant, different physics.
* :func:`refuse_modal_truncation_as_physical_cut` raises because keeping
  the first ``n`` modes of a basis is a numerical approximation with a
  convergence error, not a physical operation on a phonon.
* :func:`refuse_unit_comparison` raises when numbers from two domains
  with different units are compared by magnitude alone.

Nothing here is measured. No lattice, plate, resonator, cavity or
boundary exists; every number is arithmetic on a declared model, and the
standing verdict is that the domains are typed and not interchangeable.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

import numpy as np

from . import dynboundary

# --- verdicts, claim class, tolerances -----------------------------------

DEFAULT_VERDICT = "MODE_MIXING_DOMAINS_TYPED_NOT_INTERCHANGEABLE"

VERDICTS = (
    DEFAULT_VERDICT,
    "AVOIDED_CROSSING_MINIMUM_SPLITTING_IS_TWICE_THE_COUPLING",
    "SHARED_ALGEBRA_IS_NOT_SHARED_MECHANISM",
    "MODAL_TRUNCATION_IS_NUMERICAL_NOT_PHYSICAL",
    "CROSS_DOMAIN_TRANSFER_REFUSED",
    "UNIT_COMPARISON_REFUSED",
    "PHYSICAL_VALIDATION_NOT_CLAIMED",
)

#: What this module's own output is: arithmetic performed in this
#: repository on declared models. The individual adapters name their own
#: source class, which for the textbook lanes is established physics.
CLAIM_CLASS = "REPOSITORY_COMPUTATIONAL_RESULT"

#: The claim classes an adapter is allowed to declare.
CLAIM_CLASSES = (
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

EVIDENCE_CLASS = "DERIVED_MATHEMATICS"

#: Tolerance on the Hermitian symmetry of a coupling matrix.
HERMITIAN_TOL = 1e-12

#: Relative tolerance used when a closed form is compared with a
#: numerical eigendecomposition.
SPLIT_TOL = 1e-10

#: Unified atomic mass constant, SI (CODATA). Used only to convert
#: declared model masses; no mass here is measured.
AMU_KG = 1.66053906660e-27


class ModeMixError(RuntimeError):
    """Raised when a mode-mixing claim exceeds what the algebra licenses.

    Covers the structural refusals (a non-Hermitian coupling matrix, a
    non-positive circuit element, an overlap outside the first-order
    expansion) and the four load-bearing firewalls:
    :func:`refuse_cross_domain_transfer`,
    :func:`refuse_shared_math_as_shared_mechanism`,
    :func:`refuse_modal_truncation_as_physical_cut` and
    :func:`refuse_unit_comparison`.
    """


# --- (1) the shared core: a Hermitian coupling matrix --------------------

def _finite(value: float, what: str) -> float:
    """Coerce to float and refuse anything non-finite."""
    x = float(value)
    if not math.isfinite(x):
        raise ModeMixError(f"{what} must be finite")
    return x


def _as_hermitian(matrix) -> np.ndarray:
    """Validate a square Hermitian coupling matrix of at least 2x2."""
    m = np.asarray(matrix, dtype=complex)
    if m.ndim != 2 or m.shape[0] != m.shape[1]:
        raise ModeMixError("a coupling matrix must be square")
    if m.shape[0] < 2:
        raise ModeMixError("mode mixing needs at least two modes")
    if not np.all(np.isfinite(m)):
        raise ModeMixError("a coupling matrix must be finite")
    if not np.allclose(m, m.conj().T, atol=HERMITIAN_TOL, rtol=0.0):
        raise ModeMixError(
            "a coupling matrix must be Hermitian: a non-Hermitian matrix "
            "has complex eigenvalues and no orthogonal hybrid basis, so "
            "neither a splitting nor a participation fraction means "
            "anything for it")
    return m


@dataclass(frozen=True, eq=False)
class CoupledModeSystem:
    """An NxN Hermitian coupling matrix, and nothing else.

    Deliberately domain-free: the diagonal holds bare mode quantities and
    the off-diagonal holds couplings, both in whatever units the *caller*
    is working in. The class has no opinion about what those units are,
    which is exactly why a result computed with it does not transfer
    between domains — see :func:`refuse_cross_domain_transfer`.
    """

    matrix: np.ndarray

    def __post_init__(self) -> None:
        object.__setattr__(self, "matrix", _as_hermitian(self.matrix))

    @classmethod
    def two_mode(cls, w1: float, w2: float,
                 coupling: complex = 0.0) -> "CoupledModeSystem":
        """``[[w1, k], [conj(k), w2]]``, the canonical 2x2."""
        k = complex(coupling)
        if not (math.isfinite(k.real) and math.isfinite(k.imag)):
            raise ModeMixError("the coupling must be finite")
        return cls(np.array([[_finite(w1, "w1"), k],
                             [np.conj(k), _finite(w2, "w2")]],
                            dtype=complex))

    @property
    def n(self) -> int:
        return int(self.matrix.shape[0])

    def eigendecomposition(self) -> tuple[np.ndarray, np.ndarray]:
        """Ascending eigenvalues and their orthonormal eigenvectors."""
        values, vectors = np.linalg.eigh(self.matrix)
        return np.real(values), vectors

    def eigenvalues(self) -> np.ndarray:
        """The hybridised eigenvalues, ascending."""
        return self.eigendecomposition()[0]

    def participation(self) -> np.ndarray:
        """``P[i, j]``: fraction of hybrid ``j`` sitting in bare mode ``i``.

        ``|V|**2`` for a unitary ``V``, so every row and every column sums
        to one: the hybrids exhaust the bare basis and the bare modes
        exhaust the hybrids. Nothing is lost and nothing is invented.
        """
        _, vectors = self.eigendecomposition()
        return np.abs(vectors) ** 2

    def splitting(self) -> float:
        """The full spread ``max(eigenvalue) - min(eigenvalue)``."""
        values = self.eigenvalues()
        return float(values[-1] - values[0])


@dataclass(frozen=True, eq=False)
class EigenSplit:
    """The closed-form hybridisation of two coupled modes.

    ``lower`` and ``upper`` are the eigenvalues, ``theta_rad`` the mixing
    angle, and ``participation`` the 2x2 array whose ``[i, j]`` entry is
    the fraction of hybrid ``j`` (0 = lower, 1 = upper) in bare mode
    ``i``. Every quantity is in the caller's units; the class does not
    know what they are.
    """

    w1: float
    w2: float
    coupling: float
    lower: float
    upper: float
    theta_rad: float
    participation: np.ndarray

    @property
    def detuning(self) -> float:
        """``w1 - w2``, the bare separation."""
        return self.w1 - self.w2

    @property
    def splitting(self) -> float:
        """``upper - lower``; equals ``2*|k|`` at zero detuning."""
        return self.upper - self.lower

    @property
    def mixing_angle_deg(self) -> float:
        return math.degrees(self.theta_rad)

    @property
    def is_maximally_mixed(self) -> bool:
        """True when each hybrid is half of each bare mode."""
        return abs(abs(self.theta_rad) - 0.25 * math.pi) < 1e-9

    def eigenvectors(self) -> np.ndarray:
        """Columns ``[lower, upper]``: ``(-sin t, cos t)`` and
        ``(cos t, sin t)`` for the mixing angle ``t``."""
        c, s = math.cos(self.theta_rad), math.sin(self.theta_rad)
        return np.array([[-s, c], [c, s]], dtype=float)

    def as_dict(self) -> dict:
        return {
            "w1": self.w1,
            "w2": self.w2,
            "coupling": self.coupling,
            "detuning": self.detuning,
            "lower": self.lower,
            "upper": self.upper,
            "splitting": self.splitting,
            "mixing_angle_deg": self.mixing_angle_deg,
            "participation": self.participation.tolist(),
            "measured_here": "nothing",
        }


def eigen_split(w1: float, w2: float, coupling: float) -> EigenSplit:
    """Hybridise two modes: eigenvalues, mixing angle, participation.

    For ``H = [[w1, k], [k, w2]]`` with real ``k``,

        ``lower, upper = mean -/+ 0.5*sqrt((w1-w2)**2 + 4*k**2)``
        ``theta = 0.5*atan2(2k, w1-w2)``

    and the eigenvectors are ``(cos t, sin t)`` for the upper branch and
    ``(-sin t, cos t)`` for the lower one. The splitting depends on the
    coupling only through ``|k|``, so a complex coupling may be passed
    through its magnitude; the general complex case is handled by
    :class:`CoupledModeSystem`.
    """
    a = _finite(w1, "w1")
    b = _finite(w2, "w2")
    k = _finite(coupling, "the coupling")
    delta = a - b
    radius = math.hypot(delta, 2.0 * k)
    mean = 0.5 * (a + b)
    theta = 0.5 * math.atan2(2.0 * k, delta)
    c2, s2 = math.cos(theta) ** 2, math.sin(theta) ** 2
    part = np.array([[s2, c2], [c2, s2]], dtype=float)
    return EigenSplit(a, b, k, mean - 0.5 * radius, mean + 0.5 * radius,
                      theta, part)


def participation(w1: float, w2: float, coupling: float) -> np.ndarray:
    """The 2x2 participation array of :func:`eigen_split`.

    Row ``i`` is bare mode ``i``, column ``j`` is hybrid ``j`` with
    ``0 = lower`` and ``1 = upper``. Rows and columns both sum to one.
    """
    return eigen_split(w1, w2, coupling).participation


def minimum_splitting(coupling: float) -> float:
    """``2*|k|``: the closest two coupled modes can approach."""
    return 2.0 * abs(_finite(coupling, "the coupling"))


def avoided_crossing(reference: float = 1.0, coupling: float = 0.05,
                     detunings=None, n_points: int = 201,
                     span: float | None = None) -> dict:
    """Sweep the detuning through zero and watch the modes repel.

    ``w2`` is held at ``reference`` and ``w1`` is swept across it. The
    eigenvalues never cross while ``k != 0``; the splitting is minimised
    at zero detuning, where it equals ``2*|k|`` exactly and the mixing
    angle is 45 degrees. The sweep grid always contains zero, so the
    minimum is evaluated, not interpolated.
    """
    w2 = _finite(reference, "the reference frequency")
    k = _finite(coupling, "the coupling")
    if detunings is None:
        if n_points < 3 or n_points % 2 == 0:
            raise ModeMixError("a sweep needs an odd n_points of at least 3")
        width = _finite(span if span is not None
                        else max(20.0 * abs(k), 1e-3 * max(1.0, abs(w2))),
                        "the sweep span")
        if width <= 0.0:
            raise ModeMixError("the sweep span must be positive")
        # Built symmetrically about an exact zero so the minimum of the
        # sweep is evaluated at zero detuning rather than near it.
        half = (int(n_points) - 1) // 2
        positive = np.linspace(0.0, width, half + 1)[1:]
        grid = np.concatenate([-positive[::-1], [0.0], positive])
    else:
        grid = np.asarray(list(detunings), dtype=float)
        if grid.size < 3:
            raise ModeMixError("a sweep needs at least three detunings")
        if not np.all(np.isfinite(grid)):
            raise ModeMixError("every detuning must be finite")

    splits = [eigen_split(w2 + float(d), w2, k) for d in grid]
    splitting = np.array([s.splitting for s in splits])
    lower = np.array([s.lower for s in splits])
    upper = np.array([s.upper for s in splits])
    j = int(np.argmin(splitting))
    expected = minimum_splitting(k)
    scale = max(1.0, abs(expected))
    at_zero = [s for s in splits if s.detuning == 0.0]
    angle_zero = (at_zero[0].mixing_angle_deg if at_zero else None)
    never_cross = bool(k != 0.0 and np.all(upper - lower > 0.0))
    return {
        "reference": w2,
        "coupling": k,
        "detuning": grid.tolist(),
        "lower": lower.tolist(),
        "upper": upper.tolist(),
        "splitting": splitting.tolist(),
        "mixing_angle_deg": [s.mixing_angle_deg for s in splits],
        "minimum_splitting": float(splitting[j]),
        "expected_minimum_splitting": expected,
        "detuning_at_minimum": float(grid[j]),
        "grid_contains_zero_detuning": bool(np.any(grid == 0.0)),
        "minimum_matches_twice_the_coupling": bool(
            abs(float(splitting[j]) - expected) <= SPLIT_TOL * scale),
        "splitting_never_below_twice_the_coupling": bool(
            np.all(splitting >= expected - SPLIT_TOL * scale)),
        "branches_never_cross": never_cross,
        "mixing_angle_at_zero_detuning_deg": angle_zero,
        "note": ("as the bare modes are tuned through each other the "
                 "hybrids repel; the closest approach is 2*|k| and the "
                 "hybrids are half-and-half there"),
        "verdict": "AVOIDED_CROSSING_MINIMUM_SPLITTING_IS_TWICE_THE_COUPLING",
        "measured_here": "nothing",
    }


# --- (2) the five typed domains ------------------------------------------

class Domain(Enum):
    """Five physically distinct mixing problems. Not interchangeable.

    Each names a mechanism, a length scale and a set of units. They share
    :class:`CoupledModeSystem` and nothing else.
    """

    ATOMIC_LATTICE_PHONON = "ATOMIC_LATTICE_PHONON"
    MACROSCOPIC_QUARTZ_ELASTIC = "MACROSCOPIC_QUARTZ_ELASTIC"
    BVD_ELECTRICAL = "BVD_ELECTRICAL"
    OPTICAL_CAVITY_TRANSVERSE = "OPTICAL_CAVITY_TRANSVERSE"
    DYNAMIC_BOUNDARY = "DYNAMIC_BOUNDARY"


@dataclass(frozen=True)
class DomainAdapter:
    """What one adapter mixes, in what units, on whose authority.

    ``does_not_license`` is required to be non-empty. An adapter that
    cannot say what its result fails to establish has had its physics
    removed from the description.
    """

    domain: Domain
    units: str
    source: str
    source_class: str
    length_scale: str
    what_mixes: str
    coupling_origin: str
    does_not_license: str

    def __post_init__(self) -> None:
        if not isinstance(self.domain, Domain):
            raise ModeMixError("an adapter must name a Domain member")
        for name in ("units", "source", "length_scale", "what_mixes",
                     "coupling_origin", "does_not_license"):
            if not str(getattr(self, name)).strip():
                raise ModeMixError(
                    f"an adapter must declare a non-empty {name}")
        if self.source_class not in CLAIM_CLASSES:
            raise ModeMixError(
                f"{self.source_class!r} is not a declared claim class")

    def as_dict(self) -> dict:
        return {
            "domain": self.domain.value,
            "units": self.units,
            "source": self.source,
            "source_class": self.source_class,
            "length_scale": self.length_scale,
            "what_mixes": self.what_mixes,
            "coupling_origin": self.coupling_origin,
            "does_not_license": self.does_not_license,
            "measured_here": "nothing",
        }


#: Why a III-V result cannot be carried to alpha quartz, stated once.
ALPHA_QUARTZ_LATTICE_NOTE = (
    "alpha quartz is a DIFFERENT lattice from a III-V zinc-blende "
    "semiconductor. It is trigonal (space group P3121/P3221) with three "
    "SiO2 formula units — nine atoms — per primitive cell, so it carries "
    "27 phonon branches rather than 6; its force-constant tensor, its "
    "eigenvectors and its acoustic anisotropy are its own; it is "
    "piezoelectric, so its polar modes carry LO-TO splitting that a "
    "two-atom chain has no term for; and its bonding is a covalent "
    "network rather than a two-sublattice ionic pair. Nothing about a "
    "III-V acoustic/optical branch structure survives that change of "
    "lattice, and re-using its force constants or its mixing angle in "
    "quartz is a category error.")


DOMAIN_ADAPTERS: dict[Domain, DomainAdapter] = {
    Domain.ATOMIC_LATTICE_PHONON: DomainAdapter(
        domain=Domain.ATOMIC_LATTICE_PHONON,
        units=("rad/s against wavevector in rad/m; masses in kg, force "
               "constants in N/m, lattice constant in m"),
        source=("lattice dynamics of a two-atom-basis crystal: the "
                "dynamical matrix of a III-V zinc-blende cell with "
                "unequal cation and anion masses, giving acoustic and "
                "optical branches"),
        source_class="SOURCE_ESTABLISHED_PHYSICS",
        length_scale="one primitive cell, about 5e-10 m",
        what_mixes=("the two sublattice displacements: in phase at the "
                    "zone centre (acoustic), out of phase (optical)"),
        coupling_origin=("the interatomic force constant carried across "
                         "the cell, phase factor 1 + exp(-i q a), so the "
                         "coupling is wavevector dependent and vanishes "
                         "at the zone boundary"),
        does_not_license=(
            "it does not license any statement about a macroscopic "
            "resonator. A phonon branch at ~1e13 rad/s and a plate mode "
            "at ~1e7 Hz are separated by six orders of magnitude and by "
            "the entire continuum limit, in which the optical branch has "
            "no counterpart at all. " + ALPHA_QUARTZ_LATTICE_NOTE),
    ),
    Domain.MACROSCOPIC_QUARTZ_ELASTIC: DomainAdapter(
        domain=Domain.MACROSCOPIC_QUARTZ_ELASTIC,
        units=("Hz for mode frequencies; dimensionless mode shapes over "
               "the plate; dimensionless strain and kinetic energy "
               "fractions; plate dimensions in m"),
        source=("linear elasticity of a contoured anisotropic plate: "
                "thickness-shear, flexural, twist and spurious "
                "anharmonic overtone modes, with energy trapping under "
                "the electrodes"),
        source_class="SOURCE_ESTABLISHED_PHYSICS",
        length_scale="one plate, about 1e-3 m across",
        what_mixes=("the thickness-shear mode with flexure, twist and "
                    "nearby anharmonic overtones sharing the same plate"),
        coupling_origin=("the overlap of two mode shapes over the plate "
                         "under elastic anisotropy, contour and mounting "
                         "asymmetry; a bevel changes both the frequency "
                         "and the overlap"),
        does_not_license=(
            "it does not license any statement about lattice dynamics. A "
            "plate mode is a continuum solution over millimetres with no "
            "primitive cell in it, so it says nothing about branches, "
            "wavevectors, force constants or optical phonons — and a "
            "measured or modelled plate frequency cannot be read back as "
            "an atomic quantity. It also does not license an electrical "
            "claim: a mode shape is not an impedance, and only a "
            "declared piezoelectric coupling coefficient connects the "
            "two."),
    ),
    Domain.BVD_ELECTRICAL: DomainAdapter(
        domain=Domain.BVD_ELECTRICAL,
        units="ohm, henry, farad and Hz at a two-terminal electrical port",
        source=("the Butterworth-Van Dyke equivalent circuit: a motional "
                "branch R1-L1-C1 in parallel with the static electrode "
                "capacitance C0, the standard small-signal model of a "
                "piezoelectric resonator"),
        source_class="SOURCE_ESTABLISHED_PHYSICS",
        length_scale="a lumped circuit; no length at all",
        what_mixes=("the motional branch with the static capacitance, "
                    "giving series and parallel resonances, and the main "
                    "response with any spurious branch in the same band"),
        coupling_origin=("the capacitance ratio C0/C1 sets the pole-zero "
                         "spacing; a spurious mode appears as a second "
                         "motional branch across the same C0"),
        does_not_license=(
            "it does not license any mechanical or lattice claim. The "
            "BVD elements are an electrical fit at one port: R1, L1 and "
            "C1 are not a mass, a stiffness or a damping of any "
            "identified body, and no mode shape, strain field or phonon "
            "population can be recovered from them. Two resonators with "
            "identical BVD parameters may have entirely different mode "
            "shapes."),
    ),
    Domain.OPTICAL_CAVITY_TRANSVERSE: DomainAdapter(
        domain=Domain.OPTICAL_CAVITY_TRANSVERSE,
        units=("dimensionless transverse mode indices (n, m) and "
               "longitudinal index q; frequencies in Hz; waist, "
               "displacement and wavelength in m; tilt in rad"),
        source=("paraxial Gaussian-mode theory of an optical resonator: "
                "Hermite-Gauss transverse modes spaced by the Gouy "
                "phase, mixed by mirror misalignment and non-spherical "
                "figure through their overlap integrals"),
        source_class="SOURCE_ESTABLISHED_PHYSICS",
        length_scale="a cavity, 1e-2 to 1e0 m, with a waist near 1e-4 m",
        what_mixes=("transverse modes of neighbouring order, and the two "
                    "orientations of a degenerate transverse family when "
                    "the mirror figure is astigmatic"),
        coupling_origin=("the overlap integral of a displaced or tilted "
                         "Gaussian with the unperturbed basis: "
                         "displacement in units of the waist, tilt in "
                         "units of the divergence angle"),
        does_not_license=(
            "it does not license any acoustic, elastic or lattice claim. "
            "The field here is electromagnetic and the modes are "
            "solutions of the paraxial wave equation in free space "
            "between mirrors; a transverse index is not a branch index, "
            "a Gouy phase is not a dispersion relation, and an overlap "
            "integral over a beam profile is not a force constant."),
    ),
    Domain.DYNAMIC_BOUNDARY: DomainAdapter(
        domain=Domain.DYNAMIC_BOUNDARY,
        units=("photon number (dimensionless), squeezing parameter as a "
               "dimensionless rapidity, and mode detunings in units of "
               "the boundary modulation rate"),
        source=("the Bogoliubov treatment of a boundary condition that "
                "changes in time, as implemented in r11/dynboundary.py: "
                "a_out = alpha*a_in + beta*conj(a_in_dagger) with "
                "|alpha|**2 - |beta|**2 == 1"),
        source_class="SOURCE_ESTABLISHED_PHYSICS",
        length_scale="a field mode; the boundary itself has no thickness",
        what_mixes=("positive- and negative-frequency parts of one "
                    "quantum field, and separately two field modes "
                    "converted into each other at fixed total photon "
                    "number"),
        coupling_origin=("the time dependence of the boundary condition; "
                         "the pair-creating part is set by the switching "
                         "time and has no classical analogue"),
        does_not_license=(
            "it does not license reading any other adapter's rotation as "
            "a squeeze, or the reverse. The Bogoliubov mixing is "
            "hyperbolic: it preserves |alpha|**2 - |beta|**2, not a sum "
            "of squares, so it is not a member of the Hermitian family "
            "the shared core implements and it creates quanta where a "
            "rotation only relabels them. It also says nothing "
            "mechanical: there is no mass, stiffness or mode shape in "
            "it, and nothing here is measured."),
    ),
}


def domain_adapter(domain: Domain) -> DomainAdapter:
    """The adapter for one domain."""
    if not isinstance(domain, Domain):
        raise ModeMixError("a domain must be a Domain member")
    if domain not in DOMAIN_ADAPTERS:
        raise ModeMixError(f"no adapter registered for {domain!r}")
    return DOMAIN_ADAPTERS[domain]


def domain_units(domain: Domain) -> str:
    """The units this adapter works in. No two adapters share them."""
    return domain_adapter(domain).units


def domain_source(domain: Domain) -> str:
    """The source this adapter's physics comes from."""
    return domain_adapter(domain).source


def domain_source_class(domain: Domain) -> str:
    """The claim class of this adapter's source."""
    return domain_adapter(domain).source_class


def domain_does_not_license(domain: Domain) -> str:
    """What a result in this domain explicitly fails to establish."""
    return domain_adapter(domain).does_not_license


# --- (3) adapter A: atomic lattice phonons -------------------------------

@dataclass(frozen=True)
class DiatomicChain:
    """A two-atom-basis chain standing in for a III-V primitive cell.

    Unequal masses on the two sublattices, one nearest-neighbour force
    constant, one lattice constant. The dynamical matrix is

        ``D(q) = [[2C/m_a, -C*(1+exp(-i q a))/sqrt(m_a m_b)], [h.c., 2C/m_b]]``

    whose eigenvalues are ``omega**2``. It reproduces the acoustic and
    optical branch structure, the mass-difference gap at the zone
    boundary, and the vanishing of the interbranch coupling there. It is
    one-dimensional: the full zinc-blende problem is a 6x6 dynamical
    matrix with a direction-dependent force-constant tensor, and this
    chain reproduces the branch structure and nothing else.

    The default masses and lattice constant are representative III-V
    values carried as declared model numbers. Nothing is measured.
    """

    mass_a_amu: float = 69.723
    mass_b_amu: float = 74.921595
    force_constant_n_per_m: float = 40.0
    lattice_constant_m: float = 5.6533e-10

    def __post_init__(self) -> None:
        if min(self.mass_a_amu, self.mass_b_amu) <= 0.0:
            raise ModeMixError("both sublattice masses must be positive")
        if self.force_constant_n_per_m <= 0.0:
            raise ModeMixError("the force constant must be positive")
        if self.lattice_constant_m <= 0.0:
            raise ModeMixError("the lattice constant must be positive")

    @property
    def mass_a_kg(self) -> float:
        return self.mass_a_amu * AMU_KG

    @property
    def mass_b_kg(self) -> float:
        return self.mass_b_amu * AMU_KG

    @property
    def zone_boundary_q(self) -> float:
        """``pi/a``, the edge of the first Brillouin zone."""
        return math.pi / self.lattice_constant_m

    def coupling(self, q: float) -> complex:
        """``-C*(1 + exp(-i q a))/sqrt(m_a m_b)``, in rad**2/s**2."""
        a = self.lattice_constant_m
        c = self.force_constant_n_per_m
        scale = c / math.sqrt(self.mass_a_kg * self.mass_b_kg)
        return -scale * (1.0 + complex(math.cos(-q * a), math.sin(-q * a)))

    def coupling_magnitude(self, q: float) -> float:
        """``2C|cos(qa/2)|/sqrt(m_a m_b)``: zero at the zone boundary."""
        return abs(self.coupling(q))

    def dynamical_matrix(self, q: float) -> CoupledModeSystem:
        """The 2x2 Hermitian dynamical matrix at wavevector ``q``."""
        c = self.force_constant_n_per_m
        return CoupledModeSystem(np.array(
            [[2.0 * c / self.mass_a_kg, self.coupling(q)],
             [np.conj(self.coupling(q)), 2.0 * c / self.mass_b_kg]],
            dtype=complex))

    def omega_squared_split(self, q: float) -> EigenSplit:
        """The hybridisation in ``omega**2``, via the shared core.

        The eigenvalues of a Hermitian 2x2 depend on the coupling only
        through its magnitude, so the complex phase factor is passed
        through :meth:`coupling_magnitude`.
        """
        c = self.force_constant_n_per_m
        return eigen_split(2.0 * c / self.mass_a_kg,
                           2.0 * c / self.mass_b_kg,
                           self.coupling_magnitude(q))

    def branches(self, q: float) -> tuple[float, float]:
        """``(omega_acoustic, omega_optical)`` in rad/s at wavevector ``q``."""
        values = self.dynamical_matrix(q).eigenvalues()
        clipped = np.clip(values, 0.0, None)
        return (float(math.sqrt(clipped[0])), float(math.sqrt(clipped[1])))

    def zone_centre_optical_rad_s(self) -> float:
        """``sqrt(2C(1/m_a + 1/m_b))``: the closed form at ``q -> 0``."""
        c = self.force_constant_n_per_m
        return math.sqrt(2.0 * c * (1.0 / self.mass_a_kg
                                    + 1.0 / self.mass_b_kg))

    def zone_boundary_gap_rad_s(self) -> float:
        """The branch gap at ``q = pi/a``, which is a pure mass effect."""
        low, high = self.branches(self.zone_boundary_q)
        return high - low

    def dispersion(self, n_points: int = 41) -> dict:
        """Both branches across the first half Brillouin zone."""
        if n_points < 2:
            raise ModeMixError("a dispersion needs at least two points")
        qs = np.linspace(0.0, self.zone_boundary_q, int(n_points))
        pairs = [self.branches(float(q)) for q in qs]
        acoustic = [p[0] for p in pairs]
        optical = [p[1] for p in pairs]
        return {
            "q_rad_per_m": qs.tolist(),
            "acoustic_rad_s": acoustic,
            "optical_rad_s": optical,
            "coupling_rad2_s2": [self.coupling_magnitude(float(q))
                                 for q in qs],
            "acoustic_starts_at_zero": bool(acoustic[0] < 1e-6 * optical[0]),
            "optical_never_below_acoustic": bool(
                all(o >= a for a, o in zip(acoustic, optical))),
            "zone_boundary_gap_rad_s": self.zone_boundary_gap_rad_s(),
            "units": domain_units(Domain.ATOMIC_LATTICE_PHONON),
            "measured_here": "nothing",
        }


#: The declared III-V model chain used by the report.
DEFAULT_CHAIN = DiatomicChain()


# --- (4) adapter B: macroscopic quartz elastic modes ---------------------

class ElasticMode(Enum):
    """Plate modes that share one resonator and therefore mix."""

    THICKNESS_SHEAR = "THICKNESS_SHEAR"
    FLEXURAL = "FLEXURAL"
    TWIST = "TWIST"
    SPURIOUS_ANHARMONIC = "SPURIOUS_ANHARMONIC"


#: Declared model frequencies near a 13 MHz working point, in Hz. They
#: are chosen numbers for a coupled-mode example, not measurements of any
#: plate.
DEFAULT_PLATE_MODES: dict[ElasticMode, float] = {
    ElasticMode.THICKNESS_SHEAR: 13.000_000e6,
    ElasticMode.FLEXURAL: 12.940_000e6,
    ElasticMode.TWIST: 13.070_000e6,
    ElasticMode.SPURIOUS_ANHARMONIC: 13.012_000e6,
}

ELASTIC_MODE_ROLES: dict[ElasticMode, str] = {
    ElasticMode.THICKNESS_SHEAR:
        "the wanted mode: shear across the plate thickness, trapped "
        "under the electrodes",
    ElasticMode.FLEXURAL:
        "bending of the plate as a whole; low frequency, strongly "
        "mount-coupled, an unwanted neighbour",
    ElasticMode.TWIST:
        "torsion about the plate axis; another unwanted neighbour with "
        "its own mount sensitivity",
    ElasticMode.SPURIOUS_ANHARMONIC:
        "an anharmonic overtone of the wanted mode with extra nodal "
        "lines; near in frequency and hard to separate",
}


def plate_mode_frequency_hz(mode: ElasticMode,
                            frequencies: dict | None = None) -> float:
    """The declared frequency of one plate mode, in Hz."""
    if not isinstance(mode, ElasticMode):
        raise ModeMixError("a plate mode must be an ElasticMode member")
    table = DEFAULT_PLATE_MODES if frequencies is None else frequencies
    if mode not in table:
        raise ModeMixError(f"no declared frequency for {mode!r}")
    return _finite(table[mode], "a plate mode frequency")


def elastic_hybridisation(mode_a: ElasticMode, mode_b: ElasticMode,
                          coupling_hz: float = 4.0e3,
                          frequencies: dict | None = None) -> EigenSplit:
    """Hybridise two plate modes, in Hz, using the shared core."""
    if mode_a is mode_b:
        raise ModeMixError(
            "a mode does not hybridise with itself; name two modes")
    return eigen_split(plate_mode_frequency_hz(mode_a, frequencies),
                       plate_mode_frequency_hz(mode_b, frequencies),
                       _finite(coupling_hz, "the coupling"))


def modal_energy_fractions(omega_rad_s: float, q: float,
                           qdot: float) -> dict:
    """Strain and kinetic fractions of one mode's energy.

    ``E_strain = 0.5*omega**2*q**2`` and ``E_kinetic = 0.5*qdot**2`` for a
    mass-normalised modal coordinate, so the two fractions sum to one by
    construction. At a turning point the energy is all strain; passing
    through zero displacement it is all kinetic. This is the same modal
    bookkeeping used by the classical boundary lane, applied to a plate.
    """
    w = _finite(omega_rad_s, "the modal frequency")
    if w <= 0.0:
        raise ModeMixError("a modal frequency must be positive")
    strain = 0.5 * (w * _finite(q, "the modal displacement")) ** 2
    kinetic = 0.5 * _finite(qdot, "the modal velocity") ** 2
    total = strain + kinetic
    if total <= 0.0:
        raise ModeMixError("a mode with no energy has no energy fractions")
    return {
        "strain_energy": strain,
        "kinetic_energy": kinetic,
        "total_energy": total,
        "strain_fraction": strain / total,
        "kinetic_fraction": kinetic / total,
        "fractions_sum_to_one": True,
        "units": domain_units(Domain.MACROSCOPIC_QUARTZ_ELASTIC),
        "measured_here": "nothing",
    }


#: Declared bevel sensitivity: contouring removes material from the rim,
#: lowering the trapped thickness-shear frequency. The coefficient is a
#: model number, not a measured contour coefficient.
BEVEL_SENSITIVITY_PER_UNIT = -0.02


def bevel_frequency_hz(base_hz: float, bevel_fraction: float,
                       sensitivity: float = BEVEL_SENSITIVITY_PER_UNIT
                       ) -> float:
    """``f = f0 * (1 + sensitivity * bevel_fraction)``.

    A declared linear model of contouring: the bevel fraction is the
    fraction of the plate radius that is contoured, and the sensitivity
    is negative because removing rim material lowers the trapped mode.
    The functional form is a modelling choice; only the monotone trend
    is claimed.
    """
    f0 = _finite(base_hz, "the base frequency")
    if f0 <= 0.0:
        raise ModeMixError("the base frequency must be positive")
    b = _finite(bevel_fraction, "the bevel fraction")
    if not 0.0 <= b <= 1.0:
        raise ModeMixError("the bevel fraction must lie in [0, 1]")
    out = f0 * (1.0 + _finite(sensitivity, "the bevel sensitivity") * b)
    if out <= 0.0:
        raise ModeMixError(
            "this bevel model has driven the frequency to zero: the "
            "linear form has left its domain")
    return out


#: Scale of the declared energy-trapping model, in plateback units.
TRAPPING_SCALE = 0.004


def energy_trapping_fraction(plateback_fraction: float,
                             electrode_radius_ratio: float = 0.5,
                             scale: float = TRAPPING_SCALE) -> float:
    """Fraction of the mode energy held under the electrodes.

    Energy trapping is real physics: mass loading lowers the cutoff
    frequency under the electrodes, so the wanted mode is propagating
    there and evanescent outside, and the trapped fraction rises with the
    plateback (the fractional frequency lowering) and with the electrode
    coverage. The functional form here,
    ``1 - exp(-plateback*coverage/scale)``, is a declared monotone model
    with the right limits (nothing trapped at zero plateback, saturating
    below one), not a plate solution.
    """
    p = _finite(plateback_fraction, "the plateback fraction")
    r = _finite(electrode_radius_ratio, "the electrode radius ratio")
    s = _finite(scale, "the trapping scale")
    if p < 0.0:
        raise ModeMixError("the plateback fraction cannot be negative")
    if not 0.0 < r <= 1.0:
        raise ModeMixError("the electrode radius ratio must lie in (0, 1]")
    if s <= 0.0:
        raise ModeMixError("the trapping scale must be positive")
    return float(1.0 - math.exp(-p * r / s))


# --- (5) adapter C: the BVD electrical branch ----------------------------

def bvd_series_resonance_hz(l1_h: float, c1_f: float) -> float:
    """``fs = 1/(2*pi*sqrt(L1*C1))``. The static C0 does not enter."""
    l1 = _finite(l1_h, "L1")
    c1 = _finite(c1_f, "C1")
    if l1 <= 0.0 or c1 <= 0.0:
        raise ModeMixError("L1 and C1 must be positive")
    return 1.0 / (2.0 * math.pi * math.sqrt(l1 * c1))


def bvd_parallel_resonance_hz(fs_hz: float, c1_f: float,
                              c0_f: float) -> float:
    """``fp = fs*sqrt(1 + C1/C0)``. Above ``fs`` whenever C1, C0 > 0."""
    fs = _finite(fs_hz, "fs")
    c1 = _finite(c1_f, "C1")
    c0 = _finite(c0_f, "C0")
    if fs <= 0.0:
        raise ModeMixError("fs must be positive")
    if c1 <= 0.0 or c0 <= 0.0:
        raise ModeMixError("C1 and C0 must be positive")
    return fs * math.sqrt(1.0 + c1 / c0)


def bvd_quality_factor(fs_hz: float, c1_f: float, r1_ohm: float) -> float:
    """``Q = 1/(2*pi*fs*C1*R1)``, so Q rises as R1 falls."""
    fs = _finite(fs_hz, "fs")
    c1 = _finite(c1_f, "C1")
    r1 = _finite(r1_ohm, "R1")
    if fs <= 0.0 or c1 <= 0.0:
        raise ModeMixError("fs and C1 must be positive")
    if r1 <= 0.0:
        raise ModeMixError("R1 must be positive")
    return 1.0 / (2.0 * math.pi * fs * c1 * r1)


def bvd_quality_factor_from_inductance(fs_hz: float, l1_h: float,
                                       r1_ohm: float) -> float:
    """``Q = 2*pi*fs*L1/R1``: the same Q, from the other reactance.

    Equal to :func:`bvd_quality_factor` on a consistent branch because
    ``2*pi*fs*L1 == 1/(2*pi*fs*C1)`` at series resonance.
    """
    fs = _finite(fs_hz, "fs")
    l1 = _finite(l1_h, "L1")
    r1 = _finite(r1_ohm, "R1")
    if fs <= 0.0 or l1 <= 0.0:
        raise ModeMixError("fs and L1 must be positive")
    if r1 <= 0.0:
        raise ModeMixError("R1 must be positive")
    return 2.0 * math.pi * fs * l1 / r1


def motional_inductance_h(fs_hz: float, c1_f: float) -> float:
    """Invert the series relation: ``L1 = 1/((2*pi*fs)**2 * C1)``."""
    fs = _finite(fs_hz, "fs")
    c1 = _finite(c1_f, "C1")
    if fs <= 0.0 or c1 <= 0.0:
        raise ModeMixError("fs and C1 must be positive")
    return 1.0 / ((2.0 * math.pi * fs) ** 2 * c1)


@dataclass(frozen=True)
class BVDBranch:
    """A Butterworth-Van Dyke branch: R1, L1, C1 across a static C0.

    Every field is a declared circuit element in SI units. Nothing here
    is measured, and no physical resonator is claimed to have these
    values.
    """

    r1_ohm: float
    l1_h: float
    c1_f: float
    c0_f: float

    def __post_init__(self) -> None:
        for name in ("r1_ohm", "l1_h", "c1_f", "c0_f"):
            value = _finite(getattr(self, name), name)
            if value <= 0.0:
                raise ModeMixError(
                    f"{name} must be positive: a BVD branch with a "
                    f"non-positive element is not a passive circuit")

    @classmethod
    def planted(cls, fs_hz: float = 13.0e6, c1_f: float = 5.0e-15,
                r1_ohm: float = 8.0,
                c0_f: float = 3.0e-12) -> "BVDBranch":
        """A branch built to land on a chosen ``fs`` exactly.

        ``C1``, ``R1`` and ``C0`` are planted and ``L1`` is solved from
        the target, so :meth:`series_resonance_hz` returns ``fs_hz`` to
        floating precision. That is what makes the formulas testable
        rather than merely evaluated.
        """
        return cls(r1_ohm=r1_ohm, l1_h=motional_inductance_h(fs_hz, c1_f),
                   c1_f=c1_f, c0_f=c0_f)

    def series_resonance_hz(self) -> float:
        return bvd_series_resonance_hz(self.l1_h, self.c1_f)

    def parallel_resonance_hz(self) -> float:
        return bvd_parallel_resonance_hz(self.series_resonance_hz(),
                                         self.c1_f, self.c0_f)

    def quality_factor(self) -> float:
        return bvd_quality_factor(self.series_resonance_hz(), self.c1_f,
                                  self.r1_ohm)

    def quality_factor_from_inductance(self) -> float:
        return bvd_quality_factor_from_inductance(
            self.series_resonance_hz(), self.l1_h, self.r1_ohm)

    @property
    def capacitance_ratio(self) -> float:
        """``C0/C1``: sets how far the parallel resonance sits above fs."""
        return self.c0_f / self.c1_f

    def pole_zero_spacing_hz(self) -> float:
        """``fp - fs``, strictly positive for any passive branch."""
        return self.parallel_resonance_hz() - self.series_resonance_hz()

    def as_dict(self) -> dict:
        return {
            "r1_ohm": self.r1_ohm,
            "l1_h": self.l1_h,
            "c1_f": self.c1_f,
            "c0_f": self.c0_f,
            "fs_hz": self.series_resonance_hz(),
            "fp_hz": self.parallel_resonance_hz(),
            "q": self.quality_factor(),
            "q_from_inductance": self.quality_factor_from_inductance(),
            "capacitance_ratio": self.capacitance_ratio,
            "pole_zero_spacing_hz": self.pole_zero_spacing_hz(),
            "units": domain_units(Domain.BVD_ELECTRICAL),
            "measured_here": "nothing",
        }


def bvd_hybridisation(branch: BVDBranch, spurious_hz: float,
                      coupling_hz: float = 2.0e3) -> EigenSplit:
    """Hybridise the main response with a spurious branch, in Hz.

    A second motional branch across the same C0 shows up as a second
    resonance; where the two sit close together the responses repel in
    exactly the way the shared core describes. The coupling is a declared
    model number here, not a fitted one.
    """
    if not isinstance(branch, BVDBranch):
        raise ModeMixError("a BVD hybridisation needs a BVDBranch")
    return eigen_split(branch.series_resonance_hz(),
                       _finite(spurious_hz, "the spurious frequency"),
                       _finite(coupling_hz, "the coupling"))


# --- (6) adapter D: optical cavity transverse modes ----------------------

@dataclass(frozen=True)
class CavityMode:
    """A Hermite-Gauss cavity mode ``TEM_{n,m}`` at longitudinal index q."""

    longitudinal: int = 100000
    n_index: int = 0
    m_index: int = 0

    def __post_init__(self) -> None:
        if min(self.n_index, self.m_index) < 0:
            raise ModeMixError("transverse indices cannot be negative")
        if self.longitudinal < 0:
            raise ModeMixError("the longitudinal index cannot be negative")

    @property
    def transverse_order(self) -> int:
        """``n + m``, the order that the Gouy phase counts."""
        return int(self.n_index + self.m_index)

    @property
    def label(self) -> str:
        return f"TEM{self.n_index}{self.m_index}"


@dataclass(frozen=True)
class OpticalCavity:
    """A paraxial two-mirror cavity, as declared model numbers.

    ``fsr_hz`` is the free spectral range, ``gouy_phase_rad`` the
    round-trip Gouy phase that spaces the transverse families,
    ``waist_m`` the beam waist and ``wavelength_m`` the optical
    wavelength. No cavity exists and nothing is aligned.
    """

    fsr_hz: float = 1.5e9
    gouy_phase_rad: float = 0.35
    waist_m: float = 5.0e-4
    wavelength_m: float = 1.064e-6

    def __post_init__(self) -> None:
        if self.fsr_hz <= 0.0:
            raise ModeMixError("the free spectral range must be positive")
        if not 0.0 < self.gouy_phase_rad < math.pi:
            raise ModeMixError(
                "the round-trip Gouy phase must lie in (0, pi)")
        if self.waist_m <= 0.0 or self.wavelength_m <= 0.0:
            raise ModeMixError("the waist and wavelength must be positive")

    @property
    def transverse_spacing_hz(self) -> float:
        """``fsr * gouy/(2*pi)``: the spacing between transverse families."""
        return self.fsr_hz * self.gouy_phase_rad / (2.0 * math.pi)

    @property
    def divergence_angle_rad(self) -> float:
        """``lambda/(pi*w0)``: the far-field half-angle of the mode."""
        return self.wavelength_m / (math.pi * self.waist_m)

    def mode_frequency_hz(self, mode: CavityMode) -> float:
        """``fsr*(q + (n+m+1)*gouy/(2*pi))``, the paraxial mode frequency."""
        if not isinstance(mode, CavityMode):
            raise ModeMixError("a mode frequency needs a CavityMode")
        return self.fsr_hz * mode.longitudinal + (
            (mode.transverse_order + 1) * self.transverse_spacing_hz)

    def misalignment_overlap(self, displacement_m: float = 0.0,
                             tilt_rad: float = 0.0) -> float:
        """First-order amplitude scattered into the next transverse order.

        A lateral displacement ``d`` contributes ``d/w0`` and a tilt
        ``theta`` contributes ``theta/theta_div`` with
        ``theta_div = lambda/(pi*w0)``; the two are in quadrature, so the
        amplitude is the quadrature sum. This is the standard first-order
        mode-matching result and it is only valid while the amplitude is
        small — beyond that the expansion has left its domain and is
        refused rather than extrapolated.
        """
        d = _finite(displacement_m, "the displacement") / self.waist_m
        t = _finite(tilt_rad, "the tilt") / self.divergence_angle_rad
        amplitude = math.hypot(d, t)
        if amplitude > 1.0:
            raise ModeMixError(
                "the first-order overlap expansion has broken down: an "
                "amplitude above one means most of the power has left "
                "the two-mode subspace, and a 2x2 coupling matrix no "
                "longer describes the cavity")
        return amplitude

    def transverse_coupling_hz(self, displacement_m: float = 0.0,
                               tilt_rad: float = 0.0) -> float:
        """Misalignment coupling between neighbouring orders, in Hz.

        Taken as the overlap amplitude times the transverse family
        spacing: a declared scaling that is linear in the overlap and
        zero for a perfectly aligned cavity.
        """
        return self.transverse_spacing_hz * self.misalignment_overlap(
            displacement_m, tilt_rad)

    def astigmatic_split_hz(self, mode: CavityMode,
                            delta_gouy_rad: float) -> float:
        """Splitting of a degenerate family by a non-spherical mirror.

        A mirror whose two principal curvatures differ gives different
        Gouy phases in x and y, so ``TEM_{n,m}`` and ``TEM_{m,n}`` — which
        are degenerate on a spherical mirror — separate by
        ``fsr*(n-m)*delta_gouy/(2*pi)``. It is zero for ``n == m``, which
        is the honest statement that astigmatism cannot split a family
        with nothing to split.
        """
        if not isinstance(mode, CavityMode):
            raise ModeMixError("an astigmatic split needs a CavityMode")
        d = _finite(delta_gouy_rad, "the Gouy phase difference")
        return (self.fsr_hz * (mode.n_index - mode.m_index) * d
                / (2.0 * math.pi))


def optical_hybridisation(cavity: OpticalCavity, mode_a: CavityMode,
                          mode_b: CavityMode,
                          displacement_m: float = 0.0,
                          tilt_rad: float = 0.0) -> EigenSplit:
    """Hybridise two transverse modes under misalignment, in Hz."""
    if not isinstance(cavity, OpticalCavity):
        raise ModeMixError("an optical hybridisation needs an OpticalCavity")
    return eigen_split(cavity.mode_frequency_hz(mode_a),
                       cavity.mode_frequency_hz(mode_b),
                       cavity.transverse_coupling_hz(displacement_m,
                                                     tilt_rad))


# --- (7) adapter E: the dynamic-boundary Bogoliubov lane -----------------

def bogoliubov_pair(r: float) -> tuple[float, float]:
    """``(alpha, beta) = (cosh r, sinh r)``, identity-checked.

    Delegated to the dynamic-boundary lane so the two modules cannot
    drift apart, and validated there against
    ``|alpha|**2 - |beta|**2 == 1``.
    """
    rho = _finite(r, "the squeezing parameter")
    alpha, beta = dynboundary.squeezing_alpha_beta(rho)
    dynboundary.check_bogoliubov(alpha, beta)
    return (float(alpha), float(beta))


def bogoliubov_matrix(r: float) -> np.ndarray:
    """``[[cosh r, sinh r], [sinh r, cosh r]]``: a squeeze, not a rotation.

    It is symmetric, and it is *not* a member of the family the shared
    core implements: it acts on ``(a, a_dagger)`` and preserves the
    indefinite form ``|alpha|**2 - |beta|**2``, so it creates quanta. A
    Hermitian coupling matrix generates a rotation, which only relabels
    them. Same 2x2 shape, different invariant, different physics.
    """
    alpha, beta = bogoliubov_pair(r)
    return np.array([[alpha, beta], [beta, alpha]], dtype=float)


def rotation_matrix(theta: float) -> np.ndarray:
    """``[[cos t, -sin t], [sin t, cos t]]``, for the comparison below."""
    t = _finite(theta, "the mixing angle")
    return np.array([[math.cos(t), -math.sin(t)],
                     [math.sin(t), math.cos(t)]], dtype=float)


def rotation_versus_squeeze(angle: float = 0.4) -> dict:
    """The same number read as a rotation angle and as a rapidity.

    Both matrices are 2x2 with unit determinant, and there the similarity
    stops: the rotation preserves ``x**2 + y**2`` and creates nothing,
    while the squeeze preserves ``x**2 - y**2`` and its ``beta`` is
    exactly the pair-creation amplitude. Quoting one as the other is the
    error :func:`refuse_shared_math_as_shared_mechanism` refuses.
    """
    t = _finite(angle, "the angle")
    rot = rotation_matrix(t)
    sqz = bogoliubov_matrix(t)
    probe = np.array([1.0, 0.0])
    rot_out = rot @ probe
    sqz_out = sqz @ probe
    return {
        "angle": t,
        "rotation": rot.tolist(),
        "squeeze": sqz.tolist(),
        "rotation_determinant": float(np.linalg.det(rot)),
        "squeeze_determinant": float(np.linalg.det(sqz)),
        "rotation_sum_of_squares": float(rot_out @ rot_out),
        "squeeze_sum_of_squares": float(sqz_out @ sqz_out),
        "squeeze_indefinite_form": float(sqz_out[0] ** 2 - sqz_out[1] ** 2),
        "rotation_preserves_sum_of_squares": bool(
            abs(float(rot_out @ rot_out) - 1.0) < 1e-12),
        "squeeze_preserves_sum_of_squares": bool(
            abs(float(sqz_out @ sqz_out) - 1.0) < 1e-12),
        "squeeze_preserves_indefinite_form": bool(
            abs(float(sqz_out[0] ** 2 - sqz_out[1] ** 2) - 1.0) < 1e-12),
        "mean_photon_number": dynboundary.squeezing_photon_number(t),
        "note": ("a Hermitian coupling generates a rotation and conserves "
                 "quanta; a time-dependent boundary generates a squeeze "
                 "and creates them in pairs. The 2x2 shape is shared and "
                 "the mechanism is not"),
        "units": domain_units(Domain.DYNAMIC_BOUNDARY),
        "measured_here": "nothing",
    }


def dynamic_boundary_hybridisation(detuning: float = 0.0,
                                   coupling: float = 0.25,
                                   r: float = 0.4) -> dict:
    """Both halves of what a moving boundary does to two field modes.

    The photon-number-conserving half is an ordinary beam-splitter-like
    mixing of two modes and *is* covered by the shared core, so it is
    computed with :func:`eigen_split` in units of the boundary modulation
    rate. The pair-creating half is the Bogoliubov squeeze and is not: it
    is reported separately, with its own invariant and its own mean
    photon number.
    """
    split = eigen_split(_finite(detuning, "the detuning"), 0.0,
                        _finite(coupling, "the coupling"))
    alpha, beta = bogoliubov_pair(r)
    return {
        "hermitian_part": split.as_dict(),
        "hermitian_part_conserves_photon_number": True,
        "alpha": alpha,
        "beta": beta,
        "bogoliubov_defect": dynboundary.bogoliubov_defect(alpha, beta),
        "mean_photon_number": dynboundary.squeezing_photon_number(r),
        "squeeze_part_conserves_photon_number": False,
        "units": domain_units(Domain.DYNAMIC_BOUNDARY),
        "source": domain_source(Domain.DYNAMIC_BOUNDARY),
        "measured_here": "nothing",
    }


# --- (8) every adapter, computed with the shared core --------------------

def domain_hybridisation(domain: Domain) -> dict:
    """One canonical hybridisation per domain, all through one core.

    This is the whole demonstration: five mechanisms, five sets of units,
    five sources, one piece of matrix algebra — and no transfer between
    them. The numbers below are not comparable with each other, and
    :func:`refuse_unit_comparison` enforces that.
    """
    adapter = domain_adapter(domain)
    if domain is Domain.ATOMIC_LATTICE_PHONON:
        chain = DEFAULT_CHAIN
        q = 0.25 * chain.zone_boundary_q
        split = chain.omega_squared_split(q)
        detail = {
            "wavevector_rad_per_m": q,
            "acoustic_rad_s": chain.branches(q)[0],
            "optical_rad_s": chain.branches(q)[1],
            "zone_boundary_gap_rad_s": chain.zone_boundary_gap_rad_s(),
            "quantity_split": "omega**2 in rad**2/s**2",
        }
    elif domain is Domain.MACROSCOPIC_QUARTZ_ELASTIC:
        split = elastic_hybridisation(ElasticMode.THICKNESS_SHEAR,
                                      ElasticMode.SPURIOUS_ANHARMONIC)
        detail = {
            "modes": [ElasticMode.THICKNESS_SHEAR.value,
                      ElasticMode.SPURIOUS_ANHARMONIC.value],
            "energy_fractions": modal_energy_fractions(
                2.0 * math.pi * 13.0e6, 1.0e-9, 0.0),
            "bevelled_hz": bevel_frequency_hz(13.0e6, 0.2),
            "trapped_fraction": energy_trapping_fraction(0.005),
            "quantity_split": "frequency in Hz",
        }
    elif domain is Domain.BVD_ELECTRICAL:
        branch = BVDBranch.planted()
        split = bvd_hybridisation(branch, 13.03e6)
        detail = {
            "branch": branch.as_dict(),
            "quantity_split": "frequency in Hz",
        }
    elif domain is Domain.OPTICAL_CAVITY_TRANSVERSE:
        cavity = OpticalCavity()
        split = optical_hybridisation(cavity, CavityMode(100000, 1, 0),
                                      CavityMode(100000, 0, 1),
                                      displacement_m=2.0e-5)
        detail = {
            "overlap_amplitude": cavity.misalignment_overlap(2.0e-5),
            "transverse_spacing_hz": cavity.transverse_spacing_hz,
            "astigmatic_split_hz": cavity.astigmatic_split_hz(
                CavityMode(100000, 1, 0), 1.0e-3),
            "quantity_split": "frequency in Hz",
        }
    else:
        boundary = dynamic_boundary_hybridisation()
        split = eigen_split(0.0, 0.0, 0.25)
        detail = {
            "boundary": boundary,
            "rotation_versus_squeeze": rotation_versus_squeeze(),
            "quantity_split": "mode detuning in units of the "
                              "modulation rate",
        }
    return {
        "domain": domain.value,
        "units": adapter.units,
        "source": adapter.source,
        "source_class": adapter.source_class,
        "does_not_license": adapter.does_not_license,
        "split": split.as_dict(),
        "detail": detail,
        "computed_with": "the shared CoupledModeSystem core",
        "comparable_with_other_domains": False,
        "measured_here": "nothing",
    }


# --- (9) the load-bearing refusals ---------------------------------------

#: The canonical cross-domain attack this module exists to refuse.
CANONICAL_CROSS_DOMAIN_ATTACK = (Domain.ATOMIC_LATTICE_PHONON,
                                 Domain.MACROSCOPIC_QUARTZ_ELASTIC)


def refuse_cross_domain_transfer(src_domain: Domain,
                                 dst_domain: Domain) -> None:
    """Refuse carrying a result from one domain into another.

    Returns ``None`` for ``src is dst`` — a domain may of course speak
    about itself — and raises for every other ordered pair. Sharing a 2x2
    coupling matrix is sharing a piece of linear algebra; it is not
    sharing a mechanism, a length scale, a set of units or a source. The
    canonical case is a III-V atomic-lattice mixing result quoted at an
    alpha-quartz macroscopic plate.
    """
    src = domain_adapter(src_domain)
    dst = domain_adapter(dst_domain)
    if src.domain is dst.domain:
        return None
    extra = ""
    if (src.domain, dst.domain) == CANONICAL_CROSS_DOMAIN_ATTACK:
        extra = " " + ALPHA_QUARTZ_LATTICE_NOTE
    raise ModeMixError(
        f"a result in {src.domain.value} does not transfer to "
        f"{dst.domain.value}. The source domain works in "
        f"[{src.units}] on the authority of [{src.source}] at a length "
        f"scale of [{src.length_scale}]; the destination works in "
        f"[{dst.units}] on the authority of [{dst.source}] at a length "
        f"scale of [{dst.length_scale}]. Both hybridise through a "
        f"Hermitian coupling matrix, and that shared algebra is the only "
        f"thing they share: the couplings have different physical "
        f"origins ([{src.coupling_origin}] against "
        f"[{dst.coupling_origin}]), the eigenvalues carry different "
        f"units, and the eigenvectors live in different spaces. The "
        f"source domain states outright that {src.does_not_license}"
        f"{extra} CROSS_DOMAIN_TRANSFER_REFUSED")


def refuse_shared_math_as_shared_mechanism(
        domain_a: Domain | None = None, domain_b: Domain | None = None,
        claim: str = "the two systems share a physical mechanism") -> None:
    """Refuse identical algebra as evidence of identical physics.

    Always raises. Two systems can have the same eigenvalue algebra
    because a 2x2 Hermitian matrix has exactly one way to split; that is
    a fact about matrices. Establishing a shared mechanism needs shared
    degrees of freedom, a shared coupling with the same physical origin,
    the same units, and a prediction that transfers — not a shared
    formula.
    """
    names = ""
    if domain_a is not None or domain_b is not None:
        a = getattr(domain_a, "value", domain_a)
        b = getattr(domain_b, "value", domain_b)
        names = f" between {a} and {b}"
    raise ModeMixError(
        f"the claim {claim!r}{names} is refused. Identical eigenvalue "
        f"algebra is evidence about algebra: every 2x2 Hermitian matrix "
        f"splits by sqrt(detuning**2 + 4*k**2) and mixes at "
        f"theta = 0.5*atan2(2k, detuning), whatever the entries mean. "
        f"That the same expression describes a phonon branch pair, a "
        f"plate-mode pair, a motional and a spurious circuit branch, two "
        f"transverse cavity modes and two field modes at a moving "
        f"boundary is a statement about linear algebra, not about "
        f"physics. The dynamic-boundary lane makes the gap concrete: its "
        f"photon-number-conserving part is a rotation and its Bogoliubov "
        f"part is a squeeze, both 2x2, with different invariants and "
        f"different consequences — one relabels quanta and the other "
        f"creates them. A shared mechanism would require shared degrees "
        f"of freedom, a coupling with the same physical origin, common "
        f"units, and a prediction that survives transfer. None of that "
        f"follows from a shared formula. "
        f"SHARED_ALGEBRA_IS_NOT_SHARED_MECHANISM")


def refuse_modal_truncation_as_physical_cut(
        n_kept: int = 2, n_total: int = 27,
        claim: str = "the truncated modes were physically removed") -> None:
    """Refuse a numerical basis truncation read as a physical operation.

    Always raises. Keeping the first ``n_kept`` of ``n_total`` modes is a
    Galerkin approximation: it introduces a convergence error, it is
    checked by increasing ``n_kept`` until the answer stops moving, and
    it changes nothing about the system being modelled. Nothing in the
    lattice, the plate, the circuit, the cavity or the field is cut,
    removed, quenched or forbidden by a choice of basis size.
    """
    kept, total = int(n_kept), int(n_total)
    raise ModeMixError(
        f"the claim {claim!r} is refused. Keeping {kept} of {total} modes "
        f"is a NUMERICAL approximation — a truncated basis in a Galerkin "
        f"or modal-superposition calculation — with a convergence error "
        f"that is quantified by raising the mode count until the result "
        f"stops moving. It is not a physical cut: no phonon is destroyed, "
        f"no branch is removed from the crystal, no plate mode is "
        f"suppressed and no field mode is depopulated by a choice made in "
        f"a solver. The discarded modes still exist in the system; they "
        f"are absent from the calculation, and their absence is an error "
        f"term, not an effect. "
        f"MODAL_TRUNCATION_IS_NUMERICAL_NOT_PHYSICAL")


def refuse_unit_comparison(domain_a: Domain, domain_b: Domain,
                           value_a: float | None = None,
                           value_b: float | None = None) -> None:
    """Refuse comparing two domains' numbers by magnitude alone.

    Returns ``None`` when both domains work in the same units — a
    comparison within one unit system is arithmetic, not a category
    error — and raises otherwise. A splitting of 4000 in Hz and a
    splitting of 4000 in rad**2/s**2 are not "the same size"; they are
    not the same kind of quantity.
    """
    a = domain_adapter(domain_a)
    b = domain_adapter(domain_b)
    if a.units == b.units:
        return None
    pair = ""
    if value_a is not None or value_b is not None:
        pair = f" (given {value_a!r} against {value_b!r})"
    raise ModeMixError(
        f"comparing a {a.domain.value} quantity with a "
        f"{b.domain.value} quantity by number alone is refused{pair}. "
        f"The first is expressed in [{a.units}] and the second in "
        f"[{b.units}]; these are different kinds of quantity, so their "
        f"magnitudes are not commensurable and no ratio, difference, "
        f"ranking or agreement between them means anything. Converting "
        f"would require a declared physical relation between the two "
        f"domains, and no such relation is established here. "
        f"UNIT_COMPARISON_REFUSED")


# --- (10) the report ------------------------------------------------------

def modemix_report() -> dict:
    """The standing statement of what this module is and is not."""
    crossing = avoided_crossing()
    return {
        "claim_class": CLAIM_CLASS,
        "what_this_is": (
            "one reusable coupled-mode mathematics layer — a Hermitian "
            "coupling matrix, its eigen-split, its mixing angle and its "
            "participation fractions — with five physically typed "
            "adapters that share it and nothing else"),
        "the_shared_core": {
            "matrix": "[[w1, k], [k, w2]], Hermitian, NxN supported",
            "eigenvalues": "mean -/+ 0.5*sqrt((w1-w2)**2 + 4*k**2)",
            "mixing_angle": "theta = 0.5*atan2(2k, w1-w2)",
            "minimum_splitting": "2*|k|, at zero detuning",
            "participation": "|V|**2; rows and columns each sum to one",
        },
        "the_avoided_crossing": {
            "coupling": crossing["coupling"],
            "minimum_splitting": crossing["minimum_splitting"],
            "expected_minimum_splitting":
                crossing["expected_minimum_splitting"],
            "minimum_matches_twice_the_coupling":
                crossing["minimum_matches_twice_the_coupling"],
            "detuning_at_minimum": crossing["detuning_at_minimum"],
            "mixing_angle_at_zero_detuning_deg":
                crossing["mixing_angle_at_zero_detuning_deg"],
            "branches_never_cross": crossing["branches_never_cross"],
        },
        "domains": {d.value: domain_adapter(d).as_dict() for d in Domain},
        "hybridisations": {d.value: domain_hybridisation(d)
                           for d in Domain},
        "units_are_distinct": len({domain_units(d) for d in Domain}) == 5,
        "sources_are_distinct": len({domain_source(d) for d in Domain}) == 5,
        "alpha_quartz_note": ALPHA_QUARTZ_LATTICE_NOTE,
        "firewalls": [
            "a result in one domain does not transfer to another, however "
            "similar the algebra — refuse_cross_domain_transfer",
            "identical eigenvalue algebra is not evidence of a shared "
            "physical mechanism — refuse_shared_math_as_shared_mechanism",
            "truncating a modal basis is a numerical approximation with a "
            "convergence error, not a physical cut of a phonon — "
            "refuse_modal_truncation_as_physical_cut",
            "quantities from domains with different units are not "
            "comparable by magnitude — refuse_unit_comparison",
        ],
        "canonical_attacks_refused": [
            "confusing III-V atomic-lattice mode mixing with alpha-quartz "
            "macroscopic mode mixing: different lattice, different cell, "
            "different branch count, different units, six orders of "
            "magnitude apart in frequency",
            "reading a truncated modal basis as a physically cut phonon",
        ],
        "verdicts": list(VERDICTS),
        "claim_classes": list(CLAIM_CLASSES),
        "evidence_class": EVIDENCE_CLASS,
        "hardware_status": (
            "DEFERRED — no lattice, plate, resonator, cavity or boundary "
            "has been built, driven or read out"),
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "what_this_does_not_say": (
            "It does not say any crystal, plate, circuit, cavity or "
            "boundary exists, or that any frequency, splitting, coupling, "
            "quality factor, energy fraction or photon number was "
            "measured. Every model parameter is a declared number in "
            "declared units, and the representative masses, lattice "
            "constant, plate frequencies, circuit elements and cavity "
            "parameters are chosen inputs, not observations. It does not "
            "say the five adapters describe one physical effect: they "
            "share a Hermitian 2x2 and nothing else, and a number from "
            "one of them is neither a prediction for, nor evidence "
            "about, any of the others. It does not say that a III-V "
            "lattice result applies to alpha quartz, that a plate mode "
            "is a phonon, that BVD elements are a mass and a stiffness, "
            "that an optical overlap integral is a force constant, or "
            "that a Bogoliubov squeeze is a rotation. It does not say "
            "that truncating a modal basis removes anything from any "
            "physical system."),
        "verdict": DEFAULT_VERDICT,
    }
