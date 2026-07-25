"""P23 — multiple comparisons and sequential analysis.

POWER: Benjamini-Hochberg / Holm recover planted true effects while
controlling error; the look-elsewhere inflation is shown for uncorrected
reporting. NEGATIVE: uncorrected multiple comparisons refused; optional
stopping refused; exploratory-as-confirmatory refused. DETERMINISM: same
seed reproduces the family and the simulations byte-for-byte."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

try:
    import jsonschema
except ImportError:  # pragma: no cover
    jsonschema = None

from r15 import claims as C
from r15 import multiple_testing as MT
from r13.preregister import Preregistration


# --- fixtures -------------------------------------------------------------

def _prereg(stopping_rule: str) -> Preregistration:
    return Preregistration(
        study_id="P23_SEQ",
        hypothesis="the planted contrast exceeds its matched null",
        predicted_signature="a single preregistered contrast crosses alpha",
        null_model="permuted labels, marginals preserved",
        decision_rule="declare support only if the sealed contrast p <= 0.05",
        analysis_plan="test the one sealed contrast; no scan",
        stopping_rule=stopping_rule,
        power_on_planted="recovers a planted effect at the sealed contrast",
        epoch_committed=20260724,
    )


# =========================================================================
# POWER: corrections recover true effects while controlling error
# =========================================================================

def test_bh_recovers_all_planted_effects():
    planted = MT.synthetic_planted_family(n_tests=60, n_true=5, true_p=1e-6,
                                           seed=7)
    res = MT.power_and_error(planted, MT.CorrectionMethod.BENJAMINI_HOCHBERG,
                             alpha=0.05)
    assert res["true_positive_rate"] == 1.0        # every planted effect found
    assert res["fdr_observed"] <= 0.05             # FDR held at alpha


def test_holm_recovers_effects_and_controls_fwer():
    planted = MT.synthetic_planted_family(n_tests=60, n_true=5, true_p=1e-8,
                                           seed=11)
    res = MT.power_and_error(planted, MT.CorrectionMethod.HOLM, alpha=0.05)
    assert res["true_positive_rate"] == 1.0
    assert res["false_discoveries"] == 0           # FWER: no false rejection


def test_bh_is_more_powerful_than_bonferroni_with_many_effects():
    # Many moderate effects: FDR control recovers at least as many as FWER.
    planted = MT.synthetic_planted_family(n_tests=100, n_true=20, true_p=1e-3,
                                           seed=3)
    bh = MT.power_and_error(planted, MT.CorrectionMethod.BENJAMINI_HOCHBERG,
                            0.05)
    bonf = MT.power_and_error(planted, MT.CorrectionMethod.BONFERRONI, 0.05)
    assert bh["n_rejected"] >= bonf["n_rejected"]
    assert bh["true_positive_rate"] >= bonf["true_positive_rate"]


def test_correction_controls_familywise_error_under_global_null():
    # All nulls true: Bonferroni holds the family-wise error at/below alpha,
    # while the uncorrected smallest-p rate is the inflated look-elsewhere
    # value.
    alpha = 0.05
    fwer = MT.corrected_family_fpr(30, alpha, MT.CorrectionMethod.BONFERRONI,
                                   trials=4000, seed=5)
    assert fwer <= alpha + 0.01


# =========================================================================
# POWER: the look-elsewhere inflation for uncorrected reporting
# =========================================================================

def test_look_elsewhere_probability_matches_formula():
    assert MT.look_elsewhere_probability(1, 0.05) == pytest.approx(0.05)
    assert MT.look_elsewhere_probability(20, 0.05) == pytest.approx(
        1 - 0.95 ** 20)
    # It climbs toward 1 as the number of tests grows.
    assert MT.look_elsewhere_probability(100, 0.05) > 0.99


def test_uncorrected_min_p_is_inflated_far_above_alpha():
    alpha = 0.05
    m = 20
    sim = MT.uncorrected_min_p_fpr(m, alpha, trials=6000, seed=0)
    analytic = MT.look_elsewhere_probability(m, alpha)
    assert sim == pytest.approx(analytic, abs=0.03)
    assert sim > 0.5                                # ~0.64, not 0.05


def test_correction_removes_the_inflation():
    alpha = 0.05
    m = 20
    inflated = MT.uncorrected_min_p_fpr(m, alpha, trials=6000, seed=0)
    corrected = MT.corrected_family_fpr(m, alpha,
                                        MT.CorrectionMethod.BONFERRONI,
                                        trials=6000, seed=0)
    assert corrected < inflated
    assert corrected <= alpha + 0.01


# =========================================================================
# POWER: hidden retries increase the trial count and the correction
# =========================================================================

def test_hidden_retries_increase_trials():
    fam = MT.TestFamily(name="swept", p_values=(0.01, 0.2, 0.5),
                        hidden_retries=17)
    assert fam.n_reported == 3
    assert fam.total_trials() == 20
    assert MT.effective_trials(3, 17) == 20


def test_hidden_retries_change_the_correction():
    # Same reported p-values; disclosing the retries makes the smallest p
    # fail correction that it would have passed against the reported count.
    reported = MT.TestFamily(name="r", p_values=(0.004, 0.3, 0.4))
    hidden = MT.TestFamily(name="h", p_values=(0.004, 0.3, 0.4),
                           hidden_retries=40)
    r = MT.correct(reported, MT.CorrectionMethod.BONFERRONI, 0.05)
    h = MT.correct(hidden, MT.CorrectionMethod.BONFERRONI, 0.05)
    assert r.rejected[0] is True
    assert h.rejected[0] is False                   # 0.004 * 43 > 0.05


# =========================================================================
# Sequential analysis: peeking spends alpha
# =========================================================================

def test_alpha_spending_is_monotonic_and_sums_to_alpha():
    sched = MT.alpha_spending(0.05, [0.25, 0.5, 0.75, 1.0],
                              MT.SpendingFunction.POCOCK)
    cum = sched.cumulative_spend
    assert all(cum[i] < cum[i + 1] for i in range(len(cum) - 1))
    assert cum[-1] == pytest.approx(0.05, abs=1e-9)  # final spend == alpha
    assert all(a > 0 for a in sched.nominal_alpha)   # every look spends some


def test_spending_boundary_controls_sequential_fpr():
    # Peeking at four looks with the FULL alpha inflates the false-positive
    # rate; the spent-down boundary holds it at alpha.
    alpha = 0.05
    sched = MT.alpha_spending(alpha, [0.25, 0.5, 0.75, 1.0],
                              MT.SpendingFunction.POCOCK)
    naive = MT.naive_peeking_fpr(4, alpha, trials=8000, seed=2)
    spent = MT.spent_peeking_fpr(sched, trials=8000, seed=2)
    assert naive > 0.10                              # inflated well past alpha
    assert spent == pytest.approx(alpha, abs=0.015)  # held at alpha
    assert spent < naive


def test_naive_peeking_matches_look_elsewhere():
    naive = MT.naive_peeking_fpr(5, 0.05, trials=8000, seed=4)
    assert naive == pytest.approx(MT.look_elsewhere_probability(5, 0.05),
                                  abs=0.03)


def test_sequential_stops_at_first_crossing():
    sched = MT.alpha_spending(0.05, [0.25, 0.5, 0.75, 1.0],
                              MT.SpendingFunction.POCOCK)
    # A tiny p at look 3, nothing before.
    ps = (0.9, 0.4, 1e-6, 0.5)
    dec = MT.evaluate_sequential(sched, ps)
    assert dec.stopped is True
    assert dec.stop_look == 3
    assert dec.reject is True


def test_sequential_no_crossing_does_not_reject():
    sched = MT.alpha_spending(0.05, [0.5, 1.0], MT.SpendingFunction.LINEAR)
    dec = MT.evaluate_sequential(sched, (0.4, 0.3))
    assert dec.stopped is False
    assert dec.reject is False


def test_obrien_fleming_spends_less_early_than_pocock():
    fr = [0.25, 0.5, 0.75, 1.0]
    obf = MT.alpha_spending(0.05, fr, MT.SpendingFunction.OBRIEN_FLEMING)
    poc = MT.alpha_spending(0.05, fr, MT.SpendingFunction.POCOCK)
    # OBF is conservative early: its first-look boundary is stricter.
    assert obf.nominal_alpha[0] < poc.nominal_alpha[0]
    # Both spend the whole budget by the end.
    assert obf.cumulative_spend[-1] == pytest.approx(0.05, abs=1e-6)
    assert poc.cumulative_spend[-1] == pytest.approx(0.05, abs=1e-9)


# =========================================================================
# NEGATIVE: the refusals
# =========================================================================

def test_refuse_uncorrected_multiple_comparisons():
    fam = MT.TestFamily(name="scan", p_values=(0.001, 0.2, 0.4, 0.6, 0.8))
    with pytest.raises(MT.MultipleTestingError, match="look-elsewhere"):
        MT.refuse_uncorrected_multiple_comparisons(fam)
    # Once corrected, it is allowed through.
    ok = MT.refuse_uncorrected_multiple_comparisons(fam, corrected=True)
    assert ok["allowed"] is True


def test_refuse_counts_hidden_retries_even_for_one_reported_test():
    fam = MT.TestFamily(name="one", p_values=(0.001,), hidden_retries=9)
    with pytest.raises(MT.MultipleTestingError):
        MT.refuse_uncorrected_multiple_comparisons(fam)


def test_single_test_needs_no_correction():
    fam = MT.TestFamily(name="single", p_values=(0.001,))
    ok = MT.refuse_uncorrected_multiple_comparisons(fam)
    assert ok["single_test"] is True


def test_refuse_optional_stopping_without_rule():
    prereg = _prereg(stopping_rule="")               # no stopping rule
    with pytest.raises(Exception):                   # PreregisterError
        MT.refuse_optional_stopping(prereg, peeked_and_stopped=True)


def test_preregistered_stopping_rule_is_allowed():
    prereg = _prereg(stopping_rule="fixed 4 looks, Pocock alpha-spending")
    out = MT.refuse_optional_stopping(prereg, peeked_and_stopped=True)
    assert out["has_preregistered_stopping_rule"] is True
    assert out["allowed"] is True


def test_exploratory_scan_cannot_yield_confirmatory_pvalue():
    fam = MT.TestFamily(name="explore", p_values=(1e-5, 0.3, 0.4, 0.5))
    # No sealed preregistration -> the top hit is not confirmatory.
    with pytest.raises(MT.MultipleTestingError, match="confirmatory"):
        MT.refuse_exploratory_as_confirmatory(None, scanned_family=fam)


def test_pvalue_out_of_range_refused():
    with pytest.raises(MT.MultipleTestingError):
        MT.TestFamily(name="bad", p_values=(0.5, 1.5))
    with pytest.raises(MT.MultipleTestingError):
        MT.TestFamily(name="bad", p_values=())


def test_alpha_out_of_range_refused():
    fam = MT.TestFamily(name="f", p_values=(0.1, 0.2))
    with pytest.raises(MT.MultipleTestingError):
        MT.correct(fam, MT.CorrectionMethod.HOLM, 1.5)
    with pytest.raises(MT.MultipleTestingError):
        MT.correct(fam, MT.CorrectionMethod.HOLM, 0.0)


def test_correction_cannot_use_fewer_trials_than_reported():
    with pytest.raises(MT.MultipleTestingError):
        MT.bonferroni_adjust([0.1, 0.2, 0.3], m=2)


# =========================================================================
# Diagnostics
# =========================================================================

def test_diagnose_flags_extreme_z_and_low_null_variance():
    diag = MT.diagnose([0.4, 1.1, 12.0, -0.7], null_variance=1e-9)
    assert diag.extreme_z_indices == (2,)
    assert diag.low_null_variance is True
    assert diag.max_abs_z == pytest.approx(12.0)


def test_diagnose_clean_input_flags_nothing():
    diag = MT.diagnose([0.4, 1.1, -0.7], null_variance=1.0)
    assert diag.extreme_z_indices == ()
    assert diag.low_null_variance is False


# =========================================================================
# DETERMINISM
# =========================================================================

def test_planted_family_is_deterministic_under_seed():
    a = MT.synthetic_planted_family(50, 4, seed=99)
    b = MT.synthetic_planted_family(50, 4, seed=99)
    assert a.family.p_values == b.family.p_values
    assert a.true_effects == b.true_effects
    assert MT.family_digest(a.family) == MT.family_digest(b.family)


def test_different_seed_differs():
    a = MT.synthetic_planted_family(50, 4, seed=1)
    b = MT.synthetic_planted_family(50, 4, seed=2)
    assert MT.family_digest(a.family) != MT.family_digest(b.family)


def test_simulations_are_deterministic_under_seed():
    assert MT.uncorrected_min_p_fpr(10, 0.05, trials=1000, seed=0) == \
        MT.uncorrected_min_p_fpr(10, 0.05, trials=1000, seed=0)
    sched = MT.alpha_spending(0.05, [0.5, 1.0], MT.SpendingFunction.POCOCK)
    assert MT.spent_peeking_fpr(sched, trials=1000, seed=0) == \
        MT.spent_peeking_fpr(sched, trials=1000, seed=0)


# =========================================================================
# Claim discipline and the report
# =========================================================================

def test_report_claims_nothing_measured():
    rep = MT.multiple_testing_report()
    assert rep["measured_here"] == "nothing"
    assert rep["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert rep["claim_class"] == C.ClaimClass.SOFTWARE_IMPLEMENTED.value
    assert rep["verdict"] == MT.VERDICT


def test_report_shows_inflation_and_control():
    rep = MT.multiple_testing_report()
    seq = rep["sequential_example"]
    assert seq["naive_peeking_fpr"] > seq["spent_boundary_fpr"]
    ex = rep["worked_example"]
    assert ex["look_elsewhere_probability"] > 0.05
    assert ex["fwer_after_correction_simulated"] <= 0.07


def test_fixture_class_is_synthetic_observation():
    planted = MT.synthetic_planted_family(10, 2, seed=0)
    assert planted.claim_class == C.ClaimClass.SYNTHETIC_OBSERVATION.value


# =========================================================================
# The phase receipt
# =========================================================================

def test_receipt_conforms_to_phase_receipt_schema():
    if jsonschema is None:
        pytest.skip("jsonschema not installed")
    root = Path(__file__).resolve().parents[2]
    schema = json.loads(
        (root / "r15" / "schemas" / "phase_receipt.schema.json").read_text())
    receipt = json.loads(
        (root / "docs" / "v8" / "receipts" / "P23.json").read_text())
    jsonschema.validate(receipt, schema)
    assert receipt["phase_id"] == "P23"
    assert receipt["status"] == "COMPLETE"
    assert receipt["blocked_reason"] is None
    assert receipt["commit"] is None
