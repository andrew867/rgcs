"""P14 — the two-channel rotating field, interrupted: modelled, never run.

The three rotation senses are exercised with numbers, including the
degenerate (linear) case that the whole experiment leans on as its
control. The one exact preregistered prediction — a round-trip phase of
exactly 1/7 turn for the N=7 scalar geometry — is checked as a
``Fraction`` equality and not as a float comparison. The cutoff sweep is
required to cover a full turn with every observable blocked, all eight
controls are required before any result, and the bench claim, the
unfrozen scoring and the missing-control cases are all required to raise.
"""

from __future__ import annotations

import math
from fractions import Fraction

import pytest

from r11 import rotfield as RF
from r11.phasealpha import Quantity, Unit


# --- (1) rotation sense: CW, CCW and the degenerate linear case ----------

def test_balanced_quadrature_drive_rotates_counterclockwise():
    """ax == ay with a quarter-turn lag is the (cos, sin) circular drive."""
    sense = RF.rotation_sense(1, 1, Fraction(1, 4))
    assert sense is RF.RotationSense.COUNTERCLOCKWISE
    assert sense.sign == 1
    assert sense.rotates


def test_three_quarter_turn_lag_rotates_clockwise():
    sense = RF.rotation_sense(1, 1, Fraction(3, 4))
    assert sense is RF.RotationSense.CLOCKWISE
    assert sense.sign == -1
    assert sense.rotates


def test_equal_phase_channels_are_linear_and_degenerate():
    """p = 0 puts both channels in phase: the tip runs along a line."""
    for phase in (Fraction(0), Fraction(1, 2), Fraction(1), Fraction(3, 2)):
        sense = RF.rotation_sense(1, 1, phase)
        assert sense is RF.RotationSense.DEGENERATE, phase
        assert sense.sign == 0
        assert not sense.rotates
        assert RF.polarization(1, 1, phase) is RF.Polarization.LINEAR


def test_one_channel_only_is_degenerate():
    """The ONE_CHANNEL_ONLY control: kill a channel and nothing rotates."""
    assert RF.rotation_sense(1, 0, Fraction(1, 4)) \
        is RF.RotationSense.DEGENERATE
    assert RF.rotation_sense(0, 1, Fraction(1, 4)) \
        is RF.RotationSense.DEGENERATE
    assert RF.polarization(1, 0, Fraction(1, 4)) is RF.Polarization.LINEAR


def test_amplitude_imbalance_is_elliptical_but_still_rotates():
    assert RF.polarization(1, 1, Fraction(1, 4)) is RF.Polarization.CIRCULAR
    assert RF.polarization(Fraction(1), Fraction(2), Fraction(1, 4)) \
        is RF.Polarization.ELLIPTICAL
    assert RF.rotation_sense(Fraction(1), Fraction(2), Fraction(1, 4)) \
        is RF.RotationSense.COUNTERCLOCKWISE
    # balanced channels off quadrature are elliptical too
    assert RF.polarization(1, 1, Fraction(1, 8)) is RF.Polarization.ELLIPTICAL


def test_negative_channel_phase_reverses_the_sense():
    forward = RF.rotation_sense(1, 1, Fraction(1, 4))
    back = RF.rotation_sense(1, 1, Fraction(-1, 4))
    assert forward is RF.RotationSense.COUNTERCLOCKWISE
    assert back is RF.RotationSense.CLOCKWISE
    assert forward.sign == -back.sign


def test_reversed_phase_is_an_involution_and_reverses_the_sense():
    p = Fraction(1, 4)
    assert RF.reversed_phase(RF.reversed_phase(p)) == p
    assert RF.rotation_sense(1, 1, RF.reversed_phase(p)).sign \
        == -RF.rotation_sense(1, 1, p).sign
    # a linear drive has no sense to reverse
    assert RF.rotation_sense(1, 1, RF.reversed_phase(Fraction(0))) \
        is RF.RotationSense.DEGENERATE


