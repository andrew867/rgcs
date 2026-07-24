"""R12 — the South-referenced frame with no forced inversion."""

from __future__ import annotations

import numpy as np
import pytest

from r11 import earthface as E
from r12 import bodylock as B


# --- the four operations, their determinants and handedness ------------

def test_proper_south_up_is_diag_1_minus1_minus1_with_det_plus_one():
    assert np.allclose(E.SOUTH_UP_ROTATION, np.diag([1.0, -1.0, -1.0]))
    assert float(np.linalg.det(E.SOUTH_UP_ROTATION)) == pytest.approx(1.0)
    assert B.determinant_sign(B.SouthOperation.PROPER_ROTATION) == +1
    assert B.is_proper(B.SouthOperation.PROPER_ROTATION)


def test_the_mirror_is_improper_with_det_minus_one():
    mirror = np.diag([1.0, 1.0, -1.0])
    assert float(np.linalg.det(mirror)) == pytest.approx(-1.0)
    assert B.determinant_sign(B.SouthOperation.MIRROR_IMPROPER) == -1
    assert not B.is_proper(B.SouthOperation.MIRROR_IMPROPER)


def test_is_proper_is_correct_for_all_four_members():
    assert B.is_proper(B.SouthOperation.PROPER_ROTATION) is True
    assert B.is_proper(B.SouthOperation.MIRROR_IMPROPER) is False
    assert B.is_proper(B.SouthOperation.LATITUDE_SIGN_FLIP) is False
    assert B.is_proper(B.SouthOperation.AXIS_RELABEL) is True


def test_changes_handedness_is_correct_for_all_four_members():
    assert B.changes_handedness(B.SouthOperation.PROPER_ROTATION) is False
    assert B.changes_handedness(B.SouthOperation.MIRROR_IMPROPER) is True
    assert B.changes_handedness(B.SouthOperation.LATITUDE_SIGN_FLIP) is True
    assert B.changes_handedness(B.SouthOperation.AXIS_RELABEL) is False


def test_proper_and_relabel_preserve_handedness_mirror_and_latflip_do_not():
    for op in (B.SouthOperation.PROPER_ROTATION,
               B.SouthOperation.AXIS_RELABEL):
        assert B.is_proper(op) and not B.changes_handedness(op)
    for op in (B.SouthOperation.MIRROR_IMPROPER,
               B.SouthOperation.LATITUDE_SIGN_FLIP):
        assert B.changes_handedness(op) and not B.is_proper(op)


def test_a_non_member_operation_is_refused():
    with pytest.raises(B.BodyLockError):
        B.is_proper("SOUTH")


# --- the double-inversion audit ----------------------------------------

def test_net_handedness_of_two_improper_ops_is_plus_one():
    ops = (B.SouthOperation.MIRROR_IMPROPER,
           B.SouthOperation.LATITUDE_SIGN_FLIP)
    assert B.net_handedness(ops) == +1


def test_net_handedness_of_a_single_improper_op_is_minus_one():
    assert B.net_handedness((B.SouthOperation.MIRROR_IMPROPER,)) == -1
    assert B.net_handedness((B.SouthOperation.LATITUDE_SIGN_FLIP,)) == -1


def test_net_handedness_of_proper_only_is_plus_one():
    assert B.net_handedness((B.SouthOperation.PROPER_ROTATION,)) == +1


def test_a_single_improper_op_flips_and_two_restore_handedness():
    one = B.double_inversion_audit((B.SouthOperation.MIRROR_IMPROPER,))
    assert one["net_handedness"] == -1
    assert one["single_flip_reverses"] is True
    assert one["is_double_inversion"] is False
    two = B.double_inversion_audit(
        (B.SouthOperation.MIRROR_IMPROPER,
         B.SouthOperation.LATITUDE_SIGN_FLIP))
    assert two["net_handedness"] == +1
    assert two["is_double_inversion"] is True


def test_refuse_forced_inversion_raises_on_the_double_inversion_pipeline():
    ops = (B.SouthOperation.MIRROR_IMPROPER,
           B.SouthOperation.LATITUDE_SIGN_FLIP)
    with pytest.raises(B.BodyLockError):
        B.refuse_forced_inversion(ops, claims_inversion=True)


