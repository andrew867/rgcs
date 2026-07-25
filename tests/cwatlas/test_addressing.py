"""P25/P26 — face selection, edge tie-breaking, and octal path addressing."""

from __future__ import annotations

import numpy as np
import pytest

from cwatlas import addressing as A
from cwatlas.icosahedron import build_icosahedron
from cwatlas.subdivision import MAX_CHILD_INDEX


def _ico():
    return build_icosahedron()


# --- P25: face selection ---------------------------------------------------


def test_select_face_returns_valid_face_id():
    ico = _ico()
    rng = np.random.default_rng(0)  # seeded: deterministic, not wall-clock
    for _ in range(200):
        d = rng.normal(size=3)
        sel = A.select_face(ico, d)
        assert 0 <= sel.face_id < len(ico.faces)


def test_face_centroid_selects_its_own_face():
    ico = _ico()
    normals = ico.face_normals
    for f in range(len(ico.faces)):
        assert A.select_face(ico, normals[f]).face_id == f


def test_interior_point_is_not_on_boundary():
    ico = _ico()
    tri = A.face_triangle(ico, 0)
    interior = 0.2 * tri.a + 0.3 * tri.b + 0.5 * tri.c
    sel = A.select_face(ico, interior)
    assert sel.on_boundary is False
    assert sel.tied_face_ids == (sel.face_id,)


def test_edge_point_ties_and_breaks_to_lowest_id():
    ico = _ico()
    # An edge shared by two faces: pick a face, find a neighbour sharing an
    # edge, and take the midpoint direction of the shared vertex pair.
    faces = ico.faces
    found = False
    for fa in range(len(faces)):
        for fb in range(fa + 1, len(faces)):
            shared = set(faces[fa]) & set(faces[fb])
            if len(shared) == 2:
                i, j = sorted(shared)
                mid = ico.vertices[i] + ico.vertices[j]  # on the shared edge
                sel = A.select_face(ico, mid)
                assert sel.on_boundary is True
                assert fa in sel.tied_face_ids and fb in sel.tied_face_ids
                # deterministic tie-break: the lowest id among the tied faces
                assert sel.face_id == min(sel.tied_face_ids)
                found = True
                break
        if found:
            break
    assert found


def test_vertex_point_ties_five_faces():
    ico = _ico()
    # Every icosahedron vertex is shared by exactly five faces.
    v0 = ico.vertices[0]
    sel = A.select_face(ico, v0)
    assert sel.on_boundary is True
    assert len(sel.tied_face_ids) == 5
    assert sel.face_id == min(sel.tied_face_ids)


def test_select_face_is_deterministic():
    ico = _ico()
    d = np.array([0.3, -0.7, 0.5])
    assert A.select_face(ico, d) == A.select_face(ico, d)


def test_select_face_refuses_degenerate_direction():
    ico = _ico()
    with pytest.raises(A.AddressError):
        A.select_face(ico, [0.0, 0.0, 0.0])
    with pytest.raises(A.AddressError):
        A.select_face(ico, [1.0, np.nan, 0.0])
    with pytest.raises(A.AddressError):
        A.select_face(ico, [1.0, 2.0])


def test_face_triangle_out_of_range_refused():
    ico = _ico()
    with pytest.raises(A.AddressError):
        A.face_triangle(ico, 20)
    with pytest.raises(A.AddressError):
        A.face_triangle(ico, -1)


# --- P26: recursive octal refinement ---------------------------------------


def test_encode_path_has_requested_depth_and_octal_digits():
    ico = _ico()
    tri = A.face_triangle(ico, 3)
    p = 0.2 * tri.a + 0.3 * tri.b + 0.5 * tri.c
    addr = A.encode_path(ico, p, depth=12)
    assert addr.depth == 12
    assert len(addr.path) == 12
    assert all(0 <= d <= MAX_CHILD_INDEX for d in addr.path)


def test_encode_path_is_stable():
    ico = _ico()
    tri = A.face_triangle(ico, 7)
    p = 0.5 * tri.a + 0.25 * tri.b + 0.25 * tri.c
    assert A.encode_path(ico, p, 12) == A.encode_path(ico, p, 12)


def test_encode_then_decode_cell_contains_point_POWER():
    ico = _ico()
    rng = np.random.default_rng(1)
    for _ in range(50):
        d = rng.normal(size=3)
        addr = A.encode_path(ico, d, depth=8)
        cell = A.path_cell(ico, addr.face_id, addr.path)
        # the point projected onto the cell must be inside it
        u, v, w = A.barycentric(cell, d)
        assert min(u, v, w) >= -1e-9


def test_depth_zero_path_is_the_whole_face():
    ico = _ico()
    addr = A.encode_path(ico, A.face_triangle(ico, 0).a + A.face_triangle(ico, 0).b
                         + A.face_triangle(ico, 0).c, depth=0)
    assert addr.path == ()
    cell = A.path_cell(ico, addr.face_id, addr.path)
    face = A.face_triangle(ico, addr.face_id)
    assert np.allclose(cell.corners(), face.corners())


def test_cwpack40_depth_packs_to_36_bits():
    ico = _ico()
    tri = A.face_triangle(ico, 5)
    p = 0.4 * tri.a + 0.35 * tri.b + 0.25 * tri.c
    addr = A.encode_path(ico, p, depth=A.CWPACK40_DEPTH)
    value, bits = addr.packed_bits()
    assert bits == 36
    assert 0 <= value < (1 << 36)


def test_octal_string_matches_path():
    ico = _ico()
    tri = A.face_triangle(ico, 2)
    p = 0.6 * tri.a + 0.2 * tri.b + 0.2 * tri.c
    addr = A.encode_path(ico, p, depth=6)
    assert addr.octal_string() == "".join(str(d) for d in addr.path)


def test_encode_path_refuses_negative_depth():
    ico = _ico()
    tri = A.face_triangle(ico, 0)
    with pytest.raises(A.AddressError):
        A.encode_path(ico, tri.a, depth=-1)


def test_path_cell_refuses_bad_digit():
    ico = _ico()
    with pytest.raises(A.AddressError):
        A.path_cell(ico, 0, [0, 1, 8])  # 8 is out of range
    with pytest.raises(A.AddressError):
        A.path_cell(ico, 0, [0, -1])


def test_report_claims_nothing_geographic():
    r = A.addressing_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
    assert r["claim_class"] == "MATHEMATICAL_TRANSLATION"
    assert r["tie_break_rule"] == "LOWEST_ID_ADJACENT_FACE"
    assert r["cwpack40_path_bits"] == 36
