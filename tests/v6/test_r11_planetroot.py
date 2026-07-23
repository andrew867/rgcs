"""P02 — body-specific planetary magnetic roots: taxonomy, refusals,
circularity power, the null control, and altitude attenuation."""

from __future__ import annotations

import numpy as np
import pytest

from r11 import planetroot as P


# --- field-class taxonomy ----------------------------------------------

@pytest.mark.parametrize("body,expected", [
    ("EARTH", P.FieldClass.INTRINSIC_DYNAMO_FIELD),
    ("MARS", P.FieldClass.CRUSTAL_REMANENT_FIELD),
    ("MOON", P.FieldClass.CRUSTAL_REMANENT_FIELD),
    ("JUPITER", P.FieldClass.OFFSET_OR_MULTIPOLE_DYNAMO),
    ("MERCURY", P.FieldClass.OFFSET_OR_MULTIPOLE_DYNAMO),
    ("VENUS", P.FieldClass.INDUCED_SOLAR_WIND_FIELD),
])
def test_each_body_has_its_own_field_class(body, expected):
    assert P.field_class_of(body) is expected


def test_only_dynamo_bodies_are_flagged_as_dynamo():
    dynamo = {b for b, m in P.BODIES.items() if m.has_global_dynamo}
    assert dynamo == {"EARTH", "JUPITER", "MERCURY"}


def test_no_resolved_field_model_is_representable():
    b = P.unmodelled_body("SOME_BODY")
    assert b.field_class is P.FieldClass.NO_RESOLVED_FIELD_MODEL
    assert not b.has_global_dynamo
    assert P.FieldClass.NO_RESOLVED_FIELD_MODEL in set(P.FieldClass)


def test_an_unmodelled_body_gets_no_assumed_earth_field():
    with pytest.raises(P.PlanetRootError):
        P.resolve_body("PLANET_NINE")


def test_jupiter_is_the_only_body_without_a_solid_surface():
    surfaceless = {b for b, m in P.BODIES.items() if not m.has_solid_surface}
    assert surfaceless == {"JUPITER"}


# --- refusals ----------------------------------------------------------

@pytest.mark.parametrize("body", ["MARS", "MOON", "VENUS"])
def test_earth_method_on_a_non_dynamo_body_is_refused(body):
    with pytest.raises(P.PlanetRootError, match="BODY_SPECIFIC"):
        P.refuse_earth_method_on_non_dynamo_body(
            P.resolve_body(body), P.RootMethod.RADIAL_FIELD_EXTREMUM)


@pytest.mark.parametrize("body", ["MARS", "MOON", "VENUS"])
def test_dispatch_blocks_the_earth_construction_on_those_bodies(body):
    grid = P.synthetic_anomaly_grid([(-45.0, 20.0, 800.0, 6.0)])
    with pytest.raises(P.PlanetRootError):
        P.construct_root(P.RootMethod.RADIAL_FIELD_EXTREMUM, body, grid=grid)


def test_the_same_construction_is_allowed_on_earth():
    grid = P.synthetic_anomaly_grid([(30.0, -40.0, 900.0, 6.0)])
    r = P.construct_root(P.RootMethod.RADIAL_FIELD_EXTREMUM, "EARTH",
                         grid=grid)
    assert abs(r["lat_deg"] - 30.0) < 2.0
    assert abs(r["lon_deg"] + 40.0) < 2.0


def test_gas_giant_surface_assumption_is_refused():
    with pytest.raises(P.PlanetRootError, match="PRESSURE LEVEL"):
        P.refuse_surface_assumption_for_gas_giant(P.resolve_body("JUPITER"))


def test_dispatch_refuses_a_surface_reference_level_on_jupiter():
    grid = P.synthetic_anomaly_grid([(0.0, 0.0, 500.0, 8.0)])
    with pytest.raises(P.PlanetRootError):
        P.construct_root(P.RootMethod.RADIAL_FIELD_EXTREMUM, "JUPITER",
                         grid=grid, reference_level="MEAN_SURFACE")


def test_jupiter_works_when_a_pressure_level_is_declared():
    grid = P.synthetic_anomaly_grid([(0.0, 0.0, 500.0, 8.0)])
    r = P.construct_root(P.RootMethod.RADIAL_FIELD_EXTREMUM, "JUPITER",
                         grid=grid,
                         reference_level="ONE_BAR_PRESSURE_LEVEL")
    assert r["reference_level"] == "ONE_BAR_PRESSURE_LEVEL"


