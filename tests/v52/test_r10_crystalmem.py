"""R10.6 — the fading-memory crystal shift register, as hypothesis.

Every test here is written to be *capable of failing*: for each physical
claim there is an input that would flip the assertion. The load-bearing
ones are the firewall tests -- that the decay curve alone cannot tell a
memory from ordinary relaxation, and that a destructive read without a
refresh loses the data -- because those are what stop a decaying echo
from being mistaken for storage.
"""

from __future__ import annotations

import math
from dataclasses import replace
from fractions import Fraction as F

import pytest

from r10 import crystalmem as C


# --- module discipline -------------------------------------------------

def test_module_is_exported_and_sorted():
    import r10
    assert "crystalmem" in r10.__all__
    assert r10.__all__ == sorted(r10.__all__)


def test_status_is_from_the_contract_and_not_exotic():
    assert C.CLAIM_STATUS == "BENCH_TEST_REQUIRED"
    assert C.CLAIM_STATUS in C.CONTRACT_STATUSES
    for s in C.CONTRACT_STATUSES:
        assert "MEASURED" != s
        assert "REPLICATED" != s


def test_nothing_is_measured_and_validation_is_disclaimed():
    assert C.MEASURED_HERE == "nothing"
    assert C.VALIDATION == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert C.HARDWARE_STATUS.startswith("DEFERRED")


# --- 1. the retention window ------------------------------------------

def test_retention_window_matches_the_formula():
    """t_max = tau * ln(A0 / threshold). Falsifiable: any other closed
    form for t_max would fail this against the direct log."""
    tau = 1.0
    thr = float(C.READ_THRESHOLD)
    t_max = C.retention_window(tau)
    assert t_max == pytest.approx(tau * math.log(1.0 / thr))
    assert t_max / tau == pytest.approx(math.log(1.0 / thr))


def test_amplitude_at_the_window_edge_equals_the_threshold():
    tau = 3.0
    t_max = C.retention_window(tau)
    assert C.retention_amplitude(t_max, tau) == pytest.approx(
        float(C.READ_THRESHOLD))


def test_recoverable_flips_across_the_window():
    """A bit is readable just inside the window and not just outside it.
    If retention did not decay this could never flip."""
    tau = 2.0
    t_max = C.retention_window(tau)
    assert C.recoverable(t_max * 0.999, tau)
    assert not C.recoverable(t_max * 1.001, tau)


def test_the_window_scales_with_tau():
    """Double the time constant, double the window. A window that
    ignored tau would fail here."""
    assert C.retention_window(2.0) == pytest.approx(
        2.0 * C.retention_window(1.0))


def test_retention_refuses_bad_inputs():
    with pytest.raises(ValueError):
        C.retention_amplitude(1.0, 0.0)
    with pytest.raises(ValueError):
        C.retention_amplitude(-1.0, 1.0)
    with pytest.raises(ValueError):
        C.retention_window(-1.0)


def test_window_refused_when_write_is_below_threshold():
    with pytest.raises(ValueError):
        C.retention_window(1.0, a0=float(C.READ_THRESHOLD) / 2)


# --- 2. destructive read and refresh ----------------------------------

def _fresh_readable_bit(value=1, tau=1.0, dt=0.1):
    b = C.write_bit(value)
    b = C.age_bit(b, tau, dt)          # aged but still well above threshold
    assert b.amplitude > float(C.READ_THRESHOLD)
    return b


def test_a_readable_bit_reads_back_its_value():
    b = _fresh_readable_bit(value=1)
    r = C.destructive_read(b)
    assert r.recovered and r.value == 1


def test_read_without_refresh_loses_the_data():
    """The defining property of a memory cell over a passive echo: the
    read consumes the state, so a second read finds nothing. If the read
    were non-destructive the residual would still be readable and this
    would fail."""
    b = _fresh_readable_bit(value=1)
    first = C.destructive_read(b)
    assert first.recovered and first.value == 1
    assert first.residual.amplitude == 0.0
    second = C.destructive_read(first.residual)
    assert not second.recovered
    assert second.value is None


def test_refresh_after_read_persists_the_data():
    """A refresh (rewrite) restores the cell, so the next read succeeds.
    Falsifiable: if refresh did not restore amplitude, this read fails."""
    b = _fresh_readable_bit(value=1)
    first = C.destructive_read(b)
    restored = C.refresh(first.residual)
    second = C.destructive_read(restored)
    assert second.recovered and second.value == 1


