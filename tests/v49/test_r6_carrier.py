"""P06 — information-carrier transduction.

The load-bearing test in this file is
``test_semantic_test_is_zero_once_conditioned_on_the_waveform``. The
encoder works, so the marginal I(M;Y) is large and positive; the
apparatus responds to the waveform, so conditioning on the waveform
removes all of it. That gap is the semantic ceiling.
"""

from __future__ import annotations

import math
import random

import pytest

import r6
from r6 import carrier as C


# --- helpers ----------------------------------------------------------

def _bits(n: int, seed: int) -> tuple[int, ...]:
    rng = random.Random(seed)
    return tuple(rng.randint(0, 1) for _ in range(n))


def _wide_channel(sigma: float) -> C.Channel:
    """Effectively memoryless: alpha ~ 0.998, so no meaningful ISI."""
    return C.Channel(gain=1.0, bandwidth_hz=1e6, noise_sigma=sigma,
                     sample_rate_hz=1e6)


# --- encoder ----------------------------------------------------------

def test_all_three_schemes_are_supported():
    assert set(C.SCHEMES) == {"OOK", "BPSK", "FSK"}


@pytest.mark.parametrize("scheme", ["OOK", "BPSK", "FSK"])
def test_encode_decode_round_trip(scheme):
    bits = _bits(64, seed=7)
    symbols = C.encode(bits, scheme)
    assert len(symbols) == len(bits)
    assert C.decode(symbols, scheme) == bits


@pytest.mark.parametrize("scheme", ["OOK", "BPSK", "FSK"])
def test_encode_is_deterministic(scheme):
    bits = "01101001"
    assert C.encode(bits, scheme) == C.encode(bits, scheme)
    assert C.encode(bits, scheme) == C.encode([0, 1, 1, 0, 1, 0, 0, 1],
                                              scheme)


def test_encode_rejects_non_binary_input():
    with pytest.raises(ValueError):
        C.encode("0102", "BPSK")
    with pytest.raises(ValueError):
        C.encode([0, 1, 2], "BPSK")


def test_encode_rejects_an_unknown_scheme():
    with pytest.raises(ValueError, match="unknown scheme"):
        C.encode([0, 1], "QAM64")


def test_fsk_symbols_are_frequency_offsets_not_amplitudes():
    assert "Hz" in C.SYMBOL_UNITS["FSK"]
    assert C.CONSTELLATIONS["FSK"] != C.CONSTELLATIONS["BPSK"]


# --- channel ----------------------------------------------------------

def test_channel_validates_its_parameters():
    with pytest.raises(ValueError):
        C.Channel(gain=0.0)
    with pytest.raises(ValueError):
        C.Channel(noise_sigma=-1.0)
    with pytest.raises(ValueError):
        C.Channel(delay_samples=-1)
    with pytest.raises(ValueError):
        C.Channel(bandwidth_hz=0.0)


def test_transmit_is_deterministic_given_the_seed():
    x = C.encode(_bits(32, seed=3), "BPSK")
    ch = _wide_channel(0.3)
    assert C.transmit(x, ch, seed=11) == C.transmit(x, ch, seed=11)
    assert C.transmit(x, ch, seed=11) != C.transmit(x, ch, seed=12)


def test_transmit_applies_the_declared_delay():
    x = (1.0, 1.0, 1.0, 1.0)
    ch = C.Channel(bandwidth_hz=1e6, sample_rate_hz=1e6, delay_samples=2)
    y = C.transmit(x, ch, seed=1)
    assert len(y) == len(x)
    assert abs(y[0]) < 1e-9


def test_noiseless_wide_channel_round_trips():
    bits = _bits(200, seed=5)
    ch = _wide_channel(0.0)
    x = C.encode(bits, "BPSK")
    y = C.transmit(x, ch, seed=1)
    assert C.symbol_error_rate(x, C.receive(y, ch, "BPSK")) == 0.0


# --- symbol error ------------------------------------------------------

