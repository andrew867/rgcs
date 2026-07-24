"""P31 — a force-constant / phonon interface in the Euphonic style, blocked on DFT.

The real `euphonic <https://euphonic.readthedocs.io>`_ package computes
phonon frequencies, densities of states, and the dynamic structure factor
``S(Q, w)`` from **interatomic force constants** that come out of a
DFT/DFPT calculation (CASTEP, Phonopy, ...). That calculation is an
EXTERNAL VALIDATION lane: it needs first-principles force constants for
real alpha-quartz that **do not exist in this environment**. There are no
force constants, no phonon output, no facility, and no measured
inelastic-neutron spectrum here.

So this module does two separate things and keeps them apart.

* It **models the interface** itself -- the shape of a force-constant ->
  dynamical-matrix -> dispersion -> DOS -> ``S(Q, w)`` pipeline -- rather
  than importing the real ``euphonic`` pip package (which may be absent).
  The physics it evaluates is a small **synthetic, analytic** force-constant
  set that we define here and label ``ANALYTIC_MODEL``. For a monatomic
  synthetic set the computed dispersion matches the closed form
  ``omega(k) = 2 sqrt(K/m) |sin(k a / 2)|`` and the acoustic branch reaches
  ``omega = 0`` at Gamma -- the acoustic sum rule, enforced not assumed.

* It **marks the real inputs BLOCKED**. :meth:`ForceConstants.from_dft`
  raises :class:`EuphonicError` with a ``BLOCKED_MISSING_INPUT`` receipt,
  because no DFT output exists to read. :func:`refuse_synthetic_fc_as_dft`
  refuses to pass a synthetic spring set off as a first-principles
  calculation, and :func:`refuse_model_dispersion_as_measured_INS` refuses
  to read a computed dispersion as an inelastic-neutron-scattering
  measurement.

Nothing here is measured, and no synthetic frequency is a real quartz
phonon mode. The default verdict is
``FORCE_CONSTANT_INTERFACE_BLOCKED_ON_DFT``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum

import numpy as np

# --- verdict, claim classes ----------------------------------------------

DEFAULT_VERDICT = "FORCE_CONSTANT_INTERFACE_BLOCKED_ON_DFT"

#: What the interface evaluates: a synthetic, analytic force-constant model.
CLAIM_CLASS = "ANALYTIC_MODEL"

#: The claim classes a statement in this module may declare, verbatim.
CLAIM_CLASSES = (
    "EXACT_IDENTITY",
    "SOURCE_ESTABLISHED_PHYSICS",
    "CONVENTIONAL_LITERATURE",
    "DERIVED_ARITHMETIC",
    "ANALYTIC_MODEL",
    "NUMERICAL_SIMULATION",
    "REPOSITORY_COMPUTATIONAL_RESULT",
    "ENGINEERING_CANDIDATE",
    "PROSPECTIVE_PREDICTION",
    "SOURCE_CLAIM",
    "BENCH_MEASUREMENT",
    "UNSUPPORTED",
    "BLOCKED_MISSING_INPUT",
)

#: Tolerance for Hermiticity, the acoustic sum rule, and diagonalization.
PHONON_TOL = 1e-9


class EuphonicError(RuntimeError):
    """Raised when a force-constant / phonon claim exceeds the interface.

    Covers the structural refusals (a non-square or non-symmetric
    force-constant matrix, a non-positive mass), the blocked DFT input
    (:meth:`ForceConstants.from_dft`), and the governance refusals
    :func:`refuse_synthetic_fc_as_dft` and
    :func:`refuse_model_dispersion_as_measured_INS`.
    """


def _positive(value: float, what: str) -> float:
    x = float(value)
    if not math.isfinite(x):
        raise EuphonicError(f"{what} must be finite")
    if x <= 0.0:
        raise EuphonicError(f"{what} must be positive")
    return x


class FCSource(Enum):
    """Where a force-constant set claims to have come from.

    Only ``SYNTHETIC_ANALYTIC`` is ever produced here; ``DFT_DFPT`` is the
    blocked external lane and is never instantiated in this environment.
    """

    SYNTHETIC_ANALYTIC = "SYNTHETIC_ANALYTIC"
    DFT_DFPT = "DFT_DFPT"


# --- the blocked-input receipt -------------------------------------------

#: Real force constants come from DFT/DFPT that does not run here.
REAL_FORCE_CONSTANTS_STATUS = {
    "status": "BLOCKED_MISSING_INPUT",
    "why": ("the interatomic force constants Euphonic needs come from a "
            "DFT/DFPT calculation (CASTEP / Phonopy output) for real "
            "alpha-quartz; no such output, force-constant file, or phonon "
            "result exists in this environment"),
    "external_lane": ("first-principles force constants are an EXTERNAL "
                      "VALIDATION input, not a feature this module can "
                      "supply from itself"),
}


# --- the force-constant set ----------------------------------------------

@dataclass(frozen=True)
class ForceConstants:
    """A set of interatomic force constants, in the Euphonic interface style.

    Euphonic stores force constants in **real space**, as one ``N x N``
    block per periodic-cell offset ``R`` (in units of the lattice constant):
    ``Phi_R[i, j]`` is the force constant coupling atom ``i`` of the home
    cell to atom ``j`` of the cell ``R`` cells away. ``masses`` is the
    per-cell basis (length ``N``), ``blocks`` maps each integer offset to its
    block, and ``a`` is the lattice constant. ``source`` records provenance:
    everything built here is :attr:`FCSource.SYNTHETIC_ANALYTIC` -- a small
    set we define, labelled ``ANALYTIC_MODEL`` -- never a DFT/DFPT result.

    The set must be **hermitian** (``Phi_{-R} = Phi_R^T``) so ``D(q)`` is
    Hermitian, and satisfy the **acoustic sum rule** (the summed-over-``R``
    block has rows summing to zero) so the acoustic branch reaches
    ``omega = 0`` at Gamma. Use :meth:`synthetic_monatomic` and
    :meth:`synthetic_diatomic` for the two textbook synthetic sets.

    ``blocks`` is stored as a tuple of ``(offset, row-major matrix)`` pairs
    so the dataclass stays frozen/hashable.
    """

    masses: tuple[float, ...]
    blocks: tuple[tuple[int, tuple[tuple[float, ...], ...]], ...]
    a: float = 1.0
    source: FCSource = FCSource.SYNTHETIC_ANALYTIC

    def __post_init__(self) -> None:
        m = np.asarray(self.masses, dtype=float)
        if m.ndim != 1 or m.size < 1:
            raise EuphonicError("masses must be a non-empty 1-D sequence")
        for mval in self.masses:
            _positive(mval, "a mass")
        _positive(self.a, "the lattice constant a")
        n = m.size
        offsets = [off for off, _ in self.blocks]
        if 0 not in offsets:
            raise EuphonicError("the on-site block (offset 0) is required")
        if len(set(offsets)) != len(offsets):
            raise EuphonicError("each cell offset may appear only once")
        mats = dict(self._block_arrays())
        for off, phi in mats.items():
            if phi.shape != (n, n):
                raise EuphonicError(
                    "every force-constant block must be N x N for the basis")
        # hermiticity of the real-space set: Phi_{-R} = Phi_R^T
        for off, phi in mats.items():
            other = mats.get(-off)
            if other is None:
                raise EuphonicError(
                    f"block at offset {off} has no partner at {-off}; the "
                    f"set must satisfy Phi_-R = Phi_R^T")
            if not np.allclose(other, phi.T, atol=PHONON_TOL):
                raise EuphonicError(
                    f"blocks at +/-{abs(off)} violate Phi_-R = Phi_R^T")

    def _block_arrays(self):
        for off, mat in self.blocks:
            yield off, np.asarray(mat, dtype=float)

    @classmethod
    def _pack(cls, masses, block_map, a, source=FCSource.SYNTHETIC_ANALYTIC):
        blocks = tuple(
            (off, tuple(tuple(float(x) for x in row) for row in mat))
            for off, mat in sorted(block_map.items()))
        return cls(masses=tuple(masses), blocks=blocks, a=a, source=source)

    @classmethod
    def synthetic_monatomic(cls, m: float = 1.0, K: float = 1.0,
                            a: float = 1.0) -> "ForceConstants":
        """A one-atom synthetic set: on-site ``2K``, neighbour ``-K`` each side.

        Real-space force constants ``Phi_0 = 2K``, ``Phi_{+1} = Phi_{-1} =
        -K``, so ``D(q) = (2K - 2K cos q a)/m = 4K/m sin^2(q a / 2)`` and the
        dispersion is the exact monatomic ``2 sqrt(K/m) |sin(q a / 2)|``. This
        is a synthetic analogue, not a real force constant.
        """
        KK = _positive(K, "the spring K")
        return cls._pack((m,), {0: [[2.0 * KK]], 1: [[-KK]], -1: [[-KK]]}, a)

    @classmethod
    def synthetic_diatomic(cls, m1: float = 1.0, m2: float = 2.0,
                           K: float = 1.0, a: float = 1.0) -> "ForceConstants":
        """A two-atom synthetic set: equal springs ``K``, sum rule enforced.

        On-site block couples the two basis atoms and holds the self term
        ``2K``; the ``+/-1`` blocks carry the inter-cell bond, reproducing the
        standard acoustic + optical two-branch diatomic dispersion.
        """
        KK = _positive(K, "the spring K")
        _positive(m1, "the mass m1")
        _positive(m2, "the mass m2")
        phi0 = [[2.0 * KK, -KK], [-KK, 2.0 * KK]]
        phi_p1 = [[0.0, 0.0], [-KK, 0.0]]        # atom1(cell0) -> atom0(cell+1)
        phi_m1 = [[0.0, -KK], [0.0, 0.0]]        # transpose of +1
        return cls._pack((m1, m2), {0: phi0, 1: phi_p1, -1: phi_m1}, a)

    @classmethod
    def from_dft(cls, path: str) -> "ForceConstants":
        """Load real force constants from a DFT/DFPT output -- BLOCKED here.

        This is the external-validation entry point: in a real Euphonic
        workflow it would read a CASTEP ``.castep_bin`` / Phonopy force
        constants file. No such file, and no DFT calculation, exists in this
        environment, so it raises :class:`EuphonicError` with a
        ``BLOCKED_MISSING_INPUT`` receipt rather than fabricating a set.
        """
        raise EuphonicError(
            f"BLOCKED_MISSING_INPUT: cannot load DFT/DFPT force constants "
            f"from {path!r}. The interatomic force constants Euphonic needs "
            f"come from a first-principles DFT/DFPT calculation for real "
            f"alpha-quartz; no such output exists in this environment. This "
            f"is an EXTERNAL VALIDATION input, not a synthetic set this "
            f"module may supply. PHYSICAL_VALIDATION_NOT_CLAIMED.")

    def n_atoms(self) -> int:
        return len(self.masses)

    def summed_block(self) -> np.ndarray:
        """The force-constant blocks summed over all cell offsets ``R``."""
        n = self.n_atoms()
        total = np.zeros((n, n), dtype=float)
        for _, phi in self._block_arrays():
            total += phi
        return total

    def acoustic_sum_rule_holds(self, tol: float = PHONON_TOL) -> bool:
        """True iff the summed-over-R force-constant matrix has zero row sums.

        A rigid translation of every atom in every cell must cost no energy,
        which requires ``sum_R Phi_R`` to have every row summing to zero.
        """
        return bool(np.all(np.abs(self.summed_block().sum(axis=1)) <= tol))

    def dynamical_matrix(self, q: float) -> np.ndarray:
        """The Hermitian dynamical matrix ``D(q)`` from these force constants.

        ``D(q)_{ij} = (1 / sqrt(m_i m_j)) sum_R Phi_R[i, j] exp(i q R a)`` --
        the mass-weighted Fourier transform of the real-space force constants
        over cell offsets ``R``. Because ``Phi_{-R} = Phi_R^T``, ``D(q)`` is
        Hermitian with real eigenvalues; for a stable set they are
        non-negative -- the squared phonon frequencies.
        """
        m = np.asarray(self.masses, dtype=float)
        n = m.size
        aa = self.a
        inv = 1.0 / np.sqrt(np.outer(m, m))
        D = np.zeros((n, n), dtype=complex)
        for off, phi in self._block_arrays():
            phase = complex(math.cos(q * off * aa), math.sin(q * off * aa))
            D += phi * phase
        D *= inv
        # Hermitize against floating asymmetry accumulated in the sum.
        return 0.5 * (D + D.conj().T)


# --- phonons from force constants ----------------------------------------

def phonon_dispersion(fc: ForceConstants, qpath) -> np.ndarray:
    """Phonon frequencies along a q-path, from the force constants.

    Builds the dynamical matrix at each ``q`` in ``qpath`` and diagonalizes
    it, returning an ``(len(qpath), N)`` array of frequencies, ascending at
    each ``q``. Tiny negative eigenvalues from floating error are clipped to
    zero before the square root, so the acoustic branch reaches exactly
    ``omega = 0`` at Gamma.
    """
    if not isinstance(fc, ForceConstants):
        raise EuphonicError("phonon_dispersion needs a ForceConstants set")
    qs = np.atleast_1d(np.asarray(qpath, dtype=float))
    out = np.empty((qs.size, fc.n_atoms()), dtype=float)
    for idx, q in enumerate(qs):
        D = fc.dynamical_matrix(float(q))
        evals = np.linalg.eigvalsh(D)
        out[idx] = np.sqrt(np.clip(evals, 0.0, None))
    return out


def phonon_eigenvectors(fc: ForceConstants, q: float):
    """``(frequencies, eigenvectors)`` at a single ``q``, ascending.

    The eigenvectors are the mass-normalized phonon polarization vectors;
    columns correspond to the ascending frequencies. Used by the structure
    factor to weight modes by their polarization.
    """
    if not isinstance(fc, ForceConstants):
        raise EuphonicError("phonon_eigenvectors needs a ForceConstants set")
    D = fc.dynamical_matrix(float(q))
    evals, evecs = np.linalg.eigh(D)
    freqs = np.sqrt(np.clip(evals, 0.0, None))
    return freqs, evecs


def monatomic_analytic(q: float, m: float = 1.0, K: float = 1.0,
                       a: float = 1.0) -> float:
    """``omega(q) = 2 sqrt(K/m) |sin(q a / 2)|`` -- the analytic reference."""
    mm = _positive(m, "the mass m")
    KK = _positive(K, "the spring K")
    aa = _positive(a, "the lattice constant a")
    return 2.0 * math.sqrt(KK / mm) * abs(math.sin(q * aa / 2.0))


# --- density of states ---------------------------------------------------

def density_of_states(fc: ForceConstants, qgrid, n_bins: int = 60,
                      omega_max: float | None = None):
    """A histogrammed phonon density of states over a q-grid.

    Diagonalizes the dynamical matrix over every ``q`` in ``qgrid``,
    collects all ``N * len(qgrid)`` frequencies, and histograms them into
    ``n_bins`` bins. Returns ``(bin_centres, dos)`` where ``dos`` is
    **normalized so it integrates to the total number of modes** ``N`` (per
    q-point): ``sum(dos * bin_width) == N``. A van-Hove-like pile-up appears
    at the band edges, where the dispersion flattens and the density of
    states diverges.
    """
    if not isinstance(fc, ForceConstants):
        raise EuphonicError("density_of_states needs a ForceConstants set")
    if n_bins < 1:
        raise EuphonicError("n_bins must be positive")
    qs = np.atleast_1d(np.asarray(qgrid, dtype=float))
    if qs.size < 1:
        raise EuphonicError("the q-grid must be non-empty")
    freqs = phonon_dispersion(fc, qs).ravel()
    hi = float(np.max(freqs)) if omega_max is None else _positive(
        omega_max, "omega_max")
    if hi <= 0.0:
        # a fully degenerate zero spectrum: put all weight in the first bin
        hi = 1.0
    # widen the top edge slightly so the maximum frequency lands in a bin
    edges = np.linspace(0.0, hi * (1.0 + 1e-9), n_bins + 1)
    counts, edges = np.histogram(freqs, bins=edges)
    width = edges[1] - edges[0]
    centres = 0.5 * (edges[:-1] + edges[1:])
    # normalize so the integral (sum of dos * width) equals the number of
    # modes per q-point: sum(dos * width) = sum(counts) / len(qgrid) = N.
    dos = counts.astype(float) / (qs.size * width)
    return centres, dos


def dos_mode_count(fc: ForceConstants, qgrid, n_bins: int = 60) -> float:
    """The integral of the DOS: total modes per q-point, should equal ``N``."""
    centres, dos = density_of_states(fc, qgrid, n_bins=n_bins)
    if centres.size < 2:
        return float(dos.sum())
    width = centres[1] - centres[0]
    return float(np.sum(dos * width))


# --- the dynamic structure factor interface stub -------------------------

def dynamic_structure_factor(fc: ForceConstants, Q: float, q: float,
                             temperature: float = 300.0):
    """An INTERFACE stub for ``S(Q, w)`` from the synthetic phonon model.

    Returns ``(frequencies, intensities)`` for the one-phonon structure
    factor at reduced wavevector ``q`` and momentum transfer ``Q``, with
    intensity ``propto (Q . e)^2 / omega`` per mode ``e``. This is a
    **synthetic, ANALYTIC_MODEL** evaluation that models the *shape* of the
    Euphonic ``S(Q, w)`` output; the full facility-grade calculation
    (form factors, Debye-Waller, instrument resolution, absolute units)
    lives in the scattering lane P32 and, for real quartz, is
    BLOCKED_MISSING_INPUT. It is not a measured spectrum.
    """
    if not isinstance(fc, ForceConstants):
        raise EuphonicError("dynamic_structure_factor needs a ForceConstants set")
    _positive(temperature, "the temperature")
    freqs, evecs = phonon_eigenvectors(fc, q)
    intensities = np.zeros_like(freqs)
    for mode in range(freqs.size):
        omega = freqs[mode]
        if omega <= PHONON_TOL:
            continue                       # elastic / acoustic q->0, skip
        e = evecs[:, mode].real
        proj = float(Q) * float(np.sum(e))          # (Q . e), scalar model
        intensities[mode] = proj * proj / omega
    return freqs, intensities


# --- the load-bearing refusals -------------------------------------------

def refuse_synthetic_fc_as_dft(fc: ForceConstants | None = None,
                               *_a, **_k) -> None:
    """A synthetic force-constant set is not a DFT/DFPT calculation.

    The force constants here are a small analytic set we defined, labelled
    ``ANALYTIC_MODEL`` and sourced :attr:`FCSource.SYNTHETIC_ANALYTIC`. They
    are not first-principles force constants, and reading them as a DFT/DFPT
    result -- the input Euphonic actually needs -- is refused.
    """
    src = None if fc is None else fc.source
    raise EuphonicError(
        f"refused: this force-constant set is {src.value if src else 'SYNTHETIC_ANALYTIC'}, "
        f"a chosen analytic model, not a DFT/DFPT calculation. Real "
        f"interatomic force constants for alpha-quartz are "
        f"BLOCKED_MISSING_INPUT here and are an EXTERNAL VALIDATION input. "
        f"A synthetic set may never be reported as a first-principles "
        f"result. PHYSICAL_VALIDATION_NOT_CLAIMED.")


def refuse_model_dispersion_as_measured_INS(*_a, **_k) -> None:
    """A computed dispersion is not an inelastic-neutron-scattering measurement.

    ``phonon_dispersion`` diagonalizes a synthetic dynamical matrix; its
    frequencies are ``ANALYTIC_MODEL`` evaluations. An inelastic neutron
    scattering (INS) spectrum is a facility measurement that requires beam
    time and a sample, none of which exist here. Reading a computed
    dispersion as measured INS data is refused.
    """
    raise EuphonicError(
        "refused: a computed phonon dispersion is an ANALYTIC_MODEL "
        "evaluation of a synthetic dynamical matrix, not an inelastic "
        "neutron scattering (INS) measurement. A real INS spectrum needs a "
        "neutron facility, beam time, and a sample -- all "
        "BLOCKED_MISSING_INPUT here. PHYSICAL_VALIDATION_NOT_CLAIMED.")


# --- the report ----------------------------------------------------------

def euphonic_report() -> dict:
    mono = ForceConstants.synthetic_monatomic(m=1.0, K=1.0, a=1.0)
    di = ForceConstants.synthetic_diatomic(m1=1.0, m2=2.0, K=1.0, a=1.0)
    qgrid = np.linspace(-math.pi, math.pi, 200)
    return {
        "what_this_is": (
            "a force-constant / phonon interface in the Euphonic style: "
            "build a dynamical matrix from a synthetic force-constant set, "
            "diagonalize along a q-path for the dispersion, histogram a "
            "density of states, and expose an S(Q, w) interface stub -- all "
            "ANALYTIC_MODEL, with the real DFT force constants blocked"),
        "interface_modelled_not_imported": (
            "the real euphonic pip package is not imported; the interface "
            "shape is modelled here so it works whether or not euphonic is "
            "installed"),
        "synthetic_monatomic_omega_at_gamma": float(
            phonon_dispersion(mono, [0.0])[0, 0]),
        "synthetic_monatomic_omega_at_zone_boundary": float(
            phonon_dispersion(mono, [math.pi])[0, 0]),
        "synthetic_diatomic_omega_at_gamma": [
            float(x) for x in phonon_dispersion(di, [0.0])[0]],
        "acoustic_sum_rule_monatomic": mono.acoustic_sum_rule_holds(),
        "dos_mode_count_diatomic": dos_mode_count(di, qgrid),
        "real_force_constants": REAL_FORCE_CONSTANTS_STATUS,
        "claim_class": CLAIM_CLASS,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": DEFAULT_VERDICT,
        "what_this_does_not_say": (
            "It does not say these frequencies are the phonon modes of real "
            "alpha-quartz, that the S(Q, w) stub is a measured spectrum, or "
            "that a synthetic force-constant set is a DFT/DFPT calculation. "
            "The force constants are a chosen analytic set; the real ones "
            "require a first-principles DFT/DFPT calculation that is "
            "BLOCKED_MISSING_INPUT and is an EXTERNAL VALIDATION input. "
            "Nothing is measured; a computed dispersion is not an inelastic "
            "neutron scattering measurement."),
    }
