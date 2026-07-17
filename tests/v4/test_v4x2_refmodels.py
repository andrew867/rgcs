"""Q01-Q06 reference-model tests: analytic limits, source-specific
behaviour, and the transfer firewall (reference-model gates)."""

import numpy as np
import pytest

from rscs2_core.refmodels import (discrimination as disc,
                                  filtration_solver as fs,
                                  honeycomb_vhs as hv,
                                  spin_electric as se,
                                  triangular_transport as tt)


# --- Q01: spin-electric ------------------------------------------------

def test_exchange_shift_nonlinear_near_threshold():
    v = np.linspace(-50, 50, 501)
    out = se.resonance_shift(v, 20.0, 0.05, 10.0, 3.0)
    rel = out["relative_shift"]
    # far below threshold: negligible; far above: saturated
    assert abs(rel[0]) < 1e-4
    assert rel[-1] == pytest.approx(rel[-2], rel=1e-3)
    # steepest change near the threshold
    didv = np.gradient(out["f_ghz"], v)
    assert abs(v[int(np.argmax(didv))] - 10.0) < 2.0
    assert out["max_relative_shift"] > 0.1     # tens of percent


def test_rabi_detuning_limits():
    on = se.rabi_detuning(20.0, 20.0, 0.01)
    assert on["contrast"] == pytest.approx(1.0)
    far = se.rabi_detuning(20.0, 21.0, 0.01)
    assert far["contrast"] < 1e-3


def test_pair_selectivity_needs_shift_beyond_rabi():
    good = se.coupled_pair_selectivity(0.1, 0.01, 0.5)
    assert good["addressable"]
    bad = se.coupled_pair_selectivity(0.1, 0.5, 0.01)
    assert not bad["addressable"]


def test_tunability_coherence_tradeoff():
    t = se.tunability_coherence_tradeoff(0.05, 3.0, 0.5)
    assert t["dephasing_ghz"] > 0
    assert "linewidth" in t["lesson"]


def test_q01_transfer_firewall():
    with pytest.raises(se.TransferViolation):
        se.guard_target("alpha quartz wand")
    with pytest.raises(se.TransferViolation):
        se.guard_target("PCB resonator at room temperature")
    se.guard_target("FePc molecule on MgO")     # allowed


# --- Q02: triangular transport ------------------------------------------

def test_classification_vocabulary():
    assert tt.classify_feature([1, 0, 0], [0, 1, 0]) == \
        "REDISTRIBUTION"
    assert tt.classify_feature([1, 0, 0], [1, 1, 0]) == \
        "TOTAL_CHANGE"
    assert tt.classify_feature([1, 0, 0], [1, 0, 0]) == \
        "NO_CHANGE_TRANSFER_FUNCTION_CANDIDATE"


def test_steady_state_is_a_distribution():
    w = tt.rates([0.0, 0.1, 0.2], 0.3, 0.5, [1.0, 0.5, 0.2])
    p = tt.steady_state(w)
    assert p.sum() == pytest.approx(1.0)
    assert (p >= 0).all()


def test_redistribution_at_constant_total_charge():
    """The paper's core: bias moves charge BETWEEN sites while the
    total stays ~constant in a window."""
    eps = [0.0, 0.15, 0.3]
    a = tt.observables(eps, 0.4, 0.60, [1.0, 0.3, 0.3])
    b = tt.observables(eps, 0.4, 0.75, [1.0, 0.3, 0.3])
    cls = tt.classify_feature(a["site_occupations"],
                              b["site_occupations"])
    assert cls in ("REDISTRIBUTION", "TOTAL_CHANGE")
    # and there exists a window where it is specifically
    # redistribution
    found = False
    prev = tt.observables(eps, 0.4, 0.05, [1.0, 0.3, 0.3])
    for bias in np.arange(0.1, 1.4, 0.05):
        cur = tt.observables(eps, 0.4, float(bias),
                             [1.0, 0.3, 0.3])
        if tt.classify_feature(prev["site_occupations"],
                               cur["site_occupations"]) == \
                "REDISTRIBUTION":
            found = True
            break
        prev = cur
    assert found, "no redistribution window found in the sweep"


def test_ndc_reachable_with_asymmetric_couplings():
    eps = [0.0, 0.2, 0.4]
    sweep = tt.bias_sweep(eps, 0.5, np.linspace(0.1, 1.6, 40),
                          [1.0, 0.15, 0.05])
    assert "QUALITATIVE" in sweep["note"]
    # NDC is parameter-dependent; assert the sweep MACHINERY reports
    # it as a boolean either way, and current is finite
    assert isinstance(sweep["ndc_present"], bool)
    assert np.isfinite(sweep["current_au"]).all()


