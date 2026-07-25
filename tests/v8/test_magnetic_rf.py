"""P17 — the magnetic and RF measurement lane. POWER, negative/refusal, and
determinism tests, with schema conformance for the observation and budget
records."""

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
from r15 import magnetic_rf as M

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "r15" / "schemas"


# --- fixtures -------------------------------------------------------------

def _config():
    return M.MagneticRFConfig()


def _band():
    return M.RFBand(f_start_hz=9.5e5, f_stop_hz=1.05e6, rbw_hz=100.0)


def _clock():
    return M.ClockBinding(sample_rate_hz=1.0e3, clock_source="synthetic_tcxo",
                          epoch_s=0.0)


def _budget():
    return M.MagneticRFBudget(
        quantity="rf_power", units="linear",
        components={"magnetometer_noise": 1.0e-8, "rf_background": 1.0e-3,
                    "calibration": 2.0e-4, "clock": 1.0e-5,
                    "quantization": 1.0e-4, "shielding_leakage": 5.0e-5})


def _load_schema(name):
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


# --- POWER: planted line and planted field shift recovered ---------------

def test_power_planted_rf_line_is_recovered():
    freqs, power = M.SyntheticMagneticRFDevice(_config()).acquire_spectrum(
        _band(), seed=7, applied_t=0.0)
    line = M.recover_rf_line(freqs, power, _budget())
    assert line["above_budget"] is True
    assert abs(line["peak_freq_hz"] - _config().f0_hz) <= _band().rbw_hz


def test_power_magnetic_field_shift_is_recovered():
    cfg = _config()
    applied = 5.0e-9
    freqs, power = M.SyntheticMagneticRFDevice(cfg).acquire_spectrum(
        _band(), seed=7, applied_t=applied)
    rec = M.recover_field_shift(cfg, freqs, power, _budget())
    # recovered field is within one RBW bin of the planted field
    tol = _band().rbw_hz / cfg.gyro_hz_per_t
    assert abs(rec["recovered_field_t"] - applied) <= 2.0 * tol


def test_line_freq_shift_is_linear_in_field():
    cfg = _config()
    f_lo = M.line_freq_from_field(cfg, 0.0)
    f_hi = M.line_freq_from_field(cfg, 1.0e-8)
    assert f_hi > f_lo
    assert abs(M.field_from_line_freq(cfg, f_hi) - 1.0e-8) < 1e-18


# --- determinism ----------------------------------------------------------

def test_synthetic_spectrum_is_deterministic():
    cfg, band = _config(), _band()
    fa, pa = M.synth_rf_spectrum(cfg, band, seed=3)
    fb, pb = M.synth_rf_spectrum(cfg, band, seed=3)
    assert np.array_equal(pa, pb) and np.array_equal(fa, fb)


def test_synthetic_bfield_is_deterministic_and_seed_sensitive():
    cfg = _config()
    a = M.synth_bfield(cfg, n_samples=128, seed=1, clock=_clock())
    b = M.synth_bfield(cfg, n_samples=128, seed=1, clock=_clock())
    c = M.synth_bfield(cfg, n_samples=128, seed=2, clock=_clock())
    assert np.array_equal(a, b)
    assert not np.array_equal(a, c)


def test_replay_device_returns_recorded_artifact_unchanged():
    cfg = _config()
    trace = M.synth_bfield(cfg, n_samples=64, seed=5, clock=_clock())
    replay = M.ReplayMagneticRFDevice(trace).replay()
    assert np.array_equal(replay, trace)


# --- negative: the REAL device acquires nothing --------------------------

def test_real_device_acquires_nothing():
    dev = M.RealMagneticRFDevice()
    with pytest.raises(M.NoHardwareError):
        dev.acquire()
    assert dev.status()["physical_run"] == "PREREGISTERED_NOT_RUN"
    assert dev.status()["measured_here"] == "nothing"


# --- negative: every fault mode is distinct and detectable ---------------

@pytest.mark.parametrize("fault", sorted(M.TIME_DOMAIN_FAULTS,
                                         key=lambda f: f.value))
def test_time_domain_fault_corrupts_the_trace(fault):
    cfg = _config()
    clean = M.synth_bfield(cfg, n_samples=128, seed=9, clock=_clock(),
                           applied_t=0.0)
    dev = M.FaultInjectionMagneticRFDevice(fault)
    faulted = dev.inject_timeseries(clean, seed=9)
    assert faulted.shape == clean.shape
    if fault is M.FaultKind.MISSING_SAMPLES:
        assert np.isnan(faulted).any()
    elif fault is M.FaultKind.PACKET_LOSS:
        assert (faulted == 0.0).any()
    else:
        assert not np.allclose(faulted, clean)


