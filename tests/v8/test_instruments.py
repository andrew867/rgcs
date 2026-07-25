"""R15 P01: the instrument registry, its four modes, and its refusals."""

from __future__ import annotations

from datetime import date

import numpy as np
import pytest

from r15 import claims
from r15 import instruments as I
from r15 import synthetic_instruments as SI


# --- fixtures -------------------------------------------------------------

VALID_CAL = I.Calibration(
    "cal_valid", "generic", date(2026, 1, 1), date(2027, 1, 1))
EXPIRED_CAL = I.Calibration(
    "cal_expired", "generic", date(2019, 1, 1), date(2020, 1, 1))
AS_OF = date(2026, 7, 24)


def _registry_with_synthetic(instrument_type="source",
                             cal=VALID_CAL) -> I.InstrumentRegistry:
    reg = I.InstrumentRegistry()
    reg.register_calibration(cal)
    dev = SI.build_synthetic_device(instrument_type,
                                    calibration_ids=(cal.calibration_id,))
    reg.register(dev)
    return reg


# --- synthetic drivers are deterministic under a seed --------------------

@pytest.mark.parametrize("itype", sorted(SI.SYNTHETIC_DRIVERS))
def test_synthetic_same_seed_identical(itype):
    dev = SI.build_synthetic_device(itype)
    cap = dev.driver.capability
    a = dev.acquire(cap, n_samples=256, seed=7)
    b = dev.acquire(cap, n_samples=256, seed=7)
    assert np.array_equal(a.samples, b.samples, equal_nan=True)
    assert a.digest() == b.digest()


@pytest.mark.parametrize("itype", sorted(SI.SYNTHETIC_DRIVERS))
def test_synthetic_different_seed_differs(itype):
    dev = SI.build_synthetic_device(itype)
    cap = dev.driver.capability
    a = dev.acquire(cap, n_samples=256, seed=1)
    b = dev.acquire(cap, n_samples=256, seed=2)
    assert not np.array_equal(a.samples, b.samples)


def test_all_nine_driver_types_present():
    assert set(SI.SYNTHETIC_DRIVERS) == {
        "source", "digitizer", "impedance", "microphone", "accelerometer",
        "photodiode", "thermal", "magnetic", "clock"}


def test_synthetic_reading_is_synthetic_observation():
    dev = SI.build_synthetic_device("source")
    a = dev.acquire(I.Capability.SOURCE, n_samples=64, seed=0)
    assert a.claim_class is claims.ClaimClass.SYNTHETIC_OBSERVATION
    assert a.claim_class not in claims.MEASUREMENT_CLASSES


# --- expired / missing calibration forces refusal ------------------------

def test_expired_calibration_refused():
    reg = _registry_with_synthetic(cal=EXPIRED_CAL)
    with pytest.raises(I.InstrumentError, match="calibration"):
        reg.acquire("synthetic_source", I.Capability.SOURCE, as_of=AS_OF,
                    n_samples=64, seed=0)


def test_valid_calibration_permits_acquisition():
    reg = _registry_with_synthetic(cal=VALID_CAL)
    a = reg.acquire("synthetic_source", I.Capability.SOURCE, as_of=AS_OF,
                    n_samples=64, seed=0)
    assert a.samples.size == 64


def test_missing_calibration_refused():
    reg = I.InstrumentRegistry()
    dev = SI.build_synthetic_device("source")  # no calibration_ids
    reg.register(dev)
    with pytest.raises(I.InstrumentError, match="no calibration"):
        reg.acquire("synthetic_source", I.Capability.SOURCE, as_of=AS_OF)


# --- unsupported capability refused --------------------------------------

def test_unsupported_capability_refused():
    reg = _registry_with_synthetic("source")
    with pytest.raises(I.InstrumentError, match="capability"):
        reg.acquire("synthetic_source", I.Capability.MAGNETIC, as_of=AS_OF,
                    n_samples=64, seed=0)


def test_record_rejects_non_capability():
    with pytest.raises(I.InstrumentError):
        I.InstrumentRecord(
            instrument_id="x", instrument_type="x",
            mode=I.InstrumentMode.SYNTHETIC_DEVICE, firmware="f",
            clock_source="c", capabilities=frozenset({"not_a_cap"}),
            uncertainty_model={"sigma": 1.0})


