"""P09 — bench readiness and the honest stop."""

from __future__ import annotations

import pytest

from r6 import bench as B


def test_not_ready_for_bench():
    assert B.bench_readiness()["ready_for_bench"] is False


def test_status_says_physically_untested():
    assert B.bench_readiness()["status"] == \
        "SOFTWARE_COMPLETE_PHYSICALLY_UNTESTED"


def test_gates_that_need_institutions_are_shut():
    """Documentation gates may open; the rest cannot without people."""
    missing = B.bench_readiness()["gates_missing"]
    for g in ("CALIBRATION_PLAN", "SAFETY_REVIEW",
              "OPERATOR_COMPETENCE", "PREREGISTERED_ANALYSIS"):
        assert g in missing


def test_every_gate_has_recorded_evidence():
    a = B.current_assessment()
    for g in B.READINESS_GATES:
        assert g in a.evidence, f"{g} has no evidence entry"


def test_absent_gates_say_absent():
    a = B.current_assessment()
    for g in a.missing():
        assert a.evidence[g].startswith("ABSENT"), (
            f"{g} is missing but its evidence does not say so")


def test_biological_exposure_is_refused_entirely():
    h = B.HAZARDS["BIOLOGICAL_EXPOSURE"]
    assert h["status"] == "REFUSED_ENTIRELY"
    assert h["control"] == "none offered"


def test_mains_construction_requires_a_qualified_person():
    assert B.HAZARDS["MAINS_CONSTRUCTION"]["status"] == \
        "REFUSED_UNLESS_QUALIFIED"


def test_optical_hazard_requires_enclosed_beam():
    assert "enclosed" in B.HAZARDS["OPTICAL"]["control"]
    assert "eye height" in B.HAZARDS["OPTICAL"]["control"]


def test_rf_hazard_excludes_open_radiator():
    assert "no open 2.45 GHz radiator" in B.HAZARDS["RF_EMISSION"]["control"]


def test_fracture_hazard_is_present():
    """The source itself warns the sound could breach the crystal."""
    assert "MECHANICAL_FRACTURE" in B.HAZARDS


def test_refused_hazards_are_listed():
    r = B.bench_readiness()
    assert set(r["hazards_refused"]) == {"MAINS_CONSTRUCTION",
                                         "BIOLOGICAL_EXPOSURE"}


def test_statement_denies_every_physical_act():
    s = B.bench_readiness()["statement"].lower()
    for phrase in ("no coil has been wound", "no crystal",
                   "no clock compared", "no geophysical dataset"):
        assert phrase in s


def test_next_step_is_the_reachable_one():
    """The honest recommendation is the witness channel, not the coil."""
    n = B.bench_readiness()["next_real_step"]
    assert "two-oscillator" in n
    assert "without needing the coil" in n


def test_synthetic_cannot_be_relabelled_as_measurement():
    with pytest.raises(RuntimeError) as e:
        B.refuse_synthetic_as_measurement()
    assert "BENCH_MEASUREMENT" in str(e.value)


def test_assessment_record_round_trips():
    rec = B.current_assessment().as_record()
    assert rec["ready"] is False
    assert isinstance(rec["missing"], list)
