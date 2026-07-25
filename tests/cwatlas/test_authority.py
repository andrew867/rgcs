"""P06 — frame, epoch, and root authority registry tests."""

from __future__ import annotations

import dataclasses

import pytest

from cwatlas import authority as A


def test_register_and_lookup_round_trips():
    reg = A.AuthorityRegistry()
    cert = reg.register_new(
        A.AuthorityType.ORIENTATION, "SYNTH_ORIENT_A", "1.0.0",
        {"body_id": "EARTH", "kind": "orientation_profile"})
    got = reg.lookup(A.AuthorityType.ORIENTATION, "SYNTH_ORIENT_A")
    assert got == cert
    # the certificate carries its authority + version so a decode can pin it
    assert got.authority_id == "SYNTH_ORIENT_A"
    assert got.version == "1.0.0"
    assert reg.is_registered(A.AuthorityType.ORIENTATION, "SYNTH_ORIENT_A")


def test_unregistered_frame_or_epoch_is_refused():
    reg = A.AuthorityRegistry()
    with pytest.raises(A.AuthorityError):
        reg.lookup(A.AuthorityType.FRAME, "NOPE")
    with pytest.raises(A.AuthorityError):
        reg.require_frame_epoch("ITRF2020", "EPOCH_2020_0")  # nothing registered


def test_frame_certificate_requires_schema_fields():
    # FRAME/EPOCH payloads must satisfy frame_epoch.schema.json required fields
    with pytest.raises(A.AuthorityError):
        A.make_certificate(A.AuthorityType.FRAME, "ITRF2020", "1.0.0",
                           {"body_id": "EARTH"})  # missing frame_id, epoch, ...
    ok = A.make_certificate(A.AuthorityType.FRAME, "ITRF2020", "1.0.0", {
        "body_id": "EARTH", "frame_id": "ITRF2020", "epoch": "2020.0",
        "time_scale": "TT_DECIMAL_YEAR", "orientation_profile_id": "SYNTH_ORIENT_A",
    })
    assert ok.verify()


def test_certificate_hash_is_stable_and_deterministic():
    payload = {"body_id": "EARTH", "kind": "planet"}
    c1 = A.make_certificate(A.AuthorityType.BODY, "EARTH", "1.0.0", payload)
    c2 = A.make_certificate(A.AuthorityType.BODY, "EARTH", "1.0.0", dict(payload))
    assert c1.hash == c2.hash                 # deterministic
    assert c1.hash.startswith("sha256:")
    assert c1 == c2                            # equal ignoring hash field
    assert c1.verify() and c2.verify()


def test_tamper_is_detected_on_verify_register_and_lookup():
    good = A.make_certificate(A.AuthorityType.BODY, "EARTH", "1.0.0",
                              {"body_id": "EARTH", "kind": "planet"})
    # forge a certificate: mutate the payload but keep the old hash
    forged = dataclasses.replace(good, payload={"body_id": "MARS", "kind": "planet"})
    assert not forged.verify()                 # hash no longer matches payload
    reg = A.AuthorityRegistry()
    with pytest.raises(A.AuthorityError):
        reg.register(forged)                   # tamper refused at registration
    # a certificate tampered after registration is caught on lookup too
    reg.register(good)
    reg._certs[(A.AuthorityType.BODY, "EARTH", "1.0.0")] = forged
    with pytest.raises(A.AuthorityError):
        reg.lookup(A.AuthorityType.BODY, "EARTH")


def test_versionless_lookup_refuses_when_ambiguous():
    reg = A.AuthorityRegistry()
    reg.register_new(A.AuthorityType.FRAME, "ITRF2020", "1.0.0", {
        "body_id": "EARTH", "frame_id": "ITRF2020", "epoch": "2020.0",
        "time_scale": "TT_DECIMAL_YEAR", "orientation_profile_id": "O"})
    reg.register_new(A.AuthorityType.FRAME, "ITRF2020", "2.0.0", {
        "body_id": "EARTH", "frame_id": "ITRF2020", "epoch": "2020.0",
        "time_scale": "TT_DECIMAL_YEAR", "orientation_profile_id": "O"})
    with pytest.raises(A.AuthorityError):           # no hidden default
        reg.lookup(A.AuthorityType.FRAME, "ITRF2020")
    # both legacy versions remain reachable when named explicitly
    assert reg.lookup(A.AuthorityType.FRAME, "ITRF2020", "1.0.0").version == "1.0.0"
    assert reg.lookup(A.AuthorityType.FRAME, "ITRF2020", "2.0.0").version == "2.0.0"


def test_default_registry_is_reachable_and_frame_epoch_pinnable():
    reg = A.default_registry()
    frame, epoch = reg.require_frame_epoch("ITRF2020", "EPOCH_2020_0")
    assert frame.authority_type is A.AuthorityType.FRAME
    assert epoch.authority_type is A.AuthorityType.EPOCH
    assert frame.verify() and epoch.verify()
    # every preloaded certificate verifies
    assert all(c.verify() for c in reg.certificates())


def test_report_ships_no_measurement_or_physical_claim():
    r = A.authority_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
    assert r["verdict"].startswith("GREEN_R10_8_1_P06")
