"""R10.8.3 reconciliation tests — typed decoder candidates.

Locks the operator-instructed interleaved XYZ decode (exact required values),
the orange-slice structural line, the local-triangle candidate, variable-depth
anisotropy, the prefix-containment law, the inverse encoder, and the recorded
mod-20 defect of the locked production parser. No test here asserts that any
source vector decodes to a real place (``SOURCE_ORIGIN_VALIDATED: no``).
"""

from fractions import Fraction

import pytest

from cwatlas.r1082 import decoder_candidates as dc
from cwatlas.r1082 import spatialization

IX = dc.InterleavedXYZDecimalV1

# 2.1 required exact decodes (operator instruction, verbatim).
REQUIRED = {
    "165892743": ("187", "694", "523"),
    "165892763": ("187", "696", "523"),
    "165892783": ("187", "698", "523"),
    "165876523": ("185", "672", "563"),
    "165877623": ("186", "672", "573"),
}


def test_required_interleaved_decodes_exact():
    for raw, (x, y, z) in REQUIRED.items():
        p = IX.deinterleave(raw)
        assert (p["X"], p["Y"], p["Z"]) == (x, y, z), raw


def test_orange_slice_x_z_fixed_y_steps_by_two():
    xs, ys, zs = zip(*(REQUIRED[v] for v in
                       ("165892743", "165892763", "165892783")))
    assert set(xs) == {"187"} and set(zs) == {"523"}
    assert [int(y) for y in ys] == [694, 696, 698]


def test_stonehenge_to_nearby_delta():
    a = tuple(int(v) for v in REQUIRED["165876523"])
    b = tuple(int(v) for v in REQUIRED["165877623"])
    assert tuple(q - p for p, q in zip(a, b)) == (1, 0, 10)


def test_variable_length_anisotropic_depths():
    # corrected vector: 11 digits -> depths (4, 4, 3); last digit is a Y
    # refinement digit, NOT a shell field.
    p = IX.deinterleave("16782953437")
    assert (p["X"], p["Y"], p["Z"]) == ("1853", "6237", "794")
    assert IX.depths("16782953437") == (4, 4, 3)
    assert IX.depths("1678523973") == (4, 3, 3)


def test_local_triangle_lambda_and_height():
    lt = IX.local_triangle("165876523")
    lam = tuple(float(v) for v in lt["lambda"])
    assert lam == pytest.approx((0.143, 0.185, 0.672), abs=1e-12)
    assert float(lt["height"]) == pytest.approx(0.563, abs=1e-12)


def test_orange_slice_simplex_line_exact():
    lams = [IX.local_triangle(v)["lambda"] for v in
            ("165892743", "165892763", "165892783")]
    d1 = tuple(b - a for a, b in zip(lams[0], lams[1]))
    d2 = tuple(b - a for a, b in zip(lams[1], lams[2]))
    step = (Fraction(-2, 1000), Fraction(0), Fraction(2, 1000))
    assert d1 == step and d2 == step  # exact rationals, no float slack
    heights = {IX.local_triangle(v)["height"] for v in
               ("165892743", "165892763", "165892783")}
    assert heights == {Fraction(523, 1000)}


def test_prefix_containment_law():
    base = "165876523"
    ext = IX.append_digits(base, "417")
    assert ext == "165876523417"
    assert IX.contains(base, ext)
    assert IX.contains(base, base)
    assert not IX.contains(base, "165876524000")
    # nesting is strict per axis for a full extra triplet
    bi, ei = IX.intervals(base), IX.intervals(ext)
    for ax in dc.AXES:
        assert bi[ax][0] <= ei[ax][0] and ei[ax][1] <= bi[ax][1]
        assert (ei[ax][1] - ei[ax][0]) == (bi[ax][1] - bi[ax][0]) / 10


def test_interleave_round_trip_and_depth_constraint():
    for raw in list(REQUIRED) + ["16782953437", "1678523973"]:
        p = IX.deinterleave(raw)
        assert IX.interleave(p["X"], p["Y"], p["Z"]) == raw
    with pytest.raises(ValueError):
        IX.interleave("18", "6237", "794")  # X shallower than Y: unrealisable


def test_registry_is_typed_and_complete():
    ids = [c.candidate_id for c in dc.CANDIDATES]
    assert ids == ["BASE100_FOLD_MOD20_V1", "FIELD_SPLIT_V1",
                   "BARY_DIGIT_V1", "CW_INTERLEAVED_XYZ_FLATTENED_V1",
                   "CW_RECURSIVE_XYZ_LEVELS_V1",
                   "CW_OCTAL_PACKET_F5_Q22_S3_V1"]
    for c in dc.CANDIDATES:
        assert c.status and c.known_defect  # no silent selection
    assert dc.candidate("BASE100_FOLD_MOD20_V1").status == \
        "LOCKED_PRODUCTION_KNOWN_DEFECT"
    with pytest.raises(KeyError):
        dc.candidate("NOPE")


def test_production_mod20_defect_is_real_not_prose():
    """The recorded defect reproduces against the live production parser:
    routes differing only in the final token by multiples of 20 land on the
    same face."""
    fam = spatialization.get_family("F1_CANONICAL_DIRECT_BE")
    faces = {fam.address_of_route((1, 2, 3, 4, t))[0]
             for t in (23, 43, 63, 83)}
    assert len(faces) == 1, faces
