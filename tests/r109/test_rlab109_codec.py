"""R10.9 acceptance — compact packet, depth dispatch, refusals."""

from __future__ import annotations

import pytest

from r109 import codec, face_node, superseded
from r109.types import CodecTypeError, CompactAddress, WireAddress


COMPACT_FIXTURES = {
    165876523: (4, (3, 3, 0, 1, 2, 0, 2, 1, 2, 1, 1), 3, "1170611453"),
    167849523: (5, (0, 0, 0, 0, 2, 1, 1, 3, 0, 1, 2), 3, "1200227063"),
    165879243: (4, (3, 3, 0, 1, 2, 0, 3, 2, 3, 2, 1), 3, "1170616713"),
    168930443: (5, (0, 0, 2, 0, 3, 1, 1, 2, 1, 0, 1), 3, "1204326213"),
    167854923: (5, (0, 0, 0, 0, 2, 2, 0, 1, 2, 2, 1), 3, "1200241513"),
}


@pytest.mark.parametrize("raw,expected", COMPACT_FIXTURES.items())
def test_compact_decodes_exactly(raw, expected):
    f5, path, s3, octal = expected
    wire = WireAddress.from_raw(raw, "test")
    assert wire.octal == octal and wire.octal_depth == 10
    compact, trace = codec.decode_compact(wire)
    assert compact.f5 == f5
    assert compact.q22_path == path
    assert compact.s3 == s3
    assert codec.encode_compact(compact) == raw          # encode(decode(x)) == x


def test_montreal_direct_is_compact_authority():
    wire = WireAddress.from_raw(165879243, "R109-MTL-01")
    compact, trace = codec.decode_compact(wire)
    assert trace["binary30"] == "001001111000110001110111001011"
    assert trace["octal10"] == "1170616713"
    assert compact.f5 == 4 and compact.s3 == 3
    assert compact.q22_path == (3, 3, 0, 1, 2, 0, 3, 2, 3, 2, 1)


def test_depth_dispatch_t10_t11():
    assert codec.classify(WireAddress.from_raw(165876523, "t")) == "T10"
    assert codec.classify(WireAddress.from_raw(1643789253, "t")) == "T11"
    assert codec.classify(WireAddress.from_raw(1672875493, "t")) == "T11"


def test_long_values_never_truncated():
    wire = WireAddress.from_raw(1643789253, "t")
    with pytest.raises(CodecTypeError):
        codec.decode_compact(wire)
    with pytest.raises(CodecTypeError):
        codec.refuse_truncation(1643789253)


def test_stale_affine_bridge_disabled_in_production():
    with pytest.raises(CodecTypeError, match="superseded"):
        codec.refuse_affine_bridge(1643789253)
    # historical replay demands the exact profile id
    with pytest.raises(CodecTypeError):
        superseded.historical_affine(43789253)
    y = superseded.historical_affine(
        43789253, profile=superseded.HISTORICAL_PROFILE)
    assert y == 165876523      # archived arithmetic reproduces exactly


def test_superseded_montreal_transcription_not_current():
    from r109.registry import assert_fit_allowed, RegistryError, record
    assert record(168729543).status == "SUPERSEDED"
    with pytest.raises(RegistryError):
        assert_fit_allowed(168729543)
    with pytest.raises(RegistryError):
        assert_fit_allowed(168500683)


def test_decimal_triplet_xyz_refused():
    with pytest.raises(CodecTypeError):
        codec.refuse_decimal_triplet_xyz(165876523)


def test_face_node_arithmetic():
    assert face_node.NODE_23 == 23
    assert face_node.node_state(23) == 23
    assert face_node.STONEHENGE_TOP_SIX_STATE == 9
    assert face_node.FACE_OFFSET == 14                    # 23 - 9
    assert face_node.source_face(4) == 18                 # (F5 + 14) mod 20
    assert face_node.source_face(5) == 19
    with pytest.raises(CodecTypeError):
        face_node.node_state(64)                          # six-bit bound


def test_literal_face_23_refused():
    with pytest.raises(CodecTypeError):
        face_node.source_face(23)
    with pytest.raises(CodecTypeError):
        face_node.refuse_literal_face_23()
    with pytest.raises(CodecTypeError):
        codec.refuse_reserved_face_promotion(23)
    from rgcs_coordinate.codecs import federation_terra_30 as t10
    with pytest.raises(t10.PacketError):
        t10.encode(23, (0,) * 11, 3)                      # frozen parser refuses


def test_face_order_authority_is_source_reported():
    a = face_node.FACE_ORDER_AUTHORITY
    assert a["root_feature"] == "Wilkes face"
    assert a["routing_graph"] == "dodecahedral dual"
    assert a["order"] == "clockwise"
    assert a["phase_zero"] == "SAA direction"
    assert a["evidence_class"] == "SOURCE_REPORTED"
