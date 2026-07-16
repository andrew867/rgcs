"""C04: frequency-key registry tests (gates G10/G11)."""
from __future__ import annotations

import math

import pytest

from rscs2_core.frequency_keys import (PHI, build_registry,
                                       coincidence_significance)

REG = build_registry()


def test_all_52_ids_present_with_kinds():
    """Gate G10: F001..F052 all present, each typed."""
    assert set(REG) == {f"F{i:03d}" for i in range(1, 53)}
    for rec in REG.values():
        assert rec["kind"] == "FrequencyKeyRecord"
        assert rec["frequency_kind"]
        assert rec["status"]


def test_exact_derived_arithmetic():
    assert REG["F002"]["value_hz"] == 4096 * 5 == 20480
    assert REG["F003"]["value_hz"] == 4096 * 8 == 2 ** 15
    assert REG["F009"]["value_hz"] == 4096 / 100
    assert REG["F013"]["value_hz"] == 4096 / 200
    assert REG["F014"]["value_hz"] == 20 * 256
    assert REG["F015"]["value_hz"] == 20 * 512
    assert REG["F030"]["value_hz"] == 465 * 44
    assert REG["F031"]["value_hz"] == 787 * 26
    assert REG["F032"]["value_hz"] == pytest.approx(210.42 * 98,
                                                    rel=1e-12)
    assert REG["F046"]["value"] == pytest.approx(4096 * 0.552,
                                                 rel=1e-12)
    assert REG["F047"]["value"] == pytest.approx(
        (2 / 3) * 4096 * 0.552, rel=1e-12)
    assert REG["F043"]["period_at_4096_s"] == 192 / 4096


def test_misses_recorded_exactly_never_rounded():
    """The anti-numerology core: 21x195 = 4095 is ONE HERTZ off 4096
    and stays that way; 465x44 misses 20480 by exactly 20 Hz."""
    assert REG["F007"]["value_hz"] == 21 * 195 == 4095
    assert REG["F007"]["exact_miss_hz"] == 1.0
    assert REG["F007"]["status"] == "SOURCE_HYPOTHESIS"
    assert REG["F030"]["exact_miss_hz"] == 20480 - 465 * 44 == 20.0
    assert REG["F031"]["exact_miss_hz"] == 20480 - 787 * 26 == 18.0
    # F046: the 552 ms window does NOT close (non-integer cycles)
    assert REG["F046"]["value"] != round(REG["F046"]["value"])
    # F049: no exact powers-of-eight relation
    assert "NOT integral" in REG["F049"]["audit"]


def test_dimensional_hygiene():
    """Angle-derived and non-frequency values are typed as such."""
    assert REG["F039"]["frequency_kind"] == "angle_derived_motif"
    assert REG["F040"]["frequency_kind"] == "angle_derived_motif"
    assert "NOT a" in REG["F039"]["note"] or "not a" in \
        REG["F039"]["note"]
    assert REG["F050"]["frequency_kind"] == "non_frequency_value"
    assert "value_hz" not in REG["F050"]
    assert REG["F044"]["frequency_kind"] == "dimensionless_ratio"
    assert REG["F044"]["value"] == pytest.approx(PHI ** 8, rel=1e-12)


def test_fibonacci_like_sequence_property():
    s = REG["F036"]["sequence_hz"]
    for i in range(2, len(s)):
        assert s[i] == s[i - 1] + s[i - 2]


def test_timing_relations():
    assert REG["F042"]["period_s"] == pytest.approx(
        60 * math.pi / 4096, rel=1e-15)
    # F041 vs F042: within 0.06 ms, recorded not promoted
    assert abs(REG["F041"]["period_s"] - REG["F042"]["period_s"]) \
        < 6e-5
    assert REG["F042"]["status"] == "SOURCE_HYPOTHESIS"


def test_look_elsewhere_null_model():
    """Gate G11: a 20 Hz 'near miss' inside a 2.7 kHz band with many
    tried products is NOT significant."""
    out = coincidence_significance(
        20460.0, targets_hz=[20480.0], tolerance_hz=25.0,
        band_hz=(18500.0, 21200.0), n_candidates_tried=30)
    assert out["within_tolerance"]
    assert out["expected_chance_hits"] > 0.5
    assert not out["significant"]
    # a genuinely tight, un-searched match CAN be significant
    tight = coincidence_significance(
        20480.001, [20480.0], tolerance_hz=0.01,
        band_hz=(18500.0, 21200.0), n_candidates_tried=1)
    assert tight["significant"]
    # monotone: more tried candidates -> less significant
    a = coincidence_significance(20460, [20480], 25, (18500, 21200),
                                 1)["expected_chance_hits"]
    b = coincidence_significance(20460, [20480], 25, (18500, 21200),
                                 50)["expected_chance_hits"]
    assert b == pytest.approx(50 * a, rel=1e-12)


def test_no_source_value_promoted_above_hypothesis():
    for rid, rec in REG.items():
        if "SRC" in rec["evidence_tags"] and \
                "DER" not in rec["evidence_tags"]:
            assert rec["status"] in ("SOURCE_HYPOTHESIS",), rid
