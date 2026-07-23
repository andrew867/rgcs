"""P06 — Cs-137/Ba-137 coarse ages, Cs-133 fine phase, and the alias trap."""

from __future__ import annotations

from fractions import Fraction

import pytest

from r11 import isotope as I


# --- the two cesiums are different typed systems ------------------------

def test_cs133_and_cs137_are_different_typed_systems():
    assert I.CS133.system is I.IsotopeSystem.CS133_CLOCK
    assert I.CS137.system is I.IsotopeSystem.CS137_RADIONUCLIDE
    assert I.CS133.system is not I.CS137.system
    assert I.CS133.stable and not I.CS137.stable
    assert I.CS133.evidence_class is I.EvidenceClass.DEFINITION
    assert I.CS137.evidence_class is I.EvidenceClass.EVALUATED_LITERATURE


def test_conflating_the_clock_with_the_radionuclide_is_refused():
    with pytest.raises(I.IsotopeError):
        I.refuse_isotope_conflation(I.CS133, I.CS137)


def test_the_refusal_itself_refuses_a_same_system_comparison():
    """Calling it on one system twice is misuse, not a finding."""
    with pytest.raises(I.IsotopeError):
        I.refuse_isotope_conflation(I.CS133, I.CS133)


# --- Part 1: the coarse age ---------------------------------------------

def test_ratio_one_gives_exactly_one_half_life():
    """R = 1 => log2(2) = 1 => t = T_half, exactly."""
    assert I.coarse_age(1) == I.CS137_HALF_LIFE_YEARS
    assert I.coarse_age(Fraction(1)) == 30.05


def test_ratio_three_gives_exactly_two_half_lives():
    """R = 3 => log2(4) = 2 => t = 2 * T_half, exactly."""
    assert I.coarse_age(3) == 2 * I.CS137_HALF_LIFE_YEARS
    assert I.coarse_age(7) == 3 * I.CS137_HALF_LIFE_YEARS


def test_zero_daughter_means_zero_elapsed_time():
    assert I.coarse_age(0) == 0.0


def test_the_half_life_is_the_packs_value_and_exact_as_a_rational():
    assert I.CS137_HALF_LIFE_YEARS == 30.05
    assert I.CS137_HALF_LIFE_YEARS_EXACT == Fraction(601, 20)
    assert float(I.CS137_HALF_LIFE_YEARS_EXACT) == I.CS137_HALF_LIFE_YEARS


def test_a_negative_ratio_has_no_age():
    with pytest.raises(I.IsotopeError):
        I.coarse_age(-0.5)


def test_a_nonpositive_half_life_is_refused():
    with pytest.raises(I.IsotopeError):
        I.coarse_age(1, t_half=0)


def test_inverse_convention_round_trips_against_the_forward_one():
    """N_Cs/N_Ba is the reciprocal reporting convention."""
    R = Fraction(192, 55)
    assert I.age_from_inverse_ratio(1 / R) == I.coarse_age(R)
    assert I.age_from_inverse_ratio(Fraction(1, 3)) == I.coarse_age(3)
    assert I.age_from_inverse_ratio(1) == I.CS137_HALF_LIFE_YEARS


def test_a_zero_parent_ratio_is_refused_rather_than_infinite():
    with pytest.raises(I.IsotopeError):
        I.age_from_inverse_ratio(0)


# --- the mandatory declarations -----------------------------------------

def test_all_seven_declarations_default_to_undeclared():
    r = I.coarse_age_result(Fraction(192, 55))
    assert set(r.undeclared_fields()) == set(I.MANDATORY_DECLARATIONS)
    assert len(I.MANDATORY_DECLARATIONS) == 7
    assert not r.closed_system_declared
    assert not r.is_fully_declared()
    assert r.measured_here == "nothing"


def test_age_is_refused_while_the_closed_system_is_undeclared():
    r = I.coarse_age_result(Fraction(192, 55))
    with pytest.raises(I.IsotopeError):
        I.refuse_age_without_closed_system_declaration(r)


def test_age_is_still_refused_when_one_declaration_is_missing():
    """Six of seven is not a declaration; the refusal must be total."""
    declared = {name: "declared for this test"
                for name in I.MANDATORY_DECLARATIONS
                if name != "contamination"}
    r = I.coarse_age_result(Fraction(192, 55),
                            closed_system_declared=True, **declared)
    assert r.undeclared_fields() == ("contamination",)
    with pytest.raises(I.IsotopeError):
        I.refuse_age_without_closed_system_declaration(r)


def test_age_is_still_refused_when_only_the_closed_system_is_missing():
    declared = {name: "declared for this test"
                for name in I.MANDATORY_DECLARATIONS}
    r = I.coarse_age_result(Fraction(192, 55), **declared)
    assert r.undeclared_fields() == ()
    assert not r.closed_system_declared
    with pytest.raises(I.IsotopeError):
        I.refuse_age_without_closed_system_declaration(r)


