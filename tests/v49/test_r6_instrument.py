"""P05 — instrument matrix and Phryll residual boundary.

The tests that matter here are the refusals. A residual registry that
cheerfully accepts a residual on a partially instrumented apparatus
would pass every structural test in this file and still be the exact
error core/07 exists to prevent.
"""

from __future__ import annotations

import pytest

import r6
from r6 import instrument as I


# --- helpers ----------------------------------------------------------

def _first_instrument(channel: str) -> I.Instrument:
    return I.instruments_by_channel()[channel][0]


def _measurements(exclude: tuple[str, ...] = (),
                  unbounded: tuple[str, ...] = ()
                  ) -> tuple[I.ChannelMeasurement, ...]:
    """One bounded measurement per ordinary channel, minus exclusions."""
    out = []
    for ch in r6.ORDINARY_CHANNELS:
        if ch in exclude:
            continue
        ins = _first_instrument(ch)
        out.append(I.ChannelMeasurement(
            channel=ch, instrument_id=ins.id, value=1.0, unit=ins.unit,
            uncertainty=ins.uncertainty, bounded=ch not in unbounded,
            notes="model figure; not bench data"))
    return tuple(out)


def _good_sham() -> I.ShamControl:
    return I.ShamControl(
        control_id="SHAM-01", n_sham_epochs=40, n_live_epochs=40,
        blinded_to_operator=True, randomized_order=True,
        drive_current_verified_zero=True)


def _residual(**kw) -> I.ResidualRecord:
    ms = kw.pop("measurements", None) or _measurements()
    base = dict(record_id="RES-01", observable="collector charge step",
                magnitude=0.0, magnitude_unit="C",
                measurements=ms, sham_control=_good_sham())
    base.update(kw)
    if base["magnitude"] == 0.0:
        base["magnitude"] = 10.0 * I.combined_uncertainty(ms)
    return I.register_residual(**base)


# --- the matrix -------------------------------------------------------

def test_all_eighteen_ordinary_channels_have_an_instrument():
    by_channel = I.instruments_by_channel()
    assert len(r6.ORDINARY_CHANNELS) == 18
    for ch in r6.ORDINARY_CHANNELS:
        assert by_channel[ch], f"no instrument declared for {ch!r}"


def test_instrument_ids_are_unique():
    ids = [i.id for i in I.INSTRUMENT_MATRIX]
    assert len(ids) == len(set(ids))


def test_every_instrument_sits_on_a_declared_ordinary_channel():
    for ins in I.INSTRUMENT_MATRIX:
        assert ins.channel in r6.ORDINARY_CHANNELS


def test_instrument_refuses_an_undeclared_channel():
    with pytest.raises(ValueError, match="not a declared ordinary channel"):
        I.Instrument(
            id="BAD", channel="torsion_field", quantity="q", unit="u",
            range_min=0.0, range_max=1.0, resolution=1e-3,
            uncertainty=1e-2, calibration_id="C",
            calibration_due_epoch=0.0)


def test_instrument_refuses_zero_uncertainty():
    with pytest.raises(ValueError, match="uncertainty must be positive"):
        I.Instrument(
            id="BAD", channel="drive_voltage", quantity="V", unit="V",
            range_min=0.0, range_max=1.0, resolution=1e-3,
            uncertainty=0.0, calibration_id="C",
            calibration_due_epoch=0.0)


def test_the_source_requested_instruments_are_present():
    """E/M/RF to 10 GHz, DC-MHz magnetics, radiation, IR thermal,
    matched oscillators, optical 200-1800 nm, the 52-degree copper cone
    and sound."""
    blob = " ".join(f"{i.id} {i.quantity} {i.notes}"
                    for i in I.INSTRUMENT_MATRIX)
    assert "10 GHz" in blob
    assert "MATCHED PRECISION" in blob
    assert "52-degree copper cone" in blob
    assert "200-1100 nm" in blob and "900-1800 nm" in blob
    by_channel = I.instruments_by_channel()
    assert len(by_channel["magnetic_field"]) >= 3      # single + three axis
    assert len(by_channel["oscillator_phase_and_frequency"]) >= 2
    assert by_channel["radiation"]
    assert by_channel["sound_and_ultrasound"]
    assert any("thermal camera" in i.notes
               for i in by_channel["thermal_state"])


