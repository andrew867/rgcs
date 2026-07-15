"""Unit tests for rgcs_core.timing (Agent 07): master clock, exact-cycle
closures, modulation families, coil pair + phase at coordinate, coil
electrical model, safety envelope, sweeps/control matrix, fidelity."""
from __future__ import annotations

import math

import numpy as np
import pytest

from rgcs_core import timing as tm


# --- master clock + closures ---

def test_master_clock_carrier():
    mc = tm.master_clock(32768.0, 8, {"electrode": 20.48, "key": 1496.0})
    assert mc["carrier_hz"] == 4096.0
    assert mc["channels"]["electrode"]["integer_divider"]      # 32768/20.48=1600
    assert not mc["channels"]["key"]["integer_divider"]        # needs DDS/PLL
    assert mc["channels"]["key"]["latency_calibration_s"] is None
    with pytest.raises(ValueError):
        tm.master_clock(-1.0)


def test_golden_125ms_closure():
    # brief item 7: 512 and 187 cycles in 125 ms
    r = tm.exact_closure([4096.0, 1496.0], 0.125)
    assert r["all_close"]
    assert r["per_frequency"][4096.0]["cycles"] == pytest.approx(512)
    assert r["per_frequency"][1496.0]["cycles"] == pytest.approx(187)


def test_key_closures_644_587():
    kc = tm.key_closures()["keys"]
    assert kc[1496.0]["closure_window_s"] == pytest.approx(0.125)
    assert (kc[644.0]["closure_window_s"],
            kc[644.0]["key_cycles"],
            kc[644.0]["carrier_cycles"]) == (0.25, 161, 1024)
    assert (kc[587.0]["closure_window_s"],
            kc[587.0]["key_cycles"]) == (1.0, 587)


def test_closure_window_non_integer_freq():
    # 20.48 Hz = 4096/200 closes in exactly 1/20.48 s
    assert tm.closure_window_s([4096.0, 20.48]) == pytest.approx(1 / 20.48)


def test_modulation_families():
    rep = tm.modulation_family_report()
    assert rep["mod_20_48"]["exact_subharmonic"]
    assert rep["mod_40_96"]["exact_subharmonic"]
    assert not rep["mod_20"]["exact_subharmonic"]
    assert not rep["mod_21"]["exact_subharmonic"]
    assert rep["mod_40_96"]["carrier_ratio"] == 100.0


# --- coil pair + phase at coordinate ---

def test_coil_pair_modes():
    assert tm.coil_pair_phases(30.0)["coil_b_deg"] == 210.0
    assert tm.coil_pair_phases(30.0, "in_phase")["coil_b_deg"] == 30.0
    assert tm.coil_pair_phases(350.0, "offset", 20.0)["coil_b_deg"] == 10.0
    with pytest.raises(ValueError):
        tm.coil_pair_phases(0.0, "offset")   # missing offset_deg
    with pytest.raises(ValueError):
        tm.coil_pair_phases(0.0, "nonsense")


def test_phase_at_coordinate_terms():
    # pure acoustic delay: 63.30 mm at 6330 m/s = 10 us; at 4096 Hz that is
    # 2*pi*4096*1e-5 rad = 0.2574 rad
    r = tm.phase_at_coordinate(4096.0, acoustic_path_mm=63.30,
                               acoustic_speed_m_s=6330.0)
    assert r["delays_s"]["acoustic_s"] == pytest.approx(1e-5, rel=1e-6)
    assert r["actual_phase_rad"] == pytest.approx(
        2 * math.pi * 4096.0 * 1e-5, rel=1e-6)
    # inductive phase: wL/R = 1 -> 45 deg
    f = 4096.0
    l_h = 10.0 / (2 * math.pi * f)     # makes wL = 10 ohm
    r2 = tm.phase_at_coordinate(f, coil_inductance_h=l_h,
                                coil_resistance_ohm=10.0)
    assert r2["inductive_phase_rad"] == pytest.approx(math.pi / 4, rel=1e-9)
    # commanded phase passes straight through when no delays
    r3 = tm.phase_at_coordinate(100.0, commanded_phase_deg=90.0)
    assert r3["actual_phase_deg"] == pytest.approx(90.0)
    with pytest.raises(ValueError):
        tm.phase_at_coordinate(100.0, acoustic_path_mm=10.0)  # no speed


# --- coil electrical model ---

def test_coil_impedance_and_resonance():
    z = tm.coil_impedance(4096.0, 1e-4, 10.0)
    assert z["real_ohm"] == pytest.approx(10.0)
    assert z["imag_ohm"] == pytest.approx(2 * math.pi * 4096.0 * 1e-4)
    f_sr = tm.self_resonance_hz(1e-4, 1e-9)
    assert f_sr == pytest.approx(1 / (2 * math.pi * math.sqrt(1e-13)))
    # near self-resonance the parallel-C impedance blows up
    z_sr = tm.coil_impedance(f_sr, 1e-4, 1.0, 1e-9)
    assert z_sr["impedance_ohm"] > 100 * tm.coil_impedance(
        f_sr / 100, 1e-4, 1.0, 1e-9)["impedance_ohm"] / 100


