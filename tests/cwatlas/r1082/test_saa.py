"""P06 — Shell-resolved SAA magnetic minimum (the DYNAMIC layer)."""

from __future__ import annotations

import numpy as np
import pytest

from cwatlas.r1082 import claims, saa


# -- focused ----------------------------------------------------------------

def test_resolve_returns_a_candidate_region_not_measured():
    m = saa.resolve_from_shell(2020.0, 6)
    assert m.result_class == claims.ResultClass.CANDIDATE_REGION.value
    assert m.evidence_class == claims.EvidenceClass.DERIVED_MATHEMATICS.value
    assert m.uncertainty_region.area_m2 > 0.0  # never invented precision


def test_direction_is_a_unit_vector():
    m = saa.resolve_from_shell(2020.0, 6)
    assert np.isclose(np.linalg.norm(m.direction_ecef), 1.0)


def test_shell_supplies_radius():
    # The shell (not a separate altitude request) supplies the radius.
    m = saa.resolve_from_shell(2020.0, 3)
    assert m.radius_m == saa.NOMINAL_SHELL_RADIUS_M[3]


def test_explicit_shell_radius_override_is_used():
    m = saa.resolve_from_shell(2020.0, 6, radius_m=6.8e6)
    assert m.radius_m == 6.8e6


# -- POWER: drifts with epoch AND shifts with radius ------------------------

def test_position_drifts_with_epoch():
    a = saa.resolve_from_shell(2000.0, 6)
    b = saa.resolve_from_shell(2040.0, 6)
    # Same shell (same radius), different epoch -> position moves.
    assert a.radius_m == b.radius_m
    assert (a.latitude_deg, a.longitude_deg) != (b.latitude_deg, b.longitude_deg)
    assert abs(a.longitude_deg - b.longitude_deg) > 1.0  # westward drift


def test_position_shifts_with_radius():
    # Same epoch, different shell (different radius) -> position shifts.
    a = saa.resolve_from_shell(2020.0, 3)      # surface
    b = saa.resolve_from_shell(2020.0, 7)      # high satellite
    assert a.radius_m != b.radius_m
    assert (a.latitude_deg, a.longitude_deg) != (b.latitude_deg, b.longitude_deg)


def test_field_magnitude_depends_on_both_epoch_and_radius():
    base = saa.resolve_from_shell(2020.0, 6)
    later = saa.resolve_from_shell(2050.0, 6)
    higher = saa.resolve(2020.0, base.radius_m + 1.0e6)
    assert base.field_nt != later.field_nt      # epoch dependence
    assert base.field_nt != higher.field_nt     # radius dependence


# -- negative: validity + altitude-missing-when-shell -----------------------

def test_epoch_outside_validity_refused():
    with pytest.raises(saa.SAAError):
        saa.resolve(1800.0, saa.R0_M)


def test_radius_outside_validity_refused():
    with pytest.raises(saa.SAAError):
        saa.resolve(2020.0, 1.0e5)


def test_unknown_shell_index_refused():
    with pytest.raises(Exception):
        saa.resolve_from_shell(2020.0, 99)


def test_altitude_missing_when_shell_present_is_refused():
    # A shell is present -> claiming altitude is missing is refused.
    with pytest.raises(claims.R1082ClaimError):
        saa.refuse_altitude_missing(shell_state=3)


def test_no_shell_present_does_not_refuse_altitude():
    saa.refuse_altitude_missing(shell_state=None)  # no shell -> no refusal


# -- determinism ------------------------------------------------------------

def test_resolution_is_deterministic():
    a = saa.resolve_from_shell(2025.5, 6)
    b = saa.resolve_from_shell(2025.5, 6)
    assert (a.latitude_deg, a.longitude_deg, a.field_nt) == (
        b.latitude_deg, b.longitude_deg, b.field_nt)


# -- report -----------------------------------------------------------------

def test_report_declares_both_dependencies_and_no_measurement():
    r = saa.saa_report()
    assert r["drifts_with_epoch"] is True
    assert r["shifts_with_radius"] is True
    assert r["shell_supplies_radius"] is True
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["source_origin"] == "SOURCE_ORIGIN_NOT_VALIDATED"
