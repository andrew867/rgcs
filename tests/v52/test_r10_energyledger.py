"""P17 — the energy ontology, the first-law ledger, and the Carnot bound.

Every test here has an input that makes it fail. The category tests
fail if ``__add__`` stops discriminating; the balance tests fail if a
term is dropped or perturbed by one part in 10^21; the Carnot tests
fail if the bound is computed in floating point and a tie is decided
the wrong way.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction as F

import pytest

from r10 import energyledger as E
from r10.energyledger import Energy, EnergyKind as K


# --- the ontology is a type system, not a naming convention ------------

def test_adding_different_categories_is_refused():
    """The load-bearing behaviour. Reservoir energy plus heat is not a
    quantity of anything."""
    heat = Energy(K.HEAT, F(1))
    work = Energy(K.WORK, F(1))
    res = Energy(K.RESERVOIR_ENERGY, F(1), temperature_k=F(300))
    for a, b in ((heat, work), (work, res), (heat, res),
                 (res, Energy(K.DISSIPATION, F(1)))):
        with pytest.raises(E.EnergyCategoryError):
            a + b


def test_adding_the_same_category_works_and_is_exact():
    a = Energy(K.HEAT, F(1, 3))
    b = Energy(K.HEAT, F(1, 6))
    assert (a + b).joules == F(1, 2)
    assert (a + b).kind is K.HEAT


def test_subtraction_also_discriminates_category():
    with pytest.raises(E.EnergyCategoryError):
        Energy(K.HEAT, F(2)) - Energy(K.WORK, F(1))


def test_total_refuses_a_mixed_iterable():
    with pytest.raises(E.EnergyCategoryError):
        E.total([Energy(K.HEAT, F(1)), Energy(K.WORK, F(1))])


def test_total_of_an_empty_iterable_is_refused():
    """An empty sum has no determinate category, so it is not zero."""
    with pytest.raises(ValueError):
        E.total([])


def test_as_work_refuses_every_non_work_category():
    assert Energy(K.WORK, F(5)).as_work().joules == F(5)
    for q in (Energy(K.HEAT, F(5)),
              Energy(K.STORED_ENERGY, F(5)),
              Energy(K.DISSIPATION, F(5)),
              Energy(K.RESERVOIR_ENERGY, F(5), temperature_k=F(300))):
        with pytest.raises(E.EnergyCategoryError):
            q.as_work()


def test_reservoir_energy_without_a_temperature_is_refused():
    """An unassessable quantity is the one that gets treated as free."""
    with pytest.raises(ValueError):
        Energy(K.RESERVOIR_ENERGY, F(1))
    # ... but heat and work need no temperature to be well formed.
    assert Energy(K.HEAT, F(1)).temperature_k is None


def test_negative_and_nonpositive_inputs_are_refused():
    with pytest.raises(ValueError):
        Energy(K.WORK, F(-1))
    with pytest.raises(ValueError):
        Energy(K.RESERVOIR_ENERGY, F(1), temperature_k=F(0))
    with pytest.raises(ValueError):
        Energy(K.RESERVOIR_ENERGY, F(1), temperature_k=F(-5))


def test_state_and_transit_kinds_partition_the_ontology():
    assert E.STATE_KINDS.isdisjoint(E.TRANSIT_KINDS)
    assert E.STATE_KINDS | E.TRANSIT_KINDS == set(K)


# --- the first law, exactly --------------------------------------------

def test_fixture_balances_to_exactly_zero():
    """Exact rational equality, not approx. A 1e-21 J perturbation
    below fails this test and would pass a float tolerance."""
    r = E.quantum_otto_fixture().first_law_residual()
    assert r == 0
    assert isinstance(r, F)


def test_one_zeptojoule_of_missing_energy_is_caught():
    """The input that makes the balance test fail.

    A term short by 1e-21 J out of 1e-18 J -- one part in a thousand,
    but stated exactly -- must be reported, not absorbed.
    """
    fx = E.quantum_otto_fixture()
    broken = replace(fx, dissipation=Energy(
        K.DISSIPATION, fx.dissipation.joules - F(1, 10 ** 21)))
    assert broken.first_law_residual() == F(1, 10 ** 21)
    with pytest.raises(E.FirstLawViolation):
        broken.check_first_law()


def test_dropping_the_dissipation_term_breaks_the_balance():
    """The commonest way a ledger appears to close when it does not."""
    fx = E.quantum_otto_fixture()
    broken = replace(fx, dissipation=Energy(K.DISSIPATION, F(0)))
    assert broken.first_law_residual() > 0
    with pytest.raises(E.FirstLawViolation):
        broken.check_first_law()


def test_the_ledger_refuses_a_state_quantity_as_a_cycle_term():
    """Reservoir energy is not a term in a cycle balance."""
    fx = E.quantum_otto_fixture()
    with pytest.raises(E.EnergyCategoryError):
        replace(fx, heat_in=Energy(K.RESERVOIR_ENERGY, F(1),
                                   temperature_k=F(300)))
    with pytest.raises(E.EnergyCategoryError):
        replace(fx, work_out=Energy(K.STORED_ENERGY, F(1)))


def test_the_ledger_refuses_heat_where_work_belongs():
    fx = E.quantum_otto_fixture()
    with pytest.raises(E.EnergyCategoryError):
        replace(fx, work_out=Energy(K.HEAT, fx.work_out.joules))


def test_reversed_reservoir_temperatures_are_refused():
    fx = E.quantum_otto_fixture()
    with pytest.raises(ValueError):
        replace(fx, t_hot_k=F(100), t_cold_k=F(200))


# --- efficiency and the Carnot bound -----------------------------------

def test_fixture_efficiency_is_the_stated_twelve_percent():
    assert E.quantum_otto_fixture().efficiency() == F(12, 100)


def test_carnot_bound_is_exact_rational():
    b = E.carnot_efficiency(F(200), F(300))
    assert b == F(1, 3)
    assert isinstance(b, F)


def test_carnot_bound_is_zero_at_equal_temperatures():
    """Kelvin-Planck, as a return value."""
    assert E.carnot_efficiency(F(300), F(300)) == 0


def test_carnot_bound_approaches_one_only_as_the_sink_approaches_zero():
    assert E.carnot_efficiency(F(1), F(10 ** 6)) < 1
    assert E.carnot_efficiency(F(1, 10 ** 9), F(300)) < 1


def test_fixture_sits_under_its_carnot_bound():
    fx = E.quantum_otto_fixture()
    assert fx.efficiency() < fx.carnot_bound()
    assert fx.check_carnot() == F(1, 3)


def test_an_efficiency_above_the_bound_is_refused():
    """The input that makes the previous test fail: 40% between 200 K
    and 300 K, where the bound is 33.3%."""
    with pytest.raises(E.CarnotBoundExceeded):
        E.check_efficiency_claim(F(40, 100), F(200), F(300))
    fx = E.quantum_otto_fixture()
    over = replace(fx, work_out=Energy(K.WORK, fx.heat_in.joules
                                       * F(40, 100)))
    with pytest.raises(E.CarnotBoundExceeded):
        over.check_carnot()


def test_the_bound_is_decided_exactly_at_the_boundary():
    """Exactly at the bound is permitted; any excess at all is not.

    The excess used here, 1e-18, is below float64 resolution at this
    magnitude -- ``float(bound + 1e-18) == float(bound)`` -- so a
    float implementation of the comparison passes the claim and this
    test fails. That is the point of computing the bound as an exact
    rational.
    """
    bound = E.carnot_efficiency(F(200), F(300))
    assert bound == F(1, 3)
    assert E.check_efficiency_claim(bound, F(200), F(300)) == bound

    excess = F(1, 10 ** 18)
    assert float(bound + excess) == float(bound), (
        "this test is only meaningful while the excess is invisible "
        "to float64")
    with pytest.raises(E.CarnotBoundExceeded):
        E.check_efficiency_claim(bound + excess, F(200), F(300))


def test_declaring_the_reservoir_non_thermal_does_not_lift_the_refusal():
    """A super-Carnot number against a squeezed bath means the wrong
    bound was quoted, not that this bound was beaten."""
    with pytest.raises(E.CarnotBoundExceeded) as e:
        E.check_efficiency_claim(F(9, 10), F(200), F(300),
                                 reservoirs_are_thermal=False)
    assert "not the applicable bound" in str(e.value)


def test_reversed_or_nonpositive_temperatures_are_refused():
    with pytest.raises(ValueError):
        E.carnot_efficiency(F(300), F(200))
    with pytest.raises(ValueError):
        E.carnot_efficiency(F(0), F(300))
    with pytest.raises(ValueError):
        E.carnot_efficiency(F(200), F(-300))


def test_zero_heat_in_gives_undefined_not_infinite_efficiency():
    fx = E.quantum_otto_fixture()
    empty = E.CycleLedger(
        label="null", heat_in=Energy(K.HEAT, F(0)),
        work_out=Energy(K.WORK, F(0)),
        heat_rejected=Energy(K.HEAT, F(0)),
        dissipation=Energy(K.DISSIPATION, F(0)),
        t_hot_k=fx.t_hot_k, t_cold_k=fx.t_cold_k)
    assert empty.first_law_residual() == 0
    with pytest.raises(ZeroDivisionError):
        empty.efficiency()


# --- availability is not magnitude -------------------------------------

def test_extractable_work_from_an_isothermal_reservoir_is_exactly_zero():
    """The whole point. A joule or a yottajoule, the answer is 0."""
    for magnitude in (F(1), F(10 ** 24)):
        res = Energy(K.RESERVOIR_ENERGY, magnitude,
                     temperature_k=F(290))
        assert E.available_work_bound(res, F(290)).joules == 0


def test_extractable_work_scales_with_the_gradient_not_the_magnitude():
    """Two reservoirs, same energy, different temperature: different
    availability. Fails if availability is read off magnitude."""
    warm = Energy(K.RESERVOIR_ENERGY, F(1000), temperature_k=F(400))
    hot = Energy(K.RESERVOIR_ENERGY, F(1000), temperature_k=F(800))
    assert (E.available_work_bound(warm, F(200)).joules
            == F(1000) * F(1, 2))
    assert (E.available_work_bound(hot, F(200)).joules
            == F(1000) * F(3, 4))


def test_available_work_bound_returns_work_not_a_relabelled_reservoir():
    res = Energy(K.RESERVOIR_ENERGY, F(1000), temperature_k=F(400))
    out = E.available_work_bound(res, F(200))
    assert out.kind is K.WORK
    assert out.as_work() is out


def test_available_work_bound_refuses_non_reservoir_inputs():
    with pytest.raises(E.EnergyCategoryError):
        E.available_work_bound(Energy(K.HEAT, F(1)), F(200))
    with pytest.raises(E.EnergyCategoryError):
        E.available_work_bound(Energy(K.STORED_ENERGY, F(1)), F(200))


def test_a_hotter_sink_than_the_reservoir_is_refused():
    res = Energy(K.RESERVOIR_ENERGY, F(1000), temperature_k=F(300))
    with pytest.raises(ValueError):
        E.available_work_bound(res, F(400))


def test_isothermal_extraction_claim_is_refused_by_name():
    res = Energy(K.RESERVOIR_ENERGY, F(10 ** 11), temperature_k=F(290),
                 label="a litre of seawater")
    with pytest.raises(E.ExtractionRefused) as e:
        E.refuse_extraction_without_gradient(res, F(290))
    assert "exactly zero" in str(e.value)
    # with a gradient it does not refuse -- the refusal is specific,
    # not blanket
    E.refuse_extraction_without_gradient(res, F(200))


def test_vacuum_energy_as_a_source_is_refused_unconditionally():
    with pytest.raises(E.ExtractionRefused) as e:
        E.refuse_vacuum_energy_as_source()
    msg = str(e.value)
    assert "ground state" in msg
    assert "force is not a fuel" in msg
    # no argument makes it permit the claim
    with pytest.raises(E.ExtractionRefused):
        E.refuse_vacuum_energy_as_source(joules=1e40, permitted=True)


# --- literature entries must be sourced --------------------------------

def test_a_literature_entry_without_a_source_is_refused():
    """An unsourced number is an invented number."""
    with pytest.raises(ValueError):
        E.LiteratureEngine("mystery engine", "unspecified", "Otto",
                           0.5, source="   ", precision="exact")


def test_a_literature_entry_without_a_precision_is_refused():
    with pytest.raises(ValueError):
        E.LiteratureEngine("mystery engine", "unspecified", "Otto",
                           0.5, source="Journal 1, 1 (2000)",
                           precision="")


def test_a_literature_efficiency_at_or_above_unity_is_refused():
    for bad in (1.0, 1.5):
        with pytest.raises(ValueError):
            E.LiteratureEngine("impossible", "x", "Otto", bad,
                               source="Journal 1, 1 (2000)",
                               precision="as published")


def test_every_registered_engine_carries_a_source_and_a_precision():
    assert E.LITERATURE_ENGINES
    for eng in E.LITERATURE_ENGINES:
        assert eng.source.strip()
        assert eng.precision.strip()


def test_the_squeezed_reservoir_entry_quotes_no_efficiency():
    """It exceeds the standard bound, so quoting it against that bound
    would be the category error the module exists to prevent."""
    squeezed = [e for e in E.LITERATURE_ENGINES
                if "squeezed" in e.label][0]
    assert squeezed.reported_efficiency is None
    assert "not thermal" in squeezed.note


# --- claim hygiene ------------------------------------------------------

def test_the_fixture_record_disclaims_measurement():
    rec = E.quantum_otto_fixture().certify()
    assert rec["measured_here"] == "nothing"
    assert rec["evidence_class"] == "ARITHMETIC_ON_A_SYNTHETIC_FIXTURE"
    assert "not a measurement" in rec["what_this_does_not_say"]


def test_the_ontology_record_disclaims_resonator_claims():
    o = E.energy_ontology()
    assert o["measured_here"] == "nothing"
    assert "resonator is a heat engine" in o["what_this_does_not_say"]
    assert "reservoir energy is not a work budget" in \
        o["what_this_does_not_say"]


def test_the_ontology_lists_all_five_kinds():
    o = E.energy_ontology()
    assert set(o["kinds"]) == {"HEAT", "WORK", "RESERVOIR_ENERGY",
                               "STORED_ENERGY", "DISSIPATION"}


def test_certify_runs_both_gates_and_reports_a_positive_margin():
    rec = E.quantum_otto_fixture().certify()
    assert rec["first_law_exact"] is True
    assert rec["carnot_margin"] > 0
    assert rec["dissipated_fraction"] == F(3, 100)
