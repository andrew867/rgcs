"""R12 — epoch candidates from four independent clocks: their
characteristic times, the twenty-one-order spread, the Cs-133 dating
refusal, the mixed-time-scale refusal, and the non-unique epoch."""

from __future__ import annotations

import pytest

from r12 import epochcand as E


# --- all four clocks are present ---------------------------------------

def test_all_four_clocks_have_characteristic_times():
    times = E.characteristic_times()
    assert len(times) == 4
    for entry in times.values():
        assert entry["characteristic_time_s"] > 0
    kinds = {entry["kind"] for entry in times.values()}
    assert kinds == {
        "GEOLOGICAL_DECAY", "DECADES_DECAY",
        "FREQUENCY_DEFINITION", "ASTRONOMICAL_TIME_SCALE"}


def test_ba130_half_life_is_of_order_1e21_years():
    assert 1e20 <= E.BA130_HALF_LIFE_YEARS <= 1e22
    assert E.BA130.relative_uncertainty is not None
    assert E.BA130.relative_uncertainty > 0.0


def test_cs137_half_life_is_30_05_years():
    assert E.CS137_DECAY_YEARS == 30.05
    assert str(E.CS137_HALF_LIFE_YEARS_EXACT) == "601/20"


def test_cs133_is_exactly_the_si_second_and_is_a_definition():
    d = E.cs133_frequency_standard()
    assert d["hyperfine_hz"] == 9192631770
    assert d["is_exact_integer"] is True
    assert d["claim_class"] == "EXACT_IDENTITY"
    assert d["uncertainty_kind"] == "ZERO_BY_DEFINITION"
    assert d["is_dating_clock"] is False


# --- Cs-133 is a standard, not a dating clock --------------------------

def test_refuse_cs133_as_dating_clock_always_raises():
    with pytest.raises(E.EpochCandError, match="dating clock"):
        E.refuse_cs133_as_dating_clock()


def test_refuse_cs133_as_dating_clock_raises_with_a_claimed_year():
    with pytest.raises(E.EpochCandError):
        E.refuse_cs133_as_dating_clock(claimed_epoch_year=202607)


# --- mixed time scales -------------------------------------------------

def test_refuse_mixed_time_scale_raises_for_tai_vs_ut1():
    with pytest.raises(E.EpochCandError, match="different time scales"):
        E.refuse_mixed_time_scale(E.TimeScale.TAI, E.TimeScale.UT1)


def test_refuse_mixed_time_scale_allows_same_scale():
    assert E.refuse_mixed_time_scale(E.TimeScale.TAI, E.TimeScale.TAI) is None
    assert E.refuse_mixed_time_scale(E.TimeScale.TT, E.TimeScale.TT) is None


def test_all_five_named_scales_plus_utc_exist():
    scales = E.time_scales()["scales"]
    for name in ("TT", "TDB", "TAI", "UT1", "ET"):
        assert name in scales
    assert "UTC" in scales


# --- the twenty-one-order spread ---------------------------------------

def test_epoch_span_orders_of_magnitude_exceeds_twenty():
    spread = E.epoch_span_orders_of_magnitude()
    assert spread > 20.0


# --- combining candidates yields an interval, not a point --------------

def test_combine_candidates_returns_more_than_one_member():
    combined = E.combine_candidates()
    assert combined.alias_count > 1
    assert combined.unique is False
    assert len(combined.members) > 1


def test_combine_candidates_refuses_a_zero_width_interval():
    with pytest.raises(E.EpochCandError):
        E.combine_candidates(coarse_lo_years=5.0, coarse_hi_years=5.0)


# --- the epoch is never unique -----------------------------------------

def test_refuse_unique_epoch_always_raises_with_no_args():
    with pytest.raises(E.EpochCandError):
        E.refuse_unique_epoch()


def test_refuse_unique_epoch_raises_even_when_fully_supplied():
    # Even a claimed alias_count of 1 with both extra observables cannot
    # open the escape here, because the real combined alias count is huge
    # and this module always evaluates the real one when no count is given.
    with pytest.raises(E.EpochCandError):
        E.refuse_unique_epoch(
            alias_count=E.combine_candidates().alias_count,
            independent_coarse_anchor="SOME_ANCHOR",
            second_coherent_observable="SOME_OBSERVABLE",
            claimed_epoch_year=202607)


# --- report ------------------------------------------------------------

def test_report_carries_verdict_and_claim_discipline():
    r = E.epochcand_report()
    assert r["verdict"] == "EPOCH_CANDIDATES_ENUMERATED_NONE_UNIQUE"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["spread_exceeds_twenty"] is True
    assert r["combined_candidate"]["unique"] is False
    assert "what_this_does_not_say" in r
