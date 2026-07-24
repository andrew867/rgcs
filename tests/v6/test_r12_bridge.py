"""Typed cross-domain coupling certificates (R12 bridge rule)."""

from __future__ import annotations

import pytest

from r12 import bridge as B


def _cert(**kw):
    base = dict(
        certificate_id="piezo",
        source=B.Domain.MACROSCOPIC_ELASTIC,
        target=B.Domain.ELECTRICAL_BVD,
        state_variables=("strain", "polarization"),
        units=("dimensionless", "C/m^2"),
        coupling_operator="piezoelectric tensor d_ij",
        overlap_factor=0.6,
        detuning=0.0,
        damping=1.0,
        phase_matching="none required (quasi-static)",
        symmetry_allowed=True,
        energy_in="mechanical work on the electrodes",
        energy_out="electrical energy in the load",
        uncertainty="+/- 10% on d_ij",
        null_model="a centrosymmetric control has zero piezo response",
        falsifying_measurement="measure charge vs applied strain; null if flat",
    )
    base.update(kw)
    return B.CouplingCertificate(**base)


def test_a_complete_certificate_licenses_one_direction():
    c = _cert()
    B.register(c)
    assert B.transfer_allowed(c.source, c.target)
    B.refuse_uncertified_transfer(c.source, c.target)   # must not raise


def test_an_uncertified_transfer_is_refused_by_default():
    with pytest.raises(B.BridgeError):
        B.refuse_uncertified_transfer(B.Domain.OPTICAL_CAVITY,
                                      B.Domain.THERMAL)


def test_same_domain_needs_no_certificate():
    B.refuse_uncertified_transfer(B.Domain.MAGNETIC, B.Domain.MAGNETIC)


def test_a_certificate_connects_two_different_domains():
    with pytest.raises(B.BridgeError):
        _cert(source=B.Domain.MAGNETIC, target=B.Domain.MAGNETIC)


def test_every_state_variable_needs_its_own_unit():
    with pytest.raises(B.BridgeError):
        _cert(state_variables=("strain", "polarization"), units=("C/m^2",))


def test_an_empty_required_declaration_voids_the_certificate():
    for empty in ("coupling_operator", "falsifying_measurement",
                  "null_model", "energy_in"):
        with pytest.raises(B.BridgeError):
            _cert(**{empty: "   "})


def test_a_complete_certificate_is_only_a_candidate_until_measured():
    c = _cert()
    assert c.status is B.CertificateStatus.AWAITING_FALSIFICATION
    assert c.claim_class == "ENGINEERING_CANDIDATE"
    with pytest.raises(B.BridgeError):
        B.refuse_certificate_as_evidence(c)


def test_a_measured_certificate_would_be_bench_but_none_exist_here():
    c = _cert(measurement_performed=True)
    assert c.status is B.CertificateStatus.SURVIVED_FALSIFICATION
    assert c.claim_class == "BENCH_MEASUREMENT"
    # the module declares that no such measurement can be performed here
    assert B.MEASUREMENT_STATUS == "BLOCKED_MISSING_DATA"


def test_certificates_are_directional():
    c = _cert()
    with pytest.raises(B.BridgeError):
        B.refuse_reverse_direction(c)


def test_certificates_do_not_compose():
    with pytest.raises(B.BridgeError):
        B.refuse_chained_transfer(_cert(), _cert())


def test_transfer_efficiency_peaks_at_zero_detuning():
    on = _cert(detuning=0.0, damping=1.0, overlap_factor=0.6)
    off = _cert(detuning=5.0, damping=1.0, overlap_factor=0.6)
    assert on.transfer_efficiency() == pytest.approx(0.6)
    assert off.transfer_efficiency() < on.transfer_efficiency()


def test_overlap_and_damping_are_bounded():
    with pytest.raises(B.BridgeError):
        _cert(overlap_factor=1.5)
    with pytest.raises(B.BridgeError):
        _cert(damping=-1.0)


def test_digest_is_stable_and_sensitive():
    a = _cert()
    assert a.digest == _cert().digest
    assert a.digest != _cert(coupling_operator="different law").digest


def test_report_states_the_new_rule_and_claims_nothing():
    r = B.bridge_report()
    assert r["rule"] == ["NO_AUTOMATIC_EQUIVALENCE",
                         "TRANSFER_ALLOWED_WITH_EXPLICIT_COUPLING_CERTIFICATE"]
    assert len(r["required_declarations"]) == 9
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert "superseded, not deleted" in r["supersedes"]
