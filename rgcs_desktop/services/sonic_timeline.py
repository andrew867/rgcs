"""Frequency Key Studio timeline engine: segments, ramp curves, and
whole-session rendering.

A session (frequency_session schema) is a list of timeline segments
(each with a beat ramp) plus a list of layers. Beat-bearing layers
(binaural / monaural / isochronic) follow the session's beat envelope;
noise beds run for the full duration.
"""
from __future__ import annotations

import numpy as np

from rgcs_desktop.services import sonic_audio
from rgcs_desktop.services.sonic_audio import (AudioError,
                                               DEFAULT_SAMPLE_RATE)

SEGMENT_KINDS = ("intro", "relax", "ramp_down", "hold", "exploration",
                 "ramp_up", "return", "outro")
RAMP_CURVES = ("linear", "cosine", "exponential", "stepped")


class TimelineError(ValueError):
    """A refused session/timeline structure (with the reason)."""


def ramp(start: float, end: float, n: int, curve: str = "linear",
         steps: int = 8) -> np.ndarray:
    """A ramp of ``n`` values from start to end along a named curve."""
    if curve not in RAMP_CURVES:
        raise TimelineError(f"unknown ramp curve {curve!r} "
                            f"(supported: {', '.join(RAMP_CURVES)})")
    if n <= 0:
        return np.empty(0)
    x = np.linspace(0.0, 1.0, n)
    if curve == "linear":
        shape = x
    elif curve == "cosine":
        shape = 0.5 * (1 - np.cos(np.pi * x))
    elif curve == "exponential":
        shape = (np.expm1(3 * x)) / np.expm1(3)
    else:  # stepped
        shape = np.floor(x * steps) / max(steps - 1, 1)
        shape = np.clip(shape, 0.0, 1.0)
    return start + (end - start) * shape


def validate_session(session: dict) -> None:
    """Structural checks beyond the JSON schema."""
    segments = session.get("segments") or []
    if not segments:
        raise TimelineError("session has no segments")
    for seg in segments:
        if seg.get("kind") not in SEGMENT_KINDS:
            raise TimelineError(f"unknown segment kind {seg.get('kind')!r}")
        if seg.get("duration_s", 0) <= 0:
            raise TimelineError("segment duration must be > 0")
        if seg.get("curve", "linear") not in RAMP_CURVES:
            raise TimelineError(f"unknown curve {seg.get('curve')!r}")
    total = sum(float(s["duration_s"]) for s in segments)
    declared = float(session.get("duration_s", total))
    if abs(total - declared) > 0.5:
        raise TimelineError(
            f"segment durations sum to {total:g} s but the session "
            f"declares {declared:g} s")


def beat_envelope(session: dict,
                  sample_rate: int = DEFAULT_SAMPLE_RATE) -> np.ndarray:
    """Per-sample beat frequency across the whole session."""
    validate_session(session)
    parts = []
    for seg in session["segments"]:
        n = int(round(float(seg["duration_s"]) * sample_rate))
        start = float(seg.get("beat_start_hz", 0.0))
        end = float(seg.get("beat_end_hz", start))
        parts.append(ramp(start, end, n, seg.get("curve", "linear")))
    return np.concatenate(parts) if parts else np.empty(0)


def _wobble_multiplier_env(layer: dict, n_samples: int,
                           sample_rate: int) -> np.ndarray | None:
    """Per-sample frequency multiplier from the layer's wobble stage
    table (cyclic; one dwell period per stage), or None."""
    wobble = layer.get("wobble")
    if not wobble:
        return None
    from rgcs_desktop.services.sonic_recipes import wobble_by_name
    table = wobble_by_name(wobble["name"])
    multipliers = np.asarray(table["multipliers"], dtype=np.float64)
    dwell_s = float(wobble.get("dwell_s", 1.0))
    if dwell_s <= 0:
        raise TimelineError("wobble dwell must be > 0 seconds")
    stage_idx = (np.arange(n_samples) // int(round(dwell_s
                                                   * sample_rate))) \
        % len(multipliers)
    return multipliers[stage_idx]


