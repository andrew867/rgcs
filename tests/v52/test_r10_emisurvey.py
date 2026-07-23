"""P10 — blinded ABAB EMI survey: schedule, null, power, refusal, privacy."""

from __future__ import annotations

import numpy as np
import pytest

from r10 import emisurvey as E


def test_abab_schedule_alternates_and_reveal_round_trips():
    sched = E.abab_schedule(8, seed=1)
    states = E.reveal(sched, sched.key)
    # true states strictly alternate A, B, A, B, ...
    assert states == ("A", "B", "A", "B", "A", "B", "A", "B")
    # the blind codes also alternate but do not reveal ON/OFF directly
    assert sched.blind_codes[0] != sched.blind_codes[1]
    assert len(set(sched.blind_codes)) == 2


def test_reveal_rejects_a_foreign_key():
    sched = E.abab_schedule(4, seed=2)
    with pytest.raises(E.EmiError):
        E.reveal(sched, {"not_a_code": "A"})


def test_too_few_blocks_refused():
    with pytest.raises(E.EmiError):
        E.abab_schedule(1)


def test_null_no_difference_gives_p_not_small():
    """Control: with no ON/OFF difference the p-value is not small."""
    rng = np.random.default_rng(3)
    n = 24
    sched = E.abab_schedule(n, seed=3)
    states = np.array(E.reveal(sched, sched.key), dtype=object)
    metrics = rng.normal(0.0, 1.0, size=n)     # identical for ON and OFF
    res = E.shuffled_label_null(metrics, states, trials=1000, seed=4)
    assert res["p_value"] > 0.2
    assert res["verdict"] == "NO_ON_OFF_DIFFERENCE"


def test_power_planted_excess_is_recovered():
    """Power: a real ON-block excess is detected with a small p-value."""
    pw = E.planted_effect_power(n_blocks=24, excess=3.0, trials=1000)
    assert pw["has_power"]
    assert pw["p_value"] < 0.05


def test_block_effect_needs_both_states():
    with pytest.raises(E.EmiError):
        E.block_effect([1.0, 2.0], ["A", "A"])


def test_refuse_causal_claim_raises():
    outcome = E.SurveyOutcome(perceived_communication_quality=0.9,
                              measured_EMI_environment=0.8,
                              instrument_readout_quality=0.7)
    with pytest.raises(E.EmiError):
        E.refuse_causal_claim(outcome)


def test_public_view_omits_private_location():
    survey = E.EmiSurvey(
        survey_id="S1",
        location_private="a specific private address",
        timestamp="2026-07-23T00:00:00Z",
        devices=("led_lamp", "smps"),
        covariates={"location": "private raw location",
                    "temperature_c": 21.0},
    )
    pub = survey.public_view()
    flat = str(pub)
    assert "a specific private address" not in flat
    assert "private raw location" not in flat
    assert "location_private" not in pub
    assert pub["location_disclosed"] == "WITHHELD_PRIVATE"
    assert "location" not in pub["covariates"]
    assert pub["covariates"]["temperature_c"] == 21.0
    assert pub["status"] == "BLOCKED_NO_DATA_SOURCE"


def test_report_is_software_only_and_measures_nothing():
    r = E.emisurvey_report()
    assert r["measured_here"] == "nothing"
    assert r["verdict"] == "EMI_SURVEY_SOFTWARE_ONLY"
    assert r["evidence_class"] == "DERIVED_MATHEMATICS"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["real_data"]["status"] == "BLOCKED_NO_DATA_SOURCE"
    assert "not_faked" in r["real_data"]
    assert len(r["three_outcomes"]) == 3
