"""R15 P18 — the clock and phase measurement lane.

Power tests (planted jitter, skew, phase and drift recovered), negative and
refusal tests (REAL acquires nothing; every fault alters the reading; a
jitter-raised floor is ordinary, not a signal; relativistic language
refused), the closure test (common clock vs independent oscillators), the
uncertain-latency test, determinism, and schema conformance.
"""

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
from r15 import clock_phase as CP

_SCHEMA_DIR = Path(__file__).resolve().parents[2] / "r15" / "schemas"


# --- POWER: planted phase, skew, drift, jitter recovered -----------------

def test_planted_phase_recovered():
    spec = CP.SyntheticClockSpec(planted_phase=0.6)
    acq = CP.synthesize(spec, seed=0)
    assert CP.recover_phase(acq) == pytest.approx(0.6, abs=1e-6)


@pytest.mark.parametrize("phi", [-1.2, 0.0, 0.4, 2.5])
def test_phase_recovered_over_range(phi):
    acq = CP.synthesize(CP.SyntheticClockSpec(planted_phase=phi), seed=1)
    assert CP.recover_phase(acq) == pytest.approx(phi, abs=1e-6)


def test_planted_integer_skew_recovered_exactly():
    ref = CP.synthesize(CP.SyntheticClockSpec(skew_samples=0), seed=2)
    ch = CP.synthesize(CP.SyntheticClockSpec(skew_samples=9), seed=2)
    assert CP.recover_skews([ref.samples, ch.samples]) == (0, 9)


def test_injected_drift_is_recovered():
    spec = CP.SyntheticClockSpec(drift_rate=7e-3, jitter_std=1e-7)
    acq = CP.synthesize(spec, seed=4)
    assert CP.estimate_drift(acq.time_error, acq.tau0) == \
        pytest.approx(7e-3, rel=1e-2)


def test_planted_jitter_is_recovered():
    spec = CP.SyntheticClockSpec(jitter_std=3e-6, drift_rate=2e-3)
    acq = CP.synthesize(spec, seed=6)
    est = CP.estimate_jitter(acq.time_error, acq.tau0)
    assert est == pytest.approx(3e-6, rel=0.1)


def test_frequency_offset_recovered():
    spec = CP.SyntheticClockSpec(freq_offset=4e-4, jitter_std=1e-8)
    acq = CP.synthesize(spec, seed=8)
    assert CP.estimate_frequency_offset(acq.time_error, acq.tau0) == \
        pytest.approx(4e-4, rel=1e-2)


def test_allan_deviation_decreases_for_white_phase_noise():
    # a pure white-phase-noise clock: ADEV falls as tau grows.
    spec = CP.SyntheticClockSpec(jitter_std=1e-6)
    acq = CP.synthesize(spec, seed=0)
    adev = CP.allan_deviation(acq.time_error, acq.tau0, m_list=[1, 8, 64])
    taus = sorted(adev)
    assert adev[taus[0]] > adev[taus[-1]]


# --- closure: common clock differs from independent oscillators ----------

def test_common_clock_closure_differs_from_independent():
    spec = CP.SyntheticClockSpec(jitter_std=2e-6, drift_rate=5e-3)
    common = CP.common_clock_closure(spec)
    indep = CP.independent_oscillator_closure(spec)
    assert indep["closure_residual"] > 100.0 * common["closure_residual"]
    assert common["hypothesis"] == "common_clock"
    assert indep["hypothesis"] == "independent_oscillators"


def test_common_clock_closure_is_near_zero():
    spec = CP.SyntheticClockSpec(jitter_std=1e-7)
    common = CP.common_clock_closure(spec)
    assert common["closure_residual"] < 1e-4


# --- unknown latency stays uncertain -------------------------------------

def test_unknown_latency_stays_uncertain():
    lat = CP.transport_latency(4, fs=8000.0, reference_delay_s=None)
    assert lat["resolved"] is False
    assert lat["uncertainty"]["half_width"] > 0.0
    assert lat["uncertainty"]["low"] < lat["value"] < lat["uncertainty"]["high"]


def test_known_reference_resolves_latency():
    lat = CP.transport_latency(4, fs=8000.0, reference_delay_s=5e-4)
    assert lat["resolved"] is True
    assert lat["uncertainty"]["half_width"] == 0.0


# --- jitter raises the noise floor: ordinary, not a signal ---------------

def test_more_jitter_lowers_snr_raises_floor():
    spec = CP.SyntheticClockSpec()
    low = CP.jitter_noise_floor(spec, 1e-6, n_realizations=8, seed=0)
    high = CP.jitter_noise_floor(spec, 1e-4, n_realizations=8, seed=0)
    assert high["tone_snr"] < low["tone_snr"]
    assert high["noise_floor"] > low["noise_floor"]


