"""P32 — synthetic INS / IXS scattering predictions, tested against closed forms."""

from __future__ import annotations

import math

import numpy as np
import pytest

from r13 import scattering as S


def test_kinematics_conserve_energy_and_momentum():
    # A synthetic neutron event; Q and hbar_omega are the bookkeeping.
    k_i = [3.0, 0.0, 0.0]
    k_f = [2.0, 1.0, 0.0]
    ev = S.scattering_kinematics(k_i, k_f)
    Q = np.array(k_i) - np.array(k_f)
    assert np.allclose(ev.Q_vec(), Q)
    # neutron energy transfer = (|k_i|^2 - |k_f|^2) / 2 in reduced units
    assert ev.hbar_omega == pytest.approx((9.0 - 5.0) / 2.0)
    # the excitation carrying (Q, hbar_omega) conserves both laws
    assert S.conserves(ev, [0.0, 0.0, 0.0], Q, ev.hbar_omega)
    # the scattering triangle closes (law of cosines)
    assert S.scattering_triangle_closes(ev)
    # POWER: a wrong excitation momentum does NOT conserve
    assert not S.conserves(ev, [0.0, 0.0, 0.0], Q + np.array([0.1, 0, 0]),
                           ev.hbar_omega)
    # POWER: a wrong excitation energy does NOT conserve
    assert not S.conserves(ev, [0.0, 0.0, 0.0], Q, ev.hbar_omega + 0.5)


def test_xray_kinematics_use_photon_dispersion():
    ev = S.scattering_kinematics([2.0, 0.0, 0.0], [0.0, 2.0, 0.0],
                                 probe=S.Probe.XRAY)
    # |k_i| = |k_f| = 2, so an X-ray event here is elastic: no energy transfer
    assert ev.hbar_omega == pytest.approx(0.0, abs=1e-12)


def test_bragg_peaks_land_on_reciprocal_points_and_obey_braggs_law():
    a = 5.0
    hkl = (1, 1, 0)
    G = S.reciprocal_vector(hkl, a)
    # POWER: a peak lands exactly on the reciprocal point, and not off it
    assert S.bragg_condition(G, G)
    assert not S.bragg_condition(G + np.array([0.2, 0.0, 0.0]), G)
    # |G| = 2 pi / d links the reciprocal point to the plane spacing
    d = S.d_spacing(hkl, a)
    assert np.linalg.norm(G) == pytest.approx(2.0 * math.pi / d)
    # Bragg's law 2 d sin(theta) = n lambda holds for the computed angle
    lam = 2.0
    assert S.braggs_law_holds(hkl, a, lam, n=1)
    theta = S.bragg_angle(hkl, a, lam, n=1)
    assert 2.0 * d * math.sin(theta) == pytest.approx(lam)
    # POWER: a different order gives a different angle (law is not vacuous)
    assert S.bragg_angle(hkl, a, lam, n=1) != \
        pytest.approx(S.bragg_angle(hkl, a, lam, n=2))


def test_forbidden_reflection_raises():
    # n lambda / 2d > 1 has no real Bragg angle
    with pytest.raises(S.ScatteringError):
        S.bragg_angle((1, 0, 0), a=1.0, wavelength=5.0, n=1)


def test_one_phonon_peaks_at_model_frequencies():
    model = S.PhononModel.synthetic()
    # Q with components on every axis so every mode is allowed
    omegas, intens = S.one_phonon_sqw(model, [1.0, 1.0, 1.0], temperature=300.0)
    assert np.allclose(np.sort(omegas), np.sort(model.frequencies()))
    assert np.all(intens > 0.0)


def test_one_phonon_selection_rule_zeroes_transverse_geometry():
    model = S.PhononModel.synthetic()
    # Q along x: only the longitudinal-x mode (omega=1) is allowed;
    # the transverse y and z modes have Q . e = 0 and vanish.
    omegas, intens = S.one_phonon_sqw(model, [2.0, 0.0, 0.0])
    order = np.argsort(omegas)
    intens = intens[order]
    assert intens[0] > 0.0                     # longitudinal, allowed
    assert intens[1] == pytest.approx(0.0)     # transverse-y, forbidden
    assert intens[2] == pytest.approx(0.0)     # transverse-z, forbidden
    # POWER: rotating Q to gain a y-component switches the y mode back on,
    # so the zero above is the geometry, not a dead computation.
    _, intens2 = S.one_phonon_sqw(model, [2.0, 2.0, 0.0])
    intens2 = intens2[np.argsort(_)]
    assert intens2[1] > 0.0


def test_detailed_balance_ratio_matches_boltzmann():
    model = S.PhononModel.synthetic()
    Q = [1.0, 0.0, 0.0]           # allowed for the longitudinal-x mode
    T = 4.0
    ratio = S.detailed_balance_ratio(model, Q, mode_index=0, temperature=T)
    omega = model.modes[0].omega
    assert ratio == pytest.approx(math.exp(omega / T))
    # POWER: the ratio is temperature-dependent and > 1 at finite T; a
    # different temperature gives a different, correct ratio.
    ratio_hot = S.detailed_balance_ratio(model, Q, 0, temperature=40.0)
    assert ratio > 1.0
    assert ratio_hot == pytest.approx(math.exp(omega / 40.0))
    assert ratio != pytest.approx(ratio_hot)


def test_detailed_balance_undefined_for_forbidden_geometry():
    model = S.PhononModel.synthetic()
    # mode 1 is transverse-y; Q along x gives Q . e = 0
    with pytest.raises(S.ScatteringError):
        S.detailed_balance_ratio(model, [1.0, 0.0, 0.0], mode_index=1,
                                 temperature=10.0)


def test_bad_inputs_are_refused():
    with pytest.raises(S.ScatteringError):
        S.scattering_kinematics([1.0, 0.0], [0.0, 0.0, 0.0])   # not a 3-vector
    with pytest.raises(S.ScatteringError):
        S.reciprocal_vector((1, 1, 1), a=0.0)                  # bad lattice


def test_refuse_synthetic_sqw_as_beamtime_data_raises():
    with pytest.raises(S.ScatteringError):
        S.refuse_synthetic_sqw_as_beamtime_data()


def test_refuse_prediction_as_detection_raises():
    with pytest.raises(S.ScatteringError):
        S.refuse_prediction_as_detection()


def test_report_verdict_and_no_measurement():
    r = S.scattering_report()
    assert r["verdict"] == "SYNTHETIC_INS_IXS_PREDICTION_PROSPECTIVE"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["claim_class"] == "PROSPECTIVE_PREDICTION"
    assert r["real_beamtime"]["status"] == "BLOCKED_MISSING_INPUT"
    assert "what_this_does_not_say" in r
