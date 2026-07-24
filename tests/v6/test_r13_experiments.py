"""P25-P30 — the prospective experiment registry: exactly six
preregistered protocols, all with null models and power promises,
validation that refuses a missing null, a power-discipline helper, and
the two refusals."""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from r13 import experiments as E


# --- (1) exactly six, all preregistered, all with null + power -----------

def test_exactly_six_experiments():
    assert len(E.REGISTRY) == 6
    ids = {e.id for e in E.REGISTRY}
    assert ids == set(E.ExperimentId)          # one of each, no duplicates


def test_all_preregistered_not_run_with_prediction_class():
    for e in E.REGISTRY:
        assert e.status == "PREREGISTERED_NOT_RUN"
        assert e.claim_class == "PROSPECTIVE_PREDICTION"


def test_every_experiment_has_a_null_model_and_power_flag():
    for e in E.REGISTRY:
        assert e.has_null_model()
        assert e.null_model
        assert isinstance(e.power_on_planted_data, bool)
        assert e.power_on_planted_data is True


def test_the_six_pack_experiments_are_present():
    ids = {e.id for e in E.REGISTRY}
    for required in (E.ExperimentId.P25_BASELINE_MODAL_SURVEY,
                     E.ExperimentId.P26_AVOIDED_CROSSING_SWEEP,
                     E.ExperimentId.P27_ROTATION_VS_SQUEEZE,
                     E.ExperimentId.P28_POLARIZATION_STATE,
                     E.ExperimentId.P29_CUTOFF_PHASE_TIMING,
                     E.ExperimentId.P30_CROSS_DOMAIN_TRANSFER):
        assert required in ids


# --- (2) an experiment cannot claim to have run --------------------------

def test_run_status_is_refused_at_construction():
    base = E.REGISTRY[0]
    with pytest.raises(E.ExperimentsError):
        dataclasses.replace(base, status="RUN")


def test_measurement_claim_class_is_refused_at_construction():
    base = E.REGISTRY[0]
    with pytest.raises(E.ExperimentsError):
        dataclasses.replace(base, claim_class="BENCH_MEASUREMENT")
    with pytest.raises(E.ExperimentsError):
        dataclasses.replace(base, claim_class="INDEPENDENTLY_REPLICATED")


# --- (3) registry validation, and a missing null is refused --------------

def test_validate_registry_passes_on_the_six():
    result = E.validate_registry()
    assert result["experiment_count"] == 6
    assert result["all_have_null_model"] is True
    assert result["all_have_power_on_planted_data"] is True
    assert result["all_preregistered_not_run"] is True


def test_a_missing_null_model_is_refused():
    broken = list(E.REGISTRY)
    broken[2] = dataclasses.replace(broken[2], null_model="")
    with pytest.raises(E.ExperimentsError):
        E.validate_registry(tuple(broken))


def test_a_missing_power_promise_is_refused():
    broken = list(E.REGISTRY)
    broken[3] = dataclasses.replace(broken[3], power_on_planted_data=False)
    with pytest.raises(E.ExperimentsError):
        E.validate_registry(tuple(broken))


def test_wrong_registry_size_is_refused():
    with pytest.raises(E.ExperimentsError):
        E.validate_registry(E.REGISTRY[:5])


# --- (4) the power discipline: detects a planted effect, nulls on noise --

def test_planted_signal_power_check_detects_effect_and_nulls_on_noise():
    """POWER: a competent detector flags a planted step and stays silent
    on pure noise, so has_power is True."""
    planted = np.concatenate([np.zeros(64), 8.0 * np.ones(64)])

    def detect(x: np.ndarray) -> bool:
        half = x.size // 2
        return bool(abs(x[half:].mean() - x[:half].mean()) > 3.0)

    result = E.planted_signal_power_check(detect, planted)
    assert result["detects_planted_effect"] is True
    assert result["detects_pure_noise"] is False
    assert result["has_power"] is True


def test_powerless_detector_is_reported_as_such():
    """A detector that fires on everything has no specificity, so it has
    no power even though it 'detects' the planted effect."""
    planted = np.concatenate([np.zeros(64), 8.0 * np.ones(64)])

    def always_true(x: np.ndarray) -> bool:
        return True

    result = E.planted_signal_power_check(always_true, planted)
    assert result["detects_planted_effect"] is True
    assert result["detects_pure_noise"] is True
    assert result["has_power"] is False


def test_empty_planted_effect_is_refused():
    with pytest.raises(E.ExperimentsError):
        E.planted_signal_power_check(lambda x: True, np.array([]))


# --- (5) the two refusals ------------------------------------------------

def test_refuse_prediction_as_result_raises():
    with pytest.raises(E.ExperimentsError):
        E.refuse_prediction_as_result(E.REGISTRY[0])
    with pytest.raises(E.ExperimentsError):
        E.refuse_prediction_as_result(
            E.ExperimentId.P25_BASELINE_MODAL_SURVEY)


def test_refuse_preregistration_as_confirmation_raises():
    with pytest.raises(E.ExperimentsError):
        E.refuse_preregistration_as_confirmation()


# --- (6) the report ------------------------------------------------------

def test_report_verdict_and_claims_no_measurement():
    rep = E.experiments_report()
    assert rep["verdict"] == "PROSPECTIVE_EXPERIMENT_REGISTRY_PREREGISTERED"
    assert len(rep["experiments"]) == 6
    assert rep["all_preregistered_not_run"] is True
    assert rep["all_have_null_model"] is True
    assert rep["all_have_power_on_planted_data"] is True
    assert rep["power_discipline_demo"]["has_power"] is True
    assert rep["measured_here"] == "nothing"
    assert rep["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert rep["claim_class"] == "PROSPECTIVE_PREDICTION"
    assert "what_this_does_not_say" in rep


def test_experiments_module_imports_from_r13():
    from r13 import experiments          # noqa: F401
    assert experiments.DEFAULT_VERDICT == \
        "PROSPECTIVE_EXPERIMENT_REGISTRY_PREREGISTERED"
