"""P12 — chiral phonons, analytic model."""

from __future__ import annotations

import math

import numpy as np
import pytest

from r13 import chiral as C


# --- per-mode angular momentum -------------------------------------------

def test_left_and_right_circular_are_equal_and_opposite():
    """POWER: e_+ carries +hbar and e_- carries -hbar, exactly opposite.

    Compared in units of hbar so the tolerance is meaningful and not
    swamped by pytest's absolute-tolerance floor on 1e-34-scale numbers.
    """
    e_plus, e_minus = C.circular_basis()
    lz_plus = C.phonon_angular_momentum(e_plus) / C.HBAR_J_S
    lz_minus = C.phonon_angular_momentum(e_minus) / C.HBAR_J_S
    assert lz_plus == pytest.approx(1.0)
    assert lz_minus == pytest.approx(-1.0)
    assert lz_plus == pytest.approx(-lz_minus)


def test_linear_polarization_carries_no_angular_momentum():
    """POWER: a linear mode has l_z = 0 at any orientation."""
    for angle in (0.0, 0.3, math.pi / 4, 1.0):
        lz = C.phonon_angular_momentum(C.linear_polarization(angle))
        assert lz / C.HBAR_J_S == pytest.approx(0.0, abs=1e-12)


def test_angular_momentum_would_fail_if_sign_were_wrong():
    """Falsifiable: e_+ is +hbar, not -hbar (compared in hbar units)."""
    e_plus, _ = C.circular_basis()
    lz = C.phonon_angular_momentum(e_plus) / C.HBAR_J_S
    assert lz != pytest.approx(-1.0)
    assert lz == pytest.approx(1.0)


def test_helicity_classification():
    e_plus, e_minus = C.circular_basis()
    assert C.helicity_of(e_plus) is C.Helicity.LEFT
    assert C.helicity_of(e_minus) is C.Helicity.RIGHT
    assert C.helicity_of(C.linear_polarization()) is C.Helicity.LINEAR


# --- the circular basis ---------------------------------------------------

def test_circular_basis_is_orthonormal():
    e_plus, e_minus = C.circular_basis()
    assert complex(np.vdot(e_plus, e_plus)) == pytest.approx(1.0)
    assert complex(np.vdot(e_minus, e_minus)) == pytest.approx(1.0)
    assert abs(complex(np.vdot(e_plus, e_minus))) == pytest.approx(0.0,
                                                                    abs=1e-12)


def test_circular_modes_are_rotation_eigenvectors_with_pm_i():
    """L e_± = ± e_±; equivalently the mode rotates as exp(∓ i t)."""
    e_plus, e_minus = C.circular_basis()
    assert C.rotation_eigenvalue(e_plus) == pytest.approx(1.0)
    assert C.rotation_eigenvalue(e_minus) == pytest.approx(-1.0)
    # The generator acting on e_x ± i e_y multiplies by ±i componentwise:
    # L = [[0,-i],[i,0]], so L e_+ = e_+ means the phase circulates.
    lp = C.ROTATION_GENERATOR @ e_plus
    assert np.allclose(lp, e_plus)
    lm = C.ROTATION_GENERATOR @ e_minus
    assert np.allclose(lm, -e_minus)


def test_generator_eigenvalues_are_plus_and_minus_i_on_the_axes():
    """The rotation generator's own spectrum is ±i on (e_x, e_y)? No —
    it is Hermitian with real eigenvalues ±1; the circular modes are its
    eigenvectors, and each cartesian component of e_± carries a ±i."""
    vals = np.linalg.eigvalsh(C.ROTATION_GENERATOR)
    assert sorted(np.real(vals)) == pytest.approx([-1.0, 1.0])
    e_plus, _ = C.circular_basis()
    # componentwise phase: e_plus = (1, i)/sqrt2, the i is the circulation
    assert e_plus[1] / e_plus[0] == pytest.approx(1.0j)


def test_linear_polarization_is_not_a_rotation_eigenvector():
    with pytest.raises(C.ChiralError):
        C.rotation_eigenvalue(C.linear_polarization(0.0))


# --- chirality at K versus K' --------------------------------------------

def test_opposite_chirality_at_K_and_K_prime():
    lk = C.valley_pseudo_angular_momentum(C.Valley.K) / C.HBAR_J_S
    lkp = C.valley_pseudo_angular_momentum(C.Valley.K_PRIME) / C.HBAR_J_S
    assert lk == pytest.approx(1.0)
    assert lkp == pytest.approx(-1.0)
    assert lk == pytest.approx(-lkp)
    flip = C.chirality_flips_between_valleys()
    assert flip["equal_and_opposite"] is True


# --- valley selection rule ------------------------------------------------

def test_valley_selection_flips_with_helicity():
    assert C.valley_selection(C.Helicity.LEFT) is C.Valley.K
    assert C.valley_selection(C.Helicity.RIGHT) is C.Valley.K_PRIME
    assert (C.valley_selection(C.Helicity.LEFT)
            is not C.valley_selection(C.Helicity.RIGHT))


def test_linear_drive_selects_no_valley():
    with pytest.raises(C.ChiralError):
        C.valley_selection(C.Helicity.LINEAR)


# --- structural refusals --------------------------------------------------

def test_zero_and_wrong_shape_polarizations_are_refused():
    with pytest.raises(C.ChiralError):
        C.phonon_angular_momentum([0.0, 0.0])
    with pytest.raises(C.ChiralError):
        C.phonon_angular_momentum([1.0, 0.0, 0.0])


# --- the refusal ----------------------------------------------------------

def test_refuse_model_chirality_as_measured_raises():
    with pytest.raises(C.ChiralError):
        C.refuse_model_chirality_as_measured(l_z=C.HBAR_J_S)


# --- report ---------------------------------------------------------------

def test_report_verdict_and_no_measurement():
    r = C.chiral_report()
    assert r["verdict"] == "CHIRAL_PHONON_MODEL_ANALYTIC"
    assert r["claim_class"] == "ANALYTIC_MODEL"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert "what_this_does_not_say" in r
    assert r["angular_momentum"]["e_plus_l_z_over_hbar"] == pytest.approx(1.0)
    assert r["angular_momentum"]["e_minus_l_z_over_hbar"] == pytest.approx(-1.0)
