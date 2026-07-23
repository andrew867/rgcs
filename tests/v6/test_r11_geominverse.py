"""P11 — geometric inverse: exact phi angle, and a centroid inverse that
is underdetermined.

Every test here can fail. The exact constants are checked against the
verified high-precision values, the 51.843 comparison is checked to
carry a real non-zero difference (so rounding it away breaks the suite),
the solver is checked to actually solve a planted problem (so a broken
solver cannot masquerade as underdetermination), and the family is
checked to contain genuinely different parameter sets (so returning the
same body six times fails).
"""

from __future__ import annotations

import math
from decimal import Decimal, localcontext

import numpy as np
import pytest

from r11 import geominverse as G


# =======================================================================
# Part 1 -- the exact symbolic constants
# =======================================================================

def test_phi_reproduces_the_verified_float():
    assert G.PHI == 1.618033988749895
    # and it is the closed form, not a coincidence of typing
    assert G.PHI == (1.0 + math.sqrt(5.0)) / 2.0


def test_phi_exact_is_high_precision_not_a_rounded_float():
    phi = G.phi_exact()
    assert isinstance(phi, Decimal)
    # far more digits than a double carries
    assert len(str(phi).replace(".", "").lstrip("0")) >= 50
    assert str(phi).startswith("1.6180339887498948482045868343656381")


def test_phi_exact_satisfies_its_defining_equation():
    """phi^2 == phi + 1. A hardcoded rounded literal would not."""
    with localcontext() as ctx:
        ctx.prec = 80
        phi = G.phi_exact(80)
        residual = abs(phi * phi - (phi + 1))
    assert residual < Decimal(1).scaleb(-70)


def test_phi_exact_precision_is_a_real_knob():
    low = G.phi_exact(20)
    high = G.phi_exact(60)
    assert str(low) != str(high)
    assert str(high).startswith(str(low)[:18])


def test_sqrt_phi_reproduces_the_verified_float():
    assert G.SQRT_PHI == 1.272019649514069
    assert G.SQRT_PHI == math.sqrt(G.PHI)


def test_sqrt_phi_exact_squares_back_to_phi():
    with localcontext() as ctx:
        ctx.prec = 80
        s = G.sqrt_phi_exact(80)
        residual = abs(s * s - G.phi_exact(80))
    assert residual < Decimal(1).scaleb(-70)


def test_atan_sqrt_phi_deg_reproduces_the_verified_float():
    assert G.ATAN_SQRT_PHI_DEG == 51.827292372987756
    assert G.ATAN_SQRT_PHI_DEG == math.degrees(math.atan(math.sqrt(G.PHI)))


def test_atan_sqrt_phi_deg_high_precision_agrees_to_fourteen_digits():
    exact = G.ATAN_SQRT_PHI_DEG_EXACT
    assert isinstance(exact, Decimal)
    assert str(exact).startswith("51.8272923729877")
    assert abs(float(exact) - G.ATAN_SQRT_PHI_DEG) < 1e-13


def test_float_and_high_precision_angles_differ_only_in_the_last_ulp():
    """The float chain is one unit in the last place off. Recorded, not hidden."""
    gap = abs(G.ATAN_SQRT_PHI_FLOAT_VS_EXACT_DEG)
    assert 0.0 < gap < 1e-13
    # and it is utterly negligible against the 51.843 gap
    assert gap < abs(G.SUPPLIED_ANGLE_COMPARISON["difference_deg"]) / 1e9


def test_high_precision_angle_is_computed_not_looked_up():
    """tan(atan(sqrt(phi))) == sqrt(phi), at 60 digits."""
    with localcontext() as ctx:
        ctx.prec = 70
        rad = G.atan_sqrt_phi_rad(70)
        # sin/cos via the identity tan = s / sqrt(1 - s^2) is awkward in
        # Decimal; check instead that doubling back through the degree
        # conversion is self-consistent and that the radian value is the
        # right size for an angle a shade over 45 degrees.
        pi = G._dec_pi(70)
        deg = rad * Decimal(180) / pi
        assert abs(deg - G.atan_sqrt_phi_deg(70)) < Decimal(1).scaleb(-60)
    assert math.tan(float(rad)) == pytest.approx(G.SQRT_PHI, rel=1e-15)
    assert 45.0 < float(deg) < 60.0


# --- the comparison that must not be rounded away ----------------------

def test_compare_to_51_843_returns_the_exact_difference():
    cmp = G.compare_to(51.843)
    assert cmp["supplied_deg"] == 51.843
    assert cmp["exact_deg"] == 51.827292372987756
    # the verified difference, to the last digit a double carries
    assert cmp["difference_deg"] == 0.01570762701224737
    assert cmp["difference_deg"] == pytest.approx(0.015707627, abs=1e-9)


