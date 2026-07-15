"""Waveform / timing preview builder (RGCS v3, Agent 08).

Headless (Qt-free) view-model for the desktop waveform-and-timing preview:
renders sample arrays for the function-generator presets and the v2 macro
envelope modes so the UI (and tests) can display exactly what a channel
will emit. Also builds the phase-budget view rows from
rgcs_core.timing.phase_at_coordinate output.

Pure presentation math -- no drive hardware, no side effects.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from rgcs_core.drive import DRIVE_PRESETS, drive_sequence
from rgcs_core.timing import function_generator_presets

__all__ = ["preview_waveform", "preview_macro_envelope",
           "phase_budget_rows"]


def preview_waveform(preset_name: str, duration_s: float = 0.01,
                     sample_rate_hz: float = 1_000_000.0) -> dict[str, Any]:
    """Sample array for one function-generator preset.

    Returns t_s / value_v arrays plus the preset dict. Burst/macro presets
    are previewed at their carrier; the macro envelope itself is previewed
    with preview_macro_envelope()."""
    presets = function_generator_presets()
    if preset_name not in presets:
        raise ValueError(f"unknown preset {preset_name!r}; expected one of "
                         f"{sorted(presets)}")
    if not (math.isfinite(duration_s) and duration_s > 0):
        raise ValueError("duration_s must be positive and finite")
    if not (math.isfinite(sample_rate_hz) and sample_rate_hz > 0):
        raise ValueError("sample_rate_hz must be positive and finite")
    p = presets[preset_name]
    f = float(p.get("frequency_hz", p.get("carrier_hz", 0.0)))
    if f <= 0:
        raise ValueError(f"preset {preset_name!r} has no previewable "
                         f"frequency")
    amp = float(p.get("amplitude_vpp", 2.0)) / 2.0
    n = max(2, int(round(duration_s * sample_rate_hz)))
    t = np.arange(n) / sample_rate_hz
    wf = p.get("waveform", "sine")
    if wf in ("square", "ttl_trigger", "burst_macro"):
        v = amp * np.sign(np.sin(2 * np.pi * f * t))
    elif wf == "pulse":
        width_s = float(p.get("pulse_width_us", 100.0)) * 1e-6
        v = amp * ((t % (1.0 / f)) < width_s).astype(float)
    else:
        v = amp * np.sin(2 * np.pi * f * t)
    return {"preset": dict(p), "t_s": t, "value_v": v,
            "sample_rate_hz": float(sample_rate_hz)}


def preview_macro_envelope(mode: str = "half_spacing",
                           carrier_hz: float = 4096.0) -> dict[str, Any]:
    """ON/OFF envelope segments of a v2 macro mode for the timing lane.

    Wraps the frozen v2 drive_sequence (cycle-exact allocations, G-12) and
    reshapes it into [(t_start_ms, t_end_ms, state)] segments the preview
    can draw. Mode names are the frozen v2 names only (D7-002)."""
    if mode not in DRIVE_PRESETS:
        raise ValueError(f"unknown macro mode {mode!r}; expected one of "
                         f"{sorted(DRIVE_PRESETS)}")
    seq = drive_sequence(mode, carrier_hz)
    p = DRIVE_PRESETS[mode]
    segments: list[tuple[float, float, str]] = []
    t = 0.0
    for _ in range(int(p["bursts"])):
        segments.append((t, t + p["on_ms"], "on"))
        t += p["on_ms"]
        segments.append((t, t + p["spacing_ms"], "off"))
        t += p["spacing_ms"]
    segments.append((t, t + p["pause_ms"], "pause"))
    t += p["pause_ms"]
    return {"mode": mode, "carrier_hz": float(carrier_hz),
            "segments": segments, "macro_ms": t,
            "drive_sequence": seq}


def phase_budget_rows(budget: dict[str, Any]) -> list[dict[str, Any]]:
    """Reshape phase_at_coordinate() output into display rows (one per
    delay term + inductive + total), for the optical-path/phase-delay
    view. A None/absent budget field never appears as 0 silently -- only
    terms actually present in the budget are shown."""
    if "delays_s" not in budget or "actual_phase_deg" not in budget:
        raise ValueError("budget must be a phase_at_coordinate() result")
    rows = [{"term": name, "delay_s": val, "kind": "delay"}
            for name, val in budget["delays_s"].items()]
    rows.append({"term": "inductive",
                 "phase_rad": budget["inductive_phase_rad"],
                 "kind": "phase"})
    rows.append({"term": "TOTAL", "delay_s": budget["total_delay_s"],
                 "phase_deg": budget["actual_phase_deg"], "kind": "total"})
    return rows
