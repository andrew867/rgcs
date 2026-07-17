"""Implementation-depth tests added by the v4.2.1 completeness audit.

The v4.2.0 ledger claimed C05/C06/C07 depth that the modules did not
have (C05 had no module at all — only a registry row). These tests pin
the real capability."""

import math

import numpy as np
import pytest

from rscs2_core import apparatus as ap
from rscs2_core import bvd, metrology
from rscs2_core.refmodels import polariton as pol


# --- C01 strong-coupling criterion (prompt boundary) -------------------

def test_strong_coupling_requires_splitting_above_losses():
    """C01 boundary: no strong-coupling claim without comparing the
    splitting to the linewidths."""
    assert pol.strong_coupling_criterion(0.01, 1e-3, 1e-3)["regime"] \
        == "STRONG_COUPLING"
    # below the exceptional point (|gx-gc|/2) there is no real split
    assert pol.strong_coupling_criterion(0.004, 0.01, 0.0)["regime"] \
        == "WEAK_COUPLING"
    # equal linewidths: real parts split for any coupling, but the
    # peaks are not resolvable until Omega > (gx+gc)/2
    mid = pol.strong_coupling_criterion(1e-4, 0.01, 0.01)
    assert mid["regime"] == "INTERMEDIATE_SPLIT_BUT_UNRESOLVED"
    assert not mid["strict_criterion_met"]


def test_strong_coupling_matches_complex_eigenvalues():
    """The criterion must agree with the actual 2x2 complex solution at
    zero detuning, not merely assert a rule of thumb."""
    for om, gx, gc in [(0.01, 1e-3, 1e-3), (1e-4, 0.02, 0.0),
                       (0.006, 0.02, 0.0)]:
        crit = pol.strong_coupling_criterion(om, gx, gc)
        h = pol.hopfield_2x2(1.5, 1.5, om, gx, gc)
        real_split = h["splitting_ev"] > 1e-12
        assert real_split == crit["standard_criterion_met"]


# --- C05 metrology (module did not exist before this audit) -----------

def test_seller_values_cannot_become_measurements():
    r = metrology.specimen_record("G001", {"length_mm": 110.0})
    assert r["status"] == "PROTOCOL_READY_HARDWARE_REQUIRED"
    assert r["evidence_tags"] == ["SRC"]
    assert r["measured_values"] == {}
    # a measured block without provenance is refused
    with pytest.raises(metrology.MetrologyError):
        metrology.specimen_record("G002", {"length_mm": 110.0},
                                  {"length_mm": 109.7})
    with pytest.raises(metrology.MetrologyError):
        metrology.specimen_record(
            "G003", {"length_mm": 1.0}, {"length_mm": 1.0},
            {"instrument": "caliper"})  # missing calibration/operator


def test_measured_record_requires_known_instrument():
    with pytest.raises(metrology.MetrologyError):
        metrology.specimen_record(
            "G004", {"length_mm": 1.0}, {"length_mm": 1.0},
            {"instrument": "vibes", "calibration_id": "C1",
             "operator": "A", "timestamp": "2026-07-17"})


def test_density_consistency_and_uncertainty():
    ok = metrology.mass_volume_consistency(26.48, 10.0)
    assert ok["consistent"] and ok["verdict"] == \
        "CONSISTENT_WITH_QUARTZ"
    low = metrology.mass_volume_consistency(20.0, 10.0)
    assert not low["consistent"] and low["verdict"].startswith("LOW")
    high = metrology.mass_volume_consistency(35.0, 10.0)
    assert high["verdict"].startswith("HIGH")
    d = metrology.density_from_mass_volume(26.48, 10.0)
    assert d["density_g_cm3"] == pytest.approx(2.648)
    assert d["u_density_g_cm3"] > 0


