"""P11 — the detector matrix: every transducer has a sensitivity domain."""

from __future__ import annotations

import pytest

from r11 import detectors as D


# --- every capability states both halves of its domain -------------------

def test_every_detector_kind_has_a_capability():
    for kind in D.DetectorKind:
        cap = D.capability(kind)
        assert cap.kind is kind
        assert cap.measurand
        assert cap.mechanism
        assert cap.status == "MODEL_ONLY"
        assert cap.measured_here == "nothing"


def test_every_capability_has_a_non_empty_couples_to_and_cannot_detect():
    for kind in D.DetectorKind:
        cap = D.capability(kind)
        assert cap.couples_to, f"{kind.value} transduces nothing"
        assert cap.cannot_detect, (
            f"{kind.value} claims to reach every observable; the honest "
            f"half of the domain is missing")
        assert not (cap.couples_to & cap.cannot_detect)
        assert cap.couples_to | cap.cannot_detect == set(D.Observable)


def test_every_capability_declares_a_band_and_a_floor():
    for kind in D.DetectorKind:
        cap = D.capability(kind)
        assert cap.f_max_hz > cap.f_min_hz >= 0.0
        assert cap.amplitude_floor > 0.0
        assert cap.amplitude_floor_units


def test_an_empty_cannot_detect_is_refused_at_construction():
    with pytest.raises(D.DetectorError):
        D.DetectorCapability(
            kind=D.DetectorKind.CCD,
            measurand="everything",
            mechanism="unspecified",
            frequency_range_hz=(1.0, 10.0),
            amplitude_floor=1.0,
            amplitude_floor_units="arb",
            couples_to=frozenset(D.Observable),
            cannot_detect=frozenset(),
        )


def test_an_unclassified_observable_is_refused_at_construction():
    with pytest.raises(D.DetectorError):
        D.DetectorCapability(
            kind=D.DetectorKind.HALL,
            measurand="magnetic flux density",
            mechanism="Lorentz deflection",
            frequency_range_hz=(0.0, 1e6),
            amplitude_floor=1e-6,
            amplitude_floor_units="T",
            couples_to=frozenset({D.Observable.MAGNETIC_FIELD}),
            cannot_detect=frozenset({D.Observable.PHONON}),
        )


# --- can_detect ----------------------------------------------------------

def test_a_ccd_does_not_detect_phonons():
    assert D.can_detect(D.DetectorKind.CCD, D.Observable.PHONON) is False
    assert D.Observable.PHONON in D.capability(
        D.DetectorKind.CCD).cannot_detect


def test_a_piezoelectric_element_detects_an_acoustic_field():
    assert D.can_detect(D.DetectorKind.PIEZOELECTRIC,
                        D.Observable.ACOUSTIC) is True
    assert D.can_detect(D.DetectorKind.PIEZOELECTRIC,
                        D.Observable.STRAIN) is True


def test_a_hall_element_detects_a_magnetic_field_and_nothing_mechanical():
    assert D.can_detect(D.DetectorKind.HALL,
                        D.Observable.MAGNETIC_FIELD) is True
    assert D.can_detect(D.DetectorKind.HALL, D.Observable.ACOUSTIC) is False
    assert D.can_detect(D.DetectorKind.HALL, D.Observable.STRAIN) is False
    assert D.can_detect(D.DetectorKind.HALL,
                        D.Observable.OPTICAL_INTENSITY) is False


def test_an_optical_detector_reaches_intensity_phase_and_displacement():
    for obs in (D.Observable.OPTICAL_INTENSITY, D.Observable.OPTICAL_PHASE,
                D.Observable.DISPLACEMENT):
        assert D.can_detect(D.DetectorKind.OPTICAL, obs) is True
    assert D.can_detect(D.DetectorKind.OPTICAL,
                        D.Observable.MAGNETIC_FIELD) is False


def test_no_detector_in_the_matrix_couples_to_an_individual_phonon():
    for kind in D.DetectorKind:
        assert D.can_detect(kind, D.Observable.PHONON) is False


def test_can_detect_refuses_an_untyped_observable():
    with pytest.raises(D.DetectorError):
        D.can_detect(D.DetectorKind.CCD, "phonon")
    with pytest.raises(D.DetectorError):
        D.can_detect("ccd", D.Observable.PHONON)


