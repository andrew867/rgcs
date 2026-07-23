"""P13 — phase-conjugate return under EMI.

EMI is a control that must reduce the effect: additive interference is
not part of the reciprocal channel, so it does not refocus and the
metric degrades monotonically. Coherent averaging recovers incoherent
noise but not a coherent interferer, and reciprocity is still required.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from r10 import phaseconj as PC
from r10 import pcemi as P


# --- (1) synthesizing interference --------------------------------------

def test_interference_hits_the_requested_power_exactly():
    for kind in P.InterferenceKind:
        x = P.interference(4096, 1, kind, 3.5)
        assert float(np.mean(np.abs(x) ** 2)) == pytest.approx(3.5, rel=1e-9)


def test_zero_power_is_exactly_zero():
    x = P.interference(256, 1, P.InterferenceKind.BROADBAND, 0.0)
    assert np.all(x == 0)


def test_negative_power_is_refused():
    with pytest.raises(P.PcEmiError):
        P.interference(256, 1, P.InterferenceKind.BROADBAND, -1.0)


def test_the_three_kinds_are_genuinely_different():
    nb = P.interference(1024, 1, P.InterferenceKind.NARROWBAND, 1.0)
    bb = P.interference(1024, 1, P.InterferenceKind.BROADBAND, 1.0)
    im = P.interference(1024, 1, P.InterferenceKind.IMPULSIVE, 1.0)
    # narrowband concentrates in one spectral bin; broadband does not.
    nb_crest = P.peak_to_rms(np.fft.fft(nb))
    bb_crest = P.peak_to_rms(np.fft.fft(bb))
    assert nb_crest > 10 * bb_crest
    # impulsive is sparse in time: most samples are zero.
    assert np.mean(np.abs(im) > 0) < 0.05


def test_emi_spec_synthesizes_reproducibly():
    spec = P.EmiSpec(P.InterferenceKind.NARROWBAND, 2.0, seed=7)
    a = spec.synthesize(512)
    b = P.interference(512, 7, P.InterferenceKind.NARROWBAND, 2.0)
    assert np.allclose(a, b)


# --- (2) zero-EMI refocus matches the R10.7 clean refocus ---------------

def test_zero_emi_matches_the_phaseconj_clean_refocus():
    """At zero interference the round trip is identical to R10.7's."""
    n = 4096
    channel = PC.phase_screen(n, PC.SEED, strength=math.pi)
    pulse = PC.make_pulse(n, seed=PC.SEED)
    clean = PC.peak_to_rms(PC.round_trip(pulse, channel, channel,
                                         "phase_conjugate"))
    res = P.refocus_under_emi(pulse, channel, np.zeros(n, dtype=complex))
    assert res["peak_to_rms"] == pytest.approx(clean, rel=1e-12)
    assert math.isinf(res["snr"])


def test_interference_length_mismatch_is_refused():
    n = 256
    channel = PC.phase_screen(n, PC.SEED)
    pulse = PC.make_pulse(n, seed=PC.SEED)
    with pytest.raises(P.PcEmiError):
        P.refocus_under_emi(pulse, channel, np.zeros(n + 1, dtype=complex))


# --- (3) the headline: monotone degradation -----------------------------

def test_the_focusing_metric_degrades_monotonically_with_emi_power():
    d = P.degradation_curve(kind=P.InterferenceKind.BROADBAND)
    metrics = np.asarray(d["metrics"])
    # strictly non-increasing (small numerical tolerance).
    assert np.all(np.diff(metrics) <= 1e-9)
    assert d["monotone_decreasing"]
    # zero-EMI point equals the clean refocus; the last is far below it.
    assert metrics[0] == pytest.approx(d["clean_metric"], rel=1e-12)
    assert metrics[-1] < 0.25 * metrics[0]


def test_high_emi_approaches_the_random_return_null():
    d = P.degradation_curve(kind=P.InterferenceKind.BROADBAND)
    assert d["approaches_null"]
    assert d["metrics"][-1] < 2.0 * d["null_mean"]
    assert d["verdict"] == "EMI_DEGRADES_REFOCUS_MONOTONICALLY"


def test_degradation_holds_for_narrowband_and_impulsive_too():
    for kind in (P.InterferenceKind.NARROWBAND, P.InterferenceKind.IMPULSIVE):
        d = P.degradation_curve(kind=kind)
        assert np.all(np.diff(np.asarray(d["metrics"])) <= 1e-9)


# --- (4) the power of averaging, and its limit --------------------------

def test_incoherent_averaging_recovers_refocus_about_sqrt_n():
    """N incoherent records improve the received SNR by ~N (amplitude
    ~sqrt(N)), and the focusing metric rises."""
    g = P.averaging_gain(kind=P.InterferenceKind.BROADBAND, repeats=16)
    # power SNR gain ~ repeats
    assert g["incoherent_snr_gain"] == pytest.approx(16, rel=0.4)
    assert g["incoherent_metric_n"] > g["incoherent_metric_1"]


def test_a_coherent_interferer_is_not_averaged_away():
    g = P.averaging_gain(kind=P.InterferenceKind.NARROWBAND, repeats=16)
    # a coherent interferer is identical every repeat: no SNR gain at all.
    assert g["coherent_snr_gain"] == pytest.approx(1.0, abs=1e-9)
    assert g["coherent_metric_n"] == pytest.approx(g["coherent_metric_1"],
                                                   rel=1e-9)


def test_claiming_averaging_removes_a_coherent_interferer_is_refused():
    with pytest.raises(P.PcEmiError):
        P.refuse_average_away_coherent(coherent=True, repeats=64)
    # incoherent noise genuinely averages down: no refusal.
    P.refuse_average_away_coherent(coherent=False, repeats=64)


def test_bad_repeat_counts_are_refused():
    channel = PC.phase_screen(256, PC.SEED)
    pulse = PC.make_pulse(256, seed=PC.SEED)
    with pytest.raises(P.PcEmiError):
        P.coherent_average_refocus(pulse, channel,
                                   P.InterferenceKind.BROADBAND, 1.0, 0)


# --- (5) reciprocity is still required ----------------------------------

def test_a_nonreciprocal_channel_does_not_refocus_even_at_zero_emi():
    rc = P.reciprocity_control()
    assert rc["reciprocity_required"]
    assert rc["nonreciprocal_metric"] < 0.5 * rc["reciprocal_metric"]
    assert rc["verdict"] == "RECIPROCITY_REQUIRED"


# --- the report ----------------------------------------------------------

def test_report_claims_no_measurement():
    r = P.pcemi_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["evidence_class"] == "DERIVED_MATHEMATICS"
    assert r["verdict"] == "PHASE_CONJUGATE_UNDER_EMI_SOFTWARE_ONLY"
    assert "what_this_does_not_say" in r
