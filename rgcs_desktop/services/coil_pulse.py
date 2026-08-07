"""Coil and Pulse Designer services: wire length / resistance
estimates, exact sideband arithmetic, pulse timing tables, and the
build-sheet PDF.

All numbers here are model outputs from the declared formulas below —
estimates for planning a build, never measurements.
"""
from __future__ import annotations

import math
from fractions import Fraction
from pathlib import Path

from rgcs_desktop.services import pdf_sheets
from rgcs_desktop.services.design_studio import MODEL_OUTPUT, claim_boundary
from rgcs_desktop.services.export_receipts import make_receipt
from rgcs_desktop.services.frequency_keys_lib import known_key_hz

PULSE_MODES = ("base_4096", "am_key", "pwm_key", "timing_fm_key",
               "phase_dither_key", "quadrature_key")

#: Resistivity (ohm·m, ~20 °C handbook values) — declared model inputs.
RESISTIVITY_OHM_M = {
    "copper": 1.68e-8,
    "silver": 1.59e-8,
    "aluminum": 2.65e-8,
    "nichrome": 1.10e-6,
}


class PulseError(ValueError):
    """A refused pulse/coil parameter (with the reason)."""


def awg_diameter_mm(awg: int) -> float:
    """AWG -> conductor diameter in mm (standard geometric formula)."""
    if not 0 <= int(awg) <= 50:
        raise PulseError(f"unsupported wire gauge AWG {awg}")
    return 0.127 * (92.0 ** ((36 - int(awg)) / 39.0))


def estimate_wire_length(coil: dict) -> float:
    """Helix length in metres for one or more identical coils.

    L = turns * sqrt((2*pi*r)^2 + pitch^2), pitch = height/turns.
    """
    r_mm = float(coil["radius_mm"])
    h_mm = float(coil.get("height_mm", 0.0))
    turns = int(coil["turns"])
    count = int(coil.get("count", 1))
    if r_mm <= 0 or turns <= 0 or count <= 0:
        raise PulseError("coil radius, turns, and count must be positive")
    pitch = h_mm / turns if turns else 0.0
    per_turn = math.sqrt((2 * math.pi * r_mm) ** 2 + pitch ** 2)
    return per_turn * turns * count / 1000.0


def estimate_resistance(wire: dict, length_m: float) -> float:
    """R = rho * L / A for the declared wire material and gauge."""
    material = str(wire.get("material", "copper")).lower()
    rho = RESISTIVITY_OHM_M.get(material)
    if rho is None:
        raise PulseError(
            f"no declared resistivity for wire material '{material}' "
            f"(known: {', '.join(sorted(RESISTIVITY_OHM_M))})")
    if "diameter_mm" in wire:
        d_mm = float(wire["diameter_mm"])
    else:
        d_mm = awg_diameter_mm(int(wire["gauge_awg"]))
    area_m2 = math.pi * (d_mm / 2000.0) ** 2
    if length_m < 0:
        raise PulseError("wire length must be >= 0")
    return rho * length_m / area_m2


def sidebands(carrier_hz: float, key_hz: float, orders: int = 3) -> list[dict]:
    """Exact sideband table: carrier ± n·key, n = 1..orders.

    Exact decimal arithmetic (Fraction over the decimal string) so
    4096 ± 925 gives exactly 3171/5021 and 4096 ± 963.026 gives exactly
    3132.974/5059.026.
    """
    c = Fraction(str(carrier_hz))
    k = Fraction(str(key_hz))
    if c <= 0:
        raise PulseError("carrier must be > 0")
    if k < 0:
        raise PulseError("key must be >= 0")
    table = []
    for n in range(1, int(orders) + 1):
        lower = c - n * k
        upper = c + n * k
        table.append({
            "order": n,
            "lower_hz": float(lower) if lower > 0 else None,
            "upper_hz": float(upper),
            "lower_note": ("" if lower > 0
                           else f"carrier - {n}·key is not positive; "
                                f"omitted"),
        })
    return table


def classify_key(key_hz: float) -> dict:
    """Known keys come from the frequency key library; anything else is
    allowed only as *custom*, with a warning attached."""
    known = known_key_hz(key_hz)
    if known is not None:
        return {"status": known.get("source_status", "registered"),
                "label": known.get("label", ""), "warning": None}
    return {"status": "custom",
            "label": f"custom key {key_hz:g} Hz",
            "warning": (f"{key_hz:g} Hz is not in the frequency key "
                        f"library; recorded as a custom key with no "
                        f"source status")}


