"""P04 — crystal axis and interferometric alignment."""

from __future__ import annotations

import math

import pytest

import r7
from r7 import alignment as AL


# --- the axis object --------------------------------------------------

def test_axis_accepts_a_unit_vector():
    a = AL.Axis(0.0, 0.0, 1.0, "LOCAL_LEVEL", AL.from_arcsec(1.0),
                kind="GRAVITY")
    assert a.norm == pytest.approx(1.0)
    assert a.components == (0.0, 0.0, 1.0)


def test_axis_rejects_a_non_unit_vector():
    with pytest.raises(ValueError, match="unit vector"):
        AL.Axis(0.0, 0.0, 2.0, "LOCAL_LEVEL", 0.0)


def test_axis_rejects_the_zero_vector():
    """The zero vector has no direction; normalizing it invents one."""
    with pytest.raises(ValueError, match="no direction"):
        AL.Axis(0.0, 0.0, 0.0, "LOCAL_LEVEL", 0.0)
    with pytest.raises(ValueError, match="no direction"):
        AL.Axis.unit(0.0, 0.0, 0.0, "LOCAL_LEVEL", 0.0)


def test_axis_unit_normalizes():
    a = AL.Axis.unit(3.0, 0.0, 4.0, "SPECIMEN_BODY", 0.0)
    assert a.norm == pytest.approx(1.0)
    assert a.z == pytest.approx(0.8)


def test_axis_rejects_unknown_frame_kind_and_negative_sigma():
    with pytest.raises(ValueError):
        AL.Axis(0.0, 0.0, 1.0, "NOT_A_FRAME", 0.0)
    with pytest.raises(ValueError):
        AL.Axis(0.0, 0.0, 1.0, "MOUNT", 0.0, kind="NOT_A_KIND")
    with pytest.raises(ValueError):
        AL.Axis(0.0, 0.0, 1.0, "MOUNT", -1e-6)


def test_angle_between_orthogonal_axes_is_ninety_degrees():
    a = AL.Axis(1.0, 0.0, 0.0, "MOUNT", 0.0)
    b = AL.Axis(0.0, 1.0, 0.0, "MOUNT", 0.0)
    assert a.angle_to(b) == pytest.approx(math.pi / 2)


def test_separation_record_flags_a_frame_mismatch():
    a = AL.Axis(0.0, 0.0, 1.0, "MOUNT", 0.0, kind="BODY")
    b = AL.Axis(0.0, 0.0, 1.0, "GEOCENTRIC", 0.0, kind="GRAVITY")
    rec = a.separation_record(b)
    assert rec["same_frame"] is False
    assert "identity transform" in rec["note"]
    assert rec["evidence_class"] == "DERIVED_ARITHMETIC"


# --- the misalignment budget -----------------------------------------

def test_budget_names_every_term():
    b = AL.misalignment_budget()
    assert set(b["term_names"]) == {
        "cut_tolerance_rad", "mounting_tolerance_rad",
        "gravity_deflection_rad", "measurement_error_rad"}
    for name, term in b["terms"].items():
        assert term["what"], f"{name} has no description"
        assert term["origin"], f"{name} has no stated origin"


def test_budget_adds_in_quadrature():
    b = AL.misalignment_budget(
        cut_tolerance_rad=3e-3, mounting_tolerance_rad=4e-3,
        gravity_deflection_rad=0.0, measurement_error_rad=0.0)
    assert b["total_rad"] == pytest.approx(5e-3)
    assert b["combination"].startswith("quadrature")


def test_quadrature_total_is_below_the_linear_sum():
    b = AL.misalignment_budget()
    linear = sum(t["value_rad"] for t in b["terms"].values())
    assert b["total_rad"] < linear
    assert b["total_rad"] >= max(
        t["value_rad"] for t in b["terms"].values())


def test_budget_reports_the_dominant_term():
    b = AL.misalignment_budget()
    worst = max(b["terms"], key=lambda k: b["terms"][k]["value_rad"])
    assert b["dominant_term"] == worst


def test_budget_takes_the_measurement_term_from_a_method():
    b = AL.misalignment_budget(method="XRD_LAUE_BACK_REFLECTION")
    assert b["terms"]["measurement_error_rad"]["value_rad"] == \
        pytest.approx(AL.from_deg(0.01))


def test_budget_rejects_negative_terms_and_unknown_methods():
    with pytest.raises(ValueError):
        AL.misalignment_budget(cut_tolerance_rad=-1.0)
    with pytest.raises(ValueError):
        AL.misalignment_budget(method="OUIJA_BOARD")


# --- three distinct axes ---------------------------------------------

