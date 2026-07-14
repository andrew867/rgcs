"""rgcs_core.drive — pulse timing, exact cycle families, envelopes,
microsecond coil pulses, and source presets (RG-12/13/14, D-13).

Units: times in ms/us/s as suffixed; frequencies in Hz; voltages in V;
currents in A; inductance in uH; energy in uJ.

Phase residue r_phi is computed on CYCLE COUNTS only, never on duty
(A-21; closes D-13): r_phi = c - round(c) for nominal cycle count c.
Golden: half-spacing nominal c = 1507.328 -> r_phi = +0.328 cycles.
"""

from __future__ import annotations

import math
from typing import Any

from ..provenance import classified, classification_string

__all__ = ["DRIVE_PRESETS", "phase_residue_cycles", "drive_sequence",
           "electrode_pulse_metrics", "sound_key_macro",
           "micro_pulse_metrics", "source_preset_catalog"]

#: Envelope-family presets (RG-12): on/spacing/pause ms are Source claim
#: (JH log); the cycle-exact allocations are Derived (RGCS engineering
#: refinement) and do NOT replace the source-stated millisecond values.
DRIVE_PRESETS: dict[str, dict[str, float | int]] = {
    "standard": {"on_ms": 46.0, "spacing_ms": 46.0, "pause_ms": 184.0,
                 "bursts": 4, "exact_cycles": 2261},
    "half_spacing": {"on_ms": 46.0, "spacing_ms": 23.0, "pause_ms": 92.0,
                     "bursts": 4, "exact_cycles": 1508},
    "double_rate": {"on_ms": 23.0, "spacing_ms": 23.0, "pause_ms": 92.0,
                    "bursts": 4, "exact_cycles": 1131},
}


def _positive(name: str, v: float) -> None:
    if not (math.isfinite(v) and v > 0):
        raise ValueError(f"{name} must be positive and finite; got {v!r}")


@classified("Derived", sources=("RG-12",),
            note="r_phi defined on CYCLE COUNTS only, never duty (A-21, "
                 "D-13); distinct from the offset to an exact-cycle preset")
def phase_residue_cycles(nominal_cycles: float) -> float:
    """Phase residue r_phi = c - round(c) in cycles (D-13). Golden:
    c = 1507.328 -> +0.328 (the register's -0.328 was an erratum)."""
    if not math.isfinite(nominal_cycles):
        raise ValueError("nominal_cycles must be finite")
    return nominal_cycles - round(nominal_cycles)


@classified("Derived", sources=("RG-12",),
            note="millisecond presets are Source claim (JH log); "
                 "cycle-exact rows are Derived engineering refinements that "
                 "do not replace the source-stated millisecond values")
def drive_sequence(mode: str = "half_spacing",
                   carrier_hz: float = 4096.0) -> dict[str, Any]:
    """Envelope-family timing with exact-cycle allocation (RG-12).
    Golden (G-12): 2261 = 754+754+753 (552.001953125 ms);
    1508 = 754+377+377 (368.1640625 ms); 1131 = 377+377+377
    (276.123046875 ms)."""
    _positive("carrier_hz", carrier_hz)
    if mode not in DRIVE_PRESETS:
        raise ValueError(f"unknown mode {mode!r}; expected one of "
                         f"{sorted(DRIVE_PRESETS)}")
    p = DRIVE_PRESETS[mode]
    bursts = int(p["bursts"])
    macro_ms = bursts * (p["on_ms"] + p["spacing_ms"]) + p["pause_ms"]
    nominal_cycles = carrier_hz * macro_ms / 1000.0
    exact = int(p["exact_cycles"])
    duty = bursts * p["on_ms"] / macro_ms
    on_total = round(exact * duty)
    spacing_weight = bursts * p["spacing_ms"]
    pause_weight = p["pause_ms"]
    spacing_total = round((exact - on_total) * spacing_weight
                          / (spacing_weight + pause_weight))
    pause_total = exact - on_total - spacing_total

    def distribute(total: int, count: int) -> list[int]:
        base, remainder = divmod(total, count)
        return [base + (1 if i < remainder else 0) for i in range(count)]

    return {
        "mode": mode,
        "carrier_hz": carrier_hz,
        "carrier_period_us": 1e6 / carrier_hz,
        "on_ms": p["on_ms"], "spacing_ms": p["spacing_ms"],
        "pause_ms": p["pause_ms"], "bursts": bursts,
        "macro_ms": macro_ms, "macro_hz": 1000.0 / macro_ms,
        "nominal_cycles": nominal_cycles,
        "phase_residue_cycles": phase_residue_cycles(nominal_cycles),
        "duty": duty,
        "exact_cycles": exact,
        "exact_macro_ms": exact / carrier_hz * 1000.0,
        "on_total_cycles": int(on_total),
        "spacing_total_cycles": int(spacing_total),
        "pause_cycles": int(pause_total),
        "on_burst_cycles": distribute(int(on_total), bursts),
        "spacing_burst_cycles": distribute(int(spacing_total), bursts),
        "classification": classification_string(drive_sequence),
    }


@classified("Derived", sources=("RG-13",),
            note="operating points (20 Hz / 15 V) are Source claim (JH log)")
def electrode_pulse_metrics(frequency_hz: float = 20.0,
                            amplitude_v: float = 15.0,
                            session_s: float = 60.0) -> dict[str, Any]:
    """Electrode-branch timing arithmetic (RG-13). The 20 Hz / 15 V
    operating point is a Source claim (JH log), never a design target."""
    _positive("frequency_hz", frequency_hz)
    _positive("amplitude_v", amplitude_v)
    _positive("session_s", session_s)
    return {
        "frequency_hz": frequency_hz,
        "period_ms": 1000.0 / frequency_hz,
        "amplitude_v": amplitude_v,
        "pulses_per_session": frequency_hz * session_s,
        "fractional_offset_from_20hz": frequency_hz / 20.0 - 1.0,
        "classification": classification_string(electrode_pulse_metrics),
    }