# --- the caduceus / torsion refusal ------------------------------------

def test_caduceus_torsion_sensor_is_uncalibrated_no_standard():
    devices = {d.id: d for d in I.UNCALIBRATED_DEVICES}
    dev = devices["DEV-CADUCEUS-TORSION-01"]
    assert dev.calibration_status == "UNCALIBRATED_NO_STANDARD"
    assert "caduceus" in dev.reason
    assert "no accepted calibration standard" in dev.reason.lower()
    assert "NOT a measurement channel" in dev.reason


def test_caduceus_sensor_is_not_in_the_instrument_matrix():
    assert all("CADUCEUS" not in i.id for i in I.INSTRUMENT_MATRIX)
    with pytest.raises(KeyError):
        I.instrument("DEV-CADUCEUS-TORSION-01")


def test_an_uncalibrated_device_cannot_be_registered_as_an_instrument():
    with pytest.raises(ValueError, match="no accepted calibration"):
        I.Instrument(
            id="BAD-TORSION", channel="magnetic_field",
            quantity="torsion", unit="au", range_min=0.0, range_max=1.0,
            resolution=1e-3, uncertainty=1e-2, calibration_id="none",
            calibration_due_epoch=0.0,
            calibration_status="UNCALIBRATED_NO_STANDARD")


def test_uncalibrated_device_class_holds_only_that_status():
    with pytest.raises(ValueError):
        I.UncalibratedDevice(
            id="X", claimed_quantity="q", reason="r",
            calibration_status="CALIBRATED_TRACEABLE")


# --- coverage ----------------------------------------------------------

def test_coverage_report_is_complete_and_names_nothing_missing():
    cov = I.coverage_report()
    assert cov["complete"] is True
    assert cov["missing"] == ()
    assert set(cov["covered"]) == set(r6.ORDINARY_CHANNELS)
    assert cov["n_channels"] == 18
    assert cov["n_instruments"] == len(I.INSTRUMENT_MATRIX)
    for ch in r6.ORDINARY_CHANNELS:
        assert cov["instruments_per_channel"][ch]


def test_coverage_report_lists_uncalibrated_devices_separately():
    cov = I.coverage_report()
    assert "DEV-CADUCEUS-TORSION-01" in cov["uncalibrated_devices"]
    for ids in cov["instruments_per_channel"].values():
        assert "DEV-CADUCEUS-TORSION-01" not in ids


def test_coverage_report_says_the_specs_are_not_bench_data():
    assert "not bench data" in I.coverage_report()["note"]


# --- measurements -------------------------------------------------------

def test_channel_measurement_rejects_a_mismatched_instrument():
    with pytest.raises(ValueError, match="registered on channel"):
        I.ChannelMeasurement(
            channel="radiation", instrument_id="INS-T-IR-01",
            value=1.0, unit="K", uncertainty=1.0)


def test_combined_uncertainty_is_root_sum_square():
    ms = _measurements()
    u = I.combined_uncertainty(ms)
    assert u > 0
    assert u >= max(m.uncertainty for m in ms)


# --- registration refusals ----------------------------------------------

def test_residual_refused_when_a_channel_is_unmeasured_and_names_it():
    with pytest.raises(I.RefusedError) as exc:
        _residual(measurements=_measurements(exclude=("radiation",)))
    msg = str(exc.value)
    assert "radiation" in msg
    assert "unmeasured or unbounded" in msg


def test_residual_refusal_names_every_missing_channel():
    missing = ("radiation", "optical", "force_and_torque")
    with pytest.raises(I.RefusedError) as exc:
        _residual(measurements=_measurements(exclude=missing))
    msg = str(exc.value)
    for ch in missing:
        assert ch in msg