def test_a_faded_bit_below_threshold_is_not_recovered():
    """Age a bit past its window and the read fails. If retention did not
    fade this would wrongly recover."""
    b = C.write_bit(1)
    b = C.age_bit(b, tau_s=1.0, dt_s=C.retention_window(1.0) * 1.01)
    r = C.destructive_read(b)
    assert not r.recovered


def test_destructive_read_forces_refresh_flag():
    assert C.refresh_required(True) is True
    assert C.refresh_required(False) is False


def test_bad_stored_bit_is_refused():
    with pytest.raises(ValueError):
        C.StoredBit(1.0, 2, 0.0)       # value not a bit
    with pytest.raises(ValueError):
        C.StoredBit(-1.0, 1, 0.0)      # negative amplitude


# --- 3. shift register: decay plus dispersion -------------------------

def _reg(dispersion=50.0):
    return C.ShiftRegister(n_stages=64, stage_latency_s=0.1, tau_s=1.0,
                           dispersion_stages=dispersion)


def test_fidelity_is_strictly_decreasing_in_stage():
    reg = _reg()
    vals = [C.stage_fidelity(reg, k) for k in range(reg.n_stages + 1)]
    assert all(a > b for a, b in zip(vals, vals[1:]))


def test_stage_zero_fidelity_is_the_write_amplitude():
    reg = _reg()
    assert C.stage_fidelity(reg, 0) == pytest.approx(reg.a0)


def test_last_readable_stage_is_a_true_boundary():
    """Fidelity is above threshold at the last readable stage and below
    at the next one. If the boundary search were off by one this fails."""
    reg = _reg()
    last = C.last_readable_stage(reg)
    thr = float(reg.threshold)
    assert C.stage_fidelity(reg, last) > thr
    assert C.stage_fidelity(reg, last + 1) <= thr


def test_dispersion_strictly_reduces_the_number_of_readable_stages():
    """Turning dispersion on must cost stages. If dispersion did nothing
    (or helped) this would fail -- it is the whole reason a shift
    register is worse than a single cell."""
    with_disp = C.last_readable_stage(_reg(dispersion=50.0))
    without_disp = C.last_readable_stage(_reg(dispersion=math.inf))
    assert with_disp < without_disp


def test_no_dispersion_matches_pure_decay():
    """With dispersion off the surviving-stage boundary is exactly the
    decay-only prediction floor(tau/latency * ln(1/thr))."""
    reg = _reg(dispersion=math.inf)
    thr = float(reg.threshold)
    k_decay = math.floor(reg.tau_s / reg.stage_latency_s * math.log(1 / thr))
    assert C.last_readable_stage(reg) == k_decay


def test_capacity_counts_the_readable_prefix():
    reg = _reg()
    assert C.readable_stage_count(reg) == C.last_readable_stage(reg) + 1


def test_register_refuses_bad_parameters():
    with pytest.raises(ValueError):
        C.ShiftRegister(0, 0.1, 1.0, 50.0)
    with pytest.raises(ValueError):
        C.ShiftRegister(8, 0.0, 1.0, 50.0)
    with pytest.raises(ValueError):
        C.ShiftRegister(8, 0.1, 1.0, 0.0)
    with pytest.raises(ValueError):
        C.stage_fidelity(_reg(), 999)


# --- 4. the firewall: memory vs ordinary relaxation -------------------

def test_decay_curves_are_indistinguishable():
    """With equal time constants the memory envelope and the ordinary
    relaxation envelope are the same curve. This is the core firewall:
    the decay curve carries no bit about which model is right."""
    times = [i * 0.05 for i in range(200)]
    r = C.decay_curves_indistinguishable(1.0, times)
    assert r["indistinguishable"]
    assert r["max_abs_diff"] == pytest.approx(0.0, abs=1e-12)


def test_the_two_amplitude_functions_agree_pointwise():
    for t in (0.0, 0.5, 1.0, 3.7, 10.0):
        assert C.memory_amplitude(t, 2.0) == \
            C.ordinary_relaxation_amplitude(t, 2.0)


def test_the_null_readout_is_independent_of_what_was_written():
    """A passive relaxation carries no pattern: its thresholded readout
    is the same fixed shape whatever you 'wrote'. If the null somehow
    depended on the input it would be encoding information, and this
    fails."""
    a = C.read_pattern_relaxation_null([1, 0, 1, 1, 0, 1])
    b = C.read_pattern_relaxation_null([0, 0, 0, 0, 0, 0])
    assert a == b


