"""RCW P02 locks — structural codec: goldens, parity, properties.

The public codec must agree bit-for-bit with the frozen repository
parser (``r12.icosapacket``) on every golden vector AND on a
deterministic exhaustive-property sweep — the frozen parser stays the
authority; the public module is an adapter of it, never a
reinterpretation.
"""

import random

import pytest

from r12 import icosapacket as pk

from rgcs_coordinate.codecs import federation_terra_30 as ft30
from rgcs_coordinate.provenance import corpus


def test_stonehenge_golden_vector():
    t = ft30.decode(165876523)
    assert t.binary30 == "001001111000110001001100101011"
    assert t.octal10 == "1170611453"
    assert t.face_id == 4 and t.face_status == "valid-source-face-range"
    assert t.q22_bits == "1111000110001001100101"
    assert t.q22_path == (3, 3, 0, 1, 2, 0, 2, 1, 2, 1, 1)
    assert t.extracted_shell == 3
    assert t.spatial_octal_path == "117061145"
    m = t.morton_audit
    assert (m.x_index, m.y_index, m.z_index) == (83, 80, 461)
    assert (m.x_bits, m.y_bits, m.z_bits) == (
        "001010011", "001010000", "111001101")
    assert ft30.encode(t.face_id, t.q22_path, t.extracted_shell) \
        == 165876523


def test_orange_slice_golden_vectors():
    """Raw extractions verbatim: shells 7, 3, 7 — the corpus layer, not
    the codec, carries the operator correction to active 7,7,7."""
    shells = [ft30.decode(int(v)).extracted_shell
              for v in ("165892743", "165892763", "165892783")]
    assert shells == [7, 3, 7]
    assert corpus.orange_slice_active_shells() == (7, 7, 7)


def test_bit_parity_with_frozen_r12_parser_on_corpus():
    for v in corpus.vectors():
        raw = int(v.raw_decimal)
        face, path, shell = pk.decode(raw)
        t = ft30.decode(raw)
        assert t.face_id == face
        assert t.q22_path == tuple(pk.path_levels(path))
        assert t.extracted_shell == shell
        rec = pk.decode_record(raw)
        assert t.binary30 == rec["bits"]
        assert t.octal10 == rec["octal"]


def test_bit_parity_property_sweep_deterministic():
    """5000 seeded random words + the range edges: public codec and
    frozen parser agree exactly, and round-trips are exact."""
    rng = random.Random(1085)
    words = [0, 1, (1 << 30) - 1] + \
        [rng.randrange(1 << 30) for _ in range(5000)]
    for raw in words:
        t = ft30.decode(raw)
        assert int(t.binary30, 2) == raw and int(t.octal10, 8) == raw
        if t.face_id <= 19:
            face, path, shell = pk.decode(raw)
            assert (t.face_id, t.q22_path, t.extracted_shell) == \
                (face, tuple(pk.path_levels(path)), shell)
            assert ft30.encode(t.face_id, t.q22_path,
                               t.extracted_shell) == raw
        else:
            # declared difference, not drift: the frozen parser REFUSES
            # reserved faces (20..31 name no icosahedron face); the
            # public codec decodes the fields and labels them reserved
            # so a user sees WHY the word is malformed. Same authority,
            # different reporting surface — locked here.
            assert t.face_status == "reserved"
            with pytest.raises(Exception):
                pk.decode(raw)


def test_out_of_family_values_refused_never_truncated():
    with pytest.raises(ft30.PacketError, match="SEPARATE family"):
        ft30.decode(1 << 30)
    with pytest.raises(ft30.PacketError, match="non-negative"):
        ft30.decode(-1)
    for v in ("1678523973", "16752349783"):
        with pytest.raises(ft30.PacketError):
            ft30.decode(int(v))


def test_encode_guards():
    with pytest.raises(ft30.PacketError, match="reserved"):
        ft30.encode(20, (0,) * 11, 0)
    with pytest.raises(ft30.PacketError, match="quaternary"):
        ft30.encode(4, (0,) * 10, 0)
    with pytest.raises(ft30.PacketError, match="S3"):
        ft30.encode(4, (0,) * 11, 8)


def test_reserved_face_status():
    # craft a word with face 21 via raw bits (decode allows, labels it)
    raw = int("10101" + "0" * 22 + "000", 2)
    t = ft30.decode(raw)
    assert t.face_id == 21 and t.face_status == "reserved"


def test_morton_indices_refuse_coordinate_reading():
    with pytest.raises(ft30.PacketError, match="not latitude"):
        ft30.refuse_indices_as_coordinates("latitude")
