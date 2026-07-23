"""P13 — the Mars frame pilot: the frame completes, the root is refused."""

from __future__ import annotations

import math

import numpy as np
import pytest

from r11 import earthface as E
from r11 import marspilot as M
from r11 import planetroot as P


# --- part 1: the Mars reference ellipsoid ------------------------------

def test_the_published_radii_are_the_iau_mola_values():
    assert M.MARS_EQUATORIAL_RADIUS_M == 3396190.0
    assert M.MARS_POLAR_RADIUS_M == 3376200.0
    assert M.MARS_A > M.MARS_B


def test_flattening_is_derived_from_the_two_radii_not_invented():
    assert M.MARS_F == pytest.approx(
        (M.MARS_A - M.MARS_B) / M.MARS_A, rel=1e-15)
    assert M.MARS_E2 == pytest.approx(1.0 - (M.MARS_B / M.MARS_A) ** 2,
                                      rel=1e-12)
    assert M.MARS_INVERSE_FLATTENING == pytest.approx(169.89, abs=0.05)


def test_equator_prime_meridian_lands_at_the_equatorial_radius():
    v = M.mars_geodetic_to_body_fixed(0.0, 0.0, 0.0)
    assert v[0] == pytest.approx(M.MARS_EQUATORIAL_RADIUS_M, abs=1e-6)
    assert v[1] == pytest.approx(0.0, abs=1e-6)
    assert v[2] == pytest.approx(0.0, abs=1e-6)


def test_the_north_pole_lands_at_the_polar_radius():
    v = M.mars_geodetic_to_body_fixed(90.0, 0.0, 0.0)
    assert v[2] == pytest.approx(M.MARS_POLAR_RADIUS_M, abs=1e-6)
    assert v[0] == pytest.approx(0.0, abs=1e-6)
    assert v[1] == pytest.approx(0.0, abs=1e-6)


def test_the_south_pole_lands_at_minus_the_polar_radius():
    v = M.mars_geodetic_to_body_fixed(-90.0, 0.0, 0.0)
    assert v[2] == pytest.approx(-M.MARS_POLAR_RADIUS_M, abs=1e-6)


def test_ninety_east_on_the_equator_lands_on_the_y_axis():
    v = M.mars_geodetic_to_body_fixed(0.0, 90.0, 0.0)
    assert v[1] == pytest.approx(M.MARS_EQUATORIAL_RADIUS_M, abs=1e-6)
    assert v[0] == pytest.approx(0.0, abs=1e-6)


def test_height_adds_along_the_equatorial_radius():
    v = M.mars_geodetic_to_body_fixed(0.0, 0.0, 1000.0)
    assert v[0] == pytest.approx(M.MARS_EQUATORIAL_RADIUS_M + 1000.0,
                                 abs=1e-6)


def test_the_mars_ellipsoid_is_not_the_earth_ellipsoid():
    mars = M.mars_geodetic_to_body_fixed(0.0, 0.0, 0.0)
    earth = E.geodetic_to_ecef(0.0, 0.0, 0.0)
    assert abs(float(mars[0]) - float(earth[0])) > 1e6


def test_out_of_range_latitude_is_refused():
    with pytest.raises(M.MarsPilotError):
        M.mars_geodetic_to_body_fixed(91.0, 0.0, 0.0)


def test_out_of_range_longitude_is_refused():
    with pytest.raises(M.MarsPilotError):
        M.mars_geodetic_to_body_fixed(0.0, 1000.0, 0.0)


# --- part 1b: the longitude and latitude conventions -------------------

def test_the_iau_mars_frame_is_east_positive_planetocentric():
    assert M.IAU_MARS_LONGITUDE is M.LongitudeConvention.EAST_POSITIVE
    assert M.IAU_MARS_LATITUDE is M.LatitudeConvention.PLANETOCENTRIC
    assert M.MARS_BODY_FIXED_FRAME == "MARS_BODY_FIXED_IAU"


def test_mixing_longitude_conventions_is_refused():
    with pytest.raises(M.MarsPilotError):
        M.refuse_mixed_longitude_convention(
            M.LongitudeConvention.EAST_POSITIVE,
            M.LongitudeConvention.WEST_POSITIVE)


def test_matching_longitude_conventions_pass_through():
    out = M.refuse_mixed_longitude_convention(
        M.LongitudeConvention.EAST_POSITIVE,
        M.LongitudeConvention.EAST_POSITIVE)
    assert out is M.LongitudeConvention.EAST_POSITIVE


def test_an_unlabelled_longitude_convention_is_refused():
    with pytest.raises(M.MarsPilotError):
        M.refuse_mixed_longitude_convention("east", "east")


