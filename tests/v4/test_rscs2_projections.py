"""Agent 08: optical, coil, and drive projections (RSCS2-E.8..E.11).
Every physical law is anchored to a closed form or a FROZEN v3 value."""
from __future__ import annotations

import math

import numpy as np
import pytest

from rscs2_core import fem, projections as pj
from rscs2_core.crystal110 import build_crystal

C_M_S = 299_792_458.0


# --- optical -----------------------------------------------------------

def test_octave_presets_are_arithmetic():
    """The octave wavelengths are exactly c/2^49 and c/2^48; the ratio
    is exactly 2; the preset declares the arithmetic disclaimer."""
    g = pj.WAVELENGTH_PRESETS_NM["octave_green"]
    ir = pj.WAVELENGTH_PRESETS_NM["octave_ir"]
    assert g["nm"] == pytest.approx(C_M_S / 2.0 ** 49 * 1e9, rel=1e-14)
    assert ir["nm"] / g["nm"] == pytest.approx(2.0, rel=1e-14)
    assert g["nm"] == pytest.approx(532.538, abs=5e-3)
    assert ir["nm"] == pytest.approx(1065.077, abs=5e-3)
    for preset in (g, ir):
        assert "ARITHMETIC" in preset["origin"]
        assert "no coupling claim" in preset["origin"]


def test_sellmeier_reproduces_frozen_indices_at_sodium_d():
    """Conservative-extension anchor: Ghosh (1999) Sellmeier at
    589.3 nm reproduces the FROZEN handbook constants (D6-002)."""
    from rgcs_core.optics import QUARTZ_N_E, QUARTZ_N_O
    n = pj.quartz_sellmeier(589.3)
    assert n["n_o"] == pytest.approx(QUARTZ_N_O, abs=2e-4)
    assert n["n_e"] == pytest.approx(QUARTZ_N_E, abs=2e-4)
    # positive uniaxial at every preset wavelength
    for preset in pj.WAVELENGTH_PRESETS_NM.values():
        assert pj.quartz_sellmeier(preset["nm"])["birefringence"] > 0
    with pytest.raises(ValueError):
        pj.quartz_sellmeier(150.0)               # outside validity


def test_uniaxial_index_limits_and_monotone():
    n = pj.quartz_sellmeier(632.8)
    assert pj.uniaxial_index(0.0, n["n_o"], n["n_e"]) == \
        pytest.approx(n["n_o"], rel=1e-12)
    assert pj.uniaxial_index(math.pi / 2, n["n_o"], n["n_e"]) == \
        pytest.approx(n["n_e"], rel=1e-12)
    th = np.linspace(0, math.pi / 2, 20)
    vals = [pj.uniaxial_index(t, n["n_o"], n["n_e"]) for t in th]
    assert np.all(np.diff(vals) > 0)             # o -> e monotone


def test_vector_snell_matches_frozen_scalar_and_tir():
    """The vector refraction angle equals the frozen scalar law; the
    transmitted ray lies in the plane of incidence; TIR raises."""
    from rgcs_core.optics import snell_refraction
    nrm = np.array([0.0, 0.0, 1.0])              # outward normal
    d = np.array([math.sin(math.radians(30.0)), 0.0,
                  -math.cos(math.radians(30.0))])
    out = pj.refract_ray(d, nrm, 1.0, 1.5443)
    assert out["incidence_deg"] == pytest.approx(30.0, abs=1e-10)
    assert out["refraction_deg"] == pytest.approx(
        snell_refraction(30.0, 1.0, 1.5443), abs=1e-10)
    t = out["transmitted"]
    assert abs(t[1]) < 1e-14                     # plane of incidence
    assert math.degrees(math.acos(-np.dot(t, nrm))) == pytest.approx(
        out["refraction_deg"], abs=1e-9)
    with pytest.raises(ValueError):              # TIR going high->low
        pj.refract_ray(np.array([math.sin(1.2), 0, -math.cos(1.2)]),
                       nrm, 1.5443, 1.0)


