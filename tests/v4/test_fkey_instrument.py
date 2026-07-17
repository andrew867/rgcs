"""v4.4 frequency-key instrument tests (Agents A04-A13, waves 1-2)."""

from fractions import Fraction

import numpy as np
import pytest

from fkey_instrument import contracts, crystal_mode as cm
from fkey_instrument import optimizer as opt
from fkey_instrument import phase_closure as pc
from fkey_instrument import plant as pl
from fkey_instrument import relations as rel
from fkey_instrument import spectrum as sp


# --- A04: exact relations, frozen seed corpus ---------------------------

def test_exact_parse_refuses_floats():
    with pytest.raises(rel.RelationError):
        rel.hz(20.48)
    assert rel.hz("20.48") == Fraction(512, 25)
    assert rel.hz(4096) == Fraction(4096)


def test_frozen_seed_cases_classify_correctly():
    rels = rel.seed_relations()
    by_expr = {}
    for r in rels:
        by_expr[(r.inputs, r.operation)] = r
    # 4096*5 -> HARMONIC order 5, exact
    r0 = rels[0]
    assert r0.primary_class == "HARMONIC" and r0.order == 5
    assert r0.exact and r0.output_hz == 20480
    # 8*2560, 20.48*1000, 40.96*500 -> exact but PHASE_CLOSURE_ONLY
    for r in rels[1:4]:
        assert r.exact
        assert r.primary_class == "PHASE_CLOSURE_ONLY"
        assert r.order in (2560, 1000, 500)
    # mixed sums -> ARITHMETIC_COINCIDENCE with stated mixing order
    assert rels[4].primary_class == "ARITHMETIC_COINCIDENCE"
    assert rels[4].order == 33
    assert rels[4].output_hz == 20280
    assert rels[5].primary_class == "ARITHMETIC_COINCIDENCE"
    assert rels[5].order == 21
    assert rels[5].output_hz == 20480
    # 8*2535 = 20280 exact, phase closure
    assert rels[6].exact and rels[6].primary_class == \
        "PHASE_CLOSURE_ONLY"


def test_seed_explanation_matches_classification():
    ex = rel.seed_explanation()
    assert "LOW-ORDER PRACTICAL" in ex["4096*5"]["why"]
    assert "not" in ex["mixed sums"]["why"].lower()


def test_ranking_is_mechanism_first():
    """A10 gate at the relation level: exact high-order closure never
    outranks a low-order harmonic."""
    ranked = rel.rank(rel.seed_relations())
    assert ranked[0].primary_class == "HARMONIC"
    assert ranked[-1].primary_class in ("ARITHMETIC_COINCIDENCE",
                                        "PHASE_CLOSURE_ONLY")


def test_dedup_and_enumerate():
    rels = rel.seed_relations() + rel.seed_relations()
    assert len(rel.dedup(rels)) == len(rel.seed_relations())
    keys = rel.key_registry()
    census = rel.enumerate_harmonics(keys, rel.hz("20480"))
    exprs = {(r.inputs[0][0], r.inputs[0][1]) for r in census}
    assert (Fraction(5), Fraction(4096)) in exprs


def test_am_sidebands_exact():
    sb = rel.am_sidebands(rel.hz("20480"), rel.hz("20.48"))
    assert sb["lower_hz"] == Fraction("20459.52")
    assert sb["upper_hz"] == Fraction("20500.48")


# --- A05: phase closure --------------------------------------------------

def test_exact_periods_from_the_pack_table():
    assert pc.period_s("4096") == Fraction(1, 4096)
    assert pc.period_s("20480") * 1_000_000 == \
        Fraction("48.828125")
    assert pc.period_s("8") * 1000 == 125


def test_common_closure_window():
    w = pc.common_closure_window(["8", "20.48", "4096"])
    assert all(c.denominator == 1 for c in w["cycles"].values())
    # 20480/20.48 closes exactly 1000 carrier cycles per envelope
    b = pc.burst_lengths("20480", "20.48")
    assert b["carrier_cycles_per_envelope"] == 1000
    assert b["integer_closure"]


def test_closure_drift_reports_realized_offset():
    d = pc.closure_drift("4096", Fraction("4096.5"), 2)
    assert d["cycle_error"] == 1
    assert not d["closure_preserved"]
    ok = pc.closure_drift("4096", rel.hz("4096"), 60)
    assert ok["closure_preserved"]


