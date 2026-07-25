"""P34 -- geospatial address to CW-GEO-1 vector: round-trip, negative, schema."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cwatlas.address_to_vector import (
    AddressVectorError,
    address_to_vector,
    address_to_vector_report,
    vector_to_address,
)
from cwatlas.map_to_address import map_click_to_address

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "cwatlas" / "schemas"


def _validator():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(
        (SCHEMA_DIR / "geospatial_address.schema.json").read_text("utf-8"))
    return jsonschema.Draft202012Validator(schema)


def _addr(**over):
    # Grid-aligned lat/lon (multiples of 1e-8 deg) so CW-GEO-1 round-trips exact.
    base = dict(
        body_id="EARTH", frame_id="ITRF2020", epoch="2020.0",
        latitude_deg=45.0, longitude_deg=-73.5, uncertainty_m=1.0,
        height_m=142.0)
    base.update(over)
    return map_click_to_address(**base)


# -- POWER round-trip -------------------------------------------------------

def test_address_to_vector_to_address_is_exact():
    a = _addr()
    enc = address_to_vector(a)
    back = vector_to_address(enc.vector)
    assert back.latitude_deg == pytest.approx(a.latitude_deg, abs=1e-8)
    assert back.longitude_deg == pytest.approx(a.longitude_deg, abs=1e-8)
    assert back.height_m == pytest.approx(a.height_m, abs=1e-4)
    assert back.body_id == a.body_id
    assert back.frame_id == a.frame_id
    assert back.epoch == a.epoch


def test_round_trip_carries_shell_state():
    a = _addr(shell_state=5)
    back = vector_to_address(address_to_vector(a).vector)
    assert back.shell_state == 5


def test_mars_address_round_trips():
    a = _addr(body_id="MARS", frame_id="IAU_MARS_BODY_FIXED")
    back = vector_to_address(address_to_vector(a).vector)
    assert back.body_id == "MARS"
    assert back.latitude_deg == pytest.approx(a.latitude_deg, abs=1e-8)


def test_vector_carries_checksum_and_verifies():
    enc = address_to_vector(_addr())
    assert enc.verify()
    assert enc.canonical.verify_checksum()


# -- negative ---------------------------------------------------------------

def test_corrupted_vector_is_refused():
    enc = address_to_vector(_addr())
    tampered = enc.vector.replace("lat=", "lat=9")
    with pytest.raises(AddressVectorError):
        vector_to_address(tampered)


def test_non_address_input_is_refused():
    with pytest.raises(AddressVectorError):
        address_to_vector("not an address")  # type: ignore[arg-type]


def test_garbage_vector_is_refused():
    with pytest.raises(AddressVectorError):
        vector_to_address("v=1.0.0;codec=CW-GEO-1;garbage")


# -- determinism ------------------------------------------------------------

def test_encoding_is_deterministic():
    assert address_to_vector(_addr()).vector == address_to_vector(_addr()).vector


# -- schema conformance -----------------------------------------------------

def test_decoded_address_conforms_to_schema():
    validator = _validator()
    back = vector_to_address(address_to_vector(_addr()).vector)
    validator.validate(back.to_dict())


# -- report -----------------------------------------------------------------

def test_report_declares_canonical_round_trip():
    r = address_to_vector_report()
    assert r["claim_class"] == "CANONICAL_ROUND_TRIP"
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