def _mounting(tilt_rad: float = 1e-3) -> AL.CrystalMounting:
    return AL.CrystalMounting(
        specimen_id="NONE-NO-SPECIMEN-EXISTS",
        body_axis=AL.Axis(0.0, 0.0, 1.0, "MOUNT",
                          AL.from_arcsec(1.0), kind="BODY",
                          method="AUTOCOLLIMATOR"),
        gravity_axis=AL.Axis(0.0, 0.0, 1.0, "MOUNT",
                             AL.from_deg(0.1), kind="GRAVITY",
                             method="BUBBLE_LEVEL_OR_PLUMB"),
        c_axis=AL.Axis.unit(math.sin(tilt_rad), 0.0, math.cos(tilt_rad),
                            "MOUNT", AL.from_deg(0.01), kind="C_AXIS",
                            method="XRD_LAUE_BACK_REFLECTION"))


def test_the_three_axes_are_separate_objects():
    m = _mounting()
    rep = m.coincidence_report()
    assert set(rep["pairs"]) == {"body_to_c", "body_to_gravity",
                                 "c_to_gravity"}
    assert rep["pairs"]["body_to_c"]["separation_rad"] > 0.0


def test_mounting_rejects_an_axis_of_the_wrong_kind():
    with pytest.raises(ValueError):
        AL.CrystalMounting(
            specimen_id="X",
            body_axis=AL.Axis(0.0, 0.0, 1.0, "MOUNT", 0.0,
                              kind="GRAVITY"),
            gravity_axis=AL.Axis(0.0, 0.0, 1.0, "MOUNT", 0.0,
                                 kind="GRAVITY"),
            c_axis=AL.Axis(0.0, 0.0, 1.0, "MOUNT", 0.0, kind="C_AXIS"))


def test_a_c_axis_without_a_lattice_method_is_caveated():
    m = AL.CrystalMounting(
        specimen_id="X",
        body_axis=AL.Axis(0.0, 0.0, 1.0, "MOUNT", 0.0, kind="BODY"),
        gravity_axis=AL.Axis(0.0, 0.0, 1.0, "MOUNT", 0.0,
                             kind="GRAVITY"),
        c_axis=AL.Axis(0.0, 0.0, 1.0, "MOUNT", 0.0, kind="C_AXIS",
                       method="CONOSCOPIC_INTERFERENCE_FIGURE"))
    rep = m.coincidence_report()
    assert rep["c_axis_from_lattice_measurement"] is False
    assert "morphological" in rep["caveat"]


# --- methods ----------------------------------------------------------

def test_every_method_is_cited_as_literature_or_catalogue_class():
    for name, spec in AL.ALIGNMENT_METHODS.items():
        assert spec["source_class"] in (
            "LITERATURE_CLASS", "MANUFACTURER_CATALOGUE_CLASS"), name


def test_autocollimator_is_about_one_arcsecond():
    assert AL.ALIGNMENT_METHODS["AUTOCOLLIMATOR"]["resolution_arcsec"] \
        == pytest.approx(1.0)


def test_xrd_laue_is_the_only_direct_c_axis_method():
    """Conoscopy finds the optic axis optically; only diffraction
    interrogates the lattice."""
    direct = AL.method_registry()["direct_c_axis_methods"]
    assert direct == ["XRD_LAUE_BACK_REFLECTION"]


def test_best_method_for_the_c_axis_is_laue_not_the_finer_instruments():
    best = AL.best_method_for("C_AXIS")
    assert best["method"] == "XRD_LAUE_BACK_REFLECTION"
    # Finer instruments exist. They measure something else.
    assert "AUTOCOLLIMATOR" in \
        best["finer_instruments_that_measure_something_else"]
    assert "LASER_INTERFEROMETRY" in \
        best["finer_instruments_that_measure_something_else"]


def test_best_method_for_body_and_gravity():
    assert AL.best_method_for("BODY")["method"] == "LASER_INTERFEROMETRY"
    assert AL.best_method_for("GRAVITY")["method"] == \
        "BUBBLE_LEVEL_OR_PLUMB"


def test_best_method_rejects_an_unknown_axis_kind():
    with pytest.raises(ValueError):
        AL.best_method_for("MAGNETIC")


# --- the critical refusal --------------------------------------------

def test_c_axis_from_morphology_is_refused():
    with pytest.raises(AL.AlignmentRefused):
        AL.refuse_c_axis_from_morphology(prism_faces=6)


def test_the_refusal_names_both_twin_laws():
    with pytest.raises(AL.AlignmentRefused) as exc:
        AL.refuse_c_axis_from_morphology()
    msg = str(exc.value)
    assert "Brazil" in msg
    assert "Dauphine" in msg
    assert "twinning" in msg


def test_the_refusal_names_diffraction_as_the_alternative():
    with pytest.raises(AL.AlignmentRefused) as exc:
        AL.refuse_c_axis_from_morphology()
    assert "XRD_LAUE_BACK_REFLECTION" in str(exc.value)