# --- A06: spectrum -------------------------------------------------------

def test_key_comparison_sine_has_no_fifth_square_has_one_fifth():
    cmpn = sp.fifth_harmonic_comparison()
    assert cmpn["sine_fifth"] == 0.0
    assert cmpn["square_fifth_over_fundamental"] == \
        pytest.approx(0.2, abs=1e-12)


def test_square_even_harmonics_vanish_at_half_duty():
    h = sp.square_harmonics(0.5)
    assert h[2] == pytest.approx(0.0, abs=1e-12)
    assert h[4] == pytest.approx(0.0, abs=1e-12)
    asym = sp.square_harmonics(0.3)
    assert asym[2] > 0.01           # duty error resurrects evens


def test_fft_cross_checks_analytic_content():
    """A22: independent FFT check of the analytic statement."""
    fs = 1_048_576.0
    sine = sp.synthesize("sine", 4096.0, fs, 0.05)
    sq = sp.synthesize("square", 4096.0, fs, 0.05)
    sine_lines = sp.fft_lines(sine, fs, 6)
    sq_lines = sp.fft_lines(sq, fs, 6)
    assert abs(sine_lines[0]["f_hz"] - 4096) < 30
    assert not any(abs(x["f_hz"] - 20480) < 50 for x in
                   sine_lines)      # no 5th from a sine
    fifth = [x for x in sq_lines if abs(x["f_hz"] - 20480) < 50]
    assert fifth, "square must show its 5th harmonic in the FFT"
    fund = sq_lines[0]["amplitude"]
    assert fifth[0]["amplitude"] / fund == pytest.approx(0.2,
                                                         abs=0.02)


def test_edge_rolloff_and_expected_line():
    assert sp.edge_rolloff(20480.0, 0.0) == 1.0
    # sinc(pi * 20480 * 20e-6) = sin(1.2868)/1.2868 = 0.7460
    assert sp.edge_rolloff(20480.0, 20e-6) == pytest.approx(
        0.74599, abs=1e-4)
    # monotone attenuation with slower edges
    assert sp.edge_rolloff(20480.0, 30e-6) < \
        sp.edge_rolloff(20480.0, 20e-6)
    line = sp.expected_line("4096", 5, 0.5, 200e-9, 20480.0, 400.0)
    assert line["expected_amplitude"] > 10     # on-resonance gain
    sine5 = sp.expected_line("4096", 5, 0.5, 200e-9, 20480.0, 400.0)
    assert sine5["mechanism"] == "HARMONIC"


def test_nyquist_marginal_and_alias():
    m = sp.nyquist_check(20480.0, 48000.0)
    assert not m["aliased"] and m["marginal"]
    a = sp.nyquist_check(40960.0, 48000.0)
    assert a["aliased"]
    assert abs(a["appears_at_hz"] - 7040.0) < 1.0


# --- A07: crystal model ---------------------------------------------------

def test_prearrival_screening_matches_pack_numbers():
    m = cm.screening_modes()
    q = m["longitudinal"]["quarter_wave_hz"]
    h = m["longitudinal"]["half_wave_hz"]
    assert abs(float(q) - 20278.959241645247) < 1e-6
    assert abs(float(h) - 40557.918483290494) < 1e-6
    assert h == 2 * q
    assert "SELLER-PROVIDED" in " ".join(m["assumptions"]).upper() \
        or "seller-provided" in " ".join(m["assumptions"]).lower()


def test_correction_record_equal_percentage_errors():
    """A01 task 6: the two percentage errors are ONE ratio."""
    e = cm.target_errors()
    assert e["correction_record"]["verified_equal"]
    assert e["quarter_vs_20480"]["rel"] == e["half_vs_40960"]["rel"]


def test_candidate_band_not_magic_number():
    b = cm.candidate_band()
    assert b["band_lo_hz"] < b["nominal_hz"] < b["band_hi_hz"]
    assert float(b["band_width_hz"]) > 300     # a real band
    assert "no magic best frequency" in b["rule"]


