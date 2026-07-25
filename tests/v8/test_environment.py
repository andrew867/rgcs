"""P03 -- the environmental ledger: nuisance channels, clock alignment, and
the quadrature error budget with its sub-budget refusal."""

from __future__ import annotations

import numpy as np
import pytest

from r15 import environment as E
from r15.claims import ClaimClass, EvidenceLevel


# a shared experiment clock: 200 samples at 10 Hz, timestamps passed in
def _clock(n: int = 200, fs: float = 10.0, t0: float = 1000.0) -> np.ndarray:
    return t0 + np.arange(n, dtype=float) / fs


# --- channels -------------------------------------------------------------

def test_channel_carries_units_uncertainty_and_a_verifying_hash():
    t = _clock()
    ch = E.synthetic_channel(E.EnvChannelKind.TEMPERATURE, t, seed=1,
                             mean=295.0, noise=0.02, uncertainty=0.05)
    assert ch.units == "K"
    assert ch.uncertainty == 0.05
    assert ch.n == t.size
    assert ch.verify_hash()
    assert ch.claim_class is ClaimClass.SYNTHETIC_OBSERVATION


def test_editing_a_trace_breaks_its_hash():
    t = _clock()
    ch = E.synthetic_channel(E.EnvChannelKind.PRESSURE, t, seed=2, mean=1e5)
    tampered = E.EnvChannel(kind=ch.kind, source=ch.source, t=ch.t,
                            values=np.asarray(ch.values) + 1.0,
                            units=ch.units, uncertainty=ch.uncertainty,
                            sample_hash=ch.sample_hash)
    assert not tampered.verify_hash()


def test_mismatched_trace_lengths_are_rejected():
    with pytest.raises(E.EnvLedgerError):
        E.EnvChannel.from_series(E.EnvChannelKind.HUMIDITY,
                                 [0.0, 1.0, 2.0], [1.0, 2.0])


def test_nonincreasing_timestamps_are_rejected():
    with pytest.raises(E.EnvLedgerError):
        E.EnvChannel.from_series(E.EnvChannelKind.HUMIDITY,
                                 [0.0, 0.0, 1.0], [1.0, 2.0, 3.0])


def test_negative_uncertainty_is_rejected():
    with pytest.raises(E.EnvLedgerError):
        E.EnvChannel.from_series(E.EnvChannelKind.TEMPERATURE,
                                 [0.0, 1.0], [295.0, 295.1], uncertainty=-1.0)


# --- determinism ----------------------------------------------------------

def test_synthetic_channels_are_deterministic_under_a_seed():
    t = _clock()
    a = E.synthetic_channel(E.EnvChannelKind.VIBRATION, t, seed=7, noise=0.1)
    b = E.synthetic_channel(E.EnvChannelKind.VIBRATION, t, seed=7, noise=0.1)
    c = E.synthetic_channel(E.EnvChannelKind.VIBRATION, t, seed=8, noise=0.1)
    assert a.sample_hash == b.sample_hash
    assert np.array_equal(a.values, b.values)
    assert a.sample_hash != c.sample_hash


def test_synthetic_ledger_is_reproducible():
    t = _clock()
    l1 = E.synthetic_ledger("run-A", t, seed=42)
    l2 = E.synthetic_ledger("run-A", t, seed=42)
    h1 = [ch.sample_hash for ch in l1.channels]
    h2 = [ch.sample_hash for ch in l2.channels]
    assert h1 == h2
    assert set(l1.kinds()) == set(E.EnvChannelKind)


# --- REQUIRED: synthetic drift appears in expected outputs ----------------

def test_synthetic_drift_appears_in_drift_rate():
    t = _clock(n=300, fs=10.0)
    # inject a known +0.5 K/s drift on temperature
    ch = E.synthetic_channel(E.EnvChannelKind.TEMPERATURE, t, seed=3,
                             mean=295.0, noise=1e-4, drift_rate=0.5)
    assert E.drift_rate(ch) == pytest.approx(0.5, abs=1e-2)


def test_drift_override_flows_through_the_ledger():
    t = _clock(n=300, fs=10.0)
    led = E.synthetic_ledger("run-drift", t, seed=5,
                             drift_overrides={E.EnvChannelKind.PRESSURE: 2.0})
    p = led.authoritative(E.EnvChannelKind.PRESSURE)
    assert E.drift_rate(p) == pytest.approx(2.0, abs=0.2)
    # a channel with no injected drift stays flat
    v = led.authoritative(E.EnvChannelKind.VIBRATION)
    assert abs(E.drift_rate(v)) < 0.1


# --- REQUIRED: clock misalignment is detected -----------------------------