def _render_beat_layer(layer: dict, beat_env: np.ndarray,
                       sample_rate: int) -> np.ndarray:
    """Render a binaural/monaural/isochronic layer following the
    session beat envelope via phase integration (smooth ramps).

    An optional layer ``wobble`` walks a cyclic stage table of
    frequency multipliers (dwell seconds per stage), applied to the
    carrier (default) or the beat. Phase integration keeps stage
    boundaries click-free."""
    carrier = float(layer.get("carrier_hz", 0.0))
    if carrier <= 0:
        raise TimelineError(f"layer {layer.get('layer_id')} needs a "
                            f"carrier_hz")
    dt = 1.0 / sample_rate
    kind = layer["type"]

    wobble_env = _wobble_multiplier_env(layer, len(beat_env),
                                        sample_rate)
    carrier_env = np.full(len(beat_env), carrier, dtype=np.float64)
    if wobble_env is not None:
        target = (layer.get("wobble") or {}).get("target", "carrier")
        if target == "carrier":
            carrier_env = carrier_env * wobble_env
        elif target == "beat":
            beat_env = beat_env * wobble_env
        else:
            raise TimelineError(f"wobble target must be 'carrier' or "
                                f"'beat', got {target!r}")
        peak_hz = float(np.max(carrier_env) + np.max(beat_env) / 2)
        if peak_hz >= 0.95 * sample_rate / 2:
            raise TimelineError(
                f"wobbled frequency peaks at {peak_hz:.0f} Hz — too "
                f"close to the {sample_rate // 2} Hz Nyquist limit; "
                f"use a lower carrier or a smaller wobble table")
    carrier = carrier_env
    if kind == "binaural":
        left_freq = carrier - beat_env / 2.0
        right_freq = carrier + beat_env / 2.0
        left = np.sin(2 * np.pi * np.cumsum(left_freq) * dt)
        right = np.sin(2 * np.pi * np.cumsum(right_freq) * dt)
        return np.stack([left, right], axis=1).astype(np.float32)
    if kind == "monaural":
        lo = np.sin(2 * np.pi * np.cumsum(carrier - beat_env / 2.0) * dt)
        hi = np.sin(2 * np.pi * np.cumsum(carrier + beat_env / 2.0) * dt)
        mono = 0.5 * (lo + hi)
        return np.stack([mono, mono], axis=1).astype(np.float32)
    if kind == "isochronic":
        tone = np.sin(2 * np.pi * np.cumsum(carrier) * dt)
        gate_phase = np.cumsum(beat_env) * dt % 1.0
        duty = float(layer.get("duty", 0.5))
        if not 0 < duty <= 1:
            raise TimelineError(f"duty must be in (0, 1], got {duty}")
        envelope = (gate_phase < duty).astype(np.float64)
        edge = max(1, int(0.002 * sample_rate))
        kernel = np.hanning(2 * edge + 1)
        kernel /= kernel.sum()
        envelope = np.convolve(envelope, kernel, mode="same")
        gated = (tone * envelope)
        return np.stack([gated, gated], axis=1).astype(np.float32)
    raise TimelineError(f"not a beat layer: {kind}")


_NOISE_FNS = {
    "white_noise": sonic_audio.white_noise,
    "pink_noise": sonic_audio.pink_noise,
    "brown_noise": sonic_audio.brown_noise,
    "surf_noise": sonic_audio.surf_noise,
}


def _render_file_layer(layer: dict, duration_s: float,
                       sample_rate: int) -> np.ndarray:
    """voice_cue / music_bed from a WAV file, resampled to the session
    rate and placed at layer['start_s'] (default 0), truncated/padded
    to the session length."""
    path = layer.get("file")
    if not path:
        raise TimelineError(
            f"layer {layer.get('layer_id')} ({layer.get('type')}) has "
            f"no file — attach a WAV or remove the layer")
    audio, src_rate = sonic_audio.load_wav(path)
    audio = sonic_audio.resample_linear(audio, src_rate, sample_rate)
    n_total = int(round(duration_s * sample_rate))
    start = int(round(float(layer.get("start_s", 0.0)) * sample_rate))
    if start < 0:
        raise TimelineError("layer start_s must be >= 0")
    out = np.zeros((n_total, 2), dtype=np.float32)
    end = min(n_total, start + audio.shape[0])
    if start < n_total:
        out[start:end] = audio[:end - start]
    return out


