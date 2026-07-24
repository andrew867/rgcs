"""R12 — reciprocal space: the dual lattice, Laue, Bragg, structure factors.

This module is **textbook crystallography**, implemented correctly and
claiming nothing beyond it. There is no new physics here and none is
offered: the reciprocal lattice, the Laue condition, Bragg's law, the
hexagonal d-spacing formula and the structure factor are all more than a
century old, and the module's job is to compute them exactly and to
refuse the three over-readings the rest of this repository keeps having
to refuse.

**The defining identity.** Given three non-coplanar direct lattice
vectors ``a1, a2, a3`` spanning a cell of volume
``V = a1 . (a2 x a3)``, the reciprocal vectors are

    b1 = 2*pi*(a2 x a3)/V,  b2 = 2*pi*(a3 x a1)/V,  b3 = 2*pi*(a1 x a2)/V

and they satisfy

    ai . bj = 2*pi*delta_ij

identically, for every lattice, with no approximation anywhere. That is
the ``EXACT_IDENTITY`` of this module: :func:`duality_matrix` builds the
3x3 array of dot products, :func:`duality_defect` measures its distance
from ``2*pi*I``, and :meth:`DirectLattice.reciprocal` refuses to hand
back a reciprocal lattice whose duality defect exceeds
:data:`DUALITY_TOL`. The companion identity ``V* = (2*pi)**3 / V`` falls
out of the same algebra and is checked alongside it.

**Alpha quartz, as a conventional literature cell.** Trigonal, space
group ``P3121`` or ``P3221`` — an *enantiomorphic pair*, because quartz
is chiral and a right-handed crystal and a left-handed crystal are
different crystals with mirror-image screw axes. The hexagonal cell is
``a = b = 4.913 A``, ``c = 5.405 A``, ``gamma = 120 deg``, carried as
``CONVENTIONAL_LITERATURE`` and never as a measurement made here. Its
reciprocal cell and its cell volume are computed from those numbers by
the same general code that handles any lattice.

**Laue and Bragg are the same statement.** The scattering vector is
``Q = k_out - k_in``; the Laue condition is ``Q = G`` for some reciprocal
lattice vector ``G = h*b1 + k*b2 + l*b3``. For elastic scattering
``|Q| = 4*pi*sin(theta)/lambda`` and ``|G_hkl| = 2*pi/d_hkl``, so
``Q = G`` is ``2*d*sin(theta) = lambda`` written in vector form.
:func:`laue_is_bragg` computes both sides and reports their agreement,
which is a derivation and not a coincidence.

**Systematic absences come from symmetry, not from the sample.** The
structure factor ``F(hkl) = sum_j f_j exp(2*pi*i*(h*x_j + k*y_j + l*z_j))``
is implemented generically over an atom list. Plant a ``3_1`` screw axis
along ``c`` — the orbit ``(x, y, z)``, ``(-y, x-y, z+1/3)``,
``(-x+y, -x, z+2/3)`` — and ``F(00l)`` vanishes identically unless
``l`` is a multiple of three. Plant a ``2_1`` screw and ``F(00l)``
vanishes unless ``l`` is even. Those extinctions are arithmetic
consequences of the planted symmetry, which is what makes them a POWER
test rather than an assertion.

**The firewall.** Reciprocal space is a *mathematical dual* of the direct
lattice, with units of inverse length. A reciprocal lattice point is not
a place: it is an index triple ``(h, k, l)`` labelling a family of
lattice planes, and no object, observer or signal can be at one.
:func:`refuse_reciprocal_as_physical_space` refuses that reading, and
:func:`refuse_qspace_as_geographic` refuses the further step of treating
a Q-space coordinate as a location on a planet — Q-space is defined per
crystal and per orientation, it rotates when the specimen is rotated on
its mount, and it has no origin, no scale and no axes in common with any
geographic frame. :func:`refuse_measured_pattern_claim` refuses the last
one: no diffractometer exists in this repository and no pattern has been
collected.

Nothing here is measured. Every number is either arithmetic on a declared
cell or a conventional literature value quoted as such.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

import numpy as np

# --- verdict, claim vocabulary, tolerances -------------------------------

#: The standing verdict for this module.
VERDICT = "RECIPROCAL_SPACE_MODEL_STANDARD_CRYSTALLOGRAPHY"

#: The typed claim vocabulary, exact strings, shared across the release.
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

EXACT_IDENTITY = "EXACT_IDENTITY"
SOURCE_ESTABLISHED_PHYSICS = "SOURCE_ESTABLISHED_PHYSICS"
REPOSITORY_COMPUTATIONAL_RESULT = "REPOSITORY_COMPUTATIONAL_RESULT"
BENCH_MEASUREMENT = "BENCH_MEASUREMENT"

#: The claim class of the module as a whole: standard crystallography.
CLAIM_CLASS = SOURCE_ESTABLISHED_PHYSICS

#: The class the alpha-quartz cell constants are carried under.
CONVENTIONAL_LITERATURE = "CONVENTIONAL_LITERATURE"

EVIDENCE_CLASS = "DERIVED_MATHEMATICS"
MEASURED_HERE = "nothing"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: Relative tolerance on the duality identity ``ai . bj == 2*pi*delta_ij``.
#: The identity is exact in algebra; this bounds the floating-point
#: evaluation of it, and nothing is allowed through above it.
DUALITY_TOL = 1e-12

#: A cell whose volume is below this fraction of ``|a1||a2||a3|`` is
#: treated as degenerate: its three vectors are coplanar and it spans no
#: three-dimensional lattice, so it has no reciprocal.
DEGENERATE_CELL_TOL = 1e-12

#: A structure-factor magnitude at or below this fraction of the total
#: scattering power is a systematic absence rather than a small value.
ABSENCE_TOL = 1e-9

TWO_PI = 2.0 * math.pi


class ReciprocalError(RuntimeError):
    """Raised when a reciprocal-space claim exceeds what the algebra says.

    Covers the structural guards (a degenerate cell, a non-integer
    Miller index, a non-physical wavelength, a Bragg angle with no
    solution) and the three load-bearing firewalls:
    :func:`refuse_reciprocal_as_physical_space`,
    :func:`refuse_qspace_as_geographic` and
    :func:`refuse_measured_pattern_claim`.
    """


# --- (0) small guards -----------------------------------------------------

def _finite(value: object, what: str) -> float:
    """Coerce to float and refuse anything non-finite."""
    try:
        x = float(value)                             # type: ignore[arg-type]
    except (TypeError, ValueError):
        raise ReciprocalError(f"cannot read {value!r} as {what}") from None
    if not math.isfinite(x):
        raise ReciprocalError(f"{what} must be finite, got {value!r}")
    return x


def _positive(value: object, what: str) -> float:
    x = _finite(value, what)
    if x <= 0.0:
        raise ReciprocalError(f"{what} must be positive, got {x!r}")
    return x


def _as_vector(value: object, what: str) -> np.ndarray:
    """A finite real 3-vector, as a fresh read-only array."""
    v = np.asarray(value, dtype=float).reshape(-1)
    if v.size != 3:
        raise ReciprocalError(
            f"{what} must be a 3-vector; got {v.size} components")
    if not np.all(np.isfinite(v)):
        raise ReciprocalError(f"{what} must be finite")
    out = np.array(v, dtype=float)
    out.setflags(write=False)
    return out


def _as_hkl(h: object, k: object, l: object) -> tuple[int, int, int]:
    """Miller indices are integers; a reciprocal lattice point is a lattice
    point, and a non-integer triple names no plane family at all."""
    out = []
    for name, value in (("h", h), ("k", k), ("l", l)):
        if isinstance(value, bool):
            raise ReciprocalError(f"the Miller index {name} is not a boolean")
        if isinstance(value, (int, np.integer)):
            out.append(int(value))
            continue
        x = _finite(value, f"the Miller index {name}")
        if x != int(x):
            raise ReciprocalError(
                f"the Miller index {name} must be an integer, got {value!r}. "
                f"Reciprocal lattice points are lattice points; a "
                f"non-integer triple labels no family of planes")
        out.append(int(x))
    if out == [0, 0, 0]:
        raise ReciprocalError(
            "(0, 0, 0) is the origin of reciprocal space, not a reflection: "
            "it has no plane family, no d-spacing and no Bragg angle")
    return (out[0], out[1], out[2])


# --- (1) the direct lattice and its dual ---------------------------------

def reciprocal_vectors(a1: object, a2: object, a3: object
                       ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """``b1, b2, b3`` from ``a1, a2, a3``, by the defining construction.

    ``b1 = 2*pi*(a2 x a3)/V``, ``b2 = 2*pi*(a3 x a1)/V`` and
    ``b3 = 2*pi*(a1 x a2)/V`` with ``V = a1 . (a2 x a3)``. The cyclic
    order is load-bearing: ``a3 x a1`` and ``a1 x a3`` differ by a sign,
    and a sign error here inverts the handedness of the dual basis while
    leaving every length unchanged.
    """
    v1 = _as_vector(a1, "a1")
    v2 = _as_vector(a2, "a2")
    v3 = _as_vector(a3, "a3")
    volume = float(np.dot(v1, np.cross(v2, v3)))
    scale = float(np.linalg.norm(v1) * np.linalg.norm(v2)
                  * np.linalg.norm(v3))
    if scale <= 0.0 or abs(volume) <= DEGENERATE_CELL_TOL * scale:
        raise ReciprocalError(
            "the three direct lattice vectors are coplanar (or one of them "
            "is zero): the cell volume vanishes, the vectors span no "
            "three-dimensional lattice, and there is no reciprocal lattice "
            "to construct")
    b1 = TWO_PI * np.cross(v2, v3) / volume
    b2 = TWO_PI * np.cross(v3, v1) / volume
    b3 = TWO_PI * np.cross(v1, v2) / volume
    for b in (b1, b2, b3):
        b.setflags(write=False)
    return (b1, b2, b3)


def duality_matrix(direct: object, reciprocal: object) -> np.ndarray:
    """The 3x3 array ``M[i, j] = ai . bj``.

    For a correctly constructed dual basis this is ``2*pi`` times the
    identity, exactly. Building it as a matrix rather than checking three
    scalars is deliberate: the off-diagonal entries are the half of the
    identity that catches a swapped or mis-signed vector, and a
    construction that got only the diagonal right would pass a weaker
    test.
    """
    a = [_as_vector(v, f"a{i + 1}") for i, v in enumerate(direct)]
    b = [_as_vector(v, f"b{j + 1}") for j, v in enumerate(reciprocal)]
    if len(a) != 3 or len(b) != 3:
        raise ReciprocalError(
            "the duality matrix needs three direct and three reciprocal "
            "vectors")
    return np.array([[float(np.dot(a[i], b[j])) for j in range(3)]
                     for i in range(3)], dtype=float)


def duality_defect(direct: object, reciprocal: object) -> float:
    """``max |ai . bj - 2*pi*delta_ij|``, in units of ``2*pi``.

    Zero in exact arithmetic. Anything above :data:`DUALITY_TOL` is a
    construction error, not a rounding one.
    """
    m = duality_matrix(direct, reciprocal)
    return float(np.max(np.abs(m - TWO_PI * np.eye(3))) / TWO_PI)


def check_duality(direct: object, reciprocal: object,
                  tol: float = DUALITY_TOL) -> float:
    """Return the duality defect, or refuse the pair of bases.

    This is the module's ``EXACT_IDENTITY`` enforced as a precondition
    rather than reported as a result: a reciprocal basis that does not
    satisfy ``ai . bj = 2*pi*delta_ij`` is not a reciprocal basis, and no
    d-spacing, structure factor or Laue condition computed from it means
    anything.
    """
    defect = duality_defect(direct, reciprocal)
    limit = _positive(tol, "the duality tolerance")
    if defect > limit:
        raise ReciprocalError(
            f"the duality identity ai . bj = 2*pi*delta_ij fails: relative "
            f"defect {defect:.3e} exceeds {limit:.3e}. This identity is "
            f"exact in algebra for every lattice, so a defect above "
            f"floating-point noise means the dual basis was constructed "
            f"wrongly — a swapped cross-product order, a sign, or a volume "
            f"taken with the wrong orientation")
    return defect


@dataclass(frozen=True, eq=False)
class ReciprocalLattice:
    """The dual basis ``b1, b2, b3``, in inverse length.

    Every quantity here has units of inverse length (per angstrom, if the
    direct cell was given in angstroms). That is the first and simplest
    reason a reciprocal lattice point is not a place:
    :func:`refuse_reciprocal_as_physical_space` states the rest.
    """

    b1: np.ndarray
    b2: np.ndarray
    b3: np.ndarray

    def __post_init__(self) -> None:
        object.__setattr__(self, "b1", _as_vector(self.b1, "b1"))
        object.__setattr__(self, "b2", _as_vector(self.b2, "b2"))
        object.__setattr__(self, "b3", _as_vector(self.b3, "b3"))

    @property
    def vectors(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        return (self.b1, self.b2, self.b3)

    @property
    def volume(self) -> float:
        """``b1 . (b2 x b3)``, which equals ``(2*pi)**3 / V``."""
        return float(np.dot(self.b1, np.cross(self.b2, self.b3)))

    def g_vector(self, h: object, k: object, l: object) -> np.ndarray:
        """``G_hkl = h*b1 + k*b2 + l*b3``, in inverse length."""
        i, j, m = _as_hkl(h, k, l)
        g = i * self.b1 + j * self.b2 + m * self.b3
        g.setflags(write=False)
        return g

    def g_magnitude(self, h: object, k: object, l: object) -> float:
        """``|G_hkl| = 2*pi/d_hkl``."""
        return float(np.linalg.norm(self.g_vector(h, k, l)))

    def d_spacing(self, h: object, k: object, l: object) -> float:
        """``d_hkl = 2*pi/|G_hkl|``, in the direct cell's length unit."""
        magnitude = self.g_magnitude(h, k, l)
        if magnitude <= 0.0:
            raise ReciprocalError(
                "a reciprocal lattice vector of zero length has no "
                "d-spacing")
        return TWO_PI / magnitude

    def cell_parameters(self) -> dict:
        """Reciprocal cell lengths and inter-axial angles."""
        return _cell_parameters(self.b1, self.b2, self.b3)

    def as_dict(self) -> dict:
        return {
            "b1": self.b1.tolist(),
            "b2": self.b2.tolist(),
            "b3": self.b3.tolist(),
            "reciprocal_volume": self.volume,
            "cell_parameters": self.cell_parameters(),
            "units": "inverse length (per unit of the direct cell)",
            "measured_here": MEASURED_HERE,
        }