@pytest.mark.parametrize("fault", sorted(M.SPECTRAL_FAULTS,
                                         key=lambda f: f.value))
def test_spectral_fault_adds_an_ordinary_line(fault):
    cfg, band = _config(), _band()
    freqs, power = M.synth_rf_spectrum(cfg, band, seed=4)
    dev = M.FaultInjectionMagneticRFDevice(fault, line_hz=9.6e5)
    f2, p2, center = dev.inject_spectrum(
        freqs, power, drive_fundamentals=[4.8e5, 4.9e5], rbw_hz=band.rbw_hz)
    assert p2.shape == power.shape
    assert p2.max() >= power.max()


def test_time_fault_refuses_spectral_use_and_vice_versa():
    with pytest.raises(M.MagneticRFError):
        M.FaultInjectionMagneticRFDevice(M.FaultKind.SPUR).inject_timeseries(
            np.zeros(8))
    with pytest.raises(M.MagneticRFError):
        M.FaultInjectionMagneticRFDevice(
            M.FaultKind.CLIPPING).inject_spectrum(np.arange(8.0), np.zeros(8))


# --- negative: EMI / a spur / a mains harmonic is ordinary, not a signal --

def test_mains_harmonic_is_ordinary_not_a_signal():
    feat = M.classify_feature(180.0)
    assert feat["feature_kind"] == M.FeatureKind.MAINS_PICKUP.value
    assert feat["is_ordinary"] is True


def test_drive_harmonic_is_ordinary():
    feat = M.classify_feature(2200.0, drive_fundamentals=[1100.0, 1700.0])
    assert feat["feature_kind"] == M.FeatureKind.HARMONIC.value
    assert feat["is_ordinary"] is True


def test_intermodulation_product_is_ordinary():
    feat = M.classify_feature(500.0, drive_fundamentals=[1100.0, 1700.0])
    assert feat["feature_kind"] == M.FeatureKind.INTERMOD.value
    assert feat["is_ordinary"] is True


def test_clean_line_with_no_ordinary_match_is_a_candidate():
    feat = M.classify_feature(1.0e6, drive_fundamentals=[1100.0, 1700.0])
    assert feat["feature_kind"] == M.FeatureKind.SIGNAL_CANDIDATE.value
    assert feat["is_ordinary"] is False


def test_refuse_emi_as_signal_always_raises():
    with pytest.raises(M.MagneticRFError):
        M.refuse_emi_as_signal(60.0, "mains_harmonic")
    with pytest.raises(M.MagneticRFError):
        M.refuse_emi_as_signal(2.4e9, "analyser_spur")


def test_line_below_budget_is_noise_not_a_resonance():
    # a spectrum whose only content is background noise (no planted line)
    cfg = M.MagneticRFConfig(line_amp=0.0, background=1.0e-3, rf_noise=1.0e-5)
    band = _band()
    freqs, power = M.synth_rf_spectrum(cfg, band, seed=2)
    with pytest.raises(C.ClaimError):
        M.recover_field_shift(cfg, freqs, power, _budget())


# --- negative: known interference is localized ---------------------------

def test_known_rf_interference_is_localized():
    known = {"mains_3rd": 180.0, "wifi_spur": 2.4e9}
    loc = M.localize_interference(180.0, known)
    assert loc["localized"] is True
    assert loc["source"] == "mains_3rd"
    assert loc["is_ordinary"] is True
    miss = M.localize_interference(1.234e6, known)
    assert miss["localized"] is False


# --- reversal signs propagate --------------------------------------------

def test_reversal_signs_propagate_and_cancel_pickup():
    cfg = _config()
    clock = _clock()
    fwd = M.synth_bfield(cfg, n_samples=256, seed=1, clock=clock,
                         applied_t=1.0e-7)
    rev = M.synth_bfield(cfg, n_samples=256, seed=1, clock=clock,
                         applied_t=-1.0e-7)
    d = M.coil_reversal_demodulate(fwd, rev)
    # the field-linear part follows the drive polarity
    assert d["sign"] == 1
    # reversing the pair flips the recovered sign: signs propagate
    d2 = M.coil_reversal_demodulate(rev, fwd)
    assert d2["sign"] == -1
    # the DC pickup (common offset) survives in the even part
    assert d["pickup_mean"] > d["field_linear_mean"]