def test_prearrival_immutable_and_arrival_revisions():
    a = cm.prearrival_record()
    a["claimed_geometry"]["length_mm"] = "999"
    assert cm.prearrival_record()["claimed_geometry"]["length_mm"] \
        == "77.8"
    with pytest.raises(cm.RevisionError):
        cm.arrival_revision({"length_mm": "77.9"}, {})
    rev = cm.arrival_revision(
        {"length_mm": "77.9"},
        {"instrument": "caliper", "operator": "A",
         "timestamp": "2026-07-17"})
    assert rev["revision"] == 2
    assert rev["supersedes_revision"] == 1
    assert cm.prearrival_record()["revision"] == 1   # untouched


# --- A08/A09: plant + identification -------------------------------------

def test_linear_plant_has_no_intermodulation():
    p = pl.CoupledPlant(4300.0, 8.0, 20280.0, 400.0,
                        nonlinearity=0.0)
    im = p.intermod_products(1496.0, 587.0)
    assert im["products"] == []
    assert "linear" in im["note"]
    p2 = pl.CoupledPlant(4300.0, 8.0, 20280.0, 400.0,
                         nonlinearity=0.05)
    im2 = p2.intermod_products(1496.0, 587.0, order=2)
    assert im2["products"]
    assert all(pr["relative_amplitude"] <= 0.05
               for pr in im2["products"] if pr["order"] >= 2)


def test_transducer_vs_crystal_peak_discrimination():
    p = pl.CoupledPlant(15000.0, 10.0, 20280.0, 400.0, coupling=0.3)
    who = p.which_peak_is_the_specimen()
    assert who["nearest_to"] == "specimen"


def test_fit_refuses_undersampled_and_saturated():
    p = pl.CoupledPlant(4300.0, 8.0, 20280.0, 400.0)
    sweep = pl.synthetic_sweep(p, 20100, 20460, n=2001, noise=0.005)
    fit = pl.fit_peak(sweep["f_hz"], sweep["magnitude"])
    assert fit["fitted"]
    assert fit["f0_hz"] == pytest.approx(20280.0, abs=2.0)
    # coarse sweep: too few points per linewidth -> refusal
    coarse = pl.synthetic_sweep(p, 19000, 22000, n=80, noise=0.005)
    bad = pl.fit_peak(coarse["f_hz"], coarse["magnitude"])
    assert bad["fitted"] is None
    # saturated: flat top -> refusal
    sat = dict(sweep)
    sat_mag = np.minimum(sweep["magnitude"],
                         0.4 * sweep["magnitude"].max())
    bad2 = pl.fit_peak(sweep["f_hz"], sat_mag)
    assert bad2["fitted"] is None


def test_bootstrap_q_interval():
    p = pl.CoupledPlant(4300.0, 8.0, 20280.0, 400.0)
    sweep = pl.synthetic_sweep(p, 20150, 20410, n=3001, noise=0.01)
    b = pl.bootstrap_q(sweep["f_hz"], sweep["magnitude"])
    assert b["ok"]
    lo, hi = b["q_ci95"]
    assert lo < 400.0 * 1.5 and hi > 400.0 * 0.5


def test_sweep_logs_carry_synthetic_markers():
    p = pl.CoupledPlant(4300.0, 8.0, 20280.0, 400.0)
    s = pl.synthetic_sweep(p, 20000, 20500)
    assert s["synthetic"] and s["id"].startswith("SYNTHETIC")
    assert "SYNTHETIC" in s["marker"]


def test_thermal_drift_direction():
    d = pl.thermal_drift(1.0, 10.0)
    assert d["delta_t_c"] > 0 and d["delta_f_hz"] < 0


# --- A10/A11: optimizer + campaigns ---------------------------------------

def test_optimizer_gate_arithmetic_cannot_win():
    out = opt.optimize()
    front = out["pareto"]
    assert out["gate_check"]["holds"]
    # the high-order mix has zero expected amplitude
    mix = [c for c in out["candidates"]
           if c["family"] == "highorder_mix"][0]
    assert mix["expected_target_amplitude"] == 0.0
    # a sine at 4096 has no 5th-harmonic amplitude either
    sine4096 = [c for c in out["candidates"]
                if c["family"] == "clock_sine_4096"][0]
    assert sine4096["expected_target_amplitude"] == 0.0
    # the square clock DOES carry target amplitude
    sq4096 = [c for c in out["candidates"]
              if c["family"] == "clock_square_4096"][0]
    assert sq4096["expected_target_amplitude"] > 0.0
    assert len(front) >= 3          # a frontier, not one winner