def test_residual_refused_when_a_channel_is_present_but_unbounded():
    with pytest.raises(I.RefusedError) as exc:
        _residual(measurements=_measurements(unbounded=("optical",)))
    msg = str(exc.value)
    assert "optical" in msg
    assert "did not bound" in msg


def test_residual_refused_without_a_sham_control():
    with pytest.raises(I.RefusedError, match="no sham-drive control"):
        _residual(sham_control=None)


def test_residual_refused_when_the_sham_control_is_unblinded():
    sham = I.ShamControl(
        control_id="SHAM-BAD", n_sham_epochs=40, n_live_epochs=40,
        blinded_to_operator=False, randomized_order=True,
        drive_current_verified_zero=True)
    with pytest.raises(I.RefusedError, match="not blinded"):
        _residual(sham_control=sham)


def test_residual_refused_when_sham_order_is_not_randomized():
    sham = I.ShamControl(
        control_id="SHAM-BAD", n_sham_epochs=40, n_live_epochs=40,
        blinded_to_operator=True, randomized_order=False,
        drive_current_verified_zero=True)
    with pytest.raises(I.RefusedError, match="not randomized"):
        _residual(sham_control=sham)


def test_residual_refused_when_sham_current_was_never_verified():
    sham = I.ShamControl(
        control_id="SHAM-BAD", n_sham_epochs=40, n_live_epochs=40,
        blinded_to_operator=True, randomized_order=True,
        drive_current_verified_zero=False)
    with pytest.raises(I.RefusedError, match="zero drive current"):
        _residual(sham_control=sham)


def test_residual_refused_inside_the_combined_uncertainty():
    ms = _measurements()
    u = I.combined_uncertainty(ms)
    with pytest.raises(I.RefusedError) as exc:
        I.register_residual(
            record_id="RES-SMALL", observable="collector charge step",
            magnitude=0.5 * u, magnitude_unit="C", measurements=ms,
            sham_control=_good_sham())
    assert "does not exceed" in str(exc.value)
    assert "null result is a result" in str(exc.value)


def test_residual_refused_when_an_instrument_is_not_in_the_matrix():
    # A measurement citing an instrument outside the matrix cannot even
    # be constructed, so it can never reach register_residual().
    with pytest.raises(KeyError, match="no instrument"):
        I.ChannelMeasurement(channel="optical", instrument_id="NOPE",
                             value=1.0, unit="u", uncertainty=1.0)
    assert len(_measurements()) == 18


# --- successful registration ---------------------------------------------

def test_registered_residual_sits_at_unexplained_instrument_residual():
    rec = _residual()
    assert rec.evidence_class == "UNEXPLAINED_INSTRUMENT_RESIDUAL"
    assert rec.evidence_class in r6.PHRYLL_CLASSES
    assert rec.missing_channels() == ()
    assert rec.significant() is True
    assert any("not yet understood" in n for n in rec.notes)
    assert any("Not bench data" in n for n in rec.notes)


def test_residual_record_serializes_with_its_ceiling():
    d = _residual().as_record()
    assert d["evidence_class"] == "UNEXPLAINED_INSTRUMENT_RESIDUAL"
    assert d["missing_channels"] == []
    assert "CANDIDATE_NEW_MECHANISM is the top" in d["ceiling"]
    assert "not a substance" in d["ceiling"]


# --- the ladder ------------------------------------------------------------

def test_evidence_class_must_be_on_the_ladder():
    with pytest.raises(ValueError, match="not on the ladder"):
        I.ResidualRecord(record_id="R", observable="o",
                         evidence_class="PHRYLL_CONFIRMED")


