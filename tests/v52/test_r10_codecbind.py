"""P08 — codec output to coordinate binding, and its refusals."""

from __future__ import annotations

import pytest

from r10 import codecbind as CB
from r10.rootframe import RootFrame

E = "2026-07-22T00:00Z"
FRAME = "EARTH_MOON_ICRF"


def _rootframe():
    return RootFrame(
        root_id="EARTH_ROOT",
        domain="EARTH_MOON",
        body="EARTH",
        parent_root=None,
        epoch=E,
        primary_direction=(1.0, 0.0, 0.0),
        secondary_direction=(0.0, 1.0, 0.0),
        handedness="RIGHT",
        centre=(0.0, 0.0, 0.0),
        scale=1.0,
        derivation="CALCULATED",
        source_authority="OMEGA",
        evidence_status="MATH",
    )


def test_preregistered_binding_with_frame_epoch_uncertainty_succeeds():
    b = CB.bind_coordinate(
        codec_value=(8300, 1876),
        root="EARTH_ROOT",
        frame_id=FRAME,
        epoch=E,
        uncertainty=12.5,
        preregistered=True,
        layer="D3",
    )
    assert b.verdict == "CODEC_BINDING_SOFTWARE_VALID"
    assert b.preregistered is True
    assert b.root == "EARTH_ROOT"
    assert b.frame_id == FRAME
    assert b.layer == "D3"


def test_binding_accepts_a_typed_rootframe():
    b = CB.bind_coordinate(
        codec_value=42,
        root=_rootframe(),
        frame_id=FRAME,
        epoch=E,
        uncertainty=[[1.0, 0.0], [0.0, 1.0]],
        preregistered=True,
    )
    assert b.root == "EARTH_ROOT"
    assert b.verdict == "CODEC_BINDING_SOFTWARE_VALID"


def test_missing_frame_raises():
    with pytest.raises(CB.CodecBindError):
        CB.bind_coordinate(42, "EARTH_ROOT", "", E, 1.0, preregistered=True)


def test_missing_epoch_raises():
    with pytest.raises(CB.CodecBindError):
        CB.bind_coordinate(42, "EARTH_ROOT", FRAME, "", 1.0, preregistered=True)


def test_zero_uncertainty_point_raises():
    with pytest.raises(CB.CodecBindError):
        CB.bind_coordinate(42, "EARTH_ROOT", FRAME, E, 0.0, preregistered=True)


def test_missing_uncertainty_raises():
    with pytest.raises(CB.CodecBindError):
        CB.bind_coordinate(42, "EARTH_ROOT", FRAME, E, None, preregistered=True)


def test_all_zero_covariance_raises():
    with pytest.raises(CB.CodecBindError):
        CB.bind_coordinate(42, "EARTH_ROOT", FRAME, E,
                           [[0.0, 0.0], [0.0, 0.0]], preregistered=True)


def test_non_preregistered_binding_raises_as_retrofit():
    with pytest.raises(CB.CodecBindError):
        CB.bind_coordinate(42, "EARTH_ROOT", FRAME, E, 1.0, preregistered=False)


def test_ad_hoc_string_root_is_refused():
    with pytest.raises(CB.CodecBindError):
        CB.bind_coordinate(42, "MADE_UP_ROOT", FRAME, E, 1.0,
                           preregistered=True)


def test_refuse_binding_without_frame_epoch_helper_raises():
    with pytest.raises(CB.CodecBindError):
        CB.refuse_binding_without_frame_epoch(42, "", "")


def test_refuse_zero_uncertainty_point_helper_raises():
    with pytest.raises(CB.CodecBindError):
        CB.refuse_zero_uncertainty_point(42)


def test_refuse_retrofit_binding_helper_raises():
    with pytest.raises(CB.CodecBindError):
        CB.refuse_retrofit_binding(42, FRAME)


def test_binding_better_than_chance_only_when_preregistered():
    good = CB.binding_is_better_than_chance(preregistered=True)
    bad = CB.binding_is_better_than_chance(preregistered=False)
    assert good["power"] == "BETTER_THAN_CHANCE"
    assert bad["power"] == "NO_BETTER_THAN_CHANCE"


def test_report_measures_nothing_and_disclaims():
    r = CB.codecbind_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["evidence_class"] == "DERIVED_MATHEMATICS"
    assert r["verdict"] == "CODEC_BINDING_SOFTWARE_VALID"


def test_binding_records_provenance_and_default():
    b = CB.bind_coordinate(42, "EARTH_ROOT", FRAME, E, 1.0,
                           preregistered=True, provenance="TIER_A_DECLARATION")
    assert b.provenance == "TIER_A_DECLARATION"
    d = CB.bind_coordinate(42, "EARTH_ROOT", FRAME, E, 1.0, preregistered=True)
    assert d.provenance == "PREREGISTERED_DECLARATION"
    assert d.layer is None