def test_enclosed_area_sign_agrees_with_the_exact_sense():
    for phase in (Fraction(1, 4), Fraction(1, 3), Fraction(3, 4),
                  Fraction(5, 8)):
        area = RF.enclosed_area(1, 1, phase)
        assert math.copysign(1.0, area) == RF.sense_sign(1, 1, phase)
    assert RF.enclosed_area(1, 1, Fraction(0)) == pytest.approx(0.0)


def test_float_phase_is_refused():
    """A sign decided on a mantissa bit is not a decided sign."""
    with pytest.raises(RF.RotFieldError):
        RF.rotation_sense(1, 1, 0.25)
    with pytest.raises(RF.RotFieldError):
        RF.rotation_sense(1.0, 1, Fraction(1, 4))


def test_negative_channel_amplitude_is_refused():
    with pytest.raises(RF.RotFieldError):
        RF.rotation_sense(-1, 1, Fraction(1, 4))


# --- (2) the drive: units, waveform, and an independent sense check ------

def test_drive_rejects_an_angular_frequency_as_a_frequency():
    """omega and f differ by 2*pi, and the drive will not take one for the other."""
    with pytest.raises(RF.RotFieldError):
        RF.RotatingDrive(f_drive=Quantity(4096.0, Unit.RADIANS_PER_SECOND))
    with pytest.raises(RF.RotFieldError):
        RF.RotatingDrive(f_drive=4096.0)


def test_drive_omega_is_two_pi_f():
    drive = RF.CIRCULAR_DRIVE
    assert drive.omega().unit is Unit.RADIANS_PER_SECOND
    assert drive.omega().value == pytest.approx(2 * math.pi * 4096.0)


def test_quarter_turn_lag_reproduces_the_sine_channel_exactly():
    """By = B0*ay*cos(2*pi*(f t - 1/4)) is B0*ay*sin(2*pi*f t)."""
    drive = RF.CIRCULAR_DRIVE
    for k in range(9):
        t = k * drive.period_s() / 8.0
        bx, by = drive.field(t)
        turns = 4096.0 * t
        assert bx == pytest.approx(math.cos(2 * math.pi * turns), abs=1e-12)
        assert by == pytest.approx(math.sin(2 * math.pi * turns), abs=1e-12)


def test_sampled_trajectory_agrees_with_the_exact_rational_sense():
    """Two independent routes to the sense must not disagree."""
    cases = (
        (Fraction(1, 4), RF.RotationSense.COUNTERCLOCKWISE),
        (Fraction(3, 4), RF.RotationSense.CLOCKWISE),
        (Fraction(0), RF.RotationSense.DEGENERATE),
        (Fraction(1, 2), RF.RotationSense.DEGENERATE),
        (Fraction(1, 8), RF.RotationSense.COUNTERCLOCKWISE),
    )
    for phase, expected in cases:
        drive = RF.RotatingDrive(phase=phase)
        report = RF.sense_consistency(drive)
        assert report["agree"], report
        assert drive.sense is expected, phase
        assert RF.numeric_sense(drive) is expected, phase


def test_reversed_drive_reverses_the_sampled_sense_too():
    drive = RF.CIRCULAR_DRIVE
    flipped = drive.reversed()
    assert RF.numeric_sense(flipped).sign == -RF.numeric_sense(drive).sign
    assert flipped.polarization is RF.Polarization.CIRCULAR


def test_linear_control_drive_is_degenerate():
    assert RF.LINEAR_CONTROL_DRIVE.sense is RF.RotationSense.DEGENERATE
    assert RF.LINEAR_CONTROL_DRIVE.polarization is RF.Polarization.LINEAR
    assert RF.LINEAR_CONTROL_DRIVE.as_dict()["rotation_sense_sign"] == 0


def test_a_drive_with_both_channels_dead_is_refused():
    with pytest.raises(RF.RotFieldError):
        RF.RotatingDrive(ax=Fraction(0), ay=Fraction(0))


