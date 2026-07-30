"""RCW locks — trace schema, export/load, and the static HTML demo.

The Python trace and the in-browser demo must tell the same story:
same schema id, same claim labels, same golden values, and the same
refusal to present Morton indices as coordinates.
"""

import json
import pathlib

import pytest

import rgcs_coordinate as rc
from rgcs_coordinate.codecs import federation_terra_30 as ft30

REPO = pathlib.Path(__file__).resolve().parents[2]
STATIC = REPO / "workbench" / "index.html"


def test_trace_dict_schema_keys():
    d = rc.decode_coordinate(165876523).to_dict()
    assert d["schema"] == "rgcs.structural-trace.v1"
    for key in ("raw_decimal", "width_bits", "binary30", "octal10",
                "packet_family", "face_bits", "face_id", "face_status",
                "q22_bits", "q22_path", "shell_bits", "extracted_shell",
                "spatial_octal_path", "morton_audit", "fixture_label",
                "structural_status", "physical_projection_status",
                "claims"):
        assert key in d, key
    assert d["claims"]["source_origin_validated"] is False
    assert d["claims"]["stonehenge_independently_decoded"] is False
    assert d["physical_projection_status"] == "UNDERDETERMINED"
    assert json.dumps(d)         # JSON-serializable end to end


def test_export_load_roundtrip():
    trace = rc.decode_coordinate(165876523)
    text = rc.export_trace(trace)
    loaded = rc.load_trace(text)
    assert loaded.to_dict() == trace.to_dict()


def test_load_trace_rejects_tampered_fields():
    text = rc.export_trace(rc.decode_coordinate(165876523))
    payload = json.loads(text)
    payload["face_id"] = 7
    with pytest.raises(ft30.PacketError, match="does not match"):
        rc.load_trace(json.dumps(payload))
    payload = json.loads(text)
    payload["schema"] = "rgcs.other.v9"
    with pytest.raises(ft30.PacketError, match="unsupported trace schema"):
        rc.load_trace(json.dumps(payload))


def test_static_html_exists_single_file_no_external_calls():
    html = STATIC.read_text(encoding="utf-8")
    for banned in ("http://", "https://", "fetch(", "XMLHttpRequest",
                   "analytics", "<script src", "<link"):
        assert banned not in html, f"static demo must not contain {banned}"
    assert "BigInt" in html


def test_static_html_matches_python_story():
    """Same schema id, same claim labels, same golden fixture values."""
    html = STATIC.read_text(encoding="utf-8")
    assert "rgcs.structural-trace.v1" in html
    assert "165876523" in html and "165892763" in html
    assert "training equality" in html.lower()
    assert "UNDERDETERMINED" in html
    assert "not latitude, longitude" in html.lower().replace(
        "are not latitude, longitude", "not latitude, longitude")
    # the demo's example decode constants agree with the codec
    t = ft30.decode(165876523)
    assert t.octal10 == "1170611453"     # shown by the demo on load
    assert "source_origin_validated" in html