def _cert(**over):
    base = dict(
        body_id="EARTH",
        body_fixed_frame="EARTH_BODY_FIXED_IAU",
        rotation_axis=(0.0, 0.0, 1.0),
        prime_meridian="DECLARED_ZERO_MERIDIAN",
        shape_model="REFERENCE_ELLIPSOID",
        reference_surface_or_pressure_level="REFERENCE_ELLIPSOID",
        magnetic_model="SYNTHETIC_DEGREE_1_MODEL",
        magnetic_model_epoch="EPOCH_A",
        field_class=P.FieldClass.INTRINSIC_DYNAMO_FIELD,
        altitude=0.0,
        scalar_or_vector_feature="RADIAL_COMPONENT_EXTREMUM",
        critical_point_or_contour_rule="GLOBAL_MAX_ABS_RADIAL",
        zero_direction="TOWARD_DECLARED_PRIME_MERIDIAN",
        handedness="RIGHT",
        uncertainty=0.5,
        temporal_stability="STABLE_WITHIN_EPOCH",
    )
    base.update(over)
    return P.PlanetaryRootCertificate(**base)


def test_a_certificate_with_no_epoch_is_refused_as_timeless():
    with pytest.raises(P.PlanetRootError, match="EPOCH_SPECIFIC"):
        P.certify_root(_cert(magnetic_model_epoch=None))


def test_a_drifting_feature_may_not_be_a_timeless_address():
    with pytest.raises(P.PlanetRootError, match="drift"):
        P.certify_root(_cert(
            body_id="JUPITER",
            field_class=P.FieldClass.OFFSET_OR_MULTIPOLE_DYNAMO,
            scalar_or_vector_feature="GREAT_BLUE_SPOT"))


def test_refuse_timeless_root_is_always_a_refusal():
    with pytest.raises(P.PlanetRootError):
        P.refuse_timeless_root(_cert())


def test_a_complete_certificate_certifies_only_as_epoch_bound():
    c = P.certify_root(_cert())
    assert c["epoch_bound"] is True
    assert c["timeless"] is False
    assert c["epoch"] == "EPOCH_A"


def test_a_certificate_with_a_hole_is_rejected():
    with pytest.raises(P.PlanetRootError, match="prime_meridian"):
        P.certify_root(_cert(prime_meridian=""))


def test_a_certificate_with_zero_uncertainty_is_rejected():
    with pytest.raises(P.PlanetRootError, match="uncertainty"):
        P.certify_root(_cert(uncertainty=0.0))


def test_no_resolved_field_model_cannot_be_certified():
    with pytest.raises(P.PlanetRootError, match="BLOCKED_MISSING_DATA"):
        P.certify_root(_cert(
            field_class=P.FieldClass.NO_RESOLVED_FIELD_MODEL))


def test_calling_a_contour_a_circle_without_the_test_is_refused():
    with pytest.raises(P.PlanetRootError, match="circularity test"):
        P.refuse_circle_without_test(None)


def test_declare_circle_refuses_an_untested_fit():
    with pytest.raises(P.PlanetRootError):
        P.declare_circle({"circular": True})          # no tested/prereg flags


def test_declare_circle_refuses_a_failing_fit():
    fit = P.circularity(_ellipse(axis_ratio=2.0))
    with pytest.raises(P.PlanetRootError):
        P.declare_circle(fit)


def test_declare_circle_accepts_a_passing_fit():
    d = P.declare_circle(P.circularity(_circle()))
    assert d["shape"] == "CIRCLE"


def test_target_dependent_selection_is_refused():
    with pytest.raises(P.PlanetRootError, match="after"):
        P.refuse_target_dependent_selection(
            P.RootMethod.STABLE_CLOSED_CONTOUR, "a chosen point")


def test_select_method_refuses_once_the_target_has_been_inspected():
    with pytest.raises(P.PlanetRootError):
        P.select_method(P.RootMethod.NULL_SADDLE_NETWORK,
                        preregistration_id="PR_1", target_inspected=True)


def test_select_method_accepts_a_preregistered_choice():
    s = P.select_method(P.RootMethod.NULL_SADDLE_NETWORK,
                        preregistration_id="PR_1", target_inspected=False)
    assert s["method"] == "NULL_SADDLE_NETWORK"
    assert s["target_inspected_first"] is False


# --- circularity: power in both directions -----------------------------

def _circle(n=48, radius=3.0, noise=0.0, seed=11):
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    r = radius + (rng.standard_normal(n) * noise if noise else 0.0)
    return np.column_stack([r * np.cos(t), r * np.sin(t)])


def _ellipse(n=48, radius=3.0, axis_ratio=2.0):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return np.column_stack([radius * axis_ratio * np.cos(t),
                            radius * np.sin(t)])


