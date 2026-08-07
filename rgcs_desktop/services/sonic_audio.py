"""Frequency Key Studio audio engine (Qt-free, numpy).

Defaults per the plan pack: 48 kHz sample rate, float32 internally,
16-bit PCM WAV export, deterministic seeds for noise. The mixer never
clips: if the mixed peak exceeds 0.95 the mix is normalized down and
the receipt records it.

Binaural convention (PAT-US5213562A vocabulary): a carrier and a beat
give left = carrier - beat/2, right = carrier + beat/2, so 102 Hz with
a 4 Hz beat yields the patent's 100/104 Hz example.
"""
from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

DEFAULT_SAMPLE_RATE = 48000
#: mixed audio above this peak is normalized down (never clipped)
PEAK_CEILING = 0.95


class AudioError(ValueError):
    """A refused audio parameter (with the reason)."""


# ------------------------------------------------------------- helpers

def _n_samples(duration_s: float, sample_rate: int) -> int:
    if duration_s <= 0:
        raise AudioError(f"duration must be > 0, got {duration_s}")
    if sample_rate < 8000:
        raise AudioError(f"sample rate too low: {sample_rate}")
    return int(round(duration_s * sample_rate))


def _time(duration_s: float, sample_rate: int) -> np.ndarray:
    n = _n_samples(duration_s, sample_rate)
    return np.arange(n, dtype=np.float64) / sample_rate


def peak(audio: np.ndarray) -> float:
    return float(np.max(np.abs(audio))) if audio.size else 0.0


def rms(audio: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(audio, dtype=np.float64)))) \
        if audio.size else 0.0


def db_to_gain(gain_db: float) -> float:
    return float(10.0 ** (gain_db / 20.0))


# ---------------------------------------------------------- generators

def sine(freq_hz: float, duration_s: float,
         sample_rate: int = DEFAULT_SAMPLE_RATE,
         phase: float = 0.0) -> np.ndarray:
    if freq_hz <= 0:
        raise AudioError(f"frequency must be > 0, got {freq_hz}")
    if freq_hz >= sample_rate / 2:
        raise AudioError(f"{freq_hz} Hz is at/above Nyquist for "
                         f"{sample_rate} Hz")
    t = _time(duration_s, sample_rate)
    return np.sin(2 * np.pi * freq_hz * t + phase).astype(np.float32)


def binaural_pair(carrier_hz: float, beat_hz: float) -> tuple[float, float]:
    """left/right frequencies for a binaural pair.

    carrier 102, beat 4 -> (100.0, 104.0) — the patent example.
    """
    if carrier_hz <= 0:
        raise AudioError("carrier must be > 0")
    if beat_hz < 0:
        raise AudioError("beat must be >= 0")
    if beat_hz / 2 >= carrier_hz:
        raise AudioError(f"beat {beat_hz} Hz too large for carrier "
                         f"{carrier_hz} Hz")
    return carrier_hz - beat_hz / 2.0, carrier_hz + beat_hz / 2.0


def render_binaural(carrier_hz: float, beat_hz: float, duration_s: float,
                    sample_rate: int = DEFAULT_SAMPLE_RATE) -> np.ndarray:
    """Stereo (n, 2) float32: left/right sine pair."""
    left_hz, right_hz = binaural_pair(carrier_hz, beat_hz)
    left = sine(left_hz, duration_s, sample_rate)
    right = sine(right_hz, duration_s, sample_rate)
    return np.stack([left, right], axis=1)


def render_monaural(carrier_hz: float, beat_hz: float, duration_s: float,
                    sample_rate: int = DEFAULT_SAMPLE_RATE) -> np.ndarray:
    """Stereo (n, 2): both tones summed identically in both ears
    (physical amplitude beat at ``beat_hz``)."""
    left_hz, right_hz = binaural_pair(carrier_hz, beat_hz)
    mono = 0.5 * (sine(left_hz, duration_s, sample_rate)
                  + sine(right_hz, duration_s, sample_rate))
    return np.stack([mono, mono], axis=1).astype(np.float32)


