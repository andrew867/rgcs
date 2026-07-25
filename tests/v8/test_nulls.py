"""P21 tests — the null-model registry.

Structure: POWER (every registered null detects a planted effect and stays
non-significant on pure noise, with a roughly uniform p-value distribution
under H0); the four required matched-null facts (equal temperament is not a
rational-ratio control; ISM bands are anthropogenic; p is never printed as
zero; unit conversion preserves relational conclusions); NEGATIVE / refusal
paths (a vacuous null is refused, absence-as-evidence is refused without
power, a circular null is refused); and DETERMINISM under seed.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from r15 import nulls as N
from r15.claims import ClaimError


# ---------------------------------------------------------------------------
# fixtures / helpers
# ---------------------------------------------------------------------------

def _noise_null() -> N.NullModel:
    return N.NullModel(
        name="noise_only", family=N.NullFamily.GENERIC,
        method=N.NullMethod.NOISE_ONLY,
        description="white noise at the data's amplitude scale",
        generator=N.noise_only_surrogate, derivation_family="noise")


def _permutation_null() -> N.NullModel:
    return N.NullModel(
        name="permutation", family=N.NullFamily.GENERIC,
        method=N.NullMethod.PERMUTATION,
        description="a shuffle preserving the marginal distribution",
        generator=N.permutation_surrogate, derivation_family="labels")


def _planted_tone(seed: int = 1) -> np.ndarray:
    rng = np.random.default_rng(seed)
    t = np.linspace(0.0, 1.0, 256)
    return np.sin(2 * np.pi * 7 * t) + 0.1 * rng.standard_normal(256)


def _planted_group_shift(seed: int = 1) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return (np.concatenate([np.zeros(64), 5.0 * np.ones(64)])
            + 0.5 * rng.standard_normal(128))


# ===========================================================================
# POWER — generic nulls detect planted effects, stay silent on noise
# ===========================================================================

def test_noise_null_detects_planted_tone():
    planted = _planted_tone()
    res = N.monte_carlo_p_value(N.spectral_peak_statistic, planted,
                                _noise_null(), n_trials=499, seed=11)
    assert res.significant
    assert res.p_value < 0.05


def test_noise_null_silent_on_pure_noise():
    noise = np.random.default_rng(2).standard_normal(256)
    res = N.monte_carlo_p_value(N.spectral_peak_statistic, noise,
                                _noise_null(), n_trials=499, seed=11)
    assert not res.significant


def test_permutation_null_has_power():
    planted = _planted_group_shift()
    noise = np.random.default_rng(3).standard_normal(128)
    pr = N.prove_power(_permutation_null(), N.group_mean_diff_statistic,
                       planted, noise, n_trials=499, seed=5)
    assert pr.detects_planted
    assert not pr.fires_on_noise
    assert pr.has_power


def test_noise_null_h0_p_values_are_uniform():
    pv = N.null_p_value_distribution(
        _noise_null(), N.spectral_peak_statistic,
        lambda rng: rng.standard_normal(128),
        n_datasets=60, n_trials=199, seed=7)
    report = N.p_values_are_uniform(pv)
    assert report["approximately_uniform"], report


def test_permutation_null_h0_p_values_are_uniform():
    pv = N.null_p_value_distribution(
        _permutation_null(), N.group_mean_diff_statistic,
        lambda rng: rng.standard_normal(128),
        n_datasets=60, n_trials=199, seed=13)
    report = N.p_values_are_uniform(pv)
    assert report["approximately_uniform"], report


# ===========================================================================
# POWER — the four matched-null families each prove power
# ===========================================================================

def test_representation_null_detects_rational_scale():
    planted = N.just_intonation_ratios()
    noise = N.span_matched_surrogate(np.random.default_rng(4), planted)
    pr = N.prove_power(N.REPRESENTATION_NULL, N.rationality_score,
                       planted, noise, n_trials=499, seed=17)
    assert pr.has_power


def test_design_null_detects_natural_line_not_ism():
    report = N.prove_design_power()
    assert report.planted_is_novel          # hydrogen line is novel
    assert not report.control_is_novel       # 2.45 GHz Wi-Fi band is not
    assert report.has_power


def test_relationship_null_certifies_invariant_rejects_artifact():
    report = N.prove_relationship_power()
    assert report.genuine_conclusion_invariant
    assert not report.artifact_conclusion_invariant
    assert report.has_power


def test_physics_null_detects_specimen_not_fixture():
    planted = N.planted_specimen_spectrum(np.random.default_rng(21))
    control = N.fixture_only_spectrum(np.random.default_rng(22))
    pr = N.prove_power(N.PHYSICS_NULL, N.specimen_window_peak_statistic,
                       planted, control, n_trials=499, seed=23)
    assert pr.detects_planted
    assert not pr.fires_on_noise
    assert pr.has_power


def test_default_registry_all_families_have_power():
    reg = N.build_default_registry()
    validation = N.validate_registry(reg)
    assert validation["all_have_power"]
    assert validation["all_non_circular"]
    assert validation["binding_count"] == 4
    assert set(validation["families_covered"]) == {
        "REPRESENTATION", "DESIGN", "RELATIONSHIP", "PHYSICS"}


# ===========================================================================
# REQUIRED FACTS
# ===========================================================================

def test_equal_temperament_is_not_a_rational_ratio_control():
    # the required test: equal temperament is not a rational-ratio control
    assert N.equal_temperament_is_rational_ratio_control() is False
    assert not N.is_rational_ratio_control(N.equal_temperament_ratios())
    # the genuine rational control passes
    assert N.is_rational_ratio_control(N.just_intonation_ratios())


def test_ism_bands_are_anthropogenic_structure():
    # the required test: ISM bands are anthropogenic structure
    assert N.is_anthropogenic_band(2.45e9)
    assert N.is_anthropogenic_band(13.56e6)
    # a natural spectral line is not an ISM allocation
    assert not N.is_anthropogenic_band(N.HYDROGEN_LINE_HZ)
    assert len(N.ism_bands()) >= 6


def test_p_value_is_never_printed_as_zero():
    # the required test: P is never printed as zero
    planted = _planted_tone()
    res = N.monte_carlo_p_value(N.spectral_peak_statistic, planted,
                                _noise_null(), n_trials=999, seed=31)
    assert res.p_value > 0.0
    assert res.p_value >= res.mc_resolution
    text = res.p_value_text
    assert text != "0"
    assert "0.0" != text
    # at the floor it is rendered as an upper bound, not a zero
    assert res.p_value == pytest.approx(res.mc_resolution) or "<" not in text
    floor_text = N.format_p_value(res.mc_resolution, res.mc_resolution)
    assert floor_text.startswith("<")


def test_unit_conversion_preserves_relational_conclusions():
    # the required test: unit conversion preserves relational conclusions
    freqs = np.array([120.0, 340.0, 55.0, 900.0])
    assert N.conclusion_invariant_under_units(freqs, (1.0, 1e-3, 1e-6, 1e3))
    # ordering identical under Hz -> kHz
    assert N.ordering_conclusion(freqs) == N.ordering_conclusion(freqs * 1e-3)
    # correlation sign invariant under positive rescaling
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y = np.array([2.0, 4.1, 5.9, 8.2, 9.8])
    assert N.correlation_sign(x, y) == N.correlation_sign(x * 1000.0, y * 3.28)


# ===========================================================================
# NEGATIVE / refusal paths
# ===========================================================================

def test_refuse_null_without_power_raises():
    with pytest.raises(N.NullError):
        N.refuse_null_without_power("dead_null")


def test_registry_refuses_a_null_without_power():
    reg = N.NullRegistry()
    with pytest.raises(N.NullError):
        reg.register("x", _noise_null(), effect_family="tone",
                     has_power=False)


def test_refuse_absence_as_evidence_raises():
    with pytest.raises(N.NullError):
        N.refuse_absence_as_evidence()


def test_guard_absence_claim_refuses_without_power():
    powerless = N.PowerReport(
        null_name="weak", p_on_planted=0.5, p_on_noise=0.5,
        detects_planted=False, fires_on_noise=False, has_power=False,
        alpha=0.05, mc_resolution=0.001)
    with pytest.raises(N.NullError):
        N.guard_absence_claim(powerless)


def test_bounded_absence_statement_only_after_power():
    powered = N.PowerReport(
        null_name="ok", p_on_planted=0.001, p_on_noise=0.4,
        detects_planted=True, fires_on_noise=False, has_power=True,
        alpha=0.05, mc_resolution=0.001)
    noise = np.random.default_rng(9).standard_normal(256)
    res = N.monte_carlo_p_value(N.spectral_peak_statistic, noise,
                                _noise_null(), n_trials=199, seed=9)
    assert not res.significant
    stmt = N.bounded_absence_statement(res, powered)
    assert "bounded" in stmt
    assert "not proven" in stmt


def test_refuse_p_value_zero_raises():
    with pytest.raises(N.NullError):
        N.refuse_p_value_zero()
    with pytest.raises(N.NullError):
        N.format_p_value(0.0, 0.001)


def test_registry_refuses_circular_null():
    circular = N.NullModel(
        name="circular", family=N.NullFamily.GENERIC,
        method=N.NullMethod.NOISE_ONLY, description="derived from the effect",
        generator=N.noise_only_surrogate, derivation_family="same_family")
    reg = N.NullRegistry()
    with pytest.raises(N.NullError):
        reg.register("m", circular, effect_family="same_family",
                     has_power=True)


def test_refuse_equal_temperament_as_rational_control_raises():
    with pytest.raises(N.NullError):
        N.refuse_equal_temperament_as_rational_control()


def test_refuse_flat_spectrum_null_for_ism_raises():
    with pytest.raises(N.NullError):
        N.refuse_flat_spectrum_null_for_ism()


def test_refuse_unit_dependent_conclusion_raises():
    with pytest.raises(N.NullError):
        N.refuse_unit_dependent_conclusion()


def test_refuse_fixture_response_as_signal_delegates_to_claims():
    # delegates to the governance core's noise-to-resonance refusal
    with pytest.raises(ClaimError):
        N.refuse_fixture_response_as_signal()


def test_negative_unit_conversion_factor_refused():
    with pytest.raises(N.NullError):
        N.conclusion_invariant_under_units(np.array([1.0, 2.0]), (-1.0,))


def test_malformed_null_model_refused():
    with pytest.raises(N.NullError):
        N.NullModel(name="", family=N.NullFamily.GENERIC,
                    method=N.NullMethod.NOISE_ONLY, description="d",
                    generator=N.noise_only_surrogate, derivation_family="f")
    with pytest.raises(N.NullError):
        N.NullModel(name="n", family=N.NullFamily.GENERIC,
                    method=N.NullMethod.NOISE_ONLY, description="d",
                    generator=N.noise_only_surrogate, derivation_family="")


# ===========================================================================
# surrogate properties
# ===========================================================================

def test_permutation_preserves_marginal_distribution():
    rng = np.random.default_rng(1)
    ref = rng.standard_normal(64)
    surr = N.permutation_surrogate(np.random.default_rng(2), ref)
    assert np.allclose(np.sort(ref), np.sort(surr))


def test_span_matched_stays_within_range():
    ref = np.array([3.0, 7.0, 5.0, 4.0])
    surr = N.span_matched_surrogate(np.random.default_rng(2), ref)
    assert surr.min() >= ref.min() - 1e-12
    assert surr.max() <= ref.max() + 1e-12


def test_phase_randomized_preserves_power_spectrum():
    rng = np.random.default_rng(1)
    x = np.cumsum(rng.standard_normal(256))
    surr = N.phase_randomized_surrogate(np.random.default_rng(9), x)
    ps_x = np.abs(np.fft.rfft(x - x.mean()))
    ps_s = np.abs(np.fft.rfft(surr - surr.mean()))
    assert np.max(np.abs(ps_x - ps_s)) < 1e-8 * ps_x.max()


# ===========================================================================
# DETERMINISM
# ===========================================================================

def test_monte_carlo_is_deterministic_under_seed():
    planted = _planted_tone()
    a = N.monte_carlo_p_value(N.spectral_peak_statistic, planted,
                              _noise_null(), n_trials=199, seed=42)
    b = N.monte_carlo_p_value(N.spectral_peak_statistic, planted,
                              _noise_null(), n_trials=199, seed=42)
    assert a.p_value == b.p_value
    assert a.statistic == b.statistic


def test_different_seed_gives_different_surrogates():
    ref = np.random.default_rng(0).standard_normal(64)
    s1 = N.noise_only_surrogate(np.random.default_rng(1), ref)
    s2 = N.noise_only_surrogate(np.random.default_rng(2), ref)
    assert not np.allclose(s1, s2)


def test_report_is_deterministic():
    a = N.nulls_report()
    b = N.nulls_report()
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


# ===========================================================================
# report claims nothing beyond software / synthetic
# ===========================================================================

def test_report_claims_nothing_measured():
    r = N.nulls_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["claim_cap"] == "SYNTHETIC_OBSERVATION"
    assert r["verdict"] == "NULL_MODEL_REGISTRY_POWER_PROVEN"
    assert r["registry_validation"]["all_have_power"]


def test_report_reports_mc_resolution_and_never_zero_p():
    r = N.nulls_report()
    mc = r["worked_monte_carlo"]
    assert mc["monte_carlo_resolution"] > 0.0
    assert mc["p_is_never_zero"]
    assert mc["p_value"] > 0.0


# ===========================================================================
# receipt conforms to the phase receipt schema
# ===========================================================================

def test_receipt_conforms_to_phase_receipt_schema():
    jsonschema = pytest.importorskip("jsonschema")
    root = Path(__file__).resolve().parents[2]
    receipt = json.loads(
        (root / "docs/v8/receipts/P21.json").read_text(encoding="utf-8"))
    schema = json.loads(
        (root / "r15/schemas/phase_receipt.schema.json").read_text(
            encoding="utf-8"))
    jsonschema.validate(receipt, schema)
    assert receipt["phase_id"] == "P21"
    assert receipt["status"] == "COMPLETE"
    assert receipt["blocked_reason"] is None
    assert receipt["commit"] is None
