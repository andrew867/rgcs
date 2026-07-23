"""R11 — planetary orbital levels versus atomic shells.

The load-bearing tests: the fitter demonstrably works (planted ``n**2``
data is recovered by the hydrogenic model), the random order-statistic
control is competitive with the "meaningful" models on the eight-planet
set, frozen parameters do not transfer to an independent system, and
neither refusal can be talked out of raising.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from r11 import orbitalscaling as O


@pytest.fixture(scope="module")
def report() -> dict:
    """One report for the whole module; the nulls are Monte Carlo."""
    return O.orbitalscaling_report(null_trials=120)


# --- the datasets are well formed --------------------------------------

def test_three_independent_systems_are_declared():
    assert set(O.SYSTEMS) == {"solar_planets", "jovian_galilean",
                              "saturnian_major"}


def test_every_system_is_sorted_outward_and_dimensionless_after_scaling():
    for s in O.SYSTEMS.values():
        a = np.asarray(s.semi_major_axis, float)
        assert np.all(np.diff(a) > 0)
        assert s.scale.units == s.units
        norm = s.normalized()
        assert np.all(norm > 0) and np.all(np.isfinite(norm))
        assert len(norm) == s.n == len(s.bodies)


def test_the_eight_planets_carry_their_published_axes():
    assert O.SOLAR_SYSTEM.bodies[0] == "Mercury"
    assert O.SOLAR_SYSTEM.semi_major_axis[2] == pytest.approx(1.000)
    assert O.SOLAR_SYSTEM.semi_major_axis[-1] == pytest.approx(30.069)
    assert O.SOLAR_SYSTEM.n == 8


def test_a_system_listed_inward_is_refused():
    with pytest.raises(O.ScalingError):
        O.OrbitalSystem("bad", "X", "km", ("a", "b", "c"),
                        (3.0, 2.0, 1.0), O.JOVIAN_SCALES[0])


def test_a_scale_in_the_wrong_units_is_refused():
    with pytest.raises(O.ScalingError):
        O.OrbitalSystem("bad", "X", "AU", ("a", "b", "c"),
                        (1.0, 2.0, 3.0), O.JOVIAN_SCALES[0])


# --- every model fits and returns a finite in-sample error --------------

def test_every_model_fits_the_solar_system_with_finite_error():
    fits = O.fit_models(O.SOLAR_SYSTEM.normalized(), include_null=False,
                        system=O.SOLAR_SYSTEM)
    for name in O.STRUCTURED_MODELS:
        f = fits[name]
        assert f.status == "FIT"
        assert math.isfinite(f.rms_log_error)
        assert f.rms_log_error > 0.0
        assert f.n_params >= 1
        assert f.n_points == 8


def test_every_model_fits_every_system():
    for s in O.SYSTEMS.values():
        for name, fn in O.FITTERS.items():
            f = fn(s.normalized())
            assert math.isfinite(f.rms_log_error), (s.system_id, name)


def test_fit_models_reports_the_control_and_the_blocked_model():
    fits = O.fit_models(O.SOLAR_SYSTEM.normalized(), null_trials=25,
                        system=O.SOLAR_SYSTEM)
    assert set(fits) == set(O.STRUCTURED_MODELS) | {O.NULL_MODEL,
                                                    "formation_informed"}
    assert fits[O.NULL_MODEL].status == "CONTROL"
    assert fits["formation_informed"].status == O.BLOCKED_MISSING_DATA


def test_the_formation_informed_model_is_blocked_not_guessed():
    f = O.formation_informed_model(O.SOLAR_SYSTEM)
    assert f.status == O.BLOCKED_MISSING_DATA
    assert math.isnan(f.rms_log_error)
    assert "migration" in f.note


def test_the_control_can_never_be_selected_as_an_explanation():
    fits = O.fit_models(O.SOLAR_SYSTEM.normalized(), null_trials=25)
    assert O.best_model(fits).model in O.STRUCTURED_MODELS


def test_fewer_than_three_radii_cannot_test_a_law():
    with pytest.raises(O.ScalingError):
        O.fit_models([1.0, 2.0])


# --- power: the fitter actually works ----------------------------------

def test_data_generated_from_n_squared_is_best_fit_by_the_hydrogenic_model():
    """If planted hydrogenic data were NOT recovered, every null result
    below would be a broken fitter rather than a finding."""
    n = np.arange(1, 9, dtype=float)
    planted = 3.7 * n ** 2
    fits = O.fit_models(planted, include_null=False)
    assert fits["hydrogenic"].rms_log_error < 1e-9
    assert O.best_model(fits).model == "hydrogenic"


def test_planted_n_squared_survives_a_little_noise():
    rng = np.random.default_rng(4)
    n = np.arange(1, 9, dtype=float)
    planted = np.sort(3.7 * n ** 2 * np.exp(rng.normal(0.0, 0.01, 8)))
    fits = O.fit_models(planted, include_null=False)
    assert O.best_model(fits).model == "hydrogenic"
    assert fits["hydrogenic"].rms_log_error < 0.05


def test_the_power_law_fitter_recovers_a_planted_exponent():
    n = np.arange(1, 9, dtype=float)
    for p_true in (1.0, 1.5, 2.0, 2.5):
        fit = O.fit_power_law(0.9 * n ** p_true)
        assert fit.params["p"] == pytest.approx(p_true, abs=1e-6)
        assert fit.rms_log_error < 1e-9


def test_planted_geometric_data_is_best_fit_by_the_geometric_model():
    n = np.arange(1, 9, dtype=float)
    fits = O.fit_models(2.0 * 1.7 ** n, include_null=False)
    assert O.best_model(fits).model == "geometric"
    assert fits["geometric"].params["k"] == pytest.approx(1.7, rel=1e-6)


# --- the null: sorted noise fits about as well --------------------------

def test_the_random_order_statistic_null_is_competitive_on_eight_planets():
    """The headline. A handful of sorted radii fit something almost
    always, so the planetary fit is not evidence of a shell structure."""
    res = O.random_null_comparison(O.SOLAR_SYSTEM.normalized(), trials=200,
                                   seed=20260723)
    assert res["p_value"] > 0.05
    assert res["null_competitive"] is True
    assert res["verdict"] == "NO_BETTER_THAN_CHANCE"
    # the control's median error is the same order as the observed one
    assert res["null_error_ratio"] < 3.0
    # and a healthy slice of pure noise fits strictly better
    assert res["null_q10_rms_log_error"] < res["observed_rms_log_error"]


def test_the_null_is_stable_across_seeds():
    for seed in (1, 77, 20260723):
        res = O.random_null_comparison(O.SOLAR_SYSTEM.normalized(),
                                       trials=120, seed=seed)
        assert res["verdict"] == "NO_BETTER_THAN_CHANCE"


def test_the_control_error_sits_near_the_structured_errors():
    solar = O.SOLAR_SYSTEM.normalized()
    fits = O.fit_models(solar, include_null=False)
    structured = [f.rms_log_error for f in fits.values()
                  if f.status == "FIT"]
    control = O.null_order_statistic(solar, trials=120).rms_log_error
    assert min(structured) < control < max(structured)


def test_the_control_draws_match_the_observed_count_and_range():
    rng = np.random.default_rng(0)
    r = O.SOLAR_SYSTEM.normalized()
    draw = O.random_sorted_radii(len(r), float(r[0]), float(r[-1]), rng)
    assert len(draw) == len(r)
    assert np.all(np.diff(draw) > 0)
    assert draw[0] == pytest.approx(r[0], rel=1e-6)
    assert draw[-1] == pytest.approx(r[-1], rel=1e-6)


def test_the_control_refuses_a_degenerate_range():
    rng = np.random.default_rng(0)
    with pytest.raises(O.ScalingError):
        O.random_sorted_radii(8, 5.0, 5.0, rng)


def test_the_hydrogenic_shape_is_the_worst_fit_in_every_real_system():
    """The shape the analogy actually predicts, r = A n^2, fits every
    real system worse than any competing family."""
    for s in O.SYSTEMS.values():
        errs = {n: fn(s.normalized()).rms_log_error
                for n, fn in O.FITTERS.items()}
        assert errs["hydrogenic"] == max(errs.values()), s.system_id


def test_an_exponent_near_two_is_not_the_good_news_it_looks_like():
    """The planets do fit p ~ 2.1 -- with a residual so large the fit is
    worthless, and with no other system agreeing."""
    solar = O.fit_power_law(O.SOLAR_SYSTEM.normalized())
    assert solar.params["p"] == pytest.approx(2.0, abs=0.25)
    assert solar.rms_log_error > 0.4          # a factor-1.5 typical miss
    jov = O.fit_power_law(O.JOVIAN_GALILEAN.normalized())
    assert abs(jov.params["p"] - 2.0) > 0.5


def test_fitted_exponents_are_not_universal():
    ex = O.fitted_exponents()
    assert ex["universal"] is False
    assert ex["spread"] > 0.5


# --- out of sample: nothing transfers -----------------------------------

def test_planet_parameters_do_not_transfer_to_a_moon_system():
    res = O.out_of_sample_error(O.SOLAR_SYSTEM, O.JOVIAN_GALILEAN)
    assert res["out_of_sample_rms_log_error"] > \
        res["in_sample_rms_log_error"]
    assert res["degradation_factor"] > 3.0
    assert res["verdict"] == "NO_UNIVERSAL_MAPPING"


def test_no_model_at_all_survives_the_move_to_another_system():
    for eval_system in (O.JOVIAN_GALILEAN, O.SATURNIAN_MAJOR):
        res = O.out_of_sample_error(O.SOLAR_SYSTEM, eval_system)
        for name, row in res["per_model"].items():
            assert (row["out_of_sample_rms_log_error"]
                    > 2.0 * row["in_sample_rms_log_error"]), name


def test_transfer_fails_in_both_directions():
    there = O.out_of_sample_error(O.JOVIAN_GALILEAN, O.SATURNIAN_MAJOR)
    assert there["degradation_factor"] > 3.0
    assert there["verdict"] == "NO_UNIVERSAL_MAPPING"


def test_a_system_is_not_a_holdout_for_itself():
    with pytest.raises(O.ScalingError):
        O.out_of_sample_error(O.SOLAR_SYSTEM, O.SOLAR_SYSTEM)


def test_a_fitted_resonance_chain_cannot_be_stretched_to_new_bodies():
    fit = O.fit_resonance_chain(O.JOVIAN_GALILEAN.normalized())
    with pytest.raises(O.ScalingError):
        O.predict("resonance_chain", fit.params, 8)


def test_predict_rejects_an_unknown_model():
    with pytest.raises(O.ScalingError):
        O.predict("shell_structure", {}, 4)


# --- normalisation discipline -------------------------------------------

def test_per_target_normalization_is_refused():
    with pytest.raises(O.ScalingError) as e:
        O.refuse_per_target_normalization(
            O.SOLAR_SYSTEM, [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])
    assert "one free parameter per" in str(e.value)


def test_a_whole_system_renormalization_is_allowed():
    alt = O.renormalize(O.SOLAR_SYSTEM, O.ScaleKind.SYNCHRONOUS_ORBIT)
    assert alt.scale.kind is O.ScaleKind.SYNCHRONOUS_ORBIT
    assert alt.n == O.SOLAR_SYSTEM.n
    ratio = alt.normalized() / O.SOLAR_SYSTEM.normalized()
    assert np.allclose(ratio, ratio[0])       # one scale, every body


def test_an_undeclared_scale_cannot_be_invented():
    with pytest.raises(O.ScalingError):
        O.renormalize(O.SOLAR_SYSTEM, O.ScaleKind.HILL_RADIUS)


def test_the_verdict_does_not_depend_on_which_declared_scale_is_used():
    """Changing the declared scale is a uniform shift in log space, so it
    cannot rescue the claim -- which is exactly why per-target
    normalisation is the temptation that has to be blocked."""
    base = O.random_null_comparison(O.SOLAR_SYSTEM.normalized(), trials=120,
                                    seed=5)
    alt = O.renormalize(O.SOLAR_SYSTEM, O.ScaleKind.ROCHE_LIMIT)
    other = O.random_null_comparison(alt.normalized(), trials=120, seed=5)
    assert base["observed_rms_log_error"] == pytest.approx(
        other["observed_rms_log_error"], rel=1e-6)
    assert base["verdict"] == other["verdict"]


# --- the refusal that matters -------------------------------------------

def test_shared_physics_cannot_be_read_off_a_good_fit():
    with pytest.raises(O.ScalingError) as e:
        O.refuse_shared_physics_from_fit("titius_bode", 1e-9,
                                         "solar_planets")
    assert "not evidence of shared physics" in str(e.value)


def test_even_a_perfect_fit_is_refused():
    with pytest.raises(O.ScalingError):
        O.refuse_shared_physics_from_fit("hydrogenic", 0.0)


# --- look elsewhere ------------------------------------------------------

def test_look_elsewhere_correction_shrinks_significance_as_the_search_grows():
    small = O.look_elsewhere_correction(2, 1, p_value=0.01)
    big = O.look_elsewhere_correction(5, 3, p_value=0.01)
    assert big["corrected_p_value"] > small["corrected_p_value"]
    assert big["corrected_alpha"] < small["corrected_alpha"]
    assert big["effective_trials"] == 15


def test_a_marginal_result_stops_being_significant_after_correction():
    one = O.look_elsewhere_correction(1, 1, p_value=0.02)
    many = O.look_elsewhere_correction(5, 3, p_value=0.02)
    assert one["significant_after_correction"] is True
    assert many["significant_after_correction"] is False


def test_the_corrected_p_value_is_clipped_at_one():
    res = O.look_elsewhere_correction(5, 3, p_value=0.5)
    assert res["corrected_p_value"] == 1.0


def test_look_elsewhere_correction_rejects_nonsense_inputs():
    with pytest.raises(O.ScalingError):
        O.look_elsewhere_correction(0, 3)
    with pytest.raises(O.ScalingError):
        O.look_elsewhere_correction(5, 3, p_value=1.5)


# --- the error metric ----------------------------------------------------

def test_rms_log_error_is_zero_on_an_exact_prediction():
    r = O.SOLAR_SYSTEM.normalized()
    assert O.rms_log_error(r, r) == pytest.approx(0.0)


def test_rms_log_error_is_scale_free():
    r = O.SOLAR_SYSTEM.normalized()
    pred = O.predict("power_law", O.fit_power_law(r).params, len(r))
    assert O.rms_log_error(r, pred) == pytest.approx(
        O.rms_log_error(1000.0 * r, 1000.0 * pred))


def test_rms_log_error_rejects_a_shape_mismatch():
    with pytest.raises(O.ScalingError):
        O.rms_log_error([1.0, 2.0, 3.0], [1.0, 2.0])


def test_a_nonpositive_prediction_is_infinitely_wrong_not_a_crash():
    assert math.isinf(O.rms_log_error([1.0, 2.0, 3.0], [1.0, -2.0, 3.0]))


# --- claim discipline ----------------------------------------------------

def test_report_holds_the_default_verdict(report):
    r = report
    assert r["verdict"] == "ORBITAL_ATOMIC_SCALING_UNESTABLISHED"
    assert r["verdict"] == O.VERDICT_UNESTABLISHED
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["evidence_class"] == "DERIVED_MATHEMATICS"


def test_report_states_the_physics_distinction_and_the_trap(report):
    r = report
    assert "eigenvalue" in r["physics_distinction"]
    assert "no established universal" in r["physics_distinction"]
    assert "almost always" in r["the_trap"]
    assert "identical search" in r["the_test"]


def test_report_disclaims_quantised_orbits_and_lucky_residuals(report):
    r = report
    n = r["what_this_does_not_say"]
    assert "quantised" in n
    assert "sorted random radii reach" in n
    assert "do not transfer" in n


def test_report_carries_the_control_and_both_refusals(report):
    r = report
    assert O.NULL_MODEL in r["models_compared"]
    assert r["blocked_models"]["formation_informed"] == "BLOCKED_MISSING_DATA"
    assert set(r["refusals"]) == {"refuse_per_target_normalization",
                                  "refuse_shared_physics_from_fit"}


def test_report_carries_the_negative_null_and_the_failed_transfer(report):
    r = report
    assert r["random_null"]["verdict"] == "NO_BETTER_THAN_CHANCE"
    assert r["out_of_sample"]["verdict"] == "NO_UNIVERSAL_MAPPING"
    assert r["fitted_exponents"]["universal"] is False


def test_report_does_not_hide_the_one_system_that_beats_chance(report):
    r = report
    jov = r["per_system_null"]["jovian_galilean"]
    assert jov["verdict"] == "TIGHTER_THAN_CHANCE"
    assert "Laplace resonance" in r["the_one_system_that_beats_chance"]
    # and it does not survive the correction for the whole search
    assert r["look_elsewhere"]["significant_after_correction"] is False


def test_the_module_names_no_private_source():
    import inspect
    text = inspect.getsource(O).lower()
    # The tokens are assembled from fragments on purpose: a guard that
    # spells the forbidden literal writes that literal into the public
    # tree and trips the publication firewall on itself.
    forbidden = ("c:" + chr(92) + "users", "one" + "drive",
                 "rgcs" + "-" + "priv" + "ate")
    for token in forbidden:
        assert token not in text