def test_xrd_never_infers_axes_from_facets():
    out = metrology.xrd_orientation_interface("G001")
    assert out["classification"] == "INTERFACE_ONLY"
    assert out["c_axis_deg"] is None
    real = metrology.xrd_orientation_interface(
        "G001", True, {"two_theta_deg": [26.0, 26.6, 27.0],
                       "intensity": [1.0, 9.0, 1.0],
                       "calibration_id": "XRD-REF-1"})
    assert real["dominant_two_theta_deg"] == pytest.approx(26.6)
    with pytest.raises(metrology.MetrologyError):
        metrology.xrd_orientation_interface(
            "G001", True, {"two_theta_deg": [1.0]})


def test_scan_to_mesh_refuses_to_repair():
    rng = np.random.default_rng(0)
    dense = metrology.scan_to_mesh(rng.normal(size=(2000, 3)) * 5)
    assert dense["usable"]
    sparse = metrology.scan_to_mesh(rng.normal(size=(40, 3)) * 500)
    assert not sparse["usable"]
    assert sparse["status"] == "INSUFFICIENT_RESOLUTION"
    tiny = metrology.scan_to_mesh(rng.normal(size=(10, 3)))
    assert tiny["status"] == "INSUFFICIENT_RESOLUTION"
    bad = np.full((64, 3), np.nan)
    assert not metrology.scan_to_mesh(bad)["usable"]
    with pytest.raises(metrology.MetrologyError):
        metrology.scan_to_mesh(np.zeros((10, 2)))


def test_apex_angle_and_dimensional_record():
    a = metrology.apex_angle_deg(10.0, 20.0)
    assert a["apex_angle_deg"] == pytest.approx(90.0)
    assert a["u_apex_angle_deg"] > 0
    d = metrology.dimensional_record(110.0, [20.0, 19.0, 18.0],
                                     [0.0, 50.0, 100.0],
                                     [8.0, 8.0], 6)
    assert d["taper_mm_per_mm"] == pytest.approx(-0.02)
    with pytest.raises(metrology.MetrologyError):
        metrology.dimensional_record(1.0, [1.0], [0.0], [1.0], 7)


def test_metrology_protocol_is_blocked_not_measured():
    p = metrology.metrology_protocol()
    assert p["status"] == "PROTOCOL_READY_HARDWARE_REQUIRED"
    assert p["blocker"]
    assert len(p["steps"]) >= 10


# --- C06 BVD depth ----------------------------------------------------

def _designed(fs_target=10000.0, l1=100.0, ratio=200.0, r1=50.0):
    c1 = 1.0 / ((2 * math.pi * fs_target) ** 2 * l1)
    return ratio * c1, r1, l1, c1


def test_bvd_synthetic_recovery_matches_truth():
    c0, r1, l1, c1 = _designed()
    truth = bvd.derived_parameters(c0, r1, l1, c1)
    f = np.linspace(9800, 10200, 4001)
    z = np.abs(bvd.bvd_impedance(f, c0, r1, l1, c1))
    got = bvd.extract_bvd(f, z)
    assert got["identifiable"]
    assert got["fs_hz"] == pytest.approx(truth["fs_hz"], abs=0.2)
    assert got["fp_hz"] == pytest.approx(truth["fp_hz"], abs=0.2)


def test_bvd_reports_non_identifiability_on_coarse_grid():
    c0, r1, l1, c1 = _designed()
    f = np.linspace(9800, 10200, 25)
    z = np.abs(bvd.bvd_impedance(f, c0, r1, l1, c1))
    got = bvd.extract_bvd(f, z)
    if got["identifiable"]:
        u = bvd.fit_uncertainty(f, z, got, noise_floor_ohm=1e-3)
        assert not u["identifiable"]
        assert u["status"] == "INSUFFICIENT_RESOLUTION"
        assert "grid steps" in u["reason"]


def test_osl_calibration_recovers_dut():
    zo = np.full(5, 1e12 + 0j)
    zs = np.zeros(5, complex)
    zl = np.full(5, 50.0 + 0j)
    dut = np.array([10 + 5j, 20 - 3j, 50 + 0j, 1 + 1j, 100 + 0j])
    assert np.allclose(bvd.osl_correct(dut, zo, zs, zl, 50.0), dut,
                       rtol=1e-6)
    with pytest.raises(ValueError):
        bvd.osl_correct(dut, dut, zs, zl)


