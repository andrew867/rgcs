"""P06 — Shell-resolved South Atlantic Anomaly magnetic minimum (DYNAMIC layer).

The locked ``EARTH_ROOT_D_V1`` root's *dynamic* phase-zero direction is the
South Atlantic Anomaly (SAA) magnetic-field-magnitude minimum, evaluated at the
packet's encoded **epoch** and its body-relative **shell radius** (Locked
Decisions §7). This module is a simple, deterministic parametric SAA-minimum
model ``f(epoch, radius) -> direction`` with the two dependencies the contract
demands:

* the minimum **drifts with epoch** (the SAA migrates westward over years);
* the minimum **shifts with the shell radius** (its position depends on the
  body-relative altitude the shell supplies).

The **shell supplies the radius**. Altitude is therefore never "missing" when a
shell profile is present — attempting to report it as missing is refused by
``cwatlas.r1082.claims.refuse_altitude_missing_when_shell_present``.

Governance: the model is ``DERIVED_MATHEMATICS`` over an ``OPERATOR_SELECTION``
parameter set. It measures nothing and validates nothing physical. Its output
carries uncertainty (a region), not invented precision. Every value is passed
in; no wall-clock is read.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np

from cwatlas import geodesy, shells, uncertainty
from cwatlas.r1082 import claims

#: Field-model identity (a versioned parametric adapter, not IGRF/WMM data).
FIELD_MODEL_ID = "CW-SAA-PARAMETRIC"
FIELD_MODEL_VERSION = "1.0.0"

#: Validity range of the parametric model (declared).
EPOCH_MIN_YEAR = 1900.0
EPOCH_MAX_YEAR = 2100.0
RADIUS_MIN_M = 3.0e6
RADIUS_MAX_M = 5.0e7

#: Reference epoch / radius the linear model is expanded about.
EPOCH0_YEAR = 2020.0
#: Reference radius: WGS84 mean radius plus a 400 km LEO band.
R0_M = 6371000.0 + 400000.0

#: SAA-minimum reference position (deg) and its declared drift/shift rates.
#: These are CONVENTIONAL operator selections, not measured field values.
LAT0_DEG = -25.0
LON0_DEG = -50.0
DLAT_DT_DEG_PER_YEAR = 0.20      # SAA migrates slowly poleward-ish (declared)
DLON_DT_DEG_PER_YEAR = -0.30     # SAA drifts westward (declared)
DLAT_DR_DEG_PER_M = 1.0e-6       # 1 deg per 1000 km of radius (declared)
DLON_DR_DEG_PER_M = -2.0e-6      # 2 deg per 1000 km of radius (declared)

#: Reference field magnitude at (EPOCH0, R0) and its declared gradients (nT).
B0_NT = 22000.0
DB_DT_NT_PER_YEAR = -8.0
DB_DR_NT_PER_M = -1.0e-3

#: Nominal body-relative shell radii (metres). DECLARED operator selection —
#: monotonic in shell index, NOT measured altitudes. A shell profile may
#: override these with an explicit ``radius_m``.
NOMINAL_SHELL_RADIUS_M: dict[int, float] = {
    0: 0.0,                       # infinite centre / recursive closure
    1: 1.20e6,                    # core
    2: 3.48e6,                    # mantle
    3: 6.371e6,                   # surface
    4: 6.371e6 + 1.2e4,           # low-aircraft regime
    5: 6.371e6 + 2.0e4,           # higher-aircraft regime
    6: 6.371e6 + 5.0e5,           # satellite-orbit regime
    7: 6.371e6 + 2.0e7,           # high-satellite regime
    8: 4.2e7,                     # equal-pull / effective-potential boundary
}


class SAAError(ValueError):
    """Raised outside the model validity range or on invalid shell input."""


@dataclass(frozen=True)
class SAAMinimum:
    """The resolved SAA field-magnitude minimum at one (epoch, radius).

    ``direction_ecef`` is the unit ECEF direction of the minimum. It carries an
    uncertainty region (never a point) and a result class — a candidate region,
    not a measured fact.
    """

    epoch_year: float
    radius_m: float
    latitude_deg: float
    longitude_deg: float
    field_nt: float
    direction_ecef: Tuple[float, float, float]
    uncertainty_region: uncertainty.ErrorRegion
    field_model: str = FIELD_MODEL_ID
    field_model_version: str = FIELD_MODEL_VERSION
    result_class: str = claims.ResultClass.CANDIDATE_REGION.value
    evidence_class: str = claims.EvidenceClass.DERIVED_MATHEMATICS.value


def within_validity(epoch_year: float, radius_m: float) -> bool:
    """Whether ``(epoch, radius)`` is inside the declared model validity."""
    return (EPOCH_MIN_YEAR <= epoch_year <= EPOCH_MAX_YEAR
            and RADIUS_MIN_M <= radius_m <= RADIUS_MAX_M)


def _direction_ecef(lat_deg: float, lon_deg: float) -> np.ndarray:
    x, y, z = geodesy.geodetic_to_ecef(lat_deg, lon_deg, 0.0)
    v = np.array([x, y, z], dtype=float)
    return v / np.linalg.norm(v)


def resolve(epoch_year: float, radius_m: float) -> SAAMinimum:
    """Resolve the SAA minimum at an epoch and a body-relative radius.

    The position drifts with ``epoch_year`` and shifts with ``radius_m`` (both
    dependencies are live — this is the POWER property). Refuses inputs outside
    the declared validity range rather than extrapolating silently.
    """
    if not (np.isfinite(epoch_year) and np.isfinite(radius_m)):
        raise SAAError("epoch_year and radius_m must be finite.")
    if not within_validity(epoch_year, radius_m):
        raise SAAError(
            f"outside model validity: epoch {epoch_year} must be in "
            f"[{EPOCH_MIN_YEAR}, {EPOCH_MAX_YEAR}] and radius {radius_m} in "
            f"[{RADIUS_MIN_M}, {RADIUS_MAX_M}].")

    dt = epoch_year - EPOCH0_YEAR
    dr = radius_m - R0_M
    lat = LAT0_DEG + DLAT_DT_DEG_PER_YEAR * dt + DLAT_DR_DEG_PER_M * dr
    lon = LON0_DEG + DLON_DT_DEG_PER_YEAR * dt + DLON_DR_DEG_PER_M * dr
    # Keep the modelled minimum on the sphere; clamp latitude, wrap longitude.
    lat = max(-89.0, min(89.0, lat))
    lon = ((lon + 180.0) % 360.0) - 180.0
    field = B0_NT + DB_DT_NT_PER_YEAR * dt + DB_DR_NT_PER_M * dr

    direction = _direction_ecef(lat, lon)
    # A modelled minimum is a candidate region, not invented precision: give it
    # an explicit non-zero uncertainty footprint.
    region = uncertainty.propagate_circle(
        center=(lat, lon),
        input_sigma_m=1.0e5,       # 100 km modelling sigma (declared)
        quantization_m=0.0,
        cell_size_m=1.0e4,
        justification="SAA parametric-model uncertainty (declared)",
    )
    return SAAMinimum(
        epoch_year=float(epoch_year),
        radius_m=float(radius_m),
        latitude_deg=float(lat),
        longitude_deg=float(lon),
        field_nt=float(field),
        direction_ecef=(float(direction[0]), float(direction[1]),
                        float(direction[2])),
        uncertainty_region=region,
    )


def radius_from_shell(shell_index: int, body_id: str = "EARTH",
                      radius_m: Optional[float] = None) -> float:
    """Return the body-relative radius the shell supplies.

    Validates the shell index through the green ``cwatlas.shells`` registry. An
    explicit ``radius_m`` (from a shell profile) overrides the nominal table.
    Because the shell supplies the radius, altitude is *never* missing here.
    """
    shells.make_shell_state(shell_index, body_id)  # refuses unknown index
    if radius_m is not None:
        if not np.isfinite(radius_m) or radius_m <= 0.0:
            raise SAAError("radius_m must be positive and finite.")
        return float(radius_m)
    return float(NOMINAL_SHELL_RADIUS_M[shell_index])


def resolve_from_shell(epoch_year: float, shell_index: int,
                       body_id: str = "EARTH",
                       radius_m: Optional[float] = None) -> SAAMinimum:
    """Resolve the SAA minimum with the radius supplied by the shell.

    This is the contract path: the shell (not a separate altitude request)
    provides the radius. See :func:`radius_from_shell`.
    """
    radius = radius_from_shell(shell_index, body_id=body_id, radius_m=radius_m)
    return resolve(epoch_year, radius)


def refuse_altitude_missing(shell_state) -> None:
    """Refuse any claim that altitude is missing while a shell is present.

    Delegates to the locked-root refusal so the red team indexes it in one
    place. The shell supplies the radius; altitude is present via the shell.
    """
    claims.refuse_altitude_missing_when_shell_present(shell_state=shell_state)


def saa_report() -> dict:
    """P06 declaration receipt. Both dependencies live; nothing measured."""
    return {
        "phase_id": "P06",
        "tranche": "T02",
        "what_this_is": (
            "the DYNAMIC phase-zero direction of EARTH_ROOT_D_V1 — a "
            "deterministic parametric SAA field-minimum model f(epoch, radius) "
            "whose position drifts with epoch and shifts with the "
            "shell-supplied radius."),
        "field_model": FIELD_MODEL_ID,
        "field_model_version": FIELD_MODEL_VERSION,
        "epoch_validity_year": [EPOCH_MIN_YEAR, EPOCH_MAX_YEAR],
        "radius_validity_m": [RADIUS_MIN_M, RADIUS_MAX_M],
        "drifts_with_epoch": True,
        "shifts_with_radius": True,
        "shell_supplies_radius": True,
        "altitude_missing_when_shell_present": (
            "REFUSED (shell supplies the radius)"),
        "evidence_class": claims.EvidenceClass.DERIVED_MATHEMATICS.value,
        "result_class": claims.ResultClass.CANDIDATE_REGION.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
        "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
        "verdict": "SAA_SHELL_RESOLVED_MINIMUM_EPOCH_AND_RADIUS_DEPENDENT",
        "what_this_does_not_say": (
            "The parametric minimum is a modelled candidate region, not a "
            "measured geomagnetic field value or a validated coordinate."),
    }