def test_clock_misalignment_is_detected():
    t = _clock(t0=1000.0)
    aligned = E.synthetic_channel(E.EnvChannelKind.ACOUSTIC, t, seed=1)
    # a trace whose clock starts 5 s late
    late = E.synthetic_channel(E.EnvChannelKind.ACOUSTIC, t + 5.0, seed=1)
    assert E.is_clock_aligned(aligned, 1000.0, tol_s=0.5)
    assert not E.is_clock_aligned(late, 1000.0, tol_s=0.5)
    assert E.clock_offset_seconds(late, 1000.0) == pytest.approx(5.0)


def test_trace_lag_recovers_a_sample_shift():
    t = _clock()
    ref = E.synthetic_channel(E.EnvChannelKind.LINE_VOLTAGE, t, seed=9,
                              mean=120.0, noise=1.0)
    shifted_vals = np.roll(np.asarray(ref.values), 4)
    shifted = E.EnvChannel.from_series(E.EnvChannelKind.LINE_VOLTAGE, t,
                                       shifted_vals)
    assert E.trace_lag_samples(ref, shifted) == 4


def test_realign_moves_the_origin_to_the_experiment_clock():
    t = _clock(t0=1000.0)
    late = E.synthetic_channel(E.EnvChannelKind.EMI_RF, t + 5.0, seed=2)
    fixed = E.realign_to_clock(late, 1000.0)
    assert fixed.t0 == pytest.approx(1000.0)
    assert np.array_equal(fixed.values, late.values)


# --- REQUIRED: missing required environment invalidates the run -----------

def test_missing_required_channel_invalidates_the_run():
    t = _clock()
    # a ledger with only temperature, but the default required set has seven
    only_temp = E.EnvironmentLedger(
        run_id="run-thin", mode=E.EnvMode.SYNTHETIC, clock_t0=float(t[0]),
        channels=(E.synthetic_channel(E.EnvChannelKind.TEMPERATURE, t, seed=1),))
    res = E.check_completeness(only_temp, E.MissingDataPolicy.INVALIDATE)
    assert not res.valid
    assert E.EnvChannelKind.HUMIDITY in res.missing
    assert res.evidence is EvidenceLevel.E0


def test_missing_channel_caps_evidence_below_a_full_synthetic_ledger():
    t = _clock()
    full = E.synthetic_ledger("run-full", t, seed=1)
    full_res = E.check_completeness(full, E.MissingDataPolicy.INVALIDATE)
    assert full_res.valid
    assert full_res.evidence is E.MAX_ENV_EVIDENCE            # E2
    # DEGRADE keeps the run but caps evidence to E1 when a channel is missing
    thin = E.EnvironmentLedger(
        run_id="run-thin", mode=E.EnvMode.SYNTHETIC, clock_t0=float(t[0]),
        channels=(E.synthetic_channel(E.EnvChannelKind.TEMPERATURE, t, seed=1),))
    degraded = E.check_completeness(thin, E.MissingDataPolicy.DEGRADE)
    assert degraded.valid
    assert degraded.evidence.value < E.MAX_ENV_EVIDENCE.value


def test_evidence_never_reaches_physical_even_when_complete():
    t = _clock()
    full = E.synthetic_ledger("run-full", t, seed=1)
    res = E.check_completeness(full)
    assert res.evidence.value < EvidenceLevel.E4.value


# --- REQUIRED: manual declarations have lower authority than sensor -------

def test_manual_declaration_has_lower_authority_than_sensor():
    assert E.source_authority(E.EnvSource.MANUAL) < \
        E.source_authority(E.EnvSource.SENSOR)
    assert E.source_authority(E.EnvSource.SYNTHETIC) < \
        E.source_authority(E.EnvSource.SENSOR)


def test_authoritative_channel_prefers_the_sensor_trace():
    t = _clock()
    manual = E.EnvChannel.from_series(
        E.EnvChannelKind.TEMPERATURE, t, np.full(t.size, 294.0),
        source=E.EnvSource.MANUAL, uncertainty=2.0)
    sensor = E.EnvChannel.from_series(
        E.EnvChannelKind.TEMPERATURE, t, np.full(t.size, 295.0),
        source=E.EnvSource.SENSOR, uncertainty=0.05)
    led = E.EnvironmentLedger(
        run_id="run-conflict", mode=E.EnvMode.REPLAY, clock_t0=float(t[0]),
        channels=(manual, sensor))
    chosen = led.authoritative(E.EnvChannelKind.TEMPERATURE)
    assert chosen.source is E.EnvSource.SENSOR


def test_manual_note_typed_as_source_claim_not_observation():
    t = _clock()
    manual = E.EnvChannel.from_series(
        E.EnvChannelKind.HUMIDITY, t, np.full(t.size, 45.0),
        source=E.EnvSource.MANUAL)
    assert manual.claim_class is ClaimClass.SOURCE_CLAIM


