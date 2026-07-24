"""P31 — the Euphonic-style force-constant / phonon interface, blocked on DFT."""

from __future__ import annotations

import math

import numpy as np
import pytest

from r13 import euphonic as E


def test_from_dft_raises_blocked_missing_input():
    with pytest.raises(E.EuphonicError) as exc:
        E.ForceConstants.from_dft("some_castep_output.castep_bin")
    assert "BLOCKED_MISSING_INPUT" in str(exc.value)


def test_synthetic_dispersion_matches_analytic_monatomic():
    fc = E.ForceConstants.synthetic_monatomic(m=1.3, K=0.7, a=1.1)
    for q in np.linspace(-math.pi / 1.1, math.pi / 1.1, 25):
        omega = E.phonon_dispersion(fc, [q])[0, 0]
        analytic = E.monatomic_analytic(q, m=1.3, K=0.7, a=1.1)
        assert omega == pytest.approx(analytic, abs=1e-9)
    # POWER: the analytic form is not constant — a wrong q gives a different
    # value, so the match above is not vacuous.
    assert E.monatomic_analytic(0.5, m=1.3, K=0.7, a=1.1) != \
        pytest.approx(E.monatomic_analytic(1.5, m=1.3, K=0.7, a=1.1))


def test_acoustic_branch_goes_to_zero_at_gamma():
    # POWER (acoustic sum rule): omega -> 0 at Gamma for the acoustic branch.
    mono = E.ForceConstants.synthetic_monatomic(m=2.0, K=3.0, a=1.0)
    assert E.phonon_dispersion(mono, [0.0])[0, 0] == pytest.approx(0.0, abs=1e-9)
    assert mono.acoustic_sum_rule_holds()
    di = E.ForceConstants.synthetic_diatomic(m1=1.0, m2=2.5, K=1.7, a=1.0)
    omega = E.phonon_dispersion(di, [0.0])[0]
    assert omega[0] == pytest.approx(0.0, abs=1e-7)     # acoustic -> 0
    assert omega[1] > 1e-3                              # optical stays finite


def test_acoustic_sum_rule_is_load_bearing():
    # If the sum rule is broken, the acoustic branch no longer reaches zero:
    # the test above could genuinely fail for a bad force-constant set.
    m1, m2, K, a = 1.0, 2.0, 1.0, 1.0
    # break the on-site term so rows no longer sum to zero
    bad = E.ForceConstants(
        masses=(m1, m2),
        blocks=((-1, ((0.0, -K), (0.0, 0.0))),
                (0, ((3.0 * K, -K), (-K, 3.0 * K))),   # on-site too large
                (1, ((0.0, 0.0), (-K, 0.0)))),
        a=a)
    assert not bad.acoustic_sum_rule_holds()
    assert E.phonon_dispersion(bad, [0.0])[0, 0] > 1e-3     # no longer zero


def test_dos_integrates_to_mode_count():
    # POWER: the DOS normalization integrates to the number of modes per
    # q-point — 1 for the monatomic set, 2 for the diatomic set.
    qgrid = np.linspace(-math.pi, math.pi, 400)
    mono = E.ForceConstants.synthetic_monatomic(m=1.0, K=1.0, a=1.0)
    di = E.ForceConstants.synthetic_diatomic(m1=1.0, m2=2.0, K=1.0, a=1.0)
    assert E.dos_mode_count(mono, qgrid) == pytest.approx(1.0, abs=1e-9)
    assert E.dos_mode_count(di, qgrid) == pytest.approx(2.0, abs=1e-9)


def test_dos_has_van_hove_like_pileup_at_band_edge():
    # The monatomic DOS diverges at the top of the band (flat dispersion),
    # so the top bins carry more weight than the middle bins.
    mono = E.ForceConstants.synthetic_monatomic(m=1.0, K=1.0, a=1.0)
    qgrid = np.linspace(-math.pi, math.pi, 2000)
    centres, dos = E.density_of_states(mono, qgrid, n_bins=40)
    top = dos[-3:].mean()
    middle = dos[len(dos) // 2 - 1:len(dos) // 2 + 2].mean()
    assert top > middle       # van-Hove-like pile-up at the band edge


def test_dynamical_matrix_is_hermitian():
    di = E.ForceConstants.synthetic_diatomic(m1=1.0, m2=2.0, K=1.3, a=1.0)
    for q in (0.0, 0.7, math.pi):
        D = di.dynamical_matrix(q)
        assert np.allclose(D, D.conj().T, atol=1e-12)
        evals = np.linalg.eigvalsh(D)
        assert np.all(evals >= -1e-9)


def test_dynamic_structure_factor_is_synthetic_interface():
    di = E.ForceConstants.synthetic_diatomic(m1=1.0, m2=2.0, K=1.0, a=1.0)
    freqs, intens = E.dynamic_structure_factor(di, Q=2.0, q=0.6)
    assert freqs.shape == intens.shape == (2,)
    assert np.all(intens >= 0.0)


def test_from_dft_source_is_never_dft():
    fc = E.ForceConstants.synthetic_monatomic()
    assert fc.source is E.FCSource.SYNTHETIC_ANALYTIC


def test_refuse_synthetic_fc_as_dft_raises():
    with pytest.raises(E.EuphonicError):
        E.refuse_synthetic_fc_as_dft(E.ForceConstants.synthetic_monatomic())


def test_refuse_model_dispersion_as_measured_ins_raises():
    with pytest.raises(E.EuphonicError):
        E.refuse_model_dispersion_as_measured_INS()


def test_bad_force_constant_set_is_refused():
    with pytest.raises(E.EuphonicError):
        E.ForceConstants(masses=(1.0,), blocks=((1, ((-1.0,),)),))  # no offset 0
    with pytest.raises(E.EuphonicError):
        # +1 block with no -1 partner breaks Phi_-R = Phi_R^T
        E.ForceConstants(masses=(1.0,),
                         blocks=((0, ((2.0,),)), (1, ((-1.0,),))))


def test_report_verdict_and_no_measurement():
    r = E.euphonic_report()
    assert r["verdict"] == "FORCE_CONSTANT_INTERFACE_BLOCKED_ON_DFT"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["claim_class"] == "ANALYTIC_MODEL"
    assert r["real_force_constants"]["status"] == "BLOCKED_MISSING_INPUT"
    assert "what_this_does_not_say" in r
