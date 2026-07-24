"""P14 — I/Q demodulation, quadrature variances, and the transducer model."""

from __future__ import annotations

import math

import numpy as np
import pytest

from r13 import quadfield as Q


def _record(amplitude, phase, w, periods=40, spp=64):
    period = 2.0 * math.pi / w
    n = periods * spp
    t = np.linspace(0.0, periods * period, n, endpoint=False)
    return t, Q.synth_tone(amplitude, phase, w, t)


def test_iq_demodulate_recovers_amplitude_and_phase_and_power():
    w = 2.0 * math.pi * 100.0
    amp, phi = 3.0, 0.6
    t, sig = _record(amp, phi, w)
    res = Q.iq_demodulate(sig, t, w)
    # I and Q land on A cos/sin (phi) / 2
    assert res.i == pytest.approx(0.5 * amp * math.cos(phi), abs=1e-9)
    assert res.q == pytest.approx(0.5 * amp * math.sin(phi), abs=1e-9)
    # amplitude and phase (POWER) recovered
    assert res.recovered_amplitude == pytest.approx(amp, abs=1e-9)
    assert res.phase == pytest.approx(phi, abs=1e-9)
    assert res.recovered_power == pytest.approx(0.5 * amp * amp, abs=1e-9)


def test_demodulation_check_flags_recovery():
    d = Q.demodulation_check(amplitude=2.5, phase=-0.4)
    assert d["amplitude_recovered"] is True
    assert d["phase_recovered"] is True


def test_complex_amplitude_magnitude_and_phase():
    w = 2.0 * math.pi * 250.0
    amp, phi = 4.0, 1.1
    t, sig = _record(amp, phi, w)
    res = Q.iq_demodulate(sig, t, w)
    a = res.amplitude_component
    assert abs(a) == pytest.approx(amp / 2.0, abs=1e-9)
    assert math.atan2(a.imag, a.real) == pytest.approx(phi, abs=1e-9)


def test_quadrature_variances_and_squeezing_indicator():
    cov = np.array([[0.5, 0.0], [0.0, 2.0]])
    vi, vq = Q.quadrature_variances(cov)
    assert vi == 0.5 and vq == 2.0
    read = Q.squeezing_readout(cov, reference=1.0)
    assert read["squeezing_indicated"] is True
    assert read["quadrature_below_reference"] == ["I"]
    # a symmetric covariance at the reference shows no squeezing
    flat = Q.squeezing_readout(np.eye(2), reference=1.0)
    assert flat["squeezing_indicated"] is False


def test_transducer_added_noise_raises_variance_by_expected_amount():
    tr = Q.Transducer(gain=4.0, noise_psd=7.0)
    v_in = 2.0
    out = tr.output_variance(v_in)
    assert out == pytest.approx(4.0 ** 2 * v_in + 7.0)
    # the added noise is exactly noise_psd above the pure-gain output
    assert out - 4.0 ** 2 * v_in == pytest.approx(7.0)


def test_transducer_gain_scales_the_signal():
    tr = Q.Transducer(gain=3.0, noise_psd=0.0)
    sig = np.array([1.0, -2.0, 0.5])
    assert np.allclose(tr.transduce(sig), 3.0 * sig)


def test_snr_degradation_is_exactly_the_added_noise_term():
    tr = Q.Transducer(gain=5.0, noise_psd=10.0)
    s, n_in = 8.0, 2.0
    deg = tr.snr_degradation(s, n_in)
    referred = 10.0 / 5.0 ** 2            # noise_psd / gain**2
    assert deg["referred_input_noise"] == pytest.approx(referred)
    assert deg["degradation_factor"] == pytest.approx(1.0 + referred / n_in)
    assert deg["excess_from_added_noise"] == pytest.approx(referred / n_in)


def test_refuse_model_squeezing_as_observed_raises():
    with pytest.raises(Q.QuadFieldError):
        Q.refuse_model_squeezing_as_observed()


def test_refuse_transduction_without_certificate_raises():
    uncertified = Q.Transducer(gain=2.0, noise_psd=1.0)
    with pytest.raises(Q.QuadFieldError):
        Q.refuse_transduction_without_certificate(uncertified)
    # even a certified transducer is a licence to model, not a measurement
    certified = Q.Transducer(gain=2.0, noise_psd=1.0, certified=True)
    with pytest.raises(Q.QuadFieldError):
        Q.refuse_transduction_without_certificate(certified)


def test_report_verdict_and_measures_nothing():
    r = Q.quadfield_report()
    assert r["verdict"] == "TWO_CHANNEL_QUADRATURE_TRANSDUCTION_MODEL"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert "what_this_does_not_say" in r