@dataclass(frozen=True, eq=False)
class DirectLattice:
    """Three non-coplanar direct lattice vectors and their dual.

    Length units are the caller's; the class has no opinion about them
    beyond requiring that the reciprocal lattice inherits their inverse.
    The alpha-quartz cell built by :func:`hexagonal_direct_lattice` uses
    angstroms, so its reciprocal is in inverse angstroms.
    """

    a1: np.ndarray
    a2: np.ndarray
    a3: np.ndarray

    def __post_init__(self) -> None:
        object.__setattr__(self, "a1", _as_vector(self.a1, "a1"))
        object.__setattr__(self, "a2", _as_vector(self.a2, "a2"))
        object.__setattr__(self, "a3", _as_vector(self.a3, "a3"))
        # Refuse a degenerate cell at construction rather than at first use.
        reciprocal_vectors(self.a1, self.a2, self.a3)

    @property
    def vectors(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        return (self.a1, self.a2, self.a3)

    @property
    def volume(self) -> float:
        """``V = a1 . (a2 x a3)``, signed by the handedness of the basis."""
        return float(np.dot(self.a1, np.cross(self.a2, self.a3)))

    @property
    def cell_volume(self) -> float:
        """``|V|``: the volume of the primitive cell."""
        return abs(self.volume)

    @property
    def is_right_handed(self) -> bool:
        """``V > 0``. A left-handed basis is legal and dualises correctly;
        the flag exists so that a handedness is never assumed silently."""
        return self.volume > 0.0

    def reciprocal(self, tol: float = DUALITY_TOL) -> ReciprocalLattice:
        """The dual basis, with the duality identity checked on the way out."""
        b1, b2, b3 = reciprocal_vectors(self.a1, self.a2, self.a3)
        check_duality(self.vectors, (b1, b2, b3), tol)
        return ReciprocalLattice(b1, b2, b3)

    def cell_parameters(self) -> dict:
        """Direct cell lengths and inter-axial angles."""
        return _cell_parameters(self.a1, self.a2, self.a3)

    def as_dict(self) -> dict:
        return {
            "a1": self.a1.tolist(),
            "a2": self.a2.tolist(),
            "a3": self.a3.tolist(),
            "cell_volume": self.cell_volume,
            "signed_volume": self.volume,
            "right_handed": self.is_right_handed,
            "cell_parameters": self.cell_parameters(),
            "measured_here": MEASURED_HERE,
        }


def _angle_deg(u: np.ndarray, v: np.ndarray) -> float:
    """The angle between two vectors, in degrees, clipped for safety."""
    nu = float(np.linalg.norm(u))
    nv = float(np.linalg.norm(v))
    if nu <= 0.0 or nv <= 0.0:
        raise ReciprocalError("a zero-length vector subtends no angle")
    cosine = float(np.dot(u, v)) / (nu * nv)
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def _cell_parameters(v1: np.ndarray, v2: np.ndarray,
                     v3: np.ndarray) -> dict:
    """Lengths and inter-axial angles of a three-vector basis."""
    return {
        "a": float(np.linalg.norm(v1)),
        "b": float(np.linalg.norm(v2)),
        "c": float(np.linalg.norm(v3)),
        "alpha_deg": _angle_deg(v2, v3),
        "beta_deg": _angle_deg(v3, v1),
        "gamma_deg": _angle_deg(v1, v2),
    }


def duality_identity(lattice: "DirectLattice | None" = None) -> dict:
    """The one exact identity this module rests on, reported.

    ``ai . bj = 2*pi*delta_ij`` holds for every lattice by construction,
    and ``V* = (2*pi)**3 / V`` follows from it. Both are stated here with
    their evaluated floating-point defects, so that "exact" means "exact
    in the algebra, and the arithmetic agrees to this many digits" rather
    than "close enough".
    """
    cell = ALPHA_QUARTZ_CELL if lattice is None else lattice
    if not isinstance(cell, DirectLattice):
        raise ReciprocalError("the duality identity needs a DirectLattice")
    dual = cell.reciprocal()
    matrix = duality_matrix(cell.vectors, dual.vectors)
    expected_reciprocal_volume = TWO_PI ** 3 / cell.volume
    volume_defect = abs(dual.volume - expected_reciprocal_volume) / abs(
        expected_reciprocal_volume)
    return {
        "identity": "ai . bj = 2*pi*delta_ij",
        "construction": ("b1 = 2*pi*(a2 x a3)/V, b2 = 2*pi*(a3 x a1)/V, "
                         "b3 = 2*pi*(a1 x a2)/V with V = a1 . (a2 x a3)"),
        "duality_matrix": matrix.tolist(),
        "two_pi": TWO_PI,
        "duality_defect_relative": duality_defect(cell.vectors,
                                                  dual.vectors),
        "duality_tolerance": DUALITY_TOL,
        "holds": duality_defect(cell.vectors, dual.vectors) <= DUALITY_TOL,
        "volume_identity": "V* = (2*pi)**3 / V",
        "direct_volume": cell.volume,
        "reciprocal_volume": dual.volume,
        "expected_reciprocal_volume": expected_reciprocal_volume,
        "volume_defect_relative": volume_defect,
        "claim_class": EXACT_IDENTITY,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "note": ("an identity about a pair of vector bases. It says "
                 "nothing about any crystal, and it is true of lattices "
                 "that no material realises"),
    }


# --- (2) alpha quartz, as a conventional literature cell -----------------

#: Alpha-quartz hexagonal cell edge, in angstroms. CONVENTIONAL_LITERATURE:
#: the room-temperature value quoted in standard crystallographic
#: references. Not measured here, and not a result of this repository.
QUARTZ_A_ANGSTROM = 4.913

#: Alpha-quartz hexagonal cell height, in angstroms. Same standing.
QUARTZ_C_ANGSTROM = 5.405

#: The hexagonal inter-axial angle, exactly 120 degrees by the setting.
QUARTZ_GAMMA_DEG = 120.0

#: The crystal class: trigonal 32 (D3), non-centrosymmetric, which is why
#: quartz is piezoelectric and optically active.
QUARTZ_CRYSTAL_CLASS = "32"
QUARTZ_CRYSTAL_SYSTEM = "trigonal"


class QuartzEnantiomorph(Enum):
    """The enantiomorphic pair of space groups. Quartz is chiral.

    ``P3121`` (No. 152) has a ``3_1`` screw axis along ``c`` and ``P3221``
    (No. 154) has a ``3_2``. They are mirror images: no rotation carries
    one into the other, and a crystal is one or the other, never both.

    Which structural handedness carries which *optical* handedness label
    is a convention that has been stated inconsistently in the
    literature, so this module records the space-group symbols and the
    screw sense and does **not** assert an optical-rotation sign for
    either member. Declaring the convention is the caller's job;
    inheriting it silently is how sign errors get published.
    """

    P3121 = "P3121"
    P3221 = "P3221"

    @property
    def space_group_number(self) -> int:
        return {"P3121": 152, "P3221": 154}[self.value]

    @property
    def screw_axis(self) -> str:
        return {"P3121": "3_1", "P3221": "3_2"}[self.value]

    @property
    def screw_translation(self) -> int:
        """The ``m`` of an ``n_m`` screw: 1 for ``3_1``, 2 for ``3_2``."""
        return {"P3121": 1, "P3221": 2}[self.value]

    def partner(self) -> "QuartzEnantiomorph":
        """The other member of the pair."""
        return (QuartzEnantiomorph.P3221 if self is QuartzEnantiomorph.P3121
                else QuartzEnantiomorph.P3121)


#: The pair, in space-group-number order.
QUARTZ_ENANTIOMORPHS: tuple[QuartzEnantiomorph, ...] = (
    QuartzEnantiomorph.P3121, QuartzEnantiomorph.P3221)


def hexagonal_direct_lattice(a: float = QUARTZ_A_ANGSTROM,
                             c: float = QUARTZ_C_ANGSTROM) -> DirectLattice:
    """A hexagonal cell with ``gamma = 120 deg``, in the standard setting.

        a1 = (a, 0, 0)
        a2 = (-a/2, a*sqrt(3)/2, 0)
        a3 = (0, 0, c)

    so that ``a1 . a2 = -a**2/2 = a**2 cos(120 deg)`` exactly and the
    cell volume is ``sqrt(3)/2 * a**2 * c``.
    """
    edge = _positive(a, "the hexagonal cell edge a")
    height = _positive(c, "the hexagonal cell height c")
    return DirectLattice(
        np.array([edge, 0.0, 0.0]),
        np.array([-0.5 * edge, 0.5 * math.sqrt(3.0) * edge, 0.0]),
        np.array([0.0, 0.0, height]),
    )


#: The alpha-quartz cell as a lattice object, built from the literature
#: constants above. Arithmetic on quoted numbers; nothing measured.
ALPHA_QUARTZ_CELL = hexagonal_direct_lattice()

#: Its dual, computed by the general construction.
ALPHA_QUARTZ_RECIPROCAL = ALPHA_QUARTZ_CELL.reciprocal()


def hexagonal_cell_volume(a: float = QUARTZ_A_ANGSTROM,
                          c: float = QUARTZ_C_ANGSTROM) -> float:
    """``V = sqrt(3)/2 * a**2 * c``, the closed form for ``gamma = 120``."""
    edge = _positive(a, "the hexagonal cell edge a")
    height = _positive(c, "the hexagonal cell height c")
    return 0.5 * math.sqrt(3.0) * edge * edge * height


def hexagonal_d_spacing(h: object, k: object, l: object,
                        a: float = QUARTZ_A_ANGSTROM,
                        c: float = QUARTZ_C_ANGSTROM) -> float:
    """The hexagonal d-spacing, from the closed form::

        1/d**2 = (4/3)*(h**2 + h*k + k**2)/a**2 + l**2/c**2

    This is an independent route to :meth:`ReciprocalLattice.d_spacing`
    for the same cell, and the two are required to agree. Two routes to
    one number is the only way a sign or a factor in either of them
    becomes visible.
    """
    i, j, m = _as_hkl(h, k, l)
    edge = _positive(a, "the hexagonal cell edge a")
    height = _positive(c, "the hexagonal cell height c")
    inverse_d_squared = ((4.0 / 3.0) * (i * i + i * j + j * j)
                         / (edge * edge) + (m * m) / (height * height))
    if inverse_d_squared <= 0.0:
        raise ReciprocalError(
            f"the reflection ({i}, {j}, {m}) gives a non-positive 1/d**2; "
            f"it names no plane family in this cell")
    return 1.0 / math.sqrt(inverse_d_squared)


def alpha_quartz_cell() -> dict:
    """The quartz cell, its dual, and its volume, with their standing."""
    cell = ALPHA_QUARTZ_CELL
    dual = ALPHA_QUARTZ_RECIPROCAL
    return {
        "crystal_system": QUARTZ_CRYSTAL_SYSTEM,
        "crystal_class": QUARTZ_CRYSTAL_CLASS,
        "space_groups": [e.value for e in QUARTZ_ENANTIOMORPHS],
        "space_group_numbers": [e.space_group_number
                                for e in QUARTZ_ENANTIOMORPHS],
        "screw_axes": {e.value: e.screw_axis for e in QUARTZ_ENANTIOMORPHS},
        "enantiomorphic_pair": True,
        "chiral": True,
        "centrosymmetric": False,
        "a_angstrom": QUARTZ_A_ANGSTROM,
        "b_angstrom": QUARTZ_A_ANGSTROM,
        "c_angstrom": QUARTZ_C_ANGSTROM,
        "gamma_deg": QUARTZ_GAMMA_DEG,
        "cell_volume_angstrom3": cell.cell_volume,
        "cell_volume_closed_form": hexagonal_cell_volume(),
        "direct": cell.as_dict(),
        "reciprocal": dual.as_dict(),
        "reciprocal_a_star_per_angstrom": float(np.linalg.norm(dual.b1)),
        "reciprocal_c_star_per_angstrom": float(np.linalg.norm(dual.b3)),
        "reciprocal_gamma_star_deg": _angle_deg(dual.b1, dual.b2),
        "closed_form_a_star": 4.0 * math.pi / (QUARTZ_A_ANGSTROM
                                               * math.sqrt(3.0)),
        "closed_form_c_star": TWO_PI / QUARTZ_C_ANGSTROM,
        "source_class": CONVENTIONAL_LITERATURE,
        "claim_class": SOURCE_ESTABLISHED_PHYSICS,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "note": ("the cell constants are conventional room-temperature "
                 "literature values, quoted; the reciprocal cell and the "
                 "volume are arithmetic on them. No specimen was "
                 "measured, indexed or refined here"),
    }


# --- (3) Laue and Bragg ---------------------------------------------------

def scattering_vector(k_in: object, k_out: object) -> np.ndarray:
    """``Q = k_out - k_in``, the momentum transfer divided by hbar.

    The sign convention is fixed here and used everywhere below: ``Q``
    points from the incident wavevector to the scattered one. The
    opposite convention appears in the literature and changes the sign of
    ``G`` in the Laue condition, which is why it is written down.
    """
    ki = _as_vector(k_in, "k_in")
    ko = _as_vector(k_out, "k_out")
    q = ko - ki
    q.setflags(write=False)
    return q


def wavevector_magnitude(wavelength: float) -> float:
    """``|k| = 2*pi/lambda``."""
    return TWO_PI / _positive(wavelength, "the wavelength")


def q_magnitude_from_theta(theta_rad: float, wavelength: float) -> float:
    """``|Q| = 4*pi*sin(theta)/lambda`` for elastic scattering.

    ``theta`` is the Bragg angle — half the scattering angle ``2*theta``.
    Confusing the two is the single most common error in this arithmetic
    and it is a factor of two in the answer, not a small one.
    """
    angle = _finite(theta_rad, "the Bragg angle theta in radians")
    return 4.0 * math.pi * math.sin(angle) / _positive(
        wavelength, "the wavelength")


def laue_condition_satisfied(q: object, g: object,
                             tol: float = 1e-9) -> bool:
    """Is ``Q == G``? The Laue condition, as a vector statement.

    Diffraction occurs when the scattering vector coincides with a
    reciprocal lattice vector. It is a condition on *three* components,
    not on a magnitude: two vectors of equal length pointing in different
    directions do not satisfy it, and a scalar comparison would let them
    through.
    """
    qv = _as_vector(q, "Q")
    gv = _as_vector(g, "G")
    scale = max(float(np.linalg.norm(gv)), float(np.linalg.norm(qv)), 1.0)
    return bool(float(np.linalg.norm(qv - gv))
                <= _positive(tol, "the Laue tolerance") * scale)


def bragg_angle_rad(d_spacing: float, wavelength: float,
                    order: int = 1) -> float:
    """Solve ``2*d*sin(theta) = n*lambda`` for ``theta``, in radians.

    Refuses the case ``n*lambda > 2*d``: there is no such reflection at
    that wavelength, and returning an angle from ``asin`` of something
    above one would be inventing one. That refusal is physics — it is why
    a long-wavelength source cannot reach short d-spacings at all.
    """
    d = _positive(d_spacing, "the d-spacing")
    lam = _positive(wavelength, "the wavelength")
    n = int(order)
    if n < 1:
        raise ReciprocalError("the Bragg order n must be a positive integer")
    sine = n * lam / (2.0 * d)
    if sine > 1.0:
        raise ReciprocalError(
            f"no order-{n} reflection exists for d = {d:g} at wavelength "
            f"{lam:g}: it would need sin(theta) = {sine:g} > 1. The "
            f"accessible condition is n*lambda <= 2*d, so this wavelength "
            f"cannot reach this d-spacing at any angle")
    return math.asin(sine)


def bragg_two_theta_deg(d_spacing: float, wavelength: float,
                        order: int = 1) -> float:
    """The scattering angle ``2*theta`` in degrees, which is what a
    diffractometer axis would read if one existed."""
    return 2.0 * math.degrees(bragg_angle_rad(d_spacing, wavelength, order))


def bragg_d_spacing(theta_rad: float, wavelength: float,
                    order: int = 1) -> float:
    """Invert Bragg's law: ``d = n*lambda/(2*sin(theta))``.

    The round trip ``theta -> d -> theta`` is the identity on
    ``(0, pi/2]``, which is the sense in which the two functions are
    inverses rather than merely related.
    """
    angle = _finite(theta_rad, "the Bragg angle theta in radians")
    lam = _positive(wavelength, "the wavelength")
    n = int(order)
    if n < 1:
        raise ReciprocalError("the Bragg order n must be a positive integer")
    sine = math.sin(angle)
    if sine <= 0.0:
        raise ReciprocalError(
            "a Bragg angle of zero (or less) has no d-spacing: the forward "
            "beam is not a reflection")
    return n * lam / (2.0 * sine)


def laue_is_bragg(h: object, k: object, l: object,
                  wavelength: float = 1.5406,
                  lattice: "DirectLattice | None" = None) -> dict:
    """Show that ``Q = G`` and ``2*d*sin(theta) = lambda`` are one statement.

    For the reflection ``(h, k, l)``: ``|G| = 2*pi/d`` by the definition
    of the dual basis, and ``|Q| = 4*pi*sin(theta)/lambda`` for elastic
    scattering. Setting them equal and cancelling ``2*pi`` gives
    ``2*d*sin(theta) = lambda`` with nothing left over. The Laue
    condition is the stronger of the two — it fixes the *direction* of
    ``Q`` as well as its length — and Bragg's law is what survives when
    only the magnitude is kept.

    The default wavelength, 1.5406 A, is the conventional Cu K-alpha1
    figure, quoted as literature and used here purely as an input number.
    """
    cell = ALPHA_QUARTZ_CELL if lattice is None else lattice
    if not isinstance(cell, DirectLattice):
        raise ReciprocalError("laue_is_bragg needs a DirectLattice")
    dual = cell.reciprocal()
    i, j, m = _as_hkl(h, k, l)
    d = dual.d_spacing(i, j, m)
    lam = _positive(wavelength, "the wavelength")
    theta = bragg_angle_rad(d, lam)
    g_magnitude = dual.g_magnitude(i, j, m)
    q_magnitude = q_magnitude_from_theta(theta, lam)
    return {
        "hkl": [i, j, m],
        "wavelength": lam,
        "d_spacing": d,
        "g_magnitude": g_magnitude,
        "q_magnitude": q_magnitude,
        "g_equals_two_pi_over_d": abs(g_magnitude - TWO_PI / d) <= 1e-12 * (
            TWO_PI / d),
        "magnitudes_agree": abs(q_magnitude - g_magnitude) <= 1e-12 * max(
            g_magnitude, 1.0),
        "theta_rad": theta,
        "theta_deg": math.degrees(theta),
        "two_theta_deg": 2.0 * math.degrees(theta),
        "bragg_residual": abs(2.0 * d * math.sin(theta) - lam),
        "derivation": ("|Q| = |G|  <=>  4*pi*sin(theta)/lambda = 2*pi/d  "
                       "<=>  2*d*sin(theta) = lambda"),
        "laue_is_stronger_than_bragg": (
            "the Laue condition fixes all three components of Q; Bragg's "
            "law keeps only its magnitude, so a Bragg angle alone does "
            "not orient a crystal"),
        "claim_class": SOURCE_ESTABLISHED_PHYSICS,
        "measured_here": MEASURED_HERE,
    }


# --- (4) structure factors and systematic absences ------------------------

@dataclass(frozen=True)
class Atom:
    """One scatterer at a fractional coordinate in the cell.

    ``scattering_factor`` is a single real constant per atom. That is a
    deliberate simplification and it is stated rather than hidden: a real
    atomic form factor falls off with ``sin(theta)/lambda`` and picks up
    an anomalous complex part near an absorption edge, neither of which
    is modelled here. Systematic absences do not depend on either, since
    they come from the *phase* sum vanishing, which is why this
    simplification is safe for exactly the use it is put to.
    """

    label: str
    x: float
    y: float
    z: float
    scattering_factor: float = 1.0

    def __post_init__(self) -> None:
        if not str(self.label).strip():
            raise ReciprocalError("an atom needs a non-empty label")
        for name in ("x", "y", "z"):
            object.__setattr__(self, name,
                               _finite(getattr(self, name),
                                       f"the fractional coordinate {name}"))
        f = _finite(self.scattering_factor, "the scattering factor")
        if f <= 0.0:
            raise ReciprocalError(
                "a scattering factor must be positive; an atom that "
                "scatters nothing is not in the structure")
        object.__setattr__(self, "scattering_factor", f)

    @property
    def fractional(self) -> tuple[float, float, float]:
        return (self.x, self.y, self.z)

    def as_dict(self) -> dict:
        return {
            "label": self.label,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "scattering_factor": self.scattering_factor,
        }


def _as_atoms(atoms: object) -> tuple[Atom, ...]:
    try:
        items = tuple(atoms)                          # type: ignore[arg-type]
    except TypeError:
        raise ReciprocalError(
            f"cannot read {atoms!r} as a list of atoms") from None
    if not items:
        raise ReciprocalError(
            "an empty atom list has no structure factor; a cell with no "
            "scatterers in it diffracts nothing")
    for a in items:
        if not isinstance(a, Atom):
            raise ReciprocalError(f"{a!r} is not an Atom")
    return items                                      # type: ignore[return-value]


def structure_factor(atoms: object, h: object, k: object,
                     l: object) -> complex:
    """``F(hkl) = sum_j f_j * exp(2*pi*i*(h*x_j + k*y_j + l*z_j))``.

    Generic over the atom list: no symmetry is assumed, nothing is folded
    in, and the sum is taken exactly as written. Everything the module
    says about extinctions is then a *consequence* of the coordinates it
    is handed, not a rule applied on top of them.
    """
    items = _as_atoms(atoms)
    i, j, m = _as_hkl(h, k, l)
    total = 0.0 + 0.0j
    for atom in items:
        phase = TWO_PI * (i * atom.x + j * atom.y + m * atom.z)
        total += atom.scattering_factor * complex(math.cos(phase),
                                                  math.sin(phase))
    return total


def structure_factor_intensity(atoms: object, h: object, k: object,
                               l: object) -> float:
    """``|F(hkl)|**2``, the quantity a detector would be proportional to.

    "Would be": no detector exists here, and
    :func:`refuse_measured_pattern_claim` refuses any reading of this
    number as a collected intensity.
    """
    f = structure_factor(atoms, h, k, l)
    return float(abs(f) ** 2)


def total_scattering_power(atoms: object) -> float:
    """``sum_j f_j``: the largest ``|F|`` any reflection could have."""
    return float(sum(a.scattering_factor for a in _as_atoms(atoms)))


def is_systematically_absent(atoms: object, h: object, k: object, l: object,
                             tol: float = ABSENCE_TOL) -> bool:
    """Is ``F(hkl)`` zero to within ``tol`` of the total scattering power?

    Scaling the threshold by ``sum_j f_j`` is what makes this a statement
    about cancellation rather than about units: an absence is a phase sum
    that vanishes, however strongly the individual atoms scatter.
    """
    magnitude = abs(structure_factor(atoms, h, k, l))
    return bool(magnitude <= _positive(tol, "the absence tolerance")
                * total_scattering_power(atoms))


def systematic_absences(atoms: object, reflections: object,
                        tol: float = ABSENCE_TOL) -> tuple:
    """Which of the given reflections are extinct, in the order supplied."""
    out = []
    for reflection in reflections:                    # type: ignore[union-attr]
        i, j, m = _as_hkl(*tuple(reflection))
        if is_systematically_absent(atoms, i, j, m, tol):
            out.append((i, j, m))
    return tuple(out)


#: The rotation part of an ``n``-fold axis along ``c``, in fractional
#: coordinates of a hexagonal cell. The three-fold is *not* a Cartesian
#: rotation matrix: in the hexagonal basis it is the integer matrix
#: ``(x, y) -> (-y, x - y)``, which is what makes the orbit close exactly.
_ROTATION_ABOUT_C: dict[int, tuple[tuple[int, int], tuple[int, int]]] = {
    2: ((-1, 0), (0, -1)),
    3: ((0, -1), (1, -1)),
}


def screw_axis_orbit(atom: Atom, fold: int = 3,
                     translation: int = 1) -> tuple[Atom, ...]:
    """The orbit of one atom under an ``n_m`` screw axis along ``c``.

    A screw axis is a rotation by ``2*pi/n`` about ``c`` combined with a
    translation of ``m/n`` along it, and applying it ``n`` times returns
    the atom to itself modulo a lattice vector. For ``3_1`` the orbit is

        (x, y, z),  (-y, x-y, z+1/3),  (-x+y, -x, z+2/3)

    and for ``2_1`` it is ``(x, y, z), (-x, -y, z+1/2)``. Nothing about
    diffraction is used to build it: it is the symmetry operation applied
    to a coordinate, and the extinctions in
    :func:`screw_axis_absence_rule` follow from it by arithmetic.
    """
    if not isinstance(atom, Atom):
        raise ReciprocalError("a screw-axis orbit needs an Atom")
    n = int(fold)
    m = int(translation)
    if n not in _ROTATION_ABOUT_C:
        raise ReciprocalError(
            f"only {sorted(_ROTATION_ABOUT_C)}-fold screw axes along c are "
            f"implemented here; {n!r} is not one of them")
    if not 1 <= m < n:
        raise ReciprocalError(
            f"an n_m screw axis needs 1 <= m < n; got n = {n}, m = {m}. "
            f"m = 0 is a pure rotation and produces no extinctions")
    (r00, r01), (r10, r11) = _ROTATION_ABOUT_C[n]
    out = [atom]
    x, y = atom.x, atom.y
    for step in range(1, n):
        x, y = r00 * x + r01 * y, r10 * x + r11 * y
        out.append(Atom(f"{atom.label}_{n}{m}_{step}", x, y,
                        atom.z + step * m / n, atom.scattering_factor))
    return tuple(out)


def screw_axis_absence_rule(fold: int = 3, translation: int = 1) -> str:
    """The ``00l`` extinction rule an ``n_m`` screw along ``c`` produces."""
    n, m = int(fold), int(translation)
    if not 1 <= m < n:
        raise ReciprocalError("an n_m screw axis needs 1 <= m < n")
    step = math.gcd(m, n)
    period = n // step
    return (f"{n}_{m} along c: 00l present only for l = {period}p "
            f"(l a multiple of {period}); all other 00l are "
            f"systematically absent")


def screw_axis_extinctions(fold: int = 3, translation: int = 1,
                           l_max: int = 12,
                           base: "Atom | None" = None) -> dict:
    """Compute the ``00l`` extinctions of a planted screw axis.

    This is the POWER demonstration of the structure-factor code: an
    orbit is generated from the symmetry operation alone, the generic
    ``F(hkl)`` sum is evaluated over ``00l``, and the surviving
    reflections are exactly the multiples of ``n/gcd(m, n)``. Nothing
    tells the sum which reflections ought to vanish; they vanish because
    the phases cancel.
    """
    n, m = int(fold), int(translation)
    seed = Atom("A", 0.47, 0.0, 0.0) if base is None else base
    orbit = screw_axis_orbit(seed, n, m)
    limit = int(l_max)
    if limit < 1:
        raise ReciprocalError("l_max must be at least 1")
    period = n // math.gcd(m, n)
    present, absent = [], []
    for l in range(1, limit + 1):
        (absent if is_systematically_absent(orbit, 0, 0, l)
         else present).append(l)
    return {
        "screw_axis": f"{n}_{m}",
        "orbit": [a.as_dict() for a in orbit],
        "orbit_size": len(orbit),
        "expected_period": period,
        "rule": screw_axis_absence_rule(n, m),
        "l_present": present,
        "l_absent": absent,
        "l_present_are_multiples_of_period": all(
            l % period == 0 for l in present),
        "l_absent_are_not_multiples_of_period": all(
            l % period != 0 for l in absent),
        "matches_rule": (present == [l for l in range(1, limit + 1)
                                     if l % period == 0]),
        "claim_class": REPOSITORY_COMPUTATIONAL_RESULT,
        "measured_here": MEASURED_HERE,
        "note": ("the extinctions are computed from the generic structure "
                 "factor over an orbit generated by the symmetry "
                 "operation; no extinction rule is applied by hand"),
    }


# --- (5) the firewall -----------------------------------------------------

def refuse_reciprocal_as_physical_space(
        point: object = None,
        claim: str = "a reciprocal lattice point is a location") -> None:
    """A reciprocal lattice point is not a place. This ALWAYS raises.

    Reciprocal space is the *mathematical dual* of the direct lattice: a
    Fourier-conjugate index space in which the point ``(h, k, l)`` labels
    the family of lattice planes with spacing ``d_hkl``. Its coordinates
    have units of inverse length; its origin is the forward beam; its
    "points" are indices, and there are infinitely many of them for a
    finite crystal. A "reciprocal address" is not an address: nothing can
    be at ``(2, 1, 3)`` because ``(2, 1, 3)`` is not somewhere.
    """
    named = f" ({point!r})" if point is not None else ""
    raise ReciprocalError(
        f"refused: {claim!r}{named}. A reciprocal lattice point is an "
        f"INDEX TRIPLE (h, k, l) in the Fourier dual of the direct "
        f"lattice, labelling a family of parallel lattice planes with "
        f"spacing d_hkl = 2*pi/|G_hkl|. Its coordinates carry units of "
        f"INVERSE LENGTH, so they are not positions and cannot be "
        f"converted into positions; the dual basis is a basis for a "
        f"function space, not for a region anyone can occupy. Nothing "
        f"travels to a reciprocal lattice point, nothing is located at "
        f"one, and a 'reciprocal address' names a plane family in one "
        f"crystal rather than a place. The direct lattice is where the "
        f"atoms are. {VERDICT}")


def refuse_qspace_as_geographic(
        q: object = None,
        claim: str = "a Q-space coordinate is a geographic position"
) -> None:
    """Q-space is per-crystal and per-orientation. This ALWAYS raises.

    ``Q = k_out - k_in`` is defined relative to a particular incident
    beam and a particular crystal in a particular orientation on its
    mount. Rotate the specimen and every Q-space coordinate changes while
    nothing about the crystal or the planet does. There is no shared
    origin, no shared scale, no shared axes and no shared units between
    Q-space and any geographic frame — one is in inverse angstroms and
    the other in degrees of arc on a specific ellipsoid — so no
    transformation between them exists to be got right or wrong.
    """
    named = f" ({q!r})" if q is not None else ""
    raise ReciprocalError(
        f"refused: {claim!r}{named}. Q-space coordinates are defined by "
        f"Q = k_out - k_in for ONE crystal in ONE orientation relative to "
        f"ONE incident beam: remount the specimen, rotate it, or change "
        f"the wavelength and every Q coordinate changes while the crystal "
        f"and the planet are untouched. Q has units of inverse length and "
        f"a geographic coordinate has units of angle on a declared "
        f"ellipsoid; they share no origin, no scale, no axes and no "
        f"units, so there is no mapping between them to calibrate. A "
        f"Q-space coordinate is not a latitude, a longitude, a bearing, a "
        f"site or a distance, and reading one as any of those is a "
        f"category error rather than an error of precision. {VERDICT}")


def refuse_measured_pattern_claim(
        claim: str = "a diffraction pattern was measured",
        reflection: object = None) -> None:
    """No diffraction pattern was measured here. This ALWAYS raises.

    There is no source, no monochromator, no goniometer, no detector and
    no specimen in this repository. Every intensity here is
    ``|F(hkl)|**2`` evaluated on a declared atom list, with a constant
    scattering factor per atom, no thermal (Debye-Waller) factor, no
    absorption, no extinction, no Lorentz-polarization correction, no
    multiplicity and no background. A computed structure-factor magnitude
    is not a peak, and a list of computed absences is not an indexed
    pattern.
    """
    named = ""
    if reflection is not None:
        named = f" for {reflection!r}"
    raise ReciprocalError(
        f"refused: {claim!r}{named} is a {BENCH_MEASUREMENT} claim and no "
        f"diffractometer exists here. There is no X-ray or neutron "
        f"source, no monochromator, no goniometer, no detector and no "
        f"specimen in this repository, and nothing has been mounted, "
        f"aligned, exposed, scanned or indexed. What this module computes "
        f"is |F(hkl)|**2 on a declared atom list with a constant "
        f"scattering factor per atom and with NO Debye-Waller factor, no "
        f"absorption, no extinction, no Lorentz-polarization correction, "
        f"no multiplicity, no instrumental profile and no background — so "
        f"even as a simulation it is not a predicted powder pattern. "
        f"{VERDICT}")


# --- (6) report ------------------------------------------------------------

def reciprocal_report() -> dict:
    """The standing statement of what this module is and is not."""
    cell = ALPHA_QUARTZ_CELL
    dual = ALPHA_QUARTZ_RECIPROCAL
    quartz_101 = hexagonal_d_spacing(1, 0, 1)
    return {
        "what_this_is": (
            "a reciprocal-space crystal and scattering model: the dual "
            "lattice construction with its defining identity, the alpha "
            "quartz cell from conventional literature, the Laue condition "
            "and Bragg's law shown to be one statement, and a generic "
            "structure factor whose systematic absences follow from "
            "planted screw symmetry"),
        "exact_identity": duality_identity(),
        "alpha_quartz": alpha_quartz_cell(),
        "d_spacings_angstrom": {
            "100": hexagonal_d_spacing(1, 0, 0),
            "101": quartz_101,
            "110": hexagonal_d_spacing(1, 1, 0),
            "002": hexagonal_d_spacing(0, 0, 2),
        },
        "d_spacing_routes_agree": bool(
            abs(dual.d_spacing(1, 0, 1) - quartz_101) <= 1e-12 * quartz_101),
        "laue_and_bragg": laue_is_bragg(1, 0, 1),
        "screw_axis_extinctions": {
            "3_1": screw_axis_extinctions(3, 1),
            "3_2": screw_axis_extinctions(3, 2),
            "2_1": screw_axis_extinctions(2, 1),
        },
        "cell_volume_angstrom3": cell.cell_volume,
        "refusals": [
            "refuse_reciprocal_as_physical_space",
            "refuse_qspace_as_geographic",
            "refuse_measured_pattern_claim",
        ],
        "firewalls": [
            "the reciprocal lattice is the Fourier dual of the direct "
            "lattice, with units of inverse length; a point in it is an "
            "index triple labelling a plane family, not a place, and a "
            "'reciprocal address' is not a location",
            "Q-space is defined per crystal, per orientation and per "
            "incident beam; it shares no origin, scale, axes or units "
            "with any geographic frame, so no Q coordinate is a "
            "planetary coordinate",
            "no diffraction pattern has been collected here, and a "
            "computed |F|**2 with no Debye-Waller, absorption, "
            "Lorentz-polarization or background term is not even a "
            "predicted pattern",
            "Miller indices are integers; a non-integer triple names no "
            "plane family",
            "the Laue condition constrains three components of Q while "
            "Bragg's law keeps only the magnitude, so a Bragg angle does "
            "not orient a crystal",
        ],
        "hardware_status": (
            "DEFERRED - no source, monochromator, goniometer, detector or "
            "specimen exists here"),
        "claim_class": CLAIM_CLASS,
        "claim_classes": list(CLAIM_CLASSES),
        "evidence_class": EVIDENCE_CLASS,
        "source_class": CONVENTIONAL_LITERATURE,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "what_would_change_this": (
            "nothing in this module needs changing: it is standard "
            "crystallography and it is claimed as standard "
            "crystallography. What a bench would add is a different "
            "thing entirely — a mounted specimen, a calibrated "
            "wavelength, an indexed pattern with its own uncertainties, "
            "and refined cell constants that could be compared against "
            "the literature values quoted here"),
        "what_this_does_not_say": (
            "It does not say anything new. The reciprocal lattice, the "
            "Laue condition, Bragg's law, the hexagonal d-spacing formula "
            "and the structure factor are established crystallography, "
            "reimplemented here and claimed as nothing more. It does not "
            "say any crystal was grown, cut, mounted, illuminated or "
            "measured: there is no source, no goniometer and no detector "
            "in this repository, and every intensity is |F|**2 on a "
            "declared atom list with a constant scattering factor and no "
            "Debye-Waller, absorption, extinction, "
            "Lorentz-polarization, multiplicity or background term. The "
            "alpha-quartz cell constants are conventional literature "
            "values quoted as such, not a refinement performed here, and "
            "the reciprocal cell and volume are arithmetic on them. It "
            "does not say a reciprocal lattice point is a place, that a "
            "'reciprocal address' locates anything, or that a Q-space "
            "coordinate corresponds to a position on any planet — "
            "reciprocal space is a mathematical dual in units of inverse "
            "length, defined per crystal and per orientation, and it has "
            "no geographic content whatsoever."),
        "verdict": VERDICT,
    }


__all__ = [
    "VERDICT", "CLAIM_CLASS", "CLAIM_CLASSES", "EXACT_IDENTITY",
    "SOURCE_ESTABLISHED_PHYSICS", "REPOSITORY_COMPUTATIONAL_RESULT",
    "BENCH_MEASUREMENT", "CONVENTIONAL_LITERATURE", "EVIDENCE_CLASS",
    "MEASURED_HERE", "PHYSICAL_VALIDATION", "DUALITY_TOL", "ABSENCE_TOL",
    "TWO_PI", "ReciprocalError",
    "reciprocal_vectors", "duality_matrix", "duality_defect",
    "check_duality", "duality_identity",
    "DirectLattice", "ReciprocalLattice",
    "QUARTZ_A_ANGSTROM", "QUARTZ_C_ANGSTROM", "QUARTZ_GAMMA_DEG",
    "QUARTZ_CRYSTAL_CLASS", "QUARTZ_CRYSTAL_SYSTEM",
    "QuartzEnantiomorph", "QUARTZ_ENANTIOMORPHS",
    "hexagonal_direct_lattice", "hexagonal_cell_volume",
    "hexagonal_d_spacing", "ALPHA_QUARTZ_CELL", "ALPHA_QUARTZ_RECIPROCAL",
    "alpha_quartz_cell",
    "scattering_vector", "wavevector_magnitude", "q_magnitude_from_theta",
    "laue_condition_satisfied", "bragg_angle_rad", "bragg_two_theta_deg",
    "bragg_d_spacing", "laue_is_bragg",
    "Atom", "structure_factor", "structure_factor_intensity",
    "total_scattering_power", "is_systematically_absent",
    "systematic_absences", "screw_axis_orbit", "screw_axis_absence_rule",
    "screw_axis_extinctions",
    "refuse_reciprocal_as_physical_space", "refuse_qspace_as_geographic",
    "refuse_measured_pattern_claim",
    "reciprocal_report",
]
