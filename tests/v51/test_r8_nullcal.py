"""P06 — adversarial null calibration and its three case studies.

The most important test in this file is
``test_blind_detector_is_caught_only_by_injection``: both detectors
return an unremarkable null on pure noise, and only the injection
sweep separates them. That is the paper.
"""

from __future__ import annotations

import random

import pytest

from r8 import nullcal as NC


# --- the harness ------------------------------------------------------

def _gen(rng):
    return [rng.gauss(0, 1) for _ in range(20)]


def _inject(v, s, rng):
    return [x + s for x in v]


def _mean(v):
    return sum(v) / len(v)


def _deaf(v):
    return 0.0        # ignores its input entirely


def test_a_working_detector_calibrates():
    r = NC.calibrate(_mean, _gen, _inject, n_trials=150)
    assert r.verdict == "CALIBRATED"
    assert r.usable
    assert r.monotonic
    assert r.power_at_max > 0.9


def test_a_deaf_detector_is_caught():
    r = NC.calibrate(_deaf, _gen, _inject, n_trials=100)
    assert r.verdict == "BLIND_DETECTOR"
    assert not r.usable
    assert r.blind


def test_blind_verdict_explains_what_the_null_means():
    r = NC.calibrate(_deaf, _gen, _inject, n_trials=100)
    assert "statement about the detector" in r.note


def test_false_positive_rate_is_measured_not_assumed():
    r = NC.calibrate(_mean, _gen, _inject, n_trials=200, alpha=0.05)
    assert 0.0 <= r.false_positive_rate <= 0.15


def test_strengths_must_include_zero():
    with pytest.raises(ValueError):
        NC.calibrate(_mean, _gen, _inject, strengths=(0.5, 1.0))


def test_calibration_is_deterministic_under_seed():
    a = NC.calibrate(_mean, _gen, _inject, n_trials=80, seed=5)
    b = NC.calibrate(_mean, _gen, _inject, n_trials=80, seed=5)
    assert a.detection_rate == b.detection_rate


def test_detection_rate_rises_with_strength():
    r = NC.calibrate(_mean, _gen, _inject, n_trials=150)
    nonzero = [x for s, x in zip(r.strengths, r.detection_rate) if s > 0]
    assert nonzero[-1] > nonzero[0]


def test_gate_refuses_an_uncalibrated_null():
    r = NC.calibrate(_deaf, _gen, _inject, n_trials=80)
    with pytest.raises(NC.CalibrationRefused) as e:
        NC.require_calibration(r)
    assert "uninterpretable" in str(e.value)


def test_gate_passes_a_calibrated_null():
    r = NC.calibrate(_mean, _gen, _inject, n_trials=150)
    NC.require_calibration(r)          # must not raise


def test_every_verdict_is_declared():
    for stat in (_mean, _deaf):
        r = NC.calibrate(stat, _gen, _inject, n_trials=80)
        assert r.verdict in NC.CALIBRATION_VERDICTS


# --- case study 1: forced structure -----------------------------------

CW = (162875493612, 162875432975, 162877542769,
      162875439275, 162875439285)


def test_forced_prefix_matches_the_r7_result():
    assert NC.forced_prefix_bits(CW, 38) == 15


def test_straddle_counterexample():
    """127 and 128 span 1 and share no leading bits."""
    assert NC.forced_prefix_bits((127, 128), 8) == 0


def test_the_cw_parse_carries_zero_informative_bits():
    rep = NC.informative_bits(CW, 38, 2, 12)
    assert rep["inside_forced_region"]
    assert rep["informative_bits"] == 0


def test_matched_interval_null_reproduces_the_structure():
    n = NC.forced_structure_null(CW, 38, 2, 12, n_draws=500)
    assert n["p_structure_reproduced"] == 1.0


def test_a_parse_reaching_past_the_forced_region_is_informative():
    rep = NC.informative_bits(CW, 38, 2, 24)
    assert not rep["inside_forced_region"]
    assert rep["informative_bits"] > 0


# --- the general bits-accounting result -------------------------------

