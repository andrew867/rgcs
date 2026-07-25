"""P34 — negative results and non-claims register."""

from __future__ import annotations

import pytest

from r15 import nonclaims as N


def test_every_non_claim_maps_to_a_raising_refusal():
    # verify_refusals_exist returns the list of MISSING/non-raising refusals
    assert N.verify_refusals_exist() == []


def test_there_is_no_phryll_detected_state():
    r = N.nonclaims_report()
    assert r["has_phryll_detected_state"] is False
    assert r["residual_ceiling"] == "UNEXPLAINED_INSTRUMENT_RESIDUAL"
    assert len(r["non_claims"]) >= 8


def test_asserting_a_non_claim_is_refused():
    with pytest.raises(N.NonClaimError):
        N.refuse_positive_claim("new energy beyond measured input")


def test_report_claims_nothing_measured():
    r = N.nonclaims_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
