"""P03 — Earth South root, city face, and the set-valued magnetic zero."""

from __future__ import annotations

import numpy as np
import pytest

from r11 import earthface as E


# --- stage 1: geodetic -> ECEF -----------------------------------------

def test_equator_prime_meridian_lands_at_the_semi_major_axis():
    v = E.geodetic_to_ecef(0.0, 0.0, 0.0)
    assert v[0] == pytest.approx(E.WGS84_A, abs=1e-6)
    assert v[1] == pytest.approx(0.0, abs=1e-6)
    assert v[2] == pytest.approx(0.0, abs=1e-6)


def test_north_pole_lands_at_the_semi_minor_axis():
    v = E.geodetic_to_ecef(90.0, 0.0, 0.0)
    assert v[2] == pytest.approx(E.WGS84_B, abs=1e-6)
    assert v[0] == pytest.approx(0.0, abs=1e-6)
    assert v[1] == pytest.approx(0.0, abs=1e-6)
    assert E.WGS84_B == pytest.approx(6356752.314245, abs=1e-5)


def test_ninety_east_on_the_equator_lands_on_the_y_axis():
    v = E.geodetic_to_ecef(0.0, 90.0, 0.0)
    assert v[1] == pytest.approx(E.WGS84_A, abs=1e-6)
    assert v[0] == pytest.approx(0.0, abs=1e-6)


def test_height_adds_along_the_equatorial_radius():
    v = E.geodetic_to_ecef(0.0, 0.0, 1000.0)
    assert v[0] == pytest.approx(E.WGS84_A + 1000.0, abs=1e-6)


def test_out_of_range_latitude_is_refused():
    with pytest.raises(E.EarthFaceError):
        E.geodetic_to_ecef(91.0, 0.0, 0.0)


def test_a_point_without_a_declared_epoch_is_refused():
    with pytest.raises(E.EarthFaceError):
        E.GeodeticPoint("NO_EPOCH", 0.0, 0.0, 0.0, "ITRF2020", "")


def test_the_control_site_is_declared_as_a_control():
    assert E.SEDONA_FACE_CONTROL.role == "CONTROL"
    assert E.SEDONA_FACE_CONTROL.epoch
    assert E.SEDONA_FACE_CONTROL.frame.startswith("ITRF")


# --- stage 2: South-Up is a rotation, not a mirror ---------------------

def test_south_up_is_diag_1_minus1_minus1():
    assert np.allclose(E.SOUTH_UP_ROTATION, np.diag([1.0, -1.0, -1.0]))


def test_south_up_determinant_is_plus_one_and_it_is_orthogonal():
    R = E.SOUTH_UP_ROTATION
    assert float(np.linalg.det(R)) == pytest.approx(1.0, abs=1e-12)
    assert np.allclose(R @ R.T, np.eye(3), atol=1e-12)
    assert E.is_proper_rotation(R)


def test_south_up_passes_the_mirror_refusal():
    out = E.refuse_mirror_view(E.SOUTH_UP_ROTATION)
    assert np.allclose(out, E.SOUTH_UP_ROTATION)


def test_a_true_mirror_is_refused():
    mirror = np.diag([1.0, 1.0, -1.0])
    assert float(np.linalg.det(mirror)) == pytest.approx(-1.0)
    assert not E.is_proper_rotation(mirror)
    with pytest.raises(E.EarthFaceError):
        E.refuse_mirror_view(mirror)


def test_a_non_orthogonal_view_is_refused():
    with pytest.raises(E.EarthFaceError):
        E.refuse_mirror_view(np.diag([2.0, 1.0, 1.0]))


def test_south_up_applied_twice_is_the_identity():
    v = np.array([1.0, 2.0, 3.0])
    assert np.allclose(E.south_up(E.south_up(v)), v)


def test_the_city_ray_is_a_unit_vector():
    d = E.city_ray(E.SEDONA_FACE_CONTROL)
    assert float(np.linalg.norm(d)) == pytest.approx(1.0, abs=1e-12)


# --- stage 3: the frozen icosahedron -----------------------------------

def test_icosahedron_has_twelve_unit_vertices():
    V = E.CANONICAL_ICOSAHEDRON.vertices
    assert V.shape == (12, 3)
    assert np.allclose(np.linalg.norm(V, axis=1), 1.0, atol=1e-12)


def test_icosahedron_has_twenty_faces_with_outward_normals():
    ico = E.CANONICAL_ICOSAHEDRON
    assert len(ico.faces) == 20
    for i in range(20):
        assert float(np.dot(ico.normal(i), ico.centroid(i))) > 0.0


def test_every_face_is_a_triangle_of_distinct_vertices():
    for face in E.CANONICAL_ICOSAHEDRON.faces:
        assert len(face) == 3
        assert len(set(face)) == 3