def test_retrospective_information_is_zero_inside_the_forced_region():
    r = NC.retrospective_information(bits_used=14, bits_forced=15)
    assert r["informative_bits"] == 0
    assert not r["carries_evidence"]
    assert "discriminates nothing" in r["interpretation"]


def test_retrospective_information_counts_the_excess():
    r = NC.retrospective_information(bits_used=20, bits_forced=15)
    assert r["informative_bits"] == 5
    assert r["carries_evidence"]


def test_bits_accounting_credits_prior_art():
    r = NC.retrospective_information(14, 15)
    assert "Efron" in r["prior_art"]
    assert "McKay" in r["prior_art"]


def test_negative_bit_counts_rejected():
    with pytest.raises(ValueError):
        NC.retrospective_information(-1, 5)


# --- case study 2: granularity mismatch -------------------------------

def test_fixed_grid_null_makes_a_negative_control_significant():
    """The artifact, reproduced. The corpus is arbitrary round numbers
    with no structure; only the null differs between the two arms."""
    m = NC.granularity_mismatch_demo()
    assert m["fixed_grid_declares_significance"]
    assert not m["matched_declares_significance"]
    assert m["inverted"]


def test_the_corpus_is_labelled_a_negative_control():
    assert "NEGATIVE CONTROL" in NC.granularity_mismatch_demo()["note"]


def test_matched_null_is_not_significant():
    m = NC.granularity_mismatch_demo()
    assert m["p_matched_granularity"] > 0.05


# --- the negative-control signature -----------------------------------

def test_negative_control_reaching_significance_condemns_the_analysis():
    s = NC.negative_control_signature(control_p=0.0025, observed_p=0.03)
    assert s["analysis_is_broken"]
    assert "NULL_INVALID" in s["verdict"]


def test_well_behaved_negative_control_passes():
    s = NC.negative_control_signature(control_p=0.83, observed_p=0.01)
    assert not s["analysis_is_broken"]


def test_signature_needs_no_knowledge_of_true_effect():
    s = NC.negative_control_signature(0.001, 0.5)
    assert "requires no knowledge of the true effect" in s["note"]


# --- case study 3: blind detector --------------------------------------

def test_blind_detector_is_caught_only_by_injection():
    """The paper's headline demonstration."""
    d = NC.blind_detector_demo()
    assert d["good_detector"]["verdict"] == "CALIBRATED"
    assert d["blind_detector"]["verdict"] == "BLIND_DETECTOR"
    assert d["separated_only_by_injection"]


def test_blind_detector_never_responds_to_any_strength():
    d = NC.blind_detector_demo()
    assert all(r == 0.0 for r in d["blind_detector"]["detection_rate"])


def test_good_detector_response_is_monotonic():
    d = NC.blind_detector_demo()
    assert d["good_detector"]["monotonic"]


# --- the pre-flight artifact -------------------------------------------

def test_preflight_passes_only_when_all_three_hold():
    assert NC.preflight(True, True, True)["null_is_interpretable"]
    for combo in ((False, True, True), (True, False, True),
                  (True, True, False)):
        assert not NC.preflight(*combo)["null_is_interpretable"]


def test_preflight_names_which_check_failed():
    p = NC.preflight(True, False, True)
    assert "STRUCTURE_NOT_FORCED" in p["failed"]
    assert "STRUCTURE_NOT_FORCED" in p["verdict"]


def test_preflight_disclaims_novelty_and_names_the_lineage():
    """The prior-art review's first requirement: do not claim the
    principle is new. Severity, positive controls, injection-recovery
    and blind analysis all predate it."""
    lin = NC.preflight(True, True, True)["lineage"]
    assert "Mayo" in lin
    assert "not claimed as novel" in lin
    assert "positive control" in lin


def test_three_checks_are_declared_with_implementations():
    assert len(NC.PREFLIGHT_CHECKS) == 3
    for name, question, impl in NC.PREFLIGHT_CHECKS:
        assert question.endswith("?")
        assert hasattr(NC, impl)