# --- REAL_DEVICE acquires nothing without hardware -----------------------

def _real_record():
    return I.InstrumentRecord(
        instrument_id="real_source", instrument_type="source",
        mode=I.InstrumentMode.REAL_DEVICE, firmware="fw-1.0",
        clock_source="ocxo", capabilities=frozenset({I.Capability.SOURCE}),
        uncertainty_model={"type": "datasheet", "sigma": 0.0},
        calibration_ids=("cal_valid",))


def test_real_device_acquisition_is_blocked_not_faked():
    dev = I.RealDevice(_real_record())
    with pytest.raises(I.NoHardwareError):
        dev.acquire(I.Capability.SOURCE, n_samples=64, seed=0)


def test_real_device_through_registry_reaches_boundary_and_blocks():
    reg = I.InstrumentRegistry()
    reg.register_calibration(VALID_CAL)
    reg.register(I.RealDevice(_real_record()))
    # calibration + capability gate pass, yet no sample is produced
    with pytest.raises(I.NoHardwareError):
        reg.acquire("real_source", I.Capability.SOURCE, as_of=AS_OF,
                    n_samples=64, seed=0)


def test_real_device_blocked_receipt_acquires_nothing():
    dev = I.RealDevice(_real_record())
    receipt = dev.blocked_receipt(I.Capability.SOURCE)
    assert receipt["acquired"] is False
    assert receipt["n_samples"] == 0
    assert receipt["status"] == "BLOCKED"


# --- fault injection covers all five faults ------------------------------

@pytest.mark.parametrize("fault", list(I.FaultMode))
def test_each_fault_alters_the_clean_reading(fault):
    inner = SI.build_synthetic_device("source",
                                      instrument_id="fi_source_inner")
    rec = I.InstrumentRecord(
        instrument_id="fi_source", instrument_type="source",
        mode=I.InstrumentMode.FAULT_INJECTION_DEVICE, firmware="fw",
        clock_source="synthetic", capabilities=frozenset({I.Capability.SOURCE}),
        uncertainty_model={"sigma": 5e-3})
    fi = I.FaultInjectionDevice(rec, inner, faults=(fault,))
    clean = inner.acquire(I.Capability.SOURCE, n_samples=512, seed=3)
    faulty = fi.acquire(I.Capability.SOURCE, n_samples=512, seed=3)
    assert fault in faulty.faults
    # the faulty reading differs from the clean one (NaN-aware)
    same = np.array_equal(clean.samples, faulty.samples, equal_nan=True)
    assert not same


def test_all_five_faults_together_are_deterministic():
    inner = SI.build_synthetic_device("digitizer",
                                      instrument_id="fi_dig_inner")
    rec = I.InstrumentRecord(
        instrument_id="fi_dig", instrument_type="digitizer",
        mode=I.InstrumentMode.FAULT_INJECTION_DEVICE, firmware="fw",
        clock_source="synthetic",
        capabilities=frozenset({I.Capability.DIGITIZE}),
        uncertainty_model={"sigma": 2e-3})
    fi = I.FaultInjectionDevice(rec, inner, faults=tuple(I.FaultMode))
    a = fi.acquire(I.Capability.DIGITIZE, n_samples=400, seed=11)
    b = fi.acquire(I.Capability.DIGITIZE, n_samples=400, seed=11)
    assert np.array_equal(a.samples, b.samples, equal_nan=True)
    assert set(a.faults) == set(I.FaultMode)


def test_packet_loss_zero_fills_and_missing_samples_nan():
    inner = SI.build_synthetic_device("microphone",
                                      instrument_id="mic_inner")
    rec_pl = I.InstrumentRecord(
        instrument_id="mic_pl", instrument_type="microphone",
        mode=I.InstrumentMode.FAULT_INJECTION_DEVICE, firmware="fw",
        clock_source="synthetic",
        capabilities=frozenset({I.Capability.ACOUSTIC}),
        uncertainty_model={"sigma": 1e-2})
    pl = I.FaultInjectionDevice(rec_pl, inner, faults=(I.FaultMode.PACKET_LOSS,))
    ms = I.FaultInjectionDevice(rec_pl, inner,
                                faults=(I.FaultMode.MISSING_SAMPLES,))
    a = pl.acquire(I.Capability.ACOUSTIC, n_samples=500, seed=5)
    b = ms.acquire(I.Capability.ACOUSTIC, n_samples=500, seed=5)
    assert np.count_nonzero(a.samples == 0.0) > 0     # a lost packet
    assert np.count_nonzero(np.isnan(b.samples)) > 0  # missing samples


