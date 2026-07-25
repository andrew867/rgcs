"""R15 P14: the electrical measurement lane -- impedance/admittance sweep,
Butterworth-Van Dyke fit, four modes, OSL calibration, and the refusals.

Power: planted BVD parameters are recovered from a synthetic impedance
sweep. Negative: a REAL device acquires nothing, every fault mode corrupts
the sweep, a synthetic fit is not a measured device, and a calibration will
not correct outside its grid. Determinism throughout.
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
from r15 import electrical as E
from r13.qcmstack import BVDResonator, fit_bvd


_SCHEMA_DIR = Path(__file__).resolve().parents[2] / "r15" / "schemas"


# --- fixtures -------------------------------------------------------------

def _synthetic_device(n=8001, **kw):
    return E.SyntheticElectricalDevice(n=n, **kw)


# --- POWER: planted BVD parameters are recovered -------------------------

def test_synthetic_bvd_parameters_are_recovered():
    dev = _synthetic_device()
    sweep = dev.acquire_sweep(seed=3)
    fit = E.fit_synthetic_bvd(sweep)
    res = E.DEFAULT_RESONATOR
    assert abs(fit["f_s_hz"] - res.f_s) / res.f_s < 1e-4
    assert abs(fit["f_p_hz"] - res.f_p) / res.f_p < 1e-3
    assert abs(fit["Q"] - res.Q) / res.Q < 1e-3
    assert abs(fit["R"] - res.R) / res.R < 1e-3
    assert abs(fit["L"] - res.L) / res.L < 1e-3
    assert abs(fit["C"] - res.C) / res.C < 1e-3
    assert abs(fit["C0"] - res.C0) / res.C0 < 1e-3


def test_recovery_holds_for_a_second_planted_resonator():
    # a different planted resonator (f_s ~ 2 MHz, Q ~ 500) is also recovered
    other = BVDResonator(R=20.0, L=1.5915e-3 / 4.0, C=1.5915e-11,
                         C0=8.0e-11)
    dev = _synthetic_device(resonator=other)
    fit = E.fit_synthetic_bvd(dev.acquire_sweep(seed=1))
    assert abs(fit["f_s_hz"] - other.f_s) / other.f_s < 1e-4
    assert abs(fit["Q"] - other.Q) / other.Q < 1e-3
    assert abs(fit["C0"] - other.C0) / other.C0 < 1e-3


def test_recovery_survives_seeded_noise():
    dev = _synthetic_device(noise=1e-4)
    fit = E.fit_synthetic_bvd(dev.acquire_sweep(seed=7))
    res = E.DEFAULT_RESONATOR
    assert abs(fit["f_s_hz"] - res.f_s) / res.f_s < 1e-3


def test_a_fitted_bvd_is_a_synthetic_observation_not_a_measurement():
    dev = _synthetic_device()
    fit = E.fit_synthetic_bvd(dev.acquire_sweep(seed=0))
    assert fit["claim_class"] == C.ClaimClass.SYNTHETIC_OBSERVATION.value
    assert fit["measured_here"] == "nothing"
    assert C.ClaimClass.SYNTHETIC_OBSERVATION not in C.MEASUREMENT_CLASSES


# --- the four modes are kept distinct ------------------------------------

def test_four_device_modes_present():
    assert {m.value for m in E.ElectricalDeviceMode} == {
        "REAL_DEVICE", "SYNTHETIC_DEVICE", "REPLAY_DEVICE",
        "FAULT_INJECTION_DEVICE"}


def test_real_device_acquires_nothing():
    real = E.RealElectricalDevice()
    with pytest.raises(E.NoElectricalHardwareError, match="acquires NOTHING"):
        real.acquire_sweep()


def test_real_device_blocked_receipt_is_preregistered_not_run():
    real = E.RealElectricalDevice()
    rec = real.blocked_receipt()
    assert rec["acquired"] is False
    assert rec["n_points"] == 0
    assert rec["physical_run"] == "PREREGISTERED_NOT_RUN"
    assert rec["claim_class"] == "BLOCKED_MISSING_INPUT"


def test_replay_device_reads_back_the_recorded_sweep():
    dev = _synthetic_device()
    original = dev.acquire_sweep(seed=5)
    replay = E.ReplayElectricalDevice(original)
    played = replay.acquire_sweep(seed=999)  # seed does not change a replay
    assert played.mode is E.ElectricalDeviceMode.REPLAY_DEVICE
    assert played.digest() == original.digest()


def test_synthetic_sweep_is_a_synthetic_observation():
    sweep = _synthetic_device().acquire_sweep(seed=0)
    assert sweep.mode is E.ElectricalDeviceMode.SYNTHETIC_DEVICE
    assert sweep.claim_class is C.ClaimClass.SYNTHETIC_OBSERVATION


# --- the five fault modes ------------------------------------------------

@pytest.mark.parametrize("fault", list(E.FaultMode))
def test_each_fault_mode_corrupts_the_sweep(fault):
    dev = _synthetic_device(n=4001)
    clean = dev.acquire_sweep(seed=2)
    faulty = E.FaultInjectionElectricalDevice(dev, (fault,)).acquire_sweep(seed=2)
    assert faulty.mode is E.ElectricalDeviceMode.FAULT_INJECTION_DEVICE
    assert faulty.faults == (fault,)
    # the faulty sweep is not the clean one (ignoring NaN placement)
    assert not np.allclose(np.nan_to_num(faulty.Z),
                           np.nan_to_num(clean.Z))


@pytest.mark.parametrize("fault", list(E.FaultMode))
def test_a_fault_sweep_is_refused_for_a_clean_fit(fault):
    dev = _synthetic_device(n=4001)
    faulty = E.FaultInjectionElectricalDevice(dev, (fault,)).acquire_sweep(seed=2)
    with pytest.raises(E.ElectricalError, match="injected faults"):
        E.fit_synthetic_bvd(faulty)


def test_fault_injection_needs_at_least_one_fault():
    dev = _synthetic_device(n=1024)
    with pytest.raises(E.ElectricalError, match="at least one FaultMode"):
        E.FaultInjectionElectricalDevice(dev, ())


def test_all_five_faults_inject_together_deterministically():
    dev = _synthetic_device(n=4001)
    fdev = E.FaultInjectionElectricalDevice(dev, tuple(E.FaultMode))
    a = fdev.acquire_sweep(seed=4)
    b = fdev.acquire_sweep(seed=4)
    assert np.array_equal(np.nan_to_num(a.Z), np.nan_to_num(b.Z))
    assert len(a.faults) == 5


# --- cable capacitance appears correctly ---------------------------------

def test_cable_capacitance_recovered_by_open_standard():
    c_cable = 5.0e-11
    fix = E.FixtureModel(cable_capacitance_f=c_cable,
                         lead_resistance_ohm=2.0,
                         topology=E.ConnectionTopology.TWO_WIRE)
    freqs = _synthetic_device().acquire_sweep(seed=0).freqs_hz
    osl = E.build_osl_calibration(freqs, fix)
    recovered = osl.recovered_cable_capacitance_f()
    assert abs(recovered - c_cable) / c_cable < 1e-6


def test_osl_correction_removes_the_fixture_and_recovers_true_c0():
    # cable capacitance in parallel is otherwise absorbed into C0
    fix = E.FixtureModel(cable_capacitance_f=5.0e-11, lead_resistance_ohm=3.0,
                         topology=E.ConnectionTopology.TWO_WIRE)
    dev = _synthetic_device(fixture=fix)
    sweep = dev.acquire_sweep(seed=1)
    osl = E.build_osl_calibration(sweep.freqs_hz, fix)

    # uncorrected: the fit sees C0 + C_cable (badly wrong C0)
    raw = fit_bvd(sweep.freqs_hz, sweep.Z)
    res = E.DEFAULT_RESONATOR
    assert abs(raw["C0"] - res.C0) / res.C0 > 0.1

    # corrected: the true C0 comes back
    z_corr = osl.correct(sweep.freqs_hz, sweep.Z)
    fixed = fit_bvd(sweep.freqs_hz, z_corr)
    assert abs(fixed["C0"] - res.C0) / res.C0 < 1e-3


def test_four_wire_drops_the_lead_impedance():
    two = E.FixtureModel(cable_capacitance_f=1e-11, lead_resistance_ohm=5.0,
                         topology=E.ConnectionTopology.TWO_WIRE)
    four = E.FixtureModel(cable_capacitance_f=1e-11, lead_resistance_ohm=5.0,
                          topology=E.ConnectionTopology.FOUR_WIRE)
    freqs = _synthetic_device().acquire_sweep(seed=0).freqs_hz
    assert np.allclose(two.series_impedance(freqs).real, 5.0)
    assert np.allclose(four.series_impedance(freqs), 0.0)


# --- calibration limits behave correctly ---------------------------------

def test_calibration_refuses_a_shorter_grid():
    fix = E.FixtureModel(cable_capacitance_f=1e-11)
    sweep = _synthetic_device().acquire_sweep(seed=0)
    osl = E.build_osl_calibration(sweep.freqs_hz, fix)
    with pytest.raises(E.CalibrationLimitError):
        osl.correct(sweep.freqs_hz[:-1], sweep.Z[:-1])


def test_calibration_refuses_a_shifted_grid():
    fix = E.FixtureModel(cable_capacitance_f=1e-11)
    sweep = _synthetic_device().acquire_sweep(seed=0)
    osl = E.build_osl_calibration(sweep.freqs_hz, fix)
    with pytest.raises(E.CalibrationLimitError, match="does not match"):
        osl.correct(sweep.freqs_hz * 1.5, sweep.Z)


def test_calibration_needs_a_finite_shunt_term():
    # a fixture with no cable capacitance has an open-circuit open standard
    fix = E.FixtureModel(cable_capacitance_f=0.0)
    freqs = _synthetic_device().acquire_sweep(seed=0).freqs_hz
    with pytest.raises(E.ElectricalError, match="shunt term"):
        E.build_osl_calibration(freqs, fix)


def test_osl_load_standard_must_be_positive():
    fix = E.FixtureModel(cable_capacitance_f=1e-11)
    freqs = _synthetic_device().acquire_sweep(seed=0).freqs_hz
    with pytest.raises(E.ElectricalError):
        E.build_osl_calibration(freqs, fix, load_ohm=-1.0)


# --- detectors: ground loop, saturation ----------------------------------

def test_ground_loop_detected_at_mains_frequency():
    rate = 1000.0
    t = np.arange(4096) / rate
    signal = 0.01 * np.sin(2 * np.pi * 3.0 * t) + 1.0 * np.sin(
        2 * np.pi * 50.0 * t)
    out = E.detect_ground_loop(signal, rate)
    assert out["ground_loop"] is True
    assert out["mains_hz"] == 50.0


def test_no_ground_loop_on_a_clean_low_frequency_record():
    rate = 1000.0
    t = np.arange(4096) / rate
    rng = np.random.default_rng(0)
    signal = np.sin(2 * np.pi * 3.0 * t) + 1e-3 * rng.standard_normal(t.size)
    assert E.detect_ground_loop(signal, rate)["ground_loop"] is False


def test_saturation_detected_on_a_clipped_record():
    t = np.linspace(0, 1, 2048)
    clipped = np.clip(2.0 * np.sin(2 * np.pi * 5.0 * t), -1.0, 1.0)
    assert E.detect_saturation(clipped)["saturated"] is True
    clean = 0.5 * np.sin(2 * np.pi * 5.0 * t)
    assert E.detect_saturation(clean)["saturated"] is False


# --- constitutive relations ----------------------------------------------

def test_impedance_admittance_phase_and_charge():
    v = np.array([1.0 + 0j, 0.0 + 1.0j])
    i = np.array([0.5 + 0j, 0.0 + 0.5j])
    z = E.impedance_from_vi(v, i)
    assert np.allclose(z, [2.0 + 0j, 2.0 + 0j])
    assert np.allclose(E.admittance(z), [0.5 + 0j, 0.5 + 0j])
    assert np.allclose(E.phase_deg(np.array([1j])), [90.0])
    # charge of a constant 1 A current over 1 s is ~1 C
    t = np.linspace(0.0, 1.0, 101)
    q = E.charge_from_current(np.ones_like(t), t)
    assert abs(q[-1] - 1.0) < 1e-9


def test_zero_current_has_no_impedance():
    with pytest.raises(E.ElectricalError, match="zero current"):
        E.impedance_from_vi(np.array([1.0 + 0j]), np.array([0.0 + 0j]))


def test_johnson_noise_is_positive_and_scales():
    n1 = E.johnson_noise_voltage(1e3, 1e4)
    n2 = E.johnson_noise_voltage(4e3, 1e4)
    assert n1 > 0
    assert abs(n2 / n1 - 2.0) < 1e-9  # sqrt(4x R) doubles the RMS


def test_source_load_divider_transfer():
    sl = E.SourceLoad(source_ohm=50.0, load_ohm=1e6)
    h = sl.divider_transfer(np.array([50.0 + 0j]))
    # a 50-ohm DUT into a 50-ohm source (meter ~open) gives about 0.5
    assert abs(h[0] - 0.5) < 1e-3


def test_single_pole_transfer_matches_analytic():
    # H(s) = 1/(s + a); reuse of r13.response.statespace_transfer
    h = E.single_pole_transfer(3.0, 1j)
    assert abs(h - 1.0 / (1j + 3.0)) < 1e-12


# --- determinism ----------------------------------------------------------

def test_synthetic_sweep_same_seed_identical():
    a = _synthetic_device(n=2001, noise=1e-3).acquire_sweep(seed=11)
    b = _synthetic_device(n=2001, noise=1e-3).acquire_sweep(seed=11)
    assert a.digest() == b.digest()


def test_synthetic_sweep_different_seed_differs_with_noise():
    a = _synthetic_device(n=2001, noise=1e-3).acquire_sweep(seed=1)
    b = _synthetic_device(n=2001, noise=1e-3).acquire_sweep(seed=2)
    assert a.digest() != b.digest()


# --- refusals and no-promotion -------------------------------------------

def test_a_sweep_cannot_be_typed_as_a_measurement():
    # the sweep guard delegates to the governance core, which raises ClaimError
    with pytest.raises(C.ClaimError):
        E.ElectricalSweep(
            instrument_id="x", mode=E.ElectricalDeviceMode.SYNTHETIC_DEVICE,
            topology=E.ConnectionTopology.TWO_WIRE,
            freqs_hz=np.array([1.0, 2.0]), Z=np.array([1.0 + 0j, 2.0 + 0j]),
            seed=0, claim_class=C.ClaimClass.PHYSICAL_MEASUREMENT)


def test_refuse_synthetic_fit_as_measured_device_raises():
    with pytest.raises(E.ElectricalError, match="not measured on a device"):
        E.refuse_synthetic_fit_as_measured_device("f_s")


def test_refuse_sweep_as_measurement_raises():
    with pytest.raises(E.ElectricalError, match="SYNTHETIC_OBSERVATION"):
        E.refuse_sweep_as_measurement()


def test_fit_refuses_a_real_sweep_object():
    # a hand-built REAL-mode sweep has no data to fit
    sweep = E.ElectricalSweep(
        instrument_id="real", mode=E.ElectricalDeviceMode.REAL_DEVICE,
        topology=E.ConnectionTopology.FOUR_WIRE,
        freqs_hz=np.linspace(1.0, 2.0, 64),
        Z=np.ones(64, dtype=complex), seed=0)
    with pytest.raises(E.NoElectricalHardwareError):
        E.fit_synthetic_bvd(sweep)


# --- report claims nothing -----------------------------------------------

def test_report_claims_nothing():
    rep = E.electrical_report()
    assert rep["measured_here"] == "nothing"
    assert rep["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert rep["physical_run"] == "PREREGISTERED_NOT_RUN"
    assert rep["claim_class"] == C.ClaimClass.SOFTWARE_IMPLEMENTED.value
    assert set(rep["fault_modes"]) == {f.value for f in E.FaultMode}


# --- schema conformance ---------------------------------------------------

@pytest.mark.skipif(jsonschema is None, reason="jsonschema not installed")
def test_error_budget_conforms_to_schema():
    schema = json.loads(
        (_SCHEMA_DIR / "error_budget.schema.json").read_text())
    jsonschema.validate(E.electrical_error_budget(), schema)


@pytest.mark.skipif(jsonschema is None, reason="jsonschema not installed")
def test_observation_record_conforms_to_schema():
    schema = json.loads(
        (_SCHEMA_DIR / "observation_record.schema.json").read_text())
    fit = E.fit_synthetic_bvd(_synthetic_device(n=4001).acquire_sweep(seed=0))
    jsonschema.validate(E.observation_record(fit), schema)


@pytest.mark.skipif(jsonschema is None, reason="jsonschema not installed")
def test_receipt_conforms_to_schema():
    receipt = json.loads(
        (Path(__file__).resolve().parents[2] / "docs" / "v8" / "receipts"
         / "P14.json").read_text())
    schema = json.loads(
        (_SCHEMA_DIR / "phase_receipt.schema.json").read_text())
    jsonschema.validate(receipt, schema)
    assert receipt["phase_id"] == "P14"
    assert receipt["status"] == "COMPLETE"
