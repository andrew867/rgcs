"""R11 P09 — a mechanical boundary that changes in time, classically.

This is the **classical** counterpart to the quantum lane in
``r11/dynboundary.py``, and the two are deliberately different objects.
The quantum lane asks what a time-dependent boundary does to a *field*:
the answer there is a Bogoliubov transformation, pair creation from
vacuum, and photon-number sectors that stay integers. Nothing in this
module is about photons, vacuum, or quanta of any kind.

**What a classical time-dependent mechanical boundary is.** Take a
discretised one-dimensional resonator — a mass-spring-damper chain with
``N`` nodes — and change the condition at its ends *while it is
ringing*: stiffen the end spring, load the support, add or remove
damping, deposit an electrode. The mass, stiffness and damping matrices
``(M, K, C)`` are different before and after, so the **modal basis
itself moves**. A displacement that was one clean mode of the old system
is a *combination* of modes of the new one, and the mixing is real
physics, not bookkeeping:

* a **SUDDEN** change leaves the displacement and the momentum
  continuous but the basis discontinuous, so the stored energy is
  **scattered** across several new modes;
* a **GRADUAL** change over a ramp time ``tau`` long compared with the
  beat periods ``1/(omega_i - omega_j)`` is **adiabatic**: the action of
  each mode is preserved, mode ``k`` stays mode ``k``, and the mixing
  matrix tends to the identity.

That monotone trend — mixing falls as ``tau`` grows, participation of
the target mode rises toward one — is the headline result of the
module, and it is produced by integrating the equations of motion, not
asserted.

**The energy books must close.** Changing a stiffness, a support
impedance or an electrode loading while the structure moves does *real
work* on it. With ``H = 0.5*p^T M(t)^-1 p + 0.5*u^T K(t) u`` and the
non-conservative force ``-C(t) v``,

    dH/dt = [0.5*u^T Kdot u - 0.5*v^T Mdot v] - v^T C v
          =            boundary power           - dissipated power

so ``E_after == E_before + W_boundary - E_dissipated`` exactly, and
:func:`energy_ledger` checks it numerically for both profiles. Omitting
``W_boundary`` breaks the identity by construction, which is how the
ledger is shown to have teeth. Any apparent energy *gain* across a
boundary change is work done by whatever moved the boundary — a
tensioner, an actuator, a bias supply — and
:func:`refuse_energy_from_nothing` refuses the alternative.

**What this is not.** It is a classical, deterministic, finite-degree-
of-freedom simulation. It establishes nothing about photon creation,
vacuum fluctuations, the dynamical Casimir effect, or any quantum
boundary effect; :func:`refuse_quantum_claim` raises rather than let a
classical mode-mixing number be quoted as a quantum one. Nothing here
is measured: no chain exists, no boundary has been switched, and every
number is arithmetic on a declared model.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from enum import Enum

import numpy as np

# --- verdicts and tolerances --------------------------------------------

DEFAULT_VERDICT = "CLASSICAL_DYNAMIC_BOUNDARY_MODEL_IMPLEMENTED"

VERDICTS = (
    DEFAULT_VERDICT,
    "SUDDEN_CHANGE_SCATTERS_MODAL_ENERGY",
    "ADIABATIC_LIMIT_PRESERVES_MODAL_IDENTITY",
    "BOUNDARY_WORK_REQUIRED",
    "BASIS_UNMOVED_NO_MODAL_SCATTERING",
    "CLASSICAL_MODEL_ESTABLISHES_NOTHING_QUANTUM",
    "PHYSICAL_VALIDATION_NOT_CLAIMED",
)

#: Relative tolerance used by :func:`energy_ledger`.
LEDGER_TOL = 1e-6

#: Tolerance on mass-normalisation (``Phi^T M Phi == I``).
ORTHONORMALITY_TOL = 1e-9

#: Default RK4 steps per period of the fastest mode present.
STEPS_PER_PERIOD = 40

#: Minimum number of RK4 steps taken across any ramp, however short.
MIN_RAMP_STEPS = 16


class MechBoundaryError(RuntimeError):
    """Raised when a mechanical-boundary claim exceeds what the model licenses.

    Covers the structural refusals (a non-positive-definite mass matrix,
    a gradual profile with no ramp time), the energy refusal
    (:func:`refuse_energy_from_nothing`) and the lane refusal
    (:func:`refuse_quantum_claim`).
    """


# --- (1) what can change at the boundary ---------------------------------

class BoundaryParameter(Enum):
    """The four independently typed boundary changes.

    They are not interchangeable and they do not touch the same matrix:

    * ``STIFFNESS`` — the grounded spring at the driven end; changes ``K``.
    * ``DAMPING`` — the dashpot at that end; changes ``C`` only, so the
      *undamped* modal basis does not move at all.
    * ``SUPPORT_IMPEDANCE`` — the support at the other end, whose
      stiffness and damping scale together; changes ``K`` and ``C``.
    * ``ELECTRODE_LOADING`` — a deposited electrode at an interior node:
      added mass, electrostatic spring softening (a *negative* grounded
      stiffness) and electrical damping; changes ``M``, ``K`` and ``C``.
    """

    STIFFNESS = "STIFFNESS"
    DAMPING = "DAMPING"
    SUPPORT_IMPEDANCE = "SUPPORT_IMPEDANCE"
    ELECTRODE_LOADING = "ELECTRODE_LOADING"


class ChangeProfile(Enum):
    """How the change is made in time."""

    SUDDEN = "SUDDEN"      # discontinuous; tau == 0
    GRADUAL = "GRADUAL"    # smooth ramp over tau > 0


#: Which :class:`ChainConfig` fields each parameter scales.
PARAMETER_FIELDS: dict[BoundaryParameter, tuple[str, ...]] = {
    BoundaryParameter.STIFFNESS: ("boundary_stiffness",),
    BoundaryParameter.DAMPING: ("boundary_damping",),
    BoundaryParameter.SUPPORT_IMPEDANCE: ("support_stiffness",
                                          "support_damping"),
    BoundaryParameter.ELECTRODE_LOADING: ("electrode_mass",
                                          "electrode_stiffness",
                                          "electrode_damping"),
}


# --- (2) the discretised resonator ---------------------------------------

@dataclass(frozen=True)
class ChainConfig:
    """A 1-D mass-spring-damper chain, grounded at both ends.

    Node ``0`` is held by the *support* (stiffness ``support_stiffness``,
    dashpot ``support_damping``); node ``n_nodes - 1`` is held by the
    *boundary* (``boundary_stiffness``, ``boundary_damping``); adjacent
    nodes are coupled by ``internal_stiffness`` and ``internal_damping``.
    An electrode may sit on one interior node, adding ``electrode_mass``,
    a grounded ``electrode_stiffness`` (negative for electrostatic
    softening) and ``electrode_damping``.

    Every field is a model parameter in arbitrary consistent units. None
    of them is a measurement of anything.
    """

    n_nodes: int = 6
    node_mass: float = 1.0
    internal_stiffness: float = 1.0
    internal_damping: float = 0.0
    support_stiffness: float = 0.6
    support_damping: float = 0.0
    boundary_stiffness: float = 0.8
    boundary_damping: float = 0.0
    electrode_node: int | None = None
    electrode_mass: float = 0.15
    electrode_stiffness: float = -0.12
    electrode_damping: float = 0.0

    def __post_init__(self) -> None:
        if self.n_nodes < 2:
            raise MechBoundaryError("a chain needs at least two nodes")
        if self.node_mass <= 0.0:
            raise MechBoundaryError("node mass must be positive")
        if self.internal_stiffness <= 0.0:
            raise MechBoundaryError("internal stiffness must be positive")
        if min(self.support_stiffness, self.boundary_stiffness) < 0.0:
            raise MechBoundaryError("end stiffnesses cannot be negative")
        if min(self.internal_damping, self.support_damping,
               self.boundary_damping, self.electrode_damping) < 0.0:
            raise MechBoundaryError("damping cannot be negative")
        if self.node_mass + self.electrode_mass <= 0.0:
            raise MechBoundaryError("electrode loading cannot cancel a mass")
        node = self.electrode_index
        if not 0 <= node < self.n_nodes:
            raise MechBoundaryError("electrode node is outside the chain")

    @property
    def electrode_index(self) -> int:
        """The interior node the electrode sits on (default: the middle)."""
        return (self.n_nodes // 2 if self.electrode_node is None
                else int(self.electrode_node))

    def conservative(self) -> "ChainConfig":
        """The same chain with every dashpot removed.

        Mode mixing is a property of ``M`` and ``K``; running the
        adiabatic study on a conservative chain keeps the modal-energy
        bookkeeping free of a decay that has nothing to do with the
        basis moving.
        """
        return replace(self, internal_damping=0.0, support_damping=0.0,
                       boundary_damping=0.0, electrode_damping=0.0)

    def dissipative(self, scale: float = 1.0) -> "ChainConfig":
        """The same chain with representative dashpots switched on."""
        if scale < 0.0:
            raise MechBoundaryError("damping scale cannot be negative")
        return replace(self, internal_damping=0.01 * scale,
                       support_damping=0.03 * scale,
                       boundary_damping=0.05 * scale,
                       electrode_damping=0.02 * scale)


#: The chain used for the mixing and adiabaticity study: conservative, so
#: every energy change is boundary work rather than decay.
DEFAULT_CHAIN = ChainConfig().conservative()

#: The chain used for the dissipation and ledger-with-damping study.
DISSIPATIVE_CHAIN = ChainConfig().dissipative()


@dataclass(frozen=True)
class MechSystem:
    """The assembled ``(M, K, C)`` of one configuration."""

    M: np.ndarray
    K: np.ndarray
    C: np.ndarray

    @property
    def n(self) -> int:
        return int(self.M.shape[0])

    @property
    def is_damped(self) -> bool:
        return bool(np.any(self.C != 0.0))


def build_system(config: ChainConfig) -> MechSystem:
    """Assemble ``(M, K, C)`` for a chain configuration.

    ``M`` is diagonal, ``K`` and ``C`` are symmetric tridiagonal plus
    grounded terms. ``K`` is positive definite whenever the grounded
    springs do not overwhelm the chain; a configuration that breaks that
    is refused rather than silently producing imaginary frequencies.
    """
    n = config.n_nodes
    m = np.full(n, float(config.node_mass))
    k = np.zeros((n, n))
    c = np.zeros((n, n))

    ki, ci = float(config.internal_stiffness), float(config.internal_damping)
    for i in range(n - 1):
        for mat, val in ((k, ki), (c, ci)):
            mat[i, i] += val
            mat[i + 1, i + 1] += val
            mat[i, i + 1] -= val
            mat[i + 1, i] -= val

    k[0, 0] += float(config.support_stiffness)
    c[0, 0] += float(config.support_damping)
    k[n - 1, n - 1] += float(config.boundary_stiffness)
    c[n - 1, n - 1] += float(config.boundary_damping)

    e = config.electrode_index
    m[e] += float(config.electrode_mass)
    k[e, e] += float(config.electrode_stiffness)
    c[e, e] += float(config.electrode_damping)

    mass = np.diag(m)
    if np.any(m <= 0.0):
        raise MechBoundaryError("every nodal mass must stay positive")
    eigenvalues = np.linalg.eigvalsh(k)
    if float(eigenvalues.min()) <= 0.0:
        raise MechBoundaryError(
            "the stiffness matrix is not positive definite: this "
            "configuration has no oscillatory modal basis, so nothing "
            "below is meaningful for it")
    return MechSystem(mass, k, c)


def with_boundary(config: ChainConfig, parameter: BoundaryParameter,
                  factor: float) -> ChainConfig:
    """Scale the fields belonging to ``parameter`` by ``factor``.

    ``factor == 1`` is the reference configuration; ``factor == 0``
    removes the boundary element entirely. Only the named parameter's
    fields move, which is what makes the four change kinds independently
    typed rather than four names for one knob.
    """
    if parameter not in PARAMETER_FIELDS:
        raise MechBoundaryError(f"unknown boundary parameter {parameter!r}")
    if not math.isfinite(float(factor)):
        raise MechBoundaryError("scale factor must be finite")
    updates = {name: getattr(config, name) * float(factor)
               for name in PARAMETER_FIELDS[parameter]}
    return replace(config, **updates)


# --- (3) modes: eigenfrequencies and mass-normalised shapes --------------

@dataclass(frozen=True)
class Modes:
    """Mass-normalised modes of one system.

    ``omega`` ascends; ``shapes`` holds the mode vectors as *columns*,
    normalised so that ``shapes.T @ M @ shapes == I`` and
    ``shapes.T @ K @ shapes == diag(omega**2)``.
    """

    omega: np.ndarray
    shapes: np.ndarray
    M: np.ndarray

    @property
    def n(self) -> int:
        return int(self.omega.size)

    def normalisation_defect(self) -> float:
        """``max|Phi^T M Phi - I|``: zero for a mass-normalised basis."""
        gram = self.shapes.T @ self.M @ self.shapes
        return float(np.max(np.abs(gram - np.eye(self.n))))


def modes(M: np.ndarray, K: np.ndarray) -> Modes:
    """Solve ``K v = omega**2 M v`` for mass-normalised modes.

    Implemented as the Cholesky reduction of the generalised symmetric
    eigenproblem to a standard one — the same object
    ``scipy.linalg.eigh(K, M)`` returns, computed with numpy so the
    module carries no extra dependency. Signs are fixed by making the
    largest-magnitude component of each shape positive, so that mixing
    matrices are reproducible rather than sign-scrambled.
    """
    mass = np.asarray(M, dtype=float)
    stiff = np.asarray(K, dtype=float)
    if mass.ndim != 2 or mass.shape[0] != mass.shape[1]:
        raise MechBoundaryError("M must be a square matrix")
    if stiff.shape != mass.shape:
        raise MechBoundaryError("K must have the same shape as M")
    if not np.allclose(mass, mass.T) or not np.allclose(stiff, stiff.T):
        raise MechBoundaryError("M and K must both be symmetric")
    try:
        chol = np.linalg.cholesky(mass)
    except np.linalg.LinAlgError as exc:
        raise MechBoundaryError(
            "M is not positive definite; a chain with a non-positive "
            "effective mass has no modal basis") from exc

    reduced = np.linalg.solve(chol, np.linalg.solve(chol, stiff).T).T
    reduced = 0.5 * (reduced + reduced.T)
    lam, vec = np.linalg.eigh(reduced)
    if float(lam.min()) < -ORTHONORMALITY_TOL:
        raise MechBoundaryError(
            "the generalised eigenproblem has a negative eigenvalue: the "
            "configuration is statically unstable, not oscillatory")
    omega = np.sqrt(np.clip(lam, 0.0, None))
    shapes = np.linalg.solve(chol.T, vec)
    for j in range(shapes.shape[1]):
        column = shapes[:, j]
        if column[int(np.argmax(np.abs(column)))] < 0.0:
            shapes[:, j] = -column
    return Modes(omega, shapes, mass)


def system_modes(system: MechSystem) -> Modes:
    """The undamped modes of a :class:`MechSystem` (``C`` plays no part)."""
    return modes(system.M, system.K)


# --- (4) states, projection, and the mixing matrix ------------------------

@dataclass(frozen=True)
class State:
    """A mechanical state: nodal displacement and nodal velocity."""

    u: np.ndarray
    v: np.ndarray

    def __post_init__(self) -> None:
        if np.asarray(self.u).shape != np.asarray(self.v).shape:
            raise MechBoundaryError("u and v must have the same shape")

    def momentum(self, M: np.ndarray) -> np.ndarray:
        """``p = M v``, the quantity that is continuous across a jump."""
        return np.asarray(M, dtype=float) @ np.asarray(self.v, dtype=float)


def kinetic_energy(state: State, M: np.ndarray) -> float:
    """``0.5 * v^T M v``."""
    v = np.asarray(state.v, dtype=float)
    return float(0.5 * v @ (np.asarray(M, dtype=float) @ v))


def potential_energy(state: State, K: np.ndarray) -> float:
    """``0.5 * u^T K u``."""
    u = np.asarray(state.u, dtype=float)
    return float(0.5 * u @ (np.asarray(K, dtype=float) @ u))


def energy(state: State, M: np.ndarray, K: np.ndarray) -> float:
    """Total mechanical energy ``0.5*v^T M v + 0.5*u^T K u``."""
    return kinetic_energy(state, M) + potential_energy(state, K)


@dataclass(frozen=True)
class ModalState:
    """A state re-expressed in a modal basis.

    ``q`` and ``qdot`` are the modal displacement and velocity
    amplitudes; ``energies`` is the per-mode energy
    ``0.5*qdot**2 + 0.5*omega**2 * q**2``, which sums to the total
    mechanical energy because the basis is mass-normalised.
    """

    q: np.ndarray
    qdot: np.ndarray
    omega: np.ndarray

    @property
    def energies(self) -> np.ndarray:
        return 0.5 * self.qdot ** 2 + 0.5 * (self.omega * self.q) ** 2

    @property
    def total_energy(self) -> float:
        return float(np.sum(self.energies))

    @property
    def fractions(self) -> np.ndarray:
        total = self.total_energy
        if total <= 0.0:
            raise MechBoundaryError(
                "a state with no energy has no modal energy fractions")
        return self.energies / total

    def participation(self, index: int) -> float:
        """Fraction of the modal energy still carried by mode ``index``."""
        if not 0 <= index < self.q.size:
            raise MechBoundaryError("mode index outside the basis")
        return float(self.fractions[index])


def project(state: State, basis: Modes) -> ModalState:
    """Re-express a state in a modal basis: ``q = Phi^T M u``.

    Mass-normalisation is what makes this a projection rather than a
    solve: ``u = Phi q`` and ``v = Phi qdot`` recover the state exactly.
    """
    u = np.asarray(state.u, dtype=float)
    v = np.asarray(state.v, dtype=float)
    if u.size != basis.n:
        raise MechBoundaryError("state and basis have different dimensions")
    weight = basis.shapes.T @ basis.M
    return ModalState(weight @ u, weight @ v, basis.omega)


def reconstruct(modal: ModalState, basis: Modes) -> State:
    """Inverse of :func:`project`: ``u = Phi q``, ``v = Phi qdot``."""
    return State(basis.shapes @ modal.q, basis.shapes @ modal.qdot)


def mode_mixing_matrix(modes_before: Modes, modes_after: Modes) -> np.ndarray:
    """``T = Phi_after^T M_after Phi_before``.

    Column ``j`` holds the after-basis amplitudes of before-mode ``j``,
    which is exactly what a sudden change hands to the new system. When
    the mass matrix does not change, ``T`` is orthogonal and its columns
    are unit vectors: a change that leaves the basis alone gives the
    identity, and a change that moves it spreads each column over
    several rows.
    """
    if modes_before.n != modes_after.n:
        raise MechBoundaryError("the two bases have different dimensions")
    return modes_after.shapes.T @ modes_after.M @ modes_before.shapes


def mixing_offdiagonal_fraction(mixing: np.ndarray,
                                index: int | None = None) -> float:
    """How much of a column of ``T`` sits off its own diagonal entry.

    ``1 - T[k,k]**2 / sum_i T[i,k]**2`` for column ``k``; averaged over
    all columns when ``index`` is None. Zero means the basis did not
    move; a large value means a sudden change would scatter that mode
    across the new ones.
    """
    matrix = np.asarray(mixing, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise MechBoundaryError("a mixing matrix must be square")
    columns = range(matrix.shape[1]) if index is None else (int(index),)
    out = []
    for j in columns:
        if not 0 <= j < matrix.shape[1]:
            raise MechBoundaryError("mode index outside the mixing matrix")
        norm = float(matrix[:, j] @ matrix[:, j])
        if norm <= 0.0:
            raise MechBoundaryError("a mixing column cannot be null")
        out.append(1.0 - float(matrix[j, j] ** 2) / norm)
    return float(np.mean(out))


def apply_sudden(state: State, before: MechSystem,
                 after: MechSystem) -> State:
    """The state immediately after a discontinuous parameter change.

    Displacement is continuous, and so is momentum ``p = M v`` — the
    forces stay bounded through the change, so no impulse is delivered.
    When the mass changes the *velocity* therefore jumps, and the
    kinetic energy jumps with it; that jump is boundary work, and
    :func:`work_done_by_boundary` books it.
    """
    p = state.momentum(before.M)
    return State(np.array(state.u, dtype=float),
                 np.linalg.solve(after.M, p))


# --- (5) energy and work accounting --------------------------------------

@dataclass(frozen=True)
class Snapshot:
    """A system together with a state in it."""

    system: MechSystem
    state: State

    @property
    def energy(self) -> float:
        return energy(self.state, self.system.M, self.system.K)


def work_done_by_boundary(before: Snapshot, after: Snapshot) -> float:
    """Energy handed to the structure by an instantaneous change.

    Evaluated from the parameter change itself, not as a residual:

        ``W = 0.5*u^T (K_a - K_b) u + 0.5*p^T (M_a^-1 - M_b^-1) p``

    with ``u`` and ``p`` the continuous displacement and momentum. The
    first term is the work done stiffening or relaxing a *displaced*
    structure; the second is what changing the inertia does to a
    *moving* one. Nothing is dissipated in zero time, so for a sudden
    change this is the whole ledger.

    For a gradual change the same quantity is the time integral
    ``\\int (0.5*u^T Kdot u - 0.5*v^T Mdot v) dt``, which
    :func:`simulate_change` accumulates alongside the trajectory.
    """
    u = np.asarray(before.state.u, dtype=float)
    p = before.state.momentum(before.system.M)
    dk = after.system.K - before.system.K
    strain_work = 0.5 * float(u @ (dk @ u))
    inertia_work = 0.5 * float(
        p @ (np.linalg.solve(after.system.M, p)
             - np.linalg.solve(before.system.M, p)))
    return strain_work + inertia_work


def energy_ledger(energy_before: float, energy_after: float,
                  boundary_work: float, dissipated: float = 0.0,
                  tol: float = LEDGER_TOL,
                  include_boundary_work: bool = True) -> dict:
    """``E_after == E_before + W_boundary - E_dissipated``, checked.

    ``include_boundary_work=False`` is the deliberate omission: drop the
    term that pays for the change and the identity fails, which is what
    makes its presence a result rather than a decoration.
    """
    if tol <= 0.0:
        raise MechBoundaryError("ledger tolerance must be positive")
    if dissipated < -abs(tol) * max(1.0, abs(energy_before)):
        raise MechBoundaryError(
            "dissipated energy is negative: a dashpot cannot be a source")
    work = float(boundary_work) if include_boundary_work else 0.0
    predicted = float(energy_before) + work - float(dissipated)
    residual = float(energy_after) - predicted
    scale = max(1.0, abs(float(energy_before)), abs(float(energy_after)))
    return {
        "energy_before": float(energy_before),
        "energy_after": float(energy_after),
        "boundary_work": float(boundary_work),
        "boundary_work_included": bool(include_boundary_work),
        "dissipated": float(dissipated),
        "predicted_energy_after": predicted,
        "residual": residual,
        "relative_residual": abs(residual) / scale,
        "tolerance": float(tol),
        "closes": bool(abs(residual) <= float(tol) * scale),
        "identity": "E_after == E_before + W_boundary - E_dissipated",
        "measured_here": "nothing",
    }


def refuse_energy_from_nothing(energy_gain: float = 1.0,
                               claimed_source: str = "the boundary itself",
                               ) -> None:
    """Refuse an energy gain across a boundary change with no payer.

    A mechanical mode that carries more energy after a boundary change
    than before it was worked on. Stiffening a displaced spring, moving
    a loaded support, or pulling an electrode off a vibrating surface all
    require force through distance, and the agent supplying that force is
    where the extra energy came from. A ledger with the gain on one side
    and nothing on the other is not an energy balance.
    """
    raise MechBoundaryError(
        f"an energy gain of {float(energy_gain):g} attributed to "
        f"{claimed_source!r} is refused. Changing a stiffness, a support "
        f"impedance, a damping or an electrode loading while the "
        f"structure is moving does work on it: W = "
        f"0.5*u^T dK u - 0.5*v^T dM v, supplied by the actuator, "
        f"tensioner or bias that made the change. The boundary is not a "
        f"source; it is the route through which an external agent pays. "
        f"BOUNDARY_WORK_REQUIRED")


def refuse_quantum_claim(claim: str = "photons were created",
                         ) -> None:
    """Refuse any quantum reading of this classical model.

    Mode mixing here is the projection of one real symmetric eigenbasis
    onto another. It has no vacuum state, no field operators, no
    commutator to preserve and no photon number. The quantum lane — the
    Bogoliubov transformation, pair creation, and the switching-time
    divergence — lives in ``r11/dynboundary.py`` and is a separate
    object with separate refusals.
    """
    raise MechBoundaryError(
        f"the claim {claim!r} is refused: this is a classical, "
        f"deterministic, finite-degree-of-freedom mechanical model. It "
        f"has no field operators, no vacuum, no commutator and no photon "
        f"number, so mode mixing here establishes nothing about photon "
        f"creation, the dynamical Casimir effect, or any quantum boundary "
        f"effect. Classical modal scattering and quantum pair creation "
        f"are different objects; the quantum lane is r11/dynboundary.py. "
        f"CLASSICAL_MODEL_ESTABLISHES_NOTHING_QUANTUM")


# --- (6) the time-dependent change ---------------------------------------

@dataclass(frozen=True)
class BoundaryChange:
    """One parameter change, typed by kind and by profile.

    ``factor_before`` and ``factor_after`` scale the fields belonging to
    ``parameter`` (see :func:`with_boundary`). ``tau`` is the ramp time
    and must be zero for a SUDDEN change and positive for a GRADUAL one.
    """

    parameter: BoundaryParameter
    profile: ChangeProfile = ChangeProfile.SUDDEN
    factor_before: float = 1.0
    factor_after: float = 4.0
    tau: float = 0.0

    def __post_init__(self) -> None:
        if not isinstance(self.parameter, BoundaryParameter):
            raise MechBoundaryError("parameter must be a BoundaryParameter")
        if not isinstance(self.profile, ChangeProfile):
            raise MechBoundaryError("profile must be a ChangeProfile")
        if self.tau < 0.0:
            raise MechBoundaryError("ramp time cannot be negative")
        if self.profile is ChangeProfile.SUDDEN and self.tau != 0.0:
            raise MechBoundaryError(
                "a SUDDEN change has no ramp time; use GRADUAL for tau > 0")
        if self.profile is ChangeProfile.GRADUAL and self.tau <= 0.0:
            raise MechBoundaryError(
                "a GRADUAL change needs tau > 0; use SUDDEN for a jump")

    def configs(self, config: ChainConfig) -> tuple[ChainConfig, ChainConfig]:
        return (with_boundary(config, self.parameter, self.factor_before),
                with_boundary(config, self.parameter, self.factor_after))

    def systems(self, config: ChainConfig) -> tuple[MechSystem, MechSystem]:
        before, after = self.configs(config)
        return build_system(before), build_system(after)


def ramp(t: float, tau: float) -> tuple[float, float]:
    """The smootherstep ramp ``s(t)`` and its rate ``sdot(t)``.

    ``s = 6x**5 - 15x**4 + 10x**3`` with ``x = t/tau`` has zero first and
    second derivative at both ends, so the ramp introduces no kink of its
    own and the approach to the adiabatic limit is set by the physics
    rather than by a discontinuity in the schedule.
    """
    if tau <= 0.0:
        return (1.0 if t > 0.0 else 0.0, 0.0)
    x = t / tau
    if x <= 0.0:
        return (0.0, 0.0)
    if x >= 1.0:
        return (1.0, 0.0)
    s = x * x * x * (10.0 + x * (-15.0 + 6.0 * x))
    sdot = 30.0 * x * x * (1.0 - x) ** 2 / tau
    return (float(s), float(sdot))


def _diagonal(matrix: np.ndarray) -> np.ndarray:
    """The diagonal of a matrix that must be diagonal."""
    d = np.diag(matrix).copy()
    if np.any(np.abs(matrix - np.diag(d)) > 0.0):
        raise MechBoundaryError(
            "the time integrator requires a diagonal mass matrix; a "
            "consistent-mass chain would need the general form")
    return d


def _integrate(before: MechSystem, after: MechSystem, state: State,
               tau: float, n_steps: int) -> tuple[State, float, float,
                                                  list[float]]:
    """RK4 on ``(u, p, W, D)`` through a ramp of duration ``tau``.

    The augmented state carries the accumulated boundary work and the
    accumulated dissipation, so the ledger terms come out of the same
    integration as the trajectory rather than being inferred from it.
    """
    if n_steps < 1:
        raise MechBoundaryError("an integration needs at least one step")
    md0 = _diagonal(before.M)
    dmd = _diagonal(after.M) - md0
    k0, dk = before.K, after.K - before.K
    c0, dc = before.C, after.C - before.C
    n = before.n

    def deriv(t: float, y: np.ndarray) -> np.ndarray:
        s, sdot = ramp(t, tau)
        md = md0 + s * dmd
        u = y[:n]
        p = y[n:2 * n]
        v = p / md
        kt = k0 + s * dk
        ct = c0 + s * dc
        out = np.empty_like(y)
        out[:n] = v
        out[n:2 * n] = -(kt @ u) - (ct @ v)
        out[2 * n] = sdot * (0.5 * float(u @ (dk @ u))
                             - 0.5 * float(np.sum(dmd * v * v)))
        out[2 * n + 1] = float(v @ (ct @ v))
        return out

    y = np.zeros(2 * n + 2)
    y[:n] = np.asarray(state.u, dtype=float)
    y[n:2 * n] = state.momentum(before.M)
    dt = tau / n_steps if tau > 0.0 else 0.0
    trace = [energy(state, before.M, before.K)]
    for step in range(n_steps):
        t = step * dt
        k1 = deriv(t, y)
        k2 = deriv(t + 0.5 * dt, y + 0.5 * dt * k1)
        k3 = deriv(t + 0.5 * dt, y + 0.5 * dt * k2)
        k4 = deriv(t + dt, y + dt * k3)
        y = y + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
        s, _ = ramp(t + dt, tau)
        md = md0 + s * dmd
        current = State(y[:n].copy(), y[n:2 * n] / md)
        trace.append(energy(current, np.diag(md), k0 + s * dk))
    md_end = md0 + dmd if tau > 0.0 else md0
    final = State(y[:n].copy(), y[n:2 * n] / md_end)
    return final, float(y[2 * n]), float(y[2 * n + 1]), trace


@dataclass(frozen=True)
class ChangeResult:
    """What one boundary change did to one mode."""

    parameter: BoundaryParameter
    profile: ChangeProfile
    tau: float
    mode_index: int
    omega_before: np.ndarray
    omega_after: np.ndarray
    energy_before: float
    energy_after: float
    boundary_work: float
    dissipated: float
    modal_energies: np.ndarray
    participation: float
    mixing_offdiagonal: float
    n_steps: int

    def ledger(self, tol: float = LEDGER_TOL,
               include_boundary_work: bool = True) -> dict:
        return energy_ledger(self.energy_before, self.energy_after,
                             self.boundary_work, self.dissipated, tol,
                             include_boundary_work)

    def as_dict(self) -> dict:
        return {
            "parameter": self.parameter.value,
            "profile": self.profile.value,
            "tau": self.tau,
            "mode_index": self.mode_index,
            "omega_before": self.omega_before.tolist(),
            "omega_after": self.omega_after.tolist(),
            "modal_energy_fractions": (
                self.modal_energies / float(np.sum(self.modal_energies))
            ).tolist(),
            "participation": self.participation,
            "mixing_offdiagonal": self.mixing_offdiagonal,
            "ledger": self.ledger(),
            "n_steps": self.n_steps,
            "measured_here": "nothing",
        }


def initial_state(basis: Modes, mode_index: int = 0,
                  amplitude: float = 1.0, phase: float = 0.0) -> State:
    """A state that is exactly one mode of the *before* system.

    ``u = a cos(phase) phi_k``, ``v = -a omega_k sin(phase) phi_k``, so
    the modal energy is ``0.5 * (a * omega_k)**2`` at every phase and
    every later modal fraction is a statement about where that one
    mode's energy went.

    The default ``phase == 0`` is the turning point: all the energy is
    strain energy, and a sudden stiffness change therefore does the most
    work it can. At ``phase == pi/2`` the structure is passing through
    zero displacement, a stiffness change does no work at all, and the
    scattering is correspondingly weaker. The phase dependence is
    physics, not an artefact, and it is exposed rather than averaged
    away.
    """
    if not 0 <= mode_index < basis.n:
        raise MechBoundaryError("mode index outside the basis")
    shape = basis.shapes[:, int(mode_index)]
    omega = float(basis.omega[int(mode_index)])
    a = float(amplitude)
    return State(a * math.cos(float(phase)) * shape,
                 -a * omega * math.sin(float(phase)) * shape)


def simulate_change(config: ChainConfig, change: BoundaryChange,
                    mode_index: int = 0,
                    steps_per_period: int = STEPS_PER_PERIOD,
                    phase: float = 0.0) -> ChangeResult:
    """Start in one before-mode, make the change, report where the energy went.

    SUDDEN is evaluated in closed form — displacement and momentum are
    continuous, nothing is dissipated in zero time, and the boundary work
    is :func:`work_done_by_boundary`. GRADUAL is integrated, and the
    boundary work and dissipation are accumulated along the trajectory.
    """
    before, after = change.systems(config)
    basis_before = system_modes(before)
    basis_after = system_modes(after)
    start = initial_state(basis_before, mode_index, phase=phase)
    e_before = energy(start, before.M, before.K)
    mixing = mode_mixing_matrix(basis_before, basis_after)
    offdiag = mixing_offdiagonal_fraction(mixing, mode_index)

    if change.profile is ChangeProfile.SUDDEN:
        end = apply_sudden(start, before, after)
        work = work_done_by_boundary(Snapshot(before, start),
                                     Snapshot(after, end))
        dissipated = 0.0
        n_steps = 0
    else:
        omega_max = float(max(basis_before.omega.max(),
                              basis_after.omega.max()))
        if omega_max <= 0.0:
            raise MechBoundaryError("the system has no non-zero mode")
        dt_target = (2.0 * math.pi / omega_max) / max(1, int(steps_per_period))
        n_steps = max(MIN_RAMP_STEPS, int(math.ceil(change.tau / dt_target)))
        end, work, dissipated, _ = _integrate(before, after, start,
                                              change.tau, n_steps)

    e_after = energy(end, after.M, after.K)
    modal = project(end, basis_after)
    return ChangeResult(
        parameter=change.parameter,
        profile=change.profile,
        tau=float(change.tau),
        mode_index=int(mode_index),
        omega_before=basis_before.omega,
        omega_after=basis_after.omega,
        energy_before=e_before,
        energy_after=e_after,
        boundary_work=float(work),
        dissipated=float(dissipated),
        modal_energies=modal.energies,
        participation=modal.participation(mode_index),
        mixing_offdiagonal=offdiag,
        n_steps=int(n_steps),
    )


def free_response(system: MechSystem, state: State, duration: float,
                  steps_per_period: int = STEPS_PER_PERIOD) -> dict:
    """Let a system ring with fixed matrices; report the energy trace.

    No parameter moves, so the boundary work is zero and the only route
    out of the ledger is the dashpots. With ``C == 0`` the energy is
    conserved to integrator accuracy; with ``C > 0`` and no drive it
    decreases, strictly, every step where the structure is moving.
    """
    if duration <= 0.0:
        raise MechBoundaryError("duration must be positive")
    basis = system_modes(system)
    omega_max = float(basis.omega.max())
    dt_target = (2.0 * math.pi / omega_max) / max(1, int(steps_per_period))
    n_steps = max(MIN_RAMP_STEPS, int(math.ceil(duration / dt_target)))
    end, work, dissipated, trace = _integrate(system, system, state,
                                              duration, n_steps)
    e_before = energy(state, system.M, system.K)
    e_after = energy(end, system.M, system.K)
    return {
        "energy_before": e_before,
        "energy_after": e_after,
        "energy_trace": trace,
        "boundary_work": float(work),
        "dissipated": float(dissipated),
        "is_damped": system.is_damped,
        "monotone_decreasing": bool(
            np.all(np.diff(np.asarray(trace)) <= 1e-12 * max(1.0, e_before))),
        "ledger": energy_ledger(e_before, e_after, work, dissipated),
        "measured_here": "nothing",
    }


# --- (7) the headline: mixing against ramp time --------------------------

#: The ramp times used by the default sweep, in units of the model's own
#: time scale. They span the sudden end (much shorter than a period) to
#: the adiabatic end (far longer than the slowest beat period).
DEFAULT_TAUS: tuple[float, ...] = (0.1, 1.0, 5.0, 20.0, 80.0)


def tau_sweep(config: ChainConfig, parameter: BoundaryParameter,
              taus: "tuple[float, ...] | list[float]" = DEFAULT_TAUS,
              mode_index: int = 0, factor_before: float = 1.0,
              factor_after: float = 4.0,
              steps_per_period: int = STEPS_PER_PERIOD,
              phase: float = 0.0) -> dict:
    """Participation of the target mode against ramp time.

    The sudden case is included as the ``tau -> 0`` end. The expected
    behaviour, and the thing the sweep exists to exhibit, is that
    participation rises monotonically with ``tau`` toward the adiabatic
    limit of one: a fast change scatters the mode, a slow one carries it
    across intact.
    """
    ramp_times = [float(t) for t in taus]
    if len(ramp_times) < 2:
        raise MechBoundaryError("a sweep needs at least two ramp times")
    if any(t <= 0.0 for t in ramp_times):
        raise MechBoundaryError("sweep ramp times must be positive")
    if any(b >= a for a, b in zip(ramp_times[1:], ramp_times)):
        raise MechBoundaryError("sweep ramp times must ascend")

    sudden = simulate_change(
        config, BoundaryChange(parameter, ChangeProfile.SUDDEN,
                               factor_before, factor_after, 0.0),
        mode_index, steps_per_period, phase)
    results = [
        simulate_change(
            config, BoundaryChange(parameter, ChangeProfile.GRADUAL,
                                   factor_before, factor_after, t),
            mode_index, steps_per_period, phase)
        for t in ramp_times]
    participation = [r.participation for r in results]
    diffs = np.diff(np.asarray(participation))
    tol = 1e-9
    basis_moves = bool(sudden.mixing_offdiagonal > 1e-12)
    if not basis_moves:
        verdict = "BASIS_UNMOVED_NO_MODAL_SCATTERING"
    elif participation[-1] > sudden.participation:
        verdict = "ADIABATIC_LIMIT_PRESERVES_MODAL_IDENTITY"
    else:
        verdict = "SUDDEN_CHANGE_SCATTERS_MODAL_ENERGY"
    return {
        "parameter": parameter.value,
        "mode_index": int(mode_index),
        "factor_before": float(factor_before),
        "factor_after": float(factor_after),
        "sudden_participation": sudden.participation,
        "sudden_mixing_offdiagonal": sudden.mixing_offdiagonal,
        "tau": ramp_times,
        "participation": participation,
        "gain_over_sudden": [p - sudden.participation for p in participation],
        "monotone_increasing": bool(np.all(diffs >= -tol)),
        "strictly_increasing": bool(np.all(diffs > 0.0)),
        "adiabatic_participation": participation[-1],
        "basis_moves": basis_moves,
        "ledgers_close": (all(r.ledger()["closes"] for r in results)
                          and sudden.ledger()["closes"]),
        "note": ("a sudden change scatters the mode across the new basis; "
                 "a ramp long compared with the beat periods carries it "
                 "across intact, and participation tends to one. A "
                 "parameter that touches neither M nor K moves no "
                 "undamped mode shape, and its sweep is flat at one"),
        "measured_here": "nothing",
        "verdict": verdict,
    }


def mixing_headline(config: ChainConfig = DEFAULT_CHAIN,
                    parameter: BoundaryParameter = BoundaryParameter.STIFFNESS,
                    ) -> dict:
    """Sudden against adiabatic for one parameter, as one small dict."""
    sweep = tau_sweep(config, parameter)
    return {
        "parameter": sweep["parameter"],
        "sudden_participation": sweep["sudden_participation"],
        "adiabatic_participation": sweep["adiabatic_participation"],
        "monotone_increasing": sweep["monotone_increasing"],
        "tau": sweep["tau"],
        "participation": sweep["participation"],
        "measured_here": "nothing",
    }


# --- (8) the report -------------------------------------------------------

def mechboundary_report() -> dict:
    """The standing statement of what this module is and is not."""
    return {
        "what_this_is": (
            "a discretised 1-D mass-spring-damper resonator whose "
            "boundary condition changes in time, in four independently "
            "typed kinds (stiffness, damping, support impedance, "
            "electrode loading) and two profiles (sudden, gradual over a "
            "ramp time tau), with mass-normalised modal projection before "
            "and after the change"),
        "the_real_result": (
            "a sudden change scatters a single mode's energy across the "
            "new modal basis, because the bases are not the same; a "
            "gradual change with tau long compared with the beat periods "
            "tends to the adiabatic limit, where the mixing matrix "
            "approaches the identity and the mode keeps its identity. "
            "Participation of the target mode rises monotonically with "
            "tau"),
        "the_energy_result": (
            "E_after == E_before + W_boundary - E_dissipated, closed "
            "numerically for both profiles. W_boundary = "
            "integral of (0.5*u^T Kdot u - 0.5*v^T Mdot v) dt is work "
            "done on the structure by whatever changed the boundary; drop "
            "it and the identity fails"),
        "parameters": [p.value for p in BoundaryParameter],
        "profiles": [p.value for p in ChangeProfile],
        "damping_note": (
            "a pure damping change moves no undamped mode shape at all: "
            "C does not enter K v = omega**2 M v, so its mixing matrix is "
            "the identity and its signature is dissipation, not "
            "scattering. That is a result about which matrix a parameter "
            "touches, not an omission. A non-proportional C still moves a "
            "little energy between modes as the structure rings, because "
            "Phi^T C Phi is not diagonal; that is damping coupling, and "
            "it is a different mechanism from a basis that has moved"),
        "firewalls": [
            "an energy gain across a boundary change is work done by the "
            "agent that changed the boundary, never a source",
            "a classical modal-scattering number is not a photon-creation "
            "number; the quantum lane is r11/dynboundary.py",
            "the mixing matrix is a projection between two real symmetric "
            "eigenbases and has no vacuum, no operators and no quanta",
            "a stiffness matrix that is not positive definite has no "
            "oscillatory modal basis and is refused rather than reported",
        ],
        "distinct_from_the_quantum_lane": (
            "r11/dynboundary.py treats a time-dependent boundary acting "
            "on a quantum field: a Bogoliubov transformation mixing "
            "positive- and negative-frequency parts, pair creation from "
            "vacuum, and a photon number that diverges only in the "
            "impossible instantaneous limit. This module treats a "
            "time-dependent boundary acting on a classical mechanical "
            "mode: a change of eigenbasis, modal scattering, and work "
            "done on a structure. The mathematics rhymes and the physics "
            "does not transfer"),
        "verdicts": list(VERDICTS),
        "evidence_class": "NUMERICAL_SIMULATION",
        "evidence_classes": ["ANALYTIC_MODEL", "NUMERICAL_SIMULATION"],
        "hardware_status": "DEFERRED — no resonator has been built or driven",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "what_this_does_not_say": (
            "It does not say any resonator exists, that any boundary was "
            "switched, or that any mode, frequency, energy or loss was "
            "measured. It does not say the chain parameters describe a "
            "real material, cut, mount or electrode: they are model "
            "numbers in arbitrary consistent units. It does not say "
            "anything about photons, vacuum, pair creation or the "
            "dynamical Casimir effect — this is a classical model and "
            "quantum claims are refused outright. It does not say energy "
            "can be extracted by cycling a boundary: the ledger closes "
            "only because an external agent pays for every change."),
        "verdict": DEFAULT_VERDICT,
    }