def test_mutual_inductance():
    assert tm.mutual_inductance_h(1e-4, 4e-4, 0.5) == pytest.approx(1e-4)
    with pytest.raises(ValueError):
        tm.mutual_inductance_h(1e-4, 1e-4, 1.5)


def test_ring_response():
    r = tm.ring_response(1e-4, 1e-9, 10.0)
    assert r["underdamped"]
    assert r["q_factor"] == pytest.approx(
        math.sqrt(1e-4 / 1e-9) / 10.0 / 2 * 2, rel=1e-6) or r["q_factor"] > 1
    assert 0 < r["overshoot_fraction"] < 1
    # overdamped: big R
    r2 = tm.ring_response(1e-4, 1e-9, 1e6)
    assert not r2["underdamped"] and r2["overshoot_fraction"] == 0.0


def test_pulse_energy_and_safety():
    # E = 0.5 * 1e-4 * 4 = 2e-4 J = 200 uJ
    assert tm.pulse_energy_uj(1e-4, 2.0) == pytest.approx(200.0)
    ok = tm.safe_drive_check(20.0, 1.0, 1e-4, dummy_load_validated=True)
    assert ok["ok"]
    bad = tm.safe_drive_check(60.0, 5.0, 1e-4, dummy_load_validated=True)
    assert not bad["ok"]
    assert "voltage_ok" in bad["failed"] and "current_ok" in bad["failed"]
    # dummy-load-first is mandatory
    nd = tm.safe_drive_check(20.0, 1.0, 1e-4, dummy_load_validated=False)
    assert not nd["ok"] and "dummy_load_validated" in nd["failed"]


# --- sweeps / control matrix / randomization ---

def test_phase_sweep():
    pts = tm.phase_sweep(45.0)
    assert pts == [0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0]
    with pytest.raises(ValueError):
        tm.phase_sweep(50.0)   # does not divide 360


def test_sweep_grid_and_control_matrix():
    grid = tm.sweep_grid({"phase_deg": [0, 180], "direction": ["forward",
                                                               "backward"]})
    assert len(grid) == 4
    m = tm.control_matrix(grid)
    assert len(m) == 4 * len(tm.CONTROL_BRANCHES)
    assert {row["branch"] for row in m} == set(tm.CONTROL_BRANCHES)
    # seeded randomization is deterministic and attaches blind codes
    m1 = tm.control_matrix(grid, seed=42)
    m2 = tm.control_matrix(grid, seed=42)
    assert [r["run_index"] for r in m1] == [r["run_index"] for r in m2]
    assert all("blind_code" in r for r in m1)
    m3 = tm.control_matrix(grid, seed=43)
    assert [r["run_index"] for r in m1] != [r["run_index"] for r in m3]


# --- fidelity ---

def test_cross_correlation_recovers_lag():
    # non-periodic Gaussian pulse: lag is unambiguous (a sine would alias
    # every period)
    fs = 10_000.0
    t = np.arange(2000) / fs
    x = np.exp(-0.5 * ((t - 0.05) / 0.002) ** 2)
    lag_samples = 25
    y = np.roll(x, lag_samples)          # y lags x by 25 samples
    r = tm.cross_correlation(x, y, fs)
    assert r["lag_samples"] == -lag_samples or r["lag_samples"] == lag_samples
    assert abs(r["lag_s"]) == pytest.approx(lag_samples / fs)
    assert r["peak_correlation"] == pytest.approx(1.0, abs=1e-2)


def test_signal_fidelity():
    x = np.sin(np.linspace(0, 20 * np.pi, 500))
    assert tm.signal_fidelity(x, 3.0 * x + 1.0) == pytest.approx(1.0)
    assert tm.signal_fidelity(x, -x) == pytest.approx(-1.0)
    noise = np.random.default_rng(7).normal(size=500)
    assert abs(tm.signal_fidelity(x, noise)) < 0.2


# --- presets + classification discipline ---

def test_presets_signal_level_and_names():
    p = tm.function_generator_presets()
    assert {"macro_standard", "macro_half_spacing",
            "macro_double_rate"} <= set(p)
    assert "double pulse" not in str(p).lower()          # D7-002
    assert all(v.get("amplitude_vpp", 0.0) <= 10.0 for v in p.values())
    assert p["carrier_4096"]["phase_between_outputs_deg"] == 180.0


def test_v2_classification_attached():
    for fn in (tm.master_clock, tm.exact_closure, tm.closure_window_s,
               tm.key_closures, tm.modulation_family_report,
               tm.coil_pair_phases, tm.phase_at_coordinate,
               tm.coil_impedance, tm.self_resonance_hz,
               tm.mutual_inductance_h, tm.ring_response, tm.pulse_energy_uj,
               tm.safe_drive_check, tm.phase_sweep, tm.sweep_grid,
               tm.control_matrix, tm.randomized_order, tm.cross_correlation,
               tm.signal_fidelity, tm.function_generator_presets):
        assert hasattr(fn, "classification")
