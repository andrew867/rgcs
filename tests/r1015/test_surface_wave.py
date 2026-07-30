"""R10.15 — surface-wave research package tests (Phases A03-E30)."""

import math

import numpy as np
import pytest

from rgcs_surface_wave import FORBIDDEN_CLAIM_TERMS, NONCLAIM
from rgcs_surface_wave.evidence import (Claim, ClaimClass, ClaimError,
                                        SOFTWARE_EMITTABLE, taxonomy)


# ------------------------------------------------------------- A03
def test_claim_taxonomy_classes():
    t = taxonomy()
    assert set(t["classes"]) == {"ESTABLISHED", "DERIVED", "SIMULATED",
                                 "HYPOTHESIS", "SOURCE_PROVENANCE",
                                 "NULL", "REPLICATION_REQUIRED"}
    assert ClaimClass.ESTABLISHED not in SOFTWARE_EMITTABLE


@pytest.mark.parametrize("term", list(FORBIDDEN_CLAIM_TERMS))
def test_forbidden_claim_terms_rejected(term):
    with pytest.raises(ClaimError):
        Claim(f"the device demonstrates {term} in simulation",
              ClaimClass.SIMULATED, "sim")


def test_valid_claim_records():
    c = Claim("the m=1 mask amplitude sets the net lateral force",
              ClaimClass.DERIVED, "angular orthogonality")
    assert c.record()["claim_class"] == "DERIVED"
    assert "antigravity" in NONCLAIM


# ------------------------------------------------------------- B07
def test_geometry_validation_and_candidates():
    from rgcs_surface_wave.geometry import (CANDIDATE, GeometryError,
                                            candidate_geometry, validate)
    geo = candidate_geometry()
    assert geo.cells == 35 and len(geo.active_cells) == 33
    assert abs(geo.area_ratio - 29 / 89) < 1e-9
    assert not geo.has_diametric_pair()          # odd cell count
    v = validate(geo)
    assert v["ok"] and any("odd" in n for n in v["notes"])
    assert CANDIDATE["claim_class"] == "SOURCE_PROVENANCE"
    with pytest.raises(GeometryError):
        candidate_geometry().__class__(
            inner_radius_m=0.2, outer_radius_m=0.1, thickness_m=1e-3)


def test_geometry_rejects_bad_dielectric():
    from rgcs_surface_wave.geometry import DielectricSlab, GeometryError
    with pytest.raises(GeometryError):
        DielectricSlab(1e-3, 1e-3, epsilon_r=0.5)
    with pytest.raises(GeometryError):
        DielectricSlab(-1e-3, 1e-3, epsilon_r=4.0)
    slab = DielectricSlab(1e-3, 3e-3, 4.4, 0.02)
    assert slab.epsilon_complex.imag < 0          # passive loss


# ------------------------------------------------------- B08/B09/B12
def test_mask_exact_arithmetic_and_parseval():
    from rgcs_surface_wave.masks import (coefficient, spectrum,
                                         two_gap_closed_form)
    active = [j for j in range(35) if j not in (0, 1)]
    sp = spectrum(35, active, m_max=6)
    assert sp["parseval_residual"] < 1e-14
    assert abs(sp["parseval_rhs"] - 33 / 35) < 1e-15
    for m in (1, 2, 5, 17, 35):
        a = two_gap_closed_form(35, 0, 1, m)
        b = coefficient(35, active, m)
        assert abs(a - b) < 1e-12, m


def test_mask_m1_magnitude_closed_form():
    """|M_1| = (2/N)|cos(dphi/2)| for a two-gap mask."""
    from rgcs_surface_wave.masks import two_gap_closed_form
    for g1, g2 in ((0, 1), (0, 7), (0, 17)):
        d = 2 * math.pi * (g2 - g1) / 35
        expect = (2 / 35) * abs(math.cos(d / 2))
        assert abs(abs(two_gap_closed_form(35, g1, g2, 1)) - expect) < 1e-12


def test_aperture_shape_factor_exact():
    from rgcs_surface_wave.masks import aperture_shape_factor
    assert aperture_shape_factor(0, 0.1) == 1.0
    w = 2 * math.pi / 35
    x = 0.5 * 3 * w
    assert abs(aperture_shape_factor(3, w) - math.sin(x) / x) < 1e-15


