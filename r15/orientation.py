"""P05 — a low-cost specimen-orientation solver, without assuming XRD.

Fixing the crystallographic orientation of a specimen is usually the job of
single-crystal X-ray diffraction: a Laue back-reflection or an indexed
four-circle run reads the lattice directly. R15's specimen authority must
work for an operator who does *not* own that instrument. This module builds
the strongest orientation workflow that a cheap, accessible bench can
support -- an optical goniometer, a pair of crossed polarizers, a phone
camera on a rotating stage -- and it is scrupulous about the three things
that bench can never recover.

**A synthetic forward model, then an inverse solver (POWER).** An
orientation of a uniaxial trigonal crystal (alpha-quartz) is written as a
rotation of the crystal frame into the lab frame, carrying the c-axis (the
optic axis), the a-axis azimuth about it, and -- separately -- the
handedness. :func:`forward_observation` maps that orientation to three cheap
observables: the extinction azimuth between crossed polarizers, the
optic-axis tilt from a conoscopic figure, and the set of rhombohedral facet
normals from goniometry. :func:`solve_orientation` inverts synthetic
observations back to the planted orientation, within a stated error budget.
That is POWER: a planted orientation is recovered from cheap data alone.

**The intrinsic ambiguities are surfaced, never hidden.** The point group
of alpha-quartz is ``32`` (``D_3``); its six proper rotations (reused from
:mod:`r13.crystalframe`) map any solved orientation onto five others that
produce *identical* observations -- a symmetry alias set, exactly the alias
idea of :mod:`r13.magroot`. Among those six, the three two-folds send the
c-axis to its negative: the optic axis is an undirected *line*, so ``+c``
and ``-c`` are indistinguishable and the 180-degree ambiguity is explicit.
:func:`refuse_orientation_as_unique` refuses to collapse the alias set.

**Handedness and c-axis polarity are not recoverable here.** Every cheap
observable in this module is achiral and unsigned: linear birefringence,
face angles and an optic-axis tilt are the same for the right-handed
``P3_121`` crystal and its left-handed ``P3_221`` enantiomorph, and the same
for ``+c`` and ``-c``. Handedness is therefore returned as ``UNDETERMINED``;
:func:`refuse_handedness_from_geometry` and
:func:`refuse_optic_axis_polarity` raise. An orientation certificate issued
without diffraction is capped below a diffraction-confirmed one, and
:func:`additional_evidence_to_upgrade` states exactly which physical
acquisitions would lift each cap -- every one of them PREREGISTERED_NOT_RUN.

Nothing here is measured. The observations are deterministic simulator
output (``SYNTHETIC_OBSERVATION``); the recovered orientation is a
``MODEL_PREDICTION``. No goniometer is read, no polarizer is turned, no
specimen is mounted. The standing verdict is
``LOW_COST_ORIENTATION_ALIAS_LIMITED_NO_XRD``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from r13.crystalframe import QUARTZ_FRAME
from r13.magroot import rotation_about_axis, shortest_arc_rotation
from r15 import claims

# --- verdict, claim vocabulary ------------------------------------------

VERDICT = "LOW_COST_ORIENTATION_ALIAS_LIMITED_NO_XRD"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: The recovered orientation is a model prediction; the synthetic
#: observations it is fitted to are synthetic observations. Neither is a
#: measurement, and no bench read here supports a physical class.
RECOVERY_CLAIM_CLASS = claims.ClaimClass.MODEL_PREDICTION.value
OBSERVATION_CLAIM_CLASS = claims.ClaimClass.SYNTHETIC_OBSERVATION.value

#: The uniaxial material whose frame and symmetry this solver reuses.
MATERIAL = "alpha-quartz (trigonal, point group 32, P3_121 / P3_221)"

#: Named intrinsic ambiguities, surfaced rather than resolved.
OPTIC_AXIS_LINE_AMBIGUITY = "OPTIC_AXIS_IS_A_LINE_C_SIGN_UNDETERMINED"
SYMMETRY_ALIAS_AMBIGUITY = "POINT_GROUP_32_SYMMETRY_ALIAS_SET"
HANDEDNESS_AMBIGUITY = "ENANTIOMORPH_UNDETERMINED_ACHIRAL_OBSERVATIONS"

_TOL = 1e-9
_Z = np.array([0.0, 0.0, 1.0])
_X = np.array([1.0, 0.0, 0.0])
_Y = np.array([0.0, 1.0, 0.0])


class OrientationError(RuntimeError):
    """Raised when the orientation solver is asked to over-claim: a unique
    orientation from a symmetry-aliased fit, a signed c-axis or a handedness
    from achiral observations, an XRD-confirmed certificate without XRD, or a
    fit whose residual exceeds the stated error budget."""


class Handedness(Enum):
    """The enantiomorph label. It is discrete and, crucially, *not*
    recoverable from any observation in this module."""

    RIGHT = "P3_121"
    LEFT = "P3_221"
    UNDETERMINED = "UNDETERMINED"


class EvidenceType(Enum):
    """The cheap evidence kinds this solver consumes, plus the certificate
    it emits. No diffraction kind appears: XRD is out of scope by design."""

    POLARIZATION = "POLARIZATION"
    EXTINCTION = "EXTINCTION"
    CONOSCOPIC = "CONOSCOPIC"
    GEOMETRY = "GEOMETRY"
    CERTIFICATE = "CERTIFICATE"


class AcquisitionMode(Enum):
    """The four acquisition modes kept strictly distinct. Only ``REAL``
    could ever produce a measurement, and it is not available here."""

    SYNTHETIC = "SYNTHETIC"
    REPLAY = "REPLAY"
    REAL = "REAL"
    FAULT_INJECTION = "FAULT_INJECTION"


class ConfidenceLevel(Enum):
    """The orientation-certificate confidence ladder. Everything at or below
    ``PRESUMPTIVE`` is reachable from the cheap bench; the two confirmed
    levels require diffraction and are unreachable here."""

    HYPOTHESIS = 0
    SCREENING = 1
    PRESUMPTIVE = 2
    XRD_CONFIRMED = 3
    XRD_REPLICATED = 4


#: A no-diffraction certificate is capped here, no matter how clean the fit.
NO_XRD_CONFIDENCE_CAP = ConfidenceLevel.PRESUMPTIVE


def cap_confidence_without_xrd(requested: ConfidenceLevel) -> ConfidenceLevel:
    """Cap a requested confidence to what a diffraction-free bench supports.

    A clean optical fit is presumptive, never confirmed: the symmetry alias
    set, the c-axis sign and the handedness all remain open without
    diffraction, so the certificate may not claim an XRD-confirmed level.
    """
    if requested.value > NO_XRD_CONFIDENCE_CAP.value:
        return NO_XRD_CONFIDENCE_CAP
    return requested


# --- small vector helpers -----------------------------------------------

def _unit(v) -> np.ndarray:
    a = np.asarray(v, dtype=float)
    if a.shape != (3,):
        raise OrientationError("a direction must be a 3-vector")
    n = float(np.linalg.norm(a))
    if n < _TOL:
        raise OrientationError("a zero vector has no direction")
    return a / n


def _vec(v) -> tuple[float, float, float]:
    a = np.asarray(v, dtype=float)
    return (float(a[0]), float(a[1]), float(a[2]))


def _c_frame(c_axis) -> tuple[np.ndarray, np.ndarray]:
    """An orthonormal (e1, e2) basis of the plane perpendicular to ``c``.

    Built by carrying the lab x, y through the shortest-arc rotation that
    aligns the lab z with ``c``. Reused for both azimuth read-out and
    azimuth synthesis so the two are exact inverses.
    """
    c = _unit(c_axis)
    A = shortest_arc_rotation(_Z, c)
    return A @ _X, A @ _Y


def azimuth_about_c(v, c_axis) -> float:
    """Azimuth of ``v`` about the c-axis, in degrees, in the (e1, e2) frame."""
    e1, e2 = _c_frame(c_axis)
    a = np.asarray(v, dtype=float)
    return math.degrees(math.atan2(float(a @ e2), float(a @ e1)))


def angle_between(u, v) -> float:
    """Unsigned angle between two vectors, in degrees."""
    a, b = _unit(u), _unit(v)
    return math.degrees(math.acos(max(-1.0, min(1.0, float(a @ b)))))


def line_angle(u, v) -> float:
    """Angle between two undirected lines: ``u`` and ``-u`` are identified."""
    a, b = _unit(u), _unit(v)
    return math.degrees(math.acos(min(1.0, abs(float(a @ b)))))


def _direction_from_c(c_axis, polar_deg: float, azimuth_deg: float
                      ) -> np.ndarray:
    """A unit vector at ``polar_deg`` from ``c`` and ``azimuth_deg`` about it."""
    c = _unit(c_axis)
    e1, e2 = _c_frame(c)
    p = math.radians(polar_deg)
    az = math.radians(azimuth_deg)
    return (math.cos(p) * c
            + math.sin(p) * (math.cos(az) * e1 + math.sin(az) * e2))


#: The crystal-frame normal of a rhombohedral {10-1-1}-type face, taken from
#: the reciprocal frame of alpha-quartz (r13.crystalframe). It is tilted off
#: the c-axis, so its full point-group-32 orbit is a pair of cones symmetric
#: about the c-*line* -- the geometric fact the solver uses to recover the
#: c-axis as the orbit's symmetry axis (an eigenvector), sign-free.
_GEN_FACE_NORMAL_CRYSTAL = _unit(QUARTZ_FRAME.reciprocal_vector(1, 0, 1))

#: The number of rhombohedral facets observed by goniometry: the full
#: point-group-32 orbit of the generating face (positive and negative
#: rhombohedra), a set invariant under the c-line symmetry.
N_FACETS = 6


# --- the orientation state ----------------------------------------------

@dataclass(frozen=True)
class OrientationState:
    """A specimen orientation, with every degree of freedom carried apart.

    ``c_axis`` is the trigonal / optic axis direction in the lab frame;
    ``a_azimuth_deg`` is the azimuth of the a-axis about it; ``handedness``
    is the enantiomorph label, held separately because no observation here
    constrains it. The optic axis, the a-axis and the facet normals are
    derived, not stored, so they can never drift out of sync with the frame.
    """

    c_axis: tuple[float, float, float]
    a_azimuth_deg: float
    handedness: Handedness = Handedness.UNDETERMINED
    material: str = MATERIAL

    def __post_init__(self) -> None:
        object.__setattr__(self, "c_axis", _vec(_unit(self.c_axis)))
        object.__setattr__(self, "a_azimuth_deg",
                           float(self.a_azimuth_deg) % 360.0)

    # -- derived directions ------------------------------------------------

    def optic_axis(self) -> tuple[float, float, float]:
        """The optic axis. For uniaxial alpha-quartz this *is* the c-axis --
        and it is an undirected line, so its sign is not physical."""
        return self.c_axis

    def rotation(self) -> np.ndarray:
        """The crystal->lab rotation that realises this orientation.

        ``R = align_z_to(c) @ Rz(a_azimuth)``. Exact inverse of
        :meth:`from_rotation`: ``R @ z == c`` and the a-axis azimuth is
        ``a_azimuth_deg``.
        """
        A = shortest_arc_rotation(_Z, np.asarray(self.c_axis, dtype=float))
        return A @ rotation_about_axis(_Z, math.radians(self.a_azimuth_deg))

    def a_axis(self) -> tuple[float, float, float]:
        """The a-axis direction in the lab frame."""
        return _vec(self.rotation() @ _X)

    def facet_normals(self) -> list[tuple[float, float, float]]:
        """The lab-frame normals of the observed rhombohedral facets.

        The six faces are the full point-group-32 orbit (all six proper
        rotations, reused from
        :meth:`r13.crystalframe.LatticeFrame.symmetry_operators`) of the
        generating crystal-frame face normal, carried into the lab by the
        orientation. Because the orbit is closed under the group, the set is
        invariant under every symmetry alias -- and under the c-line
        symmetry, so it fixes the c-axis only as an undirected line.
        """
        R = self.rotation()
        ops = QUARTZ_FRAME.symmetry_operators()  # all six proper rotations
        return [_vec(R @ (S @ _GEN_FACE_NORMAL_CRYSTAL)) for S in ops]

    @classmethod
    def from_rotation(cls, R: np.ndarray,
                      handedness: Handedness = Handedness.UNDETERMINED
                      ) -> "OrientationState":
        """Recover the (c-axis, a-azimuth) parameters of a proper rotation."""
        M = np.asarray(R, dtype=float)
        if M.shape != (3, 3):
            raise OrientationError("a rotation must be a 3x3 matrix")
        c = M @ _Z
        az = azimuth_about_c(M @ _X, c)
        return cls(_vec(c), az, handedness)


# --- the error budget ----------------------------------------------------

#: Standard (1-sigma) angular uncertainties of the cheap instruments, in
#: degrees. Declared engineering values for the bench, not measured here.
_COMPONENT_SIGMAS_DEG = {
    "goniometer_facet_angle": 0.5,
    "polarizer_extinction_angle": 1.0,
    "conoscopic_tilt_angle": 1.5,
}

#: Coverage factor for the expanded uncertainty (k=2, ~95%).
COVERAGE_FACTOR = 2.0


def build_error_budget(budget_id: str = "P05_orientation_angle") -> dict:
    """The orientation error budget, conforming to ``error_budget.schema``.

    Components combine in quadrature (root-sum-of-squares of independent
    angular contributions); the expanded uncertainty is ``k`` times the
    combined standard uncertainty.
    """
    components = [
        {"name": name, "type": "B", "distribution": "normal",
         "standard_uncertainty_deg": sigma}
        for name, sigma in _COMPONENT_SIGMAS_DEG.items()
    ]
    combined = math.sqrt(sum(s * s for s in _COMPONENT_SIGMAS_DEG.values()))
    return {
        "budget_id": budget_id,
        "quantity": "specimen_orientation_angle_deg",
        "components": components,
        "combination_method": "root_sum_of_squares",
        "combined_uncertainty": combined,
        "coverage_factor": COVERAGE_FACTOR,
    }


def expanded_uncertainty_deg(budget: dict | None = None) -> float:
    """The expanded (k-times) angular uncertainty of the budget, in degrees."""
    b = budget if budget is not None else build_error_budget()
    return float(b["combined_uncertainty"]) * float(b["coverage_factor"])


# --- typed evidence records ---------------------------------------------

@dataclass(frozen=True)
class EvidenceRecord:
    """One typed piece of cheap evidence, tagged with its acquisition mode,
    the quantity it constrains, its value and 1-sigma uncertainty, and what
    it *cannot* constrain."""

    evidence_type: EvidenceType
    mode: AcquisitionMode
    quantity: str
    value: object
    sigma_deg: float
    constrains: str
    does_not_constrain: str

    def to_dict(self) -> dict:
        return {
            "evidence_type": self.evidence_type.value,
            "mode": self.mode.value,
            "quantity": self.quantity,
            "value": self.value,
            "sigma_deg": self.sigma_deg,
            "constrains": self.constrains,
            "does_not_constrain": self.does_not_constrain,
        }


@dataclass(frozen=True)
class OrientationObservation:
    """A deterministic synthetic dataset from the cheap bench.

    Carries the polarizer extinction azimuth (mod 90 degrees), the
    conoscopic optic-axis tilt, and the goniometric facet normals, along
    with the typed evidence records and the acquisition mode. Nothing here
    is a measurement; it is simulator output.
    """

    extinction_azimuth_deg: float
    optic_axis_tilt_deg: float
    facet_normals: tuple[tuple[float, float, float], ...]
    mode: AcquisitionMode
    seed: int
    noise_deg: float
    evidences: tuple[EvidenceRecord, ...]

    def claim_class(self) -> str:
        return OBSERVATION_CLAIM_CLASS


# --- the synthetic forward model ----------------------------------------

def polarization_evidence(state: OrientationState) -> EvidenceRecord:
    """Crossed-polarizer intensity vanishes at the projected-c azimuth.

    Between crossed polarizers the birefringent slow/fast axes lie along the
    projection of the optic axis onto the viewing plane; extinction repeats
    every 90 degrees. The azimuth is read modulo 90, and it says nothing
    about the tilt out of plane or the c-axis sign.
    """
    cx, cy, _ = state.c_axis
    az = math.degrees(math.atan2(cy, cx)) % 90.0
    return EvidenceRecord(
        EvidenceType.POLARIZATION, AcquisitionMode.SYNTHETIC,
        "extinction_azimuth_deg", az, _COMPONENT_SIGMAS_DEG[
            "polarizer_extinction_angle"],
        "projected optic-axis azimuth (mod 90 deg)",
        "optic-axis tilt, c-axis sign, handedness")


def extinction_evidence(state: OrientationState) -> EvidenceRecord:
    """The extinction sharpness constrains how near the view is to the axis.

    Along the optic axis the crystal is isotropic (no extinction); the
    modelled extinction contrast grows with the optic-axis tilt. This is a
    second, weaker handle on the same tilt the conoscopic figure gives.
    """
    tilt = angle_between(state.c_axis, _Z)
    tilt = min(tilt, 180.0 - tilt)
    return EvidenceRecord(
        EvidenceType.EXTINCTION, AcquisitionMode.SYNTHETIC,
        "extinction_contrast_from_tilt_deg", tilt, _COMPONENT_SIGMAS_DEG[
            "polarizer_extinction_angle"],
        "optic-axis tilt magnitude", "azimuth sense, c-axis sign, handedness")


def conoscopic_evidence(state: OrientationState) -> EvidenceRecord:
    """A conoscopic figure gives the optic-axis tilt from the view direction.

    The melatope offset in an interference figure measures how far the optic
    axis lies from the microscope axis. It is an unsigned magnitude: the
    figure for ``+c`` and ``-c`` is identical.
    """
    tilt = angle_between(state.c_axis, _Z)
    tilt = min(tilt, 180.0 - tilt)
    return EvidenceRecord(
        EvidenceType.CONOSCOPIC, AcquisitionMode.SYNTHETIC,
        "optic_axis_tilt_deg", tilt, _COMPONENT_SIGMAS_DEG[
            "conoscopic_tilt_angle"],
        "optic-axis polar tilt", "c-axis sign, handedness, a-azimuth")


def geometry_evidence(state: OrientationState) -> EvidenceRecord:
    """Optical goniometry gives the facet inter-normal directions.

    The rhombohedral face normals form the point-group-32 orbit of one face,
    a set symmetric about the c-line; it fixes the c-axis as that symmetry
    axis (sign-free) and the a-azimuth up to the group. Because the point
    group is 32, the whole orientation is fixed only up to that symmetry, and
    the faces are the same for either enantiomorph and for either c-sign.
    """
    normals = state.facet_normals()
    return EvidenceRecord(
        EvidenceType.GEOMETRY, AcquisitionMode.SYNTHETIC,
        "facet_normals_unit", tuple(normals), _COMPONENT_SIGMAS_DEG[
            "goniometer_facet_angle"],
        "c-axis line and a-azimuth up to point-group 32",
        "which of the 6 symmetry aliases, c-axis sign, handedness")


def _seeded_perturbation(rng: np.random.Generator, v: np.ndarray,
                         angle_deg: float) -> np.ndarray:
    """Rotate ``v`` by exactly ``angle_deg`` about a random axis (seeded)."""
    if angle_deg <= 0.0:
        return _unit(v)
    axis = rng.standard_normal(3)
    # ensure the axis is not parallel to v so the rotation actually moves it
    if float(np.linalg.norm(np.cross(axis, v))) < 1e-6:
        axis = axis + _Y
    R = rotation_about_axis(_unit(np.cross(v, axis)), math.radians(angle_deg))
    return _unit(R @ v)


def forward_observation(state: OrientationState,
                        mode: AcquisitionMode = AcquisitionMode.SYNTHETIC,
                        noise_deg: float = 0.0,
                        seed: int = 0) -> OrientationObservation:
    """Map an orientation to a deterministic cheap-bench dataset.

    Produces the polarizer extinction azimuth, the conoscopic optic-axis
    tilt and the goniometric facet normals, perturbed by a seeded angular
    noise of magnitude ``noise_deg`` per facet. Fully deterministic in
    ``(state, noise_deg, seed)`` -- no wall-clock, no unseeded randomness.
    """
    if mode is AcquisitionMode.REAL:
        raise OrientationError(
            "refused: AcquisitionMode.REAL requires a physical goniometer and "
            "specimen; no such acquisition exists here. Use SYNTHETIC.")
    if noise_deg < 0.0:
        raise OrientationError("noise_deg must be non-negative")

    rng = np.random.default_rng(int(seed))
    pol = polarization_evidence(state)
    con = conoscopic_evidence(state)
    ext = extinction_evidence(state)
    clean_normals = [np.asarray(n, dtype=float) for n in state.facet_normals()]
    noisy = [_seeded_perturbation(rng, n, noise_deg) for n in clean_normals]
    geo = EvidenceRecord(
        EvidenceType.GEOMETRY, mode, "facet_normals_unit",
        tuple(_vec(n) for n in noisy),
        _COMPONENT_SIGMAS_DEG["goniometer_facet_angle"],
        "c-axis line and a-azimuth up to point-group 32",
        "which of the 6 symmetry aliases, c-axis sign, handedness")

    return OrientationObservation(
        extinction_azimuth_deg=float(pol.value),
        optic_axis_tilt_deg=float(con.value),
        facet_normals=tuple(_vec(n) for n in noisy),
        mode=mode,
        seed=int(seed),
        noise_deg=float(noise_deg),
        evidences=(pol, ext, con, geo),
    )


# --- the symmetry alias set ---------------------------------------------

def alias_set(state: OrientationState) -> list[OrientationState]:
    """Every orientation producing observations identical to ``state``.

    The six proper rotations of point group 32 (reused from
    :mod:`r13.crystalframe`) right-multiply the orientation; each image has
    the same facet-normal set, the same optic-axis tilt and the same
    extinction azimuth. The three two-folds send the c-axis to ``-c``, so the
    set always contains both ends of the optic-axis line. It always has more
    than one member: a cheap-bench fit names an equivalence class, not a
    point.
    """
    R = state.rotation()
    out = []
    for S in QUARTZ_FRAME.symmetry_operators():
        out.append(OrientationState.from_rotation(R @ S, state.handedness))
    return out


def distinct_c_axes(state: OrientationState, tol_deg: float = 1e-6
                    ) -> list[tuple[float, float, float]]:
    """The distinct c-axis *rays* in the alias set (``+c`` and ``-c`` both)."""
    axes: list[np.ndarray] = []
    for s in alias_set(state):
        c = np.asarray(s.c_axis, dtype=float)
        if not any(angle_between(c, a) < tol_deg for a in axes):
            axes.append(c)
    return [_vec(a) for a in axes]


def refuse_orientation_as_unique(state: OrientationState, **_k) -> None:
    """The cheap-bench solution is an alias class, not a unique orientation.

    Point group 32 leaves six symmetry-equivalent orientations with
    identical observations, and among them the c-axis appears with both
    signs. Collapsing that set to one orientation is choosing an arbitrary
    member and presenting it as a determination.
    """
    n = len(alias_set(state))
    raise OrientationError(
        f"refused: the recovered orientation is one of {n} "
        f"symmetry-equivalent members of a point-group-32 alias set, all "
        f"producing identical cheap-bench observations, including both signs "
        f"of the optic-axis line. A unique orientation may not be claimed "
        f"from these observations. Use alias_set() and report every member; "
        f"lifting the aliasing needs indexed diffraction.")


def refuse_optic_axis_polarity(*_a, **_k) -> None:
    """The optic axis is an undirected line; its sign is not observable.

    Linear birefringence, the conoscopic tilt and the face angles are all
    identical for ``+c`` and ``-c``. The 180-degree ambiguity is intrinsic
    to these observations and cannot be resolved without diffraction
    (e.g. anomalous-dispersion or a Laue polarity determination).
    """
    raise OrientationError(
        "refused: the optic axis is an undirected line. The extinction "
        "azimuth, the conoscopic figure and the rhombohedral face angles are "
        "identical for +c and -c, so the c-axis sign is undetermined by these "
        "observations. The 180-degree ambiguity is intrinsic; resolving it "
        "requires a diffraction polarity determination (PREREGISTERED_NOT_RUN).")


def refuse_handedness_from_geometry(*_a, **_k) -> None:
    """Handedness is not recoverable from achiral optical/geometric data.

    The right-handed P3_121 crystal and its left-handed P3_221 enantiomorph
    share the same face angles, the same linear birefringence and the same
    optic-axis tilt. Distinguishing them needs a chiral probe -- the sign of
    optical rotation, etch-figure symmetry, or anomalous-dispersion XRD.
    """
    raise OrientationError(
        "refused: handedness (P3_121 vs P3_221) cannot be inferred from the "
        "c-axis or any observation in this module. Linear birefringence, face "
        "angles and the conoscopic tilt are achiral and identical for both "
        "enantiomorphs. A chiral probe is required: optical-rotation sign, "
        "etch figures, or anomalous-dispersion diffraction (PREREGISTERED_NOT_RUN).")


# --- the inverse solver -------------------------------------------------

@dataclass(frozen=True)
class OrientationSolution:
    """The recovered orientation plus its honest limits.

    ``recovered`` is a single representative of the alias class;
    ``alias_size`` counts the symmetry-equivalent members; ``residual_deg``
    is the fit residual against the reconstructed symmetric ideal;
    ``within_budget`` is whether that residual sits inside the expanded
    uncertainty. Handedness on ``recovered`` is always ``UNDETERMINED``.
    """

    recovered: OrientationState
    recovered_tilt_deg: float
    recovered_extinction_azimuth_deg: float
    residual_deg: float
    within_budget: bool
    expanded_uncertainty_deg: float
    alias_size: int
    mode: AcquisitionMode


def _recover_c_axis(normals: list[np.ndarray]) -> np.ndarray:
    """Recover the c-axis as the symmetry axis of the facet-normal orbit.

    The faces lie on a pair of cones symmetric about the c-line, so the
    scatter matrix ``sum n_i n_i^T`` has one isolated eigenvalue whose
    eigenvector is the c-axis; the two in-plane eigenvalues are (near) equal.
    The eigenvector is returned sign-free -- the c-axis is an undirected line.
    """
    M = np.zeros((3, 3))
    for n in normals:
        M += np.outer(n, n)
    w, V = np.linalg.eigh(M)  # ascending eigenvalues
    # the isolated eigenvalue sits on the side of the larger gap
    if (w[1] - w[0]) >= (w[2] - w[1]):
        c = V[:, 0]
    else:
        c = V[:, 2]
    return _unit(c)


def solve_orientation(obs: OrientationObservation,
                      budget: dict | None = None) -> OrientationSolution:
    """Recover the planted orientation from a cheap-bench dataset (POWER).

    The c-axis is the symmetry axis of the rhombohedral facet-normal orbit
    (the isolated eigenvector of their scatter matrix), recovered as an
    undirected line; the a-azimuth is a representative face azimuth about it.
    The fit residual is the largest angular deviation of an observed facet
    from the reconstructed symmetric ideal; if it exceeds the expanded
    uncertainty of the error budget, the fit is refused as out of budget.
    """
    b = budget if budget is not None else build_error_budget()
    expanded = expanded_uncertainty_deg(b)

    normals = [_unit(n) for n in obs.facet_normals]
    if len(normals) < 3:
        raise OrientationError(
            "at least three facet normals are required to fit a c-axis")

    c_hat = _recover_c_axis(normals)
    # a representative azimuth: from a face on the +c side of the recovered
    # line (the sign is arbitrary; either choice yields a valid representative)
    upper = max(normals, key=lambda n: float(n @ c_hat))
    a0 = azimuth_about_c(upper, c_hat) % 360.0
    recovered = OrientationState(_vec(c_hat), a0, Handedness.UNDETERMINED)

    # the faces lie on two cones (+/- the cone half-angle) about the c-line.
    # fit one shared half-angle and measure each face's deviation from the
    # cone at its own azimuth: zero when the orbit is clean, growing with
    # per-face acquisition noise.
    pols = [angle_between(n, c_hat) for n in normals]
    folded = [p if p <= 90.0 else 180.0 - p for p in pols]
    theta_bar = float(np.mean(folded))
    residual = 0.0
    for n, p in zip(normals, pols):
        signed = theta_bar if p <= 90.0 else 180.0 - theta_bar
        ideal = _direction_from_c(c_hat, signed, azimuth_about_c(n, c_hat))
        residual = max(residual, angle_between(n, ideal))

    within = residual <= expanded
    if not within:
        raise OrientationError(
            f"refused: fit residual {residual:.3f} deg exceeds the expanded "
            f"orientation uncertainty {expanded:.3f} deg (k={b['coverage_factor']} "
            f"* {b['combined_uncertainty']:.3f} deg). The observations are "
            f"noisier than the error budget allows; no orientation is "
            f"reported. This is a MODEL/observation-noise refusal, not a "
            f"determination.")

    return OrientationSolution(
        recovered=recovered,
        recovered_tilt_deg=line_angle(c_hat, _Z),
        recovered_extinction_azimuth_deg=obs.extinction_azimuth_deg,
        residual_deg=residual,
        within_budget=within,
        expanded_uncertainty_deg=expanded,
        alias_size=len(alias_set(recovered)),
        mode=obs.mode,
    )


# --- the orientation certificate ----------------------------------------

def additional_evidence_to_upgrade() -> list[dict]:
    """The exact physical acquisitions needed to lift each cheap-bench cap.

    Each entry names the ambiguity, the acquisition that would resolve it,
    and the confidence level it would unlock. Every one of these is a
    physical run that is not performed here: PREREGISTERED_NOT_RUN.
    """
    return [
        {"ambiguity": SYMMETRY_ALIAS_AMBIGUITY,
         "acquisition": "indexed single-crystal diffraction (Laue or "
                        "four-circle) to select one domain of point group 32",
         "unlocks": ConfidenceLevel.XRD_CONFIRMED.name,
         "status": "PREREGISTERED_NOT_RUN"},
        {"ambiguity": OPTIC_AXIS_LINE_AMBIGUITY,
         "acquisition": "diffraction polarity determination (anomalous "
                        "dispersion / Laue back-reflection) to fix the c-axis sign",
         "unlocks": ConfidenceLevel.XRD_CONFIRMED.name,
         "status": "PREREGISTERED_NOT_RUN"},
        {"ambiguity": HANDEDNESS_AMBIGUITY,
         "acquisition": "chiral probe: optical-rotation sign, etch-figure "
                        "symmetry, or anomalous-dispersion XRD (P3_121 vs P3_221)",
         "unlocks": ConfidenceLevel.XRD_CONFIRMED.name,
         "status": "PREREGISTERED_NOT_RUN"},
        {"ambiguity": "single-run non-replication",
         "acquisition": "an independent remounted determination on a second "
                        "instrument",
         "unlocks": ConfidenceLevel.XRD_REPLICATED.name,
         "status": "PREREGISTERED_NOT_RUN"},
    ]


def refuse_certificate_confirmed_without_xrd(
        requested: ConfidenceLevel = ConfidenceLevel.XRD_CONFIRMED, **_k
) -> None:
    """A confirmed certificate may not be issued from cheap observations.

    Only diffraction can select a single domain, fix the c-axis sign and the
    handedness. Without it the certificate is capped at ``PRESUMPTIVE``.
    """
    if requested.value > NO_XRD_CONFIDENCE_CAP.value:
        raise OrientationError(
            f"refused: a {requested.name} orientation certificate requires "
            f"diffraction, which is not performed here. Without XRD the "
            f"symmetry alias set, the c-axis sign and the handedness all "
            f"remain open, so the certificate is capped at "
            f"{NO_XRD_CONFIDENCE_CAP.name}. See additional_evidence_to_upgrade().")


def generate_orientation_certificate(
        state: OrientationState,
        budget: dict | None = None,
        noise_deg: float = 0.2,
        seed: int = 0,
        requested_confidence: ConfidenceLevel = ConfidenceLevel.XRD_CONFIRMED
) -> dict:
    """Run the full cheap-bench workflow and emit a capped certificate.

    Forward-models ``state`` to a synthetic dataset, solves it, enumerates
    the alias set, caps the confidence to the no-diffraction ceiling, and
    lists the additional evidence needed to upgrade. The certificate is a
    ``MODEL_PREDICTION`` over a ``SYNTHETIC_OBSERVATION``; nothing is measured.
    """
    b = budget if budget is not None else build_error_budget()
    obs = forward_observation(state, AcquisitionMode.SYNTHETIC,
                              noise_deg=noise_deg, seed=seed)
    solution = solve_orientation(obs, b)
    aliases = alias_set(solution.recovered)
    confidence = cap_confidence_without_xrd(requested_confidence)

    # the observation binds an uncertainty and a protocol but no instrument,
    # calibration, specimen, fixture, clock, environment or raw artifact:
    # evidence caps below a physical measurement.
    bindings = claims.EvidenceBindings(uncertainty=True, protocol=True)
    evidence = claims.evidence_cap(bindings, claims.EvidenceLevel.E4)

    return {
        "certificate_type": EvidenceType.CERTIFICATE.value,
        "material": state.material,
        "mode": obs.mode.value,
        "recovered": {
            "c_axis": solution.recovered.c_axis,
            "optic_axis": solution.recovered.optic_axis(),
            "a_azimuth_deg": solution.recovered.a_azimuth_deg,
            "optic_axis_tilt_deg": solution.recovered_tilt_deg,
            "extinction_azimuth_deg": solution.recovered_extinction_azimuth_deg,
            "handedness": solution.recovered.handedness.value,
        },
        "handedness_determined": False,
        "handedness_reason": HANDEDNESS_AMBIGUITY,
        "optic_axis_sign_determined": False,
        "optic_axis_reason": OPTIC_AXIS_LINE_AMBIGUITY,
        "alias_set_size": len(aliases),
        "alias_set_c_axes": distinct_c_axes(solution.recovered),
        "symmetry_ambiguity": SYMMETRY_ALIAS_AMBIGUITY,
        "unique_orientation_claimed": False,
        "residual_deg": solution.residual_deg,
        "within_budget": solution.within_budget,
        "error_budget": b,
        "expanded_uncertainty_deg": solution.expanded_uncertainty_deg,
        "requested_confidence": requested_confidence.name,
        "confidence": confidence.name,
        "confidence_capped_by_no_xrd": confidence is not requested_confidence,
        "no_xrd_confidence_cap": NO_XRD_CONFIDENCE_CAP.name,
        "additional_evidence_to_upgrade": additional_evidence_to_upgrade(),
        "evidence_level": evidence.name,
        "evidence_types_used": [e.value for e in EvidenceType
                                if e is not EvidenceType.CERTIFICATE],
        "recovery_claim_class": RECOVERY_CLAIM_CLASS,
        "observation_claim_class": OBSERVATION_CLAIM_CLASS,
        "measured_here": "nothing",
        "physical_validation": PHYSICAL_VALIDATION,
        "verdict": VERDICT,
    }


# --- the report ----------------------------------------------------------

def orientation_report() -> dict:
    """Module report: what the cheap-bench solver does and refuses to claim."""
    planted = OrientationState(
        c_axis=_vec(rotation_about_axis((0.2, -0.5, 0.84), 0.6) @ _Z),
        a_azimuth_deg=37.0,
        handedness=Handedness.RIGHT,
    )
    budget = build_error_budget()
    obs = forward_observation(planted, noise_deg=0.2, seed=7)
    solution = solve_orientation(obs, budget)
    cert = generate_orientation_certificate(planted, budget, noise_deg=0.2,
                                            seed=7)
    recovered_error = line_angle(solution.recovered.c_axis, planted.c_axis)
    return {
        "what_this_is": (
            "a low-cost specimen-orientation solver: a synthetic forward "
            "model from orientation to cheap optical/goniometric observables "
            "and an inverse solver that recovers a planted orientation within "
            "an error budget, without assuming XRD access"),
        "material": MATERIAL,
        "evidence_types": [e.value for e in EvidenceType],
        "acquisition_modes": [m.value for m in AcquisitionMode],
        "planted_c_axis": planted.c_axis,
        "recovered_c_axis": solution.recovered.c_axis,
        "recovered_c_axis_line_error_deg": recovered_error,
        "expanded_uncertainty_deg": solution.expanded_uncertainty_deg,
        "recovered_within_uncertainty": recovered_error
        <= solution.expanded_uncertainty_deg,
        "residual_deg": solution.residual_deg,
        "alias_set_size": solution.alias_size,
        "alias_set_has_many_members": solution.alias_size > 1,
        "distinct_c_axis_rays": len(distinct_c_axes(solution.recovered)),
        "handedness_recovered": solution.recovered.handedness.value,
        "certificate_confidence": cert["confidence"],
        "certificate_confidence_capped": cert["confidence_capped_by_no_xrd"],
        "no_xrd_confidence_cap": NO_XRD_CONFIDENCE_CAP.name,
        "refusals_available": [
            "refuse_orientation_as_unique (symmetry alias set)",
            "refuse_optic_axis_polarity (c-axis sign / 180-degree ambiguity)",
            "refuse_handedness_from_geometry (achiral observations)",
            "refuse_certificate_confirmed_without_xrd (no-XRD cap)",
        ],
        "recovery_claim_class": RECOVERY_CLAIM_CLASS,
        "observation_claim_class": OBSERVATION_CLAIM_CLASS,
        "measured_here": "nothing",
        "physical_validation": PHYSICAL_VALIDATION,
        "verdict": VERDICT,
        "what_this_does_not_say": (
            "It does not measure an orientation: the observations are "
            "deterministic simulator output, not a goniometer, polarizer or "
            "camera reading of a mounted specimen, and the recovered "
            "orientation is a MODEL_PREDICTION. It does not claim a unique "
            "orientation -- point group 32 leaves a six-member symmetry alias "
            "set including both signs of the optic-axis line. It does not "
            "infer the c-axis sign or the handedness, which are invisible to "
            "these achiral observations. And it does not issue an "
            "XRD-confirmed certificate: without diffraction the confidence is "
            "capped at PRESUMPTIVE. Nothing here is measured."),
    }


__all__ = [
    "OrientationError", "Handedness", "EvidenceType", "AcquisitionMode",
    "ConfidenceLevel", "NO_XRD_CONFIDENCE_CAP", "cap_confidence_without_xrd",
    "MATERIAL", "VERDICT", "PHYSICAL_VALIDATION", "RECOVERY_CLAIM_CLASS",
    "OBSERVATION_CLAIM_CLASS", "OPTIC_AXIS_LINE_AMBIGUITY",
    "SYMMETRY_ALIAS_AMBIGUITY", "HANDEDNESS_AMBIGUITY", "N_FACETS",
    "COVERAGE_FACTOR", "azimuth_about_c", "angle_between", "line_angle",
    "OrientationState", "build_error_budget", "expanded_uncertainty_deg",
    "EvidenceRecord", "OrientationObservation", "polarization_evidence",
    "extinction_evidence", "conoscopic_evidence", "geometry_evidence",
    "forward_observation", "alias_set", "distinct_c_axes",
    "refuse_orientation_as_unique", "refuse_optic_axis_polarity",
    "refuse_handedness_from_geometry", "OrientationSolution",
    "solve_orientation", "additional_evidence_to_upgrade",
    "refuse_certificate_confirmed_without_xrd",
    "generate_orientation_certificate", "orientation_report",
]
