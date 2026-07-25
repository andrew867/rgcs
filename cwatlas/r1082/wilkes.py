"""P05 — Wilkes fixed-anchor profile registry (the FIXED spatial layer).

The locked ``EARTH_ROOT_D_V1`` root's *fixed* spatial anchor is the Wilkes
Land gravity-anomaly centroid (Locked Decisions §6). This module represents it
not as a single invented point but as a **versioned centroid-and-uncertainty
profile** — and, because multiple centroids are defensible, as an **ensemble**
of such profiles inside one locked two-layer root family.

Governance:

* The centroid is an ``OPERATOR_SELECTION`` / conventional value. It is *not*
  a measured coordinate. A source/anchor pin is not a validated physical fact.
* Uncertainty is **never collapsed to a point**: a profile with zero-area
  uncertainty is refused. Ambiguity stays a region, not invented precision.
* The selected centroid direction is bound to the root icosahedral face centre
  by reusing the green ``cwatlas`` engine (``geodesy`` + ``icosahedron``).

Deterministic; every value is passed in or declared. No wall-clock, no private
reads, synthetic/public constants only.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Tuple

import numpy as np

from cwatlas import geodesy, icosahedron
from cwatlas.r1082 import claims

#: The registry / profile-version identity for the Wilkes fixed-anchor layer.
WILKES_PROFILE_VERSION = "WILKES_CENTROID_ENSEMBLE_V1"

#: A declared placeholder centroid in the Wilkes Land region. This is a
#: CONVENTIONAL operator selection (OPERATOR_SELECTION), not a measured
#: gravity-anomaly centroid. Latitude is negative (Southern Hemisphere).
WILKES_PLACEHOLDER_LAT_DEG = -66.5
WILKES_PLACEHOLDER_LON_DEG = 135.0


class WilkesError(ValueError):
    """Raised on an invalid Wilkes profile (e.g. collapsed uncertainty)."""


def refuse_point_uncertainty(*_a, **_k) -> None:
    """A Wilkes profile whose uncertainty collapses to a point is refused."""
    raise WilkesError(
        "refused: the Wilkes fixed anchor is a centroid-and-uncertainty "
        "profile, not a point. Collapsing its uncertainty to zero area asserts "
        "precision the gravity-anomaly centroid does not support. Ambiguity is "
        "a region, never invented precision.")


@dataclass(frozen=True)
class WilkesProfile:
    """A single candidate Wilkes centroid with its covariance uncertainty.

    ``centroid_lat_deg`` / ``centroid_lon_deg`` are a declared, conventional
    operator selection. ``cov_deg2`` is a 2x2 covariance (in degrees^2) over
    (latitude, longitude) describing the centroid's uncertainty; it must be a
    finite, symmetric, positive-definite matrix — a zero (point) covariance is
    refused. ``candidate_id`` names the candidate within the ensemble.
    """

    candidate_id: str
    centroid_lat_deg: float
    centroid_lon_deg: float
    cov_deg2: Tuple[Tuple[float, float], Tuple[float, float]]
    profile_version: str = WILKES_PROFILE_VERSION
    selection_basis: str = claims.EvidenceClass.OPERATOR_SELECTION.value
    note: str = "conventional placeholder centroid; not a measured value"

    def __post_init__(self) -> None:
        if not self.candidate_id:
            raise WilkesError("candidate_id must be a non-empty string.")
        if not (-90.0 <= self.centroid_lat_deg <= 90.0):
            raise WilkesError(
                f"centroid_lat_deg out of range: {self.centroid_lat_deg!r}.")
        if not (-180.0 <= self.centroid_lon_deg <= 180.0):
            raise WilkesError(
                f"centroid_lon_deg out of range: {self.centroid_lon_deg!r}.")
        cov = np.asarray(self.cov_deg2, dtype=float)
        if cov.shape != (2, 2) or not np.all(np.isfinite(cov)):
            raise WilkesError("cov_deg2 must be a finite 2x2 matrix.")
        if not np.allclose(cov, cov.T):
            raise WilkesError("cov_deg2 must be symmetric.")
        eigvals = np.linalg.eigvalsh(cov)
        # Uncertainty never collapsed to a point: a non-positive eigenvalue is
        # a zero-width (point) region and is refused.
        if float(np.min(eigvals)) <= 0.0:
            refuse_point_uncertainty()

    def covariance_matrix(self) -> np.ndarray:
        """The 2x2 covariance as a numpy array (degrees^2)."""
        return np.asarray(self.cov_deg2, dtype=float)

    def uncertainty_area_deg2(self) -> float:
        """1-sigma covariance-ellipse area (deg^2): pi * sqrt(det Cov)."""
        det = float(np.linalg.det(self.covariance_matrix()))
        return float(np.pi * np.sqrt(max(det, 0.0)))

    def centroid_unit_vector(self) -> np.ndarray:
        """The centroid direction as an ECEF unit vector (height 0, WGS84)."""
        x, y, z = geodesy.geodetic_to_ecef(
            self.centroid_lat_deg, self.centroid_lon_deg, 0.0)
        v = np.array([x, y, z], dtype=float)
        return v / np.linalg.norm(v)

    def to_fixed_anchor_dict(self) -> dict:
        """The ``fixed_anchor`` object for ``earth_root_profile.schema.json``."""
        return {
            "type": "WILKES_GRAVITY_ANOMALY_CENTROID",
            "profile_version": self.profile_version,
            "candidate_id": self.candidate_id,
            "centroid_deg": [self.centroid_lat_deg, self.centroid_lon_deg],
            "selection_basis": self.selection_basis,
            "uncertainty": {
                "representation": "COVARIANCE_2X2_DEG2",
                "cov_deg2": [list(row) for row in self.cov_deg2],
                "area_deg2": self.uncertainty_area_deg2(),
                "collapsed_to_point": False,
                "must_be_versioned": True,
            },
        }

    def profile_hash(self) -> str:
        """A stable content hash of this candidate profile."""
        blob = json.dumps(self.to_fixed_anchor_dict(), sort_keys=True,
                          separators=(",", ":"))
        return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class WilkesEnsemble:
    """An ensemble of defensible Wilkes centroid candidates (P05 §2, §4).

    The ensemble returns *all* candidates rather than selecting the prettiest
    downstream map. A ``selected_id`` names the operator-selected candidate for
    binding to the root face centre, without discarding the alternatives.
    """

    profiles: Tuple[WilkesProfile, ...]
    selected_id: str
    profile_version: str = WILKES_PROFILE_VERSION

    def __post_init__(self) -> None:
        if not self.profiles:
            raise WilkesError("a Wilkes ensemble needs at least one candidate.")
        ids = [p.candidate_id for p in self.profiles]
        if len(set(ids)) != len(ids):
            raise WilkesError("candidate ids must be unique in the ensemble.")
        if self.selected_id not in ids:
            raise WilkesError(
                f"selected_id {self.selected_id!r} is not in the ensemble "
                f"{ids!r}.")

    def selected(self) -> WilkesProfile:
        """The operator-selected candidate profile."""
        for p in self.profiles:
            if p.candidate_id == self.selected_id:
                return p
        raise WilkesError("selected candidate not found (unreachable).")

    def ensemble_hash(self) -> str:
        """A stable hash over every candidate plus the selection."""
        parts = [p.profile_hash() for p in self.profiles]
        blob = json.dumps({"version": self.profile_version,
                          "selected": self.selected_id, "candidates": parts},
                         sort_keys=True, separators=(",", ":"))
        return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def root_face_id(self) -> int:
        """The icosahedral face id of the *selected* centroid direction.

        Binds the selected Wilkes centroid to the root face centre by reusing
        the green ``cwatlas.icosahedron`` classifier (Locked Decisions §5).
        """
        ico = icosahedron.build_icosahedron()
        return icosahedron.classify_point(ico, self.selected().centroid_unit_vector())

    def root_face_center_direction(self) -> np.ndarray:
        """The unit direction of the root icosahedral face centre."""
        ico = icosahedron.build_icosahedron()
        return ico.face_normals[self.root_face_id()]


def default_ensemble() -> WilkesEnsemble:
    """The declared default Wilkes ensemble.

    Three defensible candidate centroids in the Wilkes Land region, each with
    a non-collapsed covariance. All values are CONVENTIONAL operator
    selections — not measured gravity-anomaly centroids.
    """
    profiles = (
        WilkesProfile(
            candidate_id="WILKES_A_PLACEHOLDER",
            centroid_lat_deg=WILKES_PLACEHOLDER_LAT_DEG,
            centroid_lon_deg=WILKES_PLACEHOLDER_LON_DEG,
            cov_deg2=((4.0, 0.0), (0.0, 9.0)),
        ),
        WilkesProfile(
            candidate_id="WILKES_B_PLACEHOLDER",
            centroid_lat_deg=-67.5,
            centroid_lon_deg=139.0,
            cov_deg2=((6.25, 1.0), (1.0, 12.25)),
        ),
        WilkesProfile(
            candidate_id="WILKES_C_PLACEHOLDER",
            centroid_lat_deg=-65.0,
            centroid_lon_deg=131.0,
            cov_deg2=((5.0, -0.5), (-0.5, 8.0)),
        ),
    )
    return WilkesEnsemble(profiles=profiles, selected_id="WILKES_A_PLACEHOLDER")


def wilkes_report() -> dict:
    """P05 declaration receipt. Nothing measured; uncertainty never a point."""
    ens = default_ensemble()
    return {
        "phase_id": "P05",
        "tranche": "T02",
        "what_this_is": (
            "the FIXED spatial anchor of EARTH_ROOT_D_V1 — the Wilkes Land "
            "gravity-anomaly centroid as a versioned centroid-and-uncertainty "
            "profile ensemble bound to the root icosahedral face centre."),
        "profile_version": WILKES_PROFILE_VERSION,
        "candidate_count": len(ens.profiles),
        "selected_candidate": ens.selected_id,
        "root_face_id": ens.root_face_id(),
        "ensemble_hash": ens.ensemble_hash(),
        "evidence_class": claims.EvidenceClass.OPERATOR_SELECTION.value,
        "uncertainty_collapsed_to_point": False,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
        "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
        "verdict": "WILKES_FIXED_ANCHOR_VERSIONED_ENSEMBLE_NO_INVENTED_PRECISION",
        "what_this_does_not_say": (
            "The placeholder centroid is a conventional operator selection, "
            "not a measured gravity-anomaly centroid or a validated physical "
            "coordinate."),
    }