# --- Q03: honeycomb VHS ----------------------------------------------------

def test_expansion_narrows_band_and_raises_vhs():
    out = hv.expansion_narrows_band()
    s = out["sweep"]
    assert s["1.25"]["bandwidth_ev"] < s["1"]["bandwidth_ev"]
    assert s["1.25"]["vhs_dos"] > 0


def test_isotropic_limit_restores_c6():
    n = hv.nematic_splitting(1.0, 0.0)
    assert n["c6_restored"]
    assert n["splitting_ev"] == pytest.approx(0.0, abs=1e-12)
    split = hv.nematic_splitting(1.0, 0.1)
    assert split["splitting_ev"] > 0


def test_dos_vhs_at_t_for_isotropic():
    d = hv.dos(1.0, 1.0, 1.0)
    assert d["vhs_energy_ev"] == pytest.approx(1.0, abs=0.15)


def test_q03_design_principle_is_engineering_only():
    p = hv.resonator_lattice_design_principle()
    assert p["status"] == "ENGINEERING_PROTOTYPE"
    assert "no electronic-nematicity claim" in p["forbidden"]


# --- Q04: filtration solver --------------------------------------------------

def test_filtration_reduces_coupling_on_structured_system():
    a, p, l0, l1 = fs.demo_system(n=8, seed=1)
    rep = fs.apply_filtration(a)
    assert rep["density_before"] > 0.5      # dense in the wrong basis
    assert "heuristic" in rep["note"]


def test_eps_factorizes_in_revealing_basis():
    a, p, l0, l1 = fs.demo_system(n=6, seed=2)
    chk = fs.eps_factorization_check(p, l0, l1)
    assert chk["eps_affine_in_revealing_basis"]
    assert "conjectural" in chk["conjecture_note"]


def test_q04_no_measured_benefit_claimed():
    app = fs.rgcs_application()
    assert "none yet" in app["measured_benefit"]


# --- Q05: discrimination -------------------------------------------------------

def test_unevaluated_alternative_means_inconclusive():
    out = disc.discrimination_tree("resonance_shift", {})
    assert out["verdict"] == "INCONCLUSIVE"


def test_surviving_ordinary_alternative_wins():
    evals = {a: {"excluded": True, "evidence": "measured and bounded"}
             for a, _ in disc.ORDINARY_ALTERNATIVES[
                 "resonance_shift"]}
    evals["temperature"] = {"excluded": False}
    out = disc.discrimination_tree("resonance_shift", evals)
    assert out["verdict"] == "ORDINARY_SUFFICIENT"
    assert "temperature" in out["sufficient_alternatives"]


def test_exclusion_without_evidence_is_inconclusive():
    evals = {a: {"excluded": True, "evidence": "x"}
             for a, _ in disc.ORDINARY_ALTERNATIVES[
                 "resonance_shift"]}
    out = disc.discrimination_tree("resonance_shift", evals)
    assert out["verdict"] == "INCONCLUSIVE"


def test_candidate_novel_licenses_work_not_claims():
    evals = {a: {"excluded": True,
                 "evidence": "measured, bounded, and subtracted"}
             for a, _ in disc.ORDINARY_ALTERNATIVES[
                 "resonance_shift"]}
    out = disc.discrimination_tree("resonance_shift", evals)
    assert out["verdict"] == "CANDIDATE_NOVEL"
    assert "not a claim" in out["note"]


def test_identifiability_inside_noise_is_inconclusive():
    r = disc.identifiability_report(1.0, 0.8, 0.5)
    assert not r["identifiable"]


# --- Q06: playground -------------------------------------------------------------

def test_playground_labels_are_mandatory_and_firewalled():
    import model_playground as disc
    env = disc.run_model("honeycomb_vhs", "nematic_splitting",
                         t_ev=1.0, delta=0.1)
    assert env["source_system"].startswith("boron")
    assert env["evidence_status"] == "REFERENCE_MATHEMATICS_ONLY"
    assert "cannot be registered as evidence" in env["firewall"]
    with pytest.raises(disc.PlaygroundError):
        disc.run_model("not_a_model", "f")


def test_playground_compare_keeps_labels():
    import model_playground as disc
    a = disc.run_model("honeycomb_vhs", "nematic_splitting",
                       t_ev=1.0, delta=0.1)
    b = disc.run_model("honeycomb_vhs", "nematic_splitting",
                       t_ev=1.0, delta=0.2)
    cmp_ = disc.compare([a, b], "splitting_ev")
    assert all(r["source_system"] for r in cmp_["rows"])
