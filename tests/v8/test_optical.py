"""R15 P15: the optical measurement lane, its four modes, and its refusals.

POWER controls (a planted displacement / fringe / retardation is
recovered), negative and refusal paths (a REAL device acquires nothing;
every fault mode; intensity-only cannot yield phase; a synthetic
reconstruction is not measured), and determinism.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from jsonschema import validate

from r15 import claims
from r15 import optical as O


SCHEMA_DIR = Path(__file__).resolve().parents[2] / "r15" / "schemas"


def _schema(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


# --- POWER: a planted displacement is recovered (phase-sensitive) --------

def test_power_interferometric_recovers_planted_displacement():
    cfg = O.OpticalConfig()
    planted = 0.4 * cfg.unambiguous_displacement_m()
    trace = O.synthetic_interferogram(cfg, planted, seed=3)
    recovered = O.recover_displacement(trace, cfg)
    assert abs(recovered - planted) / abs(planted) < 1.0e-3


def test_power_across_several_planted_displacements():
    cfg = O.OpticalConfig()
    unamb = cfg.unambiguous_displacement_m()
    for frac in (0.1, 0.25, 0.5, 0.75):
        planted = frac * unamb
        trace = O.synthetic_interferogram(cfg, planted, seed=11)
        recovered = O.recover_displacement(trace, cfg)
        assert abs(recovered - planted) / abs(planted) < 5.0e-3


def test_power_photoelastic_recovers_planted_retardation():
    cfg = O.OpticalConfig()
    planted = 1.1  # radians, within [0, pi]
    trace = O.synthetic_photoelastic(cfg, planted, seed=5)
    recovered = O.recover_retardation(trace, cfg)
    assert abs(recovered - planted) < 5.0e-3


def test_power_synthetic_device_recovers_displacement_end_to_end():
    cfg = O.OpticalConfig()
    planted = 0.3 * cfg.unambiguous_displacement_m()
    dev = O.OpticalSyntheticDevice(cfg)
    obs = dev.acquire(O.ReadoutKind.INTERFEROMETRIC, run_id="r", seed=1,
                      displacement_m=planted)
    assert obs.quantity == "surface_displacement"
    assert abs(obs.value - planted) / abs(planted) < 1.0e-3
    assert obs.claim_class is claims.ClaimClass.SYNTHETIC_OBSERVATION


def test_reconstruction_round_trip_recovers_phantom():
    out = O.reconstruct_fringe_phantom(size=40, n_angles=90)
    assert out["reconstruction_error"] < 0.1
    assert out["claim_class"] == claims.ClaimClass.SYNTHETIC_OBSERVATION.value


# --- intensity-only is separated from phase-sensitive --------------------

def test_photodiode_is_phase_blind():
    cfg = O.OpticalConfig()
    unamb = cfg.unambiguous_displacement_m()
    a = O.synthetic_photodiode(cfg, displacement_m=0.0, seed=0)
    b = O.synthetic_photodiode(cfg, displacement_m=0.5 * unamb, seed=0)
    # displacement does not change the intensity-only trace at all
    assert np.array_equal(a, b)
    assert abs(O.recover_power_w(a) - cfg.power_w) < 1.0e-3 * cfg.power_w


def test_refuse_intensity_as_phase_raises():
    with pytest.raises(O.OpticalError, match="INTENSITY-ONLY"):
        O.refuse_intensity_as_phase()


def test_readout_families_are_disjoint():
    assert O.PHASE_SENSITIVE_READOUTS.isdisjoint(O.INTENSITY_ONLY_READOUTS)
    assert O.ReadoutKind.PHOTODIODE in O.INTENSITY_ONLY_READOUTS
    assert O.ReadoutKind.INTERFEROMETRIC in O.PHASE_SENSITIVE_READOUTS


# --- negative: a REAL device acquires nothing ----------------------------

def test_real_device_acquires_nothing():
    dev = O.OpticalRealDevice(O.OpticalConfig())
    with pytest.raises(O.NoOpticalHardwareError, match="acquires NOTHING"):
        dev.acquire(O.ReadoutKind.INTERFEROMETRIC, run_id="r", seed=0)


def test_real_device_blocked_receipt_is_preregistered():
    dev = O.OpticalRealDevice(O.OpticalConfig())
    rec = dev.blocked_receipt(O.ReadoutKind.INTERFEROMETRIC)
    assert rec["status"] == "BLOCKED"
    assert rec["physical_run"] == "PREREGISTERED_NOT_RUN"
    assert rec["acquired"] is False
    assert rec["measured_here"] == "nothing"


# --- the four modes are distinct -----------------------------------------

def test_four_modes_present_and_distinct():
    assert {m.value for m in O.OpticalMode} == {
        "REAL_DEVICE", "REPLAY_DEVICE", "SYNTHETIC_DEVICE",
        "FAULT_INJECTION_DEVICE"}


def test_replay_reads_back_recorded_trace():
    cfg = O.OpticalConfig()
    planted = 0.3 * cfg.unambiguous_displacement_m()
    trace = O.synthetic_interferogram(cfg, planted, seed=2)
    replay = O.OpticalReplayDevice(
        cfg, {O.ReadoutKind.INTERFEROMETRIC: trace})
    obs = replay.acquire(O.ReadoutKind.INTERFEROMETRIC, run_id="r", seed=0)
    assert obs.mode is O.OpticalMode.REPLAY_DEVICE
    assert np.array_equal(obs.samples, trace)
    assert abs(obs.value - planted) / abs(planted) < 1.0e-3


# --- every fault mode injects a distinct, recognisable pathology ---------

@pytest.mark.parametrize("fault", list(O.OpticalFault))
def test_every_fault_mode_alters_the_trace(fault):
    cfg = O.OpticalConfig()
    inner = O.OpticalSyntheticDevice(cfg)
    faulty = O.OpticalFaultInjectionDevice(inner, (fault,))
    planted = 0.3 * cfg.unambiguous_displacement_m()
    clean = inner.acquire(O.ReadoutKind.INTERFEROMETRIC, run_id="r", seed=4,
                          displacement_m=planted)
    bad = faulty.acquire(O.ReadoutKind.INTERFEROMETRIC, run_id="r", seed=4,
                         displacement_m=planted)
    assert bad.faults == (fault,)
    # the faulted trace differs from the clean one (nan-aware comparison)
    assert not np.array_equal(np.nan_to_num(bad.samples), clean.samples)


def test_fringe_washout_collapses_visibility():
    cfg = O.OpticalConfig()
    inner = O.OpticalSyntheticDevice(cfg)
    planted = 0.4 * cfg.unambiguous_displacement_m()
    faulty = O.OpticalFaultInjectionDevice(
        inner, (O.OpticalFault.FRINGE_WASHOUT,))
    clean = inner.acquire(O.ReadoutKind.INTERFEROMETRIC, run_id="r", seed=7,
                          displacement_m=planted)
    bad = faulty.acquire(O.ReadoutKind.INTERFEROMETRIC, run_id="r", seed=7,
                         displacement_m=planted)
    # the clean fringe recovers the displacement; the washed-out fringe has
    # its modulation (AC content / visibility) collapsed toward the DC level
    clean_err = abs(clean.value - planted) / abs(planted)
    assert clean_err < 1.0e-3
    assert bad.samples.std() < 0.1 * clean.samples.std()


def test_speckle_decorrelation_drops_correlation():
    field = O.synthetic_speckle_field(48, seed=0)
    assert O.speckle_correlation(field, field) == pytest.approx(1.0)
    low = O.decorrelate_speckle(field, 0.1, seed=1)
    high = O.decorrelate_speckle(field, 0.9, seed=1)
    assert O.speckle_correlation(field, high) < O.speckle_correlation(field, low)


def test_fault_injection_requires_a_fault():
    inner = O.OpticalSyntheticDevice(O.OpticalConfig())
    with pytest.raises(O.OpticalError, match="at least one"):
        O.OpticalFaultInjectionDevice(inner, ())


def test_optical_specific_faults_named():
    assert O.OPTICAL_SPECIFIC_FAULTS == {
        O.OpticalFault.FRINGE_WASHOUT, O.OpticalFault.SPECKLE_DECORRELATION}


# --- corrections are traceable -------------------------------------------

def test_dark_and_flat_corrections_are_traceable():
    x = np.array([2.0, 3.0, 4.0])
    corrected, dc = O.dark_correct(x, 1.0)
    assert dc.kind == "dark" and dc.removed == 1.0
    assert np.allclose(corrected, [1.0, 2.0, 3.0])
    flat, fc = O.flat_correct(corrected, 2.0)
    assert fc.kind == "flat" and fc.removed == 2.0
    assert np.allclose(flat, [0.5, 1.0, 1.5])


def test_reference_and_drift_corrections_are_traceable():
    ref = np.array([0.5, 0.5, 0.5])
    corrected, rc = O.reference_correct(np.array([1.0, 1.0, 1.0]), ref)
    assert rc.kind == "reference" and rc.removed == pytest.approx(0.5)
    assert np.allclose(corrected, [0.5, 0.5, 0.5])
    drift = np.linspace(0.0, 10.0, 100) + 3.0
    detrended, drc = O.drift_correct(drift)
    assert drc.kind == "drift" and drc.removed > 0.0
    assert np.allclose(detrended, 0.0, atol=1e-9)


def test_flat_correction_rejects_zero_gain():
    with pytest.raises(O.OpticalError, match="gain"):
        O.flat_correct(np.array([1.0]), 0.0)


# --- thermal load is a separate error-budget component -------------------

def test_thermal_load_is_a_distinct_budget_component():
    budget = O.build_error_budget(O.OpticalConfig())
    names = [c["name"] for c in budget["components"]]
    assert "thermal_load" in names
    assert "environment" in names
    assert names.count("thermal_load") == 1


def test_error_budget_combines_in_quadrature():
    comps = (("a", 3.0e-3), ("b", 4.0e-3))
    budget = O.build_error_budget(O.OpticalConfig(), components=comps)
    assert budget["combination_method"] == "root_sum_square"
    assert budget["combined_uncertainty"] == pytest.approx(5.0e-3)


def test_error_budget_conforms_to_schema():
    budget = O.build_error_budget(O.OpticalConfig())
    validate(instance=budget, schema=_schema("error_budget.schema.json"))


def test_observation_conforms_to_schema():
    cfg = O.OpticalConfig()
    planted = 0.3 * cfg.unambiguous_displacement_m()
    dev = O.OpticalSyntheticDevice(cfg)
    obs = dev.acquire(O.ReadoutKind.INTERFEROMETRIC, run_id="run1", seed=0,
                      displacement_m=planted)
    validate(instance=obs.as_observation_record(),
             schema=_schema("observation_record.schema.json"))


# --- bound to geometry and calibration, capped below physical ------------

def test_observation_is_bound_and_capped_below_physical():
    cfg = O.OpticalConfig()
    dev = O.OpticalSyntheticDevice(cfg)
    obs = dev.acquire(O.ReadoutKind.PHOTOELASTIC, run_id="r", seed=0,
                      retardation_rad=0.8)
    rec = obs.as_observation_record()
    assert rec["config"]["calibration_id"] == cfg.calibration_id
    assert rec["config"]["geometry_passes"] == cfg.geometry_passes
    # a synthetic observation is capped at E3, never a physical measurement
    assert obs.evidence_level() is claims.EvidenceLevel.E3
    assert obs.claim_class not in claims.MEASUREMENT_CLASSES


def test_observation_cannot_be_a_measurement_class():
    cfg = O.OpticalConfig()
    with pytest.raises(claims.ClaimError):
        O.OpticalObservation(
            observation_id="x", run_id="r", mode=O.OpticalMode.SYNTHETIC_DEVICE,
            readout=O.ReadoutKind.INTERFEROMETRIC, config=cfg,
            quantity="surface_displacement", value=0.0, units="m",
            uncertainty={}, samples=np.zeros(4), seed=0,
            claim_class=claims.ClaimClass.PHYSICAL_MEASUREMENT)


# --- refusals -------------------------------------------------------------

def test_refuse_reconstruction_as_measured_raises():
    with pytest.raises(O.OpticalError, match="SYNTHETIC_OBSERVATION"):
        O.refuse_reconstruction_as_measured()


def test_refuse_synthetic_as_physical_raises():
    with pytest.raises(O.OpticalError, match="PHYSICAL_VALIDATION_NOT_CLAIMED"):
        O.refuse_synthetic_as_physical()


# --- determinism ----------------------------------------------------------

def test_synthetic_same_seed_identical():
    cfg = O.OpticalConfig()
    a = O.synthetic_interferogram(cfg, 1.0e-8, seed=9)
    b = O.synthetic_interferogram(cfg, 1.0e-8, seed=9)
    assert np.array_equal(a, b)


def test_synthetic_different_seed_differs():
    cfg = O.OpticalConfig()
    a = O.synthetic_interferogram(cfg, 1.0e-8, seed=1)
    b = O.synthetic_interferogram(cfg, 1.0e-8, seed=2)
    assert not np.array_equal(a, b)


def test_fault_injection_is_deterministic():
    cfg = O.OpticalConfig()
    inner = O.OpticalSyntheticDevice(cfg)
    faulty = O.OpticalFaultInjectionDevice(
        inner, (O.OpticalFault.PACKET_LOSS, O.OpticalFault.DRIFT))
    a = faulty.acquire(O.ReadoutKind.INTERFEROMETRIC, run_id="r", seed=5,
                       displacement_m=1.0e-8)
    b = faulty.acquire(O.ReadoutKind.INTERFEROMETRIC, run_id="r", seed=5,
                       displacement_m=1.0e-8)
    assert np.array_equal(a.samples, b.samples)


def test_report_claims_nothing():
    rep = O.optical_report()
    assert rep["measured_here"] == "nothing"
    assert rep["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert rep["power_control_recovers_planted"] is True
    assert rep["verdict"] == O.VERDICT


def test_polarization_rosette_is_synthetic_angular_pattern():
    cfg = O.OpticalConfig()
    rosette = O.polarization_rosette(cfg, 1.0, n_analyzer=6)
    assert rosette.shape == (6,)
    assert np.all(rosette >= 0.0)
