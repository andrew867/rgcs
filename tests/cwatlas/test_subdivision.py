"""P15 — barycentric round-trip and one-to-eight refinement primitives."""

from __future__ import annotations

import numpy as np
import pytest

from cwatlas import subdivision as S
from cwatlas.icosahedron import build_icosahedron


def _tri():
    """A real icosahedral face as the working triangle."""
    ico = build_icosahedron()
    i, j, k = ico.faces[0]
    return S.SphericalTriangle.of(ico.vertices[i], ico.vertices[j],
                                  ico.vertices[k])


def test_barycentric_round_trip_point_to_bary_to_point():
    tri = _tri()
    # interior direction: weighted mix of the corners
    p = 0.2 * tri.a + 0.3 * tri.b + 0.5 * tri.c
    u, v, w = S.to_barycentric(tri, p)
    assert u + v + w == pytest.approx(1.0, abs=1e-12)
    back = S.from_barycentric(tri, (u, v, w))
    assert np.allclose(back, p / np.linalg.norm(p), atol=1e-9)


def test_barycentric_round_trip_bary_to_point_to_bary():
    tri = _tri()
    bary = (0.15, 0.55, 0.30)
    p = S.from_barycentric(tri, bary)
    u, v, w = S.to_barycentric(tri, p)
    assert np.allclose([u, v, w], bary, atol=1e-9)


def test_corners_have_unit_barycentric():
    tri = _tri()
    assert np.allclose(S.to_barycentric(tri, tri.a), (1, 0, 0), atol=1e-9)
    assert np.allclose(S.to_barycentric(tri, tri.b), (0, 1, 0), atol=1e-9)
    assert np.allclose(S.to_barycentric(tri, tri.c), (0, 0, 1), atol=1e-9)


def test_refine_produces_eight_children():
    tri = _tri()
    kids = S.refine(tri)
    assert len(kids) == S.CHILDREN_PER_NODE == 8


def test_child_index_in_zero_to_seven():
    tri = _tri()
    rng = np.random.default_rng(0)  # seeded: deterministic, not wall-clock
    for _ in range(200):
        # random interior barycentric point
        r = rng.random(3)
        r /= r.sum()
        p = S.from_barycentric(tri, tuple(r))
        idx = S.child_index(tri, p)
        assert 0 <= idx <= 7


def test_refine_then_locate_returns_same_child_POWER():
    tri = _tri()
    kids = S.refine(tri)
    for i, kid in enumerate(kids):
        centroid = (kid.a + kid.b + kid.c) / 3.0
        assert S.child_index(tri, centroid) == i


def test_children_tile_the_parent_area():
    tri = _tri()
    ico = build_icosahedron()  # reuse the area formula via a fresh computation
    from cwatlas.icosahedron import face_area  # noqa: F401  (import check)

    def area(t):
        a, b, c = t.a, t.b, t.c
        triple = abs(float(a @ np.cross(b, c)))
        denom = 1.0 + float(a @ b) + float(b @ c) + float(c @ a)
        return 2.0 * float(np.arctan2(triple, denom))

    parent = area(tri)
    total = sum(area(k) for k in S.refine(tri))
    assert total == pytest.approx(parent, abs=1e-9)


def test_determinism_of_refine_and_index():
    tri = _tri()
    assert [(*k.a, *k.b, *k.c) for k in S.refine(tri)] == \
           [(*k.a, *k.b, *k.c) for k in S.refine(tri)]
    p = 0.2 * tri.a + 0.3 * tri.b + 0.5 * tri.c
    assert S.child_index(tri, p) == S.child_index(tri, p)


def test_from_barycentric_refuses_non_partition():
    tri = _tri()
    with pytest.raises(ValueError):
        S.from_barycentric(tri, (0.5, 0.2, 0.1))  # does not sum to 1


def test_child_index_refuses_point_outside_triangle():
    tri = _tri()
    # a direction that projects beyond corner a (negative v, w barycentric)
    outside = 1.6 * tri.a - 0.3 * tri.b - 0.3 * tri.c
    with pytest.raises(ValueError):
        S.child_index(tri, outside)


def test_child_out_of_range_is_refused():
    tri = _tri()
    with pytest.raises(ValueError):
        S.child(tri, 8)


def test_degenerate_triangle_is_refused():
    with pytest.raises(ValueError):
        S.SphericalTriangle.of([1, 0, 0], [2, 0, 0], [3, 0, 0])


def test_report_claims_nothing_geographic():
    r = S.subdivision_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
    assert r["claim_class"] == "MATHEMATICAL_TRANSLATION"
    assert r["child_index_range"] == [0, 7]
