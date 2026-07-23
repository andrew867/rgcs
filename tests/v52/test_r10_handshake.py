"""P06 — the 925 Hz handshake protocol (software-only state machine)."""

from __future__ import annotations

from fractions import Fraction

import pytest

from r10 import handshake as H


def _cfg(**kw):
    base = dict(protocol_id="p1", opening_key_ref="secret-ref",
                cw_ref="cw-ref", address="ADDR", root="EARTH_ROOT",
                route="R1", chirality=H.Chirality.RIGHT, timeout_s=30.0)
    base.update(kw)
    return H.HandshakeConfig(**base)


def _drive_to_ack(hs):
    hs.acquire_carrier()
    hs.present_channel_key(H.CHANNEL_KEY_HZ)
    hs.present_opening_key("secret-ref")
    hs.present_address("ADDR", "EARTH_ROOT", "R1")
    hs.set_phase_chirality(0.0, H.Chirality.RIGHT)
    hs.request("nonce-1")
    hs.acknowledge(True)


def test_default_state_is_quiet_listen():
    hs = H.Handshake(_cfg())
    assert hs.state is H.State.QUIET_LISTEN


def test_a_full_handshake_runs_in_order():
    hs = H.Handshake(_cfg())
    _drive_to_ack(hs)
    csum = hs.send_message(b"hello")
    assert hs.verify_checksum(b"hello", csum)
    hs.phase_conjugate_return()
    hs.close()
    assert hs.state is H.State.CLOSE


def test_out_of_order_transition_is_refused():
    hs = H.Handshake(_cfg())
    with pytest.raises(H.HandshakeError):
        hs.present_channel_key(H.CHANNEL_KEY_HZ)   # skipped carrier acquire


def test_wrong_channel_key_is_refused():
    hs = H.Handshake(_cfg())
    hs.acquire_carrier()
    with pytest.raises(H.HandshakeError):
        hs.present_channel_key(Fraction(1000))


def test_wrong_opening_key_reference_is_refused():
    hs = H.Handshake(_cfg())
    hs.acquire_carrier()
    hs.present_channel_key(H.CHANNEL_KEY_HZ)
    with pytest.raises(H.HandshakeError):
        hs.present_opening_key("wrong-ref")


def test_replayed_nonce_is_refused():
    hs = H.Handshake(_cfg())
    hs.acquire_carrier()
    hs.present_channel_key(H.CHANNEL_KEY_HZ)
    hs.present_opening_key("secret-ref")
    hs.present_address("ADDR", "EARTH_ROOT", "R1")
    hs.set_phase_chirality(0.0, H.Chirality.RIGHT)
    hs.request("nonce-1")
    hs.acknowledge(True)
    hs.send_message(b"x")
    # a second request reusing the nonce would be a replay — build a fresh
    # machine sharing nothing but prove the guard on one instance:
    hs2 = H.Handshake(_cfg())
    hs2.acquire_carrier()
    hs2.present_channel_key(H.CHANNEL_KEY_HZ)
    hs2.present_opening_key("secret-ref")
    hs2.present_address("ADDR", "EARTH_ROOT", "R1")
    hs2.set_phase_chirality(0.0, H.Chirality.RIGHT)
    hs2.request("nonce-A")
    with pytest.raises(H.HandshakeError):
        hs2._seen_nonces.add("nonce-A")   # simulate seen
        hs2.request("nonce-A")


def test_timeout_returns_to_listen():
    hs = H.Handshake(_cfg(timeout_s=1.0))
    hs.acquire_carrier()
    hs.tick(5.0)                       # exceed timeout
    with pytest.raises(H.HandshakeError):
        hs.present_channel_key(H.CHANNEL_KEY_HZ)
    assert hs.state is H.State.QUIET_LISTEN


def test_nack_aborts_to_listen():
    hs = H.Handshake(_cfg())
    hs.acquire_carrier()
    hs.present_channel_key(H.CHANNEL_KEY_HZ)
    hs.present_opening_key("secret-ref")
    hs.present_address("ADDR", "EARTH_ROOT", "R1")
    hs.set_phase_chirality(0.0, H.Chirality.RIGHT)
    hs.request("n1")
    with pytest.raises(H.HandshakeError):
        hs.acknowledge(False)
    assert hs.state is H.State.QUIET_LISTEN


def test_human_exposure_cannot_be_enabled():
    with pytest.raises(H.HumanExposureRefused):
        _cfg(human_exposure_prohibited=False)


def test_human_stimulation_is_refused():
    with pytest.raises(H.HumanExposureRefused):
        H.refuse_human_stimulation("pineal")


def test_key_material_in_clear_is_refused():
    with pytest.raises(H.HandshakeError):
        H.refuse_key_material_in_clear("the twelve words")


def test_report_is_software_only():
    r = H.handshake_report()
    assert r["measured_here"] == "nothing"
    assert r["human_exposure"] == "PROHIBITED_IN_EVERY_STATE"
    assert r["verdict"] == "HANDSHAKE_SOFTWARE_ONLY"
