"""P13 — Icosahedral 20-face partition authority for ``EARTH_ROOT_D_V1``.

The locked profile partitions the sphere into the **20 spherical icosahedral
faces** (Locked Decision 3) and takes the **root feature** to be *one
icosahedral face centre* (Locked Decision 5), equivalently the matching
dodecahedral-dual vertex (bound in :mod:`cwatlas.r1082.route_graph`).

This module is a thin, *versioned* authority over the reused
:mod:`cwatlas.icosahedron` engine — it does **not** reimplement the geometry.
It fixes the deterministic face numbering, exposes the 20 face-centre unit
vectors for root binding, and mints a content ``digest`` over that numbering
and the partition version. Changing the version (or, hypothetically, the
geometry) mints a **new** partition id, so a silent regrid after a freeze is
detectable — the discipline of Locked Decisions / "no result shopping".

Everything here is ``DERIVED_MATHEMATICS`` at the ``SOFTWARE`` level. A face
id is a cell of a synthetic tessellation, not a place; selecting a *root face*
from a direction is an operator-supplied binding, not a measured coordinate and
not a validated source origin. See :mod:`cwatlas.r1082.claims`.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

import numpy as np

from cwatlas.icosahedron import (
    Icosahedron,
    build_icosahedron,
    classify_point,
)
from cwatlas.r1082 import claims as r1082_claims

#: Versioned identity of the locked partition authority. The version is part of
#: the digest: bump it and the partition id changes (a new authority record).
PARTITION_ID = "CW-R1082-ICOSA20"
PARTITION_VERSION = "1.0.0"

#: The locked partition and root-feature constants (mirrors the frozen profile
#: ``EARTH_ROOT_D_V1``; not re-decided here).
PROFILE_ID = "EARTH_ROOT_D_V1"
PARTITION_KIND = "SPHERICAL_ICOSAHEDRON_20_FACES"
ROOT_FEATURE = "ICOSAHEDRAL_FACE_CENTER"

NUM_FACES = 20

#: Decimal places the geometry is rounded to before hashing. Far below the
#: engine's construction precision, so the digest is stable across platforms
#: without depending on last-bit float noise.
_DIGEST_DECIMALS = 12


class PartitionError(ValueError):
    """Raised on an invalid face id or a degenerate root direction."""


@dataclass(frozen=True)
class RootBinding:
    """A root feature bound to one icosahedral face centre (Locked Decision 5).

    The binding is produced by classifying an operator-supplied *root
    direction* (e.g. the versioned Wilkes gravity-anomaly centroid direction)
    into its containing face. The face **centre** is the root feature; its id
    doubles as the matching dodecahedral-dual vertex id (the sanctioned bridge
    lives in :mod:`cwatlas.r1082.route_graph`).

    Attributes
    ----------
    partition_id, partition_version, partition_digest:
        The authority this binding was taken against (so a regrid invalidates
        the binding).
    root_face_id:
        The icosahedral face id ``0..19`` whose centre is the root feature.
    root_face_center:
        ``(3,)`` unit vector of that face centre.
    dual_vertex_id:
        The matching dodecahedral-dual vertex id (numerically equal to
        ``root_face_id`` — the dual map is identity on the index, but the
        *types* are kept distinct downstream to refuse conflation).
    """

    partition_id: str
    partition_version: str
    partition_digest: str
    root_face_id: int
    root_face_center: np.ndarray
    dual_vertex_id: int


@dataclass(frozen=True)
class IcosahedralPartition:
    """The versioned 20-face partition authority wrapping the engine icosa.

    Attributes
    ----------
    partition_id, version:
        Versioned identity; part of :meth:`digest`.
    ico:
        The reused deterministic :class:`cwatlas.icosahedron.Icosahedron`.
    """

    partition_id: str
    version: str
    ico: Icosahedron

    def face_centers(self) -> np.ndarray:
        """``(20, 3)`` unit face-centre directions, in stable face-id order.

        These are the vectors used for root binding (required phase work #4).
        """
        return self.ico.face_normals

    def face_center(self, face_id: int) -> np.ndarray:
        """The unit centre direction of one face."""
        self._check_face(face_id)
        return self.ico.face_normals[face_id]

    def classify(self, direction) -> int:
        """Face id ``0..19`` containing ``direction`` (reused engine classify).

        The root orientation is *not* applied here: this classifies against the
        canonical model, exactly as Locked Decision demands ("apply the root
        orientation only after constructing the canonical model").
        """
        return int(classify_point(self.ico, direction))

    def select_root(self, direction) -> RootBinding:
        """Bind the root feature to the face centre containing ``direction``.

        ``direction`` is an operator-supplied root direction (a fixed spatial
        anchor such as the versioned Wilkes centroid direction). The result is
        a binding record, not a measured coordinate: it asserts nothing about
        the anchor's physical truth or the source's origin.
        """
        face_id = self.classify(direction)
        return RootBinding(
            partition_id=self.partition_id,
            partition_version=self.version,
            partition_digest=self.digest(),
            root_face_id=face_id,
            root_face_center=self.ico.face_normals[face_id],
            dual_vertex_id=face_id,
        )

    def _check_face(self, face_id: int) -> None:
        if not isinstance(face_id, (int, np.integer)) or isinstance(face_id, bool):
            raise PartitionError(f"face id must be a plain int, got {face_id!r}")
        if not 0 <= int(face_id) < NUM_FACES:
            raise PartitionError(
                f"face id out of range 0..{NUM_FACES - 1}: {face_id!r}")

    def _canonical_geometry(self) -> dict:
        """A deterministic, JSON-serialisable view of the numbered geometry."""
        centers = np.round(self.ico.face_normals, _DIGEST_DECIMALS)
        # Normalise a signed zero to zero so the JSON is byte-stable.
        centers = centers + 0.0
        return {
            "partition_id": self.partition_id,
            "version": self.version,
            "kind": PARTITION_KIND,
            "root_feature": ROOT_FEATURE,
            "num_faces": len(self.ico.faces),
            "faces": [list(f) for f in self.ico.faces],
            "face_centers": centers.tolist(),
        }

    def digest(self) -> str:
        """Content hash over the partition version and numbered geometry.

        Deterministic (no wall-clock): a clean checkout reproduces it. The
        version participates, so bumping :data:`PARTITION_VERSION` mints a new
        partition id/digest and a post-freeze regrid is not silent.
        """
        blob = json.dumps(self._canonical_geometry(), sort_keys=True,
                          separators=(",", ":"))
        return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()


def build_partition() -> IcosahedralPartition:
    """Construct the versioned locked partition over the reused engine icosa."""
    return IcosahedralPartition(
        partition_id=PARTITION_ID,
        version=PARTITION_VERSION,
        ico=build_icosahedron(),
    )


def partition_report() -> dict:
    """Governance report: what this authority is and, emphatically, is not."""
    part = build_partition()
    return {
        "phase": "P13",
        "tranche": "T04",
        "what_this_is": (
            "the versioned, hashed icosahedral 20-face partition authority for "
            "EARTH_ROOT_D_V1: a thin wrapper over cwatlas.icosahedron with a "
            "face-centre root selection and a content digest"),
        "partition_id": part.partition_id,
        "partition_version": part.version,
        "partition_digest": part.digest(),
        "profile_id": PROFILE_ID,
        "partition_kind": PARTITION_KIND,
        "root_feature": ROOT_FEATURE,
        "num_faces": len(part.ico.faces),
        "euler_characteristic": part.ico.euler_characteristic(),
        "reused_engine": "cwatlas.icosahedron (NOT reimplemented)",
        "evidence_class": r1082_claims.EvidenceClass.DERIVED_MATHEMATICS.value,
        "level": "SOFTWARE",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
        "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
        "verdict": "R1082_ICOSA20_PARTITION_AUTHORITY_VERSIONED_HASHED",
        "what_this_does_not_say": (
            "A face id is a cell of a synthetic tessellation, not a place. "
            "Binding a root face to an operator-supplied direction is an "
            "operator selection, not a measured coordinate and not a validated "
            "source origin."),
    }
