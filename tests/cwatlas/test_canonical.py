"""P17 -- canonical CW object schema: focused, negative, schema-conformance."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cwatlas import canonical as K
from cwatlas.canonical import (
    CanonicalCoordinate,
    CanonicalCWAddress,
    CodecResult,
    CodecStatus,
)

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "cwatlas" / "schemas"


def _cw_vector_validator():
    """A jsonschema validator whose registry resolves the provenance $ref."""
    jsonschema = pytest.importorskip("jsonschema")
    from referencing import Registry, Resource

    cw = json.loads((SCHEMA_DIR / "cw_vector.schema.json").read_text("utf-8"))
    prov = json.loads(
        (SCHEMA_DIR / "provenance_event.schema.json").read_text("utf-8"))
    registry = Registry().with_resources([
        ("provenance_event.schema.json", Resource.from_contents(prov)),
        ("cw_vector.schema.json", Resource.from_contents(cw)),
    ])
    return jsonschema.Draft202012Validator(cw, registry=registry)


def _codec_result_schema():
    return json.loads((SCHEMA_DIR / "codec_result.schema.json").read_text("utf-8"))


def _coord(**over):
    base = dict(
        body_id="EARTH", frame_id="ITRF2020", epoch="2020.0",
        latitude_deg=51.178882, longitude_deg=-1.826215, height_m=142.0,
    )
    base.update(over)
    return CanonicalCoordinate(**base)


def _address():
    coord = _coord()
    raw = "v=1.0.0;codec=CW-GEO-1;body=EARTH;frame=ITRF2020;epoch=2020.0;lat=1;lon=2;h=0;shell=-"
    from cwatlas import checksums
    return CanonicalCWAddress(
        version="1.0.0",
        namespace=K.NAMESPACE,
        body_id="EARTH",
        frame_id="ITRF2020",
        epoch="2020.0",
        horizontal_coordinate=(coord.latitude_deg, coord.longitude_deg),
        radial_coordinate=coord.height_m,
        shell_state=None,
        local_residual=(0.0, 0.0, 0.0),
        codec_id="CW-GEO-1",
        checksum=checksums.checksum(raw),
        uncertainty=0.001,
        provenance=K.make_provenance(raw, epoch="2020.0"),
        raw=raw,
    )


# -- focused ----------------------------------------------------------------

def test_coordinate_normalizes_longitude_to_dateline_positive():
    c = _coord(longitude_deg=-180.0)
    assert c.longitude_deg == pytest.approx(180.0)


def test_address_exposes_all_architecture_fields():
    a = _address()
    for fieldname in (
        "version", "namespace", "body_id", "frame_id", "epoch",
        "horizontal_coordinate", "radial_coordinate", "shell_state",
        "local_residual", "codec_id", "checksum", "uncertainty", "provenance",
    ):
        assert hasattr(a, fieldname)


def test_address_checksum_verifies_and_detects_corruption():
    a = _address()
    assert a.verify_checksum()
    from cwatlas import checksums
    tampered = CanonicalCWAddress(
        version=a.version, namespace=a.namespace, body_id=a.body_id,
        frame_id=a.frame_id, epoch=a.epoch,
        horizontal_coordinate=a.horizontal_coordinate,
        radial_coordinate=a.radial_coordinate, shell_state=a.shell_state,
        local_residual=a.local_residual, codec_id=a.codec_id,
        checksum=a.checksum, uncertainty=a.uncertainty, provenance=a.provenance,
        raw=a.raw.replace("lat=1", "lat=9"),
    )
    assert not tampered.verify_checksum()  # raw changed, checksum no longer binds
    assert checksums is not None


# -- schema conformance -----------------------------------------------------

def test_vector_dict_conforms_to_cw_vector_schema():
    validator = _cw_vector_validator()
    validator.validate(_address().to_vector_dict())


def test_codec_result_conforms_to_schema():
    jsonschema = pytest.importorskip("jsonschema")
    result = CodecResult(
        status=CodecStatus.OK_POINT, codec_id="CW-GEO-1",
        candidates=({"latitude_deg": 51.0, "longitude_deg": -1.0},),
        receipt_id="rcpt-0001",
    )
    jsonschema.validate(result.to_dict(), _codec_result_schema())


def test_invalid_result_conforms_to_schema():
    jsonschema = pytest.importorskip("jsonschema")
    result = CodecResult(
        status=CodecStatus.INVALID, codec_id="CW-GEO-1",
        candidates=(), receipt_id="rcpt-0002", warnings=("bad checksum",))
    jsonschema.validate(result.to_dict(), _codec_result_schema())


# -- negative: fail safely --------------------------------------------------

def test_missing_frame_or_epoch_is_refused():
    from cwatlas import claims
    with pytest.raises(claims.ClaimError):
        _coord(frame_id="")
    with pytest.raises(claims.ClaimError):
        _coord(epoch="")


def test_out_of_range_latitude_is_refused():
    with pytest.raises(K.CanonicalError):
        _coord(latitude_deg=90.5)


def test_out_of_range_shell_is_refused():
    with pytest.raises(K.CanonicalError):
        _coord(shell_state=9)


def test_non_finite_coordinate_is_refused():
    with pytest.raises(K.CanonicalError):
        _coord(latitude_deg=float("nan"))


def test_address_without_raw_is_refused():
    a = _address()
    with pytest.raises(K.CanonicalError):
        CanonicalCWAddress(
            version=a.version, namespace=a.namespace, body_id=a.body_id,
            frame_id=a.frame_id, epoch=a.epoch,
            horizontal_coordinate=a.horizontal_coordinate,
            radial_coordinate=a.radial_coordinate, shell_state=a.shell_state,
            local_residual=a.local_residual, codec_id=a.codec_id,
            checksum=a.checksum, uncertainty=a.uncertainty,
            provenance=a.provenance, raw="")


def test_negative_uncertainty_is_refused():
    a = _address()
    with pytest.raises(K.CanonicalError):
        CanonicalCWAddress(
            version=a.version, namespace=a.namespace, body_id=a.body_id,
            frame_id=a.frame_id, epoch=a.epoch,
            horizontal_coordinate=a.horizontal_coordinate,
            radial_coordinate=a.radial_coordinate, shell_state=a.shell_state,
            local_residual=a.local_residual, codec_id=a.codec_id,
            checksum=a.checksum, uncertainty=-1.0,
            provenance=a.provenance, raw=a.raw)


def test_positive_result_requires_a_candidate():
    with pytest.raises(K.CanonicalError):
        CodecResult(status=CodecStatus.OK_POINT, codec_id="CW-GEO-1",
                    candidates=(), receipt_id="rcpt-0003")


def test_bad_status_type_is_refused():
    with pytest.raises(K.CanonicalError):
        CodecResult(status="OK_POINT", codec_id="CW-GEO-1",
                    candidates=({"x": 1},), receipt_id="rcpt-0004")


# -- determinism + report ---------------------------------------------------

def test_provenance_is_deterministic():
    raw = "v=1.0.0;codec=CW-GEO-1;body=EARTH;frame=ITRF2020;epoch=2020.0;lat=1;lon=2;h=0;shell=-"
    assert K.make_provenance(raw, epoch="2020.0") == K.make_provenance(raw, epoch="2020.0")


def test_report_claims_nothing_physical():
    r = K.canonical_report()
    assert r["claim_class"] == "CANONICAL_ROUND_TRIP"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
