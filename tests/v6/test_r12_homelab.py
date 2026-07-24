"""R12 home-lab experiments — mode, phase, ringdown and isotropy.

All four experiments have a plan with non-empty controls and a
falsification criterion, all at status BLOCKED_MISSING_DATA. The ringdown
Q is recovered from a synthetic decay (POWER) and Q = pi*f0*tau matches
f0/FWHM. The isotropy null gives a p that is not small on isotropic data
and the isotropy power gives a small p on a planted cos(2*theta). The
three refusals — anisotropy-as-anomaly, result-without-controls, and the
bench claim — all raise.
"""

from __future__ import annotations

import math

import pytest

from r12 import homelab as HL


# --- (1) the four experiment plans ---------------------------------------

def test_there_are_exactly_four_typed_experiments():
    assert len(HL.Experiment) == 4
    assert {e.value for e in HL.Experiment} == {
        "MODE_SURVEY", "PHASE_RELATION", "RINGDOWN_Q", "ISOTROPY"}


def test_every_experiment_has_a_full_plan_and_is_blocked():
    for experiment in HL.Experiment:
        plan = HL.experiment_plan(experiment)
        assert plan.status == "BLOCKED_MISSING_DATA"
        assert plan.controls, experiment
        assert len(set(plan.controls)) == len(plan.controls)
        assert plan.observables
        assert plan.aim.strip()
        assert plan.null_model.strip()
        assert plan.falsification_criterion.strip()
        assert plan.anti_aliasing.strip()
        assert plan.sample_rate_hz > 0.0
        assert isinstance(plan.cost_tier, HL.CostTier)


def test_a_plan_cannot_carry_a_non_blocked_status():
    with pytest.raises(HL.HomeLabError):
        HL.ExperimentPlan(
            experiment=HL.Experiment.MODE_SURVEY, aim="a", drive="b",
            observables=("x",), sample_rate_hz=1000.0, anti_aliasing="c",
            controls=(HL.Control.NO_DRIVE_BASELINE,), null_model="d",
            falsification_criterion="e", cost_tier=HL.CostTier.LOW,
            status="BENCH_MEASUREMENT")


def test_a_plan_needs_controls_and_a_falsification_criterion():
    with pytest.raises(HL.HomeLabError):
        HL.ExperimentPlan(
            experiment=HL.Experiment.MODE_SURVEY, aim="a", drive="b",
            observables=("x",), sample_rate_hz=1000.0, anti_aliasing="c",
            controls=(), null_model="d",
            falsification_criterion="e", cost_tier=HL.CostTier.LOW)
    with pytest.raises(HL.HomeLabError):
        HL.ExperimentPlan(
            experiment=HL.Experiment.MODE_SURVEY, aim="a", drive="b",
            observables=("x",), sample_rate_hz=1000.0, anti_aliasing="c",
            controls=(HL.Control.NO_DRIVE_BASELINE,), null_model="d",
            falsification_criterion="   ", cost_tier=HL.CostTier.LOW)


# --- (2) the ringdown estimator ------------------------------------------

def test_the_two_q_formulas_are_the_same_number():
    """Q = pi*f0*tau equals f0/FWHM because FWHM = 1/(pi*tau)."""
    f0, tau = 1000.0, 0.05
    q_tau = HL.ringdown_q_from_tau(f0, tau)
    q_fwhm = HL.ringdown_q_from_fwhm(f0, HL.fwhm_from_tau(tau))
    assert q_tau == pytest.approx(q_fwhm, rel=1e-12)
    assert q_tau == pytest.approx(math.pi * f0 * tau, rel=1e-12)


def test_fwhm_and_tau_are_inverses():
    tau = 0.037
    assert HL.tau_from_fwhm(HL.fwhm_from_tau(tau)) == pytest.approx(
        tau, rel=1e-12)


def test_ringdown_q_recovered_from_a_synthetic_decay():
    """POWER: a planted tau is recovered from a synthetic ringdown."""
    f0, tau = 1000.0, 0.05
    data = HL.synthetic_ringdown(f0=f0, tau=tau, sample_rate_hz=48000.0)
    recovered = HL.estimate_ringdown_tau(data["t_s"], data["signal"])
    assert recovered == pytest.approx(tau, rel=0.05)
    estimate = HL.estimate_ringdown_q(data["t_s"], data["signal"], f0)
    assert estimate["estimated_q"] == pytest.approx(
        HL.ringdown_q_from_tau(f0, tau), rel=0.05)


def test_ringdown_recovery_demo_agrees_and_recovers():
    demo = HL.ringdown_recovery_demo()
    assert demo["q_formulas_agree"] is True
    assert demo["tau_relative_error"] < 0.05
    assert demo["estimated_q"] == pytest.approx(demo["true_q"], rel=0.05)


def test_ringdown_recovers_a_different_planted_tau():
    """The estimator is not hard-wired to one value."""
    demo = HL.ringdown_recovery_demo(f0=2000.0, tau=0.08,
                                     sample_rate_hz=96000.0)
    assert demo["estimated_tau_s"] == pytest.approx(0.08, rel=0.05)


