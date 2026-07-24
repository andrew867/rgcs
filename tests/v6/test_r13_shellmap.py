"""R13 — the eight-shell radial mapping model: monotonic boundaries, exact
boundary assignment, boundary transfer with a closed energy ledger
(POWER), thickness-scaled eigenmodes, and the bin/measurement refusals."""

from __future__ import annotations

from fractions import Fraction

import pytest

from r13 import shellmap as S


# --- the eight-shell boundaries and assignment --------------------------

def test_there_are_eight_shells_and_nine_boundaries():
    assert S.SHELL_COUNT == 8
    assert S.BOUNDARY_COUNT == 9


def test_boundaries_are_monotonic():
    model = S.default_eight_shell()
    assert model.boundaries_monotonic() is True
    b = model.boundaries
    assert all(b[i + 1] > b[i] for i in range(len(b) - 1))


def test_a_non_monotonic_boundary_set_is_refused():
    bad = (0.0, 1.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0)   # 1.0 repeated
    with pytest.raises(S.ShellMapError):
        S.EightShell(boundaries=bad)


def test_a_boundary_set_of_the_wrong_length_is_refused():
    with pytest.raises(S.ShellMapError):
        S.EightShell(boundaries=tuple(float(i) for i in range(8)))


def test_assignment_is_correct_at_each_boundary():
    model = S.default_eight_shell(inner=1000.0, step=500.0)
    b = model.boundaries
    # each left boundary lands in its own shell
    for k in range(S.SHELL_COUNT):
        assert model.assign_shell(b[k]) == k
    # the outer edge is inclusive and lands in the outermost shell
    assert model.assign_shell(b[-1]) == S.SHELL_COUNT - 1


def test_assignment_inside_a_shell_returns_that_shell():
    model = S.default_eight_shell(inner=1000.0, step=500.0)
    # a radius strictly inside shell 3: [2500, 3000)
    assert model.assign_shell(2750.0) == 3


def test_a_radius_out_of_range_is_refused_below_and_above():
    model = S.default_eight_shell(inner=1000.0, step=500.0)
    with pytest.raises(S.ShellMapError):
        model.assign_shell(999.0)
    with pytest.raises(S.ShellMapError):
        model.assign_shell(model.boundaries[-1] + 1.0)


# --- boundary transfer: the energy ledger closes exactly (POWER) --------

def test_shell_transfer_conserves_energy_exactly():
    """POWER: R + T = 1 exactly, in rational arithmetic."""
    out = S.shell_transfer(2, 3)
    assert out["energy_sum"] == Fraction(1)
    assert out["energy_conserved_exact"] is True
    assert out["reflected_fraction"] + out["transmitted_fraction"] == 1


def test_shell_transfer_matches_the_fresnel_fractions():
    out = S.shell_transfer(2, 3)
    # R = (3-2)^2 / (2+3)^2 = 1/25 ; T = 4*2*3 / 25 = 24/25
    assert out["reflected_fraction"] == Fraction(1, 25)
    assert out["transmitted_fraction"] == Fraction(24, 25)


def test_a_matched_boundary_transmits_fully():
    out = S.shell_transfer(2, 2)
    assert out["transmitted_fraction"] == 1
    assert out["reflected_fraction"] == 0
    assert out["matched"] is True


def test_energy_conserves_for_fractional_impedances_too():
    out = S.shell_transfer(Fraction(7, 3), Fraction(11, 5))
    assert out["energy_sum"] == Fraction(1)


def test_a_non_positive_impedance_is_refused():
    with pytest.raises(S.ShellMapError):
        S.shell_transfer(0, 1)


# --- radial eigenmodes scale with shell thickness -----------------------

def test_mode_spacing_scales_inversely_with_thickness():
    # doubling the thickness halves the wavenumber spacing pi/L
    assert S.mode_spacing(1000.0) == pytest.approx(2.0 * S.mode_spacing(2000.0))


def test_mode_count_scales_with_thickness():
    thin = S.radial_mode_count(1000.0, 0.1)
    thick = S.radial_mode_count(2000.0, 0.1)
    assert thin > 0
    assert thick >= 2 * thin - 1        # count grows in proportion to L


def test_radial_modes_are_the_expected_harmonic_series():
    modes = S.radial_modes(1000.0, 3)
    assert len(modes) == 3
    assert modes[1] == pytest.approx(2.0 * modes[0])
    assert modes[2] == pytest.approx(3.0 * modes[0])


# --- the load-bearing refusals ------------------------------------------

def test_refuse_shell_as_decoded_layer_always_raises():
    with pytest.raises(S.ShellMapError, match="bin"):
        S.refuse_shell_as_decoded_layer(3, 2750.0)


def test_refuse_model_shell_as_measured_always_raises():
    with pytest.raises(S.ShellMapError, match="ANALYTIC_MODEL"):
        S.refuse_model_shell_as_measured()


# --- the report ---------------------------------------------------------

def test_report_carries_verdict_and_claim_discipline():
    r = S.shellmap_report()
    assert r["verdict"] == "EIGHT_SHELL_MAPPING_MODEL"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["claim_class"] == "ANALYTIC_MODEL"
    assert r["boundaries_monotonic"] is True
    assert r["matched_boundary_transmits_fully"] is True
    assert r["mismatch_energy_conserved_exact"] is True
    assert r["shell_count"] == 8
    assert "what_this_does_not_say" in r