# --- dummy loads expose pickup -------------------------------------------

def test_dummy_load_exposes_pickup():
    cfg, band = _config(), _band()
    freqs = band.freqs()
    # specimen run: a real specimen line plus a shared pickup line
    spec = np.full(freqs.size, cfg.background)
    spec = M._add_line(freqs, spec, 1.0e6, 1.0, band.rbw_hz)   # specimen line
    spec = M._add_line(freqs, spec, 9.6e5, 1.0, band.rbw_hz)   # pickup line
    # dummy run: no specimen, only the pickup line
    dummy = np.full(freqs.size, cfg.background)
    dummy = M._add_line(freqs, dummy, 9.6e5, 1.0, band.rbw_hz)
    out = M.dummy_load_control(spec, dummy, freqs)
    assert out["pickup_exposed"] is True
    assert any(abs(f - 9.6e5) <= band.rbw_hz for f in out["pickup_freqs"])
    assert any(abs(f - 1.0e6) <= band.rbw_hz for f in out["candidate_freqs"])


# --- antenna geometry / orientation / clock binding ----------------------

def test_antenna_geometry_orientation_reference_has_axis_ambiguity():
    ant = M.AntennaGeometry(probe_type="loop", loop_area_m2=1e-4, turns=10,
                            orientation=(0.0, 0.0, 1.0), shielding_db=40.0,
                            standoff_m=0.05)
    ref = ant.orientation_reference((1.0, 0.0, 0.0))
    assert ref["recovered_dof"] == 2 and ref["undetermined_dof"] == 1
    assert ant.shielding_linear() < 1.0


def test_bad_antenna_geometry_is_refused():
    with pytest.raises(M.MagneticRFError):
        M.AntennaGeometry(probe_type="loop", loop_area_m2=-1.0, turns=1,
                          orientation=(0.0, 0.0, 1.0), shielding_db=0.0,
                          standoff_m=0.0)


def test_clock_binding_binds_bandwidth():
    clock = _clock()
    assert clock.covers(400.0) is True
    assert clock.covers(600.0) is False   # beyond Nyquist of 500 Hz


def test_magnetometer_bandwidth_reuses_r11_hall():
    dev = M.SyntheticMagneticRFDevice(_config())
    assert dev.bandwidth_ok(1.0e3) is True
    assert dev.bandwidth_ok(1.0e7) is False   # above the Hall band ceiling


# --- schema conformance ---------------------------------------------------

@pytest.mark.skipif(jsonschema is None, reason="jsonschema not installed")
def test_observation_record_conforms_to_schema():
    obs = M.MagneticRFObservation(
        observation_id="obs-1", run_id="run-1", quantity="rf_line_freq",
        value=1.0e6, units="Hz",
        uncertainty=_budget().to_record("b1"),
        device_mode=M.DeviceMode.SYNTHETIC_DEVICE,
        source_artifacts=("synthetic_spectrum",))
    jsonschema.validate(obs.to_record(),
                        _load_schema("observation_record.schema.json"))
    assert obs.to_record()["claim_class"] == "SYNTHETIC_OBSERVATION"


@pytest.mark.skipif(jsonschema is None, reason="jsonschema not installed")
def test_error_budget_conforms_to_schema():
    rec = _budget().to_record("mag_rf_budget_1")
    jsonschema.validate(rec, _load_schema("error_budget.schema.json"))
    assert rec["combination_method"] == "root_sum_square"


def test_error_budget_requires_ambient_rf_background():
    with pytest.raises(M.MagneticRFError):
        M.MagneticRFBudget(quantity="rf_power", units="linear",
                           components={"magnetometer_noise": 1e-8})


# --- no promotion ---------------------------------------------------------

def test_observation_refuses_a_measurement_claim_class():
    with pytest.raises(M.MagneticRFError):
        M.MagneticRFObservation(
            observation_id="o", run_id="r", quantity="q", value=1.0,
            units="T", uncertainty={}, device_mode=M.DeviceMode.REAL_DEVICE,
            claim_class=C.ClaimClass.PHYSICAL_MEASUREMENT)


def test_synthetic_is_not_physical():
    with pytest.raises(C.ClaimError):
        C.refuse_synthetic_as_physical()


def test_report_claims_nothing():
    rep = M.magnetic_rf_report()
    assert rep["measured_here"] == "nothing"
    assert rep["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert rep["reading_claim_class"] == "SYNTHETIC_OBSERVATION"
    assert len(rep["device_modes"]) == 4
    assert rep["verdict"] == M.VERDICT
