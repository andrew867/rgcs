"""P35 -- advanced icosahedral CW vector: round-trip, negative, schema."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cwatlas.ico_vector import (
    BITS_PER_DIGIT,
    IcoVector,
    IcoVectorError,
    address_to_ico_vector,
    direction_to_latlon,
    ico_vector_report,
    ico_vector_to_address,
    latlon_to_direction,
    parse_token_string,
)
from cwatlas.map_to_address import map_click_to_address

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "cwatlas" / "schemas"


def _validator():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(
        (SCHEMA_DIR / "geospatial_address.schema.json").read_text("utf-8"))
    return jsonschema.Draft202012Validator(schema)


def _addr(**over):
    base = dict(
        body_id="EARTH", frame_id="ITRF2020", epoch="2020.0",
        latitude_deg=45.0, longitude_deg=-73.5, uncertainty_m=1.0,
        height_m=142.0)
    base.update(over)
    return map_click_to_address(**base)


# -- POWER round-trip -------------------------------------------------------

def test_address_to_ico_to_address_is_exact():
    a = _addr()
    vec = address_to_ico_vector(a, depth=12)
    back = ico_vector_to_address(vec)
    assert back.latitude_deg == pytest.approx(a.latitude_deg, abs=1e-7)
    assert back.longitude_deg == pytest.approx(a.longitude_deg, abs=1e-7)
    assert back.body_id == a.body_id
    assert back.frame_id == a.frame_id
    assert back.epoch == a.epoch
    assert back.height_m == pytest.approx(a.height_m)


def test_latlon_direction_round_trip():
    lat, lon = direction_to_latlon(latlon_to_direction(-33.87, 151.21))
    assert lat == pytest.approx(-33.87, abs=1e-9)
    assert lon == pytest.approx(151.21, abs=1e-9)


def test_depth_12_path_packs_to_36_bits():
    vec = address_to_ico_vector(_addr(), depth=12)
    assert vec.depth == 12
    assert BITS_PER_DIGIT * vec.depth == 36


@pytest.mark.parametrize("depth", [0, 1, 6, 12])
def test_round_trip_at_selectable_depths(depth):
    a = _addr(latitude_deg=12.5, longitude_deg=88.25)
    back = ico_vector_to_address(address_to_ico_vector(a, depth=depth))
    assert back.latitude_deg == pytest.approx(a.latitude_deg, abs=1e-7)
    assert back.longitude_deg == pytest.approx(a.longitude_deg, abs=1e-7)


def test_token_string_serializes_and_parses_exactly():
    vec = address_to_ico_vector(_addr(shell_state=2), depth=12)
    parsed = parse_token_string(vec.token_string())
    assert parsed.payload() == vec.payload()
    assert parsed.shell_state == 2


def test_token_display_shows_face_and_checksum():
    disp = address_to_ico_vector(_addr(), depth=12).token_display()
    assert "CW-HCM-ICO" in disp
    assert "face=" in disp
    assert "cwck1:" in disp


def test_mars_address_round_trips():
    a = _addr(body_id="MARS", frame_id="IAU_MARS_BODY_FIXED")
    back = ico_vector_to_address(address_to_ico_vector(a, depth=10))
    assert back.body_id == "MARS"
    assert back.latitude_deg == pytest.approx(a.latitude_deg, abs=1e-7)


# -- negative ---------------------------------------------------------------

def test_corrupted_checksum_is_refused():
    vec = address_to_ico_vector(_addr(), depth=8)
    tampered = IcoVector(
        codec_id=vec.codec_id, codec_version=vec.codec_version,
        body_id=vec.body_id, frame_id=vec.frame_id, epoch=vec.epoch,
        face_id=vec.face_id, path=vec.path, residual=vec.residual,
        height_m=vec.height_m, shell_state=vec.shell_state,
        checksum="cwck1:deadbeefdeadbeef")
    assert not tampered.verify_checksum()
    with pytest.raises(IcoVectorError):
        ico_vector_to_address(tampered)


def test_negative_depth_is_refused():
    with pytest.raises(IcoVectorError):
        address_to_ico_vector(_addr(), depth=-1)


def test_excessive_depth_is_refused():
    with pytest.raises(IcoVectorError):
        address_to_ico_vector(_addr(), depth=99)


def test_unknown_body_is_refused_on_encode():
    a = _addr()
    object.__setattr__(a, "body_id", "PLUTO")  # bypass constructor guard
    with pytest.raises(Exception):
        address_to_ico_vector(a, depth=6)


def test_corrupted_token_string_is_refused():
    tok = address_to_ico_vector(_addr(), depth=8).token_string()
    with pytest.raises(IcoVectorError):
        parse_token_string(tok.replace("face=", "face=9"))


# -- determinism ------------------------------------------------------------

def test_encoding_is_deterministic():
    a = _addr()
    assert (address_to_ico_vector(a, depth=12).payload()
            == address_to_ico_vector(a, depth=12).payload())


# -- schema conformance -----------------------------------------------------

def test_decoded_address_conforms_to_schema():
    validator = _validator()
    back = ico_vector_to_address(address_to_ico_vector(_addr(), depth=12))
    validator.validate(back.to_dict())


# -- report -----------------------------------------------------------------

def test_report_declares_canonical_round_trip():
    r = ico_vector_report()
    assert r["claim_class"] == "CANONICAL_ROUND_TRIP"
    assert r["cwpack40_path_bits"] == 36
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
