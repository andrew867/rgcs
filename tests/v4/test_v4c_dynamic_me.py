"""Agent M5: dynamic magnetoelectric tests (gate E4 + E5)."""
from __future__ import annotations

import numpy as np
import pytest

from rscs2_core.refmodels.dynamic_me import (METensor,
                                             optical_rotation_observable)

MAT = "reference.dynamic_magnetoelectric"
A = np.zeros((3, 3))
A[0, 1] = 2e-12                       # single allowed off-diagonal
MASK = A != 0


def _me(**kw):
    args = dict(material_id=MAT, a_ij_s_m=A, f0_hz=1e9, gamma_hz=5e7,
                allowed_mask=MASK)
    args.update(kw)
    return METensor(**args)


def test_zero_tensor_and_zero_drive_nulls():
    z = METensor(MAT, np.zeros((3, 3)), 1e9, 5e7)
    out = z.response([1e9], np.array([0.0, 1.0, 0.0]))
    assert np.allclose(out["p_amplitude_c_m2"], 0.0)
    out2 = _me().response([1e9], np.zeros(3))
    assert np.allclose(out2["p_amplitude_c_m2"], 0.0)


def test_symmetry_forbidden_component_rejected():
    bad = A.copy()
    bad[2, 2] = 1e-12                 # outside the allowed mask
    with pytest.raises(ValueError, match="forbidden"):
        METensor(MAT, bad, 1e9, 5e7, allowed_mask=MASK)


def test_resonance_amplitude_phase_and_quadrature():
    me = _me()
    f = np.array([0.2e9, 1e9, 5e9])
    out = me.response(f, np.array([0.0, 1.0, 0.0]))
    amp = out["p_amplitude_c_m2"][:, 0]
    assert amp[1] > 5 * amp[0]                      # resonant peak
    assert amp[1] > 5 * amp[2]                      # off-resonance decay
    # on resonance the response is in QUADRATURE (phase ~ -pi/2 or
    # +pi/2 by convention): in-phase part ~ 0
    assert abs(out["p_inphase_c_m2"][1, 0]) < \
        0.1 * abs(out["p_quadrature_c_m2"][1, 0])
    # amplitude and quadrature are separate outputs (no unsigned score)
    assert "p_quadrature_c_m2" in out and "p_inphase_c_m2" in out
    # DC limit: alpha -> +a (static), phase -> 0
    dc = me.response([1e3], np.array([0.0, 1.0, 0.0]))
    assert abs(dc["p_phase_rad"][0, 0]) < 1e-3


def test_handedness_reversal_flips_sign():
    me = _me()
    rev = me.reversed_handedness()
    f = [0.5e9]
    h = np.array([0.0, 1.0, 0.0])
    a = me.response(f, h)["p_inphase_c_m2"][0, 0]
    b = rev.response(f, h)["p_inphase_c_m2"][0, 0]
    assert a == pytest.approx(-b, rel=1e-12)


def test_reciprocity_is_metadata_not_shape_inference():
    me = _me(reciprocity="DECLARED_NONRECIPROCAL")
    out = me.response([1e9], np.array([0, 1.0, 0]))
    joined = " ".join(out["assumptions"])
    assert "never inferred from tensor shape" in joined
    me2 = _me(reciprocity="DECLARED_RECIPROCAL")
    assert me2.reciprocity == "DECLARED_RECIPROCAL"


def test_kramers_kronig_consistency_and_sparse_refusal():
    me = _me()
    f = np.linspace(1e6, 8e9, 4096)
    kk = me.kramers_kronig_check(f)
    assert kk["status"] == "CHECKED"
    assert kk["relative_residual"] < 0.05          # Lorentz is causal
    sparse = me.kramers_kronig_check(np.linspace(0.9e9, 1.1e9, 16))
    assert sparse["status"] == "INSUFFICIENT_SPECTRAL_SUPPORT"
    assert sparse["classification"] == "INTERFACE_ONLY"


def test_optical_rotation_channels_separate():
    me = _me()
    obs = optical_rotation_observable(me, 0.5e9, 1e-3, 1e10)
    assert obs["rotation_rad"] != 0
    # far off resonance the absorptive channel is much smaller
    assert abs(obs["ellipticity_rad"]) < abs(obs["rotation_rad"])
    on = optical_rotation_observable(me, 1e9, 1e-3, 1e10)
    assert abs(on["ellipticity_rad"]) > abs(on["rotation_rad"])


def test_quartz_not_applicable():
    q = METensor("material.alpha_quartz", A, 1e9, 5e7,
                 allowed_mask=MASK)
    out = q.response([1e9], np.array([0, 1.0, 0]))
    assert out["classification"] == "NOT_APPLICABLE"
    assert out["value"] is None
    obs = optical_rotation_observable(q, 1e9, 1e-3, 1e10)
    assert obs["classification"] == "NOT_APPLICABLE"