def test_null_library_and_impossible_diametric():
    from rgcs_surface_wave.masks import null_library
    lib = null_library(35)
    masks = lib["masks"]
    assert masks["all_active"]["m1"] < 1e-15
    assert masks["exact_diametric_gaps"]["status"] == "IMPOSSIBLE"
    assert masks["adjacent_gaps"]["m1"] > masks[
        "nearest_diametric_gaps"]["m1"] * 20


def test_radial_profile_refuses_unknown():
    from rgcs_surface_wave.masks import MaskError, radial_shape_factor
    assert radial_shape_factor(0.08, 0.14, "uniform") == 1.0
    with pytest.raises(MaskError, match="declared profiles"):
        radial_shape_factor(0.08, 0.14, "mystery")


# ------------------------------------------------------------- B10
@pytest.mark.parametrize("kind", ["sinusoidal", "stepped", "pwm",
                                  "traveling", "reversed", "sham",
                                  "randomized"])
def test_temporal_waveforms_parseval(kind):
    from rgcs_surface_wave.temporal import coefficients
    c = coefficients(kind, n_max=8, duty=0.6)
    assert c["parseval_residual"] < 1e-12
    if c["analytic_available"]:
        assert c["analytic_max_deviation"] < 1e-3


def test_temporal_dft_quadrature_converges():
    """The stepped-wave DFT error must fall as 1/n_samples."""
    from rgcs_surface_wave.temporal import coefficients
    e1 = coefficients("stepped", n_samples=1024)["analytic_max_deviation"]
    e2 = coefficients("stepped", n_samples=4096)["analytic_max_deviation"]
    assert e2 < e1 / 3.0


def test_sham_is_a_valid_control():
    from rgcs_surface_wave.temporal import coefficients, sham_matches
    ref = coefficients("stepped", duty=0.5)
    sham = coefficients("sham", duty=0.5)
    m = sham_matches(ref, sham)
    assert m["valid_control"]
    assert sham["modulation_depth_effective"] == 0.0


def test_unknown_waveform_refuses():
    from rgcs_surface_wave.temporal import TemporalError, coefficients
    with pytest.raises(TemporalError, match="declared waveforms"):
        coefficients("sawtooth")


# ----------------------------------------------------- multi-rate
def test_rate_architecture_exact_integers():
    from rgcs_surface_wave.rates import architecture
    a = architecture()
    assert (a["f_passage_total_hz"], a["f_passage_active_hz"],
            a["f_passage_gap_hz"]) == (560, 528, 32)
    assert a["phase_states"] == 125
    assert a["phase_step_deg"] == 2.88
    assert a["timing_step_us"] == 1.953125
    assert a["phase_states_tile_one_carrier_period"] is True
    assert a["f_surface_wave_hz"] is None


def test_f_sw_must_be_derived_not_assumed():
    from rgcs_surface_wave.rates import (RateError, controlled_candidate,
                                         surface_wave_frequency)
    with pytest.raises(RateError, match="not a drive rate"):
        surface_wave_frequency()
    c = controlled_candidate(4096.0)
    assert c["status"] == "CONTROLLED_CANDIDATE_UNDER_TEST"
    assert c["claim_class"] == "HYPOTHESIS"


# ------------------------------------------------------- C13/C14/C15
def test_unit_cell_dispersion_bound_branch():
    from rgcs_surface_wave.impedance import solve_unit_cell
    r = solve_unit_cell(1e9, depth_m=5e-3, aperture_fraction=0.5,
                        period_m=5e-3)
    assert r["bound_surface_wave"]
    assert r["slow_wave_factor"] > 1.0
    assert abs(r["dispersion_residual"]) < 1e-6 * r["k_x_rad_per_m"] ** 2
    assert r["confinement_length_m"] > 0


def test_eigenmode_limits_match_bessel_zeros():
    """Ri -> 0 must reproduce the disk (J_m zeros) for m >= 1."""
    from scipy.special import jn_zeros

    from rgcs_surface_wave.eigenmodes import radial_roots
    Ro = 0.1
    for m in (1, 2, 3):
        got = radial_roots(m, 1e-5 * Ro, Ro, 2)
        want = jn_zeros(m, 2) / Ro
        assert abs(got[0] - want[0]) / want[0] < 1e-6, m