def test_symbol_error_rate_increases_with_noise():
    bits = _bits(400, seed=17)
    x = C.encode(bits, "BPSK")
    rates = []
    for sigma in (0.0, 0.4, 0.8, 1.6):
        ch = _wide_channel(sigma)
        y = C.transmit(x, ch, seed=99)
        rates.append(C.symbol_error_rate(x, C.receive(y, ch, "BPSK")))
    assert rates[0] == 0.0
    assert rates == sorted(rates)
    assert rates[-1] > rates[0]
    assert 0.0 <= rates[-1] <= 1.0


def test_symbol_error_rate_rejects_a_length_mismatch():
    with pytest.raises(ValueError, match="length mismatch"):
        C.symbol_error_rate((1.0, 1.0), (1.0,))


def test_symbol_error_rate_rejects_an_empty_sequence():
    with pytest.raises(ValueError):
        C.symbol_error_rate((), ())


# --- mutual information -------------------------------------------------

def test_mutual_information_never_exceeds_the_source_entropy():
    bits = _bits(300, seed=23)
    x = C.encode(bits, "BPSK")
    for sigma in (0.0, 0.5, 1.0, 2.0):
        ch = _wide_channel(sigma)
        y = C.receive(C.transmit(x, ch, seed=41), ch, "BPSK")
        for corr in ("none", "miller_madow"):
            mi = C.mutual_information_bits(x, y, correction=corr)
            assert -1e-12 <= mi <= C.entropy_bits(x) + 1e-12
            assert mi <= C.entropy_bits(x, correction=corr) + 1e-12
            # Clamped at min(H(X), H(Y)), so a binary source can never
            # report more than one bit per symbol however the
            # correction behaves.
            assert mi <= 1.0 + 1e-12


def test_mutual_information_falls_as_noise_rises():
    bits = _bits(400, seed=29)
    x = C.encode(bits, "BPSK")
    mis = []
    for sigma in (0.1, 1.0, 4.0):
        ch = _wide_channel(sigma)
        y = C.receive(C.transmit(x, ch, seed=53), ch, "BPSK")
        mis.append(C.mutual_information_bits(x, y))
    assert mis == sorted(mis, reverse=True)


def test_mi_bias_direction_is_documented_and_the_correction_reduces_it():
    doc = C.mutual_information_bits.__doc__
    assert "biased **UPWARD**" in doc
    assert "permutation null" in doc
    assert "Miller-Madow" in doc

    # Independent sequences: the plug-in estimate is positive anyway,
    # which is the bias, and the correction pulls it down.
    rng = random.Random(101)
    a = tuple(rng.randint(0, 3) for _ in range(40))
    b = tuple(rng.randint(0, 3) for _ in range(40))
    plugin = C.mutual_information_bits(a, b, correction="none")
    corrected = C.mutual_information_bits(a, b, correction="miller_madow")
    assert plugin > 0.0
    assert corrected <= plugin


def test_mutual_information_rejects_bad_input():
    with pytest.raises(ValueError, match="length mismatch"):
        C.mutual_information_bits((1, 2), (1,))
    with pytest.raises(ValueError):
        C.mutual_information_bits((), ())
    with pytest.raises(ValueError, match="unknown correction"):
        C.entropy_bits((1, 2), correction="jackknife")


# --- capacity -----------------------------------------------------------

def test_capacity_bound_matches_the_shannon_formula():
    ch = C.Channel(gain=2.0, bandwidth_hz=1e5, noise_sigma=0.5,
                   sample_rate_hz=1e6)
    snr = (2.0 ** 2) * 1.0 / (0.5 ** 2)
    assert C.capacity_bound(ch) == pytest.approx(1e5 * math.log2(1 + snr))


def test_capacity_bound_falls_with_noise_and_is_nyquist_capped():
    caps = [C.capacity_bound(_wide_channel(s)) for s in (0.1, 1.0, 10.0)]
    assert caps == sorted(caps, reverse=True)
    ch = C.Channel(bandwidth_hz=1e9, sample_rate_hz=1e6, noise_sigma=1.0)
    assert ch.effective_bandwidth_hz() == 5e5


def test_capacity_bound_refuses_a_noiseless_channel():
    with pytest.raises(ValueError, match="unbounded capacity"):
        C.capacity_bound(_wide_channel(0.0))


