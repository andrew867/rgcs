"""Unit tests: rgcs_core.loading and rgcs_core.drive
(RGCS-M.42..M.45; RG-12/13/14; D-10, D-13)."""

from __future__ import annotations

import pytest

from rgcs_core.loading import (loading_factor, added_modal_mass_g,
                               length_shortfall_ratio, loading_from_length,
                               apply_correction_ledger)
from rgcs_core.drive import (drive_sequence, phase_residue_cycles,
                             electrode_pulse_metrics, sound_key_macro,
                             micro_pulse_metrics, source_preset_catalog)


def test_loading_factor_is_frequency_ratio():
    assert loading_factor(4041.0, 4096.0) == pytest.approx(4041.0 / 4096.0)


def test_k_h_and_k_tilde_h_are_distinct_functions():
    # D-10: distinct symbols, distinct functions.
    assert loading_factor is not length_shortfall_ratio
    k_tilde = length_shortfall_ratio(152.0, 154.052734375)
    assert k_tilde == pytest.approx(152.0 / 154.052734375)
    out = loading_from_length(152.0, 154.052734375, 154.0)
    assert "k_tilde_h" in "".join(out.keys())
    assert "H-08b" in out["mass_loading_compatible"] \
        or "H-08" in out["mass_loading_compatible"]


def test_added_mass_zero_when_unloaded():
    assert added_modal_mass_g(1.0, 154.0)["added_modal_mass_g"] == 0.0


def test_correction_ledger_signed_and_bounded():
    r = apply_correction_ledger(4096.0, {"loading": -0.01, "T": +0.002},
                                {"loading": 0.001, "T": 0.0005})
    assert r["delta_sum"] == pytest.approx(-0.008)
    assert r["f_corrected_hz"] == pytest.approx(4096.0 * 0.992)
    assert r["first_order_valid"]
    assert r["u_f_corrected_hz"] == pytest.approx(
        4096.0 * (0.001 ** 2 + 0.0005 ** 2) ** 0.5)
    big = apply_correction_ledger(4096.0, {"geometry": 0.03})
    assert not big["first_order_valid"]


def test_phase_residue_on_cycle_counts_only():
    # D-13 golden: nominal 1507.328 -> +0.328 (positive; register erratum).
    assert phase_residue_cycles(1507.328) == pytest.approx(0.328)
    assert phase_residue_cycles(1508.0) == 0.0


def test_drive_sequence_macro_arithmetic():
    d = drive_sequence("standard")
    assert d["macro_ms"] == pytest.approx(552.0)
    assert d["duty"] == pytest.approx(1.0 / 3.0)
    assert d["nominal_cycles"] == pytest.approx(4096 * 0.552)
    assert sum(d["on_burst_cycles"]) == d["on_total_cycles"]
    assert sum(d["spacing_burst_cycles"]) == d["spacing_total_cycles"]
    assert (d["on_total_cycles"] + d["spacing_total_cycles"]
            + d["pause_cycles"]) == d["exact_cycles"]


def test_drive_sequence_unknown_mode():
    with pytest.raises(ValueError):
        drive_sequence("bogus")


def test_electrode_and_sound_macros():
    e = electrode_pulse_metrics()
    assert e["period_ms"] == pytest.approx(50.0)
    assert e["fractional_offset_from_20hz"] == 0.0
    s = sound_key_macro()
    assert s["macrocycle_s"] == pytest.approx(36.0)
    assert s["duty"] == pytest.approx(1.0 / 3.0)


def test_micro_pulse_pulses_per_period_explicit():
    # RG-14 flag: with two alternating generators, event rate doubles.
    one = micro_pulse_metrics()
    two = micro_pulse_metrics(pulses_per_period=2)
    assert two["event_rate_energy_w"] == pytest.approx(
        2 * one["event_rate_energy_w"])
    assert two["pulse_duty_fraction"] == pytest.approx(
        2 * one["pulse_duty_fraction"])
    assert one["source_range_status"] == "within principal archival range"
    custom = micro_pulse_metrics(voltage_v=100.0)
    assert custom["source_range_status"] == "comparison/custom"


def test_source_presets_are_source_claims():
    cat = source_preset_catalog()
    assert cat["classification"].startswith("Source claim")
    assert cat["presets"]["electrode_20hz"]["frequency_hz"] == 20.0
    assert cat["presets"]["sound_1496"]["frequency_hz"] == 1496.0
    assert cat["presets"]["progressive_sequence_hz"][:3] == [10.0, 20.0,
                                                             30.0]
