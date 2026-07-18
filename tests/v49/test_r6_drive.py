"""P02 — drive programme compiler: modes, realization, energy matching."""

from __future__ import annotations

import math

import pytest

import r6
from r6 import drive
from r6.drive import DriveError, DriveLimits, DriveProgram


# --------------------------------------------------------------------
# Modes
# --------------------------------------------------------------------

def test_all_four_connection_configurations_exist():
    assert drive.DRIVE_MODES == (
        "SINGLE", "PARALLEL", "SERIES", "ALTERNATING_DIFFERENTIAL")
    for m in drive.DRIVE_MODES:
        assert drive.MODE_DESCRIPTIONS[m].strip()


def test_unknown_mode_refused():
    with pytest.raises(DriveError, match="unknown drive mode"):
        DriveProgram("TORSION", ((1.0, 0.0),), 1e-3)


# --------------------------------------------------------------------
# Programme validation
# --------------------------------------------------------------------

def test_valid_program_derived_quantities():
    p = DriveProgram("PARALLEL", ((1.0, 1.0), (2.0, 2.0)), 1e-3,
                     repetition=3)
    assert p.n_slots == 2
    assert p.total_slots == 6
    assert p.total_duration_s == pytest.approx(6e-3)
    assert len(p.expanded_slots()) == 6


@pytest.mark.parametrize("kwargs", [
    dict(mode="PARALLEL", slots=(), slot_duration_s=1e-3),
    dict(mode="PARALLEL", slots=((1.0,),), slot_duration_s=1e-3),
    dict(mode="PARALLEL", slots=((1.0, 1.0),), slot_duration_s=0.0),
    dict(mode="PARALLEL", slots=((1.0, 1.0),), slot_duration_s=-1e-3),
    dict(mode="PARALLEL", slots=((float("nan"), 1.0),),
         slot_duration_s=1e-3),
    dict(mode="PARALLEL", slots=((1.0, 1.0),), slot_duration_s=1e-3,
         repetition=0),
])
def test_bad_programs_refused(kwargs):
    with pytest.raises(DriveError):
        DriveProgram(**kwargs)


def test_series_mode_refuses_unequal_currents():
    with pytest.raises(DriveError, match="SERIES"):
        DriveProgram("SERIES", ((1.0, 0.0),), 1e-3)


def test_single_mode_refuses_current_in_the_open_winding():
    with pytest.raises(DriveError, match="open"):
        DriveProgram("SINGLE", ((1.0, 1.0),), 1e-3)


def test_program_record_is_labelled_requested():
    p = drive.alternating_program(4, 2.0)
    rec = p.as_record()
    assert rec["stage"] == "REQUESTED"
    assert rec["evidence_class"] == "SYNTHETIC_MODEL"
    assert rec["units"]["slot_duration_s"] == "s"
    assert "no coil has been wound" in rec["note"]


# --------------------------------------------------------------------
# Limits
# --------------------------------------------------------------------

@pytest.mark.parametrize("kwargs", [
    dict(max_amplitude_a=0.0),
    dict(slew_rate_a_per_s=-1.0),
    dict(sample_rate_hz=0.0),
    dict(load_resistance_ohm=float("inf")),
])
def test_bad_limits_refused(kwargs):
    with pytest.raises(DriveError):
        DriveLimits(**kwargs)


# --------------------------------------------------------------------
# The source programme
# --------------------------------------------------------------------

def test_alternating_program_matches_the_source_sequence():
    """copper 1-0-1-0-1-0, silver 0-1-0-1-0-1, equal intensity."""
    p = drive.alternating_program(n_slots=6, amplitude_a=5.0)
    assert p.mode == "ALTERNATING_DIFFERENTIAL"
    train1 = tuple(1 if i1 else 0 for i1, _ in p.slots)
    train2 = tuple(1 if i2 else 0 for _, i2 in p.slots)
    assert train1 == (1, 0, 1, 0, 1, 0)
    assert train2 == (0, 1, 0, 1, 0, 1)
    # equal in intensity
    assert {abs(v) for s in p.slots for v in s if v} == {5.0}


def test_alternating_program_never_energises_both_windings():
    p = drive.alternating_program(8, 3.0)
    for i1, i2 in p.slots:
        assert i1 == 0.0 or i2 == 0.0


@pytest.mark.parametrize("kwargs", [
    dict(n_slots=0), dict(n_slots=-2), dict(amplitude_a=0.0),
    dict(amplitude_a=-1.0),
])
def test_alternating_program_refuses_bad_arguments(kwargs):
    with pytest.raises(DriveError):
        drive.alternating_program(**kwargs)


