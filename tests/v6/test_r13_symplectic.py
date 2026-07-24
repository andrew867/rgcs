"""P13 — Sp(2,R) rotation/squeeze/shear and the rotation-vs-squeeze firewall."""

from __future__ import annotations

import math

import numpy as np
import pytest

from r13 import symplectic as S


def _is_symplectic_by_hand(m):
    return np.allclose(m.T @ S.J @ m, S.J, atol=1e-9)


@pytest.mark.parametrize("factory,arg", [
    (S.rotation, 0.7),
    (S.squeeze, 0.5),
    (S.shear, 1.3),
])
def test_each_generator_is_symplectic_with_unit_determinant(factory, arg):
    m = factory(arg)
    assert S.is_symplectic(m)
    assert _is_symplectic_by_hand(m)
    assert abs(np.linalg.det(m) - 1.0) < 1e-9


def test_rotation_is_orthogonal_but_squeeze_and_shear_are_not():
    assert S.is_orthogonal(S.rotation(0.9))
    assert not S.is_orthogonal(S.squeeze(0.5))
    assert not S.is_orthogonal(S.shear(0.8))


def test_a_non_symplectic_matrix_is_rejected():
    # scaling by 2 is not symplectic (det 4)
    assert not S.is_symplectic(np.array([[2.0, 0.0], [0.0, 2.0]]))


def test_rotation_preserves_trace_of_covariance():
    cov = np.array([[2.0, 0.3], [0.3, 5.0]])
    rot = S.rotation(0.4)
    assert S.preserves_trace(rot, cov)
    evolved = S.variance_evolution(rot, cov)
    assert abs(np.trace(evolved) - np.trace(cov)) < 1e-9


def test_squeeze_preserves_det_but_splits_the_variances():
    cov = np.array([[3.0, 0.0], [0.0, 3.0]])
    sqz = S.squeeze(0.6)
    # determinant (uncertainty product) preserved
    assert S.preserves_det(sqz, cov)
    # trace (variance sum) NOT preserved
    assert not S.preserves_trace(sqz, cov)
    vx0, vp0 = S.quadrature_variances(cov)
    evolved = S.variance_evolution(sqz, cov)
    vx, vp = S.quadrature_variances(evolved)
    # one variance up, one down, product held
    assert vx > vx0 and vp < vp0
    assert abs(vx * vp - vx0 * vp0) < 1e-9


def test_determinant_of_covariance_preserved_by_all_and_by_a_product():
    cov = np.array([[2.0, 0.5], [0.5, 4.0]])
    det0 = np.linalg.det(cov)
    for m in (S.rotation(0.3), S.squeeze(0.7), S.shear(1.1)):
        assert abs(np.linalg.det(S.variance_evolution(m, cov)) - det0) < 1e-9
    product = S.compose(S.rotation(0.3), S.squeeze(0.7), S.shear(1.1))
    assert S.is_symplectic(product)
    assert abs(np.linalg.det(S.variance_evolution(product, cov)) - det0) < 1e-9


def test_product_of_symplectic_maps_is_symplectic():
    product = S.compose(S.rotation(0.5), S.squeeze(0.4), S.shear(0.9),
                        S.rotation(-0.2))
    assert S.is_symplectic(product)
    assert abs(np.linalg.det(product) - 1.0) < 1e-9


def test_refuse_squeeze_as_rotation_raises():
    with pytest.raises(S.SymplecticError):
        S.refuse_squeeze_as_rotation(0.5)


def test_refuse_symplectic_model_as_measurement_raises():
    with pytest.raises(S.SymplecticError):
        S.refuse_symplectic_model_as_measurement()


def test_rotation_versus_squeeze_distinction():
    d = S.rotation_versus_squeeze()
    assert d["rotation_is_orthogonal"] is True
    assert d["squeeze_is_orthogonal"] is False
    assert d["rotation_preserves_trace"] is True
    assert d["squeeze_preserves_trace"] is False
    assert d["rotation_preserves_det"] is True
    assert d["squeeze_preserves_det"] is True
    assert d["squeeze_amplifies_one_deamplifies_other"] is True


def test_report_verdict_and_measures_nothing():
    r = S.symplectic_report()
    assert r["verdict"] == "SYMPLECTIC_TRANSFORMS_ROTATION_SQUEEZE_SHEAR"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["claim_class"] == "ANALYTIC_MODEL"
    assert "what_this_does_not_say" in r