def test_compare_to_51_843_is_not_equal_and_says_so():
    cmp = G.compare_to(51.843)
    assert cmp["equal"] is False
    assert cmp["verdict"] == "APPROXIMATE_NOT_EXACT"
    assert cmp["verdict"] == G.ANGLE_VERDICT


def test_compare_to_high_precision_difference_agrees_with_the_float():
    cmp = G.compare_to(51.843)
    hp = float(Decimal(cmp["difference_deg_high_precision"]))
    assert hp == pytest.approx(cmp["difference_deg"], rel=1e-10)
    assert hp > 0.0


def test_the_difference_is_about_56_arcseconds_and_3e_minus_4_relative():
    cmp = G.compare_to(51.843)
    assert cmp["difference_arcsec"] == pytest.approx(56.547, abs=0.01)
    assert cmp["relative_difference"] == pytest.approx(3.0308e-4, rel=1e-3)


def test_the_difference_survives_at_every_working_precision():
    for prec in (20, 40, 60, 90):
        cmp = G.compare_to(51.843, precision=prec)
        assert cmp["equal"] is False
        assert cmp["verdict"] == "APPROXIMATE_NOT_EXACT"
        assert float(Decimal(cmp["difference_deg_high_precision"])) > 1e-3


def test_rounding_is_what_hides_the_gap_and_the_module_says_where():
    """The trap, made explicit: they share 51.8 and nothing more."""
    cmp = G.compare_to(51.843)
    assert cmp["agree_to_significant_figures"] == 3
    assert cmp["agree_to_decimal_places"] == 1
    # rounded to the one decimal place they share, they agree
    assert round(51.843, 1) == round(G.ATAN_SQRT_PHI_DEG, 1) == 51.8
    # one digit further and they do not
    assert round(51.843, 2) != round(G.ATAN_SQRT_PHI_DEG, 2)
    assert round(51.843, 3) != round(G.ATAN_SQRT_PHI_DEG, 3)
    # unrounded, they never agree
    assert 51.843 != G.ATAN_SQRT_PHI_DEG


def test_compare_to_the_exact_value_itself_reports_equal():
    """The EXACT branch is reachable, so APPROXIMATE_NOT_EXACT is a finding."""
    cmp = G.compare_to(G.ATAN_SQRT_PHI_DEG_EXACT)
    assert cmp["equal"] is True
    assert cmp["verdict"] == "EXACT"
    assert cmp["verdict"] == G.ANGLE_VERDICT_IF_EQUAL


def test_compare_to_rejects_a_non_number():
    with pytest.raises(G.GeomInverseError):
        G.compare_to(None)
    with pytest.raises(G.GeomInverseError):
        G.compare_to(True)


def test_module_level_comparison_is_the_headline_one():
    assert G.SUPPLIED_ANGLE_DEG == 51.843
    assert G.SUPPLIED_ANGLE_COMPARISON["difference_deg"] == 0.01570762701224737
    assert G.SUPPLIED_ANGLE_COMPARISON["verdict"] == "APPROXIMATE_NOT_EXACT"


# --- the refusal --------------------------------------------------------

def test_refuse_exact_angle_claim_raises():
    with pytest.raises(G.GeomInverseError):
        G.refuse_exact_angle_claim()


def test_refuse_exact_angle_claim_states_the_gap_and_the_verdict():
    with pytest.raises(G.GeomInverseError) as exc:
        G.refuse_exact_angle_claim(51.843)
    message = str(exc.value)
    assert "51.843" in message
    assert "0.01570762701224737" in message
    assert "APPROXIMATE_NOT_EXACT" in message
    assert "rounded away" in message


def test_refuse_exact_angle_claim_refuses_either_way():
    for claimed in (True, False):
        with pytest.raises(G.GeomInverseError):
            G.refuse_exact_angle_claim(51.843, claimed_exact=claimed)


# =======================================================================
# Part 2 -- the parametric family and its forward maps
# =======================================================================

CYLINDER = G.BodyParams(height_mm=200.0, base_radius_mm=10.0, taper=0.0,
                        density_kg_m3=2700.0, youngs_modulus_pa=7.0e10)


def test_a_cylinder_has_its_centroid_at_half_height():
    assert G.centroid_z(CYLINDER) == pytest.approx(100.0, rel=1e-15)


