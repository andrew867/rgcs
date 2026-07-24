"""R12 reciprocal space — the dual lattice, Laue, Bragg, structure factors.

The defining identity ai . bj = 2*pi*delta_ij is checked exactly (to
numerical tolerance) for a random cell and for the quartz cell; the
quartz reciprocal cell and volume are computed; the hexagonal d-spacing
is matched against hand values; Bragg's law round-trips theta -> d ->
theta; a planted screw axis produces the expected systematic absences
(POWER); and the three firewalls all raise.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from r12 import reciprocal as RC


# --- (1) the defining identity: ai . bj = 2*pi*delta_ij ------------------

def test_duality_identity_holds_for_a_random_cell():
    """The EXACT_IDENTITY, for an arbitrary non-degenerate lattice."""
    rng = np.random.default_rng(12345)
    two_pi = 2.0 * math.pi
    for _ in range(20):
        vectors = rng.uniform(-3.0, 3.0, size=(3, 3))
        if abs(np.linalg.det(vectors)) < 1e-3:
            continue
        b1, b2, b3 = RC.reciprocal_vectors(*vectors)
        m = RC.duality_matrix(vectors, (b1, b2, b3))
        assert np.allclose(m, two_pi * np.eye(3), atol=1e-9, rtol=0.0)
        assert RC.duality_defect(vectors, (b1, b2, b3)) <= RC.DUALITY_TOL


def test_duality_identity_holds_for_the_quartz_cell():
    cell = RC.ALPHA_QUARTZ_CELL
    dual = cell.reciprocal()
    m = RC.duality_matrix(cell.vectors, dual.vectors)
    assert np.allclose(m, RC.TWO_PI * np.eye(3), atol=1e-9, rtol=0.0)
    assert RC.duality_defect(cell.vectors, dual.vectors) <= RC.DUALITY_TOL


def test_reciprocal_volume_identity():
    """V* = (2*pi)**3 / V, the companion identity."""
    ident = RC.duality_identity()
    assert ident["claim_class"] == "EXACT_IDENTITY"
    assert ident["holds"] is True
    assert ident["volume_defect_relative"] <= RC.DUALITY_TOL


def test_check_duality_refuses_a_broken_dual_basis():
    """A dual basis with a swapped vector fails the identity and is refused."""
    cell = RC.ALPHA_QUARTZ_CELL
    b1, b2, b3 = cell.reciprocal().vectors
    with pytest.raises(RC.ReciprocalError):
        RC.check_duality(cell.vectors, (b2, b1, b3))  # b1 and b2 swapped


def test_a_degenerate_cell_has_no_reciprocal():
    with pytest.raises(RC.ReciprocalError):
        RC.reciprocal_vectors([1, 0, 0], [2, 0, 0], [0, 0, 1])  # coplanar
    with pytest.raises(RC.ReciprocalError):
        RC.DirectLattice([1, 0, 0], [0, 1, 0], [1, 1, 0])


# --- (2) the quartz reciprocal cell and volume --------------------------

def test_quartz_cell_volume_matches_the_closed_form():
    cell = RC.ALPHA_QUARTZ_CELL
    expected = 0.5 * math.sqrt(3.0) * RC.QUARTZ_A_ANGSTROM ** 2 \
        * RC.QUARTZ_C_ANGSTROM
    assert cell.cell_volume == pytest.approx(expected, rel=1e-12)
    assert RC.hexagonal_cell_volume() == pytest.approx(expected, rel=1e-12)


def test_quartz_gamma_is_120_degrees():
    params = RC.ALPHA_QUARTZ_CELL.cell_parameters()
    assert params["gamma_deg"] == pytest.approx(120.0, abs=1e-9)
    assert params["a"] == pytest.approx(RC.QUARTZ_A_ANGSTROM, rel=1e-12)
    assert params["c"] == pytest.approx(RC.QUARTZ_C_ANGSTROM, rel=1e-12)


def test_quartz_reciprocal_cell_closed_forms():
    """a* = 4*pi/(a*sqrt(3)) and c* = 2*pi/c for a hexagonal cell."""
    report = RC.alpha_quartz_cell()
    assert report["reciprocal_a_star_per_angstrom"] == pytest.approx(
        report["closed_form_a_star"], rel=1e-12)
    assert report["reciprocal_c_star_per_angstrom"] == pytest.approx(
        report["closed_form_c_star"], rel=1e-12)
    assert report["enantiomorphic_pair"] is True
    assert report["chiral"] is True
    assert set(report["space_groups"]) == {"P3121", "P3221"}
    assert report["source_class"] == "CONVENTIONAL_LITERATURE"


def test_quartz_enantiomorphs_are_a_mirror_pair():
    p1 = RC.QuartzEnantiomorph.P3121
    p2 = RC.QuartzEnantiomorph.P3221
    assert p1.partner() is p2 and p2.partner() is p1
    assert p1.screw_axis == "3_1" and p2.screw_axis == "3_2"
    assert p1.space_group_number == 152 and p2.space_group_number == 154


# --- (3) hexagonal d-spacing against hand values -------------------------

def test_hexagonal_d_spacing_matches_hand_values():
    a, c = RC.QUARTZ_A_ANGSTROM, RC.QUARTZ_C_ANGSTROM
    # (100): d = a*sqrt(3)/2 exactly for a hexagonal cell
    assert RC.hexagonal_d_spacing(1, 0, 0) == pytest.approx(
        a * math.sqrt(3.0) / 2.0, rel=1e-12)
    # (001): d = c
    assert RC.hexagonal_d_spacing(0, 0, 1) == pytest.approx(c, rel=1e-12)
    # (002): d = c/2
    assert RC.hexagonal_d_spacing(0, 0, 2) == pytest.approx(c / 2.0, rel=1e-12)
    # a fully worked hand value for (101)
    assert RC.hexagonal_d_spacing(1, 0, 1) == pytest.approx(
        3.3432093092439055, rel=1e-9)


def test_hexagonal_d_spacing_agrees_with_the_reciprocal_route():
    """The closed form and the |G| = 2*pi/d route must give one number."""
    dual = RC.ALPHA_QUARTZ_CELL.reciprocal()
    for hkl in ((1, 0, 0), (1, 0, 1), (1, 1, 0), (0, 0, 2), (2, 1, 3)):
        closed = RC.hexagonal_d_spacing(*hkl)
        via_g = dual.d_spacing(*hkl)
        assert closed == pytest.approx(via_g, rel=1e-12), hkl


def test_miller_indices_must_be_integers_and_nonzero():
    with pytest.raises(RC.ReciprocalError):
        RC.hexagonal_d_spacing(1.5, 0, 0)
    with pytest.raises(RC.ReciprocalError):
        RC.hexagonal_d_spacing(0, 0, 0)


# --- (4) Bragg round-trip and Laue == Bragg ------------------------------

def test_bragg_round_trips_theta_to_d_to_theta():
    wavelength = 1.5406
    for hkl in ((1, 0, 1), (1, 1, 0), (0, 0, 2), (1, 0, 0)):
        d = RC.hexagonal_d_spacing(*hkl)
        theta = RC.bragg_angle_rad(d, wavelength)
        d_back = RC.bragg_d_spacing(theta, wavelength)
        assert d_back == pytest.approx(d, rel=1e-12), hkl
        theta_back = RC.bragg_angle_rad(d_back, wavelength)
        assert theta_back == pytest.approx(theta, rel=1e-12), hkl


def test_bragg_refuses_an_unreachable_reflection():
    """n*lambda > 2*d has no solution; asin of >1 must be refused."""
    d = RC.hexagonal_d_spacing(0, 0, 2)               # ~2.70 A
    with pytest.raises(RC.ReciprocalError):
        RC.bragg_angle_rad(d, wavelength=10.0)        # 10 A > 2*d


def test_laue_condition_is_bragg_law():
    result = RC.laue_is_bragg(1, 0, 1)
    assert result["g_equals_two_pi_over_d"] is True
    assert result["magnitudes_agree"] is True
    assert result["bragg_residual"] == pytest.approx(0.0, abs=1e-9)


def test_laue_condition_is_a_vector_statement():
    """Two vectors of equal length but different direction do not satisfy Q=G."""
    g = np.array([1.0, 0.0, 0.0])
    q_same = np.array([1.0, 0.0, 0.0])
    q_rotated = np.array([0.0, 1.0, 0.0])             # same |Q|, wrong way
    assert RC.laue_condition_satisfied(q_same, g) is True
    assert RC.laue_condition_satisfied(q_rotated, g) is False


# --- (5) structure factor and planted systematic absences (POWER) --------

def test_structure_factor_of_one_atom_has_unit_intensity_at_the_factor():
    atoms = [RC.Atom("A", 0.0, 0.0, 0.0, scattering_factor=1.0)]
    f = RC.structure_factor(atoms, 1, 0, 0)
    assert abs(f) == pytest.approx(1.0, abs=1e-12)


def test_planted_3_1_screw_axis_extinguishes_00l_unless_l_is_a_triple():
    """POWER: a 3_1 screw along c gives 00l present only for l = 3, 6, 9..."""
    result = RC.screw_axis_extinctions(3, 1, l_max=12)
    assert result["expected_period"] == 3
    assert result["l_present"] == [3, 6, 9, 12]
    assert result["l_absent"] == [1, 2, 4, 5, 7, 8, 10, 11]
    assert result["matches_rule"] is True
    assert result["l_present_are_multiples_of_period"] is True


def test_planted_3_2_screw_axis_also_extinguishes_00l_unless_l_is_a_triple():
    result = RC.screw_axis_extinctions(3, 2, l_max=12)
    assert result["expected_period"] == 3
    assert result["l_present"] == [3, 6, 9, 12]
    assert result["matches_rule"] is True


def test_planted_2_1_screw_axis_extinguishes_odd_00l():
    """POWER: a 2_1 screw along c gives 00l present only for even l."""
    result = RC.screw_axis_extinctions(2, 1, l_max=8)
    assert result["expected_period"] == 2
    assert result["l_present"] == [2, 4, 6, 8]
    assert result["l_absent"] == [1, 3, 5, 7]
    assert result["matches_rule"] is True


def test_a_structure_without_a_screw_axis_shows_no_such_absences():
    """The absence is a consequence of symmetry: remove it and 00l returns."""
    single = [RC.Atom("A", 0.3, 0.1, 0.2)]
    absent = RC.systematic_absences(single, [(0, 0, l) for l in range(1, 8)])
    assert absent == ()                               # nothing extinguished


def test_absence_is_scaled_by_total_scattering_power():
    """Heavier atoms do not turn a real absence into a present reflection."""
    orbit = RC.screw_axis_orbit(RC.Atom("A", 0.47, 0.0, 0.0,
                                        scattering_factor=50.0), 3, 1)
    assert RC.is_systematically_absent(orbit, 0, 0, 1) is True
    assert RC.is_systematically_absent(orbit, 0, 0, 3) is False


# --- (6) the firewalls ----------------------------------------------------

def test_refuse_reciprocal_as_physical_space_always_raises():
    with pytest.raises(RC.ReciprocalError) as exc:
        RC.refuse_reciprocal_as_physical_space((2, 1, 3))
    assert "INVERSE LENGTH" in str(exc.value)


def test_refuse_qspace_as_geographic_always_raises():
    with pytest.raises(RC.ReciprocalError) as exc:
        RC.refuse_qspace_as_geographic([0.1, 0.2, 0.3])
    message = str(exc.value)
    assert "orientation" in message or "orientation" in message.lower()


def test_refuse_measured_pattern_claim_always_raises():
    with pytest.raises(RC.ReciprocalError) as exc:
        RC.refuse_measured_pattern_claim()
    assert "BENCH_MEASUREMENT" in str(exc.value)
    with pytest.raises(RC.ReciprocalError):
        RC.refuse_measured_pattern_claim("peak at 26.6 degrees",
                                         reflection=(1, 0, 1))


# --- (7) the report -------------------------------------------------------

def test_report_carries_the_verdict_and_the_disclaimers():
    report = RC.reciprocal_report()
    assert report["verdict"] == "RECIPROCAL_SPACE_MODEL_STANDARD_CRYSTALLOGRAPHY"
    assert RC.VERDICT == "RECIPROCAL_SPACE_MODEL_STANDARD_CRYSTALLOGRAPHY"
    assert report["measured_here"] == "nothing"
    assert report["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert report["claim_class"] in RC.CLAIM_CLASSES
    assert report["claim_class"] == "SOURCE_ESTABLISHED_PHYSICS"
    assert report["exact_identity"]["claim_class"] == "EXACT_IDENTITY"
    assert report["d_spacing_routes_agree"] is True
    assert report["what_this_does_not_say"]


def test_the_declared_claim_classes_are_the_shared_nine():
    assert RC.CLAIM_CLASSES == (
        "EXACT_IDENTITY", "SOURCE_ESTABLISHED_PHYSICS",
        "REPOSITORY_COMPUTATIONAL_RESULT", "ENGINEERING_CANDIDATE",
        "RETROSPECTIVE_NUMERIC_MATCH", "PROSPECTIVE_PREDICTION",
        "BENCH_MEASUREMENT", "UNSUPPORTED", "BLOCKED_MISSING_DATA")


def test_reciprocal_module_imports_under_its_package_name():
    from r12 import reciprocal
    assert reciprocal.VERDICT == RC.VERDICT
