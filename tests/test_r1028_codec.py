"""R10.28 / R10.29 — codec harness, checksum refusal, payload, SSPP."""

import math

import pytest

from r1016.quarantine import QuarantineError
from r1028 import checksum, codec36, payload, research, sspp221, vectors


# --- 36-bit arithmetic ------------------------------------------------

def test_36_bits_is_exactly_12_octal_digits():
    assert 8 ** codec36.OCTAL_DIGITS == 2 ** codec36.WORD_BITS


@pytest.mark.parametrize("name", sorted(codec36.PARTITIONS))
def test_every_partition_sums_to_36_bits(name):
    assert sum(w for _, w in codec36.PARTITIONS[name]) == codec36.WORD_BITS


def test_two_candidates_are_exact_single_block_words():
    r = vectors.decode_all()
    assert r["exact_36_bit_single_block"] == ["ANCHORAGE_ALASKA",
                                              "SANTA_FE_NEW_MEXICO"]


def test_santa_fe_correction_is_applied():
    """R10.30: 168750923535 -> 16875092353."""
    raw = dict(vectors.CANDIDATES)["SANTA_FE_NEW_MEXICO"]
    assert raw == "16875092353"
    assert len(format(int(raw), "o")) == 12
    assert raw.endswith(vectors.ESTABLISHED_TERMINAL)


def test_core30_partition_is_falsifiable_and_is_falsified():
    """H3|Core30|T3 is the one partition existing evidence can test."""
    r = vectors.decode_all()
    assert r["core30_surfaceword_compatible"] == []
    # and the reason is concrete: Anchorage's core is far outside profile
    v = int("16873059233")
    core30 = (v >> 3) & ((1 << 30) - 1)
    c = codec36.core30_is_surfaceword_compatible(core30)
    assert c["F5"] == 30 and c["F5"] not in codec36.ANCHOR_F5
    assert not c["compatible"]


def test_verified_anchors_do_match_the_profile():
    """Sanity: the profile is not vacuous."""
    for v in vectors.VERIFIED_ANCHORS.values():
        c = codec36.core30_is_surfaceword_compatible(v)
        assert c["compatible"], v


# --- checksum: the refusal is the result ------------------------------

def test_irrational_checksum_reading_is_refused():
    with pytest.raises(checksum.ChecksumError, match="irrational"):
        checksum.refuse_irrational_checksum()


def test_sqrt2_over_phi_reproduces_the_source_constant():
    assert abs(checksum.SQRT2_OVER_PHI
               - checksum.SQRT2_OVER_PHI_NOTE) < 1e-15


def test_second_clean_example_refutes_the_whole_candidate_rule_set():
    """R10.30: the Santa Fe correction added a second clean 12-octal
    word, and it eliminated the single rule that matched the first.
    That rule was chance, which is exactly why one example is not a
    result."""
    ex = [(lab, int(raw), raw) for lab, raw in vectors.CANDIDATES]
    r = checksum.search(ex)
    assert r["clean_12_octal_examples"] == 2
    assert r["rules_consistent"] == 0
    assert r["identified"] is False
    assert r["verdict"].endswith("ALL_CANDIDATE_RULES_REFUTED")


def test_one_example_alone_would_have_looked_solved():
    """The trap the second example sprang."""
    one = [("ANCHORAGE_ALASKA", int("16873059233"), "16873059233")]
    r = checksum.search(one)
    assert r["clean_12_octal_examples"] == 1
    assert r["rules_consistent"] >= 1        # a rule "matches"
    assert r["identified"] is False          # but is never reported as solved


def test_every_searched_rule_is_exact_integer_arithmetic():
    ex = [(lab, int(raw), raw) for lab, raw in vectors.CANDIDATES]
    for row in checksum.search(ex)["rows"]:
        assert row["exact_integer_rule"] is True


# --- the long payload -------------------------------------------------

def test_long_payload_is_a_codec_self_test_not_a_message():
    r = payload.report()
    assert r["pangram"]["pangram_complete"]
    assert r["alphabet_coverage"]["alphabet_complete"]
    assert r["message_decoded"] is False
    assert r["is_earth_coordinate"] is False