def test_probe_paths_reciprocity_and_target_menu():
    """Axial tx->rx and rx->tx have identical OPL/phase (reciprocity,
    D6-003 posture); centre and node prior are distinct targets; the
    eye-candidate slot is None unless supplied."""
    c = build_crystal("ideal_n7")
    pp = pj.probe_paths(c, wavelength_nm=632.8)
    a, b = pp["paths"]["axial_tx_to_rx"], pp["paths"]["axial_rx_to_tx"]
    assert a["optical_path_length_mm"] == pytest.approx(
        b["optical_path_length_mm"], rel=1e-14)
    assert a["phase_rad"] == pytest.approx(b["phase_rad"], rel=1e-14)
    assert np.allclose(a["direction"], -b["direction"])
    assert a["geometric_length_mm"] == pytest.approx(c.length_mm)
    # target menu: centre != node prior (caps are asymmetric)
    tg = pp["targets"]
    assert tg["eye_candidate_mm"] is None
    dz = abs(tg["geometric_centre_mm"][2] - tg["node_prior_mm"][2])
    # frozen RGCS-M.39: x_g - L/2 = (h_f - h_m)/2 exactly
    assert dz == pytest.approx(
        abs(c.female_cap_height_mm - c.male_cap_height_mm) / 2.0,
        rel=1e-12)
    assert dz > 0.05                             # mm; distinct locations
    s1 = pp["paths"]["side_to_centre"]["geometric_length_mm"]
    s2 = pp["paths"]["side_to_node_prior"]["geometric_length_mm"]
    assert s1 != s2
    pp2 = pj.probe_paths(c, eye_candidate_mm=np.array([0, 0, 55.0]))
    assert "side_to_eye_candidate" in pp2["paths"]


def test_photoelastic_projection_closed_form():
    """Uniform strain S over path L: dphi = (2pi/lambda)(-1/2 n^3 p S)L,
    and the frozen docstring magnitude anchor dn(S=1e-7) ~ -3e-8."""
    from rgcs_core.optics import photoelastic_index_shift
    n, p, S, L_mm, lam = 1.5443, 0.16, 1e-7, 100.0, 632.8
    dn = photoelastic_index_shift(n, p, S)
    assert dn == pytest.approx(-0.5 * n ** 3 * p * S, rel=1e-12)
    assert dn == pytest.approx(-2.95e-8, rel=0.02)   # docstring anchor
    got = pj.photoelastic_phase_shift_rad(
        np.full(10, S), np.full(10, L_mm / 10), n, p, lam)
    want = 2 * math.pi * dn * (L_mm * 1e-3) / (lam * 1e-9)
    assert got == pytest.approx(want, rel=1e-12)


def test_jones_stokes_roundtrip_and_quarter_wave():
    """Frozen PolarizationState round-trips Jones<->Stokes; a quarter-
    wave plate at 45 deg turns x-linear light circular (|helicity|=1)."""
    from rscs_core.coordinates.medium import PolarizationState
    st = PolarizationState.from_jones(1.0, 0.5 + 0.2j)
    rt = PolarizationState.from_jones(*st.jones)
    assert np.allclose(rt.stokes, st.stokes, atol=1e-12)
    qwp = pj.jones_waveplate(math.pi / 2, fast_axis_deg=45.0)
    ex, ey = pj.apply_jones(qwp, 1.0, 0.0)
    out = PolarizationState.from_jones(ex, ey)
    assert abs(out.helicity) == pytest.approx(1.0, abs=1e-12)
    hwp = pj.jones_waveplate(math.pi, fast_axis_deg=22.5)
    ex2, ey2 = pj.apply_jones(hwp, 1.0, 0.0)     # x-linear -> 45-linear
    s = PolarizationState.from_jones(ex2, ey2).stokes
    assert s[1] == pytest.approx(1.0, abs=1e-12)