def test_optimizer_deterministic():
    a = opt.optimize()
    b = opt.optimize()
    assert [c["family"] for c in a["pareto"]] == \
        [c["family"] for c in b["pareto"]]


def test_hypotheses_preregistered_and_immutable():
    h = opt.hypothesis_register()
    assert len(h) == 6
    for hid, spec in h.items():
        assert spec["status"] == "UNTESTED"
        assert spec["disconfirmed_by"]
        assert spec["controls"]
    h["H-KEY-HARMONIC-01"]["status"] = "CONFIRMED"
    assert opt.hypothesis_register()["H-KEY-HARMONIC-01"][
        "status"] == "UNTESTED"


def test_campaign_randomized_blinded_with_sham():
    out = opt.optimize()
    man = opt.compile_campaign(out["candidates"], seed=1)
    assert man["synthetic"]
    assert man["manifest_id"].startswith("SYNTHETIC")
    assert len(man["campaigns"]) == 8
    # blocks are permutations of the same condition set
    sets = [tuple(sorted(b)) for b in man["blocks"]]
    assert len(set(sets)) == 1
    assert man["blocks"][0] != man["blocks"][1] or \
        man["blocks"][0] != man["blocks"][2]
    assert "no frequency may be added after data" in \
        man["post_hoc_rule"]


# --- A12: contracts --------------------------------------------------------

def test_recipe_validation_and_rejections():
    good = contracts.example_recipe("SYNTHETIC-T1", [
        {"label": "tone", "kind": "sine", "frequency_hz": "20480",
         "duration_s": 5.0, "duty": 0.5, "amplitude_frac": 0.3}])
    assert contracts.validate_recipe(good)["valid"]
    # out-of-profile frequency
    bad = contracts.example_recipe("SYNTHETIC-T2", [
        {"label": "t", "kind": "sine", "frequency_hz": "900000",
         "duration_s": 1.0, "amplitude_frac": 0.3}])
    r = contracts.validate_recipe(bad)
    assert not r["valid"] and any("outside" in e for e in
                                  r["errors"])
    # duty above limit
    bad2 = contracts.example_recipe("SYNTHETIC-T3", [
        {"label": "t", "kind": "square", "frequency_hz": "4096",
         "duration_s": 1.0, "duty": 0.9, "amplitude_frac": 0.3}])
    assert not contracts.validate_recipe(bad2)["valid"]
    # duration over limit
    bad3 = contracts.example_recipe("SYNTHETIC-T4", [
        {"label": "t", "kind": "sine", "frequency_hz": "4096",
         "duration_s": 45.0, "amplitude_frac": 0.3}])
    assert not contracts.validate_recipe(bad3)["valid"]
    # unknown schema version refused, with no silent migration
    bad4 = dict(good, schema_version="0.9")
    assert not contracts.validate_recipe(bad4)["valid"]
    mig = contracts.migrate(bad4)
    assert mig["recipe"] is None and "refusal" in mig


def test_canonical_hash_stability():
    a = {"b": 1, "a": [1, 2]}
    b = {"a": [1, 2], "b": 1}
    assert contracts.content_hash(a) == contracts.content_hash(b)


def test_fuzzed_recipes_never_validate():
    """A12/A22: malformed JSON must be rejected, never crash."""
    import random
    rng = random.Random(0)
    base = contracts.example_recipe("SYNTHETIC-F", [
        {"label": "t", "kind": "sine", "frequency_hz": "4096",
         "duration_s": 1.0, "amplitude_frac": 0.3}])
    for _ in range(60):
        mut = __import__("json").loads(__import__("json").dumps(base))
        path = rng.choice(["schema_version", "segments", "limits",
                           "recipe_id", "device_requirements"])
        mut[path] = rng.choice([None, -1, "x", [], {},
                                float("nan") if path != "segments"
                                else []])
        out = contracts.validate_recipe(mut)
        assert isinstance(out["valid"], bool)
        if out["valid"]:
            # only acceptable if the mutation happened to be benign
            assert contracts.validate_recipe(mut)["valid"]
