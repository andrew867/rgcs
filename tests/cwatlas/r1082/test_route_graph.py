"""P14 — dodecahedral-dual route graph (locked profile adjacency)."""

from __future__ import annotations

import pytest

from cwatlas.dodecahedron import (
    ConflationError,
    DodecaVertexId,
    IcosaFaceId,
)
from cwatlas.r1082 import route_graph as R


def test_graph_is_twenty_vertices_thirty_edges_three_regular():
    g = R.build_route_graph()
    assert R.DODECA_NUM_VERTICES == 20
    assert len(g.dod.edges) == 30
    # 3-regular: every dual vertex has exactly three neighbours.
    assert {len(a) for a in g.adjacency} == {R.EXPECTED_DEGREE}
    for v in range(20):
        assert g.degree(DodecaVertexId(v)) == 3


def test_neighbors_are_symmetric_and_typed():
    g = R.build_route_graph()
    for v in range(20):
        for nb in g.neighbors(DodecaVertexId(v)):
            assert isinstance(nb, DodecaVertexId)
            back = [x.value for x in g.neighbors(nb)]
            assert v in back  # undirected symmetry


def test_shortest_path_power_and_determinism():
    g = R.build_route_graph()
    cert = g.shortest_path(DodecaVertexId(0), DodecaVertexId(0))
    assert cert.path == (0,) and cert.hops == 0
    c1 = g.shortest_path(DodecaVertexId(0), DodecaVertexId(7))
    c2 = g.shortest_path(DodecaVertexId(0), DodecaVertexId(7))
    assert c1 == c2  # deterministic
    # POWER: the path is contiguous over real edges, endpoints correct.
    assert c1.path[0] == 0 and c1.path[-1] == 7
    for a, b in zip(c1.path, c1.path[1:]):
        assert b in g.adjacency[a]


def test_face_to_dual_vertex_bridge():
    # The sanctioned bridge maps an icosa face to its dual vertex.
    dv = R.root_vertex_for_face(IcosaFaceId(11))
    assert isinstance(dv, DodecaVertexId)
    assert dv.value == 11


def test_negative_face_vertex_conflation_refused():
    g = R.build_route_graph()
    # An IcosaFaceId is not a DodecaVertexId in a vertex-space query.
    with pytest.raises(ConflationError):
        g.neighbors(IcosaFaceId(3))
    with pytest.raises(ConflationError):
        g.degree(IcosaFaceId(3))
    # A bare int is not a vertex id either.
    with pytest.raises(ConflationError):
        g.neighbors(3)
    # A bare int passed to the bridge (expects an IcosaFaceId) is refused.
    with pytest.raises(ConflationError):
        R.root_vertex_for_face(3)


def test_negative_dodeca_face_is_never_the_root():
    with pytest.raises(ConflationError):
        R.refuse_dodeca_face_as_root(2)


def test_graph_digest_deterministic():
    assert R.build_route_graph().graph_digest() == \
        R.build_route_graph().graph_digest()


def test_report_seals_claims():
    r = R.route_graph_report()
    assert r["phase"] == "P14"
    assert r["degree_set"] == [3]
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["physical_effects"] == "PHYSICAL_EFFECTS_NOT_CLAIMED"
    assert r["source_origin"] == "SOURCE_ORIGIN_NOT_VALIDATED"
    assert r["evidence_class"] == "DERIVED_MATHEMATICS"
