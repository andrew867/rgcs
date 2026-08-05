"""P08 — the atomistic phonon (mass-and-spring) model, tested analytically."""

from __future__ import annotations

import math

import numpy as np
import pytest

from r13 import atomistic as A


def test_monatomic_dispersion_matches_analytic():
    chain = A.Chain1D.monatomic(m=1.3, K=0.7, a=1.1)
    for k in np.linspace(-math.pi / 1.1, math.pi / 1.1, 25):
        omega = chain.dispersion(k)[0]
        analytic = A.monatomic_dispersion(k, m=1.3, K=0.7, a=1.1)
        # abs tol reflects sqrt of a near-zero eigenvalue at k=0
        assert omega == pytest.approx(analytic, abs=1e-6)
    # POWER: the analytic form is not a constant — a wrong k gives a
    # different value, so the match above is not vacuous.
    assert A.monatomic_dispersion(0.5, m=1.3, K=0.7, a=1.1) != \
        pytest.approx(A.monatomic_dispersion(1.5, m=1.3, K=0.7, a=1.1))


def test_monatomic_omega_zero_at_gamma():
    chain = A.Chain1D.monatomic(m=2.0, K=3.0, a=1.0)
    assert chain.dispersion(0.0)[0] == pytest.approx(0.0, abs=1e-12)
    assert A.monatomic_dispersion(0.0, m=2.0, K=3.0, a=1.0) == \
        pytest.approx(0.0, abs=1e-12)


def test_diatomic_gap_edges_at_zone_boundary():
    m1, m2, K, a = 1.0, 3.0, 2.0, 1.0
    chain = A.Chain1D.diatomic(m1=m1, m2=m2, K=K, a=a)
    omega = chain.dispersion(math.pi / a)          # zone boundary
    lower, upper = A.diatomic_zone_boundary_edges(m1, m2, K)
    assert lower == pytest.approx(math.sqrt(2.0 * K / m2))
    assert upper == pytest.approx(math.sqrt(2.0 * K / m1))
    assert omega[0] == pytest.approx(lower, abs=1e-9)   # acoustic top
    assert omega[1] == pytest.approx(upper, abs=1e-9)   # optical bottom
    # there is a genuine gap: the branches do not touch
    assert omega[1] > omega[0] + 1e-6


def test_diatomic_acoustic_branch_goes_to_zero_at_gamma():
    chain = A.Chain1D.diatomic(m1=1.0, m2=2.5, K=1.7, a=1.0)
    omega = chain.dispersion(0.0)
    # Eigensolver path: the zero eigenvalue carries BLAS-dependent
    # noise (omega ~ sqrt(eps)); CI's runner produced 7.3e-9 where
    # Windows gives <1e-9. 1e-7 is still eight decades below the
    # optical branch. The closed-form check below keeps abs=1e-12.
    assert omega[0] == pytest.approx(0.0, abs=1e-7)     # acoustic -> 0
    assert omega[1] > 1e-3                              # optical stays finite
    ac, op = A.diatomic_dispersion(0.0, m1=1.0, m2=2.5, K=1.7, a=1.0)
    assert ac == pytest.approx(0.0, abs=1e-12)
    assert op == pytest.approx(omega[1], abs=1e-9)


def test_dynamical_matrix_hermitian_with_real_nonneg_eigenvalues():
    k = 0.83
    masses = [1.0, 2.0, 1.5]
    springs = [1.1, 0.9, 1.3]
    D = A.dynamical_matrix(k, masses, springs, a=1.0)
    assert np.allclose(D, D.conj().T, atol=1e-12)       # Hermitian
    evals = np.linalg.eigvalsh(D)
    assert np.all(np.abs(evals.imag) < 1e-12) if np.iscomplexobj(evals) \
        else True
    assert np.all(evals >= -1e-9)                       # non-negative


def test_acoustic_sum_rule_enforced_and_checked():
    phi = np.array([[9.0, -1.0, -2.0],
                    [-1.0, 5.0, -3.0],
                    [-2.0, -3.0, 4.0]])
    assert not A.acoustic_sum_rule_holds(phi)           # arbitrary diagonal
    corrected = A.enforce_acoustic_sum_rule(phi)
    assert A.acoustic_sum_rule_holds(corrected)
    assert np.allclose(corrected.sum(axis=1), 0.0, atol=1e-12)
    # off-diagonal couplings are untouched; only the diagonal was fixed
    assert corrected[0, 1] == pytest.approx(-1.0)
    assert corrected[0, 0] == pytest.approx(3.0)        # -(-1 + -2)


def test_non_square_force_constant_matrix_is_refused():
    with pytest.raises(A.AtomisticError):
        A.enforce_acoustic_sum_rule(np.zeros((2, 3)))


def test_non_positive_mass_or_spring_is_refused():
    with pytest.raises(A.AtomisticError):
        A.dynamical_matrix(0.5, [0.0, 1.0], [1.0, 1.0])
    with pytest.raises(A.AtomisticError):
        A.dynamical_matrix(0.5, [1.0, 1.0], [1.0, -1.0])


def test_refuse_toy_model_as_real_spectrum_raises():
    with pytest.raises(A.AtomisticError):
        A.refuse_toy_model_as_real_spectrum()


def test_report_verdict_and_no_measurement():
    r = A.atomistic_report()
    assert r["verdict"] == "ATOMISTIC_PHONON_MODEL_ANALYTIC"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["claim_class"] == "ANALYTIC_MODEL"
    assert r["real_force_constants"]["status"] == "BLOCKED_MISSING_INPUT"
    assert "what_this_does_not_say" in r