def test_refuse_forced_inversion_does_not_raise_on_a_clean_proper_rotation():
    out = B.refuse_forced_inversion(
        (B.SouthOperation.PROPER_ROTATION,), claims_inversion=True)
    assert out["net_handedness"] == +1
    assert out["is_double_inversion"] is False


def test_a_single_honest_reflection_is_not_a_forced_inversion():
    # one improper op genuinely reverses handedness; its claim is honest
    out = B.refuse_forced_inversion(
        (B.SouthOperation.MIRROR_IMPROPER,), claims_inversion=True)
    assert out["net_handedness"] == -1


def test_the_cancelling_pair_is_allowed_when_it_does_not_claim_inversion():
    ops = (B.SouthOperation.MIRROR_IMPROPER,
           B.SouthOperation.LATITUDE_SIGN_FLIP)
    out = B.refuse_forced_inversion(ops, claims_inversion=False)
    assert out["handedness_preserved"] is True


# --- the frame itself --------------------------------------------------

def test_south_referenced_frame_is_orthonormal_proper_with_declared_hand():
    frame = B.south_referenced_frame(34.8697, -111.7610, 1372.0)
    assert frame.is_orthonormal_proper()
    assert float(np.linalg.det(frame.matrix())) == pytest.approx(1.0)
    assert frame.handedness == B.RIGHT_HANDED


def test_the_frame_applies_the_proper_rotation_to_the_ecef_position():
    frame = B.south_referenced_frame(0.0, 0.0, 0.0)
    ecef = np.array(frame.ecef_m)
    body = np.array(frame.body_position_m)
    assert np.allclose(np.array(frame.rotation) @ ecef, body, atol=1e-6)


def test_a_frame_with_no_declared_handedness_is_refused():
    with pytest.raises(B.BodyLockError):
        B.BodyFrame(0.0, 0.0, 0.0, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0),
                    ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
                    B.UNDECLARED_HANDEDNESS, 1.0)


def test_refuse_undeclared_handedness_raises_on_none_and_placeholder():
    with pytest.raises(B.BodyLockError):
        B.refuse_undeclared_handedness(None)
    with pytest.raises(B.BodyLockError):
        B.refuse_undeclared_handedness("")
    with pytest.raises(B.BodyLockError):
        B.refuse_undeclared_handedness(B.UNDECLARED_HANDEDNESS)


def test_refuse_undeclared_handedness_returns_a_declared_label():
    assert B.refuse_undeclared_handedness(B.RIGHT_HANDED) == B.RIGHT_HANDED
    assert B.refuse_undeclared_handedness(B.LEFT_HANDED) == B.LEFT_HANDED


def test_an_unrecognised_handedness_label_is_refused():
    with pytest.raises(B.BodyLockError):
        B.refuse_undeclared_handedness("SOUTHWARD")


# --- the ECEF conversion matches earthface's verified values -----------

def test_equator_prime_meridian_maps_to_the_semi_major_axis():
    frame = B.south_referenced_frame(0.0, 0.0, 0.0)
    assert frame.ecef_m[0] == pytest.approx(E.WGS84_A, abs=1e-6)
    assert frame.ecef_m[1] == pytest.approx(0.0, abs=1e-6)
    assert frame.ecef_m[2] == pytest.approx(0.0, abs=1e-6)


def test_the_north_pole_maps_to_the_semi_minor_axis():
    frame = B.south_referenced_frame(90.0, 0.0, 0.0)
    assert frame.ecef_m[2] == pytest.approx(E.WGS84_B, abs=1e-6)
    assert frame.ecef_m[0] == pytest.approx(0.0, abs=1e-6)


# --- the report --------------------------------------------------------

def test_the_report_refuses_to_over_claim():
    r = B.bodylock_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["claim_class"] == "REPOSITORY_COMPUTATIONAL_RESULT"
    assert r["verdict"] == "SOUTH_REFERENCED_FRAME_NO_FORCED_INVERSION"
    assert "magnetometer" in r["what_this_does_not_say"]


def test_the_report_lists_all_four_operations_with_their_determinants():
    r = B.bodylock_report()
    ops = r["operations"]
    assert set(ops) == {op.value for op in B.SouthOperation}
    assert ops["PROPER_ROTATION"]["determinant_sign"] == +1
    assert ops["MIRROR_IMPROPER"]["determinant_sign"] == -1
