"""P08 — Root certificate and time-varying frame API.

Assembles the complete locked ``EARTH_ROOT_D_V1`` two-layer root into one typed,
cacheable, auditable :class:`RootCertificate`:

* the **FIXED** Wilkes gravity-anomaly centroid ensemble (P05), bound to the
  root icosahedral face centre;
* the **DYNAMIC** SAA magnetic minimum (P06) resolved at the packet's encoded
  ``(epoch, shell)``;
* the **South-Up** orientation with viewpoint-safe handedness (P07).

Every input and every derived basis vector is hashed. The frame API
:func:`resolve` is deterministic and **cacheable by (epoch, shell)** — the cache
key records the model version, an epoch bucket, and the shell profile, while the
certificate preserves the *exact* requested epoch and radius (no erasure).
Requests outside the SAA model validity return a typed **refusal**.

Governance: the certificate is a ``SOFTWARE_RESULT`` over ``OPERATOR_SELECTION``
and ``DERIVED_MATHEMATICS`` inputs. It measures nothing and validates no source
origin. Every value is passed in; no wall-clock is read.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple, Union

import numpy as np

from cwatlas.r1082 import claims, saa, southup, wilkes

#: The profile this certificate realizes, and the certificate schema version.
PROFILE_ID = "EARTH_ROOT_D_V1"
CERTIFICATE_VERSION = "1.0.0"

#: Epoch-bucket resolution (years) used only for the cache key label. The
#: certificate always keeps the exact requested epoch.
EPOCH_BUCKET_YEARS = 0.1


def _hash_obj(obj) -> str:
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":"),
                     default=float)
    return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _epoch_bucket(epoch_year: float) -> float:
    return round(round(epoch_year / EPOCH_BUCKET_YEARS) * EPOCH_BUCKET_YEARS, 6)


@dataclass(frozen=True)
class RootRefusal:
    """A typed refusal returned for a request outside model validity."""

    epoch_year: float
    shell_index: int
    radius_m: Optional[float]
    reason: str
    result_class: str = claims.ResultClass.INVALID.value

    def is_refusal(self) -> bool:
        return True


@dataclass(frozen=True)
class RootCertificate:
    """The complete fixed-plus-dynamic root at one ``(epoch, shell)``."""

    profile_id: str
    certificate_version: str
    epoch_year: float
    epoch_bucket: float
    shell_index: int
    radius_m: float
    # FIXED layer
    wilkes_selected_id: str
    wilkes_ensemble_hash: str
    root_face_id: int
    root_face_center_direction: Tuple[float, float, float]
    # DYNAMIC layer
    saa: saa.SAAMinimum
    # Orientation
    orientation_pole: str
    orientation_viewpoint: str
    orientation_positive_rotation: str
    south_up_basis: Tuple[Tuple[float, float, float], ...]
    # Audit
    input_hash: str
    basis_hash: str
    certificate_hash: str
    result_class: str = claims.ResultClass.CANDIDATE_CALIBRATED_POINT.value
    evidence_class: str = claims.EvidenceClass.SOFTWARE_RESULT.value

    def is_refusal(self) -> bool:
        return False

    def to_earth_root_profile_dict(self) -> dict:
        """A full document conforming to ``earth_root_profile.schema.json``."""
        selected = None
        for p in _ensemble().profiles:
            if p.candidate_id == self.wilkes_selected_id:
                selected = p
                break
        fixed_anchor = (selected.to_fixed_anchor_dict() if selected is not None
                        else {"type": "WILKES_GRAVITY_ANOMALY_CENTROID",
                              "profile_version": wilkes.WILKES_PROFILE_VERSION,
                              "uncertainty": {}})
        return {
            "profile_id": PROFILE_ID,
            "origin": "EARTH_CENTER_OF_MASS",
            "axis": "MEAN_ROTATION_AXIS_SOUTH_UP",
            "partition": "SPHERICAL_ICOSAHEDRON_20_FACES",
            "dual_graph": "DODECAHEDRAL_20_VERTEX_DUAL",
            "root_feature": "ICOSAHEDRAL_FACE_CENTER",
            "fixed_anchor": fixed_anchor,
            "dynamic_zero": {
                "type": "SAA_FIELD_MAGNITUDE_MINIMUM",
                "field_model": self.saa.field_model,
                "field_model_version": self.saa.field_model_version,
                "epoch": {"year": self.epoch_year,
                          "bucket": self.epoch_bucket},
                "shell": {"index": self.shell_index,
                          "radius_m": self.radius_m},
                "minimum_deg": [self.saa.latitude_deg, self.saa.longitude_deg],
            },
            "orientation": {
                "pole": self.orientation_pole,
                "viewpoint": self.orientation_viewpoint,
                "positive_rotation": self.orientation_positive_rotation,
            },
            "root_face_id": self.root_face_id,
            "certificate_hash": self.certificate_hash,
        }


#: Deterministic frame cache, keyed by (model version, epoch bucket, shell,
#: radius, wilkes ensemble hash). Exact requested values are kept in the value.
_CACHE: Dict[Tuple, RootCertificate] = {}


def _ensemble() -> wilkes.WilkesEnsemble:
    return wilkes.default_ensemble()


def cache_clear() -> None:
    """Clear the frame cache (deterministic; test/maintenance use)."""
    _CACHE.clear()


def cache_size() -> int:
    return len(_CACHE)


def _cache_key(epoch_year: float, shell_index: int, radius_m: float,
               ensemble_hash: str) -> Tuple:
    return (saa.FIELD_MODEL_VERSION, _epoch_bucket(epoch_year),
            round(epoch_year, 9), shell_index, round(radius_m, 6),
            ensemble_hash)


def resolve(epoch_year: float, shell_index: int, *, body_id: str = "EARTH",
            radius_m: Optional[float] = None,
            ensemble: Optional[wilkes.WilkesEnsemble] = None) -> RootCertificate:
    """Resolve the root frame at ``(epoch, shell)`` — the time-varying API.

    Deterministic and cached by (epoch, shell). The shell supplies the radius
    (P06). Raises :class:`saa.SAAError` outside the model validity range; use
    :func:`resolve_or_refuse` for a typed refusal instead of an exception.
    """
    ens = ensemble if ensemble is not None else _ensemble()
    radius = saa.radius_from_shell(shell_index, body_id=body_id,
                                   radius_m=radius_m)
    key = _cache_key(epoch_year, shell_index, radius, ens.ensemble_hash())
    cached = _CACHE.get(key)
    if cached is not None:
        return cached

    minimum = saa.resolve(epoch_year, radius)  # raises outside validity

    face_id = ens.root_face_id()
    face_dir = ens.root_face_center_direction()
    basis = southup.south_up_basis()

    input_payload = {
        "profile_id": PROFILE_ID,
        "certificate_version": CERTIFICATE_VERSION,
        "epoch_year": epoch_year,
        "shell_index": shell_index,
        "radius_m": radius,
        "field_model_version": saa.FIELD_MODEL_VERSION,
        "wilkes_ensemble_hash": ens.ensemble_hash(),
        "wilkes_selected_id": ens.selected_id,
    }
    basis_payload = {
        "south_up_basis": basis.tolist(),
        "root_face_center_direction": [float(c) for c in face_dir],
        "saa_direction_ecef": list(minimum.direction_ecef),
    }
    input_hash = _hash_obj(input_payload)
    basis_hash = _hash_obj(basis_payload)
    certificate_hash = _hash_obj({"input": input_payload, "basis": basis_payload,
                                  "saa_field_nt": minimum.field_nt,
                                  "saa_deg": [minimum.latitude_deg,
                                              minimum.longitude_deg]})

    cert = RootCertificate(
        profile_id=PROFILE_ID,
        certificate_version=CERTIFICATE_VERSION,
        epoch_year=float(epoch_year),
        epoch_bucket=_epoch_bucket(epoch_year),
        shell_index=int(shell_index),
        radius_m=float(radius),
        wilkes_selected_id=ens.selected_id,
        wilkes_ensemble_hash=ens.ensemble_hash(),
        root_face_id=int(face_id),
        root_face_center_direction=(float(face_dir[0]), float(face_dir[1]),
                                    float(face_dir[2])),
        saa=minimum,
        orientation_pole=southup.POLE,
        orientation_viewpoint=southup.POSITIVE_ROTATION_VIEWPOINT,
        orientation_positive_rotation=southup.POSITIVE_ROTATION,
        south_up_basis=tuple(tuple(float(v) for v in row) for row in basis),
        input_hash=input_hash,
        basis_hash=basis_hash,
        certificate_hash=certificate_hash,
    )
    _CACHE[key] = cert
    return cert


def resolve_or_refuse(epoch_year: float, shell_index: int, *,
                      body_id: str = "EARTH", radius_m: Optional[float] = None,
                      ensemble: Optional[wilkes.WilkesEnsemble] = None,
                      ) -> Union[RootCertificate, RootRefusal]:
    """Like :func:`resolve` but returns a typed refusal outside validity."""
    try:
        return resolve(epoch_year, shell_index, body_id=body_id,
                       radius_m=radius_m, ensemble=ensemble)
    except saa.SAAError as exc:
        try:
            radius = saa.radius_from_shell(shell_index, body_id=body_id,
                                           radius_m=radius_m)
        except saa.SAAError:
            radius = None
        return RootRefusal(epoch_year=float(epoch_year),
                          shell_index=int(shell_index), radius_m=radius,
                          reason=str(exc))


def root_certificate_report() -> dict:
    """P08 declaration receipt. Deterministic, cacheable, nothing measured."""
    return {
        "phase_id": "P08",
        "tranche": "T02",
        "what_this_is": (
            "the complete fixed-plus-dynamic EARTH_ROOT_D_V1 root as one "
            "typed, hashed, cacheable RootCertificate, with a time-varying "
            "frame API resolve(epoch, shell)."),
        "profile_id": PROFILE_ID,
        "certificate_version": CERTIFICATE_VERSION,
        "layers": {
            "fixed": "Wilkes gravity-anomaly centroid ensemble (P05)",
            "dynamic": "SAA field-minimum at (epoch, shell) (P06)",
            "orientation": "South-Up, viewpoint-safe handedness (P07)",
        },
        "cache_key": ["field_model_version", "epoch_bucket", "epoch_exact",
                      "shell_index", "radius_m", "wilkes_ensemble_hash"],
        "epoch_bucket_years": EPOCH_BUCKET_YEARS,
        "exact_values_preserved": True,
        "refuses_outside_validity": True,
        "result_class": claims.ResultClass.CANDIDATE_CALIBRATED_POINT.value,
        "evidence_class": claims.EvidenceClass.SOFTWARE_RESULT.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
        "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
        "verdict": "ROOT_CERTIFICATE_TWO_LAYER_DETERMINISTIC_CACHEABLE_AUDITED",
        "what_this_does_not_say": (
            "The certificate is a software result under a declared calibration; "
            "it is not a measured fact and validates no source origin."),
    }