def test_a_planted_circle_passes_the_circularity_test():
    fit = P.circularity(_circle())
    assert fit["circular"] is True
    assert fit["rms_residual"] < 1e-6
    assert abs(fit["radius"] - 3.0) < 1e-6


def test_a_slightly_noisy_circle_still_passes():
    fit = P.circularity(_circle(noise=0.02))
    assert fit["circular"] is True


def test_an_ellipse_fails_the_circularity_test():
    fit = P.circularity(_ellipse())
    assert fit["circular"] is False
    assert fit["normalised_rms"] > P.CIRCULARITY_TOLERANCE


def test_a_random_blob_fails_the_circularity_test():
    rng = np.random.default_rng(5)
    fit = P.circularity(rng.standard_normal((60, 2)))
    assert fit["circular"] is False


def test_the_tolerance_was_preregistered():
    assert P.PREREGISTERED_CIRCULARITY["registered_before_seeing_data"]
    assert P.circularity(_circle())["preregistered"] is True


def test_circularity_refuses_too_few_points():
    with pytest.raises(P.PlanetRootError):
        P.circularity([[0, 1], [1, 0], [0, -1]])


# --- constructions -----------------------------------------------------

def test_a_closed_contour_around_a_round_anomaly_is_circular():
    grid = P.synthetic_anomaly_grid([(0.0, 0.0, 1000.0, 6.0)])
    r = P.construct_root(P.RootMethod.STABLE_CLOSED_CONTOUR, "EARTH",
                         grid=grid)
    assert r["shape_named"] == "CLOSED_CONTOUR_NOT_CIRCLE"
    assert P.circularity(r["contour_points"])["circular"] is True


def test_a_closed_contour_around_an_elongated_anomaly_is_not_circular():
    grid = P.synthetic_anomaly_grid([(0.0, 0.0, 1000.0, 6.0, 2.5)])
    r = P.construct_root(P.RootMethod.STABLE_CLOSED_CONTOUR, "EARTH",
                         grid=grid)
    assert P.circularity(r["contour_points"])["circular"] is False


def test_an_open_contour_is_refused():
    grid = P.synthetic_anomaly_grid([(0.0, 0.0, 1000.0, 6.0)])
    with pytest.raises(P.PlanetRootError, match="not closed"):
        P.closed_contour(grid, 0.0, 0.0, 1e-9, max_radius_deg=5.0)


def test_the_gradient_extremum_sits_off_the_peak():
    grid = P.synthetic_anomaly_grid([(0.0, 0.0, 1000.0, 6.0)])
    g = P.construct_root(P.RootMethod.HORIZONTAL_GRADIENT_EXTREMUM,
                         "EARTH", grid=grid)
    assert np.hypot(g["lat_deg"], g["lon_deg"]) > 1.0


def test_the_harmonic_principal_axis_recovers_a_planted_dipole():
    grid = P.synthetic_dipole_grid([0.0, 0.0, 1.0])
    r = P.construct_root(P.RootMethod.HARMONIC_PRINCIPAL_AXIS, "EARTH",
                         grid=grid)
    assert r["lat_deg"] > 88.0


def test_the_harmonic_principal_axis_follows_a_tilted_dipole():
    axis = np.array([np.cos(np.radians(20.0)), 0.0,
                     np.sin(np.radians(20.0))])
    grid = P.synthetic_dipole_grid(axis)
    r = P.construct_root(P.RootMethod.HARMONIC_PRINCIPAL_AXIS, "EARTH",
                         grid=grid)
    assert abs(r["lat_deg"] - 20.0) < 1.0
    assert abs(r["lon_deg"]) < 1.0


def test_nulls_are_found_between_two_opposite_lobes():
    grid = P.synthetic_anomaly_grid([(0.0, -10.0, 1000.0, 6.0),
                                     (0.0, 10.0, -1000.0, 6.0)])
    r = P.construct_root(P.RootMethod.NULL_SADDLE_NETWORK, "EARTH",
                         grid=grid)
    assert r["n_nulls"] > 0
    assert abs(r["lon_deg"]) < 2.0


def test_the_crustal_centroid_is_for_bodies_with_no_global_dynamo():
    anomalies = [(-50.0, 170.0, 1.0), (-55.0, 175.0, 1.0),
                 (-45.0, 165.0, 1.0)]
    r = P.construct_root(P.RootMethod.CRUSTAL_ANOMALY_CENTROID, "MARS",
                         anomalies=anomalies)
    assert r["lat_deg"] < -40.0
    with pytest.raises(P.PlanetRootError):
        P.construct_root(P.RootMethod.CRUSTAL_ANOMALY_CENTROID, "EARTH",
                         anomalies=anomalies)


