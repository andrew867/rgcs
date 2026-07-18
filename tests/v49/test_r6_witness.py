"""P11 — metric-indexed witness memory.

The tests that matter most here are the refusals. A decay model that
happily reports proper time would pass every numerical test in this
file and still be the exact error R6 exists to prevent.
"""

from __future__ import annotations

import math

import pytest

from r6 import witness as W


def _payload(**kw) -> W.ProbabilisticPayload:
    base = dict(payload_id="P1", p0=[0.97, 0.01, 0.01, 0.01],
                prior=[0.25] * 4, t0=0.0, tau=100.0, beta=1.0)
    base.update(kw)
    return W.ProbabilisticPayload(**base)


# --- exact core -------------------------------------------------------

def test_exact_core_digest_is_stable_and_content_sensitive():
    a = W.ExactCore("ADDR", "hash", ("read",), ("origin",), ("cal1",))
    b = W.ExactCore("ADDR", "hash", ("read",), ("origin",), ("cal1",))
    c = W.ExactCore("ADDR2", "hash", ("read",), ("origin",), ("cal1",))
    assert a.digest() == b.digest()
    assert a.digest() != c.digest()


def test_exact_core_digest_is_deterministic_across_processes():
    """sha256 of sorted JSON — not Python hash() (R4 lesson 3)."""
    a = W.ExactCore("ADDR", "h", ("read",), ("o",), ("c",))
    assert a.digest() == \
        W.ExactCore("ADDR", "h", ("read",), ("o",), ("c",)).digest()
    assert len(a.digest()) == 64


# --- payload decay ----------------------------------------------------

def test_weight_starts_at_one_and_decreases():
    p = _payload()
    assert p.weight(0.0) == 1.0
    assert p.weight(-5.0) == 1.0
    assert p.weight(100.0) == pytest.approx(math.exp(-1.0))
    assert p.weight(1e6) < 1e-9


def test_state_relaxes_to_the_declared_prior_not_to_zero():
    p = _payload()
    late = p.state(1e6)
    for x, q in zip(late, p.prior):
        assert x == pytest.approx(q, abs=1e-9)


def test_state_is_always_a_probability_vector():
    p = _payload()
    for t in (0.0, 1.0, 50.0, 100.0, 1e4):
        s = p.state(t)
        assert sum(s) == pytest.approx(1.0)
        assert all(x >= 0 for x in s)


def test_informative_bits_decay_monotonically_to_zero():
    p = _payload()
    vals = [p.informative_bits(t) for t in (0, 10, 50, 100, 500, 5000)]
    assert all(a >= b - 1e-12 for a, b in zip(vals, vals[1:]))
    assert vals[0] > 1.0
    assert vals[-1] == pytest.approx(0.0, abs=1e-6)


def test_stretch_exponent_changes_the_shape():
    fast = _payload(beta=2.0)
    slow = _payload(beta=0.5)
    assert fast.weight(200.0) < slow.weight(200.0)


def test_payload_rejects_degenerate_configuration():
    with pytest.raises(ValueError):
        _payload(tau=0.0)
    with pytest.raises(ValueError):
        _payload(beta=-1.0)
    with pytest.raises(ValueError):
        _payload(p0=[1.0], prior=[1.0])
    with pytest.raises(ValueError):
        W.ProbabilisticPayload("P", [0.5, 0.5], [0.3, 0.3, 0.4],
                               0.0, 10.0)


def test_uncharacterized_causes_lists_all_twelve_by_default():
    p = _payload()
    assert len(p.uncharacterized_causes()) == 12
    assert not p.fully_characterized()


def test_fully_characterized_requires_every_ordinary_cause():
    p = _payload(characterized_causes=W.ORDINARY_DECAY_CAUSES[:-1])
    assert not p.fully_characterized()
    p2 = _payload(characterized_causes=W.ORDINARY_DECAY_CAUSES)
    assert p2.fully_characterized()


# --- the firewall -----------------------------------------------------

def test_proper_time_from_payload_is_refused():
    p = _payload()
    with pytest.raises(W.RefusedError) as e:
        W.infer_proper_time_from_payload(p)
    assert "DECAY_IS_PROPER_TIME" in str(e.value)


def test_proper_time_still_refused_when_fully_characterized():
    """Characterizing all twelve causes does not make it a clock."""
    p = _payload(characterized_causes=W.ORDINARY_DECAY_CAUSES)
    assert p.fully_characterized()
    with pytest.raises(W.RefusedError):
        W.infer_proper_time_from_payload(p)