@classified("Derived", sources=("RG-13",),
            note="1496 Hz and 36 s macrocycle are Source claim (JH log)")
def sound_key_macro(frequency_hz: float = 1496.0, on_s: float = 3.0,
                    off_s: float = 3.0, bursts: int = 4,
                    pause_s: float = 12.0) -> dict[str, Any]:
    """Sound-key macrocycle arithmetic (RG-13): default 3 s ON / 3 s OFF
    x 4 + 12 s pause = 36 s, duty 1/3."""
    for name, v in (("frequency_hz", frequency_hz), ("on_s", on_s),
                    ("off_s", off_s), ("pause_s", pause_s)):
        _positive(name, v)
    if bursts < 1:
        raise ValueError("bursts must be >= 1")
    macro = bursts * (on_s + off_s) + pause_s
    energized = bursts * on_s
    return {
        "frequency_hz": frequency_hz, "on_s": on_s, "off_s": off_s,
        "bursts": bursts, "pause_s": pause_s, "macrocycle_s": macro,
        "macrocycle_hz": 1.0 / macro, "energized_s": energized,
        "duty": energized / macro,
        "classification": classification_string(sound_key_macro),
    }


@classified("Derived", sources=("RG-14",),
            note="circuit inference neglecting resistance (stated "
                 "assumption); operating points are Source claim; WB5 "
                 "audit: measure, don't infer")
def micro_pulse_metrics(carrier_hz: float = 4096.0,
                        pulse_width_us: float = 1.0,
                        voltage_v: float = 45.0,
                        peak_current_a: float = 2.0,
                        rise_time_us: float = 1.0,
                        decay_time_us: float = 30.0,
                        pulses_per_period: int = 1) -> dict[str, Any]:
    """Microsecond coil-pulse proxies (RG-14): L ~ V t_rise / I;
    E = L I^2 / 2; decay-voltage scale L I / t_decay. Golden (G-13):
    60 V, 1.3 us, 3 A -> 26 uH, 117 uJ.

    ``pulses_per_period`` makes the previously hidden one-pulse-per-carrier-
    period assumption explicit (RG-14 flag): with two alternating
    generators the event rate is 2x."""
    for name, v in (("carrier_hz", carrier_hz),
                    ("pulse_width_us", pulse_width_us),
                    ("voltage_v", voltage_v),
                    ("peak_current_a", peak_current_a),
                    ("rise_time_us", rise_time_us),
                    ("decay_time_us", decay_time_us)):
        _positive(name, v)
    if pulses_per_period < 1:
        raise ValueError("pulses_per_period must be >= 1")
    period_us = 1e6 / carrier_hz
    inductance_uh = voltage_v * rise_time_us / peak_current_a
    energy_uj = 0.5 * inductance_uh * peak_current_a ** 2
    within = (1 <= pulse_width_us <= 4 and 20 <= voltage_v <= 60
              and 0.2 <= peak_current_a <= 3)
    return {
        "carrier_period_us": period_us,
        "pulses_per_period": pulses_per_period,
        "pulse_duty_fraction": pulses_per_period * pulse_width_us / period_us,
        "inferred_inductance_uh": inductance_uh,
        "stored_energy_uj": energy_uj,
        "event_rate_energy_w": energy_uj * 1e-6 * carrier_hz
        * pulses_per_period,
        "decay_voltage_scale_v": inductance_uh * peak_current_a
        / decay_time_us,
        "rise_slew_a_per_us": peak_current_a / rise_time_us,
        "decay_slew_a_per_us": peak_current_a / decay_time_us,
        "source_range_status": ("within principal archival range" if within
                                else "comparison/custom"),
        "inference_note": "resistance neglected; measure L/R/clamp "
                          "behavior, don't infer (WB5 audit, JH-027)",
        "classification": classification_string(micro_pulse_metrics),
    }


@classified("Source claim", sources=("RG-13", "RG-14"),
            note="every preset is a Source claim from the JH log (with "
                 "page refs in the ledger); never a design target")
def source_preset_catalog() -> dict[str, Any]:
    """Source-preset catalogue (all Source claim, RG-13/RG-14)."""
    return {
        "classification": classification_string(source_preset_catalog),
        "presets": {
            "electrode_20hz": {"frequency_hz": 20.0, "amplitude_v": 15.0,
                               "coupling": "silver electrodes at measured "
                                           "node"},
            "electrode_21hz": {"frequency_hz": 21.0, "amplitude_v": 15.0,
                               "coupling": "comparison"},
            "sound_1496": {"frequency_hz": 1496.0, "on_s": 3.0, "off_s": 3.0,
                           "bursts": 4, "pause_s": 12.0},
            "sound_644": {"frequency_hz": 644.0, "on_s": 3.0, "off_s": 3.0,
                          "bursts": 4, "pause_s": 12.0},
            "sound_587": {"frequency_hz": 587.0, "on_s": 3.0, "off_s": 3.0,
                          "bursts": 4, "pause_s": 12.0},
            "progressive_sequence_hz": [10.0, 20.0, 30.0, 50.0, 80.0, 130.0,
                                        210.0, 340.0, 550.0],
            "coil_4096": {"carrier_hz": 4096.0, "pulse_width_us": "1-4",
                          "voltage_v": "20-60", "current_a": "0.2-3",
                          "topology": "complementary non-overlap"},
        },
    }
