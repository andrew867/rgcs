"""Agent M11: LiNiPO4 IOME tests (gates H1-H5)."""
from __future__ import annotations

import numpy as np
import pytest

from rscs2_core.refmodels import iome_linipo4 as io

MAT = "reference.linipo4"
KP = np.array([0.0, 1.0, 0.0])       # along toroidal axis b


def test_toroidal_pt_metadata_and_domains():
    """Gate H1: T -> -T under P and under time reversal; PT-even;
    populations normalize."""
    r = np.array([[1e-10, 0, 0], [-1e-10, 0, 0]])
    s = np.array([[0, 0, 1e-23], [0, 0, -1e-23]])
    t = io.ToroidalState.from_spins(r, s)
    assert t.magnitude > 0
    assert np.allclose(t.parity().t_vector_a_m2,
                       -np.asarray(t.t_vector_a_m2))
    assert np.allclose(t.time_reversal().t_vector_a_m2,
                       -np.asarray(t.t_vector_a_m2))
    assert np.allclose(t.pt().t_vector_a_m2, t.t_vector_a_m2)
    plus, minus = io.domain_states(1.0)
    assert np.allclose(np.asarray(plus.t_vector_a_m2),
                       -np.asarray(minus.t_vector_a_m2))
    p, m = io.populations(0.4)
    assert p + m == pytest.approx(1.0) and 0 <= m <= p <= 1


def test_k_and_t_reversal_flip_writing_sign():
    """Gate H2."""
    out_f = io.write_domains(MAT, KP, 1.0, 1.0, 2.0)
    out_b = io.write_domains(MAT, -KP, 1.0, 1.0, 2.0)
    assert out_f["value"]["alignment"] > 0 > out_b["value"]["alignment"]
    assert out_f["value"]["alignment"] == pytest.approx(
        -out_b["value"]["alignment"], rel=1e-12)
    plus, minus = io.domain_states(1.0)
    b_plus = io.iome_bias(KP, plus, 1.0, 2.0, io.PUMP_PRESET_NM)
    b_minus = io.iome_bias(KP, minus, 1.0, 2.0, io.PUMP_PRESET_NM)
    assert b_plus == pytest.approx(-b_minus, rel=1e-12)


def test_polarization_ablation_iome_vs_comparators():
    """Gate H3: IOME is polarization-invariant; IFE responds to
    helicity only; thermal annealing to polarization angle only."""
    lin_x, lin_y = (1.0, 0.0), (0.0, 1.0)
    rcp = (1 / np.sqrt(2), 1j / np.sqrt(2))
    lcp = (1 / np.sqrt(2), -1j / np.sqrt(2))
    a = io.write_domains(MAT, KP, 1.0, 1.0, 2.0, jones=lin_x)
    b = io.write_domains(MAT, KP, 1.0, 1.0, 2.0, jones=rcp)
    c = io.write_domains(MAT, KP, 1.0, 1.0, 2.0, jones=lcp)
    assert a["value"]["alignment"] == b["value"]["alignment"] \
        == c["value"]["alignment"]                 # IOME: pol-blind
    # IFE: helicity-signed, direction-blind
    assert io.inverse_faraday_comparator(rcp, 1.0) > 0 > \
        io.inverse_faraday_comparator(lcp, 1.0)
    assert io.inverse_faraday_comparator(lin_x, 1.0) == 0.0
    # thermal: polarization-angle-dependent, helicity-blind
    th_x = io.thermal_annealing_comparator(lin_x, 1.0)
    th_y = io.thermal_annealing_comparator(lin_y, 1.0)
    th_r = io.thermal_annealing_comparator(rcp, 1.0)
    th_l = io.thermal_annealing_comparator(lcp, 1.0)
    assert th_x != th_y and th_r == pytest.approx(th_l)


def test_zero_coupling_mixed_domain_and_offresonance_nulls():
    z = io.write_domains(MAT, KP, 1.0, 1.0, 0.0)      # lambda = 0
    assert z["value"]["alignment"] == 0.0
    mixed = io.directional_complex_index(
        KP, io.ToroidalState((0.0, 0.0, 0.0)), io.PUMP_PRESET_NM)
    assert mixed["dn_real"] == 0.0 and mixed["dn_imag"] == 0.0
    off = io.write_domains(MAT, KP, 1.0, 1.0, 2.0,
                           wavelength_nm=600.0)      # far off d-d bands
    on = io.write_domains(MAT, KP, 1.0, 1.0, 2.0,
                          wavelength_nm=1400.0)
    assert abs(off["value"]["bias"]) < 0.05 * abs(on["value"]["bias"])


def test_complex_index_channels_separate():
    """Gate H4."""
    plus, _ = io.domain_states(1.0)
    dn = io.directional_complex_index(KP, plus, 1400.0)
    assert dn["dn_real"] != 0 and dn["dn_imag"] != 0
    assert dn["dn_real"] != dn["dn_imag"]
    assert "PREDICTION partner" in dn["note"]
    rev = io.directional_complex_index(-KP, plus, 1400.0)
    assert rev["dn_imag"] == pytest.approx(-dn["dn_imag"])   # diode


def test_saturation_bounded_retention_and_erasure():
    """Gate H5 bounds + thermal behavior."""
    for law in io.SATURATION_LAWS:
        for b in (-50.0, -1.0, 0.0, 1.0, 50.0):
            a = io.written_alignment(b, law)
            assert -1.0 <= a <= 1.0
    hot = io.write_domains(MAT, KP, 1.0, 1.0, 2.0,
                           temperature_k=25.0)
    assert hot["value"]["erased"] and hot["value"]["alignment"] == 0.0
    cold = io.write_domains(MAT, KP, 1.0, 1.0, 2.0,
                            temperature_k=15.0)
    assert not cold["value"]["erased"]


def test_saturation_model_comparison_heldout():
    """Gate H5: law selection by held-out residual, not aesthetics."""
    rng = np.random.default_rng(11)
    b_tr = rng.uniform(-3, 3, 60)
    b_te = rng.uniform(-3, 3, 30)
    truth = lambda b: np.tanh(1.7 * b)
    out = io.compare_saturation_laws(
        b_tr, truth(b_tr) + 0.01 * rng.standard_normal(60),
        b_te, truth(b_te))
    assert out["selected_by_heldout_rmse"] in ("tanh", "logistic")
    assert out["scores"]["linear_clip"]["heldout_rmse"] > \
        out["scores"][out["selected_by_heldout_rmse"]]["heldout_rmse"]


def test_spatial_writing_profile():
    x = np.linspace(-2, 2, 401)
    prof = io.scanned_writing_profile(x, 0.0, 0.5, +1, 3.0)
    assert prof.max() == pytest.approx(np.tanh(3.0), rel=1e-9)
    assert abs(prof[0]) < 1e-6                     # localized
    rev = io.scanned_writing_profile(x, 0.0, 0.5, -1, 3.0)
    assert np.allclose(rev, -prof)
    # two overlapping opposite-sign spots cancel at the midpoint
    two = np.tanh(3.0 * np.exp(-2 * ((x - 0.3) / 0.5) ** 2)
                  - 3.0 * np.exp(-2 * ((x + 0.3) / 0.5) ** 2))
    assert abs(two[200]) < 1e-9


def test_quartz_not_applicable():
    out = io.write_domains("material.alpha_quartz", KP, 1.0, 1.0, 2.0)
    assert out["classification"] == "NOT_APPLICABLE"
    assert out["value"] is None