def test_allow_manual_policy_lets_a_note_substitute():
    t = _clock()
    channels = []
    for k in E.DEFAULT_REQUIRED_KINDS:
        src = E.EnvSource.MANUAL if k is E.EnvChannelKind.EMI_RF \
            else E.EnvSource.SYNTHETIC
        channels.append(E.EnvChannel.from_series(k, t, np.zeros(t.size),
                                                 source=src))
    led = E.EnvironmentLedger(
        run_id="run-manual", mode=E.EnvMode.REPLAY, clock_t0=float(t[0]),
        channels=tuple(channels))
    res = E.check_completeness(led, E.MissingDataPolicy.ALLOW_MANUAL)
    assert res.valid
    assert E.EnvChannelKind.EMI_RF in res.manual_substitutions


# --- the error budget and the sub-budget refusal --------------------------

def _budget(components=None):
    comps = components or [
        E.ErrorComponent(E.BudgetComponent.INSTRUMENT_RESOLUTION, 3.0, "Hz"),
        E.ErrorComponent(E.BudgetComponent.CLOCK, 4.0, "Hz"),
    ]
    return E.build_error_budget("bud-1", "resonant_frequency", comps)


def test_error_budget_combines_in_quadrature_and_matches_schema_keys():
    b = _budget()
    # 3-4-5 right triangle: rss of 3 and 4 is exactly 5
    assert b["combined_uncertainty"] == pytest.approx(5.0)
    assert b["combination_method"] == E.QUADRATURE
    for key in ("budget_id", "quantity", "components", "combination_method",
                "combined_uncertainty", "coverage_factor"):
        assert key in b
    assert b["measured_here"] == "nothing"


def test_all_eleven_budget_components_exist():
    assert len(list(E.BudgetComponent)) == 11
    assert E.BudgetComponent.MODEL_RESIDUAL in E.BudgetComponent
    assert E.BudgetComponent.ENVIRONMENT in E.BudgetComponent


def test_duplicate_budget_component_is_rejected():
    with pytest.raises(E.EnvLedgerError):
        E.build_error_budget("bud-dup", "q", [
            E.ErrorComponent(E.BudgetComponent.CLOCK, 1.0, "Hz"),
            E.ErrorComponent(E.BudgetComponent.CLOCK, 2.0, "Hz"),
        ])


def test_environment_component_folds_channel_uncertainties():
    t = _clock()
    led = E.synthetic_ledger("run-b", t, seed=1)
    comp = E.environment_component(led, quantity_units="Hz")
    assert comp.component is E.BudgetComponent.ENVIRONMENT
    assert comp.sigma > 0.0


def test_residual_within_budget_is_not_anomalous():
    b = _budget()
    sigma = b["combined_uncertainty"]              # 5.0
    assert E.is_within_budget(4.0, sigma)          # below budget: not anomalous
    assert not E.is_within_budget(9.0, sigma)      # above budget


def test_refuse_subbudget_as_anomaly_always_raises():
    b = _budget()
    sigma = b["combined_uncertainty"]
    # a residual well inside the budget: refusing to call it an anomaly
    with pytest.raises(E.EnvLedgerError):
        E.refuse_subbudget_as_anomaly(1.0, sigma)
    # even an above-budget residual: this guard never manufactures a discovery
    with pytest.raises(E.EnvLedgerError):
        E.refuse_subbudget_as_anomaly(100.0, sigma)


# --- the other refusals and the report ------------------------------------

def test_manual_as_sensor_is_refused():
    with pytest.raises(E.EnvLedgerError):
        E.refuse_manual_as_sensor()


def test_synthetic_env_as_measured_is_refused():
    with pytest.raises(E.EnvLedgerError):
        E.refuse_synthetic_env_as_measured()


def test_every_forbidden_promotion_is_registered_and_raises():
    assert set(E.FORBIDDEN_PROMOTIONS) == {
        "subbudget_to_anomaly", "manual_to_sensor",
        "synthetic_env_to_measured"}


def test_real_mode_is_blocked():
    st = E.real_mode_status()
    assert st["status"] == E.BLOCKED_MISSING_INPUT
    assert st["measured_here"] == "nothing"


def test_report_claims_nothing():
    r = E.environment_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["verdict"] == E.VERDICT
    assert r["real_mode_status"] == E.BLOCKED_MISSING_INPUT
    assert r["synthetic_channel_class"] == "SYNTHETIC_OBSERVATION"
    # sensor outranks manual in the reported ordering
    assert r["sources_ranked"][0] == "sensor"
    assert r["sources_ranked"][-1] == "manual"


def test_nuisance_correlation_flags_a_shared_trend():
    t = _clock()
    ch = E.synthetic_channel(E.EnvChannelKind.TEMPERATURE, t, seed=1,
                             mean=295.0, noise=1e-6, drift_rate=1.0)
    # a signal that tracks the temperature drift correlates strongly
    signal = np.asarray(ch.values) * 2.0 + 3.0
    assert E.nuisance_correlation(ch, signal) == pytest.approx(1.0, abs=1e-6)