def render_session(session: dict,
                   sample_rate: int | None = None) -> tuple[np.ndarray, dict]:
    """Render a full session to stereo float32 + mix stats.

    voice_cue / music_bed layers render from their WAV file when one is
    attached; a file layer without a file is skipped and listed in
    stats["skipped_layers"] — a stated absence, never a silent one.
    Optional session["loudness"]["target_rms_db"] applies RMS
    normalization after the mix (peak-capped; recorded in stats).
    """
    sample_rate = int(sample_rate or session.get("sample_rate",
                                                 DEFAULT_SAMPLE_RATE))
    validate_session(session)
    duration_s = float(session["duration_s"])
    env = beat_envelope(session, sample_rate)

    rendered, skipped = [], []
    for layer in session.get("layers") or []:
        kind = layer.get("type")
        entry = {"gain_db": layer.get("gain_db", -6.0),
                 "pan": layer.get("pan", 0.0),
                 "fade_in_s": layer.get("fade_in_s", 0.0),
                 "fade_out_s": layer.get("fade_out_s", 0.0)}
        if kind in ("binaural", "monaural", "isochronic"):
            entry["audio"] = _render_beat_layer(layer, env, sample_rate)
        elif kind in _NOISE_FNS:
            entry["audio"] = _NOISE_FNS[kind](duration_s, sample_rate,
                                              layer.get("seed", 0))
        elif kind in ("music_bed", "voice_cue"):
            if layer.get("file"):
                entry["audio"] = _render_file_layer(layer, duration_s,
                                                    sample_rate)
            else:
                skipped.append(f"{layer.get('layer_id')} ({kind}: no "
                               f"file attached)")
                continue
        else:
            raise TimelineError(f"unknown layer type {kind!r}")
        rendered.append(entry)

    if not rendered:
        raise TimelineError("session has no renderable layers")
    audio, stats = sonic_audio.mix_layers(rendered, duration_s,
                                          sample_rate)
    loudness = (session.get("loudness") or {}).get("target_rms_db")
    if loudness is not None:
        audio, norm = sonic_audio.normalize_rms(audio, float(loudness))
        stats["peak"] = sonic_audio.peak(audio)
        stats["rms"] = sonic_audio.rms(audio)
        stats["loudness_target_rms_db"] = float(loudness)
        stats["loudness_gain_db"] = norm["gain_db"]
        stats["loudness_peak_limited"] = norm["peak_limited"]
    stats["skipped_layers"] = skipped
    stats["beat_start_hz"] = float(env[0]) if env.size else None
    stats["beat_end_hz"] = float(env[-1]) if env.size else None
    return audio, stats


def standard_session_shape(beat_hz: float, duration_s: float) -> list[dict]:
    """The companion's standard shape: settle at a gentle start beat,
    ramp to target, hold, return. Durations scale with the session."""
    if duration_s < 10:
        raise TimelineError("session too short for the standard shape "
                            "(need >= 10 s)")
    intro = max(2.0, min(60.0, duration_s * 0.05))
    settle = max(2.0, min(180.0, duration_s * 0.10))
    ramp_s = max(2.0, min(300.0, duration_s * 0.15))
    outro = max(2.0, min(120.0, duration_s * 0.10))
    hold = duration_s - (intro + settle + ramp_s + outro)
    if hold <= 0:
        raise TimelineError("session too short for the standard shape")
    start_beat = max(beat_hz, 10.0)
    return [
        {"kind": "intro", "duration_s": intro,
         "beat_start_hz": start_beat, "beat_end_hz": start_beat,
         "curve": "linear"},
        {"kind": "relax", "duration_s": settle,
         "beat_start_hz": start_beat, "beat_end_hz": start_beat,
         "curve": "linear"},
        {"kind": "ramp_down", "duration_s": ramp_s,
         "beat_start_hz": start_beat, "beat_end_hz": beat_hz,
         "curve": "cosine"},
        {"kind": "hold", "duration_s": hold,
         "beat_start_hz": beat_hz, "beat_end_hz": beat_hz,
         "curve": "linear"},
        {"kind": "outro", "duration_s": outro,
         "beat_start_hz": beat_hz, "beat_end_hz": beat_hz,
         "curve": "linear"},
    ]
