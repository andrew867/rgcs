"""R10.8.5 corrective-run tests — octal packet family (F5 | Q22 | S3).

Locks: decimal integer -> binary FIRST (never digit-triplets); exact
Stonehenge packet values; both established interpretations (octree bits,
face-local quaternary via the reused R12 operator); shell from the final
packet bits (never the final decimal digit); family separation for longer
vectors; radix identity 4096**3 = 8**12 = 2**36."""

import pytest

from cwatlas.r1082 import decoder_candidates as dc
from r12 import icosapacket as pk
from r12 import icosarefine as rf


def test_radix_identity():
    assert 4096 ** 3 == 8 ** 12 == 2 ** 36


def test_stonehenge_exact_packet():
    rec = pk.decode_record(165876523)
    assert rec["bits"] == "001001111000110001001100101011"
    assert rec["octal"] == "1170611453"
    assert rec["face"] == 4
    assert tuple(rec["path_levels"]) == (3, 3, 0, 1, 2, 0, 2, 1, 2, 1, 1)
    assert rec["shell"] == 3
    assert rec["round_trip"] and rec["octal_round_trip"]
    # the correct Q22 window (the prompt's printed string was off by one
    # bit position; the quaternary path above is the verified content)
    assert rec["path_bits"] == "1111000110001001100101"
    assert rec["face_bits"] == "00100" and rec["shell_bits"] == "011"


def test_stonehenge_octree_bit_interpretation():
    o = format(165876523, "010o")
    spatial = o[:9]
    assert spatial == "117061145" and o[9] == "3"
    xb = "".join(format(int(d, 8), "03b")[0] for d in spatial)
    yb = "".join(format(int(d, 8), "03b")[1] for d in spatial)
    zb = "".join(format(int(d, 8), "03b")[2] for d in spatial)
    assert (xb, yb, zb) == ("001010011", "001010000", "111001101")
    assert (int(xb, 2), int(yb, 2), int(zb, 2)) == (83, 80, 461)


def test_shell_from_packet_bits_not_decimal_digit():
    # decimal final digit of 165876523 is 3 AND shell is 3 — coincidence;
    # 165892743's decimal final digit is 3 but its packet shell is 7.
    assert pk.decode(165892743)[2] == 7
    assert pk.decode(165892763)[2] == 3
    assert pk.decode(165892783)[2] == 7


def test_orange_slice_does_not_survive_octal_conversion():
    """Model-free structural discriminant: the +20-decimal line breaks
    in the octal domain (shells differ, paths diverge at level 10)."""
    recs = [pk.decode(int(v)) for v in
            ("165892743", "165892763", "165892783")]
    assert [r[0] for r in recs] == [4, 4, 4]          # same face
    assert [r[2] for r in recs] == [7, 3, 7]          # shells differ
    paths = [pk.path_levels(r[1]) for r in recs]
    shared = 0
    for cs in zip(*paths):
        if len(set(cs)) != 1:
            break
        shared += 1
    assert shared == 9                                 # 9 of 11 levels


def test_r12_operator_reused_not_reinvented():
    # the quaternary operator is R12's frozen one: 4 children tile parent
    assert rf.CHILDREN_PER_TRIANGLE == 4
    tri = rf.face_triangle(0)
    kids = rf._subdivide(tri)
    assert len(kids) == 4
    cell = rf.cell_triangle(4, (3, 3, 0, 1, 2, 0, 2, 1, 2, 1, 1))
    assert len(cell) == 3


def test_longer_vectors_are_a_separate_family():
    for v in ("1678523973", "1678295343", "16752349783", "16782953437"):
        assert int(v).bit_length() > 30   # cannot be a 30-bit word
    with pytest.raises(Exception):
        pk.encode(21, (0,) * 11, 0)       # face out of range guards hold


def test_registry_states_the_correction():
    assert dc.candidate("CW_RECURSIVE_XYZ_LEVELS_V1").status == \
        "REJECTED_FOR_SOURCE_DECODE"
    c = dc.candidate("CW_OCTAL_PACKET_F5_Q22_S3_V1")
    assert c.status == "LOCKED_INTERPRETATION_STRUCTURAL_ONLY"
    assert "r12" in c.parse