def test_ringdown_refuses_sub_nyquist_sampling():
    with pytest.raises(HL.HomeLabError):
        HL.synthetic_ringdown(f0=1000.0, tau=0.05, sample_rate_hz=1500.0)


# --- (3) the isotropy permutation test -----------------------------------

def test_isotropy_null_isotropic_data_gives_p_not_small():
    """NULL: isotropic synthetic data -> the permutation p is not small."""
    result = HL.isotropy_null_demo(trials=2000)
    assert result["p_value"] > HL.ALPHA_SIGNIFICANCE
    assert result["significant_at_alpha"] is False


def test_isotropy_power_planted_cos2theta_gives_p_small():
    """POWER: a planted cos(2*theta) -> the permutation p is small."""
    result = HL.isotropy_power_demo(trials=2000)
    assert result["p_value"] <= HL.ALPHA_SIGNIFICANCE
    assert result["significant_at_alpha"] is True


def test_isotropy_pvalue_is_reproducible_under_a_fixed_seed():
    data = HL.synthetic_anisotropic_responses(seed=7)
    a = HL.isotropy_pvalue(data, trials=500, seed=3)
    b = HL.isotropy_pvalue(data, trials=500, seed=3)
    assert a["p_value"] == b["p_value"]


def test_isotropy_needs_at_least_two_orientations():
    with pytest.raises(HL.HomeLabError):
        HL.isotropy_pvalue({0.0: [1.0, 2.0, 3.0, 4.0]})


# --- (4) the refusals -----------------------------------------------------

def test_refuse_anisotropy_as_anomaly_always_raises():
    with pytest.raises(HL.HomeLabError) as exc:
        HL.refuse_anisotropy_as_anomaly()
    message = str(exc.value)
    assert "ANISOTROPIC" in message
    assert "null" in message.lower()


def test_refuse_result_without_controls_when_one_is_missing():
    plan = HL.experiment_plan(HL.Experiment.RINGDOWN_Q)
    # all but the last declared control
    partial = plan.controls[:-1]
    assert HL.missing_controls(plan, partial) == (plan.controls[-1],)
    with pytest.raises(HL.HomeLabError) as exc:
        HL.refuse_result_without_controls(plan, partial)
    assert plan.controls[-1].value in str(exc.value)


def test_all_declared_controls_present_passes():
    plan = HL.experiment_plan(HL.Experiment.MODE_SURVEY)
    got = HL.refuse_result_without_controls(plan, plan.controls)
    assert tuple(got) == plan.controls
    # control names as strings are accepted too
    names = [c.value for c in plan.controls]
    assert HL.refuse_result_without_controls(plan, names) == plan.controls


def test_no_controls_at_all_refuses_and_names_them():
    plan = HL.experiment_plan(HL.Experiment.ISOTROPY)
    with pytest.raises(HL.HomeLabError) as exc:
        HL.refuse_result_without_controls(plan, ())
    message = str(exc.value)
    for control in plan.controls:
        assert control.value in message


def test_refuse_bench_claim_always_raises():
    with pytest.raises(HL.HomeLabError) as exc:
        HL.refuse_bench_claim()
    assert "BLOCKED_MISSING_DATA" in str(exc.value)
    with pytest.raises(HL.HomeLabError):
        HL.refuse_bench_claim("Q measured", HL.Experiment.RINGDOWN_Q)


# --- (5) the report -------------------------------------------------------

def test_report_carries_the_verdict_and_the_disclaimers():
    report = HL.homelab_report()
    assert report["verdict"] == "HOME_LAB_EXPERIMENTS_PREREGISTERED_NOT_RUN"
    assert HL.VERDICT == "HOME_LAB_EXPERIMENTS_PREREGISTERED_NOT_RUN"
    assert report["measured_here"] == "nothing"
    assert report["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert report["claim_class"] in HL.CLAIM_CLASSES
    assert report["all_blocked"] is True
    assert report["n_experiments"] == 4
    assert report["isotropy"]["null_significant"] is False
    assert report["isotropy"]["power_significant"] is True
    assert report["ringdown"]["recovery_demo"]["q_formulas_agree"] is True
    assert report["what_this_does_not_say"]


def test_the_declared_claim_classes_are_the_shared_nine():
    assert HL.CLAIM_CLASSES == (
        "EXACT_IDENTITY", "SOURCE_ESTABLISHED_PHYSICS",
        "REPOSITORY_COMPUTATIONAL_RESULT", "ENGINEERING_CANDIDATE",
        "RETROSPECTIVE_NUMERIC_MATCH", "PROSPECTIVE_PREDICTION",
        "BENCH_MEASUREMENT", "UNSUPPORTED", "BLOCKED_MISSING_DATA")


def test_homelab_module_imports_under_its_package_name():
    from r12 import homelab
    assert homelab.VERDICT == HL.VERDICT
