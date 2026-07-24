"""P05 — the linear-response core: Green function, Kramers-Kronig,
unitary S-matrix, state-space transfer function, and the two refusals."""

from __future__ import annotations

import numpy as np
import pytest

from r13 import response as R


# --- (1) the damped-oscillator Green function ----------------------------

def test_green_oscillator_peaks_at_resonance():
    w0, gamma = 1.0, 0.01
    w = np.linspace(0.5, 1.5, 4001)
    mag = np.abs(R.green_oscillator(w, w0, gamma))
    peak = w[int(np.argmax(mag))]
    # weakly damped: the magnitude peaks at the resonance to within a bin
    assert abs(peak - w0) < 2e-3
    # and the on-resonance magnitude is larger than well off resonance
    assert np.abs(R.green_oscillator(w0, w0, gamma)) > \
        10.0 * np.abs(R.green_oscillator(2.0 * w0, w0, gamma))


def test_green_on_resonance_magnitude_is_one_over_gamma_w0():
    w0, gamma = 3.0, 0.2
    g = R.green_oscillator(w0, w0, gamma)
    assert g.real == pytest.approx(0.0, abs=1e-12)
    assert abs(g) == pytest.approx(1.0 / (gamma * w0), rel=1e-12)


def test_power_fwhm_relates_to_gamma():
    w0, gamma = 1.0, 0.01
    grid = np.linspace(w0 - 5 * gamma, w0 + 5 * gamma, 20001)
    fwhm = R.half_width_of_power(grid, w0, gamma)
    # in the weakly damped limit the FWHM of |G|**2 is gamma itself
    assert fwhm == pytest.approx(gamma, rel=0.01)


def test_green_rejects_lossless_and_nonpositive():
    with pytest.raises(R.ResponseError):
        R.green_oscillator(1.0, 1.0, 0.0)       # no damping -> real-axis pole
    with pytest.raises(R.ResponseError):
        R.green_oscillator(1.0, -1.0, 0.1)      # w0 must be positive


# --- (2) the load-bearing Kramers-Kronig identity ------------------------

def test_kramers_kronig_reconstructs_the_lorentzian_real_part():
    """POWER: the real part of a Lorentzian susceptibility, reconstructed
    from its imaginary part by the Hilbert transform, matches the analytic
    real part; a scrambled imaginary part does not."""
    w0, gamma = 1.0, 0.5
    w = np.arange(-50.0, 50.0 + 1e-9, 0.02)
    chi = R.lorentzian_chi(w, w0, gamma)
    recon = R.kramers_kronig_real_from_imag(chi.imag, w)
    central = np.abs(w) < 5.0
    scale = np.abs(chi.real[central]).max()
    err = np.abs(recon[central] - chi.real[central]).max()
    assert err / scale < 0.05                    # the identity holds
    # control: the wrong imaginary part must NOT reconstruct the real part
    wrong = R.kramers_kronig_real_from_imag(chi.imag[::-1], w)
    wrong_err = np.abs(wrong[central] - chi.real[central]).max()
    assert wrong_err > 10.0 * err


def test_kramers_kronig_requires_a_uniform_grid():
    w = np.concatenate([np.linspace(-10, 0, 200), np.linspace(0.01, 10, 400)])
    with pytest.raises(R.ResponseError):
        R.kramers_kronig_real_from_imag(np.zeros_like(w), w)


# --- (3) the lossless 2x2 scatterer --------------------------------------

def test_beamsplitter_is_unitary():
    for theta, phi in [(0.0, 0.0), (0.3, 0.0), (0.6, 0.7), (1.2, -2.1)]:
        S = R.smatrix_beamsplitter(theta, phi)
        assert R.is_unitary(S)
        # unitarity asserted explicitly: S^dagger S == I to machine precision
        assert np.allclose(S.conj().T @ S, np.eye(2), atol=1e-12)


def test_beamsplitter_conserves_energy():
    S = R.smatrix_beamsplitter(0.6, 0.7)
    x = np.array([1 + 2j, 0.5 - 1j])
    out = R.scatter(S, x)
    assert float(np.vdot(out, out).real) == pytest.approx(
        float(np.vdot(x, x).real), rel=1e-12)


# --- (4) state-space -> transfer function --------------------------------

def test_single_pole_transfer_matches_hand_value():
    # A = [[-a]], B = C = [[1]], D = [[0]]  =>  H(s) = 1/(s + a)
    a, s = 2.0, 3.0j
    H = R.statespace_transfer([[-a]], [[1.0]], [[1.0]], [[0.0]], s)
    assert H == pytest.approx(1.0 / (s + a))


def test_transfer_includes_feedthrough_D():
    a, d, s = 5.0, 0.25, 1.0j
    H = R.statespace_transfer([[-a]], [[1.0]], [[1.0]], [[d]], s)
    assert H == pytest.approx(1.0 / (s + a) + d)


# --- (5) the common interface and typed adapters -------------------------

def test_each_adapter_builds_a_lorentzian_in_its_own_units():
    systems = {
        R.ResponseDomain.MECHANICAL: R.mechanical_oscillator(),
        R.ResponseDomain.ELECTRICAL_BVD: R.electrical_bvd_oscillator(),
        R.ResponseDomain.OPTICAL: R.optical_cavity_oscillator(),
    }
    unit_strings = set()
    for domain, sys in systems.items():
        assert isinstance(sys, R.LinearSystem)
        assert sys.domain is domain
        unit_strings.add(sys.units)
        # response equals the Green function at the same frequency
        assert sys.response(sys.w0) == pytest.approx(
            complex(R.green_oscillator(sys.w0, sys.w0, sys.gamma)))
    # every domain carries its own units
    assert len(unit_strings) == 3


# --- (6) the two governance refusals -------------------------------------

def test_cross_domain_transfer_without_certificate_is_refused():
    with pytest.raises(R.ResponseError):
        R.refuse_cross_domain_without_certificate(
            R.ResponseDomain.OPTICAL, R.ResponseDomain.MECHANICAL)


def test_simulation_is_not_measurement():
    with pytest.raises(R.ResponseError):
        R.refuse_simulation_as_measurement()


# --- (7) the report ------------------------------------------------------

def test_report_verdict_and_claims_no_measurement():
    rep = R.response_report()
    assert rep["verdict"] == "LINEAR_RESPONSE_CORE_IMPLEMENTED"
    assert rep["measured_here"] == "nothing"
    assert rep["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert rep["claim_class"] in R.CLAIM_CLASSES
    assert "what_this_does_not_say" in rep


def test_response_module_imports_from_r13():
    from r13 import response          # noqa: F401
    assert response.DEFAULT_VERDICT == "LINEAR_RESPONSE_CORE_IMPLEMENTED"
