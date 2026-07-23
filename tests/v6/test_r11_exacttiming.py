"""P07 — the macrocycle in exact seconds and exact carrier cycles."""

from __future__ import annotations

import inspect
from fractions import Fraction as F

import pytest

from r11 import exacttiming as T


# --- the macrocycle is a rational, not a decimal ------------------------

def test_macrocycle_is_2261_over_4096_seconds_exactly():
    assert T.MACROCYCLE_S == F(2261, 4096)
    assert T.macrocycle_s() == F(2261, 4096)
    assert T.MACROCYCLE_S.numerator == 2261
    assert T.MACROCYCLE_S.denominator == 4096


def test_the_millisecond_form_is_552_001953125_exactly():
    ms = T.macrocycle_ms()
    # compared as exact rationals, never as floats
    assert ms == F(282625, 512)
    assert ms == F(552001953125, 10 ** 9)
    assert ms == F("552.001953125")
    assert ms == F(552) + F(1, 512)
    assert isinstance(ms, F)


def test_the_two_written_forms_of_the_seconds_value_agree():
    assert T.MACROCYCLE_S == F(282625, 512000)
    assert T.MACROCYCLE_S == T.macrocycle_ms() / 1000


def test_the_denominator_is_the_4096_timebase_and_dyadic():
    facts = T.macrocycle_facts()
    assert facts["denominator_is_the_4096_timebase"] is True
    assert facts["is_dyadic_rational"] is True
    assert facts["milliseconds_decimal"] == "552.001953125"
    assert facts["seconds_exact"] == "2261/4096"
    assert T.TIMEBASE_HZ == 4096


def test_the_numerator_2261_is_7_times_17_times_19():
    assert 7 * 17 * 19 == 2261
    assert T.MACROCYCLE_S.numerator == 7 * 17 * 19


# --- exact cycle counts over the macrocycle -----------------------------

def test_4096_hz_closes_exactly_at_2261_cycles_with_zero_residue():
    assert T.cycles(4096) == F(2261)
    assert T.cycles(4096).denominator == 1
    assert T.whole_cycles(4096) == 2261
    assert T.fractional_cycles(4096) == F(0)
    assert T.residue_cycles(4096) == F(0)
    assert T.closes_exactly(4096) is True


def test_925_hz_does_not_close_and_the_exact_count_is_2091425_over_4096():
    assert T.cycles(925) == F(2091425, 4096)
    assert T.closes_exactly(925) is False
    assert T.whole_cycles(925) == 510
    assert T.fractional_cycles(925) == F(2465, 4096)
    # 510.601806640625 -- the fractional part, exactly
    assert T.fractional_cycles(925) == F("0.601806640625")
    assert T.fractional_cycles(925) != 0


def test_925_hz_signed_residue_is_the_short_way_round():
    # 0.6018... is past the half-cycle, so the signed residue is negative
    r = T.residue_cycles(925)
    assert r == F(2465, 4096) - 1
    assert r == F(-1631, 4096)
    assert -F(1, 2) < r <= F(1, 2)


def test_20_48_hz_gives_exactly_2261_over_200_cycles():
    f = F(512, 25)
    assert f == T.REGISTERED_CARRIERS[T.Carrier.F_20_48]
    assert T.cycles(f) == F(2261, 200)
    assert T.cycles(f) == F("11.305")
    assert T.closes_exactly(f) is False
    assert T.whole_cycles(f) == 11
    assert T.fractional_cycles(f) == F(61, 200)     # 0.305 exactly
    assert T.fractional_cycles(f) == F("0.305")


def test_13_mhz_does_not_close_either():
    assert T.cycles(13_000_000) == F(459265625, 64)
    assert T.closes_exactly(13_000_000) is False
    assert T.fractional_cycles(13_000_000) == F(25, 64)


def test_only_the_4096_carrier_closes_and_that_is_computed():
    assert T.carriers_that_close() == (T.Carrier.F_4096.value,)
    closing = [row for row in T.audit_registered_carriers()
               if row["closes_exactly"]]
    assert [row["label"] for row in closing] == ["F_4096_HZ"]


def test_the_registered_carriers_are_exact_values():
    assert T.REGISTERED_CARRIERS[T.Carrier.F_4096] == F(4096)
    assert T.REGISTERED_CARRIERS[T.Carrier.F_925] == F(925)
    assert T.REGISTERED_CARRIERS[T.Carrier.F_20_48] == F(512, 25)
    assert T.REGISTERED_CARRIERS[T.Carrier.F_13MHZ] == F(13_000_000)
    assert all(isinstance(v, F) for v in T.REGISTERED_CARRIERS.values())
    assert len(T.REGISTERED_CARRIERS) == 4