def test_a_construction_without_its_data_is_blocked_not_guessed():
    with pytest.raises(P.PlanetRootError, match="BLOCKED_MISSING_DATA"):
        P.construct_root(P.RootMethod.RADIAL_FIELD_EXTREMUM, "EARTH")


# --- the null control --------------------------------------------------

def test_method_seven_builds_a_root_with_no_magnetic_data():
    r = P.construct_root(P.RootMethod.SPIN_AXIS_NULL_CONTROL, "EARTH",
                         rotation_axis=(0.0, 0.0, 1.0),
                         prime_meridian_lon=0.0)
    assert r["uses_magnetic_data"] is False
    assert r["is_control"] is True
    assert r["control_label"] == "NULL_CONTROL_NO_MAGNETIC_DATA"
    assert r["lat_deg"] == 0.0 and r["lon_deg"] == 0.0
    assert r["pole_lat_deg"] == pytest.approx(90.0)


def test_the_null_control_is_available_on_every_body_including_venus():
    for body in P.BODIES:
        r = P.construct_root(P.RootMethod.SPIN_AXIS_NULL_CONTROL, body,
                             reference_level="ONE_BAR_PRESSURE_LEVEL")
        assert r["uses_magnetic_data"] is False


def test_only_method_seven_is_the_control():
    controls = [m for m in P.RootMethod
                if P.METHOD_SPEC[m]["is_control"]]
    assert controls == [P.RootMethod.SPIN_AXIS_NULL_CONTROL]
    assert P.RootMethod.SPIN_AXIS_NULL_CONTROL.value == 7


def test_all_seven_constructions_are_analytic_models():
    assert len(P.RootMethod) == 7
    assert all(P.METHOD_SPEC[m]["scientific_type"] == "ANALYTIC_MODEL"
               for m in P.RootMethod)


def test_comparing_constructions_on_mars_excludes_the_earth_recipes():
    names = {r["method"] for r in P.compare_constructions(
        "MARS", anomalies=[(-50.0, 170.0, 1.0)])}
    assert "RADIAL_FIELD_EXTREMUM" not in names
    assert "SPIN_AXIS_NULL_CONTROL" in names
    assert "CRUSTAL_ANOMALY_CENTROID" in names


# --- altitude attenuation ----------------------------------------------

def test_feature_strength_decreases_monotonically_with_altitude():
    a = P.altitude_attenuation([0.0, 100.0, 500.0, 1000.0, 5000.0])
    assert a["monotone_decreasing"] is True
    assert a["strengths_nT"][0] > a["strengths_nT"][-1]


def test_the_falloff_is_an_inverse_cube():
    r0 = 6371.2
    s0 = P.dipole_feature_strength(0.0, body_radius_km=r0)
    s1 = P.dipole_feature_strength(r0, body_radius_km=r0)   # r = 2 R
    assert s0 / s1 == pytest.approx(8.0, rel=1e-9)


def test_attenuation_holds_away_from_the_pole_too():
    a = P.altitude_attenuation([0.0, 200.0, 800.0], colatitude_deg=60.0)
    assert a["monotone_decreasing"] is True


def test_negative_altitude_is_refused():
    with pytest.raises(P.PlanetRootError):
        P.dipole_feature_strength(-1.0)


# --- report ------------------------------------------------------------

def test_report_measures_nothing_and_claims_no_physics():
    r = P.planetroot_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["verdict"] == "PLANETARY_ROOT_FRAMEWORK_SPECIFIABLE"
    assert "does not claim" in r["what_this_does_not_say"]


def test_report_keeps_the_universal_anomaly_circle_unsupported():
    r = P.planetroot_report()
    assert r["universal_anomaly_circle"]["status"] == "UNSUPPORTED"
    assert r["real_magnetic_models"]["status"] == "BLOCKED_MISSING_DATA"


def test_report_uses_the_public_neutral_candidate_alias():
    r = P.planetroot_report()
    assert r["candidate_alias"] == "PLANETARY_ROOT_CANDIDATE_A"
    assert r["candidate_status"] == "CANDIDATE_HYPOTHESIS"


def test_every_scientific_type_string_is_available():
    assert {t.value for t in P.ScientificType} == {
        "ESTABLISHED_SOURCE", "DERIVED_ARITHMETIC", "ANALYTIC_MODEL",
        "NUMERICAL_SIMULATION", "SOURCE_CLAIM", "CANDIDATE_HYPOTHESIS",
        "UNSUPPORTED", "BLOCKED_MISSING_DATA"}