def test_jitter_floor_is_known_ordinary_effect_not_signal():
    spec = CP.SyntheticClockSpec()
    r = CP.jitter_noise_floor(spec, 1e-5, n_realizations=8, seed=0)
    assert r["claim_class"] == C.ClaimClass.KNOWN_ORDINARY_EFFECT.value
    assert r["is_signal"] is False


def test_refuse_jitter_as_signal_raises():
    with pytest.raises(CP.ClockPhaseError, match="not a signal|resonance"):
        CP.refuse_jitter_as_signal()


# --- negative: REAL acquires nothing -------------------------------------

def test_real_device_acquires_nothing():
    dev = CP.RealClockDevice()
    with pytest.raises(CP.NoClockHardwareError):
        dev.acquire(seed=0)


def test_real_device_blocked_receipt_is_preregistered_not_run():
    dev = CP.RealClockDevice()
    r = dev.blocked_receipt()
    assert r["acquired"] is False
    assert r["n_samples"] == 0
    assert r["physical_run"] == "PREREGISTERED_NOT_RUN"
    assert r["status"] == "BLOCKED"


# --- negative: every fault mode alters the clean reading -----------------

@pytest.mark.parametrize("fault", list(CP.ClockFaultMode))
def test_each_fault_alters_the_clean_reading(fault):
    inner = CP.SyntheticClockDevice(CP.SyntheticClockSpec(jitter_std=1e-6))
    clean = inner.acquire(seed=5)
    fi = CP.FaultInjectionClockDevice(inner, faults=(fault,))
    faulty = fi.acquire(seed=5)
    assert fault in faulty.faults
    same_tone = np.array_equal(clean.samples, faulty.samples, equal_nan=True)
    same_te = np.array_equal(clean.time_error, faulty.time_error,
                             equal_nan=True)
    assert not (same_tone and same_te)


def test_all_eight_faults_together_are_deterministic():
    inner = CP.SyntheticClockDevice(CP.SyntheticClockSpec(jitter_std=1e-6))
    fi = CP.FaultInjectionClockDevice(inner, faults=tuple(CP.ClockFaultMode))
    a = fi.acquire(seed=11)
    b = fi.acquire(seed=11)
    assert np.array_equal(a.samples, b.samples, equal_nan=True)
    assert np.array_equal(a.time_error, b.time_error, equal_nan=True)
    assert set(a.faults) == set(CP.ClockFaultMode)


def test_clock_specific_faults_present():
    names = {f.value for f in CP.ClockFaultMode}
    assert {"cycle_slip", "glitch", "holdover"} <= names


def test_fault_device_needs_at_least_one_fault():
    inner = CP.SyntheticClockDevice(CP.SyntheticClockSpec())
    with pytest.raises(CP.ClockPhaseError):
        CP.FaultInjectionClockDevice(inner, faults=())


# --- the four modes stay distinct ----------------------------------------

def test_four_modes_are_distinct():
    assert {m.value for m in CP.ClockMode} == {
        "REAL_DEVICE", "REPLAY_DEVICE", "SYNTHETIC_DEVICE",
        "FAULT_INJECTION_DEVICE"}


def test_replay_reproduces_recorded_acquisition():
    recorded = CP.synthesize(CP.SyntheticClockSpec(planted_phase=0.3), seed=7)
    replay = CP.ReplayClockDevice(recorded)
    out = replay.acquire(seed=999)
    assert out.mode is CP.ClockMode.REPLAY_DEVICE
    assert np.array_equal(out.samples, recorded.samples)
    assert np.array_equal(out.time_error, recorded.time_error)


def test_modes_behave_differently_on_same_request():
    syn = CP.SyntheticClockDevice(CP.SyntheticClockSpec()).acquire(seed=9)
    assert syn.mode is CP.ClockMode.SYNTHETIC_DEVICE
    with pytest.raises(CP.NoClockHardwareError):
        CP.RealClockDevice().acquire(seed=9)


# --- determinism ----------------------------------------------------------

def test_same_seed_identical_acquisition():
    dev = CP.SyntheticClockDevice(
        CP.SyntheticClockSpec(jitter_std=2e-6, drift_rate=3e-3))
    a = dev.acquire(seed=3)
    b = dev.acquire(seed=3)
    assert a.digest() == b.digest()
    assert np.array_equal(a.samples, b.samples)
    assert np.array_equal(a.time_error, b.time_error)


def test_different_seed_differs():
    dev = CP.SyntheticClockDevice(CP.SyntheticClockSpec(jitter_std=2e-6))
    a = dev.acquire(seed=1)
    b = dev.acquire(seed=2)
    assert not np.array_equal(a.samples, b.samples)