# --- the load-bearing refusal -------------------------------------------

def test_refuse_ccd_phonon_claim_always_raises():
    with pytest.raises(D.DetectorError):
        D.refuse_ccd_phonon_claim()
    for exposure in (1e-3, 1.0, 60.0, 3600.0):
        with pytest.raises(D.DetectorError):
            D.refuse_ccd_phonon_claim("a long exposure integrates phonons",
                                      exposure_s=exposure)


def test_the_ccd_refusal_says_why_integration_does_not_help():
    with pytest.raises(D.DetectorError) as exc:
        D.refuse_ccd_phonon_claim()
    msg = str(exc.value)
    assert "TIME INTEGRAL" in msg
    assert "TIME-AVERAGED OPTICAL" in msg
    assert "frame rate" in msg
    assert D.DEFAULT_VERDICT in msg


# --- the general out-of-domain guard -------------------------------------

@pytest.mark.parametrize("kind,observable", [
    (D.DetectorKind.CCD, D.Observable.PHONON),
    (D.DetectorKind.HALL, D.Observable.ACOUSTIC),
    (D.DetectorKind.CCD, D.Observable.MAGNETIC_FIELD),
    (D.DetectorKind.PIEZOELECTRIC, D.Observable.OPTICAL_INTENSITY),
    (D.DetectorKind.OPTICAL, D.Observable.MAGNETIC_FIELD),
    (D.DetectorKind.CAPACITIVE, D.Observable.PHONON),
])
def test_refuse_out_of_domain_fires_outside_the_domain(kind, observable):
    with pytest.raises(D.DetectorError):
        D.refuse_out_of_domain(kind, observable)


@pytest.mark.parametrize("kind,observable", [
    (D.DetectorKind.PIEZOELECTRIC, D.Observable.ACOUSTIC),
    (D.DetectorKind.PIEZOELECTRIC, D.Observable.STRAIN),
    (D.DetectorKind.HALL, D.Observable.MAGNETIC_FIELD),
    (D.DetectorKind.CAPACITIVE, D.Observable.DISPLACEMENT),
    (D.DetectorKind.OPTICAL, D.Observable.DISPLACEMENT),
    (D.DetectorKind.CCD, D.Observable.OPTICAL_INTENSITY),
])
def test_refuse_out_of_domain_passes_a_legitimate_pairing(kind, observable):
    assert D.refuse_out_of_domain(kind, observable) is None


def test_the_guard_agrees_with_can_detect_over_the_whole_matrix():
    for kind in D.DetectorKind:
        for obs in D.Observable:
            if D.can_detect(kind, obs):
                assert D.refuse_out_of_domain(kind, obs) is None
            else:
                with pytest.raises(D.DetectorError):
                    D.refuse_out_of_domain(kind, obs)


def test_the_out_of_domain_message_names_the_artifact():
    with pytest.raises(D.DetectorError) as exc:
        D.refuse_out_of_domain(D.DetectorKind.HALL, D.Observable.ACOUSTIC)
    msg = str(exc.value)
    assert "ARTIFACT" in msg
    assert "piezoelectric" in msg          # what should have been used


# --- selection -----------------------------------------------------------

def test_select_detectors_returns_the_right_non_empty_sets():
    assert D.select_detectors(D.Observable.ACOUSTIC) == (
        D.DetectorKind.PIEZOELECTRIC,)
    assert D.select_detectors(D.Observable.MAGNETIC_FIELD) == (
        D.DetectorKind.HALL,)
    assert set(D.select_detectors(D.Observable.OPTICAL_INTENSITY)) == {
        D.DetectorKind.OPTICAL, D.DetectorKind.CCD}
    assert set(D.select_detectors(D.Observable.DISPLACEMENT)) == {
        D.DetectorKind.CAPACITIVE, D.DetectorKind.OPTICAL}
    for obs in (D.Observable.ACOUSTIC, D.Observable.MAGNETIC_FIELD,
                D.Observable.OPTICAL_INTENSITY, D.Observable.DISPLACEMENT):
        assert D.select_detectors(obs)


