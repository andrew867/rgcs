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


# --- R10.31 decoded-field checksum ------------------------------------

def test_field_checksum_reports_degeneracy_not_just_count():
    """The corpus looks like 2 examples and behaves like 1."""
    from r1028 import fieldsum
    vals = [("ANCHORAGE_ALASKA", 16873059233),
            ("SANTA_FE_NEW_MEXICO", 16875092353)]
    r = fieldsum.search(vals)
    d = r["degeneracy"]
    assert d["target_is_constant"] is True
    assert d["target_values"] == [1]
    assert d["effective_independent_examples"] == 1
    assert set(d["constant_fields"]) == {"R4", "S8", "E3_1"}


def test_field_checksum_is_still_blocked_and_says_why():
    from r1028 import fieldsum
    vals = [("ANCHORAGE_ALASKA", 16873059233),
            ("SANTA_FE_NEW_MEXICO", 16875092353)]
    r = fieldsum.search(vals)
    assert r["verdict"] == "R10_31_FIELD_CHECKSUM_STILL_BLOCKED"
    assert r["decisive"] is False
    # survivors exist but chance predicts many too
    assert r["survivor_count"] > 0
    assert r["expected_false_survivors"] > 1
    assert "degeneracy" in r["exact_failure"]


def test_every_field_rule_is_exact_and_finite():
    from r1028 import fieldsum
    d = fieldsum.fields_of(16873059233)
    for _, fn in fieldsum.rule_families():
        v = fn(d)
        assert isinstance(v, int) and 0 <= v < 8


# --- R10.31 crystal stack ---------------------------------------------

def test_4096hz_and_law_frequency_are_exactly_phase_lockable():
    from r1028 import crystal1031 as c
    r = c.phase_lock_report()
    assert r["common_reference_hz"] == 0.25
    assert r["f_op_divider"] == 52734375
    assert r["scale_a_divider"] == 16384
    assert r["phase_lockable"] is True


def test_law_frequency_is_not_a_scale_a_harmonic():
    from r1028 import crystal1031 as c
    r = c.harmonic_coincidence_report()
    assert r["is_integer_harmonic"] is False
    assert abs(r["miss_hz"] - 1430.25) < 1e-6
    assert r["excites_scale_a_by_harmonic_coincidence"] is False


def test_specimen_drive_role_is_a_negative_result():
    from r1028 import crystal1031 as c
    roles = {r["role"]: r for r in c.stack_roles()}
    assert roles["SPECIMEN_ACOUSTIC_DRIVE"]["supported"] is False
    assert roles["SPECIMEN_ACOUSTIC_DRIVE"]["status"] == "NEGATIVE_RESULT"
    assert roles["94_GHZ_CARRIER"]["supported"] is False


def test_40ghz_remains_an_unattested_fitted_constant():
    from r1028 import crystal1031 as c
    a = c.ATTESTATION_40GHZ
    assert a["attested_in_source_notes"] is False
    assert a["status"] == "UNATTESTED_FITTED_CONSTANT"


def test_lunar_lane_sources_no_coordinate():
    from r1028 import crystal1031 as c
    assert all(x["coordinate_sourced"] is False for x in c.LUNAR_ROOT_LANE)
    assert c.report()["external_facts_asserted"] == 0


# --- the ACTUAL variable-length codec (source-specified) ---------------

def test_word_length_is_variable_and_read_from_octal_length():
    from r1028 import varcodec36 as v
    assert v.VALID_OCTAL_LENGTHS == (9, 10, 11, 12)   # 27/30/33/36 bits
    for octal_len, tail in ((9, 3), (10, 6), (11, 9), (12, 12)):
        assert v.tail_bits_for(octal_len) == tail


def test_root_is_four_bits_and_unifies_the_verified_anchors():
    """The 5-bit F5 stole the top bit of the 8-bit surface field, which
    split one root family into an apparent {4,5}."""
    from r1028 import varcodec36 as v
    roots = {n: v.decode(int(x))["R4_root"] for n, x in
             (("STONEHENGE", "165876523"), ("ERIE", "167849523"),
              ("TORONTO", "168930443"))}
    assert set(roots.values()) == {2}


def test_check_digit_is_mandatory_at_every_width():
    from r1028 import varcodec36 as v
    for raw in ("165876523", "16873059233"):
        d = v.decode(int(raw))
        assert d["check_digit_m3"] == d["tail_groups"][-1]


def test_orange_triplet_is_one_cell_with_three_tails():
    """43/63/83 share R4, S8 AND P12 exactly - they are the same
    geometric cell, differing only in the tail. So they cannot be three
    separate positions along an edge."""
    from r1028 import varcodec36 as v
    ds = [v.decode(int(x)) for x in
          ("165892743", "165892763", "165892783")]
    assert len({d["R4_root"] for d in ds}) == 1
    assert len({d["S8_surface"] for d in ds}) == 1
    assert len({d["P12_path"] for d in ds}) == 1
    assert len({d["value"] for d in ds}) == 3      # but distinct words


def test_over_long_vectors_are_refused_not_forced():
    from r1028 import varcodec36 as v
    with pytest.raises(v.VarCodecError, match="not a single"):
        v.decode(168730592363363)      # 16 octal digits


# --- R10.38: variable codec is authoritative --------------------------

OPERATOR_R1038 = {
    165876523: ("001001111000110001001100101011", 2, 120, 3148, [5, 3], 3),
    167849523: ("001010000000010010111000110011", 2, 128, 1208, [6, 3], 3),
    168930443: ("001010000100011010110010001011", 2, 132, 1714, [1, 3], 3),
}


@pytest.mark.parametrize("value", sorted(OPERATOR_R1038))
def test_reproduces_the_operator_r1038_parse_exactly(value):
    from r1028 import varcodec36 as v
    bits, r4, s8, p12, e3, chk = OPERATOR_R1038[value]
    d = v.decode(value)
    assert d["total_bits"] == 30
    assert d["bits"] == bits
    assert (d["R4_root"], d["S8_surface"], d["P12_path"]) == (r4, s8, p12)
    assert d["E3"] == e3 and d["check_digit_m3"] == chk


def test_smallest_valid_width_rule_never_forces_36_bits():
    from r1028 import varcodec36 as v
    assert v.VALID_WIDTHS == (27, 30, 33, 36)
    assert v.active_width(165876523) == 30          # 28 bits -> 30
    assert v.active_width(16873059233) == 36        # 34 bits -> 36
    assert v.active_width(1) == 27                  # tiny -> 27, not 36


def test_bit_length_and_octal_width_rules_agree():
    from r1028 import varcodec36 as v
    for raw in ("165876523", "167849523", "168930443",
                "165892743", "16873059233", "16875092353"):
        assert v.width_rules_agree(int(raw))


def test_s8_layer2_partitions_the_tested_corpus():
    """S8's high-5 'layer 2' separates the families that F5 could not.
    Suggestive only: just TWO independent verified contrasts."""
    from r1028 import varcodec36 as v
    lay = {}
    for name, raw in (("STONEHENGE", "165876523"), ("ERIE", "167849523"),
                      ("TORONTO", "168930443"), ("ORANGE", "165892743"),
                      ("ANCHORAGE", "16873059233")):
        d = v.decode(int(raw))
        lay[name] = v.surface_split(d["S8_surface"])["layer2_hi5"]
    assert lay["STONEHENGE"] == lay["ORANGE"] == 15
    assert lay["ERIE"] == lay["TORONTO"] == 16
    assert lay["ANCHORAGE"] == 29
