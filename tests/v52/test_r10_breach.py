"""S17/S18 — breach as a resonance shift, and pump-branch separation.

The load-bearing tests are the ones that stop this from becoming an
anomaly generator: no baseline is refused outright, the budget shrinks
only when causes are actually controlled, and no code path anywhere
returns an exotic verdict.
"""

from __future__ import annotations

from fractions import Fraction as F

import pytest

from r10 import breach as B

ALL_CONTROLLABLE = {c.name for c in B.ORDINARY_CAUSES if c.controllable}


# --- S18: the branches stay apart --------------------------------------

def test_eight_hz_ladder_is_exact():
    L = B.eight_hz_ladder()
    assert L["exact"]
    assert L["result_hz"] == "4096"


def test_the_ladder_does_not_claim_privilege():
    L = B.eight_hz_ladder()
    n = L["what_it_does_not_show"]
    assert "3584" in n           # the counterexample from 7
    assert "property of the radix" in n


def test_twenty_point_four_eight_is_exactly_4096_over_200():
    f = B.PUMP_BRANCHES["PUMP_20_48_HZ"]["hz"]
    assert f == F(512, 25)
    assert f * 200 == 4096


def test_all_branches_are_exact_rationals():
    for name, spec in B.PUMP_BRANCHES.items():
        assert isinstance(spec["hz"], F), name
        assert spec["exact"], name
        assert spec["role"], name


def test_the_low_branches_really_do_differ():
    assert B.fractional_separation("PUMP_20_HZ", "PUMP_20_48_HZ") == \
        pytest.approx(0.024)
    assert B.fractional_separation("PUMP_20_HZ", "PUMP_21_HZ") == \
        pytest.approx(0.05)


def test_separation_is_resolvable_at_crystal_q():
    """A quartz resonator's Q is 1e4-1e6. At 1e5 the branches are
    thousands of linewidths apart -- different frequencies, not a
    matter of opinion."""
    r = B.resolvable("PUMP_20_HZ", "PUMP_20_48_HZ", 1e5)
    assert r["resolvable"]
    assert r["separated_in_linewidths"] > 1000


def test_separation_is_not_resolvable_at_low_q():
    """The test must be capable of the other answer, or it is not
    measuring anything. At Q=10 they fall inside one linewidth."""
    r = B.resolvable("PUMP_20_HZ", "PUMP_20_48_HZ", 10)
    assert not r["resolvable"]
    assert "statement about Q" in r["note"]


def test_resolvability_turns_over_near_q_equals_one_over_separation():
    sep = B.fractional_separation("PUMP_20_HZ", "PUMP_20_48_HZ")
    q_crit = 1.0 / sep
    assert not B.resolvable("PUMP_20_HZ", "PUMP_20_48_HZ",
                            q_crit * 0.9)["resolvable"]
    assert B.resolvable("PUMP_20_HZ", "PUMP_20_48_HZ",
                        q_crit * 1.1)["resolvable"]


def test_invalid_q_refused():
    with pytest.raises(ValueError):
        B.resolvable("PUMP_20_HZ", "PUMP_21_HZ", 0)


def test_collapsing_the_branches_is_refused():
    with pytest.raises(B.CollapsedBranches) as e:
        B.refuse_branch_collapse()
    msg = str(e.value)
    assert "2.40%" in msg
    assert "not interchangeable" in msg


# --- S17: the budget ----------------------------------------------------

def test_every_ordinary_cause_carries_a_source_and_a_control():
    for c in B.ORDINARY_CAUSES:
        assert c.source, c.name
        assert c.control, c.name
        assert 0 <= c.typical_ppm <= c.worst_ppm


def test_aging_is_the_one_that_cannot_be_controlled():
    aging = [c for c in B.ORDINARY_CAUSES if c.name == "AGING"][0]
    assert not aging.controllable
    assert "cannot be eliminated" in aging.control


def test_the_uncontrolled_budget_is_over_ten_ppm():
    """A few ppm is not an anomaly; it is Tuesday."""
    assert B.ordinary_budget_ppm() > 10.0


def test_controlling_causes_shrinks_the_budget():
    full = B.ordinary_budget_ppm()
    controlled = B.ordinary_budget_ppm(ALL_CONTROLLABLE)
    assert controlled < full
    # aging alone survives, and it is 2 ppm
    assert controlled == pytest.approx(2.0)


