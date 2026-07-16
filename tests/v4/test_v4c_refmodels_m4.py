"""Agent M4: exciton-magnon, avoided crossing, block Hamiltonian,
dressed spin (gates E1-E3, E5)."""
from __future__ import annotations

import math

import numpy as np
import pytest

from rscs2_core.refmodels import avoided_crossing as ac
from rscs2_core.refmodels import exciton_magnon as em
from rscs2_core.refmodels.block_hamiltonian import BlockHamiltonian
from rscs2_core.refmodels.dressed_spin import bloch_coherence
from rscs2_core.multiphysics.coupling import CouplingRejected

REF = "reference.exciton_magnon"
SOE = "reference.soe_phonon"


# --- exciton-magnon (gate E1) -------------------------------------------

def test_zero_modulation_and_small_angle():
    out = em.modulated_trace(REF, 1.5, 0.2, math.pi / 3, 0.0, 1e9)
    assert np.allclose(out["energy_t"], out["energy_t"][0])  # constant
    e0, c1, c2 = em.small_angle_expansion(math.pi / 3, 0.05)
    x = np.linspace(-0.05, 0.05, 101)
    exact = em.exciton_energy(math.pi / 3 + x)
    approx = e0 + c1 * x + c2 * x ** 2
    # O(x^3) remainder: |E'''|max/6 * x^3 ~ (1/2)/6 * 1.25e-4 ~ 1e-5
    assert np.max(np.abs(exact - approx)) < 1.2e-5


def test_sideband_structure_and_symmetry():
    """Small modulation at theta0 with sin(theta0) != 0: fundamental
    sideband dominates; analytic Jacobi-Anger amplitudes decrease."""
    out = em.modulated_trace(REF, 0.0, 1.0, math.pi / 3, 0.05, 1e9,
                             duration_s=64e-9, n=4096)
    freqs, spec = out["freqs_hz"], out["spectrum"]
    f1 = freqs[np.argmax(spec[1:]) + 1]
    assert f1 == pytest.approx(1e9, rel=0.02)         # fundamental
    amps = em.sideband_amplitudes(math.pi / 3, 0.05)
    assert amps[1] > amps[2] > amps[3]
    # at theta0 = 0 the FIRST harmonic vanishes (sin th0 = 0): the
    # leading response is the second harmonic
    amps0 = em.sideband_amplitudes(0.0, 0.05)
    assert amps0[1] < 1e-12 < amps0[2]


def test_damping_broadens_linewidth():
    sharp = em.modulated_trace(REF, 0.0, 1.0, math.pi / 3, 0.05, 1e9,
                               damping_hz=0.0, duration_s=200e-9)
    broad = em.modulated_trace(REF, 0.0, 1.0, math.pi / 3, 0.05, 1e9,
                               damping_hz=3e7, duration_s=200e-9)

    def width(out):
        s, f = out["spectrum"], out["freqs_hz"]
        pk = np.argmax(s[1:]) + 1
        half = s[pk] / 2
        above = np.nonzero(s > half)[0]
        return f[above[-1]] - f[above[0]]
    assert width(broad) > 2 * width(sharp)


def test_exciton_magnon_quartz_rejected():
    out = em.modulated_trace("material.alpha_quartz", 0.0, 1.0,
                             math.pi / 3, 0.05, 1e9)
    assert out["classification"] == "NOT_APPLICABLE"
    assert out["value"] is None


# --- avoided crossing (gate E2) -------------------------------------------

def test_zero_coupling_exact_crossing_and_frozen_anchor():
    out = ac.poles([1000.0, 1000.0], np.zeros((2, 2)))
    p = out["poles_hz"]
    assert p[0].real == pytest.approx(1000.0) == \
        pytest.approx(p[1].real)               # exact degeneracy
    # frozen v3 anchor in the lossless limit
    from rgcs_core.coupled_modes.static import coupled_two_mode
    fa, fb, g = 980.0, 1020.0, 15.0
    frozen = coupled_two_mode(fa, fb, g)
    mine = ac.two_mode(SOE, fa, fb, g)
    assert mine["value"]["lower_hz"] == pytest.approx(
        frozen["lower_hybrid_hz"], rel=1e-12)
    assert mine["value"]["upper_hz"] == pytest.approx(
        frozen["upper_hybrid_hz"], rel=1e-12)
    # minimum splitting = 2g on resonance
    res = ac.two_mode(SOE, 1000.0, 1000.0, 15.0)
    assert res["value"]["splitting_hz"] == pytest.approx(30.0,
                                                         rel=1e-12)