# --------------------------------------------------------------------
# Energy and duty
# --------------------------------------------------------------------

def test_energy_per_slot_arithmetic():
    lim = DriveLimits(load_resistance_ohm=2.0)
    p = DriveProgram("PARALLEL", ((1.0, 1.0), (2.0, 0.0)), 1e-3,
                     repetition=2)
    e = drive.energy_per_slot(p, lim)
    assert e["per_slot_j"][0] == pytest.approx(2.0 * 2.0 * 1e-3)
    assert e["per_slot_j"][1] == pytest.approx(4.0 * 2.0 * 1e-3)
    assert e["total_energy_j"] == pytest.approx(
        (e["per_slot_j"][0] + e["per_slot_j"][1]) * 2)
    assert e["units"]["total_energy_j"] == "J"
    assert e["evidence_class"] == "SYNTHETIC_MODEL"


def test_duty_cycle_of_the_source_programme():
    p = drive.alternating_program(6, 5.0)
    d = drive.duty_cycle(p)
    assert d["winding_1_duty"] == pytest.approx(0.5)
    assert d["winding_2_duty"] == pytest.approx(0.5)
    assert d["simultaneous_duty"] == 0.0
    assert d["any_winding_duty"] == 1.0
    assert d["units"]["winding_1_duty"] == "1"


def test_duty_cycle_refuses_negative_threshold():
    with pytest.raises(DriveError):
        drive.duty_cycle(drive.alternating_program(4, 1.0),
                         threshold_a=-1.0)


# --------------------------------------------------------------------
# REQUESTED vs REALIZED
# --------------------------------------------------------------------

def test_slew_limiting_makes_realized_differ_from_requested():
    p = drive.alternating_program(6, 5.0, slot_duration_s=1e-3)
    c = drive.compile_program(p, drive.DEFAULT_LIMITS)
    assert c.slew_limited is True
    assert c.max_deviation_a > 0.0
    assert c.requested_a != c.realized_a
    # a slew-limited driver cannot deliver the requested joules
    assert c.realized_energy_j < c.requested_energy_j
    assert c.energy_shortfall_fraction > 0.0


def test_an_infinitely_fast_driver_realizes_the_request():
    p = drive.alternating_program(4, 1.0, slot_duration_s=1e-3)
    lim = DriveLimits(max_amplitude_a=10.0, slew_rate_a_per_s=1e12,
                      sample_rate_hz=1e5, load_resistance_ohm=1.0)
    c = drive.compile_program(p, lim)
    assert c.slew_limited is False
    assert c.clipped is False
    assert c.max_deviation_a == pytest.approx(0.0)
    assert c.realized_energy_j == pytest.approx(c.requested_energy_j)


def test_amplitude_clipping_is_recorded():
    p = DriveProgram("PARALLEL", ((20.0, 20.0),), 1e-3)
    lim = DriveLimits(max_amplitude_a=5.0, slew_rate_a_per_s=1e9,
                      sample_rate_hz=1e5)
    c = drive.compile_program(p, lim)
    assert c.clipped is True
    peak = max(max(abs(a), abs(b)) for a, b in c.realized_a)
    assert peak == pytest.approx(5.0)
    assert c.max_deviation_a == pytest.approx(15.0)


def test_compiled_record_separates_requested_and_realized():
    p = drive.alternating_program(6, 5.0)
    rec = drive.compile_program(p).as_record()
    assert rec["requested"]["stage"] == "REQUESTED"
    assert rec["realized"]["stage"] == "REALIZED"
    assert rec["requested"]["energy_j"] != rec["realized"]["energy_j"]
    assert rec["drive_mode"] == "ALTERNATING_DIFFERENTIAL"
    assert rec["evidence_class"] == "SYNTHETIC_MODEL"
    assert rec["units"]["max_deviation_a"] == "A"
    assert "no coil has been wound" in rec["note"]


def test_compilation_is_deterministic():
    p = drive.alternating_program(6, 5.0)
    a = drive.compile_program(p)
    b = drive.compile_program(p)
    assert a.realized_a == b.realized_a
    assert a.max_deviation_a == b.max_deviation_a


def test_realized_respects_the_slew_rate_sample_by_sample():
    lim = drive.DEFAULT_LIMITS
    max_step = lim.slew_rate_a_per_s / lim.sample_rate_hz
    c = drive.compile_program(drive.alternating_program(6, 5.0), lim)
    prev = (0.0, 0.0)
    for cur in c.realized_a:
        for ch in (0, 1):
            assert abs(cur[ch] - prev[ch]) <= max_step * (1 + 1e-12)
        prev = cur