def test_centroid_matches_numerical_integration_for_a_taper():
    p = G.BodyParams(height_mm=240.0, base_radius_mm=18.0, taper=0.35,
                     density_kg_m3=2700.0, youngs_modulus_pa=7.0e10)
    z = np.linspace(0.0, p.height_mm, 200001)
    r = p.base_radius_mm * (1.0 - p.taper * z / p.height_mm)
    w = r * r
    numeric = float(np.trapezoid(w * z, z) / np.trapezoid(w, z))
    assert G.centroid_z(p) == pytest.approx(numeric, rel=1e-8)


def test_centroid_is_blind_to_radius_density_and_stiffness():
    a = G.BodyParams(240.0, 18.0, 0.35, 2700.0, 7.0e10)
    b = G.BodyParams(240.0, 3.0, 0.35, 19300.0, 4.1e11)
    assert G.centroid_z(a) == pytest.approx(G.centroid_z(b), rel=1e-15)


def test_centroid_scales_linearly_with_height():
    a = G.BodyParams(200.0, 10.0, 0.4, 2700.0, 7.0e10)
    b = G.BodyParams(400.0, 10.0, 0.4, 2700.0, 7.0e10)
    assert G.centroid_z(b) == pytest.approx(2.0 * G.centroid_z(a), rel=1e-14)


def test_frequency_is_the_declared_bar_mode():
    f = G.fundamental_frequency(CYLINDER)
    expected = math.sqrt(7.0e10 / 2700.0) / (2.0 * 0.200)
    assert f == pytest.approx(expected, rel=1e-15)


def test_frequency_is_blind_to_taper_and_radius():
    a = G.BodyParams(240.0, 18.0, 0.0, 2700.0, 7.0e10)
    b = G.BodyParams(240.0, 55.0, 0.9, 2700.0, 7.0e10)
    assert G.fundamental_frequency(a) == pytest.approx(
        G.fundamental_frequency(b), rel=1e-15)


def test_frequency_sees_only_the_ratio_of_stiffness_to_density():
    a = G.BodyParams(240.0, 18.0, 0.3, 2700.0, 7.0e10)
    b = G.BodyParams(240.0, 18.0, 0.3, 2700.0 * 3.0, 7.0e10 * 3.0)
    assert G.fundamental_frequency(a) == pytest.approx(
        G.fundamental_frequency(b), rel=1e-14)
    assert a.density_kg_m3 != b.density_kg_m3


def test_bad_parameters_are_refused():
    with pytest.raises(G.GeomInverseError):
        G.BodyParams(-1.0, 10.0, 0.0, 2700.0, 7.0e10)
    with pytest.raises(G.GeomInverseError):
        G.BodyParams(200.0, 10.0, 1.5, 2700.0, 7.0e10)
    with pytest.raises(G.GeomInverseError):
        G.BodyParams(200.0, 10.0, 0.0, 0.0, 7.0e10)
    with pytest.raises(G.GeomInverseError):
        G.BodyParams(float("nan"), 10.0, 0.0, 2700.0, 7.0e10)


def test_forward_maps_reject_a_non_bodyparams():
    with pytest.raises(G.GeomInverseError):
        G.centroid_z({"height_mm": 200.0})
    with pytest.raises(G.GeomInverseError):
        G.fundamental_frequency(None)


def test_params_from_vector_round_trips():
    p = G.BodyParams(240.0, 18.0, 0.35, 2700.0, 7.0e10)
    q = G.params_from_vector(p.as_vector())
    assert q == p
    with pytest.raises(G.GeomInverseError):
        G.params_from_vector([1.0, 2.0])


# =======================================================================
# POWER -- the solver recovers a planted problem
# =======================================================================

PLANTED = G.DEFAULT_PLANTED_PARAMS


def test_planted_body_meets_its_own_constraints():
    c = G.centroid_z(PLANTED)
    f = G.fundamental_frequency(PLANTED)
    assert G.meets_constraints(PLANTED, c, f)


def test_solver_recovers_a_body_meeting_the_planted_constraints():
    c = G.centroid_z(PLANTED)
    f = G.fundamental_frequency(PLANTED)
    result = G.solve_inverse(c, f, restarts=12, seed=7)
    best = result["solutions"][0]
    assert G.meets_constraints(best, c, f)
    assert G.centroid_z(best) == pytest.approx(c, rel=1e-8)
    assert G.fundamental_frequency(best) == pytest.approx(f, rel=1e-8)


def test_power_check_detects_the_planted_problem():
    power = G.power_check(restarts=12, seed=7)
    assert power["planted_meets_its_own_constraints"] is True
    assert power["recovered_meets_constraints"] is True
    assert power["detected"] is True


