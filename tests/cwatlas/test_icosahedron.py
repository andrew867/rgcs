"""P13 — spherical icosahedron: topology, numbering, classification, area."""

from __future__ import annotations

import numpy as np
import pytest

from cwatlas import icosahedron as I


def _ico():
    return I.build_icosahedron()


def test_counts_and_euler_characteristic():
    ico = _ico()
    assert len(ico.vertices) == I.NUM_VERTICES == 12
    assert len(ico.edges) == I.NUM_EDGES == 30
    assert len(ico.faces) == I.NUM_FACES == 20
    assert ico.euler_characteristic() == 2  # V - E + F = 2


def test_vertices_are_on_the_unit_sphere():
    ico = _ico()
    norms = np.linalg.norm(ico.vertices, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-12)


def test_all_faces_present_exactly_once():
    ico = _ico()
    assert len(set(ico.faces)) == 20
    # every face is a sorted triple of valid vertex indices
    for f in ico.faces:
        assert list(f) == sorted(f)
        assert all(0 <= i < 12 for i in f)


def test_face_numbering_is_stable_across_runs():
    a = I.build_icosahedron()
    b = I.build_icosahedron()
    assert a.faces == b.faces
    assert a.edges == b.edges
    assert np.array_equal(a.vertices, b.vertices)


def test_a_point_maps_to_exactly_one_face():
    ico = _ico()
    # Each face centroid direction classifies to its own face...
    normals = ico.face_normals
    for fid in range(20):
        assert I.classify_point(ico, normals[fid]) == fid
    # ...and an arbitrary direction lands on a single valid face.
    fid = I.classify_point(ico, [0.11, -0.7, 0.4])
    assert 0 <= fid < 20


def test_classification_is_scale_invariant():
    ico = _ico()
    p = np.array([0.3, 0.4, 0.5])
    assert I.classify_point(ico, p) == I.classify_point(ico, 7.5 * p)


def test_face_areas_sum_to_four_pi():
    ico = _ico()
    total = I.total_area(ico)
    assert total == pytest.approx(4.0 * np.pi, abs=1e-9)
    # all faces congruent -> equal areas
    areas = [I.face_area(ico, f) for f in range(20)]
    assert np.allclose(areas, areas[0], atol=1e-9)


def test_zero_direction_is_refused():
    ico = _ico()
    with pytest.raises(ValueError):
        I.classify_point(ico, [0.0, 0.0, 0.0])


def test_nonfinite_direction_is_refused():
    ico = _ico()
    with pytest.raises(ValueError):
        I.classify_point(ico, [np.nan, 1.0, 0.0])


def test_face_area_index_out_of_range_is_refused():
    ico = _ico()
    with pytest.raises(ValueError):
        I.face_area(ico, 20)


def test_report_claims_nothing_geographic():
    r = I.icosahedron_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
    assert r["claim_class"] == "MATHEMATICAL_TRANSLATION"
    assert r["euler_characteristic"] == 2
