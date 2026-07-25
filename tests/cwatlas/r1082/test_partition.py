"""P13 — icosahedral 20-face partition authority (locked profile)."""

from __future__ import annotations

import numpy as np
import pytest

from cwatlas.r1082 import partition as P


def test_partition_has_twenty_faces_and_sphere_euler():
    part = P.build_partition()
    assert len(part.ico.faces) == P.NUM_FACES == 20
    assert part.ico.euler_characteristic() == 2


def test_face_centers_are_unit_vectors():
    part = P.build_partition()
    centers = part.face_centers()
    assert centers.shape == (20, 3)
    norms = np.linalg.norm(centers, axis=1)
    assert np.allclose(norms, 1.0)


def test_digest_is_deterministic_and_versioned():
    # Same authority -> identical digest (no wall-clock).
    assert P.build_partition().digest() == P.build_partition().digest()
    # Version participates: a different version mints a new id/digest.
    a = P.build_partition()
    b = P.IcosahedralPartition(partition_id=a.partition_id, version="9.9.9",
                              ico=a.ico)
    assert a.digest() != b.digest()


def test_select_root_binds_face_centre_and_dual_vertex():
    part = P.build_partition()
    direction = np.array([0.13, 0.21, 0.97])
    binding = part.select_root(direction)
    # POWER: the bound face is the one that classifies the direction, and the
    # root feature is that face centre (Locked Decision 5).
    assert binding.root_face_id == part.classify(direction)
    assert np.allclose(binding.root_face_center,
                       part.face_center(binding.root_face_id))
    # The matching dodecahedral-dual vertex id equals the face id.
    assert binding.dual_vertex_id == binding.root_face_id
    assert binding.partition_digest == part.digest()


def test_classify_matches_nearest_face_centre():
    part = P.build_partition()
    # A direction very close to a face centre classifies to that face.
    for fid in range(20):
        c = part.face_center(fid)
        assert part.classify(c) == fid


def test_negative_bad_face_id_refused():
    part = P.build_partition()
    with pytest.raises(P.PartitionError):
        part.face_center(20)
    with pytest.raises(P.PartitionError):
        part.face_center(-1)
    with pytest.raises(P.PartitionError):
        part.face_center(True)  # bool is not a face id


def test_report_seals_claims():
    r = P.partition_report()
    assert r["phase"] == "P13"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["physical_effects"] == "PHYSICAL_EFFECTS_NOT_CLAIMED"
    assert r["source_origin"] == "SOURCE_ORIGIN_NOT_VALIDATED"
    assert r["evidence_class"] == "DERIVED_MATHEMATICS"
    assert r["verdict"]
