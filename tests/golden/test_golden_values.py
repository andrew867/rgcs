"""Golden-value tests from SOURCE_EVIDENCE_LEDGER.md Part E (G-01..G-15).

These constants are Derived and versioned (policy section 3.5); each test
names its ledger row.
"""

from __future__ import annotations

import math

import pytest

from rgcs_core.harmonics import (axial_half_wave, ladder_length_mm,
                                 harmonic_classification)
from rgcs_core.compact_modes import compact_mode_spectrum
from rgcs_core.resonance import resonance_offset
from rgcs_core.coupled_modes import coupled_two_mode
from rgcs_core.loading import loading_factor, added_modal_mass_g
from rgcs_core.geometry import (SpiralGeometry, spiral_pitch_parameter,
                                spiral_metrics, angle_audit, node_prior_mm,
                                female_to_male_frame_mm)
from rgcs_core.drive import drive_sequence, micro_pulse_metrics, \
    phase_residue_cycles
from rgcs_core.experiments import current_to_electron_rate
from rgcs_core.coherence import phase_rate_shear_scalar


def test_g01_ladder_constant():
    assert ladder_length_mm(1).mean == pytest.approx(770.263671875,
                                                     abs=1e-9)


def test_g02_l5():
    assert ladder_length_mm(5).mean == pytest.approx(154.052734375,
                                                     abs=1e-9)


def test_g03_l7():
    assert ladder_length_mm(7).mean == pytest.approx(110.037667410714,
                                                     abs=1e-9)


def test_g04_f_ax_110mm():
    f = axial_half_wave(110.0)
    assert f.mean == pytest.approx(28681.8181818, abs=1e-6)
    err_hz = f.mean - 7 * 4096.0
    assert err_hz == pytest.approx(9.81818, abs=1e-4)
    assert 100.0 * err_hz / (7 * 4096.0) == pytest.approx(0.0342431,
                                                          abs=1e-6)


def test_g05_f_ax_116mm():
    hc = harmonic_classification(116.0)
    assert hc["axial_frequency_hz"]["mean"] == pytest.approx(27198.2758621,
                                                             abs=1e-6)
    assert hc["n_eff"] == pytest.approx(6.640204, abs=1e-6)
    assert 100.0 * hc["frequency_error_fraction"] == pytest.approx(-5.1399,
                                                                   abs=1e-3)


def test_g06_compact_n1():
    s = compact_mode_spectrum(0.0, v_chi=6310.0, compact_radius_mm=100.0,
                              n_max=1)
    assert s["modes"][0]["frequency"]["mean"] == pytest.approx(
        10042.6769091, abs=1e-6)


def test_g07_epsilon_zero():
    assert resonance_offset(40960.0, 20480.0, 2.0) == 0.0


def test_g08_two_mode_hybrids():
    r = coupled_two_mode(1000.0, 1000.0, 10.0)
    assert r["lower_hybrid_hz"] == pytest.approx(990.0, abs=1e-12)
    assert r["upper_hybrid_hz"] == pytest.approx(1010.0, abs=1e-12)
    assert r["splitting_hz"] == pytest.approx(20.0, abs=1e-12)


def test_g09_loading():
    k_h = loading_factor(152.0, 154.052734375)   # ratio of like quantities
    assert k_h == pytest.approx(0.9866751189, abs=1e-9)
    dm = added_modal_mass_g(k_h, 154.0, 0.5)["added_modal_mass_g"]
    assert dm == pytest.approx(2.0937873, abs=1e-4)


def test_g10_spiral_invariants():
    assert spiral_pitch_parameter(math.e) == pytest.approx(0.15915494309,
                                                           abs=1e-11)
    m = spiral_metrics(SpiralGeometry(q_per_turn=math.e))
    assert m["curvature_invariant_rkappa"] == pytest.approx(0.98757049215,
                                                            abs=1e-11)
    assert m["scale_rotation_eigenvalue"] == pytest.approx(
        complex(-0.15915494309, 1.0), abs=1e-10)


def test_g11_angle_audit():
    out = angle_audit(51.843)
    assert out["atan_sqrt_phi_deg"] == pytest.approx(51.8272923730,
                                                     abs=1e-9)
    assert out["delta_atan_sqrt_phi_deg"] == pytest.approx(-0.015708,
                                                           abs=1e-5)


@pytest.mark.parametrize("mode,total,allocation,exact_ms", [
    ("standard", 2261, (754, 754, 753), 552.001953125),
    ("half_spacing", 1508, (754, 377, 377), 368.1640625),
    ("double_rate", 1131, (377, 377, 377), 276.123046875),
])
def test_g12_drive_families(mode, total, allocation, exact_ms):
    d = drive_sequence(mode)
    assert d["exact_cycles"] == total
    assert (d["on_total_cycles"], d["spacing_total_cycles"],
            d["pause_cycles"]) == allocation
    assert d["exact_macro_ms"] == pytest.approx(exact_ms, abs=1e-9)


def test_d13_phase_residue_half_spacing():
    # r_phi = +0.328 cycles for nominal 1507.328 (D-13; sign is POSITIVE).
    d = drive_sequence("half_spacing")
    assert d["nominal_cycles"] == pytest.approx(1507.328, abs=1e-9)
    assert d["phase_residue_cycles"] == pytest.approx(+0.328, abs=1e-9)
    assert phase_residue_cycles(1507.328) > 0


def test_g13_coil_inference():
    m = micro_pulse_metrics(voltage_v=60.0, rise_time_us=1.3,
                            peak_current_a=3.0)
    assert m["inferred_inductance_uh"] == pytest.approx(26.0, abs=1e-9)
    assert m["stored_energy_uj"] == pytest.approx(117.0, abs=1e-9)


def test_g14_electron_count_correction():
    # 1e-14 A = 62,415.09 e/s, NOT 2,000 (RG-15).
    rate = current_to_electron_rate(1e-14)
    assert rate == pytest.approx(62415.09, abs=0.01)
    assert rate / 2000.0 == pytest.approx(31.2, abs=0.01)


def test_g15_shear_scalar_identity():
    assert phase_rate_shear_scalar(3.0, 3.0, 3.0)["sigma_phi2_s2"] == 0.0
    s = phase_rate_shear_scalar(1.0, 2.0, 3.0)
    assert s["sigma_phi2_s2"] == pytest.approx(
        ((1 - 2) ** 2 + (2 - 3) ** 2 + (3 - 1) ** 2) / 3.0)


def test_node_frame_pair():
    # x_g = 78.3277 mm (female frame); 75.7250 mm is the SAME point in the
    # male frame (D-01 resolution) — not a separate estimator.
    xg = node_prior_mm(154.052734, 17.415434, 14.812763)
    assert xg == pytest.approx(78.3277, abs=1e-3)
    assert female_to_male_frame_mm(xg, 154.052734) == pytest.approx(
        75.7250, abs=1e-3)