def test_rotating_the_frozen_solid_after_load_is_refused():
    with pytest.raises(E.EarthFaceError):
        E.refuse_rotate_after_load()


def test_rotating_the_frozen_solid_names_the_reason():
    with pytest.raises(E.EarthFaceError):
        E.refuse_rotate_after_load("to move the control site onto a face")


def test_the_vertex_array_is_read_only():
    with pytest.raises(ValueError):
        E.CANONICAL_ICOSAHEDRON.vertices[0, 0] = 99.0


# --- stage 4: ray-face intersection is set-valued ----------------------

def test_a_ray_through_a_face_centroid_hits_exactly_one_face():
    ico = E.CANONICAL_ICOSAHEDRON
    for i in range(20):
        hits = E.ray_face_intersection(ico.centroid(i))
        assert hits == frozenset({i})


def test_a_ray_aimed_at_a_shared_edge_returns_two_faces():
    ico = E.CANONICAL_ICOSAHEDRON
    i, j, _k = ico.faces[0]
    edge_dir = ico.vertices[i] + ico.vertices[j]
    hits = E.ray_face_intersection(edge_dir)
    assert len(hits) > 1
    assert len(hits) == 2


def test_a_ray_aimed_at_a_vertex_returns_five_faces():
    hits = E.ray_face_intersection(E.CANONICAL_ICOSAHEDRON.vertices[0])
    assert len(hits) > 1
    assert len(hits) == 5


def test_the_control_site_ray_lands_on_one_face():
    hits = E.ray_face_intersection(E.city_ray(E.SEDONA_FACE_CONTROL))
    assert len(hits) == 1


def test_a_zero_length_ray_is_refused():
    with pytest.raises(E.EarthFaceError):
        E.ray_face_intersection(np.zeros(3))


# --- stage 5: the local face frame -------------------------------------

def test_the_local_face_frame_is_orthonormal_and_proper():
    ray = E.city_ray(E.SEDONA_FACE_CONTROL)
    idx = E.nearest_face_by_centroid(ray)
    frame = E.local_face_frame(ray, idx)
    assert frame.is_orthonormal()
    assert float(np.linalg.det(frame.matrix())) == pytest.approx(1.0)


def test_the_face_tangents_are_perpendicular_to_the_face_normal():
    ico = E.CANONICAL_ICOSAHEDRON
    frame = E.local_face_frame(ico.centroid(3), 3)
    n = np.array(frame.normal)
    assert float(np.dot(n, np.array(frame.tangent_u))) == pytest.approx(
        0.0, abs=1e-12)
    assert float(np.dot(n, np.array(frame.tangent_v))) == pytest.approx(
        0.0, abs=1e-12)


def test_the_hit_point_lies_on_the_ray():
    ico = E.CANONICAL_ICOSAHEDRON
    d = ico.centroid(7)
    p = E.face_hit_point(d, 7)
    assert np.allclose(p / float(np.linalg.norm(p)), d, atol=1e-12)


# --- stage 6: the magnetic zero is an alias set ------------------------

def _control_geometry():
    ray = E.city_ray(E.SEDONA_FACE_CONTROL)
    idx = E.nearest_face_by_centroid(ray)
    frame = E.local_face_frame(ray, idx)
    position = E.south_up(E.SEDONA_FACE_CONTROL.ecef())
    return position, frame


def test_six_candidate_scalars_are_carried_unresolved():
    assert len(list(E.MagneticScalar)) == 6
    names = {s.value for s in E.MagneticScalar}
    assert "TOTAL_INTENSITY" in names
    assert "DECLINATION" in names
    assert "POTENTIAL" in names


def test_the_alias_set_spans_scalars_altitudes_epochs_and_both_signs():
    position, frame = _control_geometry()
    aliases = E.gradient_zero_alias_set(position, frame)
    assert len(aliases) >= 4
    assert len({a.scalar for a in aliases}) >= 2
    assert {a.sign for a in aliases} == {1, -1}
    assert len({a.altitude_m for a in aliases}) >= 2
    assert len({a.epoch for a in aliases}) >= 2
    assert len(aliases) == (len(list(E.MagneticScalar))
                            * len(E.DEFAULT_ALTITUDES_M)
                            * len(E.DEFAULT_EPOCHS)
                            * len(E.DEFAULT_SIGNS))


def test_both_signs_of_every_zero_direction_are_kept():
    position, frame = _control_geometry()
    aliases = E.gradient_zero_alias_set(
        position, frame, scalars=(E.MagneticScalar.TOTAL_INTENSITY,
                                  E.MagneticScalar.INCLINATION),
        altitudes_m=(0.0,), epochs=("2026.0",))
    assert len(aliases) == 4
    by_scalar: dict = {}
    for a in aliases:
        by_scalar.setdefault(a.scalar, []).append(np.array(a.direction))
    for pair in by_scalar.values():
        assert len(pair) == 2
        assert np.allclose(pair[0], -pair[1], atol=1e-12)


