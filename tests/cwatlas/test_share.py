"""P39 -- CW URI/share: round-trip, private-in-URI refused, QR-absent handled."""

from __future__ import annotations

import pytest

from cwatlas import share
from cwatlas.claims import ClaimClass, ClaimError
from cwatlas.privacy import PrivacyError

VECTOR = "v=1.0.0;codec=CW-GEO-1;body=EARTH;frame=WGS84;epoch=2020.0;lat=5;lon=7"


def _uri() -> share.CwUri:
    return share.CwUri(
        namespace="terra", codec="CW-GEO-1", vector=VECTOR,
        frame="WGS84", epoch="2020.0")


# --- round-trip -------------------------------------------------------------

def test_uri_format_parse_round_trip():
    u = _uri()
    text = share.format_cw_uri(u)
    assert text.startswith("cw://terra/CW-GEO-1/")
    back = share.parse_cw_uri(text)
    assert back == u
    assert back.vector == VECTOR  # payload survives percent-encoding


def test_frame_and_epoch_carried_in_uri():
    text = share.format_cw_uri(_uri())
    assert "frame=WGS84" in text
    assert "epoch=2020.0" in text


def test_clipboard_string_contains_uri_and_receipt():
    block = share.to_clipboard_string(_uri(), note="synthetic demo")
    assert "cw://terra/CW-GEO-1/" in block
    assert "frame=WGS84" in block
    assert "epoch=2020.0" in block


# --- determinism ------------------------------------------------------------

def test_format_is_deterministic():
    assert share.format_cw_uri(_uri()) == share.format_cw_uri(_uri())


# --- negative: privacy ------------------------------------------------------

def test_private_token_in_vector_refused():
    bad = share.CwUri(
        namespace="terra", codec="CW-GEO-1",
        vector="C:\\Users\\someone;lat=5", frame="WGS84", epoch="2020.0")
    with pytest.raises(PrivacyError):
        share.format_cw_uri(bad)


def test_private_token_in_parse_refused():
    with pytest.raises(PrivacyError):
        share.parse_cw_uri("cw://terra/CW-GEO-1/onedrive%20-%20x?"
                           "frame=WGS84&epoch=2020.0")


def test_private_note_in_clipboard_refused():
    with pytest.raises(PrivacyError):
        share.to_clipboard_string(_uri(), note="path C:\\Users\\me")


# --- negative: malformed URI ------------------------------------------------

def test_wrong_scheme_refused():
    with pytest.raises(share.ShareError):
        share.parse_cw_uri("http://terra/CW-GEO-1/v?frame=W&epoch=1")


def test_missing_frame_epoch_refused():
    with pytest.raises(share.ShareError):
        share.parse_cw_uri("cw://terra/CW-GEO-1/v")


def test_missing_namespace_refused():
    with pytest.raises((share.ShareError, ClaimError)):
        share.CwUri(namespace="", codec="CW-GEO-1", vector="v",
                    frame="WGS84", epoch="2020.0")


def test_bad_path_shape_refused():
    with pytest.raises(share.ShareError):
        share.parse_cw_uri("cw://terra/only-one-segment?frame=W&epoch=1")


def test_empty_frame_refused_by_claim_boundary():
    # A share pin without a CRS/epoch is refused at construction (invariant 9).
    with pytest.raises((ClaimError, share.ShareError)):
        share.CwUri(namespace="terra", codec="CW-GEO-1", vector="v",
                    frame="", epoch="2020.0")


# --- QR: optional, absence handled ------------------------------------------

def test_qr_result_always_carries_uri():
    res = share.make_qr(_uri())
    assert res.uri.startswith("cw://terra/")
    # QR may or may not be available depending on the optional package; either
    # way the result is well-formed and never raises.
    assert isinstance(res.available, bool)
    if not res.available:
        assert "QR_UNAVAILABLE" in res.note
        assert res.payload is None
    else:
        assert res.payload is not None


def test_qr_absent_is_graceful(monkeypatch):
    # Force the optional import to fail and confirm graceful degradation.
    import builtins
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "qrcode":
            raise ImportError("simulated missing qrcode")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    res = share.make_qr(_uri())
    assert res.available is False
    assert "QR_UNAVAILABLE" in res.note
    assert res.uri.startswith("cw://terra/")


def test_qr_refuses_private_before_generation(monkeypatch):
    bad = share.CwUri(
        namespace="terra", codec="CW-GEO-1",
        vector="C:\\Users\\x;lat=5", frame="WGS84", epoch="2020.0")
    with pytest.raises(PrivacyError):
        share.make_qr(bad)


# --- governance report ------------------------------------------------------

def test_report_shape():
    r = share.share_report()
    assert r["claim_class"] == ClaimClass.MATHEMATICAL_TRANSLATION.value
    assert r["tracking_parameters"] == "NONE"
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
    assert r["invariant"] == "PERSONAL_DATA_NEVER_IN_A_URL"
