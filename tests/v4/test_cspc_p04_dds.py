"""P04 (A12-A17): DDS/NCO mathematics, backends, phase closure, clock
uncertainty, RF safety.

Acceptance matrix: the abstract 36-bit/2.45 GHz model is exact; the
practical backend uses realizable clocks and reports quantization
error; phase closure uses rational arithmetic; no 2.45 GHz open
radiation hardware is required.
"""
from __future__ import annotations

from fractions import Fraction

import pytest


# --- A12 abstract reference ---------------------------------------------

def test_abstract_36bit_lsb_is_the_source_number_exactly():
    """The source's 'fractal relationship' 0.0356521923... is the LSB
    of a 36-bit accumulator at 2.45 GHz, in HERTZ (CSPC-CORR-002)."""
    from cspc.dds import ABSTRACT_BITS, ABSTRACT_CLOCK_HZ, lsb_hz
    assert ABSTRACT_BITS == 36
    assert lsb_hz() == Fraction("0.03565219230949878692626953125")
    assert lsb_hz() == ABSTRACT_CLOCK_HZ / 2 ** 36


def test_dds_output_equation_is_exact():
    from cspc.dds import plan
    p = plan("1000", "XO_100MHZ", 32)
    assert p.realized_hz == Fraction(p.tuning_word) * p.clock_hz / 2 ** 32


def test_tuning_word_refuses_above_nyquist():
    from cspc.dds import DDSError, tuning_word
    with pytest.raises(DDSError):
        tuning_word(60_000_000, 100_000_000, 32)


# --- A13 practical backends ---------------------------------------------

def test_backends_report_quantization_error_and_are_realizable():
    from cspc.dds import REALIZABLE_CLOCKS, backend_comparison
    rep = backend_comparison("20480", bits=32)
    assert set(rep["backends"]) == set(REALIZABLE_CLOCKS)
    for name, row in rep["backends"].items():
        assert "relative_error_ppm" in row
        assert row["measured_hz"] is None       # never fabricated
        assert isinstance(row["tuning_word"], int)


def test_requested_realized_measured_are_three_separate_fields():
    from cspc.dds import plan
    d = plan("20480", "XO_100MHZ", 32).to_dict()
    assert d["requested_hz"] != d["realized_hz"]   # decimal clock
    assert d["measured_hz"] is None


def test_decimal_clock_cannot_represent_the_binary_family_exactly():
    from cspc.dds import exact_clocks_for
    rep = exact_clocks_for(["4096", "20480", "40960", "32768"])
    assert "XO_100MHZ" in rep["inexact_on"]
    assert "XO_125MHZ" in rep["inexact_on"]


def test_binary_reference_clock_makes_the_family_exact():
    """Exactness is an engineering choice of oscillator, not a fact
    about nature."""
    from cspc.dds import exact_clocks_for, plan
    rep = exact_clocks_for(["4096", "20480", "40960", "32768"])
    assert "XO_BINARY_2POW26" in rep["exact_on"]
    for t in ("4096", "20480", "40960", "32768"):
        assert plan(t, "XO_BINARY_2POW26", 32).exact


# --- A14 phase closure ---------------------------------------------------

def test_closure_is_computed_on_realized_not_requested():
    """Using requested frequencies would report a closure the hardware
    cannot deliver."""
    from cspc.dds import compile_recipe
    r = compile_recipe(["4096", "20480", "40960"], "XO_100MHZ", 32)
    assert r["closure_computed_on"] == "realized frequencies"
    assert r["closure_window_s_realized"] != \
        r["closure_window_s_requested"]
    assert r["all_exact"] is False


def test_binary_clock_restores_the_ideal_closure_window():
    from cspc.dds import compile_recipe
    r = compile_recipe(["4096", "20480", "40960"],
                       "XO_BINARY_2POW26", 32)
    assert r["all_exact"] is True
    assert Fraction(r["closure_window_s_realized"]) == \
        Fraction(r["closure_window_s_requested"]) == Fraction(1, 4096)


def test_recipe_carries_the_arithmetic_firewall():
    from cspc.dds import compile_recipe
    r = compile_recipe(["4096", "20480"], "XO_BINARY_2POW26", 32)
    assert "says nothing about whether a specimen responds" in \
        r["claim_boundary"]


# --- A15 shared clock ----------------------------------------------------

def test_clock_error_scales_absolutes_but_not_ratios():
    from cspc.dds import ClockModel, shared_clock_uncertainty
    cm = ClockModel(Fraction(100_000_000), Fraction(1, 100_000))
    u = shared_clock_uncertainty(["4096", "20480"], cm)
    assert u["ratios_immune_to_clock_error"] is True
    assert abs(u["tones"][0]["relative_error_ppm"] - 10.0) < 1e-9


# --- A17 RF safety -------------------------------------------------------

def _base_plan(**kw):
    from cspc.rf_safety import RFPlan
    args = dict(id="P", frequency_hz=Fraction(20480),
                enclosure="SHIELDED", output="PIEZO",
                max_power_w=Fraction(1, 10), isolated_supply=True)
    args.update(kw)
    return RFPlan(**args)


def test_open_2g4_radiator_is_refused():
    from cspc.rf_safety import approve
    v = approve(_base_plan(frequency_hz=Fraction(2_450_000_000),
                           output="ANTENNA", enclosure="OPEN"))
    assert not v.approved
    assert any("open 2.45 GHz radiation" in r.lower() or
               "2.4-2.5 ghz" in r.lower() for r in v.refusals)


def test_biological_exposure_is_refused():
    from cspc.rf_safety import approve
    v = approve(_base_plan(biological_target=True))
    assert not v.approved
    assert any("biological" in r.lower() for r in v.refusals)


def test_mains_and_non_isolated_supply_are_refused():
    from cspc.rf_safety import approve
    assert not approve(_base_plan(mains_constructed=True)).approved
    assert not approve(_base_plan(isolated_supply=False)).approved


def test_there_is_no_override_flag():
    """Following the v4.3 lifecycle precedent: no force flag exists."""
    import inspect

    from cspc import rf_safety
    src = inspect.getsource(rf_safety)
    for bad in ("force=", "override=", "ignore_safety"):
        assert bad not in src


def test_require_approved_raises_on_refusal():
    from cspc.rf_safety import SafetyRefusal, require_approved
    with pytest.raises(SafetyRefusal):
        require_approved(_base_plan(frequency_hz=Fraction(2_450_000_000),
                                    output="ANTENNA"))


def test_endorsed_architecture_has_no_radiator_and_is_untested():
    from cspc.rf_safety import ENDORSED_ARCHITECTURE
    assert ENDORSED_ARCHITECTURE["rf_radiator"].startswith("NONE")
    assert "UNTESTED" in ENDORSED_ARCHITECTURE["physical_status"]


def test_low_frequency_piezo_plan_is_approved_with_conditions():
    from cspc.rf_safety import approve
    v = approve(_base_plan())
    assert v.approved
    assert any("stop immediately" in c for c in v.conditions)
    assert any("thermal artifact" in c for c in v.conditions)
