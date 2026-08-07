"""Coil and Pulse Designer service tests, including the plan pack's
required golden sideband fixtures."""
import json
from pathlib import Path

import pytest

from rgcs_desktop.services.coil_pulse import (
    PulseError, classify_key, design_estimates, estimate_resistance,
    estimate_wire_length, generate_pulse_table, sidebands)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "design_studio"


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_925_sidebands():
    table = sidebands(4096.0, 925.0)
    assert table[0]["lower_hz"] == 3171.0
    assert table[0]["upper_hz"] == 5021.0


def test_1337_sidebands():
    table = sidebands(4096.0, 1337.0)
    assert table[0]["lower_hz"] == 2759.0
    assert table[0]["upper_hz"] == 5433.0


def test_963_026_sidebands_exact_decimal():
    table = sidebands(4096.0, 963.026)
    assert table[0]["lower_hz"] == 3132.974
    assert table[0]["upper_hz"] == 5059.026


def test_sideband_orders_and_negative_lower():
    table = sidebands(4096.0, 1337.0, orders=4)
    assert [r["order"] for r in table] == [1, 2, 3, 4]
    assert table[2]["lower_hz"] == 85.0        # 4096 - 3*1337
    assert table[3]["lower_hz"] is None        # 4096 - 4*1337 < 0
    assert "omitted" in table[3]["lower_note"]


def test_wire_length_and_resistance():
    coil = {"radius_mm": 25.0, "height_mm": 40.0, "turns": 200, "count": 2}
    length = estimate_wire_length(coil)
    assert length > 0
    single = estimate_wire_length({**coil, "count": 1})
    assert length == pytest.approx(2 * single)

    wire = {"gauge_awg": 26, "material": "copper"}
    r1 = estimate_resistance(wire, single)
    r2 = estimate_resistance(wire, length)
    assert r2 == pytest.approx(2 * r1)         # resistance scales with length
    assert r1 > 0


def test_unknown_wire_material_refused():
    with pytest.raises(PulseError):
        estimate_resistance({"gauge_awg": 26, "material": "mithril"}, 10.0)


def test_invalid_duty_cycle_refused():
    pulse = {"base_hz": 4096.0, "modulation_key_hz": 925.0,
             "mode": "am_key", "duty_cycle": 1.5}
    with pytest.raises(PulseError):
        generate_pulse_table(pulse)
    pulse["duty_cycle"] = 0.0
    with pytest.raises(PulseError):
        generate_pulse_table(pulse)


def test_unknown_mode_refused():
    with pytest.raises(PulseError):
        generate_pulse_table({"base_hz": 4096.0, "modulation_key_hz": 925.0,
                              "mode": "freeform"})


def test_pulse_table_modes():
    base = {"base_hz": 4096.0, "modulation_key_hz": 925.0,
            "duty_cycle": 0.5}
    plain = generate_pulse_table({**base, "mode": "base_4096"})
    assert len(plain) == 1 and "no modulation" in plain[0]["description"]
    am = generate_pulse_table({**base, "mode": "am_key"})
    assert len(am) == 2
    quad = generate_pulse_table({**base, "mode": "quadrature_key"})
    assert len(quad) == 3 and quad[2]["segment"] == "quadrature"


def test_registered_key_recognized_custom_key_warned():
    known = classify_key(925.0)
    assert known["warning"] is None
    assert known["status"] == "mathematical relation"
    custom = classify_key(777.7)
    assert custom["status"] == "custom"
    assert custom["warning"] is not None


def test_design_estimates_from_fixture():
    design = load("coil_pulse_925.json")
    est = design_estimates(design)
    assert est["wire_length_m"] > 0
    assert est["resistance_ohm"] > 0
    assert est["classification"] == "MODEL_OUTPUT"
    assert "dc_current_at_limit_a" in est