def test_payload_exercises_exactly_the_36_symbol_base36_alphabet():
    cov = payload.alphabet_coverage()
    assert cov["distinct_symbols"] == 36
    assert cov["exercises_full_base36_symbol_set"]
    assert cov["base36_symbol_count"] == 36


def test_base36_reading_is_a_hypothesis_not_an_adopted_partition():
    r = payload.report()
    assert "HYPOTHESIS ONLY" in r["base36_hypothesis"]
    # no partition depends on it
    assert all(sum(w for _, w in p) == 36
               for p in codec36.PARTITIONS.values())


# --- SSPP 2,2,2,1 -----------------------------------------------------

def test_221_cycle_closes_the_35_ring_exactly():
    r = sspp221.ring_arithmetic()
    assert r["cycle_sum"] == 7
    assert r["ring_closes_exactly"]
    assert r["cycles_to_close_ring"] == 5.0
    assert abs(r["phase_increment_rad"] - 2 * math.pi / 7) < 1e-12


def test_stepping_sequence_is_closed_and_has_no_repeats():
    seq = sspp221.stepping_sequence()
    assert len(seq) == len(set(seq))
    assert len(seq) == 20
    assert all(0 <= p < 35 for p in seq)


def test_active_blank_discrepancy_is_reported_not_smoothed():
    r = sspp221.report()
    assert r["positions_visited"] != sspp221.SOURCE_ACTIVE
    assert "open discrepancy" in r["discrepancy"]


def test_no_downshift_mechanism_is_claimed():
    for row in sspp221.downshift_ratio_tests():
        assert row["mechanism"] == "NONE_PROPOSED"
    assert sspp221.report()["physical_validation_claimed"] is False


# --- boundaries -------------------------------------------------------

def test_candidates_cannot_be_promoted_to_hard_anchors():
    with pytest.raises(vectors.AnchorPromotionError, match="CANDIDATE"):
        vectors.assert_not_anchor_eligible("ANCHORAGE_ALASKA")
    r = vectors.decode_all()
    assert r["promoted_to_hard_anchor"] == 0
    assert all(not x["may_train_projector"] for x in r["rows"])


def test_candidate_decode_refuses_quarantined_values():
    with pytest.raises(QuarantineError):
        vectors.decode("MONTREAL", "165879243")


def test_research_lane_asserts_no_external_facts():
    r = research.report()
    assert r["external_facts_asserted_by_this_run"] == 0
    assert r["web_research_performed"] is False
    for slot in r["formula_slots"]:
        assert slot["status"] == "EMPTY_AWAITING_SOURCE"


def test_music_cues_carry_no_codec_relevance():
    for c in research.RESEARCH_CLAIMS:
        if c["lane"] in ("music_cue", "date_cue"):
            assert c["codec_relevance"] == "NONE_ESTABLISHED"


# --- R10.30 frequency law ---------------------------------------------

def test_heterodyne_law_is_exact_dyadic():
    from r1028 import freq1030
    assert freq1030.f_op() == 13183593.75
    assert freq1030.f_op() == 54e9 / 2 ** 12
    assert abs(freq1030.f_op() - freq1030.SOURCE_CLAIM_HZ) == 93.75


def test_direct_division_of_94ghz_is_rejected_as_worse():
    from r1028 import freq1030
    direct = [t for t in freq1030.law_tests()
              if t["test"].startswith("DIRECT_DIVIDE")]
    assert direct and all("REJECTED" in t["verdict"] for t in direct)


def test_frequency_law_declares_its_fitted_constant():
    from r1028 import freq1030
    r = freq1030.report()
    assert r["law"]["free_constants_fitted"] == 1
    assert "not attested" in r["law"]["fitted_constant"]
    assert r["mechanism_proposed"] is False


def test_power_of_two_recurrences_are_not_treated_as_corroboration():
    from r1028 import freq1030
    for row in freq1030.power_of_two_recurrences():
        assert row["is_corroboration"] is False


def test_apollo_lane_asserts_no_external_facts():
    from r1028 import freq1030
    r = freq1030.report()
    assert r["external_facts_asserted"] == 0
    assert r["patent_window"]["results"] == []
    assert any("DROPPED" in a["state"] for a in freq1030.APOLLO_LANE)