def test_measured_throughput_can_be_checked_against_capacity():
    """The point of having the bound: a rate above C is a modeling
    error, not a transmission."""
    ch = _wide_channel(1.0)
    cap = C.capacity_bound(ch)
    bits = _bits(400, seed=31)
    x = C.encode(bits, "BPSK")
    y = C.receive(C.transmit(x, ch, seed=61), ch, "BPSK")
    mi_per_symbol = C.mutual_information_bits(x, y)
    achieved_bits_per_second = mi_per_symbol * ch.sample_rate_hz
    assert achieved_bits_per_second <= cap


# --- the semantic ceiling ------------------------------------------------

def _matched_waveform_design(n_per_cell: int = 12):
    """Two messages share each waveform; the output follows the
    waveform only. This is the physically ordinary situation."""
    messages, waveforms, observations = [], [], []
    for wf in ("WF-A", "WF-B"):
        for k in range(n_per_cell):
            messages.append("M0" if k % 2 == 0 else "M1")
            waveforms.append(wf)
            observations.append("Y-A" if wf == "WF-A" else "Y-B")
    return messages, waveforms, observations


def _semantic_design(n_per_cell: int = 12):
    """Same waveform, but the output tracks the message anyway — the
    only pattern that could ever support the claim."""
    messages, waveforms, observations = [], [], []
    for wf in ("WF-A", "WF-B"):
        for k in range(n_per_cell):
            m = "M0" if k % 2 == 0 else "M1"
            messages.append(m)
            waveforms.append(wf)
            observations.append("Y0" if m == "M0" else "Y1")
    return messages, waveforms, observations


def test_semantic_test_is_zero_once_conditioned_on_the_waveform():
    m, x, y = _matched_waveform_design()
    res = C.semantic_information_test(m, x, y, n_permutations=200)
    assert res.mi_marginal_bits >= 0.0
    assert res.mi_conditional_bits == pytest.approx(0.0, abs=1e-9)
    assert res.status == "NO_SEMANTIC_INFORMATION_ABOVE_WAVEFORM"
    assert res.evidence_class == "ORDINARY_CHANNEL_RESULT"
    assert res.n_informative_strata == 2


def test_large_marginal_mi_collapses_to_zero_under_conditioning():
    """The headline case. The message is *mostly* predictive of the
    waveform, so the marginal I(M;Y) is substantial and would be
    quoted as evidence. Conditioning on the waveform removes all of
    it: the apparatus responded to the carrier, not to the meaning."""
    messages, waveforms, observations = [], [], []
    for wf, n_m0 in (("WF-A", 11), ("WF-B", 1)):
        for k in range(12):
            messages.append("M0" if k < n_m0 else "M1")
            waveforms.append(wf)
            observations.append("Y-A" if wf == "WF-A" else "Y-B")
    res = C.semantic_information_test(
        messages, waveforms, observations, n_permutations=200)
    assert res.mi_marginal_bits > 0.4          # looks like a result
    assert res.mi_conditional_bits == pytest.approx(0.0, abs=1e-9)
    assert res.p_value == 1.0
    assert res.status == "NO_SEMANTIC_INFORMATION_ABOVE_WAVEFORM"
    assert res.n_informative_strata == 2


def test_identical_waveforms_make_apparent_marginal_mi_an_artifact():
    """Two messages, one waveform, output driven by the waveform. The
    marginal MI is an artifact and the conditional MI says so."""
    m = ["M0", "M1"] * 12
    x = ["WF-A"] * 24
    y = ["Y-A"] * 24
    res = C.semantic_information_test(m, x, y, n_permutations=100)
    assert res.mi_conditional_bits == pytest.approx(0.0, abs=1e-9)
    assert res.status == "NO_SEMANTIC_INFORMATION_ABOVE_WAVEFORM"


def test_permutation_null_p_value_is_always_in_the_unit_interval():
    for design in (_matched_waveform_design(), _semantic_design()):
        for seed in (1, 20260718, 999):
            res = C.semantic_information_test(
                *design, n_permutations=50, seed=seed,
                blinded_labels=True, held_out_decoding=True,
                independent_replication=True)
            assert 0.0 <= res.p_value <= 1.0
            assert res.p_value > 0.0     # add-one, never exactly zero