def test_linewidths_and_large_detuning_participation():
    out = ac.two_mode(SOE, 1000.0, 1000.0, 10.0, gamma_a_hz=4.0,
                      gamma_b_hz=1.0)
    v = out["value"]
    # on resonance the hybrid linewidths average the bare ones
    assert v["lower_linewidth_hz"] == pytest.approx(2.5, rel=1e-6)
    assert v["upper_linewidth_hz"] == pytest.approx(2.5, rel=1e-6)
    sweep = ac.detuning_sweep(np.linspace(500, 1500, 21), 1000.0, 10.0)
    # far below resonance the lower branch is ~pure mode a
    assert sweep["participation_a_in_lower"][0] > 0.99
    assert sweep["participation_a_in_lower"][-1] < 0.01
    # splitting never below 2g
    split = sweep["upper"].real - sweep["lower"].real
    assert split.min() == pytest.approx(20.0, rel=1e-6)


def test_splitting_uncertainty_propagation():
    out = ac.splitting_uncertainty(1000.0, 1000.0, 10.0,
                                   {"fa": 1.0, "fb": 1.0, "g": 0.5})
    # on resonance d(split)/dg = 2, d/dfa ~ 0
    assert out["jacobian"]["g"] == pytest.approx(2.0, abs=1e-3)
    assert abs(out["jacobian"]["fa"]) < 1e-3
    assert out["sigma_splitting_hz"] == pytest.approx(1.0, rel=1e-2)


def test_avoided_crossing_quartz_rejected():
    out = ac.two_mode("material.alpha_quartz", 1000, 1010, 5)
    assert out["classification"] == "NOT_APPLICABLE"


# --- block Hamiltonian ----------------------------------------------------

def test_block_hamiltonian_hermitian_dissipative_and_gating():
    bh = BlockHamiltonian(REF)
    bh.add_block("magnon", [1.0e9], [1e6])
    bh.add_block("exciton", [1.001e9], [5e6])
    bh.couple("magnon", "exciton", 2e6)
    herm = bh.eigenmodes(dissipative=False)
    assert herm["hermitian_residual_hz"] < 1e-6      # real eigvals
    dis = bh.eigenmodes(dissipative=True)
    assert dis["stable"]
    assert np.all(dis["poles_hz"].imag <= 0)
    exp = bh.export_interface()
    assert exp["classification"] == "INTERFACE_ONLY"
    # quartz cannot even ADD a magnon block (gate E5)
    with pytest.raises(CouplingRejected):
        BlockHamiltonian("material.alpha_quartz").add_block(
            "magnon", [1e9])
    # unstable (negative damping) parameterization is rejected
    bad = BlockHamiltonian(REF).add_block("magnon", [1e9], [-1e6])
    with pytest.raises(ArithmeticError, match="unstable"):
        bad.eigenmodes()


# --- dressed spin (gate E3) -----------------------------------------------

def test_dressed_spin_regimes_and_quartz_rejection():
    common = dict(noise_sigma_rad_s=2e4, noise_tau_s=5e-4,
                  duration_s=20e-3, n=12000, seed=7)
    bare = bloch_coherence(REF, 0.0, **common)
    dressed = bloch_coherence(REF, 5e5, **common)
    # deterministic: same seed reproduces exactly
    again = bloch_coherence(REF, 5e5, **common)
    assert np.array_equal(dressed["sx_dressed"], again["sx_dressed"])
    # protection only in the declared (dressed) regime
    assert dressed["value"]["regime"] == "dressed"
    assert dressed["value"]["t_coh_dressed_s"] > \
        bare["value"]["t_coh_bare_s"]
    assert "NOT a claim" in " ".join(dressed["assumptions"])
    q = bloch_coherence("material.alpha_quartz", 5e5, **common)
    assert q["classification"] == "NOT_APPLICABLE"