def test_west_positive_longitude_converts_to_east_positive():
    assert M.to_east_longitude(
        47.95, M.LongitudeConvention.WEST_POSITIVE) == pytest.approx(312.05)
    assert M.to_east_longitude(
        312.05, M.LongitudeConvention.EAST_POSITIVE) == pytest.approx(312.05)


def test_the_two_latitude_conventions_differ_but_agree_at_the_poles():
    graphic = M.planetocentric_to_planetographic(45.0)
    assert graphic > 45.0
    assert graphic - 45.0 < 0.5
    back = M.planetographic_to_planetocentric(graphic)
    assert back == pytest.approx(45.0, abs=1e-9)
    assert M.planetocentric_to_planetographic(90.0) == 90.0
    assert M.planetocentric_to_planetographic(0.0) == pytest.approx(0.0)


# --- part 1c: the reused South-Up rotation and frozen solid ------------

def test_the_south_up_rotation_is_the_earthface_object():
    assert M.MARS_SOUTH_UP_ROTATION is E.SOUTH_UP_ROTATION
    assert np.allclose(M.MARS_SOUTH_UP_ROTATION, np.diag([1.0, -1.0, -1.0]))


def test_the_reused_south_up_rotation_is_proper():
    R = M.MARS_SOUTH_UP_ROTATION
    assert float(np.linalg.det(R)) == pytest.approx(1.0, abs=1e-12)
    assert np.allclose(R @ R.T, np.eye(3), atol=1e-12)
    assert M.is_proper_rotation(R)
    info = M.verify_reused_south_up()
    assert info["is_proper_rotation"] is True
    assert info["determinant"] == pytest.approx(1.0, abs=1e-12)
    assert info["is_the_earthface_object"] is True


def test_the_icosahedron_is_the_same_frozen_object_not_a_copy():
    assert M.MARS_ICOSAHEDRON is E.CANONICAL_ICOSAHEDRON
    assert M.MARS_ICOSAHEDRON.vertices is E.CANONICAL_ICOSAHEDRON.vertices
    assert M.MARS_ICOSAHEDRON.faces == E.CANONICAL_ICOSAHEDRON.faces
    info = M.verify_reused_icosahedron()
    assert info["is_the_earthface_object"] is True
    assert info["n_vertices"] == 12
    assert info["n_faces"] == 20
    assert info["rotated_for_mars"] is False
    assert info["vertices_read_only"] is True


def test_rotating_the_frozen_solid_for_mars_is_refused():
    with pytest.raises(M.MarsPilotError):
        M.refuse_rotate_after_load()
    with pytest.raises(M.MarsPilotError):
        M.refuse_rotate_after_load("to move a landing site onto a face")


def test_the_areocentric_ray_is_a_unit_vector():
    d = M.areocentric_ray(22.27, 312.05)
    assert float(np.linalg.norm(d)) == pytest.approx(1.0, abs=1e-12)


# --- part 1d: mars_face is set-valued ----------------------------------

def _lat_lon_of_south_up_direction(v):
    """Planetocentric (lat, lon_east) whose South-Up ray is ``v``."""
    u = E.south_up(np.asarray(v, dtype=float))
    u = u / float(np.linalg.norm(u))
    lat = math.degrees(math.asin(float(np.clip(u[2], -1.0, 1.0))))
    lon = math.degrees(math.atan2(float(u[1]), float(u[0])))
    return lat, lon


def test_a_generic_ray_hits_exactly_one_face():
    for i in range(20):
        lat, lon = _lat_lon_of_south_up_direction(
            M.MARS_ICOSAHEDRON.centroid(i))
        assert M.mars_face(lat, lon) == frozenset({i})


def test_a_ray_aimed_at_a_shared_edge_returns_a_set_of_two_faces():
    ico = M.MARS_ICOSAHEDRON
    i, j, _k = ico.faces[0]
    edge = ico.vertices[i] + ico.vertices[j]
    lat, lon = _lat_lon_of_south_up_direction(edge)
    faces = M.mars_face(lat, lon)
    assert len(faces) > 1
    assert len(faces) == 2


def test_a_ray_aimed_at_a_vertex_returns_a_set_of_five_faces():
    lat, lon = _lat_lon_of_south_up_direction(M.MARS_ICOSAHEDRON.vertices[0])
    faces = M.mars_face(lat, lon)
    assert len(faces) > 1
    assert len(faces) == 5


def test_mars_face_returns_a_frozenset_of_valid_indices():
    faces = M.mars_face(-4.59, 137.44)
    assert isinstance(faces, frozenset)
    assert all(0 <= i < 20 for i in faces)


def test_mars_face_refuses_an_out_of_range_latitude():
    with pytest.raises(M.MarsPilotError):
        M.mars_face(120.0, 0.0)


# --- part 2: the published landing sites are CONTROLS ------------------

