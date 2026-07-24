"""P10 — piezoelectric coupling reduced to a BVD certificate."""

from __future__ import annotations

import numpy as np
import pytest

from r12 import bridge as B
from r13 import piezobridge as P


# --- the coupling factor -------------------------------------------------

def test_coupling_factor_is_bounded_for_physical_inputs():
    k2 = P.coupling_factor(P.PiezoConstants.alpha_quartz())
    assert 0.0 <= k2 < 1.0


def test_zero_piezo_constant_gives_zero_coupling():
    c = P.PiezoConstants(c_E=3.0e10, e=0.0, eps_S=4.0e-11)
    assert P.coupling_factor(c) == 0.0


def test_an_unphysical_coupling_is_refused():
    # e^2 > c^E eps^S -> k^2 >= 1, refused
    with pytest.raises(P.PiezoBridgeError):
        P.coupling_factor(P.PiezoConstants(c_E=1.0, e=10.0, eps_S=1.0))


# --- the BVD circuit -----------------------------------------------------

def _circuit():
    return P.bvd_from_piezo(P.PiezoConstants.alpha_quartz(),
                            thickness_m=1.0e-3, area_m2=5.0e-5,
                            density=2648.0, quality_factor=1e4)


def test_bvd_gives_four_positive_parameters_and_fp_above_fs():
    ckt = _circuit()
    R, L, C, C0 = ckt.as_tuple()
    assert min(R, L, C, C0) > 0.0
    assert ckt.parallel_resonance_hz > ckt.series_resonance_hz


def test_fp_over_fs_tracks_the_coupling_factor():
    # a stronger piezo constant -> larger k^2 -> larger resonance split
    base = P.PiezoConstants.alpha_quartz()
    strong = P.PiezoConstants(c_E=base.c_E, e=1.6 * base.e, eps_S=base.eps_S)
    geom = dict(thickness_m=1.0e-3, area_m2=5.0e-5, density=2648.0)
    weak_ckt = P.bvd_from_piezo(base, **geom)
    strong_ckt = P.bvd_from_piezo(strong, **geom)
    weak_split = weak_ckt.parallel_resonance_hz / weak_ckt.series_resonance_hz
    strong_split = strong_ckt.parallel_resonance_hz / strong_ckt.series_resonance_hz
    assert strong_split > weak_split
    assert P.coupling_factor(strong) > P.coupling_factor(base)


def test_impedance_has_minimum_near_fs_and_maximum_near_fp():
    ckt = _circuit()
    f_s = ckt.series_resonance_hz
    f_p = ckt.parallel_resonance_hz
    f = np.linspace(0.9 * f_s, 1.1 * f_p, 40001)
    z = np.abs(P.bvd_impedance(ckt, f))
    f_min = f[int(np.argmin(z))]
    f_max = f[int(np.argmax(z))]
    # the dip sits at the series resonance, the peak at the parallel one
    assert f_min == pytest.approx(f_s, rel=1e-3)
    assert f_max == pytest.approx(f_p, rel=1e-3)
    assert f_min < f_max


# --- the certificate -----------------------------------------------------

def test_certificate_has_nine_declarations_and_awaits_falsification():
    cert = P.certificate()
    assert cert.source is B.Domain.MACROSCOPIC_ELASTIC
    assert cert.target is B.Domain.ELECTRICAL_BVD
    assert len(B.REQUIRED_DECLARATIONS) == 9
    # the certificate is complete: none of the nine is missing
    assert cert.missing_declarations() == ()
    # the ninth declaration -- the falsifying measurement -- is present
    assert "f_s" in cert.falsifying_measurement
    assert "crystal" in cert.falsifying_measurement
    assert cert.status is B.CertificateStatus.AWAITING_FALSIFICATION
    assert cert.claim_class == "ENGINEERING_CANDIDATE"


def test_certificate_is_not_yet_evidence():
    cert = P.certificate()
    with pytest.raises(B.BridgeError):
        B.refuse_certificate_as_evidence(cert)


# --- the refusals --------------------------------------------------------

def test_refuse_bvd_as_measured_crystal_raises():
    with pytest.raises(P.PiezoBridgeError):
        P.refuse_bvd_as_measured_crystal("f_s")


def test_refuse_coupling_without_certificate_raises():
    with pytest.raises(P.PiezoBridgeError):
        P.refuse_coupling_without_certificate()


# --- the report ----------------------------------------------------------

def test_report_verdict_and_claims_nothing():
    r = P.piezobridge_report()
    assert r["verdict"] == "PIEZO_TO_BVD_CERTIFICATE_ENGINEERING_CANDIDATE"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["claim_class"] == "ENGINEERING_CANDIDATE"
    assert r["certificate"]["required_declarations"] == 9
    assert "what_this_does_not_say" in r