def test_no_detector_is_selected_for_an_individual_phonon():
    assert D.select_detectors(D.Observable.PHONON) == ()


def test_selection_is_consistent_with_can_detect():
    for obs in D.Observable:
        selected = set(D.select_detectors(obs))
        assert selected == {k for k in D.DetectorKind
                            if D.can_detect(k, obs)}


# --- bandwidth -----------------------------------------------------------

def test_a_ccd_cannot_resolve_a_4096_hz_waveform_per_cycle():
    assert D.bandwidth_ok(D.DetectorKind.CCD, 4096.0) is False
    with pytest.raises(D.DetectorError):
        D.refuse_out_of_band(D.DetectorKind.CCD, 4096.0)


def test_a_piezo_or_optical_detector_can_follow_4096_hz():
    assert D.bandwidth_ok(D.DetectorKind.PIEZOELECTRIC, 4096.0) is True
    assert D.bandwidth_ok(D.DetectorKind.OPTICAL, 4096.0) is True
    assert D.refuse_out_of_band(D.DetectorKind.PIEZOELECTRIC, 4096.0) is None
    assert D.refuse_out_of_band(D.DetectorKind.OPTICAL, 4096.0) is None


def test_the_ccd_band_ceiling_is_a_frame_rate():
    cap = D.capability(D.DetectorKind.CCD)
    assert cap.f_max_hz <= 1e3            # hertz to kilohertz frame rates
    assert D.bandwidth_ok(D.DetectorKind.CCD, 1.0) is True
    assert D.bandwidth_ok(D.DetectorKind.CCD, cap.f_max_hz) is True
    assert D.bandwidth_ok(D.DetectorKind.CCD, cap.f_max_hz * 10) is False
    with pytest.raises(D.DetectorError) as exc:
        D.refuse_out_of_band(D.DetectorKind.CCD, 4096.0)
    assert "FRAME RATE" in str(exc.value)


def test_below_band_is_refused_too():
    assert D.bandwidth_ok(D.DetectorKind.OPTICAL, 1e-6) is False
    with pytest.raises(D.DetectorError):
        D.refuse_out_of_band(D.DetectorKind.OPTICAL, 1e-6)


def test_a_negative_frequency_is_refused():
    with pytest.raises(D.DetectorError):
        D.bandwidth_ok(D.DetectorKind.PIEZOELECTRIC, -1.0)


def test_the_amplitude_floor_is_enforced():
    cap = D.capability(D.DetectorKind.CAPACITIVE)
    assert D.above_floor(D.DetectorKind.CAPACITIVE,
                         cap.amplitude_floor * 10) is True
    assert D.above_floor(D.DetectorKind.CAPACITIVE,
                         cap.amplitude_floor / 10) is False


# --- nothing is measured -------------------------------------------------

def test_refuse_measured_claim_always_raises():
    with pytest.raises(D.DetectorError):
        D.refuse_measured_claim()
    with pytest.raises(D.DetectorError):
        D.refuse_measured_claim("the CCD frame")


def test_report_measures_nothing_and_carries_the_verdict():
    r = D.detectors_report()
    assert r["measured_here"] == "nothing"
    assert r["verdict"] == "CCD_PHONON_DETECTION_REFUSED"
    assert r["evidence_class"] == "ANALYTIC_MODEL"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["what_this_does_not_say"]
    assert r["phonon_selection_is_empty"] is True


def test_report_carries_every_detector_with_both_halves_of_its_domain():
    r = D.detectors_report()
    for kind in D.DetectorKind:
        entry = r["detectors"][kind.value]
        assert entry["couples_to"]
        assert entry["cannot_detect"]
        assert entry["status"] == "MODEL_ONLY"
        assert entry["measured_here"] == "nothing"
    assert r["coupling_matrix"]["ccd"]["phonon"] is False
    assert r["coupling_matrix"]["piezoelectric"]["acoustic"] is True
    assert r["coupling_matrix"]["hall"]["magnetic_field"] is True


def test_the_report_is_public_safe():
    import json
    blob = json.dumps(D.detectors_report()).lower()
    for token in ("c:\\", "c:/", "onedrive", "users\\", "users/"):
        assert token not in blob