def test_there_are_seven_declared_control_sites():
    assert len(M.CONTROL_SITES) == 7
    ids = {s.site_id for s in M.CONTROL_SITES}
    assert len(ids) == 7
    assert "PERSEVERANCE_CONTROL" in ids
    assert "VIKING_1_CONTROL" in ids


def test_every_control_site_is_marked_as_a_control():
    for s in M.CONTROL_SITES:
        assert s.role == M.CONTROL_ROLE == "CONTROL_SITE"
        assert s.longitude_convention is M.LongitudeConvention.EAST_POSITIVE
        assert s.latitude_convention is M.LatitudeConvention.PLANETOCENTRIC
        assert s.evidence_class == M.ScientificType.ESTABLISHED_SOURCE.value


def test_the_published_coordinates_are_the_expected_values():
    curiosity = M.control_site("CURIOSITY_CONTROL")
    assert curiosity.planetocentric_latitude_deg == pytest.approx(-4.59)
    assert curiosity.east_longitude_deg == pytest.approx(137.44)
    jezero = M.control_site("PERSEVERANCE_CONTROL")
    assert jezero.planetocentric_latitude_deg == pytest.approx(18.44)
    assert jezero.east_longitude_deg == pytest.approx(77.45)


def test_all_seven_control_sites_map_to_a_valid_face():
    for s in M.CONTROL_SITES:
        faces = s.faces()
        assert len(faces) >= 1
        assert all(0 <= i < 20 for i in faces)
        assert float(np.linalg.norm(s.ray())) == pytest.approx(1.0, abs=1e-12)


def test_every_control_site_has_a_body_fixed_position_near_the_ellipsoid():
    for s in M.CONTROL_SITES:
        r = float(np.linalg.norm(s.body_fixed()))
        assert M.MARS_POLAR_RADIUS_M - 1.0 <= r <= M.MARS_EQUATORIAL_RADIUS_M + 1.0


def test_using_a_control_site_as_a_target_is_refused():
    with pytest.raises(M.MarsPilotError):
        M.refuse_site_as_target(M.CONTROL_SITES[0])
    with pytest.raises(M.MarsPilotError):
        M.refuse_site_as_target()
    with pytest.raises(M.MarsPilotError):
        M.refuse_site_as_target("CURIOSITY_CONTROL", "decoded destination")


def test_a_landing_site_may_not_be_given_a_non_control_role():
    with pytest.raises(M.MarsPilotError):
        M.MarsControlSite("X", "mission", "region", 0.0, 0.0, role="TARGET")


def test_an_unknown_site_id_is_refused():
    with pytest.raises(M.MarsPilotError):
        M.control_site("SOMEWHERE_ELSE")


# --- part 3: the magnetic root is refused ------------------------------

def test_mars_is_carried_as_a_crustal_remanent_field_with_no_dynamo():
    assert M.MARS_FIELD_CLASS is P.FieldClass.CRUSTAL_REMANENT_FIELD
    assert M.MARS_BODY.has_global_dynamo is False


def test_the_five_prerequisites_default_to_unfrozen():
    p = M.MarsRootPrerequisites()
    assert set(p.unfrozen()) == set(M.REQUIRED_ROOT_PREREQUISITES)
    assert len(M.REQUIRED_ROOT_PREREQUISITES) == 5
    assert p.all_frozen() is False
    assert set(p.as_dict().values()) == {M.UNFROZEN}


def _all_frozen_kwargs() -> dict:
    return {
        "numerical_MAG_ER_vector_grid": "DECLARED_MAG_ER_VECTOR_GRID_SPEC",
        "altitude": 200.0,
        "epoch": "2026.0",
        "gradient_scalar": "TOTAL_INTENSITY",
        "sign_rule": "OUTWARD_POSITIVE",
    }


@pytest.mark.parametrize("missing", M.REQUIRED_ROOT_PREREQUISITES)
def test_magnetic_root_raises_with_any_single_prerequisite_unfrozen(missing):
    kwargs = _all_frozen_kwargs()
    kwargs[missing] = None
    prereqs = M.MarsRootPrerequisites(**kwargs)
    assert prereqs.unfrozen() == (missing,)
    with pytest.raises(M.MarsPilotError) as exc:
        M.magnetic_root(prereqs)
    assert missing in str(exc.value)


def test_a_placeholder_string_does_not_count_as_frozen():
    kwargs = _all_frozen_kwargs()
    kwargs["epoch"] = "UNFROZEN"
    with pytest.raises(M.MarsPilotError):
        M.magnetic_root(M.MarsRootPrerequisites(**kwargs))
    kwargs["epoch"] = "   "
    with pytest.raises(M.MarsPilotError):
        M.magnetic_root(M.MarsRootPrerequisites(**kwargs))


def test_magnetic_root_needs_a_prerequisites_object():
    with pytest.raises(M.MarsPilotError):
        M.magnetic_root({"epoch": "2026.0"})


