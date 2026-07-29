"""R10.34 — descrambler discipline and the 60/120 domain-wall primitive."""

import pytest

from r1034 import descramble as d
from r1034 import geom60 as g


# --- the screen must be a screen ---------------------------------------

def test_screen_passes_its_positive_control_and_rejects_shuffles():
    c = d.calibrate()
    assert c["control_passes"] is True
    assert c["separates_control_from_shuffles"] is True
    assert c["shuffle_max_density"] < c["control_density"]


def test_short_strings_are_not_screenable():
    """One chance trigram in 8 letters gives density 0.167 -- a density
    threshold calibrated on a long control is meaningless there."""
    sc = d.english_score("LCRALLY")
    assert sc["long_enough_to_screen"] is False
    assert sc["plausible_english"] is False


def test_single_chance_trigram_is_not_a_decode():
    sc = d.english_score("QQQQQQQQQALLQQQQQQQQQQQQ")
    assert sc["trigram_hits"] == 1
    assert sc["plausible_english"] is False


def test_no_numeric_string_yields_a_genuine_decode():
    r = d.report()
    assert r["genuine_decodes"] == 0
    assert r["promoted"] == 0
    assert r["verdict"].startswith("R10_34_CODEC_STILL_UNRESOLVED")


def test_transforms_are_reversible_where_claimed():
    for n in range(26):
        assert d.rot_inverse(d.rot("HELLO", n), n) == "HELLO"
    assert d.from_base36(d.to_base36(123456789)) == 123456789
    assert d.a1z26_inverse(d.a1z26("010203", 2), 2) == "010203"


def test_a1z26_refuses_out_of_range_groups():
    assert d.a1z26("990102", 2) is None      # 99 is not a letter index
    assert d.a1z26("12345", 2) is None       # length not divisible


# --- 60/120 domain-wall arithmetic -------------------------------------

def test_60_and_120_are_supplementary_views_of_one_interface():
    s = g.supplementary_pair()
    assert s["sum_deg"] == 180.0
    assert s["are_supplementary"] and s["bend_is_two_facet_units"]
    assert s["facet_tiles_plane_sixfold"] and s["bend_closes_threefold"]


def test_51_843_closes_no_circuit():
    rows = {r["case"]: r for r in g.angle_arithmetic()}
    assert rows["FACET_60"]["closes_integer_circuit"] is True
    assert rows["BEND_120"]["closes_integer_circuit"] is True
    assert rows["ALT_51_843"]["closes_integer_circuit"] is False


def test_quartz_three_fold_is_intrinsic_not_imposed():
    s = g.supplementary_pair()
    assert s["quartz_point_group"] == "32"
    assert s["three_fold_is_intrinsic_to_quartz"] is True


def test_no_singularity_is_claimed_and_the_controls_exist():
    r = g.report()
    assert r["singularity_found"] is False and r["solver_run"] is False
    cases = {c["case"] for c in r["simulation_cases"]}
    assert "FLAT_CUT_CONTROL" in cases
    assert any(c["is_control"] for c in r["simulation_cases"])
    assert all(c["status"] == "CASE_DEFINED_NO_SOLVER_RUN"
               for c in r["simulation_cases"])


def test_every_detector_declares_its_falsifier():
    for obs in g.detector_contract():
        assert obs["falsifier"]
        assert obs["required_evidence"]


def test_phase_conjugation_node_stays_provenance_language():
    r = g.report()
    assert "UNTIL_MEASURED" in r["phase_conjugation_node"]
    assert r["physical_validation_claimed"] is False