def test_a_fully_declared_result_passes_and_records_the_declarations():
    declared = {name: f"declared: {name}"
                for name in I.MANDATORY_DECLARATIONS}
    r = I.coarse_age_result(Fraction(1), closed_system_declared=True,
                            **declared)
    assert r.is_fully_declared()
    out = I.refuse_age_without_closed_system_declaration(r)
    assert out["age_years"] == I.CS137_HALF_LIFE_YEARS
    assert out["closed_system_declared"] is True
    assert set(out["declarations"]) == set(I.MANDATORY_DECLARATIONS)
    assert out["measured_here"] == "nothing"


def test_an_unknown_declaration_field_is_refused():
    with pytest.raises(I.IsotopeError):
        I.coarse_age_result(Fraction(1), initial_stable_Sr87="nope")


def test_branching_is_data_to_cite_not_an_assumption():
    b = I.branching_note()
    assert b["via_Ba137m"] == pytest.approx(0.946, abs=1e-9)
    assert b["direct_to_Ba137_ground"] == pytest.approx(0.054, abs=1e-9)
    assert b["sums_to_one"]
    assert b["source_reference"]


# --- Part 2: the orientation trap ---------------------------------------

def test_the_supplied_pair_has_a_neutral_public_alias():
    c = I.ISOTOPE_RATIO_CANDIDATE_A
    assert c.label == "ISOTOPE_RATIO_CANDIDATE_A"
    assert (c.a, c.b) == (192, 55)
    assert c.forward == Fraction(192, 55)
    assert c.inverse == Fraction(55, 192)
    assert float(c.forward) == pytest.approx(3.4909090909090907, rel=1e-15)
    assert float(c.inverse) == pytest.approx(0.2864583333333333, rel=1e-15)


def test_both_orientations_are_reported_and_give_different_ages():
    a = I.audit_ratio_orientations(192, 55)
    assert a["forward"]["ratio_exact"] == "192/55"
    assert a["inverse"]["ratio_exact"] == "55/192"
    assert a["forward"]["one_plus_R_exact"] == "247/55"
    assert a["inverse"]["one_plus_R_exact"] == "247/192"
    assert a["forward"]["age_years"] != a["inverse"]["age_years"]
    assert a["age_difference_years"] > 1.0
    # neither leg is chosen
    assert a["orientation_chosen"] is None
    assert a["orientation_status"] == "UNDECLARED_BY_DESIGN"
    assert a["verdict"] == "ORIENTATION_NOT_DETERMINED_BY_THE_DATA"


def test_each_orientation_matches_the_closed_form_age():
    a = I.audit_ratio_orientations(192, 55)
    assert a["forward"]["age_years"] == I.coarse_age(Fraction(192, 55))
    assert a["inverse"]["age_years"] == I.coarse_age(Fraction(55, 192))
    lo, hi = a["coarse_interval_years"]
    assert lo < hi
    assert lo == a["inverse"]["age_years"]      # 55/192 is the smaller R
    assert hi == a["forward"]["age_years"]


def test_choosing_the_orientation_from_a_desired_year_is_refused():
    with pytest.raises(I.IsotopeError):
        I.refuse_orientation_chosen_from_desired_year(
            192, 55, desired_year=1604)


def test_the_audit_needs_two_positive_integers():
    with pytest.raises(I.IsotopeError):
        I.audit_ratio_orientations(0, 55)


# --- Part 3: the Cs-133 fine phase and the aliases ----------------------

def test_cs133_constant_is_the_exact_defining_integer():
    assert I.CS133_HYPERFINE_HZ == 9_192_631_770
    assert isinstance(I.CS133_HYPERFINE_HZ, int)


def test_cs133_is_typed_as_a_definition_with_zero_uncertainty():
    d = I.cs133_definition()
    assert d["hyperfine_hz"] == 9_192_631_770
    assert d["is_exact_integer"]
    assert d["uncertainty"] == 0
    assert d["uncertainty_kind"] == "ZERO_BY_DEFINITION"
    assert d["evidence_class"] == "DEFINITION"
    assert d["measured_here"] == "nothing"
    assert I.CS133.uncertainty == Fraction(0)
    assert I.CS133_HYPERFINE_UNCERTAINTY == Fraction(0)


def test_a_small_interval_enumerates_its_aliases_in_full():
    """[0, 10] s at 1 Hz admits n = 0..10 -- eleven whole-cycle counts."""
    s = I.integer_cycle_aliases(0, 10, 1)
    assert s.count == 11
    assert s.enumerated == tuple(range(11))
    assert not s.truncated
    assert not s.is_unique()


