"""P17 — a unified boundary-energy ledger that closes and invents no energy."""

from __future__ import annotations

import math

import pytest

from r13 import boundaryenergy as E

ALL_DOMAINS = list(E.BoundaryDomain)


# --- abrupt and finite-time changes for all three domains -----------------

@pytest.mark.parametrize("domain", ALL_DOMAINS)
def test_abrupt_change_closes_for_every_domain(domain):
    change = E.BoundaryChange(domain, param_before=1.0, param_after=4.0,
                              coordinate=2.0)
    result = E.abrupt_change(change)
    assert result.profile == "ABRUPT"
    assert result.tau == 0.0
    assert result.dissipated == 0.0
    assert result.radiated == 0.0
    # E_after == E_before + W_boundary, nothing lost in zero time
    assert result.energy_after == result.energy_before + result.boundary_work
    # W = 0.5 * (4 - 1) * 2**2 = 6.0
    assert result.boundary_work == 0.5 * (4.0 - 1.0) * 2.0 ** 2
    assert result.ledger()["closes"]
    assert result.ledger()["e_unclosed"] == 0.0


@pytest.mark.parametrize("domain", ALL_DOMAINS)
def test_finite_time_change_closes_for_every_domain(domain):
    change = E.BoundaryChange(domain, param_before=1.0, param_after=4.0,
                              coordinate=2.0)
    result = E.finite_time_change(change, tau=3.0)
    assert result.profile == "FINITE_TIME"
    assert result.tau == 3.0
    assert result.dissipated > 0.0
    assert result.radiated > 0.0
    # E_after == E_before + W - D - R, by construction
    assert math.isclose(
        result.energy_after,
        result.energy_before + result.boundary_work
        - result.dissipated - result.radiated, rel_tol=0.0, abs_tol=1e-12)
    assert result.ledger()["closes"]


def test_finite_time_radiation_grows_as_the_ramp_gets_faster():
    change = E.BoundaryChange(E.BoundaryDomain.OPTICAL, 1.0, 4.0, 2.0)
    fast = E.finite_time_change(change, tau=0.5)
    slow = E.finite_time_change(change, tau=5.0)
    assert fast.radiated > slow.radiated


def test_finite_time_requires_positive_tau():
    change = E.BoundaryChange(E.BoundaryDomain.MECHANICAL, 1.0, 4.0)
    with pytest.raises(E.BoundaryEnergyError):
        E.finite_time_change(change, tau=0.0)
    with pytest.raises(E.BoundaryEnergyError):
        E.finite_time_change(change, tau=-1.0)


# --- the synthetic ledger closes; omitting boundary work has teeth --------

def test_synthetic_ledger_closes_at_exactly_zero():
    led = E.synthetic_ledger(include_boundary_work=True, sigma=0.0)
    assert led["e_unclosed"] == 0.0
    assert led["closes"]
    assert not led["closure_is_vacuous"]


def test_omitting_boundary_work_leaves_a_residual_equal_to_that_work():
    led = E.synthetic_ledger(include_boundary_work=False, sigma=0.0)
    work = E.SYNTHETIC_TERMS["boundary_work"]
    assert abs(led["e_unclosed"]) == work
    assert not led["closes"]


def test_power_check_reports_both_teeth():
    pc = E.power_check()
    assert pc["closed_residual_is_zero"]
    assert pc["closed_closes"]
    assert pc["omitted_residual_magnitude_equals_work"]
    assert not pc["omitted_closes"]


# --- the blocked ledger: interval includes zero, terms blocked ------------

def test_blocked_ledger_interval_includes_zero_and_terms_are_blocked():
    led = E.blocked_ledger()
    lo, hi = led["e_unclosed_interval"]
    assert lo == -math.inf and hi == math.inf
    assert led["interval_includes_zero"]
    assert led["closure_is_vacuous"]
    assert led["all_terms_blocked"]
    assert led["claim_class"] == "BLOCKED_MISSING_INPUT"
    for term in led["terms"]:
        assert term["status"] == "BLOCKED_MISSING_INPUT"
        assert term["sigma"] is None


def test_an_unknown_sigma_term_is_refused():
    with pytest.raises(E.BoundaryEnergyError):
        E.energy_ledger(0.0, 0.0, 0.0, sigmas={"not_a_term": 1.0})


# --- the four load-bearing refusals ---------------------------------------

def test_refuse_unclosed_as_new_energy_raises():
    with pytest.raises(E.BoundaryEnergyError):
        E.refuse_unclosed_as_new_energy(1.5, (-3.0, 3.0))


def test_refuse_ignored_boundary_work_raises():
    with pytest.raises(E.BoundaryEnergyError):
        E.refuse_ignored_boundary_work(
            E.synthetic_ledger(include_boundary_work=False))


def test_refuse_transferred_energy_as_loss_raises():
    with pytest.raises(E.BoundaryEnergyError):
        E.refuse_transferred_energy_as_loss(
            from_mode=0, to_modes=(1, 2), transferred=0.4)


def test_refuse_infinite_free_energy_raises():
    with pytest.raises(E.BoundaryEnergyError):
        E.refuse_infinite_free_energy(0.0)


# --- report ---------------------------------------------------------------

def test_report_verdict_and_no_measurement():
    r = E.boundaryenergy_report()
    assert r["verdict"] == "DYNAMIC_BOUNDARY_ENERGY_LEDGER_CLOSES_NO_NEW_ENERGY"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["claim_class"] == "REPOSITORY_COMPUTATIONAL_RESULT"
    assert [d.value for d in E.BoundaryDomain] == [
        "MECHANICAL", "ELECTRICAL", "OPTICAL"]
    assert "what_this_does_not_say" in r