def test_payload_is_never_a_clock():
    assert W.payload_is_a_clock(_payload()) is False
    assert W.payload_is_a_clock(
        _payload(characterized_causes=W.ORDINARY_DECAY_CAUSES)) is False


# --- clock witness ----------------------------------------------------

def test_caesium_reference_uses_the_si_definition():
    cs = W.caesium_reference()
    assert cs.nu0_hz == 9_192_631_770


def test_clock_requires_frequency_and_instability():
    with pytest.raises(ValueError):
        W.ClockWitness("W", 0.0, 1e-13)
    with pytest.raises(ValueError):
        W.ClockWitness("W", 1e9, 0.0)


def test_uncalibrated_clock_is_only_a_model():
    assert W.caesium_reference().evidence_class() == "CLOCK_MODEL"


def test_calibrated_clock_with_missing_channels_cannot_reach_comparison():
    cs = W.caesium_reference()
    cs.calibrated_against = "REF"
    assert cs.missing_channels()
    assert cs.evidence_class() == "CLOCK_CALIBRATED"


def test_full_channels_reach_comparison_only_then():
    cs = W.caesium_reference()
    cs.calibrated_against = "REF"
    cs.recorded_channels = W.NUISANCE_CHANNELS
    assert cs.evidence_class() == "CLOCK_COMPARISON"
    cs.independently_replicated = True
    assert cs.evidence_class() == "INDEPENDENTLY_REPLICATED_METROLOGY"


def test_phase_uncertainty_grows_with_averaging():
    cs = W.caesium_reference()
    assert cs.phase_uncertainty_rad(100.0) > cs.phase_uncertainty_rad(1.0)


# --- relativistic predictions ----------------------------------------

def test_gravitational_redshift_one_metre():
    """g*h/c^2 at 1 m is ~1.09e-16."""
    assert W.gravitational_redshift_frac(1.0) == \
        pytest.approx(1.09e-16, rel=0.02)


def test_velocity_dilation_is_negative():
    assert W.velocity_dilation_frac(100.0) < 0


def test_caesium_cannot_resolve_a_one_metre_height_difference():
    """The headline honest result: the platform matters.

    A 1e-13/sqrt(t) caesium beam averaged for a day reaches ~1e-15,
    still an order of magnitude above the 1.09e-16 shift.
    """
    a = W.caesium_reference("A")
    b = W.caesium_reference("B")
    a.calibrated_against = b.calibrated_against = "REF"
    a.recorded_channels = b.recorded_channels = W.NUISANCE_CHANNELS
    res = W.compare_witnesses(
        a, b, measured_frac_diff=0.0, averaging_s=86400.0,
        transfer_link_frac_uncertainty=1e-17,
        predicted_frac=W.gravitational_redshift_frac(1.0))
    assert res.status == "PREDICTION_BELOW_RESOLUTION"
    assert res.evidence_class == "CLOCK_COMPARISON"


def test_optical_clock_can_resolve_it():
    a = W.ClockWitness("OA", 4.29e14, 1e-16)
    b = W.ClockWitness("OB", 4.29e14, 1e-16)
    a.calibrated_against = b.calibrated_against = "REF"
    a.recorded_channels = b.recorded_channels = W.NUISANCE_CHANNELS
    pred = W.gravitational_redshift_frac(1.0)
    res = W.compare_witnesses(
        a, b, measured_frac_diff=pred, averaging_s=10_000.0,
        transfer_link_frac_uncertainty=1e-19, predicted_frac=pred)
    assert res.status == "RELATIVISTIC_SHIFT_CONSISTENT"
    assert res.consistent


def test_uncharacterized_clocks_cannot_test_a_resolvable_prediction():
    a = W.ClockWitness("OA", 4.29e14, 1e-16)
    b = W.ClockWitness("OB", 4.29e14, 1e-16)
    a.calibrated_against = b.calibrated_against = "REF"
    # channels deliberately not recorded
    pred = W.gravitational_redshift_frac(1.0)
    res = W.compare_witnesses(
        a, b, measured_frac_diff=pred, averaging_s=10_000.0,
        transfer_link_frac_uncertainty=1e-19, predicted_frac=pred)
    assert res.status == "PREDICTION_NOT_TESTED_UNCHARACTERIZED"
    assert res.evidence_class == "CLOCK_CALIBRATED"
    assert not res.consistent


def test_comparison_reports_missing_channels_by_name():
    a = W.caesium_reference("A")
    b = W.caesium_reference("B")
    a.calibrated_against = b.calibrated_against = "R"
    res = W.compare_witnesses(a, b, measured_frac_diff=0.0,
                              averaging_s=1.0,
                              transfer_link_frac_uncertainty=1e-15)
    assert any("nuisance channels unrecorded" in n for n in res.notes)