def test_every_alias_direction_is_a_unit_vector_in_the_face_plane():
    position, frame = _control_geometry()
    n = np.array(frame.normal)
    for a in E.gradient_zero_alias_set(position, frame):
        d = np.array(a.direction)
        assert float(np.linalg.norm(d)) == pytest.approx(1.0, abs=1e-9)
        assert float(np.dot(d, n)) == pytest.approx(0.0, abs=1e-9)


def test_different_scalars_give_different_zero_directions():
    position, frame = _control_geometry()
    aliases = E.gradient_zero_alias_set(
        position, frame, scalars=(E.MagneticScalar.TOTAL_INTENSITY,
                                  E.MagneticScalar.DECLINATION),
        altitudes_m=(0.0,), epochs=("2026.0",), signs=(1,))
    dirs = [np.array(a.direction) for a in aliases]
    assert len(dirs) == 2
    assert not np.allclose(dirs[0], dirs[1], atol=1e-6)


def test_an_alias_set_over_one_scalar_is_refused():
    position, frame = _control_geometry()
    with pytest.raises(E.EarthFaceError):
        E.gradient_zero_alias_set(
            position, frame, scalars=(E.MagneticScalar.POTENTIAL,))


def test_claiming_one_zero_without_a_sign_is_refused():
    position, frame = _control_geometry()
    with pytest.raises(E.EarthFaceError):
        E.refuse_single_zero_direction(
            scalar=E.MagneticScalar.TOTAL_INTENSITY,
            altitude_m=0.0, epoch="2026.0",
            position=position, frame=frame)


def test_claiming_one_zero_with_nothing_fixed_is_refused():
    with pytest.raises(E.EarthFaceError):
        E.refuse_single_zero_direction()


def test_claiming_one_zero_without_an_epoch_is_refused():
    position, frame = _control_geometry()
    with pytest.raises(E.EarthFaceError):
        E.refuse_single_zero_direction(
            scalar=E.MagneticScalar.INCLINATION, sign=1, altitude_m=0.0,
            position=position, frame=frame)


def test_with_all_four_choices_fixed_the_direction_is_an_alias_member():
    position, frame = _control_geometry()
    d = E.refuse_single_zero_direction(
        scalar=E.MagneticScalar.TOTAL_INTENSITY, sign=1, altitude_m=0.0,
        epoch="2026.0", position=position, frame=frame)
    aliases = E.gradient_zero_alias_set(position, frame)
    assert any(np.allclose(np.array(a.direction), np.array(d), atol=1e-12)
               for a in aliases)


def test_an_undeclared_epoch_string_is_refused_by_the_field_model():
    with pytest.raises(E.EarthFaceError):
        E.dipole_axis("whenever")


def test_the_dipole_axis_moves_between_epochs():
    a = E.dipole_axis("2020.0")
    b = E.dipole_axis("2026.0")
    assert not np.allclose(a, b, atol=1e-9)
    assert float(np.linalg.norm(a)) == pytest.approx(1.0, abs=1e-12)


# --- the pipeline and the report ---------------------------------------

def test_the_pipeline_runs_end_to_end_and_stays_proper():
    out = E.earth_face_pipeline()
    assert out["south_up_is_proper_rotation"]
    assert out["face_frame_orthonormal"]
    assert out["icosahedron_frozen"]
    assert out["alias_count"] >= 4
    assert out["verdict"] == "EARTH_FACE_LOCAL_ZERO_SPECIFIABLE_WITH_ALIASES"


def test_the_report_refuses_to_over_claim():
    r = E.earthface_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["evidence_class"] == E.ScientificType.ANALYTIC_MODEL.value
    assert r["verdict"] == "EARTH_FACE_LOCAL_ZERO_SPECIFIABLE_WITH_ALIASES"
    assert r["both_signs_preserved"] is True
    assert len(r["scalars_unresolved"]) == 6
    assert r["choice_axes"] == ["scalar", "sign", "altitude", "epoch"]
    assert "magnetometer" in r["what_this_does_not_say"]
    assert "ALIAS SET" in r["what_this_does_not_say"]


def test_the_report_names_the_control_as_a_control():
    r = E.earthface_report()
    assert r["control_location"] == "SEDONA_FACE_CONTROL"
    assert "control" in r["what_this_does_not_say"]


def test_every_scientific_type_is_available():
    names = {t.value for t in E.ScientificType}
    assert names == {
        "ESTABLISHED_SOURCE", "DERIVED_ARITHMETIC", "ANALYTIC_MODEL",
        "NUMERICAL_SIMULATION", "SOURCE_CLAIM", "CANDIDATE_HYPOTHESIS",
        "UNSUPPORTED", "BLOCKED_MISSING_DATA"}