def test_absorption_proxy_limits():
    r = pj.absorption_deposition_w(5e-3, 0.0, 0.11)
    assert r["absorbed_w"] == 0.0                # transparent limit
    r2 = pj.absorption_deposition_w(5e-3, 1e6, 0.11)
    assert r2["absorbed_w"] == pytest.approx(5e-3, rel=1e-9)  # opaque
    assert "no temperature claim" in r["note"]


# --- coil --------------------------------------------------------------

def test_biot_savart_loop_vs_exact_on_axis():
    """Polyline integrator vs the exact single-loop on-axis field at
    z = 0, R, 2R; and off-axis midplane symmetry."""
    R, current = 0.05, 2.0
    coil = pj.circular_coil(R, n_segments=512)
    for z in (0.0, R, 2 * R):
        got = pj.biot_savart_polyline(coil, current,
                                      np.array([[0.0, 0.0, z]]))[0]
        assert got[2] == pytest.approx(pj.loop_axis_field_t(R, current, z),
                                       rel=1e-4)
        assert abs(got[0]) < 1e-12 and abs(got[1]) < 1e-12
    # handedness reverses the field
    rev = pj.circular_coil(R, n_segments=512, handedness=-1)
    g2 = pj.biot_savart_polyline(rev, current,
                                 np.array([[0.0, 0.0, 0.0]]))[0]
    assert g2[2] == pytest.approx(-pj.loop_axis_field_t(R, current, 0.0),
                                  rel=1e-4)


def test_coil_pair_opposed_vs_in_phase():
    """Counter-wound + electrically opposed = fields ADD on axis
    (double-negative); same-wound + opposed = cancel at the midpoint.
    Uses the FROZEN coil_pair_phases for the electrical part."""
    R, sep, cur = 0.04, 0.06, 1.0
    mid = np.array([[0.0, 0.0, 0.0]])
    addl = pj.coil_pair_field(mid, R, sep, cur, mode="opposed",
                              counter_wound=True)
    canc = pj.coil_pair_field(mid, R, sep, cur, mode="opposed",
                              counter_wound=False)
    assert abs(addl["phasor_t"][0, 2]) > 100 * abs(canc["phasor_t"][0, 2])
    assert addl["phases_deg"]["coil_b_deg"] == pytest.approx(180.0)
    inph = pj.coil_pair_field(mid, R, sep, cur, mode="in_phase",
                              counter_wound=False)
    single = pj.loop_axis_field_t(R, cur, sep / 2.0)
    assert abs(inph["phasor_t"][0, 2]) == pytest.approx(2 * single,
                                                        rel=1e-3)


def test_field_gradient_and_energy_density():
    """div B = 0 (trace of the gradient tensor vanishes) off the wire;
    energy density matches |B|^2/2mu0."""
    R, cur = 0.05, 1.0
    coil = pj.circular_coil(R, n_segments=256)
    pts = np.array([[0.01, 0.005, 0.02]])
    grad = pj.field_gradient(
        lambda p: pj.biot_savart_polyline(coil, cur, p), pts)
    B = pj.biot_savart_polyline(coil, cur, pts)
    div = np.trace(grad[0])
    assert abs(div) < 1e-6 * np.linalg.norm(grad[0])
    u = pj.magnetic_energy_density_j_m3(B)
    assert u[0] == pytest.approx(
        np.dot(B[0], B[0]) / (2 * 4e-7 * math.pi), rel=1e-12)


def test_modal_drive_projection_orthonormality():
    """Projecting F = M phi_k returns exactly the unit vector e_k
    (mass-orthonormal modes) — pins both the projection and the
    orthonormality of solve_modes output. A uniform x body force
    couples to bending modes with nonzero f_1."""
    mesh = fem.box_mesh((0.1, 0.01, 0.01), (10, 2, 2))
    prob = fem.assemble_isotropic(mesh, 210e9, 0.3, 7850.0)
    fixed = prob.basis.get_dofs(
        lambda x: np.isclose(x[0], 0.0)).flatten()
    sol = fem.solve_modes(prob, 5, fixed_dofs=fixed)
    k = 2
    F = prob.M @ sol["modes"][:, k]
    f = pj.project_force_vector(sol, F)
    want = np.zeros(5)
    want[k] = 1.0
    assert np.allclose(f, want, atol=1e-8)
    Fu = pj.assemble_body_force(
        prob, lambda x: np.stack([np.ones_like(x[0]),
                                  np.zeros_like(x[0]),
                                  np.zeros_like(x[0])]))
    fu = pj.project_force_vector(sol, Fu)
    assert np.max(np.abs(fu)) > 0                # couples to bending