# --- no promotion, no relativity -----------------------------------------

def test_acquisition_cannot_be_a_measurement_class():
    with pytest.raises(C.ClaimError):
        CP.ClockAcquisition(
            mode=CP.ClockMode.SYNTHETIC_DEVICE, samples=np.zeros(8),
            time_error=np.zeros(8), edges=np.arange(8, dtype=float),
            fs=8000.0, tone_freq=100.0, seed=0, tau0=1 / 8000.0,
            claim_class=C.ClaimClass.PHYSICAL_MEASUREMENT)


def test_reading_is_synthetic_observation():
    acq = CP.synthesize(CP.SyntheticClockSpec(), seed=0)
    assert acq.claim_class is C.ClaimClass.SYNTHETIC_OBSERVATION
    assert acq.claim_class not in C.MEASUREMENT_CLASSES


def test_refuse_synthetic_clock_as_measured_raises():
    with pytest.raises(CP.ClockPhaseError):
        CP.refuse_synthetic_clock_as_measured()


def test_refuse_relativistic_interpretation_raises():
    with pytest.raises(CP.ClockPhaseError, match="sensitivity"):
        CP.refuse_relativistic_interpretation(1e-9)


# --- error budget ---------------------------------------------------------

def test_timing_budget_rss_combination():
    b = CP.timing_error_budget({"clock_jitter": 3e-6, "transport_delay": 4e-6})
    assert b["combination_method"] == "RSS"
    assert b["combined_uncertainty"] == pytest.approx(5e-6, rel=1e-9)
    assert b["expanded_uncertainty"] == pytest.approx(1e-5, rel=1e-9)


def test_timing_budget_separates_the_named_terms():
    b = CP.timing_error_budget({
        "synthesis_error": 1e-6, "transport_delay": 2e-6,
        "latency": 3e-6, "residual_phase": 4e-6})
    sep = b["separated"]
    assert sep["synthesis_error"] == 1e-6
    assert sep["transport_delay"] == 2e-6
    assert sep["latency"] == 3e-6
    assert sep["residual_phase"] == 4e-6


def test_unknown_budget_component_refused():
    with pytest.raises(CP.ClockPhaseError, match="unknown"):
        CP.timing_error_budget({"not_a_component": 1e-6})


def test_negative_budget_component_refused():
    with pytest.raises(CP.ClockPhaseError):
        CP.timing_error_budget({"clock_jitter": -1e-6})


def test_empty_budget_refused():
    with pytest.raises(CP.ClockPhaseError):
        CP.timing_error_budget({})


# --- report claims nothing -----------------------------------------------

def test_report_claims_nothing():
    r = CP.clock_phase_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["physical_run"] == "PREREGISTERED_NOT_RUN"
    assert r["reading_claim_class"] == "SYNTHETIC_OBSERVATION"
    assert r["closure_differs"] is True
    assert set(r["fault_modes"]) == {f.value for f in CP.ClockFaultMode}


# --- schema conformance ---------------------------------------------------

def test_phase_observation_conforms_to_schema():
    if jsonschema is None:  # pragma: no cover
        pytest.skip("jsonschema not installed")
    schema = json.loads((_SCHEMA_DIR / "observation_record.schema.json")
                        .read_text(encoding="utf-8"))
    obs = CP.phase_observation(0.7, 1e-4, run_id="run-1")
    jsonschema.validate(obs, schema)


def test_timing_budget_conforms_to_schema():
    if jsonschema is None:  # pragma: no cover
        pytest.skip("jsonschema not installed")
    schema = json.loads((_SCHEMA_DIR / "error_budget.schema.json")
                        .read_text(encoding="utf-8"))
    b = CP.timing_error_budget({
        "synthesis_error": 1e-6, "clock_jitter": 2e-6, "sync_skew": 1e-7,
        "transport_delay": 5e-6, "latency": 1e-6, "residual_phase": 3e-6})
    jsonschema.validate(b, schema)


def test_receipt_conforms_to_phase_receipt_schema():
    if jsonschema is None:  # pragma: no cover
        pytest.skip("jsonschema not installed")
    schema = json.loads((_SCHEMA_DIR / "phase_receipt.schema.json")
                        .read_text(encoding="utf-8"))
    receipt = json.loads(
        (Path(__file__).resolve().parents[2] / "docs" / "v8" / "receipts"
         / "P18.json").read_text(encoding="utf-8"))
    jsonschema.validate(receipt, schema)
    assert receipt["phase_id"] == "P18"
    assert receipt["status"] == "COMPLETE"
