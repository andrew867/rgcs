"""P25 — DDS recipe compiler: FTW round-trip, limits, seal, determinism."""

from __future__ import annotations

import pytest

from r15 import dds_recipes as D


def _dev():
    return D.DDSDeviceSpec(f_clk=100_000_000.0, ftw_bits=32)


def test_dyadic_target_compiles_to_exact_ftw():
    dev = _dev()
    t = D.FrequencyTarget.dyadic(dev, numerator=1, power=4)  # f_clk/16
    ftw = D.frequency_to_ftw(t, dev)
    assert D.ftw_to_frequency(ftw, dev) == pytest.approx(dev.f_clk / 16.0)


def test_ftw_round_trips_within_one_lsb():
    dev = _dev()
    t = D.FrequencyTarget.approximate(1_000_000.0, label="1MHz")
    ftw = D.frequency_to_ftw(t, dev)
    back = D.ftw_to_frequency(ftw, dev)
    assert abs(back - 1_000_000.0) <= dev.freq_lsb


def test_word_to_ftw_to_word_is_identity():
    dev = _dev()
    for ftw in (1, 12345, 2 ** 30):   # all below Nyquist (ftw < 2**31)
        f = D.ftw_to_frequency(ftw, dev)
        t = D.FrequencyTarget.approximate(f, label="rt")
        assert D.frequency_to_ftw(t, dev) == ftw


def test_over_nyquist_is_refused():
    dev = _dev()
    with pytest.raises(D.DDSError):
        t = D.FrequencyTarget.approximate(dev.nyquist * 1.5, label="hi")
        D.frequency_to_ftw(t, dev)


def test_compile_sweep_bounds_quantization_error():
    dev = _dev()
    recipe = D.compile_sweep(dev, 1e5, 5e6, 32, recipe_id="sw")
    assert len(recipe.steps) == 32
    assert recipe.max_quantization_error() <= dev.freq_lsb * 1.0001


def test_seal_is_deterministic_and_changes_on_edit():
    dev = _dev()
    r1 = D.compile_sweep(dev, 1e5, 5e6, 8, recipe_id="sw")
    r2 = D.compile_sweep(dev, 1e5, 5e6, 8, recipe_id="sw")
    assert r1.seal() == r2.seal()
    r3 = D.compile_sweep(dev, 1e5, 6e6, 8, recipe_id="sw")
    assert r3.seal() != r1.seal()


def test_report_claims_nothing_measured():
    r = D.dds_recipes_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