def test_the_long_axis_is_not_the_c_axis():
    assert AL.c_axis_is_the_long_axis() is False


# --- plumb is not "toward the centre" ---------------------------------

def test_geocentric_deviation_vanishes_at_equator_and_pole():
    assert AL.plumb_geocentric_deviation_rad(0.0) == pytest.approx(0.0)
    assert AL.plumb_geocentric_deviation_rad(
        math.pi / 2 - 1e-9) == pytest.approx(0.0, abs=1e-6)


def test_max_deviation_peaks_near_forty_five_degrees():
    peak = AL.max_plumb_geocentric_deviation()
    assert peak["at_geodetic_latitude_deg"] == pytest.approx(45.0,
                                                             abs=0.5)


def test_max_deviation_is_about_zero_point_one_nine_degrees():
    """The equatorial-bulge term: ~0.192 deg = ~11.5 arcmin."""
    peak = AL.max_plumb_geocentric_deviation()
    assert peak["max_deviation_deg"] == pytest.approx(0.192, abs=0.005)
    assert peak["max_deviation_arcmin"] == pytest.approx(11.5, abs=0.3)


def test_plumb_geocentric_deviation_dwarfs_the_autocollimator():
    """The numeric comparison the P04 firewall rests on.

    An autocollimator resolves ~1 arcsec. The geodetic-to-geocentric
    difference reaches ~690 arcsec. Saying "aligned to the core" when
    you mean "plumb" is an error some 690 times the resolution of the
    instrument used to make the claim.
    """
    peak = AL.max_plumb_geocentric_deviation()
    auto = AL.ALIGNMENT_METHODS["AUTOCOLLIMATOR"]["resolution_rad"]
    assert peak["max_deviation_arcsec"] > 600.0
    assert peak["max_deviation_rad"] > auto
    assert peak["max_deviation_rad"] / auto > 500.0


def test_earth_axis_note_keeps_the_three_directions_apart():
    note = AL.earth_axis_note()
    assert note["plumb_is_geocentric_radial"] is False
    assert len(note["three_directions"]) == 3
    assert note["ratio_max_deviation_to_autocollimator"] > 500.0
    assert "arcmin" in note["deflection_of_vertical_range"]


def test_deflection_of_the_vertical_is_arcsec_to_arcmin_class():
    defl = AL.DEFAULT_BUDGET_TERMS["gravity_deflection_rad"]["value"]
    assert 1.0 <= AL.arcsec(defl) <= 60.0


# --- alignment report -------------------------------------------------

def test_a_claim_inside_the_budget_is_unresolved():
    rep = AL.alignment_report(AL.from_arcsec(0.5),
                              method="AUTOCOLLIMATOR")
    assert rep["resolvable"] is False
    assert "unresolved" in rep["verdict"]


def test_a_claim_above_the_budget_is_testable():
    rep = AL.alignment_report(AL.from_deg(5.0),
                              method="AUTOCOLLIMATOR")
    assert rep["resolvable"] is True


def test_alignment_report_rejects_bad_inputs():
    with pytest.raises(ValueError):
        AL.alignment_report(-1.0)
    with pytest.raises(ValueError):
        AL.alignment_report(1e-3, method="DOWSING_ROD")


# --- house rules ------------------------------------------------------

def test_no_forbidden_state_appears_in_the_module():
    src = (AL.__file__)
    with open(src, encoding="utf-8") as fh:
        text = fh.read()
    for state in r7.FORBIDDEN_STATES:
        assert state not in text, state


def test_every_returned_dict_carries_an_evidence_class():
    a = AL.Axis(0.0, 0.0, 1.0, "MOUNT", 0.0)
    records = [
        a.as_record(),
        a.separation_record(a),
        AL.misalignment_budget(),
        AL.method_registry(),
        AL.best_method_for("C_AXIS"),
        AL.alignment_report(1e-3),
        AL.max_plumb_geocentric_deviation(),
        AL.earth_axis_note(),
        AL.status_report(),
        _mounting().coincidence_report(),
    ]
    for rec in records:
        assert rec["evidence_class"] in ("SYNTHETIC_MODEL",
                                         "DERIVED_ARITHMETIC")


def test_status_report_is_deterministic():
    assert AL.status_report() == AL.status_report()


def test_status_report_refuses_morphological_c_axis():
    rep = AL.status_report()
    assert rep["c_axis_from_morphology"] == "REFUSED"
    assert rep["only_direct_c_axis_method"] == "XRD_LAUE_BACK_REFLECTION"
    assert rep["axes_modelled_separately"] == list(AL.AXIS_KINDS)


def test_the_module_says_nothing_is_bench_data():
    assert "Nothing here is bench data" in AL.__doc__
    assert "no specimen has been" in AL.method_registry()["provenance"]