def test_too_coarse_a_sample_rate_is_refused():
    p = drive.alternating_program(4, 1.0, slot_duration_s=1e-6)
    lim = DriveLimits(sample_rate_hz=100.0)
    with pytest.raises(DriveError, match="fewer than"):
        drive.compile_program(p, lim)


def test_compile_refuses_a_non_program():
    with pytest.raises(DriveError):
        drive.compile_program({"mode": "PARALLEL"})


# --------------------------------------------------------------------
# The energy-matched control
# --------------------------------------------------------------------

def test_control_delivers_the_same_energy_without_alternating():
    p = drive.alternating_program(6, 5.0)
    ctl = drive.matched_energy_control(p)
    assert ctl["energy_matched"] is True
    assert ctl["energy_mismatch_fraction"] < 1e-12
    assert ctl["source_total_energy_j"] == pytest.approx(
        ctl["control_total_energy_j"])
    cp = ctl["program"]
    assert cp.mode == "PARALLEL"
    # no alternation: every slot is identical and both windings are live
    assert len(set(cp.slots)) == 1
    for i1, i2 in cp.slots:
        assert i1 > 0.0 and i2 > 0.0


def test_parallel_control_amplitude_is_amplitude_over_root_two():
    p = drive.alternating_program(6, 5.0)
    ctl = drive.matched_energy_control(p, mode="PARALLEL")
    assert ctl["control_amplitude_a"] == pytest.approx(5.0 / math.sqrt(2))


def test_single_channel_control_matches_energy_too():
    p = drive.alternating_program(6, 5.0)
    ctl = drive.matched_energy_control(p, mode="SINGLE")
    assert ctl["control_amplitude_a"] == pytest.approx(5.0)
    assert ctl["energy_matched"] is True
    assert ctl["program"].mode == "SINGLE"


def test_control_has_no_differential_component_but_same_energy():
    from r6 import helix
    p = drive.alternating_program(6, 5.0)
    ctl = drive.matched_energy_control(p)
    for i1, i2 in ctl["program"].slots:
        d = helix.common_differential_decomposition(i1, i2)
        assert d["differential_mode_a"] == pytest.approx(0.0)
    assert ctl["varied"].startswith("temporal structure")


def test_control_preserves_slot_count_duration_and_repetition():
    p = drive.alternating_program(8, 4.0, slot_duration_s=2e-3,
                                  repetition=3)
    cp = drive.matched_energy_control(p)["program"]
    assert cp.n_slots == p.n_slots
    assert cp.slot_duration_s == p.slot_duration_s
    assert cp.repetition == p.repetition


def test_control_may_not_be_the_structure_under_test():
    p = drive.alternating_program(6, 5.0)
    with pytest.raises(DriveError, match="under test"):
        drive.matched_energy_control(p, mode="ALTERNATING_DIFFERENTIAL")


def test_series_is_refused_as_a_control_with_a_reason():
    p = drive.alternating_program(6, 5.0)
    with pytest.raises(DriveError, match="duplicates"):
        drive.matched_energy_control(p, mode="SERIES")


def test_control_states_why_it_is_required_and_its_limitation():
    ctl = drive.matched_energy_control(drive.alternating_program(6, 5.0))
    assert "structure" in ctl["why_required"]
    assert "slew" in ctl["limitation"].lower()
    assert ctl["matched_quantity"] == "resistively dissipated energy"
    assert ctl["evidence_class"] == "SYNTHETIC_MODEL"
    assert ctl["units"]["control_amplitude_a"] == "A"


# --------------------------------------------------------------------
# Claim-language guards
# --------------------------------------------------------------------

def test_module_declares_no_coil_has_been_wound():
    assert "no coil has been wound" in drive.__doc__.lower()


def test_module_uses_no_forbidden_state():
    import pathlib
    src = pathlib.Path(drive.__file__).read_text(encoding="utf-8")
    for state in r6.FORBIDDEN_STATES:
        assert state not in src, f"{state} appears in r6/drive.py"


def test_every_public_result_carries_evidence_class():
    p = drive.alternating_program(4, 2.0)
    results = [
        p.as_record(),
        drive.energy_per_slot(p),
        drive.duty_cycle(p),
        drive.compile_program(p).as_record(),
        drive.matched_energy_control(p),
        drive.DEFAULT_LIMITS.as_record(),
    ]
    for r in results:
        assert r["evidence_class"] == "SYNTHETIC_MODEL"
        assert "units" in r