def generate_pulse_table(pulse: dict) -> list[dict]:
    """Timing rows for the selected pulse mode. Refuses invalid duty
    cycles and unknown modes."""
    mode = pulse.get("mode")
    if mode not in PULSE_MODES:
        raise PulseError(
            f"unknown pulse mode {mode!r} (supported: "
            f"{', '.join(PULSE_MODES)})")
    base = float(pulse["base_hz"])
    key = float(pulse.get("modulation_key_hz", 0.0))
    duty = pulse.get("duty_cycle", 0.5)
    if not 0 < float(duty) <= 1:
        raise PulseError(f"duty cycle must be in (0, 1], got {duty}")
    duty = float(duty)
    if base <= 0:
        raise PulseError("base frequency must be > 0")

    base_period_us = 1e6 / base
    rows = [{
        "segment": "carrier",
        "description": f"base carrier {base:g} Hz",
        "frequency_hz": base,
        "period_us": base_period_us,
        "duty": duty,
    }]
    if mode == "base_4096":
        rows[0]["description"] = (f"continuous base carrier {base:g} Hz, "
                                  f"no modulation")
        return rows
    if key <= 0:
        raise PulseError(f"mode {mode} requires a modulation key > 0")
    key_period_us = 1e6 / key
    descriptions = {
        "am_key": f"amplitude envelope at {key:g} Hz",
        "pwm_key": f"pulse-width modulation at {key:g} Hz "
                   f"(duty swings around {duty:g})",
        "timing_fm_key": f"timing modulation of the carrier at {key:g} Hz",
        "phase_dither_key": f"phase dither keyed at {key:g} Hz",
        "quadrature_key": f"quadrature pair offset 90° keyed at {key:g} Hz",
    }
    rows.append({
        "segment": "modulation",
        "description": descriptions[mode],
        "frequency_hz": key,
        "period_us": key_period_us,
        "duty": duty,
    })
    if mode == "quadrature_key":
        rows.append({
            "segment": "quadrature",
            "description": f"second channel, +90° phase at {key:g} Hz",
            "frequency_hz": key,
            "period_us": key_period_us,
            "duty": duty,
        })
    return rows


def design_estimates(design: dict) -> dict:
    """Wire + electrical estimates for a coil/pulse design dict."""
    coil = design.get("coil") or {}
    wire = design.get("wire") or {}
    length_m = estimate_wire_length(coil)
    resistance = estimate_resistance(wire, length_m)
    limits = design.get("limits") or {}
    est = {
        "wire_length_m": length_m,
        "resistance_ohm": resistance,
        "classification": MODEL_OUTPUT,
    }
    v = limits.get("voltage_v")
    if v is not None and resistance > 0:
        i = float(v) / resistance
        est["dc_current_at_limit_a"] = i
        cap = limits.get("current_a")
        est["exceeds_current_limit"] = (cap is not None
                                        and i > float(cap))
    return est


def render_coil_pulse_pdf(design: dict, out_path: Path) -> dict:
    """Build/calibration sheet PDF with wire, pulse, and sideband
    tables. Carries the model-output claim boundary."""
    pulse = design["pulse"]
    est = design.get("estimates") or design_estimates(design)
    sb = design.get("sidebands") or sidebands(
        pulse["base_hz"], pulse.get("modulation_key_hz", 0.0))
    key_info = classify_key(float(pulse.get("modulation_key_hz", 0.0)))
    ptable = generate_pulse_table(pulse)

    wire_rows = [
        ("wire", f"AWG {design['wire'].get('gauge_awg', '?')} "
                 f"{design['wire'].get('material', 'copper')}"),
        ("wire length estimate (m)", est.get("wire_length_m")),
        ("resistance estimate (ohm)", est.get("resistance_ohm")),
        ("DC current at voltage limit (A)",
         est.get("dc_current_at_limit_a")),
    ]
    sb_rows = [[r["order"], r["lower_hz"], r["upper_hz"],
                r.get("lower_note", "")] for r in sb]
    pt_rows = [[r["segment"], r["description"], r["frequency_hz"],
                r["period_us"], r["duty"]] for r in ptable]

    key_note = key_info["warning"] or (
        f"modulation key status: {key_info['status']}")

    input_hash = pdf_sheets.sheet_input_hash(design)
    out_path = pdf_sheets.render_sheet_pdf(
        title="RGCS Engineering Build Sheet — Coil and Pulse",
        subtitle=(f"Design {design['design_id']} · assembly "
                  f"{design['source_assembly_id']} · mode "
                  f"{pulse['mode']}"),
        sections=[
            ("Wire and coil estimates (model outputs)",
             pdf_sheets.rows_block(wire_rows)),
            ("Sideband table (carrier ± n·key)",
             pdf_sheets.table_block(
                 ["order", "lower (Hz)", "upper (Hz)", "note"], sb_rows)),
            ("Pulse timing table",
             pdf_sheets.table_block(
                 ["segment", "description", "f (Hz)", "period (µs)",
                  "duty"], pt_rows)),
            ("Modulation key", pdf_sheets.paragraph(key_note)),
            ("Measurement plan", pdf_sheets.paragraph(
                "Measure actual coil resistance and driven waveforms "
                "before relying on any estimate above; record measured "
                "values beside the model outputs.")),
        ],
        boundary=claim_boundary("build_sheet"),
        out_path=Path(out_path),
        input_hash=input_hash)
    return make_receipt(
        inputs=design, outputs=[out_path], classification=MODEL_OUTPUT,
        object_id=design["design_id"],
        source_ids=[design["source_assembly_id"]],
        boundary=claim_boundary("build_sheet"))