def test_the_budget_never_reaches_zero():
    """Aging is irreducible, so no amount of control licenses a
    zero-tolerance claim."""
    assert B.ordinary_budget_ppm(ALL_CONTROLLABLE) > 0


def test_naming_an_unknown_cause_as_controlled_is_refused():
    with pytest.raises(ValueError):
        B.ordinary_budget_ppm({"PHRYLL_FIELD"})


# --- S17: the verdicts --------------------------------------------------

def _ok(ppm, controlled=None):
    return B.assess_shift(ppm, controlled=controlled or set(),
                          has_pre_baseline=True, baseline_days=30)


def test_a_small_shift_is_ordinary():
    assert _ok(3.0)["verdict"] == "ORDINARY"


def test_a_large_shift_with_nothing_controlled_is_not_promoted():
    """50 ppm beats the typical budget but sits inside the worst case,
    so it buys nothing while causes are uncontrolled."""
    r = _ok(50.0)
    assert r["verdict"] == "WITHIN_UNCONTROLLED_BUDGET"
    assert r["uncontrolled"]


def test_the_same_shift_means_more_once_causes_are_controlled():
    """The verdict must depend on the controls, or the controls are
    decorative."""
    assert _ok(50.0)["verdict"] == "WITHIN_UNCONTROLLED_BUDGET"
    assert _ok(50.0, ALL_CONTROLLABLE)["verdict"] == \
        "UNEXPLAINED_BY_THIS_BUDGET"


def test_no_baseline_is_refused_outright():
    """Aging guarantees the frequency was already moving. Without a
    before-state there is nothing to have shifted from."""
    r = B.assess_shift(1000.0, has_pre_baseline=False)
    assert r["verdict"] == "REFUSED_NO_BASELINE"
    assert "unfalsifiable" in r["why"]


def test_a_zero_length_baseline_is_also_refused():
    r = B.assess_shift(1000.0, has_pre_baseline=True, baseline_days=0)
    assert r["verdict"] == "REFUSED_NO_BASELINE"


def test_negative_shift_magnitude_refused():
    with pytest.raises(ValueError):
        _ok(-1.0)


def test_no_verdict_anywhere_is_exotic():
    """The strongest guard in the module: there is no code path that
    returns a positive exotic finding."""
    for v in B.VERDICTS:
        assert "BREACH" not in v
        assert "CONFIRMED" not in v
        assert "EXOTIC" not in v
        assert "ANOMAL" not in v.upper()
    assert set(B.VERDICTS) == {
        "ORDINARY", "WITHIN_UNCONTROLLED_BUDGET",
        "UNEXPLAINED_BY_THIS_BUDGET", "REFUSED_NO_BASELINE"}


def test_every_reachable_verdict_is_declared():
    seen = {
        _ok(3.0)["verdict"],
        _ok(50.0)["verdict"],
        _ok(50.0, ALL_CONTROLLABLE)["verdict"],
        B.assess_shift(1.0, has_pre_baseline=False)["verdict"],
    }
    assert seen <= set(B.VERDICTS)
    assert len(seen) == 4          # all four are reachable


def test_the_unexplained_verdict_disclaims_itself():
    r = _ok(500.0, ALL_CONTROLLABLE)
    n = r["what_this_verdict_is_not"]
    assert "does not mean the cause is exotic" in n or \
        "certainly does not mean the cause is" in n
    assert "missing from the budget" in n


# --- protocol and claim discipline -------------------------------------

def test_the_protocol_names_the_control_that_matters_most():
    p = B.breach_protocol()
    assert "second untreated crystal" in p["the_control_that_matters_most"]
    assert "differential" in p["the_control_that_matters_most"]


def test_the_protocol_requires_a_long_baseline():
    p = B.breach_protocol()
    assert any("weeks, not hours" in s
               for s in p["required_before_any_claim"])


def test_hardware_is_declared_deferred():
    p = B.breach_protocol()
    assert p["hardware_status"].startswith("DEFERRED")
    assert p["measured_here"] == "nothing"


def test_a_breach_claim_is_refused():
    with pytest.raises(RuntimeError) as e:
        B.refuse_breach_claim()
    msg = str(e.value)
    assert "No apparatus has been built" in msg
    assert "UNEXPLAINED_BY_THIS_BUDGET" in msg
