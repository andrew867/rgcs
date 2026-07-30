"""R10.18 — the MeshLineage must be CONSTRUCTED, never inferred.

These tests exist because a prior run treated "L2 matches but L1 fails"
as a mystery. It was not a mystery: comparing a bare child index across
different parents is a category error. Parentage here is built by actual
subdivision, and `triangle_id // 4` is never trusted.
"""

import numpy as np
import pytest

from r1018 import lineage as L


@pytest.fixture(scope="module")
def nodes():
    return L.build(max_depth=2)


def test_lineage_is_complete_and_all_five_validations_pass(nodes):
    r = L.validate(nodes)
    assert r["failures"] == [], r["failures"]
    assert r["all_passed"]
    assert r["nodes"] == 420 and r["level1"] == 80 and r["level2"] == 320


def test_every_level2_triangle_has_exactly_one_level1_parent(nodes):
    for n in (n for n in nodes.values() if n.depth == 2):
        parents = [m for m in nodes.values()
                   if n.triangle_id in m.children]
        assert len(parents) == 1 and parents[0].depth == 1


def test_bare_child_index_is_not_a_cell_identity(nodes):
    """The rule that caught the previous run."""
    r = L.validate(nodes)
    amb = r["l2_index_is_ambiguous_without_parent"]
    assert set(amb) == {0, 1, 2, 3}
    for idx, parents in amb.items():
        assert len(parents) == 80, (idx, len(parents))


def test_parent_contains_each_child_centroid(nodes):
    for n in nodes.values():
        if n.parent_triangle_id is None:
            continue
        p = nodes[n.parent_triangle_id]
        assert L.contains(p.vertices, np.asarray(n.centroid, float))


def test_floor_division_parentage_is_ordering_dependent(nodes):
    """`flat_index // 4` is not lineage -- it is a property of the
    enumeration order, and it silently produces a DIFFERENT answer under
    a different but equally natural ordering.

    That is the whole hazard: it appears to work, so a run that relies
    on it looks correct until the ordering changes underneath it.
    """
    l2 = [n for n in nodes.values() if n.depth == 2]

    def groups(order):
        """{flat//4 bucket: set of true L1 parents in that bucket}"""
        out = {}
        for flat, n in enumerate(order):
            out.setdefault(flat // 4, set()).add(n.level1_parent_id)
        return out

    depth_first = sorted(l2, key=lambda n: (n.root_face_id, n.path))
    by_child_idx = sorted(l2, key=lambda n: (n.child_index_in_parent,
                                             n.root_face_id, n.path[0]))

    # Under depth-first enumeration the shortcut happens to agree...
    assert all(len(v) == 1 for v in groups(depth_first).values())
    # ...and under child-index-major enumeration it is simply wrong.
    broken = [k for k, v in groups(by_child_idx).items() if len(v) > 1]
    assert broken, "the shortcut must be demonstrably ordering-dependent"
    assert len(broken) >= 0.9 * len(groups(by_child_idx))


def test_constructed_parent_is_always_the_path_prefix(nodes):
    """Lineage comes from the recorded subdivision, not arithmetic."""
    for n in (n for n in nodes.values() if n.depth == 2):
        assert n.level1_parent_id == f"F{n.root_face_id}:{n.path[0]}"
        assert nodes[n.parent_triangle_id].path == n.path[:1]


def test_children_are_built_from_parent_vertices_and_edge_midpoints(nodes):
    for n in nodes.values():
        if n.parent_triangle_id is None:
            continue
        p = nodes[n.parent_triangle_id]
        allowed = [np.asarray(v, float) for v in p.vertices]
        allowed += [L._unit(np.asarray(p.vertices[i], float)
                            + np.asarray(p.vertices[(i + 1) % 3], float))
                    for i in range(3)]
        for v in n.vertices:
            assert min(float(np.linalg.norm(np.asarray(v, float) - a))
                       for a in allowed) <= 1e-12
