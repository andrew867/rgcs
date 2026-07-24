"""P16 — Floquet: symplectic monodromy, tongues, quasi-energies, gain."""

from __future__ import annotations

import numpy as np
import pytest

from r13 import floquet as F


def test_monodromy_is_symplectic_det_one():
    for delta, epsilon in ((1.0, 0.4), (2.0, 0.2), (0.5, 0.3)):
        M = F.floquet_monodromy(delta, epsilon)
        assert np.linalg.det(M) == pytest.approx(1.0, abs=1e-6)
        assert F.is_symplectic(M)


def test_inside_tongue_unstable_outside_stable():
    # POWER both ways: at delta = 1 any epsilon > 0 gives |mu| > 1;
    # a detuned point keeps the multipliers on the unit circle.
    c = F.principal_tongue_contrast(epsilon=0.4)
    assert c["inside_is_unstable"] is True
    assert c["inside"]["spectral_radius"] > 1.0 + 1e-4
    assert c["outside_is_stable"] is True
    assert c["outside"]["spectral_radius"] == pytest.approx(1.0, abs=1e-4)


def test_stability_flips_when_the_drive_is_removed():
    # The negative control: with epsilon = 0 the delta = 1 point is stable,
    # so the instability is caused by the drive, not by delta alone.
    calm = F.stability_at(1.0, 0.0)
    assert calm.stable is True
    driven = F.stability_at(1.0, 0.4)
    assert driven.stable is False


def test_quasi_energies_real_and_plus_minus_paired_for_stable_case():
    T = F.drive_period()
    M = F.floquet_monodromy(2.0, 0.2)     # stable point
    assert F.is_stable(M)
    qe = F.quasi_energies(M, T)
    # real (multipliers on the unit circle)
    assert max(abs(np.imag(z)) for z in qe) < 1e-6
    # +/- pairs (symplectic structure): they sum to zero
    assert float(np.real(qe[0] + qe[1])) == pytest.approx(0.0, abs=1e-6)


def test_unstable_case_gives_complex_quasi_energies():
    T = F.drive_period()
    M = F.floquet_monodromy(1.0, 0.4)     # inside the tongue
    qe = F.quasi_energies(M, T)
    assert max(abs(np.imag(z)) for z in qe) > 1e-3


def test_parametric_gain_above_threshold_is_greater_than_one():
    g = F.parametric_gain(pump=1.0, detuning=0.0)
    assert g.above_threshold is True
    assert g.amplified > 1.0


def test_parametric_gain_is_phase_sensitive():
    # POWER: one quadrature amplified, the conjugate deamplified, product 1.
    g = F.parametric_gain(pump=1.0, detuning=0.0)
    assert g.amplified > 1.0
    assert g.deamplified < 1.0
    assert g.amplified * g.deamplified == pytest.approx(1.0, abs=1e-9)
    assert g.phase_sensitive is True


def test_below_threshold_there_is_no_net_amplification():
    # No pump, only detuning: a pure rotation, no quadrature is amplified.
    g = F.parametric_gain(pump=0.0, detuning=1.0)
    assert g.above_threshold is False
    assert g.amplified == pytest.approx(1.0, abs=1e-9)
    # A weak pump below the detuning threshold: the gain stays bounded as
    # the interaction lengthens (oscillatory), instead of the exponential
    # blow-up seen above threshold.
    weak = F.parametric_gain(pump=0.2, detuning=1.0)
    assert weak.above_threshold is False
    below = [F.parametric_gain(0.2, 1.0, length=L).amplified
             for L in (1.0, 2.0, 5.0, 10.0, 20.0, 50.0)]
    assert max(below) < 1.5
    # ... whereas above threshold the amplified quadrature grows without
    # bound and monotonically with length.
    above = [F.parametric_gain(1.0, 0.0, length=L).amplified
             for L in (1.0, 2.0, 5.0, 10.0)]
    assert above == sorted(above)
    assert above[-1] > 100.0 * max(below)


def test_refuse_model_instability_as_measured_raises():
    with pytest.raises(F.FloquetError):
        F.refuse_model_instability_as_measured(1.0, 0.4)


def test_bad_inputs_are_refused():
    with pytest.raises(F.FloquetError):
        F.floquet_monodromy(1.0, 0.4, omega_drive=0.0)   # non-positive drive
    with pytest.raises(F.FloquetError):
        F.quasi_energies(np.eye(2), 0.0)                 # non-positive period
    with pytest.raises(F.FloquetError):
        F.symplectic_defect(np.zeros((3, 3)))            # not 2x2
    with pytest.raises(F.FloquetError):
        F.parametric_gain(1.0, 0.0, length=0.0)          # non-positive length


def test_report_verdict_and_no_measurement():
    r = F.floquet_report()
    assert r["verdict"] == "FLOQUET_PARAMETRIC_MODEL_ANALYTIC"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["claim_class"] in r["claim_classes"]
    assert "what_this_does_not_say" in r
    assert r["symplectic_defect"] < 1e-6
    assert r["principal_tongue_contrast"]["inside_is_unstable"] is True
    assert r["principal_tongue_contrast"]["outside_is_stable"] is True
    assert r["quasi_energies"][
        "real_and_plus_minus_paired_for_stable_case"] is True
    assert r["parametric_gain"]["amplified"] > 1.0