# --- (3) the exact preregistered round-trip phase -------------------------

def test_n7_roundtrip_phase_is_exactly_one_seventh_of_a_turn():
    """The headline: Fraction equality, not float approximation."""
    turns = RF.roundtrip_phase_turns(6310, 4096, 7)
    assert isinstance(turns, Fraction)
    assert turns == Fraction(1, 7)
    assert turns.numerator == 1 and turns.denominator == 7


def test_n7_roundtrip_phase_in_degrees_is_exactly_360_over_7():
    degrees = RF.roundtrip_phase_degrees(6310, 4096, 7)
    assert isinstance(degrees, Fraction)
    assert degrees == Fraction(360, 7)
    assert float(degrees) == pytest.approx(51.428571428571, abs=1e-9)


def test_the_sound_speed_cancels_out_of_the_roundtrip_phase():
    """The identity holds for any v, which is what makes it geometric."""
    for v in (6310, 5000, Fraction(1234, 7), 1):
        assert RF.roundtrip_phase_turns(v, 4096, 7) == Fraction(1, 7)


def test_roundtrip_phase_is_one_over_n_for_every_n():
    for n in range(1, 13):
        assert RF.roundtrip_phase_turns(6310, 4096, n) == Fraction(1, n)


def test_segment_length_and_roundtrip_time_are_exact():
    length = RF.segment_length_m(6310, 4096, 7)
    assert length == Fraction(6310, 2 * 7 * 4096)
    assert RF.roundtrip_time_s(6310, 4096, 7) == Fraction(1, 7 * 4096)


def test_roundtrip_phase_refuses_floats_and_bad_geometry():
    with pytest.raises(RF.RotFieldError):
        RF.roundtrip_phase_turns(6310.0, 4096, 7)
    with pytest.raises(RF.RotFieldError):
        RF.roundtrip_phase_turns(6310, 4096, 0)
    with pytest.raises(RF.RotFieldError):
        RF.roundtrip_phase_turns(0, 4096, 7)


def test_roundtrip_prediction_is_reported_as_an_exact_identity():
    pred = RF.roundtrip_phase_prediction()
    assert pred["claim_class"] == "EXACT_IDENTITY"
    assert pred["roundtrip_phase_turns_exact"] == "1/7"
    assert pred["roundtrip_phase_degrees_exact"] == "360/7"
    assert pred["roundtrip_phase_turns_is_one_over_n"] is True
    assert pred["sound_speed_cancels"] is True
    assert pred["measured_here"] == "nothing"


# --- (4) the cutoff sweep, every observable blocked -----------------------

def test_cutoff_sweep_covers_a_full_turn_in_exact_rationals():
    sweep = RF.cutoff_sweep(12)
    assert sweep["n_points"] == 12
    assert len(sweep["points"]) == 12
    assert sweep["covers_full_turn"] is True
    assert sweep["step_turns_exact"] == "1/12"
    phases = [Fraction(p["cutoff_phase_turns_exact"])
              for p in sweep["points"]]
    assert phases[0] == 0
    assert phases == sorted(phases)
    assert phases[-1] == Fraction(11, 12)
    assert sum(phases, Fraction(0)) == Fraction(11, 2)


def test_cutoff_sweep_degrees_run_over_the_whole_circle():
    sweep = RF.cutoff_sweep(8)
    degrees = [p["cutoff_phase_degrees"] for p in sweep["points"]]
    assert degrees[0] == 0.0
    assert degrees[-1] == pytest.approx(315.0)
    assert all(0.0 <= d < 360.0 for d in degrees)


def test_every_observable_at_every_sweep_point_is_blocked():
    sweep = RF.cutoff_sweep(5)
    assert sweep["observables_per_point"] == len(RF.Observable)
    assert sweep["all_observables_blocked"] is True
    assert sweep["any_observable_recorded"] is False
    for point in sweep["points"]:
        assert len(point["observables"]) == len(RF.Observable)
        for obs in point["observables"]:
            assert obs["status"] == "BLOCKED_MISSING_DATA"
            assert obs["value"] is None
            assert obs["why_it_matters"]