def test_promotion_to_operational_hypothesis_requires_a_definition():
    seed = I.seed_record("R-SEED", "collector charge step")
    assert seed.evidence_class == "SOURCE_CLAIM"
    with pytest.raises(I.RefusedError, match="operational definition"):
        I.promote(seed, "OPERATIONAL_HYPOTHESIS")
    ok = I.promote(seed, "OPERATIONAL_HYPOTHESIS",
                   operational_definition=(
                       "charge on INS-C-CONE52-01 during drive epochs, "
                       "null if the sham/live contrast is inside 3 sigma"))
    assert ok.evidence_class == "OPERATIONAL_HYPOTHESIS"


def test_promotion_to_ordinary_channel_result_requires_all_channels():
    hyp = I.ResidualRecord(
        record_id="R", observable="o",
        evidence_class="OPERATIONAL_HYPOTHESIS",
        measurements=_measurements(exclude=("chemistry_material_change",)),
        sham_control=_good_sham())
    with pytest.raises(I.RefusedError) as exc:
        I.promote(hyp, "ORDINARY_CHANNEL_RESULT")
    assert "chemistry_material_change" in str(exc.value)


def test_promotion_to_ordinary_channel_result_requires_a_sham_control():
    hyp = I.ResidualRecord(
        record_id="R", observable="o",
        evidence_class="OPERATIONAL_HYPOTHESIS",
        measurements=_measurements(), sham_control=None)
    with pytest.raises(I.RefusedError, match="sham-drive control"):
        I.promote(hyp, "ORDINARY_CHANNEL_RESULT")
    ok = I.promote(
        I.ResidualRecord(record_id="R", observable="o",
                         evidence_class="OPERATIONAL_HYPOTHESIS",
                         measurements=_measurements(),
                         sham_control=_good_sham()),
        "ORDINARY_CHANNEL_RESULT")
    assert ok.evidence_class == "ORDINARY_CHANNEL_RESULT"


def test_promotion_to_residual_requires_clearing_the_noise_floor():
    ms = _measurements()
    quiet = I.ResidualRecord(
        record_id="R", observable="o",
        evidence_class="ORDINARY_CHANNEL_RESULT",
        magnitude=0.1 * I.combined_uncertainty(ms), magnitude_unit="C",
        combined_uncertainty=I.combined_uncertainty(ms),
        measurements=ms, sham_control=_good_sham())
    with pytest.raises(I.RefusedError, match="noise floor"):
        I.promote(quiet, "UNEXPLAINED_INSTRUMENT_RESIDUAL")


def test_promotion_to_replicated_anomaly_requires_an_independent_group():
    rec = _residual()
    with pytest.raises(I.RefusedError, match="no replication record"):
        I.promote(rec, "REPLICATED_ANOMALY")

    same_group = I.Replication(
        replication_id="REP-1", group=rec.group,
        apparatus_id="APP-1", blinded=True, result_consistent=True)
    with pytest.raises(I.RefusedError, match="same group"):
        I.promote(rec, "REPLICATED_ANOMALY", replication=same_group)

    unblinded = I.Replication(
        replication_id="REP-2", group="OTHER_LAB",
        apparatus_id="APP-2", blinded=False, result_consistent=True)
    with pytest.raises(I.RefusedError, match="not blinded"):
        I.promote(rec, "REPLICATED_ANOMALY", replication=unblinded)

    inconsistent = I.Replication(
        replication_id="REP-3", group="OTHER_LAB",
        apparatus_id="APP-2", blinded=True, result_consistent=False)
    with pytest.raises(I.RefusedError, match="not consistent"):
        I.promote(rec, "REPLICATED_ANOMALY", replication=inconsistent)

    good = I.Replication(
        replication_id="REP-4", group="OTHER_LAB",
        apparatus_id="APP-2", blinded=True, result_consistent=True)
    ok = I.promote(rec, "REPLICATED_ANOMALY", replication=good)
    assert ok.evidence_class == "REPLICATED_ANOMALY"
    assert len(ok.independent_replications()) == 1