def test_fault_device_needs_at_least_one_fault():
    inner = SI.build_synthetic_device("source", instrument_id="z_inner")
    rec = I.InstrumentRecord(
        instrument_id="z_fi", instrument_type="source",
        mode=I.InstrumentMode.FAULT_INJECTION_DEVICE, firmware="fw",
        clock_source="synthetic", capabilities=frozenset({I.Capability.SOURCE}),
        uncertainty_model={"sigma": 5e-3})
    with pytest.raises(I.InstrumentError):
        I.FaultInjectionDevice(rec, inner, faults=())


# --- the four modes stay distinct ----------------------------------------

def test_four_modes_are_distinct_values():
    modes = {m.value for m in I.InstrumentMode}
    assert modes == {"REAL_DEVICE", "REPLAY_DEVICE", "SYNTHETIC_DEVICE",
                     "FAULT_INJECTION_DEVICE"}


def test_replay_device_replays_recorded_artifact():
    recorded = SI.build_synthetic_device("source").acquire(
        I.Capability.SOURCE, n_samples=128, seed=42)
    rec = I.InstrumentRecord(
        instrument_id="replay_source", instrument_type="source",
        mode=I.InstrumentMode.REPLAY_DEVICE, firmware="fw",
        clock_source="recorded", capabilities=frozenset({I.Capability.SOURCE}),
        uncertainty_model={"sigma": 5e-3})
    replay = I.ReplayDevice(rec, {I.Capability.SOURCE: recorded.samples},
                            sample_rate_hz=recorded.sample_rate_hz)
    out = replay.acquire(I.Capability.SOURCE, n_samples=128, seed=0)
    assert np.array_equal(out.samples, recorded.samples)
    assert out.mode is I.InstrumentMode.REPLAY_DEVICE


def test_modes_behave_differently_on_same_request():
    # synthetic produces; real refuses; replay returns the stored artifact
    syn = SI.build_synthetic_device("source").acquire(
        I.Capability.SOURCE, n_samples=64, seed=9)
    real = I.RealDevice(_real_record())
    with pytest.raises(I.NoHardwareError):
        real.acquire(I.Capability.SOURCE, n_samples=64, seed=9)
    assert syn.mode is I.InstrumentMode.SYNTHETIC_DEVICE


# --- quarantine -----------------------------------------------------------

def test_quarantined_instrument_refused():
    reg = _registry_with_synthetic("source")
    reg.quarantine("synthetic_source", "drift out of spec")
    assert reg.is_quarantined("synthetic_source")
    with pytest.raises(I.InstrumentError, match="QUARANTINED"):
        reg.acquire("synthetic_source", I.Capability.SOURCE, as_of=AS_OF)


# --- no promotion, and the report ----------------------------------------

def test_acquisition_cannot_be_a_measurement_class():
    with pytest.raises(claims.ClaimError):
        I.Acquisition(
            instrument_id="x", mode=I.InstrumentMode.SYNTHETIC_DEVICE,
            capability=I.Capability.SOURCE, samples=np.zeros(4),
            sample_rate_hz=1.0, seed=0,
            claim_class=claims.ClaimClass.PHYSICAL_MEASUREMENT)


def test_refuse_reading_as_measurement_raises():
    with pytest.raises(I.InstrumentError):
        I.refuse_reading_as_measurement()


def test_instruments_report_claims_nothing():
    r = I.instruments_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["reading_claim_class"] == "SYNTHETIC_OBSERVATION"
    assert set(r["fault_modes"]) == {f.value for f in I.FaultMode}


def test_synthetic_report_claims_nothing():
    r = SI.synthetic_instruments_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert len(r["drivers"]) == 9


def test_record_as_dict_is_schema_shaped():
    rec = SI.synthetic_record("magnetic", calibration_ids=("cal_valid",))
    d = rec.as_dict()
    for key in ("instrument_id", "instrument_type", "mode", "firmware",
                "clock_source", "capabilities", "uncertainty_model"):
        assert key in d
    assert d["mode"] == "SYNTHETIC_DEVICE"