def test_with_all_five_frozen_the_output_is_still_only_a_candidate():
    prereqs = M.MarsRootPrerequisites(**_all_frozen_kwargs())
    assert prereqs.all_frozen() is True
    out = M.magnetic_root(prereqs)
    assert out["status"] == "ROOT_CANDIDATE_REQUIRES_REAL_GRID"
    assert out["status"] == M.ROOT_CANDIDATE_STATUS
    assert out["root_identified"] is False
    assert out["latitude_deg"] is None
    assert out["longitude_deg"] is None
    assert out["field_class"] == "CRUSTAL_REMANENT_FIELD"
    assert out["verdict"] == M.VERDICT


def test_the_grid_status_is_blocked_missing_data():
    assert M.GRID_STATUS == "BLOCKED_MISSING_DATA"
    out = M.magnetic_root(M.MarsRootPrerequisites(**_all_frozen_kwargs()))
    assert out["grid_status"] == "BLOCKED_MISSING_DATA"


def test_the_earth_dynamo_method_is_refused_on_mars():
    with pytest.raises(M.MarsPilotError) as exc:
        M.refuse_earth_dynamo_method_on_mars(
            P.RootMethod.RADIAL_FIELD_EXTREMUM)
    assert "CRUSTAL_REMANENT" in str(exc.value)
    with pytest.raises(M.MarsPilotError):
        M.refuse_earth_dynamo_method_on_mars()


def test_identifying_a_magnetic_root_always_raises():
    with pytest.raises(M.MarsPilotError):
        M.refuse_magnetic_root_identification()
    with pytest.raises(M.MarsPilotError) as exc:
        M.refuse_magnetic_root_identification(
            "SOUTHERN_HIGHLAND_ANOMALY_CANDIDATE", "all five frozen")
    assert M.VERDICT in str(exc.value)


# --- the pilot and the report ------------------------------------------

def test_the_pilot_completes_the_frame_and_stops_at_the_root():
    out = M.mars_frame_pilot()
    assert out["frame_complete"] is True
    assert out["magnetic_root_identified"] is False
    assert out["n_control_sites"] == 7
    assert out["flattening_is_derived"] is True
    assert out["grid_status"] == "BLOCKED_MISSING_DATA"
    assert out["south_up"]["is_proper_rotation"] is True
    assert out["icosahedron"]["is_the_earthface_object"] is True
    assert out["verdict"] == M.VERDICT
    for site in out["control_sites"]:
        assert site["role"] == "CONTROL_SITE"
        assert len(site["candidate_faces"]) >= 1


def test_the_report_refuses_to_over_claim():
    r = M.marspilot_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["evidence_class"] == M.ScientificType.ANALYTIC_MODEL.value
    assert r["verdict"] == (
        "MARS_FRAME_PILOT_COMPLETE_MAGNETIC_ROOT_NOT_IDENTIFIED")
    assert "no global dynamo" in r["what_this_does_not_say"]
    assert "control" in r["what_this_does_not_say"]
    assert "magnetometer" in r["what_this_does_not_say"]


def test_the_report_names_the_five_prerequisites_and_the_refusals():
    r = M.marspilot_report()
    assert set(r["root_prerequisites"]) == set(M.REQUIRED_ROOT_PREREQUISITES)
    assert r["root_prerequisites_default"] == "UNFROZEN"
    assert r["root_status"] == "ROOT_CANDIDATE_REQUIRES_REAL_GRID"
    assert r["grid_status"] == "BLOCKED_MISSING_DATA"
    for name in ("refuse_mixed_longitude_convention",
                 "refuse_rotate_after_load", "refuse_site_as_target",
                 "refuse_earth_dynamo_method_on_mars",
                 "refuse_magnetic_root_identification"):
        assert name in r["refusals"]


def test_the_report_declares_the_reuse_and_the_ellipsoid():
    r = M.marspilot_report()
    assert r["reused_objects_are_identical"] is True
    assert r["icosahedron_rotated_for_mars"] is False
    assert "SOUTH_UP_ROTATION" in r["reused_from_earthface"]
    assert "CANONICAL_ICOSAHEDRON" in r["reused_from_earthface"]
    ell = r["reference_ellipsoid"]
    assert ell["equatorial_radius_km"] == pytest.approx(3396.19)
    assert ell["polar_radius_km"] == pytest.approx(3376.20)
    assert ell["derived_not_invented"] is True
    assert ell["source_class"] == "ESTABLISHED_SOURCE"


def test_the_report_lists_seven_control_sites_that_are_not_targets():
    r = M.marspilot_report()
    assert len(r["control_sites"]) == 7
    assert r["control_sites_are_not_targets"] is True
    assert all(s["role"] == "CONTROL_SITE" for s in r["control_sites"])