def test_every_cycle_count_is_a_fraction_not_a_float():
    for hz in T.REGISTERED_CARRIER_HZ:
        assert isinstance(T.cycles(hz), F)
        assert isinstance(T.residue_cycles(hz), F)
        assert isinstance(T.fractional_cycles(hz), F)


def test_signed_residue_stays_in_the_half_open_half_cycle_band():
    for hz in T.REGISTERED_CARRIER_HZ:
        assert -F(1, 2) < T.residue_cycles(hz) <= F(1, 2)


def test_cycles_is_frequency_times_duration_over_any_duration():
    assert T.cycles(4096, F(1, 2)) == F(2048)
    assert T.cycles(925, 1) == F(925)
    assert T.closes_exactly(F(512, 25), F(25, 512)) is True


# --- the registered residue --------------------------------------------

def test_registered_residue_is_minus_one_over_125():
    assert T.registered_residue() == F(-1, 125)
    assert T.REGISTERED_RESIDUE_CYCLES == F(-1, 125)
    assert isinstance(T.registered_residue(), F)


def test_no_integer_carrier_can_leave_the_registered_residue():
    assert T.integer_carrier_with_residue_exists(F(-1, 125)) is False
    assert T.smallest_integer_carrier_for_residue(F(-1, 125)) is None


def test_residue_zero_is_achievable_and_4096_hz_is_the_witness():
    assert T.integer_carrier_with_residue_exists(F(0)) is True
    witness = T.smallest_integer_carrier_for_residue(F(0))
    assert witness == 4096
    assert T.residue_cycles(witness) == F(0)
    assert T.closes_exactly(witness) is True


def test_the_achievable_residues_are_exactly_the_multiples_of_1_over_4096():
    assert T.achievable_residues_are_multiples_of() == F(1, 4096)
    # a residue on the lattice is realisable, and the witness realises it
    r = F(7, 4096)
    assert T.integer_carrier_with_residue_exists(r) is True
    f = T.smallest_integer_carrier_for_residue(r)
    assert T.residue_cycles(f) == r
    # and one off the lattice is not
    assert T.integer_carrier_with_residue_exists(F(1, 3)) is False


def test_the_feasibility_proof_reports_the_factorisation_and_the_gcd():
    p = T.residue_feasibility_proof(F(-1, 125))
    assert p["modulus"] == 282625
    assert p["modulus_is_282625"] is True
    assert p["modulus_factors"] == [5, 5, 5, 7, 17, 19]
    assert p["modulus_factorisation"] == "5^3 * 7 * 17 * 19"
    assert 5 ** 3 * 7 * 17 * 19 == 282625
    assert p["gcd_modulus_4096"] == 1
    assert p["gcd_modulus_timebase_is_one"] is True
    assert p["gcd_2261_4096"] == 1


def test_the_feasibility_proof_states_the_modular_contradiction():
    p = T.residue_feasibility_proof(F(-1, 125))
    assert p["but_modulus_contains_factor"] == 125
    assert 282625 % 125 == 0
    assert p["and_the_remainder_mod_that_factor"] != 0
    assert p["integer_carrier_exists"] is False
    assert p["smallest_integer_carrier_hz"] is None
    assert p["status"] == "RESIDUE_NOT_REALISABLE_BY_INTEGER_CARRIER"
    assert p["residue_times_timebase_is_integer"] is False


def test_the_feasibility_proof_finds_no_contradiction_for_a_real_residue():
    p = T.residue_feasibility_proof(F(0))
    assert p["integer_carrier_exists"] is True
    assert p["smallest_integer_carrier_hz"] == 4096
    assert p["status"] == "RESIDUE_REALISABLE_BY_INTEGER_CARRIER"
    assert p["residue_times_timebase_is_integer"] is True


def test_the_registered_residue_is_retained_and_not_forced_to_fit():
    s = T.registered_residue_status()
    assert s["registered_residue_exact"] == "-1/125"
    assert s["realisable_by_integer_carrier"] is False
    assert s["retained"] is True
    assert s["status"] == "RESIDUE_NOT_REALISABLE_BY_INTEGER_CARRIER"
    assert s["control_residue_zero_is_realisable"] is True
    assert s["control_residue_zero_witness_hz"] == 4096


