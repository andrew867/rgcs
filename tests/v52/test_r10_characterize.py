"""P05 — characterization ladders: axis, density, defects, refusals."""

from __future__ import annotations

import numpy as np
import pytest

from r10 import characterize as CH


# --- Archimedes density has power --------------------------------------

def test_archimedes_recovers_quartz_density():
    # Plant a mass pair that must yield ~2.65 g/cm^3 for quartz.
    rho_water = CH.RHO_WATER_20C_G_PER_CM3
    m_air = 2.65
    # buoyant weight = displaced water = (m_air / 2.65) * rho_water
    m_water = m_air - (m_air / 2.65) * rho_water
    rho = CH.archimedes_density(m_air, m_water, rho_water)
    assert abs(rho - 2.65) < 1e-6


def test_archimedes_refuses_a_floating_specimen():
    with pytest.raises(CH.CharacterizeError):
        CH.archimedes_density(1.0, 1.0)          # zero buoyant difference
    with pytest.raises(CH.CharacterizeError):
        CH.archimedes_density(1.0, 2.0)          # apparent gain, impossible


# --- c-axis: two directions resolve, one is underdetermined ------------

def test_two_non_parallel_directions_resolve_the_c_axis():
    c = CH.resolve_c_axis([(1, 0, 0), (0, 1, 0)])
    assert np.isclose(np.linalg.norm(c), 1.0)
    assert np.allclose(np.abs(c), [0, 0, 1])


def test_single_direction_is_underdetermined():
    with pytest.raises(CH.CharacterizeError):
        CH.resolve_c_axis([(1, 0, 0)])


def test_parallel_directions_cannot_resolve_the_c_axis():
    with pytest.raises(CH.CharacterizeError):
        CH.resolve_c_axis([(1, 0, 0), (2, 0, 0)])


# --- the load-bearing refusals -----------------------------------------

def test_handedness_from_shape_is_refused():
    with pytest.raises(CH.CharacterizeError) as e:
        CH.refuse_handedness_from_shape(habit="prismatic")
    assert "handedness" in str(e.value).lower()


def test_result_without_measurement_is_refused():
    proxy = CH.request_defect(CH.DefectKind.HYDROXYL)
    assert proxy.status == "REQUESTED"
    with pytest.raises(CH.CharacterizeError):
        CH.refuse_result_without_measurement(proxy)


def test_a_proxy_cannot_be_constructed_as_measured():
    with pytest.raises(CH.CharacterizeError):
        CH.DefectProxy(kind=CH.DefectKind.TWINNING,
                       method_required=CH.Method.CROSSED_POLARIZERS,
                       value=1.0, status="MEASURED")


# --- the plan: low-cost then advanced, all REQUESTED -------------------

def test_plan_is_low_cost_then_advanced_all_requested():
    plan = CH.characterization_plan("QUARTZ")
    assert len(plan) == len(list(CH.Method))
    tiers = [r.tier for r in plan]
    # every low-cost rung precedes every advanced rung
    first_advanced = tiers.index(CH.Tier.ADVANCED)
    assert all(t is CH.Tier.LOW_COST for t in tiers[:first_advanced])
    assert all(t is CH.Tier.ADVANCED for t in tiers[first_advanced:])
    assert all(r.status == "REQUESTED" for r in plan)


def test_plan_requires_a_material_class():
    with pytest.raises(CH.CharacterizeError):
        CH.characterization_plan("")


def test_methods_carry_a_tier_and_what_they_measure():
    assert CH.Method.ARCHIMEDES_DENSITY.tier is CH.Tier.LOW_COST
    assert CH.Method.XRD_LAUE.tier is CH.Tier.ADVANCED
    assert "handedness" in CH.Method.XRD_LAUE.measures.lower()


# --- the report ---------------------------------------------------------

def test_report_measures_nothing():
    r = CH.characterize_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["evidence_class"] == "DERIVED_MATHEMATICS"
    assert r["verdict"] == "CHARACTERIZATION_LADDER_SOFTWARE_ONLY"