def test_coupling_report_requires_leakage_control():
    with pytest.raises(ValueError, match="leakage control missing"):
        pj.coil_coupling_report("mode_1", 1.0, None)
    base = {"sensor_field_t": 1e-9, "sensor_point_m": [0, 0, 0.1]}
    rep = pj.coil_coupling_report("mode_1", 1.0, base)
    assert rep["leakage_control"]["sensor_field_t"] == 1e-9
    assert "exceed the leakage baseline" in rep["claim_gate"]


def test_capacitive_proxy_magnitude():
    """e11 * V/gap: 10 V over 28.6 mm -> ~0.171*350 = 59.8 Pa."""
    t = pj.capacitive_drive_traction_pa(10.0, 28.6e-3)
    assert t == pytest.approx(0.171 * 10.0 / 28.6e-3, rel=1e-12)


# --- timing ------------------------------------------------------------

def test_macro_sequences_golden_closures_and_honest_half_spacing():
    """Standard windows reproduce the frozen golden rows (125 ms,
    250 ms, 1 s); half-spacing windows are FLAGGED not-closing where
    the cycle counts are odd (1496: 93.5 cycles in 62.5 ms)."""
    seq = pj.macro_sequences(4096.0)
    rows = {(s["key_hz"], s["sequence"]): s for s in seq["steps"]}
    assert rows[(1496.0, "standard")]["window_s"] == pytest.approx(0.125)
    assert rows[(644.0, "standard")]["window_s"] == pytest.approx(0.250)
    assert rows[(587.0, "standard")]["window_s"] == pytest.approx(1.0)
    for k in (1496.0, 644.0, 587.0):
        assert rows[(k, "standard")]["closes_exactly"]
    assert not rows[(1496.0, "half_spacing")]["closes_exactly"]
    assert not rows[(587.0, "half_spacing")]["closes_exactly"]
    # 644 Hz DOES close in 125 ms (161/2 = 80.5 -> no!) — check honestly
    assert rows[(644.0, "half_spacing")]["closes_exactly"] == \
        (644.0 * 0.125 == round(644.0 * 0.125))


def test_drive_phase_table_uses_frozen_budget():
    """One row per frequency; the total phase decomposes into the six
    frozen delay terms; the optical transit comes straight from the
    frozen ray_to_target of the axial path."""
    c = build_crystal("ideal_n7")
    pp = pj.probe_paths(c)
    transit = pp["paths"]["axial_tx_to_rx"]["transit_time_s"]
    tab = pj.drive_phase_table(
        [4096.0, 1496.0], commanded_phase_deg=0.0,
        cable_length_m=2.0, driver_delay_s=1e-6,
        coil_inductance_h=1e-3, coil_resistance_ohm=50.0,
        acoustic_path_mm=c.length_mm, acoustic_speed_m_s=6329.927,
        optical_transit_s=transit)
    assert len(tab) == 2
    for row in tab:
        d = row["delays_s"]
        assert set(d) == {"cable_s", "driver_s", "acoustic_s",
                          "optical_s", "group_s"}
        assert row["total_delay_s"] == pytest.approx(sum(d.values()))
        assert d["optical_s"] == pytest.approx(transit)
        want = (2 * math.pi * row["frequency_hz"] * row["total_delay_s"]
                + row["inductive_phase_rad"]) % (2 * math.pi)
        assert row["actual_phase_rad"] == pytest.approx(want, abs=1e-9)
