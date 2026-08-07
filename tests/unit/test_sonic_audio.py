"""Frequency Key Studio audio engine tests (plan pack 10_TESTS)."""
import numpy as np
import pytest

from rgcs_desktop.services.sonic_audio import (
    AudioError, apply_pan, binaural_pair, brown_noise, mix_layers, peak,
    pink_noise, read_wav_info, render_binaural, render_isochronic,
    render_monaural, rms, sine, surf_noise, white_noise, write_wav)


def test_binaural_pair_100_104_example():
    left, right = binaural_pair(102.0, 4.0)
    assert left == 100.0
    assert right == 104.0


def test_binaural_pair_925_schumann():
    left, right = binaural_pair(925.0, 7.83)
    assert round(right - left, 2) == 7.83
    assert round((left + right) / 2, 6) == 925.0


def test_binaural_pair_refuses_bad_input():
    with pytest.raises(AudioError):
        binaural_pair(0.0, 4.0)
    with pytest.raises(AudioError):
        binaural_pair(2.0, 10.0)      # beat too large for carrier


def test_sine_refuses_nyquist():
    with pytest.raises(AudioError):
        sine(30000.0, 1.0, 48000)


def test_render_binaural_is_stereo_and_different_channels():
    audio = render_binaural(102.0, 4.0, 0.5)
    assert audio.shape == (24000, 2)
    assert audio.dtype == np.float32
    assert not np.allclose(audio[:, 0], audio[:, 1])


def test_render_monaural_channels_identical():
    audio = render_monaural(102.0, 4.0, 0.5)
    assert np.array_equal(audio[:, 0], audio[:, 1])


def test_isochronic_gates_amplitude():
    audio = render_isochronic(200.0, 4.0, 0.5, 1.0)
    # mid-cycle off-portions must be near-silent
    envelope = np.abs(audio[:, 0])
    # sample the middle of an off window: cycle 0.25 s, off at ~0.19 s
    off_idx = int(0.19 * 48000)
    on_idx = int(0.05 * 48000)
    assert envelope[off_idx] < 0.05
    # window max: single samples can land on carrier zero-crossings
    assert envelope[on_idx:on_idx + 200].max() > 0.5
    with pytest.raises(AudioError):
        render_isochronic(200.0, 4.0, 1.5, 1.0)


def test_noise_deterministic_by_seed():
    a = pink_noise(0.25, seed=7)
    b = pink_noise(0.25, seed=7)
    c = pink_noise(0.25, seed=8)
    assert np.array_equal(a, b)
    assert not np.array_equal(a, c)
    for fn in (white_noise, brown_noise, surf_noise):
        assert fn(0.25, seed=1).shape == (12000,)


def test_pink_noise_spectrum_slopes_down():
    audio = pink_noise(2.0, seed=3).astype(np.float64)
    spectrum = np.abs(np.fft.rfft(audio)) ** 2
    freqs = np.fft.rfftfreq(len(audio), 1 / 48000)
    low = spectrum[(freqs > 50) & (freqs < 200)].mean()
    high = spectrum[(freqs > 5000) & (freqs < 20000)].mean()
    assert low > 10 * high      # 1/f: strongly tilted to low frequencies


def test_mixer_never_clips_and_reports_normalization():
    loud = np.ones((4800, 2), dtype=np.float32)
    audio, stats = mix_layers(
        [{"audio": loud, "gain_db": 0.0},
         {"audio": loud, "gain_db": 0.0}], 0.1)
    assert stats["normalized"] is True
    assert peak(audio) <= 0.95 + 1e-6
    quiet, stats2 = mix_layers([{"audio": 0.1 * loud, "gain_db": -6.0}],
                               0.1)
    assert stats2["normalized"] is False
    assert rms(quiet) > 0


def test_mixer_refuses_positive_gain():
    with pytest.raises(AudioError):
        mix_layers([{"audio": np.zeros((10, 2)), "gain_db": 3.0}], 0.1,
                   sample_rate=100)


def test_pan_moves_energy():
    audio = np.ones((100, 2), dtype=np.float32)
    left = apply_pan(audio, -1.0)
    assert rms(left[:, 0]) > 10 * rms(left[:, 1])
    with pytest.raises(AudioError):
        apply_pan(audio, 2.0)


def test_wav_roundtrip(tmp_path):
    audio = render_binaural(102.0, 4.0, 0.5)
    path = write_wav(tmp_path / "t.wav", audio)
    info = read_wav_info(path)
    assert info["channels"] == 2
    assert info["sample_rate"] == 48000
    assert info["sample_width"] == 2       # 16-bit PCM
    assert info["duration_s"] == pytest.approx(0.5, abs=1e-3)
