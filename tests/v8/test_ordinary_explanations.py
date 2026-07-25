"""P11 — the ordinary-explanation firewall.

POWER: each planted ordinary artifact is caught by its own attack, and a
clean, genuine-looking residual survives every attack (the firewall is not
vacuous). Negative: a residual within the uncertainty budget is not
anomalous, and the UNEXPLAINED label is refused before the battery runs.
Determinism: identical inputs yield an identical record.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import numpy as np
import pytest

from r13 import daq
from r15 import claims
from r15 import ordinary_explanations as oe

FS = 4096.0
N = 4096
T = np.arange(N) / FS


def _rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)


def _tone(f: float, noise: float = 0.0, seed: int = 0) -> np.ndarray:
    x = np.sin(2 * np.pi * f * T)
    if noise:
        x = x + noise * _rng(seed).standard_normal(N)
    return x


def _full_context(**over) -> oe.AttackContext:
    """A fully-populated context so every attack is applicable; the clean
    signal must still survive all of them."""
    base = dict(
        sample_rate_hz=FS,
        combined_uncertainty=0.05,
        coverage_factor=2.0,
        timebase=T.copy(),
        calibration_reference={"drift_tol": 0.25},
        suspect_tone_hz=640.0,          # below Nyquist -> aliasing N/A
        environment=_rng(2).standard_normal(N),
        aggressor=_rng(3).standard_normal(N),
        fixture_reference=_rng(4).standard_normal(N),
        expected_feature_hz=640.0,
        specimen_tol_hz=5.0,
        model_prediction=np.zeros(N),
        model_fundamental_hz=300.0,
        residual_id="R11-fixture",
        observation_ids=("obs-a", "obs-b"),
    )
    base.update(over)
    return oe.AttackContext(**base)


def _clean_signal() -> np.ndarray:
    # on-bin, stationary, uncoupled tone above the budget: a deliberately
    # genuine-looking residual
    return _tone(640.0, noise=0.02, seed=1)


# --- vocabulary -----------------------------------------------------------

def test_there_are_eleven_attacks():
    assert len(oe.ATTACKS) == 11
    assert len(list(oe.AttackName)) == 11
    # every attack maps to an ordinary-explanation claim class, never a
    # measurement or the residual ceiling
    for name, cc in oe.ATTACK_CLAIM_CLASS.items():
        assert cc not in claims.MEASUREMENT_CLASSES
        assert cc is not claims.ClaimClass.UNEXPLAINED_INSTRUMENT_RESIDUAL


# --- POWER: the firewall is not vacuous -----------------------------------

def test_clean_residual_survives_every_attack():
    ctx = _full_context()
    fired = oe.run_all_attacks(_clean_signal(), ctx)
    assert fired == []
    res = oe.classify_residual(_clean_signal(), ctx)
    assert res.classification is \
        oe.ResidualClass.UNEXPLAINED_INSTRUMENT_RESIDUAL
    assert res.claim_class is claims.ClaimClass.UNEXPLAINED_INSTRUMENT_RESIDUAL


# --- POWER: each planted artifact is caught by its own attack -------------

def _planted():
    """(attack_name, signal, context) for one planted artifact each."""
    cases = []

    # raw-data defect: an injected NaN
    sig = _clean_signal().copy()
    sig[100] = np.nan
    cases.append((oe.AttackName.RAW_DATA_DEFECT, sig, _full_context()))

    # clock error: a jittered timebase
    tb = T.copy() + _rng(9).normal(0.0, 0.15 / FS, N)
    cases.append((oe.AttackName.CLOCK_ERROR, _clean_signal(),
                  _full_context(timebase=tb)))

    # calibration drift: a multiplicative gain ramp
    drift = _tone(640.0, 0.02, 11) * np.linspace(1.0, 1.7, N)
    cases.append((oe.AttackName.CALIBRATION_DRIFT, drift, _full_context()))

    # clipping: a hard rail
    cases.append((oe.AttackName.CLIPPING, np.clip(_tone(640.0), -0.5, 0.5),
                  _full_context()))

    # aliasing: a 3700 Hz tone folding to 396 Hz at fs=4096 (via r13.daq)
    aliased = daq.sample(lambda tt: np.sin(2 * np.pi * 3700.0 * tt),
                         FS, 1.0).values
    cases.append((oe.AttackName.ALIASING, aliased,
                  _full_context(suspect_tone_hz=3700.0)))

    # spectral leakage: an off-bin tone (640.5 cycles)
    leaky = np.sin(2 * np.pi * 640.5 * T) + 0.02 * _rng(5).standard_normal(N)
    cases.append((oe.AttackName.SPECTRAL_LEAKAGE, leaky, _full_context()))

    # environmental coupling: signal tracks the environment monitor
    env = _rng(2).standard_normal(N)
    cases.append((oe.AttackName.ENVIRONMENTAL_COUPLING,
                  _tone(640.0, 0.02, 12) + 0.9 * env,
                  _full_context(environment=env)))

    # cross-talk: an aggressor channel leaks in
    agg = _rng(3).standard_normal(N)
    cases.append((oe.AttackName.CROSS_TALK,
                  _tone(640.0, 0.02, 13) + 0.6 * agg,
                  _full_context(aggressor=agg)))

    # fixture effect: the feature is the blank fixture's own signature
    blank = _tone(512.0, 0.05, 6)
    cases.append((oe.AttackName.FIXTURE_EFFECT,
                  blank + 0.05 * _rng(7).standard_normal(N),
                  _full_context(fixture_reference=blank)))

    # specimen mismatch: dominant feature far from the declared band
    cases.append((oe.AttackName.SPECIMEN_MISMATCH, _tone(640.0, 0.02, 14),
                  _full_context(expected_feature_hz=1500.0,
                                specimen_tol_hz=10.0)))

    # model inadequacy: the 'anomaly' is the 2nd harmonic of the model f0
    cases.append((oe.AttackName.MODEL_INADEQUACY, _tone(600.0, 0.02, 15),
                  _full_context(model_prediction=np.zeros(N),
                                model_fundamental_hz=300.0)))
    return cases


@pytest.mark.parametrize("attack,sig,ctx", _planted(),
                         ids=[c[0].value for c in _planted()])
def test_planted_artifact_is_caught_by_its_attack(attack, sig, ctx):
    fired = {r.name for r in oe.run_all_attacks(sig, ctx)}
    assert attack in fired
    res = oe.classify_residual(sig, ctx)
    assert res.classification is oe.ResidualClass.ORDINARY_EXPLANATION_FOUND
    # an explained residual is never the unexplained ceiling
    assert res.claim_class is not \
        claims.ClaimClass.UNEXPLAINED_INSTRUMENT_RESIDUAL


# --- multiple faults coexist; no attack has exclusive authority -----------

def test_multiple_faults_coexist():
    env = _rng(2).standard_normal(N)
    # clipping AND environmental coupling in one signal
    sig = np.clip(_tone(640.0) + 0.9 * env, -0.5, 0.5)
    fired = {r.name for r in oe.run_all_attacks(sig, _full_context(
        environment=env))}
    assert oe.AttackName.CLIPPING in fired
    assert oe.AttackName.ENVIRONMENTAL_COUPLING in fired
    assert len(fired) >= 2


def test_no_attack_has_exclusive_authority():
    # each attack that fired would independently suffice: the verdict is a
    # union, so removing any one leaves the residual explained by another
    env = _rng(2).standard_normal(N)
    sig = np.clip(_tone(640.0) + 0.9 * env, -0.5, 0.5)
    ctx = _full_context(environment=env)
    fired = [r for r in oe.run_all_attacks(sig, ctx)]
    assert len(fired) >= 2
    for r in fired:
        # each fired attack, run in isolation, still fires on its own
        solo = oe.ATTACKS[r.name](sig, ctx)
        assert solo.explained


# --- failed / inapplicable explanations remain recorded -------------------

def test_failed_explanations_are_preserved():
    ctx = _full_context()
    res = oe.classify_residual(_clean_signal(), ctx)
    # every attack is recorded even though none fired
    assert len(res.battery) == 11
    recorded = {r.name for r in res.battery}
    assert recorded == set(oe.AttackName)
    assert all(not r.explained for r in res.battery)


def test_inapplicable_attacks_are_recorded_not_dropped():
    # a bare context leaves most attacks inapplicable; they must still be
    # present in the battery, marked not-applicable
    bare = oe.AttackContext(sample_rate_hz=FS, combined_uncertainty=0.0)
    res = oe.classify_residual(_clean_signal(), bare)
    assert len(res.battery) == 11
    inapplicable = [r for r in res.battery if not r.applicable]
    assert inapplicable  # e.g. clock, calibration, aliasing, coupling...
    for r in inapplicable:
        assert not r.explained


# --- negative: within the uncertainty budget is not anomalous -------------

def test_residual_within_uncertainty_is_not_anomalous():
    # same clean tone, but the budget now covers its amplitude
    ctx = _full_context(combined_uncertainty=1.0, coverage_factor=2.0)
    res = oe.classify_residual(_clean_signal(), ctx)
    assert res.classification is oe.ResidualClass.NOISE_WITHIN_UNCERTAINTY
    assert res.classification is not \
        oe.ResidualClass.UNEXPLAINED_INSTRUMENT_RESIDUAL


# --- refusal paths --------------------------------------------------------

def test_refuse_residual_before_attacks():
    with pytest.raises(oe.OrdinaryExplanationError):
        oe.refuse_residual_before_attacks([])
    with pytest.raises(oe.OrdinaryExplanationError):
        oe.refuse_residual_before_attacks(None)
    # a real battery does not raise
    battery = oe.run_battery(_clean_signal(), _full_context())
    oe.refuse_residual_before_attacks(battery)


def test_refuse_residual_as_new_physics():
    with pytest.raises(claims.ClaimError):
        oe.refuse_residual_as_new_physics()


def test_empty_signal_is_refused():
    with pytest.raises(oe.OrdinaryExplanationError):
        oe.run_battery(np.array([1.0]), _full_context())


# --- determinism ----------------------------------------------------------

def test_classification_is_deterministic():
    sig = _clean_signal()
    ctx = _full_context()
    a = oe.classify_residual(sig, ctx).as_record()
    b = oe.classify_residual(sig, ctx).as_record()
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


# --- record conforms to residual_record.schema.json -----------------------

def test_record_conforms_to_schema():
    jsonschema = pytest.importorskip("jsonschema")
    schema_path = (Path(__file__).resolve().parents[2] / "r15" / "schemas" /
                   "residual_record.schema.json")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    record = oe.classify_residual(_clean_signal(), _full_context()).as_record()
    jsonschema.validate(record, schema)
    for key in ("residual_id", "observation_ids",
                "ordinary_explanation_attacks", "combined_uncertainty",
                "classification", "reopening_test"):
        assert key in record


# --- report claims nothing ------------------------------------------------

def test_report_claims_nothing():
    r = oe.ordinary_explanations_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["n_attacks"] == 11
    assert r["residual_ceiling"] == "UNEXPLAINED_INSTRUMENT_RESIDUAL"
    assert r["claim_class"] == "SOFTWARE_IMPLEMENTED"
    assert r["verdict"] == oe.VERDICT