def render_isochronic(carrier_hz: float, pulse_hz: float, duty: float,
                      duration_s: float,
                      sample_rate: int = DEFAULT_SAMPLE_RATE) -> np.ndarray:
    """Stereo (n, 2): carrier gated on/off at ``pulse_hz`` with the
    given duty fraction; short raised-cosine edges avoid hard clicks."""
    if not 0 < duty <= 1:
        raise AudioError(f"duty must be in (0, 1], got {duty}")
    if pulse_hz <= 0:
        raise AudioError("pulse rate must be > 0")
    tone = sine(carrier_hz, duration_s, sample_rate)
    t = _time(duration_s, sample_rate)
    cycle_pos = (t * pulse_hz) % 1.0
    envelope = (cycle_pos < duty).astype(np.float64)
    # 2 ms raised-cosine smoothing at gate edges
    edge = max(1, int(0.002 * sample_rate))
    kernel = np.hanning(2 * edge + 1)
    kernel /= kernel.sum()
    envelope = np.convolve(envelope, kernel, mode="same")
    gated = (tone * envelope).astype(np.float32)
    return np.stack([gated, gated], axis=1)


# --------------------------------------------------------------- noise

def white_noise(duration_s: float,
                sample_rate: int = DEFAULT_SAMPLE_RATE,
                seed: int | None = 0) -> np.ndarray:
    n = _n_samples(duration_s, sample_rate)
    rng = np.random.default_rng(seed)
    out = rng.standard_normal(n)
    return (out / max(np.max(np.abs(out)), 1e-9) * 0.5).astype(np.float32)


def pink_noise(duration_s: float,
               sample_rate: int = DEFAULT_SAMPLE_RATE,
               seed: int | None = 0) -> np.ndarray:
    """1/f-shaped noise via FFT spectral shaping (deterministic seed)."""
    n = _n_samples(duration_s, sample_rate)
    rng = np.random.default_rng(seed)
    spectrum = np.fft.rfft(rng.standard_normal(n))
    freqs = np.fft.rfftfreq(n, d=1.0 / sample_rate)
    scale = np.ones_like(freqs)
    nonzero = freqs > 0
    scale[nonzero] = 1.0 / np.sqrt(freqs[nonzero])
    out = np.fft.irfft(spectrum * scale, n)
    return (out / max(np.max(np.abs(out)), 1e-9) * 0.5).astype(np.float32)


def brown_noise(duration_s: float,
                sample_rate: int = DEFAULT_SAMPLE_RATE,
                seed: int | None = 0) -> np.ndarray:
    """1/f^2-shaped noise (integrated white, mean-removed)."""
    n = _n_samples(duration_s, sample_rate)
    rng = np.random.default_rng(seed)
    out = np.cumsum(rng.standard_normal(n))
    out -= np.mean(out)
    return (out / max(np.max(np.abs(out)), 1e-9) * 0.5).astype(np.float32)


def surf_noise(duration_s: float,
               sample_rate: int = DEFAULT_SAMPLE_RATE,
               seed: int | None = 0,
               swell_hz: float = 0.09) -> np.ndarray:
    """Surf-style bed: brown noise under a slow swell envelope."""
    bed = brown_noise(duration_s, sample_rate, seed)
    t = _time(duration_s, sample_rate)
    swell = 0.6 + 0.4 * np.sin(2 * np.pi * swell_hz * t - np.pi / 2)
    return (bed * swell).astype(np.float32)


# --------------------------------------------------------------- mixer

def _to_stereo(audio: np.ndarray) -> np.ndarray:
    if audio.ndim == 1:
        return np.stack([audio, audio], axis=1)
    return audio