def test_eigenmode_m0_log_convergence_is_documented():
    """m=0 converges only logarithmically because Y_0 ~ ln(x); this is
    a property of the problem, recorded rather than hidden."""
    from scipy.special import jn_zeros

    from rgcs_surface_wave.eigenmodes import radial_roots
    Ro = 0.1
    want = jn_zeros(0, 1)[0] / Ro
    e_coarse = abs(radial_roots(0, 1e-3 * Ro, Ro, 1)[0] - want) / want
    e_fine = abs(radial_roots(0, 1e-8 * Ro, Ro, 1)[0] - want) / want
    assert e_fine < e_coarse            # improves, but slowly
    assert e_fine > 1e-4                # and does NOT reach 1e-6


def test_thin_annulus_reduces_to_slab():
    from rgcs_surface_wave.eigenmodes import radial_roots
    Ri, Ro = 0.0999, 0.1000
    roots = radial_roots(1, Ri, Ro, 2)
    for p, k in enumerate(roots, start=1):
        assert abs(k * (Ro - Ri) - p * math.pi) < 1e-3


def test_annular_modes_derive_f_sw():
    from rgcs_surface_wave.eigenmodes import annular_modes
    from rgcs_surface_wave.geometry import candidate_geometry
    res = annular_modes(candidate_geometry(), m_values=(0, 1),
                        n_roots=1)
    f = res["f_surface_wave_derived_hz"]
    assert 1e8 < f < 1e10                # hundreds of MHz to GHz
    assert res["modes"][0]["determinant_residual"] < 1e-12
    assert res["modes"][0]["q_radiation"] is None
    assert "UPPER BOUND" in res["modes"][0]["q_radiation_status"]


def test_4096hz_candidate_is_falsified_as_carrier():
    """The R10.15 override's controlled test."""
    from rgcs_surface_wave.eigenmodes import test_candidate_carrier
    from rgcs_surface_wave.geometry import candidate_geometry
    t = test_candidate_carrier(candidate_geometry(), 4096.0)
    assert t["verdict"] == "FALSIFIED_AS_ELECTROMAGNETIC_CARRIER"
    assert t["circumference_in_wavelengths"] < 1e-4
    assert t["required_slow_wave_factor_for_m1"] > 1e4
    assert t["claim_class"] == "NULL"


def test_required_slow_wave_factor_is_unphysical_at_4096hz():
    from rgcs_surface_wave.impedance import required_slow_wave_factor
    r = required_slow_wave_factor(4096.0, 0.71, 1)
    assert not r["physically_reasonable"]
    assert r["required_groove_depth_m"] > 1e3      # kilometres


# ------------------------------------------------------- C16/C17
def test_floquet_coefficients_parseval():
    from rgcs_surface_wave.floquet import combined_coefficients
    c = combined_coefficients(35, [j for j in range(35) if j > 1],
                              "sinusoidal", m_max=4, n_max=3)
    assert c["parseval_residual"] < 1e-12
    assert c["separable"]


def test_sidebands_do_not_imply_force():
    from rgcs_surface_wave.floquet import solve_sidebands
    mf = {0: 1.15e9, 1: 1.17e9}
    sb = solve_sidebands(mf, 50.0, 1.17e9, 16.0, 35,
                         [j for j in range(35) if j > 1])
    assert "REFUSED" in sb["force_inference"]
    assert sb["carrier_amplitude"] > 0


def test_nonreciprocity_null_in_quasi_static_regime():
    from rgcs_surface_wave.floquet import nonreciprocity
    mf = {0: 1.15e9, 1: 1.17e9}
    nr = nonreciprocity(mf, 50.0, 1.17e9, 16.0, 35,
                        [j for j in range(35) if j > 1])
    assert nr["regime"] == "QUASI_STATIC_UNRESOLVED"
    assert nr["verdict"] == "NO_MEASURABLE_NONRECIPROCITY"
    assert nr["claim_class"] == "NULL"


def test_scale_separation_requires_impossible_q():
    from rgcs_surface_wave.rates import scale_separation
    s = scale_separation(1.15e9, 49.0, 16.0)
    assert not s["sidebands_resolved"]
    assert s["q_required_to_resolve"] > 1e7
    assert s["regime"] == "QUASI_STATIC_UNRESOLVED"


