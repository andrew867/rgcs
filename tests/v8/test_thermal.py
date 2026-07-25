"""P16 -- the thermal measurement lane: transducer conversion, sensor lag,
self-heating, the thermal coefficient of frequency, four device modes, the
thermal error budget, and the refusal that a temperature-driven shift is a
known ordinary effect rather than a signal."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from r15 import thermal as T
from r15.claims import ClaimClass

_ROOT = Path(__file__).resolve().parents[2]
_SCHEMA_DIR = _ROOT / "r15" / "schemas"


def _clock(n: int = 500, fs: float = 10.0, t0: float = 1000.0) -> np.ndarray:
    return t0 + np.arange(n, dtype=float) / fs


def _sensor(kind: T.ThermalSensorKind = T.ThermalSensorKind.THERMISTOR,
            **kw) -> T.ThermalSensor:
    params = dict(sensor_id="s1", kind=kind, location="oven-wall",
                  response_time_s=0.5, uncertainty_K=0.02)
    params.update(kw)
    return T.ThermalSensor(**params)


# --- (1) transducer conversion models -------------------------------------

def test_thermistor_beta_model_returns_reference_at_r0():
    # at R = R0 the Beta model returns exactly T0
    assert float(T.thermistor_temperature(10000.0)) == pytest.approx(298.15)
    # higher resistance (NTC) reads colder
    assert float(T.thermistor_temperature(20000.0)) < 298.15


def test_rtd_callendar_model_inverts_resistance():
    assert float(T.rtd_temperature(100.0)) == pytest.approx(273.15)
    # +0.385 ohm on a Pt100 is +1 K
    assert float(T.rtd_temperature(100.385)) == pytest.approx(274.15, abs=1e-6)


def test_thermocouple_seebeck_model_uses_reference_junction():
    assert float(T.thermocouple_temperature(0.0, t_ref_K=300.0)) == \
        pytest.approx(300.0)
    # a positive EMF reads above the cold junction
    assert float(T.thermocouple_temperature(4.1e-4, t_ref_K=300.0)) > 300.0


def test_a_nonpositive_thermistor_resistance_is_refused():
    with pytest.raises(T.ThermalError):
        T.thermistor_temperature(0.0)


# --- (2) sensor binding to location and response time ---------------------

def test_sensor_is_bound_to_a_location_and_a_response_time():
    s = _sensor()
    assert s.location == "oven-wall"
    assert s.response_time_s == 0.5
    assert s.claim_class is ClaimClass.SYNTHETIC_OBSERVATION


def test_a_sensor_without_a_location_is_refused():
    with pytest.raises(T.ThermalError):
        _sensor(location="")


def test_a_manual_sensor_is_typed_as_a_source_claim():
    s = _sensor(kind=T.ThermalSensorKind.MANUAL)
    assert s.claim_class is ClaimClass.SOURCE_CLAIM


# --- REQUIRED: known thermal coefficients reproduce drift (POWER) ---------

def test_planted_thermal_coefficient_of_frequency_is_recovered():
    t = _clock()
    p = T.SyntheticThermalParams(t_mean_K=300.0, drift_rate_K_per_s=0.02,
                                 noise_K=1e-5, f0_hz=1.0e7, t_ref_K=300.0,
                                 tcf_per_K=-2.5e-5)
    dev = T.SyntheticThermalDevice(_sensor(), p)
    acq = dev.acquire(t, seed=11)
    fit = T.fit_thermal_coefficient(acq.temperature_K, acq.frequency_hz,
                                    f0_hz=1.0e7, t_ref_K=300.0)
    assert fit.tcf_per_K == pytest.approx(-2.5e-5, rel=1e-3)
    assert fit.r_squared > 0.999


def test_planted_ambient_drift_rate_is_recovered():
    t = _clock()
    p = T.SyntheticThermalParams(drift_rate_K_per_s=0.05, noise_K=1e-5)
    dev = T.SyntheticThermalDevice(_sensor(), p)
    acq = dev.acquire(t, seed=3)
    assert T.fit_ambient_drift(acq.t, acq.temperature_K) == \
        pytest.approx(0.05, abs=1e-3)
    # detrending removes the ramp
    resid = T.correct_ambient_drift(acq.t, acq.temperature_K)
    assert abs(T.fit_ambient_drift(acq.t, resid)) < 1e-6


def test_a_quadratic_tcf_term_is_recovered_too():
    t = _clock()
    p = T.SyntheticThermalParams(drift_rate_K_per_s=0.1, noise_K=0.0,
                                 tcf_per_K=-1.0e-5, tcf2_per_K2=3.0e-7)
    dev = T.SyntheticThermalDevice(_sensor(), p)
    acq = dev.acquire(t, seed=1)
    fit = T.fit_thermal_coefficient(acq.temperature_K, acq.frequency_hz,
                                    f0_hz=p.f0_hz, t_ref_K=p.t_ref_K)
    assert fit.tcf2_per_K2 == pytest.approx(3.0e-7, rel=1e-3)


# --- REQUIRED: sensor lag is estimated ------------------------------------

def test_a_pure_delay_is_recovered_exactly():
    t = np.arange(300)
    ambient = 300.0 + np.sin(2 * np.pi * t / 50.0)
    delayed = np.roll(ambient, 5)
    assert T.estimate_sensor_lag_samples(ambient, delayed) == 5


def test_first_order_response_produces_a_lag_that_grows_with_tau():
    t = np.arange(400)
    ambient = 300.0 + np.sin(2 * np.pi * t / 40.0)
    slow = T.apply_sensor_response(ambient, 1.0, 3.0)
    slower = T.apply_sensor_response(ambient, 1.0, 10.0)
    lag_slow = T.estimate_sensor_lag_samples(ambient, slow)
    lag_slower = T.estimate_sensor_lag_samples(ambient, slower)
    assert lag_slow > 0
    assert lag_slower > lag_slow


def test_mismatched_lengths_refused_when_estimating_lag():
    with pytest.raises(T.ThermalError):
        T.estimate_sensor_lag_samples(np.zeros(10), np.zeros(9))


# --- REQUIRED: self-heating is not specimen output ------------------------

def test_self_heating_offset_is_corrected():
    s = _sensor(self_heating_K_per_W=50.0, dissipated_power_W=0.01)
    assert s.self_heating_offset_K == pytest.approx(0.5)
    indicated = np.full(10, 300.5)
    corrected = T.correct_self_heating(indicated, s)
    assert np.allclose(corrected, 300.0)


def test_self_heating_as_specimen_output_is_refused():
    with pytest.raises(T.ThermalError):
        T.refuse_self_heating_as_specimen(0.5)


def test_injected_self_heating_raises_the_trace_but_not_the_ambient():
    t = _clock(n=200)
    p = T.SyntheticThermalParams(t_mean_K=300.0, noise_K=0.0)
    clean = T.SyntheticThermalDevice(_sensor(), p)
    ref = clean.acquire(t, seed=2)
    faulty = T.FaultInjectionThermalDevice(
        clean, (T.ThermalFaultMode.SELF_HEATING,),
        config={"self_heating_K": 0.7})
    hot = faulty.acquire(t, seed=2)
    # the fault raised the indicated temperature by the self-heating offset,
    # a sensor artifact, not a real change in the ambient
    assert np.nanmean(hot.temperature_K) == \
        pytest.approx(np.nanmean(ref.temperature_K) + 0.7, abs=1e-9)
    assert T.ThermalFaultMode.SELF_HEATING in hot.faults


# --- thermal explanation of frequency and phase ---------------------------

def test_thermal_frequency_shift_matches_the_tcf_model():
    df = T.thermal_frequency_shift(10.0, f0_hz=1.0e7, tcf_per_K=-2.0e-5)
    assert df == pytest.approx(1.0e7 * -2.0e-5 * 10.0)


def test_thermal_phase_shift_scales_with_expansion_and_temperature():
    phi0 = 100.0
    dphi = T.thermal_phase_shift(phi0, 5.0, alpha_per_K=T.QUARTZ_ALPHA_A_PER_K)
    assert dphi == pytest.approx(phi0 * T.QUARTZ_ALPHA_A_PER_K * 5.0)


def test_expansion_frequency_coefficient_reads_crystalframe_quartz():
    # a thickness-governed mode falls as the lattice expands: df/f = -alpha
    assert T.expansion_frequency_coefficient("a") == \
        pytest.approx(-T.QUARTZ_ALPHA_A_PER_K)
    frame = T.quartz_lattice_at_temperature(10.0)
    # the expanded a exceeds the literature a from r13.crystalframe
    from r13 import crystalframe
    assert frame.a > crystalframe.QUARTZ_A_ANGSTROM


def test_thermal_drift_read_as_a_signal_is_refused():
    with pytest.raises(T.ThermalError):
        T.refuse_thermal_drift_as_signal(delta_T_K=5.0, df_hz=1250.0)


def test_a_temperature_driven_shift_is_a_known_ordinary_effect():
    assert T.DRIFT_CLAIM_CLASS is ClaimClass.KNOWN_ORDINARY_EFFECT
    # a thermometer does not couple to the specimen's mechanical mode
    assert T.thermal_coupling_is_an_artifact()


# --- the four modes, kept distinct ----------------------------------------

def test_real_device_acquires_nothing():
    dev = T.RealThermalDevice(_sensor())
    with pytest.raises(T.NoThermalHardwareError):
        dev.acquire(_clock(), seed=0)
    receipt = dev.preregistered_receipt()
    assert receipt["status"] == T.PREREGISTERED_NOT_RUN
    assert receipt["acquired"] is False
    assert receipt["measured_here"] == "nothing"


def test_replay_device_reads_back_the_recorded_trace_byte_for_byte():
    t = _clock(n=100)
    p = T.SyntheticThermalParams(drift_rate_K_per_s=0.01)
    src = T.SyntheticThermalDevice(_sensor(), p).acquire(t, seed=5)
    replay = T.ReplayThermalDevice(_sensor(), src.t, src.temperature_K,
                                   src.frequency_hz)
    back = replay.acquire()
    assert back.digest() == src.digest()
    assert back.mode is T.ThermalDeviceMode.REPLAY_DEVICE


def test_replay_cannot_exceed_the_recorded_length():
    t = _clock(n=20)
    src = T.SyntheticThermalDevice(_sensor(), T.SyntheticThermalParams()) \
        .acquire(t, seed=0)
    replay = T.ReplayThermalDevice(_sensor(), src.t, src.temperature_K)
    with pytest.raises(T.ThermalError):
        replay.acquire(n_samples=21)


def test_four_modes_are_distinct():
    assert len({m for m in T.ThermalDeviceMode}) == 4


@pytest.mark.parametrize("fault", list(T.ThermalFaultMode))
def test_every_fault_mode_alters_the_trace(fault):
    t = _clock(n=256)
    p = T.SyntheticThermalParams(t_mean_K=300.0, drift_rate_K_per_s=0.01,
                                 noise_K=0.05)
    clean = T.SyntheticThermalDevice(_sensor(), p)
    ref = clean.acquire(t, seed=9)
    faulty = T.FaultInjectionThermalDevice(clean, (fault,))
    out = faulty.acquire(t, seed=9)
    assert fault in out.faults
    a = np.asarray(ref.temperature_K)
    b = np.asarray(out.temperature_K)
    if fault is T.ThermalFaultMode.MISSING_SAMPLES:
        assert np.any(~np.isfinite(b))
    else:
        assert not np.array_equal(a, b)


def test_fault_injection_needs_at_least_one_fault():
    clean = T.SyntheticThermalDevice(_sensor(), T.SyntheticThermalParams())
    with pytest.raises(T.ThermalError):
        T.FaultInjectionThermalDevice(clean, ())


# --- determinism ----------------------------------------------------------

def test_synthetic_acquisition_is_deterministic_under_a_seed():
    t = _clock()
    dev = T.SyntheticThermalDevice(_sensor(), T.SyntheticThermalParams(noise_K=0.1))
    a = dev.acquire(t, seed=7)
    b = dev.acquire(t, seed=7)
    c = dev.acquire(t, seed=8)
    assert a.digest() == b.digest()
    assert a.digest() != c.digest()


def test_fault_injection_is_deterministic_under_a_seed():
    t = _clock(n=128)
    clean = T.SyntheticThermalDevice(_sensor(), T.SyntheticThermalParams(noise_K=0.05))
    faulty = T.FaultInjectionThermalDevice(clean, (T.ThermalFaultMode.PACKET_LOSS,))
    a = faulty.acquire(t, seed=4)
    b = faulty.acquire(t, seed=4)
    assert np.array_equal(np.nan_to_num(a.temperature_K),
                          np.nan_to_num(b.temperature_K))


# --- the thermal error budget ---------------------------------------------

def test_error_budget_combines_in_quadrature():
    comps = [
        T.ThermalErrorComponent(T.ThermalBudgetComponent.SENSOR_RESOLUTION, 3.0, "K"),
        T.ThermalErrorComponent(T.ThermalBudgetComponent.CALIBRATION, 4.0, "K"),
    ]
    b = T.build_thermal_error_budget("bud-1", "temperature", comps)
    assert b["combined_uncertainty"] == pytest.approx(5.0)  # 3-4-5
    assert b["combination_method"] == T.QUADRATURE
    assert b["claim_class"] == "MODEL_PREDICTION"


def test_duplicate_budget_component_is_refused():
    with pytest.raises(T.ThermalError):
        T.build_thermal_error_budget("bud-dup", "temperature", [
            T.ThermalErrorComponent(T.ThermalBudgetComponent.CALIBRATION, 1.0, "K"),
            T.ThermalErrorComponent(T.ThermalBudgetComponent.CALIBRATION, 2.0, "K"),
        ])


def test_default_thermal_budget_conforms_to_schema():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads((_SCHEMA_DIR / "error_budget.schema.json").read_text())
    budget = T.default_thermal_budget(_sensor(self_heating_K_per_W=50.0,
                                              dissipated_power_W=0.01))
    jsonschema.validate(budget, schema)
    assert budget["combined_uncertainty"] > 0.0


def test_within_budget_residual_is_not_anomalous():
    assert T.is_within_budget(0.03, 0.1)
    assert not T.is_within_budget(0.5, 0.1)


# --- observation record ---------------------------------------------------

def test_thermal_observation_record_conforms_to_schema():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(
        (_SCHEMA_DIR / "observation_record.schema.json").read_text())
    rec = T.thermal_observation_record(
        "obs-1", "run-1", value=300.12, uncertainty_K=0.02,
        source_artifacts=["thermal_trace.npy"])
    jsonschema.validate(rec, schema)
    assert rec["claim_class"] == "SYNTHETIC_OBSERVATION"
    assert rec["measured_here"] == "nothing"


# --- refusals and report --------------------------------------------------

def test_synthetic_thermal_as_measured_is_refused():
    with pytest.raises(T.ThermalError):
        T.refuse_synthetic_thermal_as_measured()


def test_manual_note_as_sensor_is_refused():
    with pytest.raises(T.ThermalError):
        T.refuse_manual_as_sensor()


def test_acquisition_cannot_be_a_measurement_class():
    # constructing an acquisition tagged as a measurement class raises
    with pytest.raises(Exception):
        T.ThermalAcquisition(
            sensor_id="s", mode=T.ThermalDeviceMode.SYNTHETIC_DEVICE,
            t=np.arange(4.0), temperature_K=np.full(4, 300.0),
            frequency_hz=None, seed=0,
            claim_class=ClaimClass.PHYSICAL_MEASUREMENT)


def test_every_forbidden_promotion_is_registered_and_raises():
    assert set(T.FORBIDDEN_PROMOTIONS) == {
        "thermal_drift_to_signal", "self_heating_to_specimen",
        "synthetic_thermal_to_measured", "manual_to_sensor"}
    for fn in T.FORBIDDEN_PROMOTIONS.values():
        with pytest.raises(T.ThermalError):
            fn()


def test_real_mode_is_preregistered_not_run():
    st = T.real_mode_status()
    assert st["status"] == T.PREREGISTERED_NOT_RUN
    assert st["measured_here"] == "nothing"


def test_report_claims_nothing():
    r = T.thermal_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["verdict"] == T.VERDICT
    assert r["real_mode_status"] == T.PREREGISTERED_NOT_RUN
    assert r["reading_claim_class"] == "SYNTHETIC_OBSERVATION"
    assert r["thermal_shift_is"] == "KNOWN_ORDINARY_EFFECT"
    assert set(r["sensor_kinds"]) == {k.value for k in T.ThermalSensorKind}
    assert len(r["fault_modes"]) == 6
