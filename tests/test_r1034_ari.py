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


# --- R10.35 EarthStar grid --------------------------------------------

def test_earthstar_node_count_is_exactly_62_by_construction():
    from r1034 import earthstar as e
    s = e.structure_check()
    assert s["nodes"] == 62 and s["nodes_match_62"]
    assert s["great_circles"] == 15 and s["great_circles_match_15"]


def test_orientation_is_not_sourced_and_is_declared():
    from r1034 import earthstar as e
    assert e.structure_check()["orientation_sourced"] is False
    for row in e.score_sites([("X", 51.1789, -1.8262)]):
        assert row["orientation_sourced"] is False
        assert row["scored_as_evidence"] is False


def test_edge_proximity_is_not_discriminating_at_the_observed_scale():
    """~1 in 3 random points sit within 151 km of a grid great circle."""
    from r1034 import earthstar as e
    base = {r["distance_km"]: r for r in e.chance_baseline(samples=60000)}
    assert base[151]["fraction_within_of_any_edge"] > 0.25
    assert base[151]["edge_test_is_discriminating"] is False


def test_node_proximity_is_far_more_discriminating_than_edge():
    from r1034 import earthstar as e
    base = {r["distance_km"]: r for r in e.chance_baseline(samples=60000)}
    at150 = base[151]
    assert at150["fraction_within_of_any_node"] < 0.02
    assert (at150["fraction_within_of_any_edge"]
            > 10 * at150["fraction_within_of_any_node"])


def test_nothing_is_promoted_without_a_blind_test():
    from r1034 import earthstar as e
    r = e.report()
    assert r["blind_test_passed"] is False
    assert r["projector_promoted"] is False
    assert r["verdict"].endswith("EXACT_FAILURES_EMITTED")


# --- R10.36 checks -----------------------------------------------------

def test_triangle_null_is_far_tighter_than_edge_null():
    """The R10.36 split: T2 is a real test, T3 is not. 120 LCD
    triangles give a 0.83% null; the 15-edge band gives ~32% at 151 km."""
    from r1034 import earthstar as e
    tri_null = 1 / 120
    base = {r["distance_km"]: r for r in e.chance_baseline(samples=60000)}
    edge_null = base[151]["fraction_within_of_any_edge"]
    assert tri_null < 0.01
    assert edge_null > 0.25
    assert edge_null > 30 * tri_null


def test_rgcs_ids_and_earthstar_labels_cannot_collide():
    """T1: disjoint by orders of magnitude, so 165892743 != node 43."""
    rgcs_min = min(int(x) for x in
                   ("165892743", "165876523", "16873059233"))
    assert rgcs_min > 62          # 62 is the whole EarthStar node set
