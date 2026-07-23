"""P08 — multi-frequency phase frame: exact closures and mixer refusal."""

from __future__ import annotations

from fractions import Fraction as F

import pytest

from r10 import multiframe as M


def test_gcd_closure_13mhz_4096_is_15_625_ms_exactly():
    interval = M.closure_interval_s(M.FREQ_13MHZ, M.FREQ_4096)
    assert interval == F(1, 64)
    assert interval == F(15625, 1_000_000)     # 15.625 ms exactly


def test_gcd_closure_13mhz_925_is_40_ms_exactly():
    interval = M.closure_interval_s(M.FREQ_13MHZ, M.FREQ_925)
    assert interval == F(1, 25)
    assert interval == F(40, 1000)             # 40 ms exactly


def test_all_three_close_at_exactly_one_second():
    interval = M.closure_interval_s(M.FREQ_13MHZ, M.FREQ_4096, M.FREQ_925)
    assert interval == F(1, 1)


def test_closure_interval_of_a_planted_pair_is_one_over_gcd():
    # 12 = 2^2*3, 18 = 2*3^2 -> gcd 6 -> exactly 1/6 s
    assert M.closure_interval_s(12, 18) == F(1, 6)
    # 8 and 12 -> gcd 4 -> exactly 1/4 s
    assert M.closure_interval_s(8, 12) == F(1, 4)


def test_closure_facts_report_the_exact_gcds():
    c = M.closure_facts()
    assert c["gcd_13mhz_4096"] == 64
    assert c["gcd_13mhz_925"] == 25
    assert c["gcd_13mhz_4096_925"] == 1
    assert c["closure_13mhz_4096_ms"] == 15.625
    assert c["closure_13mhz_925_ms"] == 40.0
    assert c["all_three_close_at_1s"]
    assert c["verdict"] == "PHASE_FRAME_EXACT"


def test_20_48_hz_is_512_over_25_exactly():
    assert M.FREQ_20_48 == F(512, 25)
    t = M.timebase_facts()
    assert t["freq_20_48_equals_512_over_25"]


def test_4096_over_20_48_is_exactly_200():
    t = M.timebase_facts()
    assert t["ratio_is_exactly_200"]
    assert F(M.FREQ_4096) / M.FREQ_20_48 == F(200)


def test_mixer_product_is_exact_sum_and_absolute_difference():
    p = M.mixer_product(M.FREQ_13MHZ, M.FREQ_925)
    assert p.sum_hz == F(13_000_925)
    assert p.difference_hz == F(12_999_075)
    assert p.verdict == "MIXER_PRODUCT_NO_MEANING_ASSIGNED"


def test_every_enumerated_mixer_product_disclaims_meaning():
    products = M.enumerate_mixer_products()
    assert len(products) == 6            # C(4,2)
    for p in products:
        assert p["verdict"] == "MIXER_PRODUCT_NO_MEANING_ASSIGNED"


def test_treating_a_mixer_product_as_a_signal_is_refused():
    p = M.mixer_product(M.FREQ_13MHZ, M.FREQ_4096)
    with pytest.raises(M.MultiFrameError):
        M.refuse_mixer_meaning(p)


def test_non_integer_frequency_is_refused_for_closure():
    with pytest.raises(ValueError):
        M.closure_interval_s(M.FREQ_20_48, M.FREQ_4096)  # 512/25 not integer


def test_report_refuses_to_over_claim():
    r = M.multiframe_report()
    assert r["evidence_class"] == "DERIVED_MATHEMATICS"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["verdict"] == "PHASE_FRAME_EXACT"
    assert "detected" in r["what_this_does_not_say"]
