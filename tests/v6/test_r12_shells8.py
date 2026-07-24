"""R12 — eight radial shells with an unresolved index-to-radius projection."""

from __future__ import annotations

from fractions import Fraction

import pytest

from r12 import shells8 as S


# --- the count is arithmetic: 3 bits address 8 shells ------------------

def test_there_are_exactly_eight_shells_and_two_cubed_is_eight():
    assert S.SHELL_COUNT == 8
    assert 2 ** S.S3_BITS == 8
    assert 2 ** 3 == S.SHELL_COUNT


def test_the_default_register_holds_eight_shells_indexed_zero_to_seven():
    reg = S.DEFAULT_REGISTER
    assert len(reg.shells) == 8
    assert [sh.index for sh in reg.shells] == list(range(8))


def test_a_register_of_the_wrong_size_is_refused():
    with pytest.raises(S.Shells8Error):
        S.ShellRegister(shells=tuple(
            S.Shell(i, float(i), float(i + 1), "u") for i in range(7)))


# --- index out of range ------------------------------------------------

def test_shell_index_out_of_range_is_refused_below_and_above():
    with pytest.raises(S.Shells8Error):
        S.refuse_shell_index_out_of_range(-1)
    with pytest.raises(S.Shells8Error):
        S.refuse_shell_index_out_of_range(8)


def test_valid_shell_indices_are_returned():
    for i in range(8):
        assert S.refuse_shell_index_out_of_range(i) == i


def test_a_shell_with_an_out_of_range_index_cannot_be_built():
    with pytest.raises(S.Shells8Error):
        S.Shell(8, 0.0, 1.0, "u")


def test_the_register_indexer_refuses_an_out_of_range_index():
    with pytest.raises(S.Shells8Error):
        S.DEFAULT_REGISTER.shell(99)


# --- the four spacing laws disagree for the same index -----------------

def test_the_four_spacing_laws_are_carried():
    laws = S.spacing_laws()
    assert len(laws) == 4
    names = {law.value for law in laws}
    assert names == {"LINEAR", "GEOMETRIC", "HYDROGENIC_N_SQUARED",
                     "LOGARITHMIC"}


def test_the_four_laws_give_pairwise_different_radii_for_the_same_index():
    radii = S.radii_under_all_laws(3, origin=1.0, spacing=1.0)
    values = list(radii.values())
    assert len(values) == 4
    for i in range(len(values)):
        for j in range(i + 1, len(values)):
            assert abs(values[i] - values[j]) > 1e-9
    assert S.laws_disagree(3)


def test_radius_under_law_matches_the_declared_formulae():
    # index 3, origin 1, spacing 1
    assert S.radius_under_law(3, S.SpacingLaw.LINEAR, 1.0, 1.0) == \
        pytest.approx(4.0)
    assert S.radius_under_law(3, S.SpacingLaw.GEOMETRIC, 1.0, 1.0) == \
        pytest.approx(8.0)
    assert S.radius_under_law(3, S.SpacingLaw.HYDROGENIC_N_SQUARED,
                              1.0, 1.0) == pytest.approx(16.0)


# --- the projection is refused unless fully declared -------------------

def test_radius_from_index_is_refused_with_nothing_declared():
    with pytest.raises(S.Shells8Error):
        S.refuse_radius_from_index(3)


def test_radius_from_index_is_refused_with_an_undeclared_basis():
    with pytest.raises(S.Shells8Error):
        S.refuse_radius_from_index(
            3, basis=S.ShellBasis.UNDECLARED, origin=1.0,
            law=S.SpacingLaw.LINEAR, spacing=1.0)


def test_radius_from_index_is_refused_with_a_missing_origin():
    with pytest.raises(S.Shells8Error):
        S.refuse_radius_from_index(
            3, basis=S.ShellBasis.GEOCENTRIC_RADIUS,
            law=S.SpacingLaw.LINEAR, spacing=1.0)


def test_radius_from_index_is_refused_with_a_missing_law():
    with pytest.raises(S.Shells8Error):
        S.refuse_radius_from_index(
            3, basis=S.ShellBasis.GEOCENTRIC_RADIUS, origin=1.0,
            spacing=1.0)


def test_radius_from_index_succeeds_with_basis_origin_and_law_declared():
    r = S.refuse_radius_from_index(
        3, basis=S.ShellBasis.GEOCENTRIC_RADIUS, origin=1.0,
        law=S.SpacingLaw.LINEAR, spacing=1.0)
    assert r == pytest.approx(4.0)


# --- the atomic-shell reading is an analogy only -----------------------

def test_atomic_shell_physics_is_refused():
    with pytest.raises(S.Shells8Error):
        S.refuse_atomic_shell_physics()


# --- the observed readings are retained without kinematics -------------

def test_the_three_observed_readings_are_ordered_inward():
    readings = S.OBSERVED_SHELL_READINGS_MILES
    assert readings == (Fraction(3478), Fraction(1903), Fraction(1238))
    assert all(a > b for a, b in zip(readings, readings[1:]))
    assert S.observed_readings_ordered_inward() is True


def test_the_observed_readings_carry_no_timestamps():
    assert S.OBSERVED_READINGS_TIMESTAMPS is None


def test_speed_orbit_and_eta_are_refused_from_the_untimed_readings():
    for q in ("speed", "orbit", "eta"):
        with pytest.raises(S.Shells8Error):
            S.refuse_reading_kinematics(q)


def test_mapping_readings_is_unresolved_without_a_declared_projection():
    out = S.map_readings_onto_register()
    assert out["status"] == S.PROJECTION_UNRESOLVED
    assert out["placements"] is None
    assert out["ordered_inward"] is True


def test_mapping_readings_places_them_under_a_declared_projection():
    out = S.map_readings_onto_register(
        basis=S.ShellBasis.ALTITUDE_ABOVE_ELLIPSOID, origin=1000.0,
        law=S.SpacingLaw.LINEAR, spacing=500.0)
    assert out["status"] == "PROJECTION_DECLARED"
    assert len(out["placements"]) == 3


# --- the report --------------------------------------------------------

def test_the_report_refuses_to_over_claim():
    r = S.shells8_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["claim_class"] == "REPOSITORY_COMPUTATIONAL_RESULT"
    assert r["verdict"] == "EIGHT_SHELL_REGISTER_DEFINED_PROJECTION_UNRESOLVED"
    assert r["shell_count"] == 8
    assert r["two_cubed_is_eight"] is True
    assert r["projection_status"] == S.PROJECTION_UNRESOLVED
    assert r["laws_disagree_for_index_3"] is True


def test_the_report_names_the_analogy_as_an_analogy():
    r = S.shells8_report()
    assert "ANALOGY" in r["what_this_does_not_say"]
    assert "measured" in r["what_this_does_not_say"]
