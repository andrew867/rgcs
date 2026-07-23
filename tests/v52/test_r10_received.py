"""P01 — append-only source correction and its scale invariant."""

from __future__ import annotations

from fractions import Fraction as F

import pytest

from r10 import received as R


def test_raw_records_are_preserved_verbatim():
    assert R.RAW_8300.raw_text == "8300"
    assert R.RAW_1876.raw_text == "1876"


def test_a_correction_does_not_overwrite_the_raw():
    rec = R.append_correction(R.RAW_8300, R.CORR_8300)
    assert rec["raw_text"] == "8300"          # untouched
    assert rec["corrected_text"] == "8.300"
    assert rec["raw_preserved"]


def test_overwriting_a_raw_record_is_refused():
    with pytest.raises(R.OverwriteRefused):
        R.refuse_overwrite(R.RAW_8300)


def test_the_ratio_is_scale_invariant():
    """8.300/1.876 == 8300/1876 exactly."""
    inv = R.ratio_invariance()
    assert inv["ratios_equal"]
    assert inv["reduced"] == "2075/469"


def test_the_residual_is_unchanged_by_the_correction():
    inv = R.ratio_invariance()
    assert inv["residual_exact"] == "1649/433825"
    assert inv["residual_percent"] == pytest.approx(0.0858, abs=1e-3)
    assert inv["verdict"] == "APPROXIMATE_NOT_EXACT"
    assert not inv["are_equal"]


def test_inventing_a_unit_is_refused():
    for unit in ("kilometres", "hertz", "Earth radii", "degrees"):
        with pytest.raises(R.UnitInventionRefused):
            R.refuse_unit_invention(F("8.300"), unit)


def test_physical_mapping_is_unresolved():
    m = R.physical_mapping_status()
    assert m["status"] == "PhysicalMappingUnresolved"
    assert m["every_model_invertible"]


def test_every_scale_model_round_trips():
    for name in R.SCALE_MODELS:
        assert R.scale_model_round_trips(name)


def test_report_says_a_corrected_number_is_not_decoded():
    r = R.received_report()
    w = r["what_this_does_not_say"]
    assert "corrected number is not a" in w and "decoded" in w
    assert r["measured_here"] == "nothing"
