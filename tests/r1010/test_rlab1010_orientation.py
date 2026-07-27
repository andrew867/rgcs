"""R10.10 acceptance — orientation algebra, dual graph, child table."""

from __future__ import annotations

import inspect

import pytest

from r1010 import child_orientation as co
from r1010 import dual_graph as dg
from r1010.orientation import ALL, IDENTITY, Orientation, OrientationError


def test_six_elements_composition_inverse_parity():
    assert len(ALL) == 6
    assert sum(1 for o in ALL if o.parity == 1) == 3
    assert sum(1 for o in ALL if o.parity == -1) == 3
    for a in ALL:
        assert a.compose(a.inverse()).perm == IDENTITY.perm
        assert a.inverse().compose(a).perm == IDENTITY.perm
        for b in ALL:
            c = a.compose(b)
            assert c in ALL                       # closure
            assert c.parity == a.parity * b.parity
    # serialization + stable hash round trip
    for o in ALL:
        assert Orientation.deserialize(o.serialize()).perm == o.perm
        assert len(o.stable_hash()) == 16
    with pytest.raises(OrientationError):
        Orientation((0, 0, 1))


def test_vertex_application():
    o = Orientation((1, 0, 2))
    assert o.apply_vertices(("A", "B", "C")) == ("B", "A", "C")
    assert o.apply_corner(0) == 1


def test_twenty_faces_thirty_adjacencies_all_reachable():
    faces = dg.load_faces()
    assert len(faces) == 20
    assert len(dg.adjacency(faces)) == 30
    rep = dg.propagate(faces)
    assert rep["all_faces_reachable"]
    assert rep["directed_edge_count"] == 60


def test_directed_transitions_invert_and_are_reflections():
    faces = dg.load_faces()
    for f, g in dg.adjacency(faces):
        t, back = dg.edge_transition(faces, f, g), dg.edge_transition(faces, g, f)
        assert back.compose(t).perm == IDENTITY.perm
        assert t.parity == -1        # every shared-edge crossing reflects


def test_path_independence_audited_and_reported():
    rep = dg.propagate()
    # The audit RUNS and reports honestly: with reflection-only
    # transitions every dual 5-cycle has odd reflection count, so
    # holonomy parity is -1 and path independence FAILS — the
    # transition/phase model is incomplete (spec-mandated finding).
    assert rep["path_independent"] is False
    assert rep["nontrivial_holonomy_cycles"] == 12
    for c in rep["vertex_cycles"]:
        assert len(c["cycle"]) == 5
        assert c["holonomy_parity"] == -1


def test_child_table_derived_and_centre_parity_explicit():
    t = co.table_receipt()["children"]
    assert t["0"]["serialized"] == "012"
    assert t["1"]["serialized"] == "012"
    assert t["2"]["serialized"] == "012"
    assert t["3"]["serialized"] == "201"          # opposite-corner map
    assert t["3"]["permutation_parity"] == 1      # cyclic, even parity
    assert t["3"]["winding_preserved"] is True    # barycentric winding kept
    assert t["3"]["geometric_inversion"] is True  # point-down (opposite)
    for k in ("0", "1", "2"):
        assert t[k]["geometric_inversion"] is False


def test_orientation_trace_through_compact_path():
    base = co.IDENTITY if hasattr(co, "IDENTITY") else None
    from r1010.orientation import Orientation
    tr = co.trace_orientation(Orientation((1, 0, 2)),
                              (3, 3, 0, 1, 2, 0, 2, 1, 2, 1, 1))
    assert len(tr) == 12
    assert tr[0]["orientation"] == "102"
    # centre children toggle the inversion flag
    inv = False
    for row in tr[1:]:
        if row["digit"] == 3:
            inv = not inv
        assert row["inverted"] == inv


def test_no_place_names_in_orientation_code():
    for mod in (co, dg):
        src = inspect.getsource(mod)
        for banned in ("Stonehenge", "Toronto", "Montreal", "Montréal",
                       "Erie", "stonehenge", "toronto", "montreal", "erie"):
            assert banned not in src
