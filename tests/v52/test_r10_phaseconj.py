"""P09 — phase-conjugate return, treated as ordinary DSP.

The real result (a reciprocal channel refocuses a phase-conjugated
return) is shown with power; every over-claim it invites — wrong
operation, wrong channel, folded-in time-of-flight, collapsed roles —
is refused.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from r10 import phaseconj as PC


# --- the analytic signal and the distinct operators --------------------

def test_analytic_signal_real_part_is_the_input():
    x = np.cos(2 * math.pi * 8 * np.arange(64) / 64)
    z = PC.analytic_signal(x)
    assert np.allclose(np.real(z), x, atol=1e-9)


def test_empty_signal_is_refused():
    with pytest.raises(ValueError):
        PC.analytic_signal(np.array([]))


def test_conjugate_signflip_timereverse_are_all_different():
    """(4) The mirror operations are genuinely distinct operations."""
    z = PC.make_pulse(64, seed=1)
    conj = PC.phase_conjugate(z)
    flip = PC.sign_invert(z)
    rev = PC.time_reverse(z)
    assert not np.allclose(conj, flip)
    assert not np.allclose(conj, rev)
    assert not np.allclose(flip, rev)


def test_mirror_is_conjugate_and_time_reverse():
    """The phase-conjugate mirror equals conj o time-reverse exactly."""
    z = PC.make_pulse(64, seed=2)
    mirror = PC.phase_conjugate_mirror(z)
    assert np.allclose(mirror, np.conj(PC.time_reverse(z)), atol=1e-9)


# --- (1) the real result, with power ------------------------------------

def test_reciprocal_conjugate_refocuses_and_others_do_not():
    """(1)+(4) Only the phase-conjugate mirror refocuses a reciprocal
    channel; identity, pointwise conjugate, time reverse and sign flip
    all fail."""
    r = PC.focusing_experiment(seed=1, null_trials=100)
    m = r["peak_to_rms"]
    base = r["base_peak_to_rms"]
    # the conjugate return recovers essentially the original crest factor
    assert m["reciprocal_conjugate"] == pytest.approx(base, rel=1e-6)
    assert r["refocus_exact"]
    # every wrong operation on the same reciprocal channel does not refocus
    for wrong in ("reciprocal_identity", "reciprocal_pointwise_conjugate",
                  "reciprocal_time_reverse", "reciprocal_sign_flip"):
        assert m[wrong] < 0.5 * base


def test_refocus_beats_the_random_return_null_with_power():
    """(7) The refocus is not an artifact of the metric: it sits far
    above a distribution of energy-matched random returns."""
    r = PC.focusing_experiment(seed=1, null_trials=200)
    assert r["refocus_z_over_null"] > 10.0
    assert r["peak_to_rms"]["reciprocal_conjugate"] > r["null_max"]
    assert r["verdict"] == "PHASE_CONJUGATE_BASELINE_VALID"
    assert r["measured_here"] == "nothing"


def test_a_nonreciprocal_channel_does_not_refocus():
    """(3) Reciprocity is the control: swap the return channel and the
    right operation buys nothing."""
    r = PC.focusing_experiment(seed=1, null_trials=50)
    m = r["peak_to_rms"]
    assert m["nonreciprocal_conjugate"] < 0.5 * m["reciprocal_conjugate"]


# --- (5) the causality firewall -----------------------------------------

def test_the_naive_buffer_cancels_the_delay_to_zero():
    """The trap: fold the propagation delay into the conjugated phase and
    the round-trip delay evaporates."""
    d = PC.naive_delay_cancellation(delay_samples=400)
    assert d["implied_round_trip_delay_samples"] == 0
    assert d["causal_delay_samples"] == 800


def test_a_return_before_the_round_trip_is_refused():
    with pytest.raises(PC.CausalityViolation):
        PC.refuse_superluminal_return(0.0, 800.0)


def test_an_honest_round_trip_books_the_full_delay():
    """(5) The refocused shape is real DSP; the timing is an external
    ledger conjugation cannot touch."""
    r = PC.causal_round_trip(delay_samples=400)
    assert r["arrives_no_earlier_than_causal"]
    assert r["arrival_samples"] == r["causal_delay_samples"] == 800
    # the buffer math alone would have delivered it at time zero
    assert r["buffer_math_would_give_samples"] == 0
    assert r["verdict"] == "CAUSAL_DELAY_REQUIRED"


def test_causal_budget_light_time():
    b = PC.CausalBudget(384_400_000.0, float(PC.SAMPLE_RATE_HZ))
    assert b.one_way_delay_s == pytest.approx(1.282, abs=0.01)
    assert b.round_trip_delay_s == pytest.approx(2.564, abs=0.02)


def test_negative_path_length_is_refused():
    with pytest.raises(ValueError):
        PC.CausalBudget(-1.0, 32768.0)


# --- (6) the roles, kept separate ---------------------------------------

def test_distinct_roles_may_not_be_collapsed_without_an_experiment():
    with pytest.raises(PC.RoleCollapse):
        PC.refuse_role_collapse(PC.Role.CARRIER, PC.Role.KEY)


def test_a_discriminating_experiment_licenses_merging():
    # same role is trivially fine; a named experiment licenses the rest
    PC.refuse_role_collapse(PC.Role.CARRIER, PC.Role.CARRIER)
    PC.refuse_role_collapse(PC.Role.CARRIER, PC.Role.KEY,
                            discriminating_experiment="a real bench test")


def test_the_local_oscillator_and_clock_are_free_parameters():
    assert PC.ROLE_FREQ_HZ[PC.Role.LOCAL_OSCILLATOR] is None
    assert PC.ROLE_FREQ_HZ[PC.Role.MESSAGE_CLOCK] is None
    assert PC.ROLE_FREQ_HZ[PC.Role.CARRIER] == PC.CARRIER_HZ


# --- the report ----------------------------------------------------------

def test_report_claims_no_measurement():
    r = PC.phaseconj_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["evidence_class"] == "DERIVED_MATHEMATICS"
