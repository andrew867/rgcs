"""R13 P40 — the epoch solver: an alias-limited residue class, a planted
epoch recovered modulo the alias period, and the two refusals.

Every test is deterministic: all epochs, phases and windows are passed
in, and no wall clock is read anywhere in the module under test."""

from __future__ import annotations

from fractions import Fraction

import pytest

from r13 import epochsolve as E


# --- helpers ------------------------------------------------------------

def _constraints_for(epoch, periods):
    return tuple(
        E.PhaseConstraint(Fraction(p), E.phase_offset_of(Fraction(epoch),
                                                         Fraction(p)),
                          label=f"P{i}")
        for i, p in enumerate(periods))


# --- POWER: the alias set has >1 member spaced by the LCM/beat period ---

def test_alias_set_has_more_than_one_member():
    # periods 3 and 4 -> lcm 12; a window of width 40 must contain
    # several aliases, not one.
    constraints = _constraints_for(7, (3, 4))
    aliases = E.epoch_alias_set(constraints, (0, 40))
    assert len(aliases) > 1


def test_alias_members_are_spaced_by_the_lcm_beat_period():
    constraints = _constraints_for(7, (3, 4))
    solution = E.solve_epoch(constraints)
    # lcm(3, 4) = 12 is the beat period.
    assert solution.alias_period == Fraction(12)
    aliases = E.epoch_alias_set(constraints, (0, 40))
    spacings = E.alias_spacing(aliases)
    assert len(spacings) >= 1
    assert all(s == Fraction(12) for s in spacings)
    # and it really is the lcm of the periods
    assert E.alias_period(constraints) == Fraction(12)


def test_alias_set_would_fail_if_it_collapsed_to_one():
    # This is the load-bearing negation: a periodic phase set is NOT a
    # unique time. If the solver ever returned a single member over a
    # wide window, this test would catch it.
    constraints = _constraints_for(7, (3, 4))
    aliases = E.epoch_alias_set(constraints, (0, 100))
    assert len(aliases) >= 8            # 7,19,...,95 -> 8 members
    assert len(set(aliases)) == len(aliases)


def test_alias_spacing_holds_for_fractional_periods():
    # Commensurate rational periods: lcm(3/2, 5/2) = 15/2.
    constraints = _constraints_for(Fraction(1), (Fraction(3, 2),
                                                 Fraction(5, 2)))
    solution = E.solve_epoch(constraints)
    assert solution.alias_period == Fraction(15, 2)
    aliases = E.epoch_alias_set(constraints, (0, 40))
    spacings = E.alias_spacing(aliases)
    assert len(aliases) > 1
    assert all(s == Fraction(15, 2) for s in spacings)


# --- POWER: a planted epoch is recovered modulo the alias period --------

def test_planted_epoch_recovered_modulo_alias_period():
    result = E.plant_and_recover(Fraction(7), (3, 4))
    assert result["consistent"] is True
    assert result["recovered_modulo_alias"] is True
    # 7 mod lcm(3,4)=12 is 7, and that is the base representative
    assert result["alias_period"] == "12"
    assert result["recovered_base_epoch"] == "7"


def test_planted_epoch_recovered_when_above_the_alias_period():
    # Plant an epoch larger than the alias period; recovery is modulo it.
    # 31 mod 12 == 7.
    result = E.plant_and_recover(Fraction(31), (3, 4))
    assert result["recovered_modulo_alias"] is True
    assert result["recovered_base_epoch"] == "7"


def test_planted_recovery_matches_direct_solution():
    constraints = _constraints_for(19, (4, 6))       # lcm 12; 19 mod 12 = 7
    solution = E.solve_epoch(constraints)
    assert solution.consistent is True
    assert solution.alias_period == Fraction(12)
    assert solution.base_epoch == Fraction(7)
    assert solution.is_unique() is False


def test_inconsistent_phases_give_an_empty_alias_class():
    # t ≡ 0 (mod 2) and t ≡ 1 (mod 4) cannot both hold: gcd(2,4)=2 does
    # not divide (1-0). A definite arithmetic result, not a date.
    constraints = (
        E.PhaseConstraint(Fraction(2), Fraction(0)),
        E.PhaseConstraint(Fraction(4), Fraction(1)),
    )
    solution = E.solve_epoch(constraints)
    assert solution.consistent is False
    assert solution.base_epoch is None
    assert E.epoch_alias_set(constraints, (0, 100)) == ()


# --- the two refusals ---------------------------------------------------

def test_refuse_epoch_as_unique_time_always_raises():
    with pytest.raises(E.EpochSolveError, match="ALIAS CLASS"):
        E.refuse_epoch_as_unique_time()


def test_refuse_epoch_as_unique_time_raises_with_a_solution():
    solution = E.solve_epoch(_constraints_for(7, (3, 4)))
    with pytest.raises(E.EpochSolveError):
        E.refuse_epoch_as_unique_time(solution, claimed_epoch=202607)


def test_refuse_phase_match_as_timestamp_authentication_always_raises():
    with pytest.raises(E.EpochSolveError, match="not timestamp authentication"):
        E.refuse_phase_match_as_timestamp_authentication()


def test_refuse_phase_match_raises_with_a_claimed_source():
    with pytest.raises(E.EpochSolveError):
        E.refuse_phase_match_as_timestamp_authentication(
            matched_phase="0.5", source="SOME_SOURCE")


# --- validation ---------------------------------------------------------

def test_bad_phase_offset_is_refused():
    with pytest.raises(E.EpochSolveError):
        E.PhaseConstraint(Fraction(3), Fraction(3))   # offset must be < period


def test_inverted_window_is_refused():
    with pytest.raises(E.EpochSolveError):
        E.epoch_alias_set(_constraints_for(7, (3, 4)), (40, 0))


# --- report -------------------------------------------------------------

def test_report_carries_verdict_and_claim_discipline():
    r = E.epochsolve_report()
    assert r["verdict"] == "EPOCH_SOLVER_ALIAS_LIMITED"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["claim_class"] == "DERIVED_ARITHMETIC"
    assert r["alias_set_has_more_than_one_member"] is True
    assert r["spacings_equal_alias_period"] is True
    assert r["power_control"]["recovered_modulo_alias"] is True
    assert "what_this_does_not_say" in r
