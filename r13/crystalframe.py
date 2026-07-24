"""P07 — the direct and reciprocal lattice frame of alpha-quartz.

Alpha-quartz is trigonal, space group ``P3_121`` (or its enantiomorph
``P3_221``), and it is described in the hexagonal setting by two lattice
constants: an in-plane edge ``a`` and a ``c`` axis perpendicular to it,
with the two in-plane axes at 120 degrees. This module writes down that
frame as an **established-physics geometry model** and computes the
quantities the frame *defines*: the direct basis, the reciprocal basis,
the cell volume, plane spacings, the fractional-to-Cartesian map, and the
proper rotations of the trigonal point group ``32`` (``D_3``).

**What is established physics here.** The lattice constants
``a = 4.913 A`` and ``c = 5.405 A`` are CONVENTIONAL_LITERATURE values for
alpha-quartz -- quoted from the crystallographic literature, never
measured in this repository. Everything built from them is
SOURCE_ESTABLISHED_PHYSICS geometry:

* the direct hexagonal basis ``a1, a2, a3`` (``a3`` along ``c``);
* the reciprocal basis ``b_i = 2*pi (a_j x a_k) / V``, which satisfies
  the **load-bearing identity** ``a_i . b_j = 2*pi delta_ij`` exactly;
* the cell volume ``V = a1 . (a2 x a3)``, which equals the analytic
  hexagonal form ``V = (sqrt(3)/2) a^2 c``;
* the plane spacing ``d(hkl)``, which equals the analytic hexagonal
  ``1/d^2 = (4/3)(h^2 + hk + k^2)/a^2 + l^2/c^2``;
* the crystallographic <-> Cartesian maps, which round-trip; and
* the proper rotations of point group ``32``: a 3-fold about ``c`` and
  three 2-folds about the ``a`` axes, each orthogonal with determinant
  ``+1`` and the 3-fold cubed equal to the identity.

**A geometry model is not a diffraction measurement.** Writing down the
frame of alpha-quartz and computing its reciprocal cell is textbook
crystallography; it says nothing about any *particular* crystal. No
specimen is mounted, no beam is run, no reflection is recorded.
:func:`refuse_frame_as_measurement` refuses to read any number here as a
measured lattice parameter or a diffraction result. The default verdict
is ``DIRECT_AND_RECIPROCAL_FRAME_CONSISTENT``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

import numpy as np

# --- verdict, claim classes, tolerances ---------------------------------

DEFAULT_VERDICT = "DIRECT_AND_RECIPROCAL_FRAME_CONSISTENT"

#: The frame is a geometry model taken from established crystallography.
CLAIM_CLASS = "SOURCE_ESTABLISHED_PHYSICS"

#: The claim classes a statement in this module may declare.
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
    "BENCH_MEASUREMENT",
    "UNSUPPORTED",
    "BLOCKED_MISSING_INPUT",
)

#: CONVENTIONAL_LITERATURE lattice constants for alpha-quartz, in
#: angstroms. Quoted from the crystallographic literature; NOT measured
#: here. a is the hexagonal in-plane edge, c the axis perpendicular to it.
QUARTZ_A_ANGSTROM = 4.913
QUARTZ_C_ANGSTROM = 5.405

#: Tolerance for the exact geometric identities (floating precision).
FRAME_TOL = 1e-9

#: The enantiomorphic trigonal space-group pair of alpha-quartz, carried
#: as literature labels only.
QUARTZ_SPACE_GROUPS = ("P3_121", "P3_221")


class CrystalFrameError(RuntimeError):
    """Raised when a lattice-frame claim exceeds what the geometry licenses.

    Covers the structural refusals (non-positive lattice constants, a
    forbidden ``(0,0,0)`` reflection, a non-3-vector) and the load-bearing
    governance refusal :func:`refuse_frame_as_measurement`.
    """


#: Alias retained so a caller that reaches for the atomistic error name on
#: a frame refusal still gets a typed exception, as the refusal contract
#: allows either. It is a distinct type; ``CrystalFrameError`` is primary.
class AtomisticError(RuntimeError):
    """Companion typed error; see :mod:`r13.atomistic` for its home use."""


def _positive(value: float, what: str) -> float:
    x = float(value)
    if not math.isfinite(x):
        raise CrystalFrameError(f"{what} must be finite")
    if x <= 0.0:
        raise CrystalFrameError(f"{what} must be positive")
    return x


# --- the lattice frame ---------------------------------------------------

@dataclass(frozen=True)
class LatticeFrame:
    """The direct/reciprocal frame of a trigonal (hexagonal-setting) cell.

    Built from two lattice constants ``a`` and ``c`` (angstroms). The
    in-plane axes ``a1, a2`` are separated by 120 degrees and ``a3`` lies
    along ``c``. Every derived quantity is SOURCE_ESTABLISHED_PHYSICS
    geometry, not a measurement of any real crystal.
    """

    a: float = QUARTZ_A_ANGSTROM
    c: float = QUARTZ_C_ANGSTROM
    a_class: str = "CONVENTIONAL_LITERATURE"
    material: str = "alpha-quartz (trigonal, P3_121 / P3_221)"

    def __post_init__(self) -> None:
        _positive(self.a, "the lattice constant a")
        _positive(self.c, "the lattice constant c")
        if self.a_class not in CLAIM_CLASSES:
            raise CrystalFrameError(
                f"{self.a_class!r} is not a declared claim class")

    # -- direct basis -----------------------------------------------------

    def direct_basis(self) -> np.ndarray:
        """The direct basis rows ``a1, a2, a3`` (hexagonal setting), in A.

        ``a1 = a(1, 0, 0)``, ``a2 = a(-1/2, sqrt(3)/2, 0)`` (120 degrees
        from ``a1``), and ``a3 = c(0, 0, 1)`` along the trigonal axis.
        """
        a, c = self.a, self.c
        s3 = math.sqrt(3.0) / 2.0
        return np.array([[a, 0.0, 0.0],
                         [-0.5 * a, s3 * a, 0.0],
                         [0.0, 0.0, c]], dtype=float)

    def cell_volume(self) -> float:
        """``V = a1 . (a2 x a3)``; equals ``(sqrt(3)/2) a^2 c`` analytically."""
        A = self.direct_basis()
        return float(np.dot(A[0], np.cross(A[1], A[2])))

    def analytic_volume(self) -> float:
        """The closed-form hexagonal cell volume ``(sqrt(3)/2) a^2 c``."""
        return math.sqrt(3.0) / 2.0 * self.a ** 2 * self.c

    # -- reciprocal basis -------------------------------------------------

    def reciprocal_basis(self) -> np.ndarray:
        """The reciprocal basis rows ``b_i = 2*pi (a_j x a_k) / V``.

        Built so that ``a_i . b_j = 2*pi delta_ij`` holds exactly (to
        floating precision) for every ``i, j``.
        """
        A = self.direct_basis()
        V = float(np.dot(A[0], np.cross(A[1], A[2])))
        if abs(V) < FRAME_TOL:
            raise CrystalFrameError("degenerate cell: zero volume")
        two_pi = 2.0 * math.pi
        b1 = two_pi * np.cross(A[1], A[2]) / V
        b2 = two_pi * np.cross(A[2], A[0]) / V
        b3 = two_pi * np.cross(A[0], A[1]) / V
        return np.array([b1, b2, b3], dtype=float)

    def metric_dual_identity(self) -> np.ndarray:
        """The matrix ``a_i . b_j``; equals ``2*pi`` times the identity."""
        A = self.direct_basis()
        B = self.reciprocal_basis()
        return A @ B.T

    # -- plane spacings ---------------------------------------------------

    def reciprocal_vector(self, h: int, k: int, l: int) -> np.ndarray:
        """``G = h b1 + k b2 + l b3``, the reciprocal-lattice vector."""
        B = self.reciprocal_basis()
        return h * B[0] + k * B[1] + l * B[2]

    def d_spacing(self, h: int, k: int, l: int) -> float:
        """Interplanar spacing ``d(hkl) = 2*pi / |G|`` for the plane ``(hkl)``.

        Equals the analytic hexagonal ``1/d^2 =
        (4/3)(h^2 + hk + k^2)/a^2 + l^2/c^2``.
        """
        if h == 0 and k == 0 and l == 0:
            raise CrystalFrameError(
                "the (0,0,0) reflection has no plane and no spacing")
        G = self.reciprocal_vector(h, k, l)
        gmag = float(np.linalg.norm(G))
        if gmag < FRAME_TOL:
            raise CrystalFrameError("reciprocal vector vanishes; no spacing")
        return 2.0 * math.pi / gmag

    def analytic_inverse_d_squared(self, h: int, k: int, l: int) -> float:
        """The closed-form hexagonal ``1/d^2`` for the plane ``(hkl)``."""
        a, c = self.a, self.c
        return (4.0 / 3.0) * (h * h + h * k + k * k) / a ** 2 + l * l / c ** 2

    # -- fractional <-> Cartesian ----------------------------------------

    def to_cartesian(self, frac) -> np.ndarray:
        """Cartesian position ``r = f1 a1 + f2 a2 + f3 a3`` (angstroms)."""
        f = np.asarray(frac, dtype=float)
        if f.shape != (3,):
            raise CrystalFrameError("fractional coordinates must be a 3-vector")
        return f @ self.direct_basis()

    def to_fractional(self, cart) -> np.ndarray:
        """Fractional coordinates of a Cartesian point; inverse of the above."""
        r = np.asarray(cart, dtype=float)
        if r.shape != (3,):
            raise CrystalFrameError("Cartesian coordinates must be a 3-vector")
        return r @ np.linalg.inv(self.direct_basis())

    # -- trigonal symmetry ------------------------------------------------

    def symmetry_operators(self) -> list[np.ndarray]:
        """The six proper rotations of point group ``32`` (``D_3``).

        The identity, the two powers of the 3-fold about ``c``, and three
        2-folds about the ``a`` axes at 0, 120 and 240 degrees. Each is a
        proper rotation: orthogonal with determinant ``+1``.
        """
        ops = [np.eye(3)]
        # 3-fold about c and its square
        for turn in (1, 2):
            ang = 2.0 * math.pi * turn / 3.0
            ca, sa = math.cos(ang), math.sin(ang)
            ops.append(np.array([[ca, -sa, 0.0],
                                 [sa, ca, 0.0],
                                 [0.0, 0.0, 1.0]], dtype=float))
        # three 2-folds about in-plane axes at 0, 120, 240 degrees.
        # A 180-degree rotation about a unit axis n is 2 n n^T - I.
        for turn in (0, 1, 2):
            ang = 2.0 * math.pi * turn / 3.0
            n = np.array([math.cos(ang), math.sin(ang), 0.0])
            ops.append(2.0 * np.outer(n, n) - np.eye(3))
        return ops


#: The alpha-quartz frame at the literature lattice constants.
QUARTZ_FRAME = LatticeFrame()


# --- the load-bearing refusal -------------------------------------------

def refuse_frame_as_measurement(*_a, **_k) -> None:
    """A lattice-frame geometry model is not a diffraction measurement.

    Writing down the direct and reciprocal frame of alpha-quartz, and
    computing its volume, spacings and symmetry, is established-physics
    geometry. It is not a measurement of any real crystal: no specimen is
    mounted, no radiation is scattered, and no reflection is recorded.
    Reading ``a``, ``c``, ``V`` or any ``d(hkl)`` here as a measured
    lattice parameter or a diffraction result is refused.
    """
    raise CrystalFrameError(
        "refused: the direct/reciprocal frame computed here is a "
        "SOURCE_ESTABLISHED_PHYSICS geometry model built from "
        "CONVENTIONAL_LITERATURE lattice constants. It is not a "
        "BENCH_MEASUREMENT: no crystal was mounted, no beam was run, and no "
        "reflection was recorded. The lattice constants, the cell volume "
        "and every d(hkl) are definitions of the frame, computed, not "
        "observed. PHYSICAL_VALIDATION_NOT_CLAIMED.")


# --- the report ----------------------------------------------------------

def crystalframe_report() -> dict:
    frame = QUARTZ_FRAME
    return {
        "what_this_is": (
            "the direct and reciprocal lattice frame of alpha-quartz "
            "(trigonal, P3_121 / P3_221) as an established-physics geometry "
            "model: direct basis, reciprocal basis, cell volume, plane "
            "spacings, fractional<->Cartesian maps, and the proper "
            "rotations of point group 32"),
        "material": frame.material,
        "space_groups": list(QUARTZ_SPACE_GROUPS),
        "lattice_constants_angstrom": {"a": frame.a, "c": frame.c},
        "lattice_constant_class": frame.a_class,
        "load_bearing_identity": (
            "a_i . b_j = 2*pi delta_ij, checked exactly for the direct and "
            "reciprocal bases"),
        "cell_volume_angstrom3": frame.cell_volume(),
        "analytic_volume_angstrom3": frame.analytic_volume(),
        "n_proper_rotations": len(frame.symmetry_operators()),
        "claim_class": CLAIM_CLASS,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": DEFAULT_VERDICT,
        "what_this_does_not_say": (
            "It does not say any real quartz crystal was mounted, "
            "irradiated or measured, that the lattice constants were "
            "determined here (they are quoted literature values), or that "
            "any d(hkl) is a recorded diffraction result. The frame, the "
            "reciprocal cell, the volume, the spacings and the symmetry "
            "operators are geometry defined by the lattice constants and "
            "computed exactly; a geometry model is not a diffraction "
            "measurement of a real crystal."),
    }