def test_the_required_observable_list_is_the_declared_one():
    names = {o["observable"] for o in
             (r.as_dict() for r in RF.REQUIRED_OBSERVABLES)}
    for required in ("COIL_CURRENT", "COIL_VOLTAGE", "ELECTRODE_VOLTAGE",
                     "ELECTRODE_CURRENT", "BVD_PARAMETERS_BEFORE",
                     "BVD_PARAMETERS_AFTER", "RINGDOWN_AMPLITUDE",
                     "RINGDOWN_PHASE", "MODAL_ENERGY_FRACTIONS",
                     "SIDEBAND_SPECTRUM", "QUALITY_FACTOR", "TEMPERATURE",
                     "ACCELEROMETER", "EXTERNAL_QTF"):
        assert required in names


def test_an_observable_cannot_be_given_a_value():
    """There is no bench, so no record here may carry a reading."""
    with pytest.raises(RF.RotFieldError):
        RF.ObservableRecord(RF.Observable.QUALITY_FACTOR, "1", "why",
                            value=12000.0)
    with pytest.raises(RF.RotFieldError):
        RF.ObservableRecord(RF.Observable.QUALITY_FACTOR, "1", "why",
                            status="BENCH_MEASUREMENT")


def test_cutoff_sweep_needs_at_least_two_points():
    with pytest.raises(RF.RotFieldError):
        RF.cutoff_sweep(1)


# --- (5) the eight controls ----------------------------------------------

def test_there_are_exactly_eight_declared_controls():
    assert len(RF.REQUIRED_CONTROLS) == 8
    assert len(set(RF.REQUIRED_CONTROLS)) == 8
    assert set(RF.CONTROL_REASONS) == set(RF.REQUIRED_CONTROLS)
    assert all(RF.CONTROL_REASONS[c] for c in RF.REQUIRED_CONTROLS)


def test_all_eight_controls_declared_passes():
    got = RF.refuse_result_without_controls(RF.REQUIRED_CONTROLS)
    assert tuple(got) == RF.REQUIRED_CONTROLS
    # names as strings are accepted too
    names = [c.value for c in RF.Control]
    assert RF.refuse_result_without_controls(names) == RF.REQUIRED_CONTROLS


def test_any_single_missing_control_refuses_the_result():
    for omitted in RF.REQUIRED_CONTROLS:
        declared = [c for c in RF.REQUIRED_CONTROLS if c is not omitted]
        assert RF.missing_controls(declared) == (omitted,)
        with pytest.raises(RF.RotFieldError) as exc:
            RF.refuse_result_without_controls(declared)
        assert omitted.value in str(exc.value)


def test_no_controls_at_all_refuses_and_names_all_eight():
    with pytest.raises(RF.RotFieldError) as exc:
        RF.refuse_result_without_controls(())
    message = str(exc.value)
    for control in RF.REQUIRED_CONTROLS:
        assert control.value in message


def test_an_undeclared_control_name_is_refused():
    with pytest.raises(RF.RotFieldError):
        RF.refuse_result_without_controls(["NOT_A_CONTROL"])


# --- (6) the refusals ------------------------------------------------------

def test_refuse_bench_claim_always_raises():
    with pytest.raises(RF.RotFieldError) as exc:
        RF.refuse_bench_claim()
    assert "BLOCKED_MISSING_DATA" in str(exc.value)
    with pytest.raises(RF.RotFieldError):
        RF.refuse_bench_claim("Q dropped after the cut",
                              RF.Observable.QUALITY_FACTOR)


