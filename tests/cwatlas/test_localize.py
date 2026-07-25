"""P27/P28 — inverse localization, cell shrink, and exact residual round-trip."""

from __future__ import annotations

import numpy as np
import pytest

from cwatlas import localize as L
from cwatlas.addressing import AddressError, encode_path, face_triangle
from cwatlas.icosahedron import build_icosahedron


def _ico():
    return build_icosahedron()


def _interior(ico, face_id, weights):
    tri = face_triangle(ico, face_id)
    p = weights[0] * tri.a + weights[1] * tri.b + weights[2] * tri.c
    return p / np.linalg.norm(p)


# --- P27: inverse cell centroid and localization ---------------------------


def test_localize_returns_cell_centroid_and_diameter():
    ico = _ico()
    loc = L.localize_cell(ico, 0, [0, 3, 5])
    assert loc.face_id == 0
    assert loc.path == (0, 3, 5)
    assert np.isclose(np.linalg.norm(loc.centroid), 1.0)
    assert loc.diameter > 0.0


def test_refine_then_localize_contains_point_POWER():
    ico = _ico()
    rng = np.random.default_rng(2)
    for _ in range(60):
        d = rng.normal(size=3)
        loc = L.refine_then_localize(ico, d, depth=9)
        assert loc.contains(d)


def test_cell_diameter_shrinks_about_half_per_depth():
    ico = _ico()
    p = _interior(ico, 4, (0.5, 0.3, 0.2))
    prev = L.cell_diameter(face_triangle(ico, 4))
    for depth in range(1, 11):
        addr = encode_path(ico, p, depth)
        diam = L.cell_diameter(L.path_cell(ico, addr.face_id, addr.path))
        ratio = diam / prev
        assert 0.4 < ratio < 0.6, f"depth {depth} ratio {ratio}"
        prev = diam


def test_localize_is_deterministic():
    ico = _ico()
    a = L.localize_cell(ico, 2, [1, 4, 7, 0])
    b = L.localize_cell(ico, 2, [1, 4, 7, 0])
    assert a.face_id == b.face_id and a.path == b.path
    assert np.allclose(a.centroid, b.centroid)
    assert a.diameter == b.diameter


def test_localize_refuses_bad_address():
    ico = _ico()
    with pytest.raises(AddressError):
        L.localize_cell(ico, 99, [0])
    with pytest.raises(AddressError):
        L.localize_cell(ico, 0, [8])


# --- P28: continuous residual, exact round-trip ----------------------------


def test_forward_inverse_round_trip_full_precision_POWER():
    ico = _ico()
    rng = np.random.default_rng(3)
    for _ in range(200):
        d = rng.normal(size=3)
        d = d / np.linalg.norm(d)
        exact = L.forward(ico, d, depth=12)
        back = L.inverse(ico, exact)
        assert np.allclose(back, d, atol=1e-9)


def test_round_trip_holds_across_depths():
    ico = _ico()
    d = _interior(ico, 6, (0.45, 0.35, 0.20))
    for depth in (0, 1, 3, 7, 12, 13):
        exact = L.forward(ico, d, depth)
        back = L.inverse(ico, exact)
        assert np.allclose(back, d, atol=1e-9), f"depth {depth}"


def test_forward_refuses_depth_beyond_construction_floor():
    ico = _ico()
    d = _interior(ico, 6, (0.4, 0.35, 0.25))
    with pytest.raises(AddressError):
        L.forward(ico, d, depth=14)


def test_residual_components_sum_to_zero():
    ico = _ico()
    d = _interior(ico, 8, (0.2, 0.5, 0.3))
    exact = L.forward(ico, d, depth=10)
    assert abs(sum(exact.residual)) < 1e-9


def test_zero_residual_reconstructs_the_centroid():
    ico = _ico()
    exact = L.ExactAddress(face_id=1, path=(2, 5, 1), residual=(0.0, 0.0, 0.0))
    point = L.inverse(ico, exact)
    loc = L.localize_cell(ico, 1, (2, 5, 1))
    assert np.allclose(point, loc.centroid, atol=1e-12)


def test_forward_is_deterministic():
    ico = _ico()
    d = _interior(ico, 9, (0.33, 0.34, 0.33))
    assert L.forward(ico, d, 12) == L.forward(ico, d, 12)


def test_inverse_refuses_non_exact_address():
    ico = _ico()
    with pytest.raises(AddressError):
        L.inverse(ico, ("not", "an", "address"))


def test_inverse_refuses_bad_residual():
    ico = _ico()
    with pytest.raises(AddressError):
        L.inverse(ico, L.ExactAddress(face_id=0, path=(1,),
                                      residual=(np.nan, 0.0, 0.0)))


def test_report_claims_canonical_round_trip_no_geo():
    r = L.localize_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
    assert r["claim_class"] == "CANONICAL_ROUND_TRIP"
