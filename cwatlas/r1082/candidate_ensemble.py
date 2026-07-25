"""P20 — Candidate map ensemble and agreement surface.

A frozen calibration (P19) still carries *unresolved* profiles: the retained
spatialization families (P18), the Wilkes centroid candidates (P05), and the
epoch profiles. Rather than collapse that ambiguity into one confident pin, this
module produces **one candidate map layer per retained profile combination** and
an **agreement / disagreement surface** across them.

For a query route (a holdout, rendered distinctly from the training anchors):

* each ``(family, wilkes_candidate, epoch)`` combination is one candidate map
  member; its point is the family's mapped route centroid rotated by the frozen
  orientation angle for that family;
* the **agreement surface** clusters the candidate directions (per-component
  variance and angular dispersion across retained families — the "per-cell
  variance"); tightly-clustered members agree, spread members disagree;
* when the anchors cannot select one mapping, the result is the complete bounded
  :data:`CANDIDATE_ALIAS_SET` plus that surface — uncertainty is **never**
  zero-collapsed.

The result conforms to ``schemas/candidate_map_result.schema.json`` and exports
to GeoJSON / KML / JSON. It is a ``CALIBRATED_CANDIDATE`` / ``SOFTWARE_RESULT``
at most — never ``MEASURED`` and never source-origin-validated. Landing near an
unsealed famous-place catalogue is **never** rewarded
(:func:`refuse_famous_place_reward`).
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

import numpy as np

from cwatlas.r1082 import (
    calibration_fit,
    calibration_freeze,
    claims,
    spatialization,
    stonehenge_anchor,
    wilkes,
)
from cwatlas.r1082.partition import build_partition

ENSEMBLE_CODEC_ID = "CW-R1082-CANDMAP"
ENSEMBLE_CODEC_VERSION = "1.0.0"

PROFILE_ID = "EARTH_ROOT_D_V1"

#: Default epoch profiles (decimal years) whose ambiguity is preserved, not
#: collapsed. Declared constants; never wall-clock reads.
DEFAULT_EPOCH_PROFILES: Tuple[float, ...] = (1990.0, 2020.0, 2050.0)

#: Two candidate directions within this angle (radians) are the same cluster.
CLUSTER_TOL_RAD = math.radians(5.0)

#: Declared angular footprint (radians) for a candidate member. NON-ZERO by
#: construction — a candidate is a region, never an invented exact point.
MEMBER_FOOTPRINT_RAD = math.radians(1.0)


class CandidateEnsembleError(ValueError):
    """Raised on a malformed ensemble request."""


def refuse_candidate_as_measured(*_a, **_k) -> None:
    """A candidate map member is not a measured fact."""
    claims.refuse_candidate_as_measured()


def refuse_famous_place_reward(*_a, **_k) -> None:
    """Refuse scoring a model by proximity to an unsealed famous-place list."""
    raise claims.R1082ClaimError(
        "refused: a candidate map is never rewarded for landing near an "
        "unsealed famous-place catalogue. Only the two sealed training anchors "
        "calibrate the map; proximity to any other well-known place is "
        "coincidence, not evidence (no result shopping).")


def _rot_z(theta_rad: float) -> np.ndarray:
    c, s = math.cos(theta_rad), math.sin(theta_rad)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]], dtype=float)


def _unit_to_latlon(v: np.ndarray) -> Tuple[float, float]:
    """Geocentric (lat, lon) in degrees of a unit direction."""
    x, y, z = float(v[0]), float(v[1]), float(v[2])
    lat = math.degrees(math.asin(max(-1.0, min(1.0, z))))
    lon = math.degrees(math.atan2(y, x))
    return (lat, lon)


@dataclass(frozen=True)
class CandidateMember:
    """One candidate map layer for a ``(family, wilkes, epoch)`` combination."""

    family_name: str
    wilkes_candidate_id: str
    epoch_year: float
    theta_deg: float
    unit_vector: Tuple[float, float, float]
    lat_deg: float
    lon_deg: float
    is_training_anchor: bool = False

    def to_dict(self) -> dict:
        return {
            "family_name": self.family_name,
            "wilkes_candidate_id": self.wilkes_candidate_id,
            "epoch_year": self.epoch_year,
            "theta_deg": self.theta_deg,
            "unit_vector": list(self.unit_vector),
            "lat_deg": self.lat_deg,
            "lon_deg": self.lon_deg,
            "is_training_anchor": self.is_training_anchor,
            "footprint_rad": MEMBER_FOOTPRINT_RAD,
        }


@dataclass(frozen=True)
class AgreementSurface:
    """Agreement / disagreement across the candidate directions.

    ``clusters`` groups member directions within :data:`CLUSTER_TOL_RAD`.
    ``per_component_variance`` is the variance of the unit-vector components
    across members (the "per-cell variance"). ``dispersion_rad`` is the maximum
    pairwise angle. ``agreement_fraction`` is the largest cluster's share.
    """

    member_count: int
    cluster_count: int
    clusters: Tuple[Tuple[int, ...], ...]
    per_component_variance: Tuple[float, float, float]
    dispersion_rad: float
    agreement_fraction: float

    def to_dict(self) -> dict:
        return {
            "member_count": self.member_count,
            "cluster_count": self.cluster_count,
            "clusters": [list(c) for c in self.clusters],
            "per_component_variance": list(self.per_component_variance),
            "dispersion_deg": math.degrees(self.dispersion_rad),
            "agreement_fraction": self.agreement_fraction,
            "collapsed_to_point": False,
        }


def _cluster(vectors: Sequence[np.ndarray]) -> Tuple[Tuple[int, ...], ...]:
    """Greedy single-linkage clustering of unit vectors by angular tolerance."""
    clusters: list[list[int]] = []
    reps: list[np.ndarray] = []
    for i, v in enumerate(vectors):
        placed = False
        for k, rep in enumerate(reps):
            ang = math.acos(float(np.clip(np.dot(v, rep), -1.0, 1.0)))
            if ang <= CLUSTER_TOL_RAD:
                clusters[k].append(i)
                placed = True
                break
        if not placed:
            clusters.append([i])
            reps.append(v)
    return tuple(tuple(c) for c in clusters)


def _agreement_surface(members: Sequence[CandidateMember]) -> AgreementSurface:
    vecs = [np.asarray(m.unit_vector, dtype=float) for m in members]
    n = len(vecs)
    clusters = _cluster(vecs)
    arr = np.asarray(vecs, dtype=float)
    var = tuple(float(v) for v in arr.var(axis=0)) if n else (0.0, 0.0, 0.0)
    dispersion = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            ang = math.acos(float(np.clip(np.dot(vecs[i], vecs[j]), -1.0, 1.0)))
            dispersion = max(dispersion, ang)
    largest = max((len(c) for c in clusters), default=0)
    return AgreementSurface(
        member_count=n,
        cluster_count=len(clusters),
        clusters=clusters,
        per_component_variance=var,
        dispersion_rad=dispersion,
        agreement_fraction=(largest / n) if n else 0.0,
    )


@dataclass(frozen=True)
class CandidateMapResult:
    """The bounded candidate map ensemble and its agreement surface."""

    query_route: Tuple[int, ...]
    members: Tuple[CandidateMember, ...]
    training_anchors: Tuple[CandidateMember, ...]
    surface: AgreementSurface
    freeze_hash: str
    result_type: str

    def to_result_dict(self) -> dict:
        """A ``candidate_map_result.schema.json``-conforming document."""
        return {
            "result_type": self.result_type,
            "profile_id": PROFILE_ID,
            "input": {
                "query_route": list(self.query_route),
                "codec_id": ENSEMBLE_CODEC_ID,
                "codec_version": ENSEMBLE_CODEC_VERSION,
                "epoch_profiles_unresolved": True,
            },
            "geometry": [m.to_dict() for m in self.members],
            "uncertainty": {
                "representation": "ANGULAR_DISPERSION_ACROSS_RETAINED_FAMILIES",
                "agreement_surface": self.surface.to_dict(),
                "collapsed_to_point": False,
            },
            "receipt": {
                "freeze_hash": self.freeze_hash,
                "training_anchors": [a.to_dict() for a in self.training_anchors],
                "evidence_class":
                    claims.EvidenceClass.CALIBRATED_CANDIDATE.value,
                "result_class": self.result_type,
                "measured_here": "nothing",
                "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
                "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
                "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
                "famous_place_proximity_rewarded": False,
            },
        }

    def to_geojson(self) -> dict:
        """A GeoJSON FeatureCollection of candidate members and anchors."""
        features = []
        for m in list(self.members) + list(self.training_anchors):
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point",
                             "coordinates": [m.lon_deg, m.lat_deg]},
                "properties": {
                    "family_name": m.family_name,
                    "wilkes_candidate_id": m.wilkes_candidate_id,
                    "epoch_year": m.epoch_year,
                    "is_training_anchor": m.is_training_anchor,
                    "evidence_class":
                        claims.EvidenceClass.CALIBRATED_CANDIDATE.value,
                },
            })
        return {"type": "FeatureCollection", "features": features}

    def to_kml(self) -> str:
        """A minimal KML document of the candidate members and anchors."""
        marks = []
        for m in list(self.members) + list(self.training_anchors):
            tag = "TRAINING_ANCHOR" if m.is_training_anchor else "CANDIDATE"
            marks.append(
                f"<Placemark><name>{tag}:{m.family_name}</name>"
                f"<Point><coordinates>{m.lon_deg},{m.lat_deg},0"
                f"</coordinates></Point></Placemark>")
        return ("<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
                "<kml xmlns=\"http://www.opengis.net/kml/2.2\"><Document>"
                + "".join(marks) + "</Document></kml>")

    def to_json(self) -> str:
        """The result document as a deterministic JSON string."""
        return json.dumps(self.to_result_dict(), sort_keys=True,
                          separators=(",", ":"), default=float)


def _theta_by_family(frozen: calibration_freeze.FrozenCalibration) -> dict:
    return dict(frozen.fitted_parameters
                .get("orientation_theta_deg_by_family", {}))


def build_candidate_map(
        query_route: Sequence[int],
        frozen: calibration_freeze.FrozenCalibration,
        *,
        anchor: Optional[stonehenge_anchor.StonehengeAnchor] = None,
        ensemble: Optional[wilkes.WilkesEnsemble] = None,
        epoch_profiles: Sequence[float] = DEFAULT_EPOCH_PROFILES,
        ico=None) -> CandidateMapResult:
    """Produce candidate map layers across the unresolved profiles.

    One member per ``(retained_family, wilkes_candidate, epoch)`` combination.
    The candidate direction is the family's mapped route centroid rotated by the
    frozen orientation angle for that family. Training anchors (Wilkes centroid
    and Stonehenge) are rendered as distinct members flagged
    ``is_training_anchor``. The result never collapses uncertainty.
    """
    if anchor is None:
        anchor = stonehenge_anchor.build_anchor()
    if ensemble is None:
        ensemble = wilkes.default_ensemble()
    if ico is None:
        ico = build_partition().ico

    route = tuple(int(t) for t in query_route)
    theta_by_family = _theta_by_family(frozen)
    retained = [n for n in frozen.retained_families if n in theta_by_family]
    if not retained:
        raise CandidateEnsembleError(
            "the frozen calibration retained no families with fitted angles")

    members: list[CandidateMember] = []
    for fam_name in retained:
        fam = spatialization.get_family(fam_name)
        theta = math.radians(theta_by_family[fam_name])
        base = fam.map_route(route, ico=ico).centroid
        base = base / np.linalg.norm(base)
        pt = _rot_z(theta) @ base
        pt = pt / np.linalg.norm(pt)
        lat, lon = _unit_to_latlon(pt)
        for wp in ensemble.profiles:
            for epoch in epoch_profiles:
                members.append(CandidateMember(
                    family_name=fam_name,
                    wilkes_candidate_id=wp.candidate_id,
                    epoch_year=float(epoch),
                    theta_deg=theta_by_family[fam_name],
                    unit_vector=(float(pt[0]), float(pt[1]), float(pt[2])),
                    lat_deg=lat,
                    lon_deg=lon,
                ))

    # Training anchors rendered distinctly from holdouts (required work #3).
    wl_dir = ensemble.selected().centroid_unit_vector()
    wl_lat, wl_lon = _unit_to_latlon(wl_dir)
    st_dir = anchor.anchor_unit_vector()
    st_lat, st_lon = _unit_to_latlon(st_dir)
    training = (
        CandidateMember(
            family_name="WILKES_FIXED_ROOT",
            wilkes_candidate_id=ensemble.selected_id,
            epoch_year=float(epoch_profiles[0]),
            theta_deg=0.0,
            unit_vector=(float(wl_dir[0]), float(wl_dir[1]), float(wl_dir[2])),
            lat_deg=wl_lat, lon_deg=wl_lon, is_training_anchor=True),
        CandidateMember(
            family_name=anchor.fixture_id,
            wilkes_candidate_id="N/A",
            epoch_year=float(epoch_profiles[0]),
            theta_deg=0.0,
            unit_vector=(float(st_dir[0]), float(st_dir[1]), float(st_dir[2])),
            lat_deg=st_lat, lon_deg=st_lon, is_training_anchor=True),
    )

    surface = _agreement_surface(members)
    # Distinct candidate clusters -> the anchors cannot select one mapping, so
    # the result is the complete bounded alias set; a single cluster is still a
    # calibrated candidate region (never a measured point).
    result_type = (claims.ResultClass.CANDIDATE_ALIAS_SET.value
                   if surface.cluster_count > 1
                   else claims.ResultClass.CANDIDATE_CALIBRATED_POINT.value)
    return CandidateMapResult(
        query_route=route,
        members=tuple(members),
        training_anchors=training,
        surface=surface,
        freeze_hash=frozen.freeze_hash,
        result_type=result_type,
    )


def candidate_ensemble_report() -> dict:
    """P20 declaration receipt. Ambiguity preserved; nothing measured."""
    fit = calibration_fit.fit_all()
    frozen = calibration_freeze.freeze_calibration(fit)
    result = build_candidate_map((7, 7, 7, 7, 7), frozen)
    return {
        "phase_id": "P20",
        "tranche": "T05",
        "what_this_is": (
            "the candidate map ensemble and agreement surface: one candidate "
            "layer per retained family x Wilkes centroid candidate x epoch "
            "profile, with a per-cell variance / angular dispersion surface; the "
            "complete bounded alias set is returned instead of collapsing "
            "uncertainty."),
        "codec_id": ENSEMBLE_CODEC_ID,
        "codec_version": ENSEMBLE_CODEC_VERSION,
        "profile_id": PROFILE_ID,
        "member_count": result.surface.member_count,
        "cluster_count": result.surface.cluster_count,
        "dispersion_deg": math.degrees(result.surface.dispersion_rad),
        "agreement_fraction": result.surface.agreement_fraction,
        "result_type": result.result_type,
        "uncertainty_collapsed_to_point": False,
        "training_anchors_rendered_distinctly": True,
        "famous_place_proximity_rewarded": False,
        "exports": ["GeoJSON", "KML", "JSON"],
        "evidence_class": claims.EvidenceClass.CALIBRATED_CANDIDATE.value,
        "max_evidence": claims.MAX_CANDIDATE_EVIDENCE.value,
        "result_class": claims.ResultClass.CANDIDATE_ALIAS_SET.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
        "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
        "verdict": "CANDIDATE_MAP_ENSEMBLE_ALIAS_SET_WITH_AGREEMENT_SURFACE",
        "what_this_does_not_say": (
            "Every layer is a CALIBRATED_CANDIDATE / SOFTWARE_RESULT under a "
            "frozen calibration. The ensemble spreads, not collapses, the "
            "unresolved profiles; it is not a measured location, and landing "
            "near a famous place is never rewarded or treated as evidence."),
    }
