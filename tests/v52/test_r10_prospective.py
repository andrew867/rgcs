"""P18 — prospective holdout registry and paper-trading harness."""

from __future__ import annotations

import pytest

from r10 import prospective as P


def _pred(pid="p1", domain=P.Domain.SIGNAL, freeze=100.0):
    return P.Prediction(pid, domain, "X will exceed threshold Y",
                        freeze_time=freeze, horizon_s=3600.0,
                        success_criterion="metric > Y at horizon",
                        multiplicity=1)


def test_a_prediction_freezes_with_a_hash():
    p = _pred()
    assert len(p.prereg_hash) == 64
    assert p.prereg_hash == _pred().prereg_hash
    assert p.prereg_hash != _pred(pid="p2").prereg_hash


def test_default_outcome_is_awaiting():
    reg = P.HoldoutRegistry()
    reg.register(_pred())
    assert reg.outcome("p1") is P.Outcome.AWAITING_OUTCOME


def test_outcome_before_freeze_is_a_lookahead_and_refused():
    reg = P.HoldoutRegistry()
    reg.register(_pred(freeze=100.0))
    with pytest.raises(P.ProspectiveError):
        reg.record_outcome("p1", P.Outcome.CONFIRMED, observed_time=50.0)


def test_outcome_after_freeze_is_allowed():
    reg = P.HoldoutRegistry()
    reg.register(_pred(freeze=100.0))
    reg.record_outcome("p1", P.Outcome.FAILED, observed_time=200.0)
    assert reg.outcome("p1") is P.Outcome.FAILED


def test_a_failed_prediction_cannot_be_deleted():
    reg = P.HoldoutRegistry()
    reg.register(_pred())
    with pytest.raises(P.ProspectiveError):
        reg.refuse_delete_failure("p1")


def test_duplicate_registration_refused():
    reg = P.HoldoutRegistry()
    reg.register(_pred())
    with pytest.raises(P.ProspectiveError):
        reg.register(_pred())


def test_scoreboard_counts_failures():
    reg = P.HoldoutRegistry()
    for i, o in enumerate([P.Outcome.CONFIRMED, P.Outcome.FAILED,
                           P.Outcome.FAILED]):
        reg.register(_pred(pid=f"p{i}", freeze=0.0))
        reg.record_outcome(f"p{i}", o, observed_time=10.0)
    sb = reg.scoreboard()
    assert sb["failed"] == 2 and sb["confirmed"] == 1 and sb["total"] == 3


def test_every_domain_is_representable():
    for d in P.Domain:
        assert _pred(domain=d).domain is d


def test_multiplicity_shrinks_alpha():
    assert P.multiplicity_adjusted_alpha(0.05, 5) == pytest.approx(0.01)


def test_paper_hypothesis_requires_paper_only():
    with pytest.raises(P.ProspectiveError):
        P.PaperHypothesis("h", 0.0, ("PLAT",), "e", "x", "bmk", 1.0,
                          "costs", 0.2, paper_only=False)


def test_paper_hypothesis_requires_frozen_rules():
    with pytest.raises(P.ProspectiveError):
        P.PaperHypothesis("h", 0.0, ("PLAT",), "", "x", "bmk", 1.0,
                          "costs", 0.2)          # empty entry_rule


def test_a_valid_paper_hypothesis_is_paper_only():
    h = P.PaperHypothesis("h", 0.0, ("PLAT", "GOLD"), "entry", "exit",
                          "SPX", 86400.0, "10bps", 0.2)
    assert h.paper_only is True


def test_real_money_is_refused():
    with pytest.raises(P.ProspectiveError):
        P.refuse_real_money()


def test_report_awaits_outcome_and_places_no_trade():
    r = P.prospective_report()
    assert r["measured_here"] == "nothing"
    assert r["verdict"] == "AWAITING_OUTCOME"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
