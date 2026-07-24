"""P24 — synchronized data-acquisition model and energy ledger."""

from __future__ import annotations

import numpy as np
import pytest

from r13 import daq as D


# --- (1) sampling: below Nyquist recovered, above Nyquist aliases (POWER) --

def test_tone_below_nyquist_is_recovered():
    fs, dur, f = 1000.0, 1.0, 300.0        # Nyquist 500, so 300 is fine
    sig = D.sample(lambda t: np.cos(2 * np.pi * f * t), fs, dur)
    assert D.alias_frequency(f, fs) == pytest.approx(300.0)
    assert D.dominant_frequency(sig.values, fs) == pytest.approx(300.0)


def test_tone_above_nyquist_aliases_to_predicted_frequency():
    fs, dur = 1000.0, 1.0
    f = 700.0                              # above Nyquist -> folds to 300
    predicted = D.alias_frequency(f, fs)
    assert predicted == pytest.approx(300.0)
    sig = D.sample(lambda t: np.cos(2 * np.pi * f * t), fs, dur)
    assert D.dominant_frequency(sig.values, fs) == pytest.approx(predicted)


def test_alias_formula_folds_higher_orders():
    fs = 1000.0
    assert D.alias_frequency(1300.0, fs) == pytest.approx(300.0)
    assert D.alias_frequency(2300.0, fs) == pytest.approx(300.0)
    assert D.alias_frequency(50.0, fs) == pytest.approx(50.0)


def test_alias_test_can_fail_if_fold_ignored():
    # the aliased tone is NOT at its original frequency; this guards the
    # POWER test above from being vacuously true
    fs, dur, f = 1000.0, 1.0, 700.0
    sig = D.sample(lambda t: np.cos(2 * np.pi * f * t), fs, dur)
    assert D.dominant_frequency(sig.values, fs) != pytest.approx(700.0)


# --- (2) synchronization: skew detected and corrected to < 1 sample -------

def _pulse(n, center, width=6.0):
    idx = np.arange(n)
    return np.exp(-0.5 * ((idx - center) / width) ** 2)


def test_known_skew_is_detected_by_cross_correlation():
    n = 512
    base = _pulse(n, 200)
    for true_skew in (0, 7, 23, -15):
        channel = np.roll(base, true_skew)
        est = D.cross_correlation_lag(base, channel)
        assert abs(est - true_skew) <= 1


def test_common_event_lines_up_after_correction():
    n = 512
    base = _pulse(n, 200)
    skews = (0, 12, -9, 31)
    channels = [np.roll(base, s) for s in skews]
    estimated = D.estimate_skews(channels)
    result = D.synchronize(channels, estimated)
    peaks = [int(np.argmax(result.aligned[i])) for i in range(result.n_channels)]
    # every channel's event lands within one sample of the reference
    assert max(peaks) - min(peaks) <= 1


# --- (3) jitter: worse SNR monotonically ----------------------------------

def test_jitter_worsens_snr_monotonically():
    f, fs, dur = 200.0, 1000.0, 1.0
    sigmas = [0.0, 1e-4, 3e-4, 1e-3]
    snrs = [D.jitter_snr(f, fs, dur, s, n_realizations=24, seed=7)
            for s in sigmas]
    # strictly decreasing: more jitter, lower signal-to-noise
    for a, b in zip(snrs, snrs[1:]):
        assert a > b


# --- (4) energy ledger: closes exactly, dropped term is the residual ------

def test_synthetic_ledger_closes_exactly():
    result = D.synthetic_ledger()
    assert result["residual"] == 0.0
    assert result["closes"] is True
    assert result["e_in"] == D.SYNTHETIC_INPUT


def test_dropping_a_loss_term_leaves_that_exact_residual():
    dropped = D.synthetic_ledger(drop="e_dissipated")
    assert dropped["residual"] == D.SYNTHETIC_LEDGER["e_dissipated"]
    assert dropped["closes"] is False
    # and it is EXACT, not merely close
    assert dropped["residual"] == 3.0


def test_energy_ledger_reports_efficiency_and_rejects_bad_term():
    r = D.energy_ledger(10.0, e_out=6.0, e_dissipated=3.0, e_stored=1.0)
    assert r["efficiency"] == pytest.approx(0.6)
    assert r["closes"] is True
    with pytest.raises(D.DAQError):
        D.energy_ledger(10.0, drop="not_a_term")


def test_real_ledger_is_blocked():
    b = D.blocked_ledger()
    assert b["claim_class"] == "BLOCKED_MISSING_INPUT"
    assert b["measured_here"] == "nothing"


# --- (5) the refusals ------------------------------------------------------

def test_refuse_unclosed_as_new_energy_raises():
    with pytest.raises(D.DAQError):
        D.refuse_unclosed_as_new_energy(0.3, (-1.0, 1.0))


def test_refuse_synthetic_daq_as_acquired_raises():
    with pytest.raises(D.DAQError):
        D.refuse_synthetic_daq_as_acquired()


# --- (6) the report --------------------------------------------------------

def test_report_states_verdict_and_measures_nothing():
    r = D.daq_report()
    assert r["verdict"] == "SYNCHRONIZED_DAQ_ENERGY_LEDGER_MODEL"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["real_ledger_status"] == "BLOCKED_MISSING_INPUT"
    assert "what_this_does_not_say" in r
