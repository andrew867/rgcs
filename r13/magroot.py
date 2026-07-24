"""P38 — the geomagnetic (IGRF) root as an orientation reference, with
its alias limits stated.

R12's :mod:`r12.igrf14root` finalised an IGRF-14 magnetic-root certificate
at an explicit epoch and left the numerical coefficient grid a declared
``BLOCKED_MISSING_DATA`` receipt. This module takes that root one honest
step further: it treats the field as an *orientation reference* -- the one
thing a single magnetic vector legitimately supplies -- and marks, in
code, the two places where the reference stops being usable.

**Orientation from a single field vector, up to one undetermined turn.**
Given the field direction in a fixed (world) frame and the same field as
seen in a body frame, the body's attitude is recovered -- but only up to
rotation *about the field axis*. One vector fixes two of the three
rotational degrees of freedom; the spin around the field line is invisible
to a single measurement. :func:`orientation_from_field` returns the
shortest-arc attitude and names the residual freedom;
:func:`rotation_about_axis` lets a caller verify that adding any turn about
the field axis leaves the measured vector unchanged. That is POWER on the
two recoverable degrees of freedom and an explicit refusal of the third.

**A field value is consistent with a LOCUS, not a point.** The main field
is not injective over the globe: an axial-dipole total intensity depends
on magnetic latitude alone, so one intensity is shared by an entire circle
of longitudes and, generically, two hemispheres. :func:`root_alias_set`
returns that set -- always more than one member -- and
:func:`refuse_root_as_unique_location` refuses to collapse it to a single
address.

**Matching a field value is not authenticating a transmitter.** The IGRF
Gauss coefficients are ``CONVENTIONAL_LITERATURE``, and the field drifts
with epoch by secular variation (reused from R12), so the same coordinate
reads a different field in a different year. That a measured value matches
a modelled one is a coincidence of numbers, never a source signature;
:func:`refuse_field_match_as_source` raises.

Nothing here is measured. The fields are declared analytic dipole models
in dimensionless-to-nanotesla model units; no magnetometer is read, no
survey is used, and no site is located. The standing verdict is
``IGRF_ROOT_AND_ORIENTATION_ALIAS_LIMITED``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

import numpy as np

from r11.earthface import dipole_axis
from r12.igrf14root import (
    MODEL_GENERATION,
    drift_between,
    epoch_validity,
    require_dynamo_body,
)


class MagRootError(RuntimeError):
    """Raised when the magnetic root is asked to over-claim: a unique
    location from a field value that names a locus, a full attitude from a
    single vector, or a source from a numeric field match."""


# --- claim vocabulary ---------------------------------------------------

class ClaimClass(Enum):
    """The claim classes a statement in this module may declare."""

    EXACT_IDENTITY = "EXACT_IDENTITY"
    SOURCE_ESTABLISHED_PHYSICS = "SOURCE_ESTABLISHED_PHYSICS"
    CONVENTIONAL_LITERATURE = "CONVENTIONAL_LITERATURE"
    DERIVED_ARITHMETIC = "DERIVED_ARITHMETIC"
    ANALYTIC_MODEL = "ANALYTIC_MODEL"
    NUMERICAL_SIMULATION = "NUMERICAL_SIMULATION"
    REPOSITORY_COMPUTATIONAL_RESULT = "REPOSITORY_COMPUTATIONAL_RESULT"
    ENGINEERING_CANDIDATE = "ENGINEERING_CANDIDATE"
    RETROSPECTIVE_NUMERIC_MATCH = "RETROSPECTIVE_NUMERIC_MATCH"
    UNSUPPORTED = "UNSUPPORTED"
    BLOCKED_MISSING_INPUT = "BLOCKED_MISSING_INPUT"


CLAIM_CLASSES: tuple[str, ...] = tuple(c.value for c in ClaimClass)

#: The IGRF Gauss coefficients are literature; the constructions here are
#: analytic dipole models.
CLAIM_CLASS = ClaimClass.ANALYTIC_MODEL.value
SOURCE_CLASS = ClaimClass.CONVENTIONAL_LITERATURE.value

PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"
VERDICT = "IGRF_ROOT_AND_ORIENTATION_ALIAS_LIMITED"

MODEL_UNITS = "MODEL_NANOTESLA"

#: Public neutral alias for the orientation reference this module supplies.
IGRF_ORIENTATION_REFERENCE_A = "IGRF_ORIENTATION_REFERENCE_A"

#: A conventional surface dipole moment strength, in model nT. Not an IGRF
#: coefficient set; a declared analytic stand-in used to exercise the
#: orientation and alias logic.
AXIAL_MOMENT_NT = 30000.0

#: What one magnetic vector leaves undetermined: the spin about the field
#: axis. A single vector fixes two rotational degrees of freedom, not three.
ORIENTATION_AMBIGUITY = "ROTATION_ABOUT_FIELD_AXIS_UNDETERMINED"


# --- small vector / rotation helpers -----------------------------------

def _unit(v) -> np.ndarray:
    a = np.asarray(v, dtype=float)
    if a.shape != (3,):
        raise MagRootError("a direction must be a 3-vector")
    n = float(np.linalg.norm(a))
    if n == 0.0:
        raise MagRootError("a zero vector has no direction")
    return a / n


def _skew(v: np.ndarray) -> np.ndarray:
    return np.array([[0.0, -v[2], v[1]],
                    [v[2], 0.0, -v[0]],
                    [-v[1], v[0], 0.0]], dtype=float)


def rotation_about_axis(axis, angle_rad: float) -> np.ndarray:
    """Proper rotation by ``angle_rad`` about ``axis`` (Rodrigues).

    This is exactly the freedom a single field vector cannot see: a
    rotation about the field axis leaves the field vector fixed, so it can
    be added to any recovered attitude without changing the measurement.
    """
    k = _unit(axis)
    K = _skew(k)
    return (np.eye(3) + math.sin(float(angle_rad)) * K
            + (1.0 - math.cos(float(angle_rad))) * (K @ K))


def shortest_arc_rotation(from_dir, to_dir) -> np.ndarray:
    """The minimal-angle proper rotation mapping ``from_dir`` to ``to_dir``.

    ``R @ from_dir == to_dir`` (as unit vectors). Of the one-parameter
    family of rotations that do this, the shortest arc is returned; the
    remaining freedom is a turn about ``to_dir`` and is what
    :func:`orientation_from_field` reports as undetermined.
    """
    a = _unit(from_dir)
    b = _unit(to_dir)
    c = float(np.dot(a, b))
    v = np.cross(a, b)
    s = float(np.linalg.norm(v))
    if s < 1e-15:
        if c > 0.0:
            return np.eye(3)
        # antiparallel: a half-turn about any axis perpendicular to a
        perp = np.array([1.0, 0.0, 0.0]) if abs(a[0]) < 0.9 \
            else np.array([0.0, 1.0, 0.0])
        return rotation_about_axis(_unit(np.cross(a, perp)), math.pi)
    K = _skew(v)
    return np.eye(3) + K + (K @ K) * ((1.0 - c) / (s * s))


def apply_rotation(R: np.ndarray, v) -> np.ndarray:
    """Apply a 3x3 rotation to a 3-vector."""
    M = np.asarray(R, dtype=float)
    if M.shape != (3, 3):
        raise MagRootError("a rotation must be a 3x3 matrix")
    return M @ np.asarray(v, dtype=float)


# --- the declared synthetic field --------------------------------------

def _geocentric_unit(lat_deg: float, lon_deg: float) -> np.ndarray:
    """Unit position on the sphere for a geocentric (lat, lon)."""
    lat = math.radians(float(lat_deg))
    lon = math.radians(float(lon_deg))
    c = math.cos(lat)
    return np.array([c * math.cos(lon), c * math.sin(lon), math.sin(lat)],
                    dtype=float)


def field_vector_at(lat_deg: float, lon_deg: float, epoch: float,
                    moment_nT: float = AXIAL_MOMENT_NT) -> np.ndarray:
    """The declared analytic dipole field vector at a location and epoch.

    The dipole axis is taken from :func:`r11.earthface.dipole_axis`, which
    drifts with epoch by the declared secular-variation model, so the same
    location reads a different vector in a different year. In model nT.
    """
    rhat = _geocentric_unit(lat_deg, lon_deg)
    m = dipole_axis(str(epoch))
    return float(moment_nT) * (3.0 * float(np.dot(m, rhat)) * rhat - m)


def field_direction_at(lat_deg: float, lon_deg: float, epoch: float
                       ) -> np.ndarray:
    """Unit direction of the declared field at a location and epoch."""
    return _unit(field_vector_at(lat_deg, lon_deg, epoch))


def field_changes_with_epoch(lat_deg: float, lon_deg: float,
                             epoch_a: float, epoch_b: float) -> dict:
    """Show the declared field at one location differs between two epochs.

    Reuses R12's :func:`~r12.igrf14root.drift_between` for the epoch-drift
    bookkeeping and adds the vector difference of the declared model. The
    field is not a fixed label on a coordinate; it is epoch-bound.
    """
    ba = field_vector_at(lat_deg, lon_deg, epoch_a)
    bb = field_vector_at(lat_deg, lon_deg, epoch_b)
    diff = float(np.linalg.norm(bb - ba))
    drift = drift_between(epoch_a, epoch_b)
    return {
        "lat_deg": float(lat_deg),
        "lon_deg": float(lon_deg),
        "epoch_a": float(epoch_a),
        "epoch_b": float(epoch_b),
        "vector_a_nT": tuple(float(x) for x in ba),
        "vector_b_nT": tuple(float(x) for x in bb),
        "vector_difference_nT": diff,
        "field_moved": diff > 0.0 or drift["drift_nT"] > 0.0,
        "r12_drift_nT": drift["drift_nT"],
        "claim_class": ClaimClass.ANALYTIC_MODEL.value,
        "note": (
            "the declared analytic field drifts with epoch; a coordinate "
            "is not a timeless field label. Reuses r12.igrf14root drift"),
    }


# --- orientation from a single field vector ----------------------------

def orientation_from_field(reference_dir, measured_dir) -> dict:
    """Recover attitude from one field vector, up to the axis ambiguity.

    ``reference_dir`` is the field direction in a fixed world frame;
    ``measured_dir`` is the same field as seen in the body frame. The body
    attitude ``R`` satisfies ``reference = R @ measured``. A single vector
    fixes only two rotational degrees of freedom, so ``R`` is recovered
    only up to a turn about the field axis (``reference``). The shortest-arc
    attitude is returned, together with the undetermined freedom.
    """
    ref = _unit(reference_dir)
    meas = _unit(measured_dir)
    R = shortest_arc_rotation(meas, ref)
    residual = float(np.max(np.abs(R @ meas - ref)))
    return {
        "reference_alias": IGRF_ORIENTATION_REFERENCE_A,
        "rotation": tuple(tuple(float(x) for x in row) for row in R),
        "reference_dir": tuple(float(x) for x in ref),
        "measured_dir": tuple(float(x) for x in meas),
        "residual_max_abs": residual,
        "recovered_dof": 2,
        "undetermined_dof": 1,
        "ambiguity": ORIENTATION_AMBIGUITY,
        "ambiguity_axis": tuple(float(x) for x in ref),
        "claim_class": ClaimClass.ANALYTIC_MODEL.value,
        "note": (
            "attitude from one field vector is fixed only up to rotation "
            "about the field axis; the spin around the field line is "
            "invisible to a single measurement"),
    }


def refuse_full_attitude_from_single_vector(*_a, **_k) -> None:
    """A single field vector does not fix a full three-axis attitude.

    Two directions (or a vector and an independent reference) are needed to
    resolve all three rotational degrees of freedom. One vector leaves a
    turn about the field axis undetermined, so a claim of a unique full
    attitude from a single magnetic reading is refused.
    """
    raise MagRootError(
        "refused: a single magnetic field vector fixes two rotational "
        "degrees of freedom, not three. The rotation about the field axis "
        "is undetermined by one measurement, so a unique full attitude may "
        "not be claimed from it. Use orientation_from_field() and report "
        f"the {ORIENTATION_AMBIGUITY} freedom, or supply a second "
        "independent direction.")


# --- the field value is consistent with a locus, not a point -----------

def axial_total_intensity(lat_deg: float, radius_ratio: float = 1.0,
                          moment_nT: float = AXIAL_MOMENT_NT) -> float:
    """|B| of an axial dipole: depends on latitude and radius only.

    ``|B| = moment * sqrt(1 + 3 sin^2(lat)) / r^3``. Because longitude does
    not enter, one intensity is shared by an entire circle of longitudes.
    """
    if radius_ratio <= 0:
        raise MagRootError("radius ratio must be positive")
    s = math.sin(math.radians(float(lat_deg)))
    return (float(moment_nT) * math.sqrt(1.0 + 3.0 * s * s)
            / float(radius_ratio) ** 3)


def root_alias_set(target_nT: float, moment_nT: float = AXIAL_MOMENT_NT,
                   n_longitudes: int = 12, radius_ratio: float = 1.0
                   ) -> list[dict]:
    """The locus of locations consistent with one axial-dipole intensity.

    Inverting ``|B|(lat)`` gives ``sin^2(lat)``, hence a magnetic latitude
    and (generically) its mirror in the other hemisphere -- and every
    longitude. The returned set therefore always has more than one member:
    a magnetic condition does not decode a location.
    """
    if n_longitudes < 2:
        raise MagRootError(
            "an alias set over fewer than two longitudes is not an alias "
            "set; the whole point is that longitude is unconstrained")
    if radius_ratio <= 0:
        raise MagRootError("radius ratio must be positive")
    f = float(target_nT) * float(radius_ratio) ** 3 / float(moment_nT)
    x = (f * f - 1.0) / 3.0
    if x < -1e-9 or x > 1.0 + 1e-9:
        raise MagRootError(
            f"target {target_nT} nT is outside the achievable axial-dipole "
            f"range [{moment_nT / radius_ratio ** 3:.3f}, "
            f"{2.0 * moment_nT / radius_ratio ** 3:.3f}] model nT")
    x = min(max(x, 0.0), 1.0)
    lat = math.degrees(math.asin(math.sqrt(x)))
    lats = sorted({round(lat, 9), round(-lat, 9)})
    lons = [(-180.0 + 360.0 * i / n_longitudes) for i in range(n_longitudes)]
    return [{"lat_deg": la, "lon_deg": lo, "radius_ratio": float(radius_ratio)}
            for la in lats for lo in lons]


def refuse_root_as_unique_location(target_nT: float = AXIAL_MOMENT_NT,
                                   **_k) -> None:
    """A field value names a locus, so it may not be read as one place.

    The main field is not injective over the globe. An intensity is shared
    by a whole circle of longitudes and generically two hemispheres, so
    collapsing the alias set to one coordinate is choosing an arbitrary
    member and presenting it as a fix.
    """
    raise MagRootError(
        f"refused: the field value {target_nT} nT is consistent with a "
        f"LOCUS of locations, not one. An axial-dipole intensity depends on "
        f"latitude alone, so it is shared by an entire circle of longitudes "
        f"and, generically, both hemispheres. Use root_alias_set() and "
        f"report every member; a magnetic condition does not uniquely "
        f"decode a location.")


def refuse_field_match_as_source(measured_nT: float = AXIAL_MOMENT_NT,
                                 modelled_nT: float = AXIAL_MOMENT_NT,
                                 **_k) -> None:
    """Matching a modelled field value is not authenticating a source.

    A close number is not a signature. The IGRF coefficients are
    literature, the field drifts with epoch, and many locations share one
    value; a measured value landing near a modelled one is a coincidence of
    numbers, never confirmation of a transmitter or its location.
    """
    raise MagRootError(
        f"refused: a measured field value ({measured_nT} nT) matching a "
        f"modelled one ({modelled_nT} nT) does not authenticate a source "
        f"or locate a transmitter. The {MODEL_GENERATION} coefficients are "
        f"CONVENTIONAL_LITERATURE, the field drifts with epoch by secular "
        f"variation, and one value is shared by a whole locus of "
        f"locations. A numeric match is not a signature; this is a "
        f"RETROSPECTIVE_NUMERIC_MATCH at best, not source authentication.")


# --- the report ---------------------------------------------------------

def magroot_report() -> dict:
    ref = field_direction_at(40.0, -105.0, 2020.0)
    # a planted body attitude, recovered up to the axis ambiguity
    R_true = rotation_about_axis((0.3, -0.7, 0.6), 0.8)
    measured = R_true.T @ ref
    orient = orientation_from_field(ref, measured)
    target = axial_total_intensity(40.0)
    aliases = root_alias_set(target)
    epoch = field_changes_with_epoch(40.0, -105.0, 2020.0, 2026.0)
    return {
        "what_this_is": (
            "the IGRF root reused as an orientation reference, with its two "
            "alias limits stated in code: attitude from one field vector is "
            "recovered only up to a turn about the field axis, and a field "
            "value is consistent with a locus of locations, not one"),
        "reference_alias": IGRF_ORIENTATION_REFERENCE_A,
        "model_generation": MODEL_GENERATION,
        "source_class": SOURCE_CLASS,
        "field_units": MODEL_UNITS,
        "orientation": {
            "residual_max_abs": orient["residual_max_abs"],
            "recovered_dof": orient["recovered_dof"],
            "undetermined_dof": orient["undetermined_dof"],
            "ambiguity": orient["ambiguity"],
        },
        "alias_set_size": len(aliases),
        "alias_set_has_many_members": len(aliases) > 1,
        "field_changes_with_epoch": epoch["field_moved"],
        "r12_drift_nT_2020_to_2026": epoch["r12_drift_nT"],
        "body_is_dynamo": require_dynamo_body("EARTH")[
            "earth_method_legitimate_here"],
        "epoch_validity_2020": epoch_validity(2020.0).value,
        "refusals_available": [
            "refuse_full_attitude_from_single_vector (always raises)",
            "refuse_root_as_unique_location (always raises)",
            "refuse_field_match_as_source (always raises)",
        ],
        "claim_class": CLAIM_CLASS,
        "measured_here": "nothing",
        "physical_validation": PHYSICAL_VALIDATION,
        "what_this_does_not_say": (
            "It does not measure a field, locate a magnetic root, or decode "
            "a location. The fields here are a declared analytic dipole in "
            "model nT, not an evaluated IGRF field, and no coefficient set "
            "is bundled. Orientation from a single field vector is recovered "
            "only up to rotation about the field axis, so a unique full "
            "attitude is refused. A field value is consistent with a whole "
            "locus of locations, so it is not a unique address. Matching a "
            "modelled value is a RETROSPECTIVE_NUMERIC_MATCH, never source "
            "authentication of a transmitter. Nothing here is measured."),
        "verdict": VERDICT,
    }


__all__ = [
    "MagRootError", "ClaimClass", "CLAIM_CLASSES", "CLAIM_CLASS",
    "SOURCE_CLASS", "PHYSICAL_VALIDATION", "VERDICT", "MODEL_UNITS",
    "IGRF_ORIENTATION_REFERENCE_A", "AXIAL_MOMENT_NT",
    "ORIENTATION_AMBIGUITY", "rotation_about_axis", "shortest_arc_rotation",
    "apply_rotation", "field_vector_at", "field_direction_at",
    "field_changes_with_epoch", "orientation_from_field",
    "refuse_full_attitude_from_single_vector", "axial_total_intensity",
    "root_alias_set", "refuse_root_as_unique_location",
    "refuse_field_match_as_source", "magroot_report",
]