def apply_fades(audio: np.ndarray, fade_in_s: float, fade_out_s: float,
                sample_rate: int) -> np.ndarray:
    out = audio.astype(np.float32).copy()
    n = out.shape[0]
    n_in = min(n, int(fade_in_s * sample_rate))
    n_out = min(n, int(fade_out_s * sample_rate))
    if n_in > 0:
        ramp = np.linspace(0.0, 1.0, n_in, dtype=np.float32)
        out[:n_in] *= ramp[:, None] if out.ndim == 2 else ramp
    if n_out > 0:
        ramp = np.linspace(1.0, 0.0, n_out, dtype=np.float32)
        out[-n_out:] *= ramp[:, None] if out.ndim == 2 else ramp
    return out


def apply_pan(audio: np.ndarray, pan: float) -> np.ndarray:
    """Constant-power pan, pan in [-1 (left), +1 (right)]."""
    if not -1 <= pan <= 1:
        raise AudioError(f"pan must be in [-1, 1], got {pan}")
    stereo = _to_stereo(audio).astype(np.float32).copy()
    angle = (pan + 1.0) * np.pi / 4.0
    stereo[:, 0] *= np.cos(angle) * np.sqrt(2)
    stereo[:, 1] *= np.sin(angle) * np.sqrt(2)
    return stereo


def mix_layers(layers: list[dict], duration_s: float,
               sample_rate: int = DEFAULT_SAMPLE_RATE) -> tuple[np.ndarray, dict]:
    """Mix rendered layers.

    Each layer dict: ``audio`` (mono or stereo array) plus optional
    ``gain_db`` (<= 0), ``pan``, ``fade_in_s``, ``fade_out_s``.
    Returns (stereo float32, stats) where stats records peak/rms and
    whether normalization engaged. Output never exceeds PEAK_CEILING.
    """
    n = _n_samples(duration_s, sample_rate)
    mix = np.zeros((n, 2), dtype=np.float64)
    for layer in layers:
        audio = _to_stereo(np.asarray(layer["audio"], dtype=np.float32))
        if audio.shape[0] < n:
            pad = np.zeros((n - audio.shape[0], 2), dtype=np.float32)
            audio = np.concatenate([audio, pad], axis=0)
        audio = audio[:n]
        audio = apply_pan(audio, float(layer.get("pan", 0.0)))
        audio = apply_fades(audio, float(layer.get("fade_in_s", 0.0)),
                            float(layer.get("fade_out_s", 0.0)),
                            sample_rate)
        gain_db = float(layer.get("gain_db", 0.0))
        if gain_db > 0:
            raise AudioError(f"layer gain must be <= 0 dB, got {gain_db}")
        mix += audio.astype(np.float64) * db_to_gain(gain_db)

    mix_peak = peak(mix)
    normalized = False
    if mix_peak > PEAK_CEILING:
        mix *= PEAK_CEILING / mix_peak
        normalized = True
    out = mix.astype(np.float32)
    stats = {"peak": peak(out), "rms": rms(out), "normalized": normalized,
             "n_layers": len(layers), "sample_rate": sample_rate,
             "duration_s": duration_s}
    return out, stats


# ----------------------------------------------------------------- wav

def write_wav(path: str | Path, audio: np.ndarray,
              sample_rate: int = DEFAULT_SAMPLE_RATE,
              bit_depth: int = 16) -> Path:
    """16-bit PCM WAV (stdlib wave module; no extra dependency)."""
    if bit_depth != 16:
        raise AudioError("only 16-bit PCM export is supported")
    stereo = _to_stereo(np.asarray(audio, dtype=np.float32))
    clipped = np.clip(stereo, -1.0, 1.0)
    pcm = (clipped * 32767.0).astype("<i2")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())
    return path


def read_wav_info(path: str | Path) -> dict:
    """Header info for verification (channels, rate, frames, duration)."""
    with wave.open(str(path), "rb") as wf:
        info = {"channels": wf.getnchannels(),
                "sample_rate": wf.getframerate(),
                "sample_width": wf.getsampwidth(),
                "frames": wf.getnframes()}
    info["duration_s"] = info["frames"] / info["sample_rate"]
    return info
