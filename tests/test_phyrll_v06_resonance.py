"""v0.6 carrier and coupled power -- including the wall-power refusal."""

from __future__ import annotations

import math
from fractions import Fraction as F

import pytest

from rgcs_phyrll_v06 import resonance as Z
from rgcs_phyrll_v06 import force_firewall as FW


def test_the_exact_scheduler_relation():
    assert Z.F_EXT == 4096 * 411 == 1683456
    assert Z.ratio_is_11_plus_4_over_37()
    assert F(411, 37) == 11 + F(4, 37)


def test_per_cell_phase_matches_the_declared_form():
    t, k, phi0 = 1.7e-6, 11, 0.3
    phi_k = 2 * math.pi * k / 37
    manual = 0.8 * math.cos(2 * math.pi * Z.F_EXT * t - 4 * phi_k + phi0)
    assert Z.cell_current(t, k, 1, 0.8, phi0) == pytest.approx(manual)


def test_inactive_cell_carries_no_current():
    assert Z.cell_current(1e-6, 5, active=0) == 0.0


def test_winding_advances_m_times_cell_pitch():
    """Adjacent cells differ in phase by exactly m*2*pi/N."""
    snap = Z.winding_snapshot(t=0.0)
    for k in (0, 10, 20):
        expect = math.cos(4 * 2 * math.pi * (k + 1) / 37 * -1)
        assert snap[k + 1] == pytest.approx(math.cos(-4 * 2 * math.pi
                                                     * (k + 1) / 37))


def test_stored_energy_and_ring_power_bookkeeping():
    u = Z.stored_energy(l_eff=1e-3, i_rms=2.0, c_eff=1e-9, v_rms=100.0)
    assert u["U_L"] == pytest.approx(4e-3)
    assert u["U_C"] == pytest.approx(1e-5)
    p = Z.ring_power(u["U"], q_factor=50.0)
    assert p == pytest.approx(2 * math.pi * Z.F_EXT * u["U"] / 50.0)


def test_wall_power_is_refused_without_a_declared_coupling():
    """The rule the spec singles out: eta never applies to wall power."""
    with pytest.raises(ValueError, match="eta_couple is undeclared"):
        Z.ring_power_from_wall(100.0)


def test_wall_power_with_declared_coupling_is_scaled():
    assert Z.ring_power_from_wall(100.0, eta_couple=0.25) == 25.0
    with pytest.raises(ValueError):
        Z.ring_power_from_wall(100.0, eta_couple=1.5)


def test_force_relation_is_tagged_bench_required():
    r = Z.force_coefficient_relation(0.01, 10.0)
    assert r["force_N"] == pytest.approx(0.1)
    assert r["claim"] == "BENCH_REQUIRED"


def test_power_sweep_is_monotone_in_current():
    rows = Z.power_sweep(1e-3, 1e-9, 50.0, [0.5, 1.0, 2.0], 100.0, 0.01)
    powers = [r["P_ring_W"] for r in rows]
    assert powers == sorted(powers)


# ---- firewall (delegating to the audited r1070tb lane) ----

def test_even_odd_decomposition_matches_the_audit_form():
    r = FW.even_odd_decomposition(7.0, 3.0)
    assert r["even"] == 5.0 and r["odd"] == 2.0


def test_third_harmonic_isolates_the_cubic_coefficient():
    h = FW.harmonic_coefficients(v_dc=0.0, v_ac=2.0, a1=1.0, a2=1.0, a3=0.5)
    assert h["h3"] == pytest.approx(0.5 * 8.0 / 4.0)
    h0 = FW.harmonic_coefficients(0.0, 2.0, 5.0, 5.0, 0.0)
    assert h0["h3"] == 0.0


def test_harmonics_reconstruct_the_polynomial_at_phase_zero():
    """DC + h1 + h2 + h3 must equal the polynomial at cos=1 (Vdc+Vac)."""
    vdc, vac, a1, a2, a3 = 0.7, 1.3, 2.0, -0.4, 0.9
    h = FW.harmonic_coefficients(vdc, vac, a1, a2, a3)
    v = vdc + vac
    poly = a1 * v + a2 * v ** 2 + a3 * v ** 3
    assert h["dc"] + h["h1"] + h["h2"] + h["h3"] == pytest.approx(poly)


def test_ehd_estimator_delegates_to_the_audited_lane():
    r = FW.ehd_drift_force(1e-6, 0.05, 2e-4)
    from r1070tb.sources import arl_force_from_mobility
    assert r["force_N"] == arl_force_from_mobility(1e-6, 0.05, 2e-4)
    assert r["vanishes_in_vacuum"] is True


def test_unmeasured_artifact_budget_blocks_any_residual_quote():
    b = FW.artifact_budget()
    assert b["budget_measured"] is False
    assert b["residual_quotable"] is False
    b2 = FW.artifact_budget(uncertainty_N=1e-6)
    assert b2["residual_quotable"] is True