def test_semantic_test_is_deterministic_given_its_seed():
    d = _semantic_design()
    a = C.semantic_information_test(*d, n_permutations=100, seed=5)
    b = C.semantic_information_test(*d, n_permutations=100, seed=5)
    assert a.p_value == b.p_value
    assert a.mi_conditional_bits == b.mi_conditional_bits


def test_degenerate_design_is_named_rather_than_reported_as_a_null():
    """Every message has its own waveform, so there is no power at all
    and the test must not pretend it found nothing."""
    m = ["M0", "M1", "M2", "M3"]
    x = ["WF-0", "WF-1", "WF-2", "WF-3"]
    y = ["Y0", "Y1", "Y2", "Y3"]
    res = C.semantic_information_test(m, x, y, n_permutations=50)
    assert res.status == "DESIGN_DEGENERATE_NO_POWER"
    assert res.mi_conditional_bits == 0.0
    assert res.p_value == 1.0
    assert res.n_informative_strata == 0
    assert any("no power" in n for n in res.notes)


def test_semantic_effect_requires_blinding_holdout_and_replication():
    d = _semantic_design()
    res = C.semantic_information_test(*d, n_permutations=200, seed=3)
    assert res.mi_conditional_bits > 0.0
    assert res.p_value <= 0.05
    assert res.status == "PRECONDITIONS_NOT_MET"
    assert res.evidence_class == "ORDINARY_CHANNEL_RESULT"

    for missing in ("blinded_labels", "held_out_decoding",
                    "independent_replication"):
        kw = {k: True for k in C.SEMANTIC_PRECONDITIONS}
        kw[missing] = False
        partial = C.semantic_information_test(
            *d, n_permutations=200, seed=3, **kw)
        assert partial.status == "PRECONDITIONS_NOT_MET"


def test_strongest_available_outcome_is_not_excluded_not_detected():
    d = _semantic_design()
    res = C.semantic_information_test(
        *d, n_permutations=200, seed=3,
        blinded_labels=True, held_out_decoding=True,
        independent_replication=True)
    assert res.status == "SEMANTIC_EFFECT_NOT_EXCLUDED"
    assert res.evidence_class == "UNEXPLAINED_INSTRUMENT_RESIDUAL"
    assert res.evidence_class in r6.PHRYLL_CLASSES
    assert "NOT EXCLUDED" in " ".join(res.notes)
    record = res.as_record()
    assert "not a detection" in record["ceiling"]


def test_semantic_statuses_contain_no_detection_state():
    for status in C.SEMANTIC_STATUSES:
        assert status not in r6.FORBIDDEN_STATES
        assert "DETECT" not in status.upper()


def test_semantic_test_validates_its_inputs():
    with pytest.raises(ValueError, match="equal length"):
        C.semantic_information_test(["a", "b"], ["x"], ["y", "z"])
    with pytest.raises(ValueError, match="at least two trials"):
        C.semantic_information_test(["a"], ["x"], ["y"])
    with pytest.raises(ValueError, match="at least one permutation"):
        C.semantic_information_test(*_semantic_design(), n_permutations=0)
    with pytest.raises(ValueError):
        C.semantic_information_test(*_semantic_design(), alpha=1.0)


# --- the refusal ------------------------------------------------------------

def test_intention_experiment_is_refused():
    with pytest.raises(C.RefusedError) as exc:
        C.refuse_intention_experiment(subject="S01", trials=100)
    msg = str(exc.value)
    assert "no human intention" in msg
    assert "later-stage only" in msg
    for ch in C.EEG_NUISANCE_CHANNELS:
        assert ch in msg


def test_eeg_nuisance_channels_match_the_contract():
    assert set(C.EEG_NUISANCE_CHANNELS) == {
        "EOG", "EMG", "ECG", "respiration", "microphone",
        "accelerometer", "temperature", "motion", "timing",
        "experimenter_cues"}


def test_eeg_carrier_alias_also_refuses():
    with pytest.raises(C.RefusedError):
        C.refuse_eeg_carrier()


def test_module_states_it_is_not_bench_data():
    assert "nothing here is bench data" in C.__doc__.lower()
    assert "not bench data" in C.semantic_information_test.__doc__.lower()
    assert "no apparatus has been characterized" in C.Channel.__doc__.lower()