def test_power_check_does_not_recover_the_planted_body_itself():
    """The solver solves the constraints; it cannot single out the body."""
    power = G.power_check(restarts=12, seed=7)
    assert power["recovered_equals_planted"] is False
    assert power["max_relative_param_difference"] > 1e-3


def test_solver_reaches_the_declared_default_target():
    result = G.solve_inverse()
    assert result["target_centroid_mm"] == 100.0
    assert result["target_centroid_point_mm"] == (0.0, 0.0, 100.0)
    assert result["max_relative_residual"] <= G.DEFAULT_TOLERANCE


def test_solver_rejects_nonsense_targets():
    with pytest.raises(G.GeomInverseError):
        G.solve_inverse(0.0, 1000.0)
    with pytest.raises(G.GeomInverseError):
        G.solve_inverse(100.0, -1.0)
    with pytest.raises(G.GeomInverseError):
        G.solve_inverse(100.0, 1000.0, restarts=0)


# =======================================================================
# UNDERDETERMINATION -- the headline
# =======================================================================

def test_solve_inverse_reports_no_unique_solution():
    result = G.solve_inverse()
    assert result["unique_solution"] is False
    assert result["verdict"] == "CENTROID_INVERSE_UNDERDETERMINED"
    assert result["solution_set_dimension"] == 3


def test_solve_inverse_returns_at_least_three_distinct_solutions():
    result = G.solve_inverse()
    assert result["n_distinct_solutions"] >= 3
    assert len(result["solutions"]) == result["n_distinct_solutions"]


def test_solution_family_returns_at_least_three_members():
    family = G.solution_family(count=3)
    assert len(family) >= 3


def test_every_family_member_meets_both_constraints():
    family = G.solution_family(count=6)
    assert len(family) >= 6
    for member in family:
        assert G.meets_constraints(member)
        assert G.centroid_z(member) == pytest.approx(100.0, rel=1e-8)
        assert G.fundamental_frequency(member) == pytest.approx(
            G.DEFAULT_TARGET_FREQ_HZ, rel=1e-8)


def test_family_members_are_genuinely_different_from_each_other():
    family = G.solution_family(count=6)
    for i in range(len(family)):
        for j in range(i + 1, len(family)):
            a = family[i].as_vector()
            b = family[j].as_vector()
            rel = float(np.max(np.abs(a - b) / np.abs(b)))
            assert rel > G.DEFAULT_DISTINCT_TOL, (
                f"members {i} and {j} are near-copies")


def test_the_family_spans_every_parameter_by_a_wide_margin():
    family = G.solution_family(count=6)
    spread = G.family_spread(family)
    assert spread["n_members"] >= 6
    # heights and tapers must genuinely differ, not merely wobble
    assert spread["ratio_max_over_min"]["height_mm"] > 1.1
    assert spread["ratio_max_over_min"]["taper"] > 2.0
    assert spread["ratio_max_over_min"]["base_radius_mm"] > 2.0
    assert spread["ratio_max_over_min"]["density_kg_m3"] > 2.0


def test_family_spread_needs_more_than_one_member():
    with pytest.raises(G.GeomInverseError):
        G.family_spread(G.solution_family(count=1)[:1])


def test_a_different_seed_finds_a_different_family():
    """The member reported is decided by the search, not by the data."""
    a = G.solution_family(count=3, seed=11)
    b = G.solution_family(count=3, seed=97)
    assert a[0].as_dict() != b[0].as_dict()
    for member in (a[0], b[0]):
        assert G.meets_constraints(member)


# --- identifiability ----------------------------------------------------

def test_identifiability_reports_a_two_by_five_jacobian():
    ident = G.identifiability()
    assert ident["n_params"] == 5
    assert ident["n_constraints"] == 2
    assert ident["jacobian_shape"] == [2, 5]


def test_identifiability_reports_rank_deficiency():
    ident = G.identifiability()
    assert ident["rank"] == 2
    assert ident["rank_deficiency"] == 3
    assert ident["null_space_dimension"] == 3
    assert ident["identifiable"] is False
    assert ident["verdict"] == "NON_IDENTIFIABLE"


def test_base_radius_has_exactly_zero_sensitivity():
    ident = G.identifiability()
    assert "base_radius_mm" in ident["zero_sensitivity_params"]
    assert ident["column_norms"]["base_radius_mm"] == 0.0
    # while the parameters that do move something are non-zero
    assert ident["column_norms"]["height_mm"] > 0.0
    assert ident["column_norms"]["taper"] > 0.0