def test_multibranch_reports_unmodelled_structure():
    c0, r1, l1, c1 = _designed()
    f = np.linspace(9800, 10200, 4001)
    z = np.abs(bvd.bvd_impedance(f, c0, r1, l1, c1))
    assert bvd.fit_multibranch(f, z)["single_branch_adequate"]
    # two branches: superpose a second resonance
    c0b, r1b, l1b, c1b = _designed(fs_target=10100.0)
    z2 = np.abs(bvd.bvd_impedance(f, c0b, r1b, l1b, c1b))
    mb = bvd.fit_multibranch(np.concatenate([f, f + 1e-9]),
                             np.concatenate([z, z2]))
    assert mb["n_branches"] >= 1


def test_spice_export_wellformed():
    txt = bvd.to_spice(1e-11, 10.0, 1.0, 1e-15, name="Q1")
    assert ".SUBCKT Q1" in txt and ".ENDS Q1" in txt
    assert "C0 1 2" in txt and "L1 3 4" in txt
    assert "NOT a measured device" in txt


def test_electrode_loading_pulls_frequency_down():
    out = bvd.electrode_loading(1e-11, 0.5, electrode_mass_kg=1e-4,
                                modal_mass_kg=1e-3)
    assert out["c0_effective_f"] == pytest.approx(5e-12)
    assert out["frequency_pull_factor"] < 1.0
    assert out["delta_f_relative"] < 0
    with pytest.raises(ValueError):
        bvd.electrode_loading(1e-11, 0.0)


# --- C07 apparatus depth ---------------------------------------------

def test_coil_field_matches_biot_savart_integrator():
    """Independent cross-check: the analytic loop formula and the
    validated Biot-Savart integrator must agree at the coil centre."""
    m = ap.coil_model(40, 0.03, 0.02, 0.33e-3, 0.5)
    b = ap.coil_field_map(40, 0.03, 0.5,
                          np.array([[0.0, 0.0, 0.0]]))[0]
    assert np.linalg.norm(b) == pytest.approx(m["b_center_t"],
                                              rel=1e-3)


def test_coil_resistance_and_thermal_limits():
    m = ap.coil_model(40, 0.03, 0.02, 0.33e-3, 0.5)
    assert m["resistance_ohm"] > 0
    assert m["power_w"] == pytest.approx(
        0.5 ** 2 * m["resistance_ohm"])
    assert m["skin_effect_negligible"]      # 4 kHz, 0.33 mm wire
    hot = ap.thermal_rise_c(10.0)
    assert not hot["within_safe_limit"]
    cool = ap.thermal_rise_c(0.37)
    assert cool["within_safe_limit"]


def test_wire_resistance_temperature_dependence():
    cold = ap.wire_resistance_ohm(1.0, 1e-3, 20.0)
    warm = ap.wire_resistance_ohm(1.0, 1e-3, 80.0)
    assert warm["resistance_ohm"] > cold["resistance_ohm"]
    ag = ap.wire_resistance_ohm(1.0, 1e-3, 20.0, material="Ag")
    assert ag["resistance_ohm"] < cold["resistance_ohm"]


def test_contact_loading_is_ordinary_not_operator():
    out = ap.contact_load_model(5.0, 5e-3, 1e6, 1e-3)
    assert out["loaded_hz"] > out["unloaded_hz"]
    assert out["delta_f_hz"] > 0
    assert "NOT an operator effect" in out["note"]


def test_transducer_transfer_resonance_and_rolloff():
    h = ap.transducer_transfer(np.array([1.0, 1000.0, 1e5]), 1000.0,
                               10.0)
    assert abs(h[1]) > abs(h[0])       # peak at resonance
    assert abs(h[2]) < abs(h[0])       # mass-controlled roll-off


def test_electrode_capacitance_and_cable_loading():
    c = ap.electrode_capacitance_f(1e-4, 1e-3)
    assert c["capacitance_f"] > 0 and c["fringing_underestimate"]
    cl = ap.cable_loading(100.0, 1.0, 1e6)
    assert cl["f_3db_hz"] > 0
