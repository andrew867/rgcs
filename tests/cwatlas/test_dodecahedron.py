"""P14 — dodecahedral dual: incidence, Euler, and refused conflation."""

from __future__ import annotations

import numpy as np
import pytest

from cwatlas import dodecahedron as D
from cwatlas.icosahedron import build_icosahedron


def _dod():
    return D.build_dodecahedron()


def test_counts_and_euler_characteristic():
    dod = _dod()
    assert len(dod.vertices) == D.NUM_VERTICES == 20
    assert len(dod.edges) == D.NUM_EDGES == 30
    assert len(dod.faces) == D.NUM_FACES == 12
    assert dod.euler_characteristic() == 2


def test_dual_incidence_matches_the_icosahedron():
    ico = build_icosahedron()
    dod = D.build_dodecahedron(ico)
    # faces<->vertices swap, edges preserved
    assert len(dod.vertices) == len(ico.faces)
    assert len(dod.faces) == len(ico.vertices)
    assert len(dod.edges) == len(ico.edges)


def test_every_dual_face_is_a_pentagon():
    dod = _dod()
    for f in dod.faces:
        assert len(f) == 5
        assert len(set(f)) == 5
        assert all(0 <= v < 20 for v in f)


def test_every_dual_vertex_has_degree_three():
    dod = _dod()
    deg = {v: 0 for v in range(20)}
    for u, w in dod.edges:
        deg[u] += 1
        deg[w] += 1
    assert all(d == 3 for d in deg.values())


def test_vertices_on_unit_sphere_and_stable():
    a = D.build_dodecahedron()
    b = D.build_dodecahedron()
    assert np.allclose(np.linalg.norm(a.vertices, axis=1), 1.0, atol=1e-12)
    assert a.faces == b.faces
    assert a.edges == b.edges


def test_dual_map_bridges_the_two_number_spaces():
    face = D.IcosaFaceId(7)
    vtx = D.dual_vertex_of_face(face)
    assert isinstance(vtx, D.DodecaVertexId)
    assert vtx.value == 7


def test_conflation_refused_bare_int_as_vertex():
    with pytest.raises(D.ConflationError):
        D.require_dodeca_vertex(5)  # a plain int is not a dodeca vertex id


def test_conflation_refused_icosa_face_as_vertex():
    with pytest.raises(D.ConflationError):
        D.require_dodeca_vertex(D.IcosaFaceId(5))  # a face is not a vertex


def test_dual_map_refuses_a_bare_int():
    with pytest.raises(D.ConflationError):
        D.dual_vertex_of_face(3)  # must be an IcosaFaceId


def test_dual_map_refuses_a_dodeca_vertex():
    with pytest.raises(D.ConflationError):
        D.dual_vertex_of_face(D.DodecaVertexId(3))  # already a vertex, not a face


def test_id_range_validation():
    with pytest.raises(ValueError):
        D.IcosaFaceId(20)
    with pytest.raises(ValueError):
        D.DodecaVertexId(-1)


def test_report_claims_nothing_geographic():
    r = D.dodecahedron_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
    assert r["claim_class"] == "MATHEMATICAL_TRANSLATION"
    assert r["euler_characteristic"] == 2