def test_ordered_readout_distinguishes_the_models():
    """Only ordered readout separates them: the memory model returns the
    pattern in order (match 1), the null cannot for a non-monotone
    pattern. If the memory readout scrambled the order, or the null
    happened to match, this fails."""
    pattern = [1, 0, 1, 1, 0, 1]
    r = C.ordered_readout_distinguishes(pattern)
    assert r["memory_match"] == F(1)
    assert r["null_match"] < F(1)
    assert r["envelope_alone_distinguishes"] is False


def test_match_fraction_is_exact():
    assert C.match_fraction([1, 0, 1], [1, 0, 1]) == F(1)
    assert C.match_fraction([1, 0, 1], [1, 1, 1]) == F(2, 3)


def test_match_fraction_refuses_length_mismatch():
    with pytest.raises(ValueError):
        C.match_fraction([1, 0], [1, 0, 1])


def test_memory_claim_is_refused_without_delayed_readout():
    with pytest.raises(C.MemoryClaimRefused) as e:
        C.refuse_memory_claim_without_delayed_readout()
    msg = str(e.value)
    assert "ordinary material relaxation" in msg
    assert "ordered delayed readout" in msg
    assert "point-for-point identical" in msg
    assert "nothing here is measured" in msg


def test_null_model_report_ties_it_together():
    times = [i * 0.1 for i in range(65)]
    r = C.null_model_report(1.0, times, [1, 0, 1, 1, 0, 1])
    assert r["decay_curve"]["indistinguishable"]
    assert r["ordered_readout"]["memory_match"] == F(1)
    assert r["measured_here"] == "nothing"


# --- 5. the schema record ---------------------------------------------

def test_build_hypothesis_fills_the_schema():
    reg = _reg()
    hyp = C.build_hypothesis(reg)
    # every schema field is present and typed
    for fld in ("memory_id", "specimen", "state_variable", "write_stimulus",
                "transport_equation", "retention_model", "dispersion_model",
                "read_operator", "destructive_read", "refresh_required",
                "capacity", "fidelity", "latency", "controls",
                "damage_thresholds", "observables", "status"):
        assert hasattr(hyp, fld)
    assert hyp.destructive_read is True
    assert hyp.refresh_required is True
    assert hyp.status == "BENCH_TEST_REQUIRED"


def test_capacity_fidelity_latency_are_computed_from_the_model():
    reg = _reg()
    hyp = C.build_hypothesis(reg)
    assert hyp.capacity["readable_stage_count"] == C.readable_stage_count(reg)
    assert hyp.capacity["last_readable_stage"] == C.last_readable_stage(reg)
    assert hyp.fidelity["at_stage_0"] == pytest.approx(reg.a0)
    assert hyp.latency["per_stage_s"] == reg.stage_latency_s
    assert hyp.latency["retention_window_s"] == pytest.approx(
        C.retention_window(reg.tau_s))


def test_destructive_read_without_refresh_is_a_schema_violation():
    """The schema's load-bearing rule. A destructive read that does not
    require a refresh is not a memory. This must raise."""
    with pytest.raises(C.SchemaViolation):
        C.CrystalMemory(
            memory_id="x", specimen="x", state_variable="x",
            write_stimulus="x", transport_equation="x", retention_model="x",
            dispersion_model="x", read_operator="x",
            destructive_read=True, refresh_required=False,
            capacity={}, fidelity={}, latency={}, controls=(),
            damage_thresholds=(), observables=())


def test_an_invented_status_is_a_schema_violation():
    with pytest.raises(C.SchemaViolation):
        C.CrystalMemory(
            memory_id="x", specimen="x", state_variable="x",
            write_stimulus="x", transport_equation="x", retention_model="x",
            dispersion_model="x", read_operator="x",
            destructive_read=True, refresh_required=True,
            capacity={}, fidelity={}, latency={}, controls=(),
            damage_thresholds=(), observables=(), status="MEMORY_CONFIRMED")


def test_controls_and_damage_thresholds_are_named_but_undriven():
    """Named, with provenance, and carrying no measured numbers -- no
    specimen is driven."""
    names = {c.name for c in C.CONTROLS}
    assert "SECOND_UNTREATED_SPECIMEN" in names
    assert "DESTRUCTIVE_READ_THEN_REFRESH" in names
    for d in C.DAMAGE_THRESHOLDS:
        assert d.mechanism and d.control and d.source


def test_report_disclaims_and_measures_nothing():
    r = C.crystalmem_report(_reg())
    assert r["status"] == "BENCH_TEST_REQUIRED"
    assert r["measured_here"] == "nothing"
    assert r["validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert "not a memory until" in r["the_firewall"]
    assert "Nothing has been measured" in r["what_this_does_not_say"]
    assert r["null_model"]["decay_curve"]["indistinguishable"]
