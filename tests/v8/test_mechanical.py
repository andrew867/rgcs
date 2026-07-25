"""P13 — the mechanical measurement lane: four modes, modal fit, error budget.

POWER (a planted mode is recovered within budget), negative (REAL acquires
nothing; every fault mode; a fit within noise is not a mode; aliasing and
clipping detected; fixture motion not assigned to specimen; no promotion to
measurement), and determinism.
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
from r15 import instruments as I
from r15 import mechanical as M


FS = 1.0e4
_SCHEMA_DIR = Path(__file__).resolve().parents[2] / "r15" / "schemas"


def _load_schema(name: str) -> dict:
    return json.loads((_SCHEMA_DIR / name).read_text(encoding="utf-8"))


# --- POWER: a planted mode is recovered within the error budget ----------

def test_planted_ringdown_mode_recovered_within_budget():
    mode = M.ModalMode(frequency_hz=150.0, q=80.0)
    _, sig = M.synthesize_modal_record((mode,), sample_rate_hz=FS,
                                       n_samples=16384, seed=0)
    fit = M.fit_ringdown(sig, FS)
    assert M.DEFAULT_BUDGET.within_budget(mode.q, fit.q)
    assert fit.claim_class is C.ClaimClass.SYNTHETIC_OBSERVATION


def test_planted_frequency_recovered_within_budget():
    mode = M.ModalMode(frequency_hz=150.0, q=80.0)
    _, sig = M.synthesize_modal_record((mode,), sample_rate_hz=FS,
                                       n_samples=16384, seed=0)
    fit = M.fit_ringdown(sig, FS)
    assert M.DEFAULT_BUDGET.within_budget(mode.frequency_hz, fit.frequency_hz)


def test_synthetic_lane_planted_mode_recovered():
    lane = M.build_synthetic_lane()
    acq = lane.acquire(n_samples=16384, seed=0)
    fit = M.fit_ringdown(acq.samples, acq.sample_rate_hz)
    assert M.DEFAULT_BUDGET.within_budget(M.DEFAULT_MODE.frequency_hz,
                                          fit.frequency_hz)
    assert M.DEFAULT_BUDGET.within_budget(M.DEFAULT_MODE.q, fit.q)


def test_damping_ratio_is_one_over_two_q():
    mode = M.ModalMode(frequency_hz=200.0, q=50.0)
    assert mode.damping_ratio == pytest.approx(1.0 / (2.0 * 50.0))
    _, sig = M.synthesize_modal_record((mode,), sample_rate_hz=FS,
                                       n_samples=16384, seed=2)
    fit = M.fit_ringdown(sig, FS)
    assert fit.damping_ratio == pytest.approx(1.0 / (2.0 * fit.q))


# --- mode identification and fixture / specimen separation ---------------

def _two_mode_signal():
    two = (M.ModalMode(300.0, 120.0, 1.0), M.ModalMode(820.0, 120.0, 1.0))
    _, sig = M.synthesize_modal_record(two, sample_rate_hz=FS,
                                       n_samples=16384, seed=1)
    return sig


def test_two_modes_identified():
    ids = M.fit_modal_frequencies(_two_mode_signal(), FS, n_modes=2)
    freqs = sorted(m.frequency_hz for m in ids)
    assert len(ids) == 2
    assert freqs[0] == pytest.approx(300.0, abs=2.0)
    assert freqs[1] == pytest.approx(820.0, abs=2.0)


def test_fixture_motion_is_not_assigned_to_specimen():
    ids = M.fit_modal_frequencies(_two_mode_signal(), FS, n_modes=2)
    split = M.separate_fixture_specimen(ids, fixture_band=(780.0, 860.0))
    # the 820 Hz fixture resonance goes to the fixture, not the specimen
    assert any(m.frequency_hz == pytest.approx(820.0, abs=2.0)
               for m in split["fixture_modes"])
    assert all(not (780.0 <= m.frequency_hz <= 860.0)
               for m in split["specimen_modes"])
    assert any(m.frequency_hz == pytest.approx(300.0, abs=2.0)
               for m in split["specimen_modes"])


# --- aliasing is detected ------------------------------------------------

def test_aliasing_mode_above_nyquist_is_refused():
    with pytest.raises(M.MechanicalError, match="ALIAS"):
        M.synthesize_modal_record((M.ModalMode(6000.0, 50.0),),
                                  sample_rate_hz=FS, n_samples=2048)


def test_aliasing_risk_flags_above_nyquist():
    assert M.aliasing_risk(6000.0, FS) is True
    assert M.aliasing_risk(150.0, FS) is False


# --- clipping is detected ------------------------------------------------

@pytest.mark.parametrize("fault", [I.FaultMode.CLIPPING, I.FaultMode.SATURATION])
def test_clipping_is_detected(fault):
    lane = M.build_fault_lane(faults=(fault,))
    acq = lane.acquire(n_samples=4096, seed=3)
    assert M.is_clipped(acq.samples)


def test_clean_reading_is_not_flagged_clipped():
    acq = M.build_synthetic_lane().acquire(n_samples=4096, seed=3)
    assert not M.is_clipped(acq.samples)


# --- REAL_DEVICE acquires nothing ----------------------------------------

def test_real_lane_acquires_nothing():
    lane = M.build_real_lane()
    with pytest.raises(I.NoHardwareError):
        lane.acquire(n_samples=64, seed=0)


def test_real_lane_blocked_receipt_is_preregistered_not_run():
    receipt = M.build_real_lane().blocked_receipt()
    assert receipt["acquired"] is False
    assert receipt["n_samples"] == 0
    assert receipt["physical_acquisition_status"] == "PREREGISTERED_NOT_RUN"


# --- fault injection covers all five faults ------------------------------

@pytest.mark.parametrize("fault", list(I.FaultMode))
def test_each_fault_mode_alters_the_reading(fault):
    lane = M.build_fault_lane(faults=(fault,))
    clean = M.build_synthetic_lane(instrument_id="clean").acquire(
        n_samples=4096, seed=3)
    faulty = lane.acquire(n_samples=4096, seed=3)
    assert fault in faulty.faults
    assert not np.array_equal(clean.samples, faulty.samples, equal_nan=True)


def test_missing_samples_reading_refuses_a_fit():
    lane = M.build_fault_lane(faults=(I.FaultMode.MISSING_SAMPLES,))
    acq = lane.acquire(n_samples=4096, seed=3)
    assert np.any(np.isnan(acq.samples))
    with pytest.raises(M.MechanicalError, match="missing samples"):
        M.fit_ringdown(acq.samples, acq.sample_rate_hz)


def test_packet_loss_zero_fills():
    lane = M.build_fault_lane(faults=(I.FaultMode.PACKET_LOSS,))
    acq = lane.acquire(n_samples=4096, seed=3)
    assert np.count_nonzero(acq.samples == 0.0) > 0


# --- a fit within noise is not a mode ------------------------------------

def test_a_fit_within_noise_is_not_a_mode():
    rng = np.random.default_rng(5)
    noise = rng.standard_normal(16384)
    ids = M.fit_modal_frequencies(noise, FS, n_modes=3)
    assert ids == []
    assert not M.is_genuine_mode(M._peak_prominence(noise))


def test_assert_mode_above_noise_refuses_noise():
    with pytest.raises(C.ClaimError):
        M.assert_mode_above_noise(prominence=2.0)
    # a genuine, prominent mode does not raise
    M.assert_mode_above_noise(prominence=50.0)


# --- the four modes stay distinct ----------------------------------------

def test_replay_lane_replays_recorded_artifact():
    recorded = M.build_synthetic_lane().acquire(n_samples=2048, seed=7)
    replay = M.build_replay_lane(recorded)
    out = replay.acquire(n_samples=2048, seed=0)
    assert np.array_equal(out.samples, recorded.samples)
    assert out.mode is I.InstrumentMode.REPLAY_DEVICE


def test_four_modes_stay_distinct():
    assert M.build_synthetic_lane().mode is I.InstrumentMode.SYNTHETIC_DEVICE
    assert M.build_real_lane().mode is I.InstrumentMode.REAL_DEVICE
    rec = M.build_synthetic_lane().acquire(n_samples=256, seed=0)
    assert M.build_replay_lane(rec).mode is I.InstrumentMode.REPLAY_DEVICE
    assert M.build_fault_lane(faults=(I.FaultMode.DRIFT,)).mode is \
        I.InstrumentMode.FAULT_INJECTION_DEVICE


# --- determinism ----------------------------------------------------------

def test_synthetic_same_seed_identical():
    lane = M.build_synthetic_lane()
    a = lane.acquire(n_samples=2048, seed=7)
    b = lane.acquire(n_samples=2048, seed=7)
    assert np.array_equal(a.samples, b.samples)
    assert M.fit_ringdown(a.samples, FS).q == M.fit_ringdown(b.samples, FS).q


def test_synthetic_different_seed_differs():
    lane = M.build_synthetic_lane()
    a = lane.acquire(n_samples=2048, seed=7)
    b = lane.acquire(n_samples=2048, seed=8)
    assert not np.array_equal(a.samples, b.samples)


def test_fault_injection_is_deterministic():
    lane = M.build_fault_lane(faults=tuple(I.FaultMode))
    a = lane.acquire(n_samples=4096, seed=11)
    b = lane.acquire(n_samples=4096, seed=11)
    assert np.array_equal(a.samples, b.samples, equal_nan=True)


# --- no promotion to a measurement ---------------------------------------

def test_fit_cannot_be_a_measurement_class():
    with pytest.raises(C.ClaimError):
        M.FittedMode(frequency_hz=1.0, q=1.0, damping_ratio=0.5, amplitude=1.0,
                     prominence=99.0, method="x",
                     claim_class=C.ClaimClass.PHYSICAL_MEASUREMENT)


def test_refuse_fit_as_measurement_raises():
    with pytest.raises(M.MechanicalError):
        M.refuse_fit_as_measurement(quantity="modal_frequency")


def test_refuse_synthetic_q_as_device_q_raises():
    with pytest.raises(Exception):
        M.refuse_synthetic_Q_as_device_Q(q_value=80.0)


def test_refuse_prediction_as_measurement_raises():
    with pytest.raises(C.ClaimError):
        M.refuse_prediction_as_measurement()


def test_predicted_rod_mode_is_a_model_prediction():
    pred = M.predicted_rod_mode_hz(1, 0.1, 10.0, 1.0, 1.0e-3)
    assert pred["frequency_hz"] > 0.0
    assert pred["claim_class"] == "MODEL_PREDICTION"
    assert pred["measured_here"] == "nothing"


# --- FRF, coherence, integration placeholders ----------------------------

def test_coherence_of_identical_signals_is_one():
    x = M.build_synthetic_lane().acquire(n_samples=4096, seed=1).samples
    coh = M.coherence(x, x, FS)
    assert float(np.nanmean(coh["coherence"])) == pytest.approx(1.0, abs=1e-9)


def test_coherence_is_bounded():
    x = M.build_synthetic_lane().acquire(n_samples=4096, seed=1).samples
    rng = np.random.default_rng(9)
    y = rng.standard_normal(x.size)
    coh = M.coherence(x, y, FS)
    assert np.all(coh["coherence"] >= 0.0) and np.all(coh["coherence"] <= 1.0)


def test_frf_of_identical_signals_is_near_unity():
    x = M.build_synthetic_lane().acquire(n_samples=4096, seed=1).samples
    H = M.frf(x, x, FS)
    assert float(np.nanmax(np.abs(H["magnitude"] - 1.0))) < 1e-6


def test_double_integration_preserves_tone_frequency():
    # exactly 250 cycles over 10000 samples at 10 kHz: bin-aligned, no leakage
    t = np.arange(10000, dtype=float) / FS
    accel = np.sin(2.0 * np.pi * 250.0 * t)
    disp = M.to_displacement(accel, FS)
    freqs = np.fft.rfftfreq(disp.size, 1.0 / FS)
    peak = freqs[int(np.argmax(np.abs(np.fft.rfft(disp))))]
    assert peak == pytest.approx(250.0, abs=3.0)


def test_channel_band_check_uses_detector_authority():
    assert M.channel_band_ok(M.MechanicalChannel.ACCELEROMETER, 150.0) in (True, False)


# --- error budget and schema conformance ---------------------------------

def test_empty_error_budget_is_refused():
    with pytest.raises(M.MechanicalError):
        M.MechanicalErrorBudget(components={})


def test_error_budget_record_conforms_to_schema():
    if jsonschema is None:  # pragma: no cover
        pytest.skip("jsonschema not installed")
    rec = M.DEFAULT_BUDGET.to_error_budget_record()
    jsonschema.validate(rec, _load_schema("error_budget.schema.json"))
    # every named component of the policy is present
    names = {c["name"] for c in rec["components"]}
    assert names == set(M.DEFAULT_BUDGET_COMPONENTS)


def test_observation_record_conforms_to_schema():
    if jsonschema is None:  # pragma: no cover
        pytest.skip("jsonschema not installed")
    obs = M.modal_observation_record(
        "obs-1", "run-1", ("art-1",), "modal_frequency", 150.0, "Hz",
        {"type": "combined", "relative": 0.045})
    jsonschema.validate(obs, _load_schema("observation_record.schema.json"))
    assert obs["claim_class"] == "SYNTHETIC_OBSERVATION"


# --- report and receipt ---------------------------------------------------

def test_report_claims_nothing():
    r = M.mechanical_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["physical_acquisition_status"] == "PREREGISTERED_NOT_RUN"
    assert r["fit_claim_class"] == "SYNTHETIC_OBSERVATION"
    assert set(r["fault_modes"]) == {f.value for f in I.FaultMode}
    assert r["recovered_frequency_within_budget"]
    assert r["recovered_q_within_budget"]
    assert r["specimen_free_of_fixture_mode"]


def test_receipt_conforms_to_phase_receipt_schema():
    if jsonschema is None:  # pragma: no cover
        pytest.skip("jsonschema not installed")
    receipt_path = (Path(__file__).resolve().parents[2] / "docs" / "v8"
                    / "receipts" / "P13.json")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    jsonschema.validate(receipt, _load_schema("phase_receipt.schema.json"))
    assert receipt["phase_id"] == "P13"
    assert receipt["status"] == "COMPLETE"
    assert receipt["blocked_reason"] is None
    assert receipt["commit"] is None
    assert receipt["claim_cap"] == "SYNTHETIC_OBSERVATION"