def test_promotion_to_candidate_requires_mechanism_and_prediction():
    rec = I.promote(
        _residual(), "REPLICATED_ANOMALY",
        replication=I.Replication(
            replication_id="REP-4", group="OTHER_LAB",
            apparatus_id="APP-2", blinded=True, result_consistent=True))

    with pytest.raises(I.RefusedError, match="proposed mechanism"):
        I.promote(rec, "CANDIDATE_NEW_MECHANISM")

    with pytest.raises(I.RefusedError, match="falsifiable prediction"):
        I.promote(rec, "CANDIDATE_NEW_MECHANISM",
                  proposed_mechanism="an unmodeled surface leakage path")

    top = I.promote(
        rec, "CANDIDATE_NEW_MECHANISM",
        proposed_mechanism="an unmodeled surface leakage path",
        falsifiable_prediction=(
            "the effect must scale with relative humidity and vanish "
            "below 10 %RH; if it does not, the mechanism is dead"))
    assert top.evidence_class == "CANDIDATE_NEW_MECHANISM"
    assert any("does not mean anything has been detected" in n
               for n in top.notes)


def test_the_ladder_cannot_be_skipped():
    seed = I.seed_record("R-SEED", "o")
    with pytest.raises(I.RefusedError, match="cannot jump"):
        I.promote(seed, "CANDIDATE_NEW_MECHANISM",
                  proposed_mechanism="m", falsifiable_prediction="p")


def test_promotion_never_moves_down_or_sideways():
    rec = _residual()
    with pytest.raises(I.RefusedError, match="already at"):
        I.promote(rec, "ORDINARY_CHANNEL_RESULT")
    with pytest.raises(I.RefusedError, match="already at"):
        I.promote(rec, "UNEXPLAINED_INSTRUMENT_RESIDUAL")


def test_there_is_no_state_above_candidate_new_mechanism():
    assert r6.PHRYLL_CLASSES[-1] == "CANDIDATE_NEW_MECHANISM"
    top = I.promote(
        I.promote(_residual(), "REPLICATED_ANOMALY",
                  replication=I.Replication(
                      replication_id="REP", group="OTHER_LAB",
                      apparatus_id="APP-2", blinded=True,
                      result_consistent=True)),
        "CANDIDATE_NEW_MECHANISM",
        proposed_mechanism="m", falsifiable_prediction="p")
    for target in ("CONFIRMED_NEW_MECHANISM", "NEW_PHYSICS",
                   "MECHANISM_ESTABLISHED"):
        with pytest.raises(I.RefusedError, match="not on the ladder"):
            I.promote(top, target)


def test_forbidden_states_are_refused_by_name():
    top = I.seed_record("R", "o")
    for bad in r6.FORBIDDEN_STATES:
        with pytest.raises(I.RefusedError, match="FORBIDDEN_STATES"):
            I.promote(top, bad)


def test_ladder_ceiling_is_inspectable():
    ceiling = I.ladder_ceiling()
    assert ceiling["ladder"] == r6.PHRYLL_CLASSES
    assert ceiling["top"] == "CANDIDATE_NEW_MECHANISM"
    assert "no detection state" in ceiling["nothing_above"]
    assert ceiling["forbidden_collapse"] == "RESIDUAL_IS_ONTOLOGY"
    assert set(ceiling["requirements"]) == set(r6.PHRYLL_CLASSES)


# --- the sham protocol -----------------------------------------------------

def test_sham_drive_protocol_is_blinded_and_randomized():
    p = I.sham_drive_protocol()
    assert "blinded" in p["blinding"].lower()
    assert "randomized" in p["randomization"].lower()
    assert len(p["steps"]) >= 5
    joined = " ".join(p["steps"]).lower()
    assert "identical" in p["principle"].lower()
    assert "no drive current" in p["principle"].lower()
    assert "seal" in joined
    assert "bench data" in p["note"]


def test_good_sham_control_has_no_deficiencies():
    assert _good_sham().deficiencies() == ()