def test_a_coarse_interval_admits_far_more_than_one_cycle_count():
    """One second of coarse width at the cesium line: ~9.19e9 aliases."""
    s = I.integer_cycle_aliases(1000, 1001, I.CS133_HYPERFINE_HZ)
    assert s.count > 1
    assert s.count == I.CS133_HYPERFINE_HZ + 1
    assert s.enumerated is None          # graceful huge-count handling
    assert s.truncated
    assert s.n_max - s.n_min + 1 == s.count


def test_an_inverted_or_negative_interval_is_refused():
    with pytest.raises(I.IsotopeError):
        I.integer_cycle_aliases(10, 1, 1)
    with pytest.raises(I.IsotopeError):
        I.integer_cycle_aliases(-1, 10, 1)
    with pytest.raises(I.IsotopeError):
        I.integer_cycle_aliases(0, 10, 0)


def test_the_joint_carrier_is_the_gcd_of_the_two_frequencies():
    assert I.rational_gcd(Fraction(9_192_631_770),
                          Fraction(10_000_000)) == Fraction(10)
    assert I.rational_gcd(Fraction(1, 2), Fraction(1, 3)) == Fraction(1, 6)


def test_a_second_carrier_reduces_the_alias_count_but_not_to_one():
    """The whole result, in one test: fewer aliases, still not unique."""
    a = I.audit_ratio_orientations(192, 55)
    lo, hi = a["coarse_interval_years"]
    d = I.aliases_with_second_carrier(lo * I.JULIAN_YEAR_S,
                                      hi * I.JULIAN_YEAR_S)
    assert d["single_carrier_alias_count"] > 1
    assert d["alias_count_reduced"]
    assert d["joint_alias_count"] < d["single_carrier_alias_count"]
    assert d["joint_alias_count"] > 1
    assert not d["unique"]
    assert d["still_ambiguous"]
    assert d["reduction_factor"] > 1e6
    assert d["verdict"] == "ALIASES_REDUCED_NOT_RESOLVED"


def test_an_identical_second_carrier_is_not_a_second_observable():
    with pytest.raises(I.IsotopeError):
        I.aliases_with_second_carrier(0, 1, I.CS133_HYPERFINE_HZ,
                                      I.CS133_HYPERFINE_HZ)


def test_a_unique_epoch_is_refused_when_aliases_remain():
    a = I.audit_ratio_orientations(192, 55)
    lo, hi = a["coarse_interval_years"]
    d = I.aliases_with_second_carrier(lo * I.JULIAN_YEAR_S,
                                      hi * I.JULIAN_YEAR_S)
    with pytest.raises(I.IsotopeError):
        I.refuse_unique_epoch(d["joint_alias_count"])


def test_a_unique_epoch_stays_refused_even_with_both_anchors_declared():
    """Declaring the anchors does not conjure a single admissible n."""
    with pytest.raises(I.IsotopeError):
        I.refuse_unique_epoch(
            2,
            independent_coarse_anchor="declared",
            second_coherent_observable="declared",
            claimed_epoch_year=123456)


def test_a_unique_epoch_is_refused_when_the_anchors_are_missing():
    with pytest.raises(I.IsotopeError):
        I.refuse_unique_epoch(1, independent_coarse_anchor=None,
                              second_coherent_observable="declared")
    with pytest.raises(I.IsotopeError):
        I.refuse_unique_epoch(1, independent_coarse_anchor=I.UNDECLARED,
                              second_coherent_observable=I.UNDECLARED)


def test_the_refusal_lets_a_genuinely_collapsed_set_through():
    """POWER: the guard is not a blanket 'no' -- it can be satisfied."""
    assert I.refuse_unique_epoch(
        1,
        independent_coarse_anchor="an independent coarse anchor",
        second_coherent_observable="a second coherent observable") is None


# --- the report ----------------------------------------------------------

def test_report_measures_nothing_and_claims_no_physical_validation():
    r = I.isotope_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["evidence_class"]
    assert r["what_this_does_not_say"]
    assert len(r["primary_sources"]) >= 4


def test_report_verdict_is_the_standing_null():
    r = I.isotope_report()
    assert r["verdict"] == "CESIUM_BARIUM_EPOCH_STILL_NON_UNIQUE"
    assert I.DEFAULT_VERDICT == "CESIUM_BARIUM_EPOCH_STILL_NON_UNIQUE"


def test_report_carries_both_orientations_and_an_unresolved_alias_set():
    r = I.isotope_report()
    assert r["orientation_audit"]["orientation_chosen"] is None
    assert r["orientation_audit"]["ages_differ"]
    assert r["alias_demonstration"]["still_ambiguous"]
    assert not r["alias_demonstration"]["unique"]
    assert r["coarse_age_model"]["undeclared_by_default"] == \
        list(I.MANDATORY_DECLARATIONS)
    assert not r["coarse_age_model"]["closed_system_declared"]
    assert {t["system"] for t in r["typed_systems"]} == {
        "cs133_clock_definition", "cs137_radionuclide"}
