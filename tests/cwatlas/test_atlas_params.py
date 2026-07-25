"""P36 -- body/epoch/shell/altitude/codec selection logic: focused, negative."""

from __future__ import annotations

import pytest

from cwatlas import claims
from cwatlas.atlas_params import (
    AtlasParams,
    ParamError,
    allowed_bodies,
    allowed_codecs,
    allowed_depths,
    allowed_frames,
    allowed_height_conventions,
    allowed_shells,
    atlas_params_report,
    default_params,
    validate_params,
)
from cwatlas.mars_frame import HeightConvention


# -- enumerations -----------------------------------------------------------

def test_enumerations_list_expected_values():
    assert allowed_bodies() == ("EARTH", "MARS")
    assert "WGS84" in allowed_frames("EARTH")
    assert allowed_frames("MARS") == ("IAU_MARS_BODY_FIXED",)
    assert None in allowed_shells()
    assert set(range(0, 9)).issubset(set(allowed_shells()))
    assert "ELLIPSOIDAL" in allowed_height_conventions()
    assert "CW-GEO-1" in allowed_codecs() and "CW-HCM-ICO" in allowed_codecs()
    lo, hi = allowed_depths()
    assert lo == 0 and hi >= 12


def test_unknown_body_has_no_frames():
    with pytest.raises(ParamError):
        allowed_frames("PLUTO")


# -- focused validation -----------------------------------------------------

def test_validate_geo1_params():
    p = validate_params(body_id="EARTH", frame_id="ITRF2020", epoch="2020.0",
                        codec_id="CW-GEO-1")
    assert isinstance(p, AtlasParams)
    assert p.depth is None
    assert p.height_convention is HeightConvention.ELLIPSOIDAL


def test_validate_ico_params_requires_depth():
    p = validate_params(body_id="EARTH", frame_id="WGS84", epoch="2020.0",
                        codec_id="CW-HCM-ICO", depth=12)
    assert p.depth == 12


def test_height_convention_accepts_string_or_enum():
    p = validate_params(body_id="MARS", frame_id="IAU_MARS_BODY_FIXED",
                        epoch="2020.0", codec_id="CW-GEO-1",
                        height_convention="AREOID")
    assert p.height_convention is HeightConvention.AREOID


def test_default_params_are_fully_populated_and_named():
    d = default_params("EARTH").to_dict()
    for key in ("body_id", "frame_id", "epoch", "shell_state",
                "height_convention", "codec_id", "depth"):
        assert key in d
    assert d["frame_id"] == "ITRF2020"
    assert d["epoch"] == "2020.0"


def test_default_params_for_ico_populates_depth():
    d = default_params("EARTH", codec_id="CW-HCM-ICO")
    assert d.depth == 12


def test_default_params_for_mars():
    d = default_params("MARS")
    assert d.body_id == "MARS"
    assert d.frame_id == "IAU_MARS_BODY_FIXED"


# -- negative ---------------------------------------------------------------

def test_missing_crs_is_refused():
    with pytest.raises(claims.ClaimError):
        validate_params(body_id="EARTH", frame_id="", epoch="2020.0",
                        codec_id="CW-GEO-1")


def test_missing_epoch_is_refused():
    with pytest.raises(claims.ClaimError):
        validate_params(body_id="EARTH", frame_id="ITRF2020", epoch="",
                        codec_id="CW-GEO-1")


def test_frame_not_valid_for_body_is_refused():
    with pytest.raises(ParamError):
        validate_params(body_id="MARS", frame_id="ITRF2020", epoch="2020.0",
                        codec_id="CW-GEO-1")


def test_unknown_codec_is_refused():
    with pytest.raises(ParamError):
        validate_params(body_id="EARTH", frame_id="WGS84", epoch="2020.0",
                        codec_id="CW-BOGUS-9")


def test_unknown_height_convention_is_refused():
    with pytest.raises(ParamError):
        validate_params(body_id="EARTH", frame_id="WGS84", epoch="2020.0",
                        codec_id="CW-GEO-1", height_convention="MAGIC")


def test_out_of_range_shell_is_refused():
    with pytest.raises(ParamError):
        validate_params(body_id="EARTH", frame_id="WGS84", epoch="2020.0",
                        codec_id="CW-GEO-1", shell_state=9)


def test_ico_without_depth_is_refused_no_hidden_default():
    with pytest.raises(ParamError):
        validate_params(body_id="EARTH", frame_id="WGS84", epoch="2020.0",
                        codec_id="CW-HCM-ICO")


def test_depth_on_non_depth_codec_is_refused():
    with pytest.raises(ParamError):
        validate_params(body_id="EARTH", frame_id="WGS84", epoch="2020.0",
                        codec_id="CW-GEO-1", depth=12)


def test_out_of_range_depth_is_refused():
    with pytest.raises(ParamError):
        validate_params(body_id="EARTH", frame_id="WGS84", epoch="2020.0",
                        codec_id="CW-HCM-ICO", depth=999)


# -- determinism ------------------------------------------------------------

def test_validation_is_deterministic():
    kw = dict(body_id="EARTH", frame_id="ITRF2020", epoch="2020.0",
              codec_id="CW-GEO-1")
    assert validate_params(**kw).to_dict() == validate_params(**kw).to_dict()


# -- report -----------------------------------------------------------------

def test_report_declares_no_hidden_defaults():
    r = atlas_params_report()
    assert r["hidden_defaults"].startswith("none")
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
    assert "defaults" in r