def test_the_infeasibility_is_exhaustively_confirmed_by_brute_force():
    # The residue of an integer carrier repeats with period 4096 in f,
    # because f * 2261/4096 advances by exactly 2261 whole cycles when f
    # advances by 4096. So sweeping f = 1..4096 is EXHAUSTIVE over every
    # integer hertz carrier, not a sample.
    target = F(-1, 125)
    residues = {T.residue_cycles(f) for f in range(1, 4097)}
    assert target not in residues
    assert len(residues) == 4096                    # all 4096 lattice sites
    assert F(0) in residues                         # and zero is one of them
    assert T.residue_cycles(4096 + 7) == T.residue_cycles(7)


# --- the two refusals ---------------------------------------------------

def test_refuse_float_timing_rejects_a_float():
    with pytest.raises(T.TimingError):
        T.refuse_float_timing(0.552)
    with pytest.raises(T.TimingError):
        T.refuse_float_timing(552.001953125)
    with pytest.raises(T.TimingError):
        T.refuse_float_timing(4096.0)


def test_refuse_float_timing_passes_exact_values_through():
    assert T.refuse_float_timing(4096) == F(4096)
    assert T.refuse_float_timing(F(512, 25)) == F(512, 25)
    assert T.refuse_float_timing("552.001953125") == F(282625, 512)
    assert isinstance(T.refuse_float_timing(925), F)


def test_the_guard_is_load_bearing_in_the_closure_math():
    with pytest.raises(T.TimingError):
        T.cycles(0.552)
    with pytest.raises(T.TimingError):
        T.cycles(4096, 0.552001953125)
    with pytest.raises(T.TimingError):
        T.residue_cycles(925.0)
    with pytest.raises(T.TimingError):
        T.closes_exactly(4096, 0.5520019531250)


def test_refuse_rounded_closure_raises():
    with pytest.raises(T.TimingError):
        T.refuse_rounded_closure()
    with pytest.raises(T.TimingError):
        T.refuse_rounded_closure(925, T.MACROCYCLE_S, F(1, 1000))
    # it refuses even when the carrier genuinely does close, because the
    # objection is to the reasoning, not to the number
    with pytest.raises(T.TimingError):
        T.refuse_rounded_closure(4096, T.MACROCYCLE_S, F(1, 10 ** 6))


def test_refuse_rounded_closure_names_the_exact_residue():
    with pytest.raises(T.TimingError, match="2091425/4096"):
        T.refuse_rounded_closure(925)


def test_negative_and_bogus_timing_values_are_refused():
    with pytest.raises(T.TimingError):
        T.cycles(-925)
    with pytest.raises(T.TimingError):
        T.cycles(4096, F(-1, 2))
    with pytest.raises(T.TimingError):
        T.refuse_float_timing(True)
    with pytest.raises(T.TimingError):
        T.refuse_float_timing(object())


# --- the report ---------------------------------------------------------

def test_report_carries_the_required_evidence_labels():
    r = T.exacttiming_report()
    assert r["evidence_class"] == "DERIVED_ARITHMETIC"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["verdict"] == "EXACT_TIMING_REGISTERED"
    assert T.VERDICT == "EXACT_TIMING_REGISTERED"


def test_report_disclaims_and_names_the_unresolved_residue():
    r = T.exacttiming_report()
    text = r["what_this_does_not_say"]
    assert isinstance(text, str) and len(text) > 200
    assert "RESIDUE_NOT_REALISABLE_BY_INTEGER_CARRIER" in text
    assert "what_would_change_this" in r


def test_report_carries_the_macrocycle_the_carriers_and_the_residue():
    r = T.exacttiming_report()
    assert r["macrocycle"]["seconds_exact"] == "2261/4096"
    assert len(r["carriers"]) == 4
    assert r["carriers_that_close"] == ["F_4096_HZ"]
    assert (r["registered_residue"]["status"]
            == "RESIDUE_NOT_REALISABLE_BY_INTEGER_CARRIER")


def test_report_is_json_shaped():
    import json
    json.dumps(T.exacttiming_report())


# --- hygiene ------------------------------------------------------------

def test_the_module_names_no_private_source():
    text = inspect.getsource(T).lower()
    # The tokens are assembled from fragments on purpose: a guard that
    # spells the forbidden literal writes that literal into the public
    # tree and trips the publication firewall on itself.
    forbidden = ("c:" + chr(92) + "users", "one" + "drive",
                 "rgcs" + "-" + "priv" + "ate")
    for token in forbidden:
        assert token not in text