def test_identifiability_is_rank_deficient_at_every_family_member():
    for member in G.solution_family(count=4):
        ident = G.identifiability(member)
        assert ident["rank"] < ident["n_params"]
        assert ident["verdict"] == "NON_IDENTIFIABLE"


def test_constraint_jacobian_shape_and_zero_column():
    j = G.constraint_jacobian(PLANTED)
    assert j.shape == (2, 5)
    radius_column = j[:, G.PARAM_NAMES.index("base_radius_mm")]
    assert np.allclose(radius_column, 0.0)
    assert np.linalg.matrix_rank(j) == 2


def test_the_centroid_row_ignores_density_and_stiffness():
    j = G.constraint_jacobian(PLANTED)
    row = j[G.CONSTRAINT_NAMES.index("centroid_z_mm")]
    assert row[G.PARAM_NAMES.index("density_kg_m3")] == pytest.approx(0.0,
                                                                     abs=1e-9)
    assert row[G.PARAM_NAMES.index("youngs_modulus_pa")] == pytest.approx(
        0.0, abs=1e-9)


def test_the_frequency_row_ignores_the_taper():
    j = G.constraint_jacobian(PLANTED)
    row = j[G.CONSTRAINT_NAMES.index("fundamental_frequency_hz")]
    assert row[G.PARAM_NAMES.index("taper")] == pytest.approx(0.0, abs=1e-9)


# --- the headline refusal ----------------------------------------------

def test_refuse_unique_geometry_raises():
    with pytest.raises(G.GeomInverseError):
        G.refuse_unique_geometry()


def test_refuse_unique_geometry_raises_however_it_is_asked():
    for args in (
        (),
        (100.0, 12500.0),
        (100.0, 12500.0, "residual is 1e-15 and the fit is clean"),
    ):
        with pytest.raises(G.GeomInverseError):
            G.refuse_unique_geometry(*args)


def test_refuse_unique_geometry_states_the_counting_argument():
    with pytest.raises(G.GeomInverseError) as exc:
        G.refuse_unique_geometry(100.0, 12500.0)
    message = str(exc.value)
    assert "100.0" in message
    assert "2 x 5" in message
    assert "solution_family()" in message
    assert "CENTROID_INVERSE_UNDERDETERMINED" in message


# =======================================================================
# The report
# =======================================================================

def test_report_measures_nothing_and_claims_no_physical_validation():
    report = G.geominverse_report()
    assert report["measured_here"] == "nothing"
    assert report["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"


def test_report_carries_the_required_verdict():
    report = G.geominverse_report()
    assert report["verdict"] == "CENTROID_INVERSE_UNDERDETERMINED"
    assert report["verdict"] == G.VERDICT


def test_report_declares_both_evidence_classes():
    report = G.geominverse_report()
    assert "DERIVED_ARITHMETIC" in report["evidence_class"]
    assert "ANALYTIC_MODEL" in report["evidence_class"]
    assert report["exact_constants"]["evidence_class"] == "DERIVED_ARITHMETIC"
    assert report["parametric_family"]["evidence_class"] == "ANALYTIC_MODEL"


def test_report_states_what_it_does_not_say():
    report = G.geominverse_report()
    text = report["what_this_does_not_say"]
    assert "51.843" in text
    assert "coincidence" in text
    assert "SOLUTION FAMILY" in text
    assert "Nothing was weighed" in text


def test_report_carries_the_angle_comparison_unrounded():
    report = G.geominverse_report()
    assert report["angle_verdict"] == "APPROXIMATE_NOT_EXACT"
    assert report["angle_comparison"]["difference_deg"] == 0.01570762701224737
    assert report["exact_constants"]["phi"] == 1.618033988749895
    assert report["exact_constants"]["sqrt_phi"] == 1.272019649514069
    assert report["exact_constants"]["atan_sqrt_phi_deg"] == \
        51.827292372987756


def test_report_carries_a_family_not_an_answer():
    report = G.geominverse_report()
    assert report["solution_family"]["n_members"] >= 3
    assert report["solution_family"]["all_meet_constraints"] is True
    assert report["identifiability"]["verdict"] == "NON_IDENTIFIABLE"
    assert report["power_control"]["detected"] is True
    assert report["target"]["centroid_mm"] == (0.0, 0.0, 100.0)


def test_report_lists_both_refusals():
    report = G.geominverse_report()
    assert "refuse_exact_angle_claim" in report["refusals"]
    assert "refuse_unique_geometry" in report["refusals"]


def test_report_is_deterministic_for_a_fixed_seed():
    a = G.geominverse_report(seed=5)
    b = G.geominverse_report(seed=5)
    assert a["solution_family"]["members"] == b["solution_family"]["members"]