# --------------------------------------------------- D19/D20 + E25
def test_manufactured_solutions_all_pass():
    from rgcs_surface_wave.manufactured import run_all
    r = run_all()
    assert r["all_passed"], [c for c in r["cases"] if not c["passed"]]
    by = {c["case"]: c for c in r["cases"]}
    assert by["M1_charge_in_uniform_field"]["relative_error"] < 1e-9
    assert by["M2_two_point_charges"]["relative_error"] < 1e-9
    assert by["M4_pair_momentum_closure"]["relative_residual"] < 1e-9


def test_open_surface_refused():
    from rgcs_surface_wave.stress import (StressError, integrate_force,
                                          sphere_surface)
    surf = sphere_surface(0.05, n_theta=20, n_phi=40)
    n = len(surf["weights"])
    open_surf = {**surf, "points": surf["points"][: n // 2],
                 "normals": surf["normals"][: n // 2],
                 "weights": surf["weights"][: n // 2], "closed": False}
    with pytest.raises(StressError, match="not closed"):
        integrate_force(open_surf, lambda p: np.zeros_like(p),
                        lambda p: np.zeros_like(p))


def test_static_force_for_modulated_system_refused():
    from rgcs_surface_wave.stress import (StressError,
                                          refuse_static_force_for_modulated_system)
    with pytest.raises(StressError, match="static field solution"):
        refuse_static_force_for_modulated_system(True, True)
    refuse_static_force_for_modulated_system(False, True)     # allowed


def test_q_multiplied_thrust_refused_everywhere():
    from rgcs_surface_wave.energy import thrust_from_q
    from rgcs_surface_wave.stress import refuse_q_multiplied_thrust
    for fn in (refuse_q_multiplied_thrust, thrust_from_q):
        with pytest.raises(ClaimError, match="Q"):
            fn(1e6, 1.0)


def test_stress_dimensional_convention():
    from rgcs_surface_wave.geometry import EPS0, MU0
    from rgcs_surface_wave.stress import dimensional_check
    d = dimensional_check(EPS0, MU0)
    assert d["ok"] and "never B B without mu" in d["convention"]


def test_polarity_reversal_gives_even_parity():
    """Maxwell stress is quadratic: reversing drive cannot flip force."""
    from rgcs_surface_wave.manufactured import (point_charge_field,
                                                superpose, uniform_field,
                                                zero_field)
    from rgcs_surface_wave.stress import (polarity_reversal_invariance,
                                          sphere_surface)
    E = superpose(point_charge_field(1e-9, (0, 0, 0)),
                  uniform_field((0.0, 0.0, 1e3)))
    p = polarity_reversal_invariance(E, zero_field,
                                     sphere_surface(0.05, n_theta=40,
                                                    n_phi=80))
    assert p["parity"] == "EVEN" and p["invariant_as_required"]


# ------------------------------------------------------- D21/D22
def test_momentum_ledger_closes_and_refuses_partial():
    from rgcs_surface_wave.momentum import MomentumError, close
    led = close({"annulus": [1e-9, 0, 0], "dielectric": [2e-10, 0, 0],
                 "supports": [-1.2e-9, 0, 0], "enclosure": [0, 0, 0]})
    assert led["status"] == "GREEN"
    with pytest.raises(MomentumError, match="missing"):
        close({"annulus": [1e-9, 0, 0]})


def test_momentum_ledger_red_when_unbalanced():
    from rgcs_surface_wave.momentum import close
    led = close({"annulus": [1e-9, 0, 0], "dielectric": [0, 0, 0],
                 "supports": [0, 0, 0], "enclosure": [0, 0, 0]})
    assert led["status"] == "RED"
    assert "does NOT close" in led["interpretation"]


def test_energy_ledger_rejects_negative_loss():
    from rgcs_surface_wave.energy import EnergyError, close
    with pytest.raises(EnergyError, match="cannot generate energy"):
        close(1.0, 0.0, 0.0, {"conductor": -0.5})
    with pytest.raises(EnergyError, match="unknown loss channels"):
        close(1.0, 0.0, 0.0, {"magic": 0.5})


def test_energy_q_is_a_ratio_only():
    from rgcs_surface_wave.energy import q_from_energy, stored_energy
    u = stored_energy(1e3, 1e-5, 4.4)
    q = q_from_energy(u["u_total_j"], 1e-6, 1e9)
    assert q["q"] > 0 and "must not multiply" in q["forbidden_use"]


# ------------------------------------------------------------- D24
def test_artifact_budget_and_controls():
    from rgcs_surface_wave.artifacts import budget, ion_wind_thrust
    b = budget(1e-12)
    assert b["verdict"] == "CANDIDATE_BELOW_ARTIFACT_FLOOR"
    assert "hard vacuum (removes ion wind and convection)" in \
        b["required_controls"]
    iw = ion_wind_thrust(1e-6, 1e-3)
    assert iw["force_n"] > 0 and "vacuum" in iw["note"]


def test_radiation_pressure_has_no_q_factor():
    from rgcs_surface_wave.artifacts import radiation_pressure
    r = radiation_pressure(1.0)
    assert abs(r["force_n"] - 1.0 / 299792458.0) < 1e-18
    assert "not multiplied by Q" in r["note"]
    assert radiation_pressure(1.0, anisotropy=0.0)["force_n"] == 0.0


# ------------------------------------------------------- E25-E30
def test_axisymmetric_control_zero_lateral_force():
    from rgcs_surface_wave.cem import axisymmetric_control
    from rgcs_surface_wave.geometry import candidate_geometry
    r = axisymmetric_control(candidate_geometry())
    assert r["passed"]
    assert r["lateral_over_axial"] < 1e-12


def test_isolated_distribution_has_zero_self_force():
    from rgcs_surface_wave.cem import ring_static_model
    from rgcs_surface_wave.geometry import candidate_geometry
    r = ring_static_model(candidate_geometry())
    assert r["self_force_magnitude_n"] < 1e-20


def test_lateral_force_tracks_m1_amplitude():
    from rgcs_surface_wave.cem import mask_comparison
    from rgcs_surface_wave.geometry import candidate_geometry
    mc = mask_comparison(candidate_geometry())
    assert mc["m1_lateral_correlation"] > 0.999
    rows = {r["mask"]: r for r in mc["rows"]}
    assert rows["all_active"]["lateral_force_n"] < 1e-20
    assert rows["adjacent_gaps"]["lateral_force_n"] > \
        rows["nearest_diametric_gaps"]["lateral_force_n"]


def test_force_is_integration_surface_invariant():
    from rgcs_surface_wave.cem import convergence_study
    from rgcs_surface_wave.geometry import candidate_geometry
    cv = convergence_study(candidate_geometry())
    assert cv["surface_converged"] and cv["placement_converged"]
    ax = [r["axial_force_n"] for r in cv["surface_placement"]]
    assert max(ax) - min(ax) < 1e-12 * abs(ax[0])


def test_enclosure_invariant_enforced():
    from rgcs_surface_wave.cem import CemError, ring_static_model
    from rgcs_surface_wave.geometry import candidate_geometry
    with pytest.raises(CemError, match="encloses"):
        ring_static_model(candidate_geometry(),
                          surface_radius_factor=0.3)


def test_reduced_transient_matches_harmonic_balance():
    from rgcs_surface_wave.cem import reduced_transient
    t = reduced_transient(1.0e9, 30.0, 16.0)
    assert t["agree"], t["relative_difference"]
    assert t["cycles_integrated"] >= t["ring_up_cycles_required"]
    assert t["modulation_frozen_in_window"]


def test_independent_solver_cross_check():
    from rgcs_surface_wave.cem import cross_check_eigenmodes
    c = cross_check_eigenmodes(0.0822616, 0.1441097, m=1)
    assert c["agree"], c["max_relative_difference"]
    assert len(c["formulations"]) == 2


def test_ladder_status_declares_unexecuted_rungs():
    from rgcs_surface_wave.cem import ladder_status
    st = ladder_status()
    statuses = {r["name"]: r["status"] for r in st["rungs"]}
    assert statuses["full transient switching"] == "REDUCED_ORDER_ONLY"
    assert statuses["coupled structural/thermal/acoustic"] == \
        "NOT_EXECUTED"
    assert "no result in this release rests on a NOT_EXECUTED rung" \
        in st["rule"]


# ------------------------------------------------------------- F33
def test_receipts_hash_and_verify():
    from rgcs_surface_wave.receipts import make_receipt, verify_receipt
    r = make_receipt("test", {"a": 1}, {"b": 2},
                     ClaimClass.SIMULATED.value, ["limited"])
    assert verify_receipt(r)["ok"]
    assert r["publication_status"] == "HOLD"
    assert "not measurements" in r["nonclaim"]
    r["outputs"]["b"] = 3
    assert not verify_receipt(r)["ok"]