def test_evidence_class_always_on_the_ladder():
    a = W.caesium_reference("A")
    b = W.caesium_reference("B")
    res = W.compare_witnesses(a, b, measured_frac_diff=1e-14,
                              averaging_s=1.0,
                              transfer_link_frac_uncertainty=1e-15)
    assert res.evidence_class in W.WITNESS_CLASSES


# --- reconstruction ---------------------------------------------------

def test_fresh_payload_reconstructs_without_observations():
    r = W.reconstruct(_payload(), t=0.0)
    assert r.status == "DECAYED_STATE_REPORTED"
    assert r.information_gain_bits > 1.0


def test_fully_decayed_payload_refuses():
    r = W.reconstruct(_payload(), t=1e6)
    assert r.status == "UNIDENTIFIABLE"
    assert r.posterior is None
    assert "cannot restore information" in r.refusal_reason


def test_root_certificate_does_not_rescue_a_decayed_payload():
    """The information bound, stated as a test.

    A certificate attests provenance. It carries no information about
    the physical state and must not change the outcome.
    """
    without = W.reconstruct(_payload(), t=1e6)
    with_cert = W.reconstruct(_payload(), t=1e6,
                              root_certificate="ROOT-LOCK-1")
    assert without.status == with_cert.status == "UNIDENTIFIABLE"
    assert with_cert.posterior is None


def test_new_observation_can_rescue_a_decayed_payload():
    """Valid new observations may sharpen the posterior — that is the
    only thing that may."""
    r = W.reconstruct(_payload(), t=1e6,
                      observations=[[10.0, 1.0, 1.0, 1.0]])
    assert r.status == "RECONSTRUCTED"
    assert r.posterior[0] > 0.6
    assert r.information_gain_bits > 0


def test_impossible_observation_is_refused_not_normalized():
    r = W.reconstruct(_payload(), t=0.0,
                      observations=[[0.0, 0.0, 0.0, 0.0]])
    assert r.status == "UNIDENTIFIABLE"
    assert "zero likelihood" in r.refusal_reason


def test_reconstruction_rejects_wrong_alphabet():
    with pytest.raises(ValueError):
        W.reconstruct(_payload(), t=0.0, observations=[[1.0, 1.0]])


def test_reconstruction_rejects_negative_likelihood():
    with pytest.raises(ValueError):
        W.reconstruct(_payload(), t=0.0,
                      observations=[[1.0, -1.0, 1.0, 1.0]])


# --- tamper evidence --------------------------------------------------

def _record(i: int, prev: str | None) -> W.WitnessRecord:
    return W.WitnessRecord(
        record_id=f"R{i}",
        exact=W.ExactCore(f"ADDR{i}", "h", ("read",), ("o",), ("c",)),
        payload=_payload(payload_id=f"P{i}"),
        witness=W.caesium_reference(f"W{i}"),
        event_counter=i, prev_chain_hash=prev)


def _chain(n: int) -> list[W.WitnessRecord]:
    out: list[W.WitnessRecord] = []
    prev = None
    for i in range(n):
        r = _record(i, prev)
        out.append(r)
        prev = r.chain_hash()
    return out


def test_intact_chain_verifies():
    rep = W.verify_chain(_chain(5))
    assert rep["ok"] and rep["status"] == "VALID"


def test_broken_link_detected():
    c = _chain(5)
    c[3].prev_chain_hash = "0" * 64
    rep = W.verify_chain(c)
    assert not rep["ok"]
    assert rep["status"] == "TAMPER_EVIDENCE_FAILED"
    assert any("chain break" in p for p in rep["problems"])


def test_non_monotonic_counter_detected():
    c = _chain(5)
    c[3].event_counter = 1
    rep = W.verify_chain(c)
    assert not rep["ok"]
    assert any("not monotonic" in p for p in rep["problems"])


def test_mutating_the_exact_core_breaks_the_chain():
    c = _chain(4)
    c[1].exact = W.ExactCore("TAMPERED", "h", ("read",), ("o",), ("c",))
    rep = W.verify_chain(c)
    assert not rep["ok"]


def test_record_status_reports_payload_decay():
    r = _record(0, None)
    assert r.status(0.0) == "VALID"
    assert r.status(1e6) in ("PAYLOAD_DECAYING",
                             "CLOCK_CONFIDENCE_DECAYING")


def test_record_status_values_are_declared():
    r = _record(0, None)
    for t in (0.0, 10.0, 1e6):
        assert r.status(t) in W.RECORD_STATUSES