def test_refuse_unfrozen_scoring_always_raises():
    with pytest.raises(RF.RotFieldError):
        RF.refuse_unfrozen_scoring()
    with pytest.raises(RF.RotFieldError) as exc:
        RF.refuse_unfrozen_scoring(RF.FROZEN_PREDICTIONS, observed=[1, 2, 3])
    # even the correct hash does not buy a score: there is nothing to score
    assert RF.PREREGISTRATION_HASH in str(exc.value)


# --- (7) preregistration ---------------------------------------------------

def test_the_prediction_set_is_hashed_and_the_hash_is_stable():
    assert RF.PREREGISTRATION_HASH == RF.FROZEN_PREDICTIONS.prereg_hash
    assert len(RF.PREREGISTRATION_HASH) == 64
    assert RF.FROZEN_PREDICTIONS.prereg_hash \
        == RF.FROZEN_PREDICTIONS.prereg_hash


def test_changing_any_prediction_changes_the_hash():
    original = RF.FROZEN_PREDICTIONS
    amended = RF.PredictionSet(
        original.set_id,
        original.predictions[:-1] + (
            RF.Prediction("P_ADDED_AFTERWARDS",
                          "a statement written after the fact",
                          "scored however it happens to come out"),),
    )
    assert amended.prereg_hash != original.prereg_hash


def test_a_prediction_set_needs_predictions_and_unique_ids():
    with pytest.raises(RF.RotFieldError):
        RF.PredictionSet("EMPTY", ())
    duplicate = RF.FROZEN_PREDICTIONS.predictions[0]
    with pytest.raises(RF.RotFieldError):
        RF.PredictionSet("DUPES", (duplicate, duplicate))


def test_a_prediction_needs_a_declared_claim_class_and_a_criterion():
    with pytest.raises(RF.RotFieldError):
        RF.Prediction("P", "statement", "criterion", claim_class="VIBES")
    with pytest.raises(RF.RotFieldError):
        RF.Prediction("P", "statement", "   ")


def test_the_exact_identity_is_in_the_frozen_set():
    prereg = RF.preregistration()
    ids = {p["prediction_id"]: p for p in prereg["predictions"]}
    assert "P_ROUNDTRIP_PHASE" in ids
    assert ids["P_ROUNDTRIP_PHASE"]["claim_class"] == "EXACT_IDENTITY"
    assert prereg["outcome"] == "AWAITING_OUTCOME"
    assert prereg["outcomes_available_here"] is False
    assert prereg["frozen_before_any_comparison"] is True


# --- (8) the report --------------------------------------------------------

def test_report_carries_the_verdict_and_the_disclaimers():
    report = RF.rotfield_report()
    assert report["verdict"] == "ROTATING_FIELD_EXPERIMENT_PREREGISTERED_NOT_RUN"
    assert RF.VERDICT == "ROTATING_FIELD_EXPERIMENT_PREREGISTERED_NOT_RUN"
    assert report["measured_here"] == "nothing"
    assert report["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert report["claim_class"] in RF.CLAIM_CLASSES
    assert report["claim_class"] == "PROSPECTIVE_PREDICTION"
    assert report["what_this_does_not_say"]
    assert report["n_controls_required"] == 8
    assert report["controls_run"] == 0
    assert report["cutoff_sweep"]["all_observables_blocked"] is True
    assert report["cutoff_sweep"]["any_observable_recorded"] is False
    assert report["exact_prediction"]["claim_class"] == "EXACT_IDENTITY"
    assert report["preregistration"]["prereg_hash"] == RF.PREREGISTRATION_HASH


def test_the_declared_claim_classes_are_the_shared_nine():
    assert RF.CLAIM_CLASSES == (
        "EXACT_IDENTITY", "SOURCE_ESTABLISHED_PHYSICS",
        "REPOSITORY_COMPUTATIONAL_RESULT", "ENGINEERING_CANDIDATE",
        "RETROSPECTIVE_NUMERIC_MATCH", "PROSPECTIVE_PREDICTION",
        "BENCH_MEASUREMENT", "UNSUPPORTED", "BLOCKED_MISSING_DATA")
