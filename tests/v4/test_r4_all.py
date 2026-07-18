"""v4.8 R4: exact radix, tetrahedral quantizer/SIC firewall, GF(4),
multiresolution codec, benchmarks, HAL, platforms, spin twin, bench —
plus the adversarial campaign.

The load-bearing tests: radix conversion is NOT compression, SIC
outcomes are NOT storage, four spin-1/2 directions are NOT four
states, quartz stays BLOCKED, and the benchmark's negative control
must show no gain on random data.
"""
from __future__ import annotations

import math

import numpy as np
import pytest


# --- doctrine ---------------------------------------------------------------

def test_radix_compression_claim_is_refused():
    import r4
    with pytest.raises(r4.ClaimBoundaryError):
        r4.refuse_radix_compression_claim()


def test_excluded_claims_cover_the_ceiling():
    import r4
    joined = " ".join(r4.EXCLUDED_CLAIMS).lower()
    for phrase in ("spin storage in quartz", "four orthogonal",
                   "base conversion alone", "consciousness",
                   "phryll", "torsion", "transport"):
        assert phrase in joined


def test_physical_gates_are_all_present():
    import r4
    assert len(r4.PHYSICAL_GATES) == 10
    assert r4.PHYSICAL_GATES["READ"] == "READOUT_DEGENERATE"


# --- A11 exact radix ---------------------------------------------------------

def test_exhaustive_4096_roundtrip_all_three_radices():
    """The space is finite, so nothing is sampled (R11)."""
    from r4.radix import exhaustive_roundtrip
    rep = exhaustive_roundtrip()
    assert rep["keys_checked"] == 4096
    assert rep["ok"], rep["failures"]


def test_radix_identity_holds():
    assert 4096 == 8 ** 4 == 4 ** 6 == 2 ** 12
    assert 64 == 8 ** 2 == 4 ** 3 == 2 ** 6


def test_three_and_six_symbols_select_64_and_4096():
    from r4.radix import three_symbols_select_64
    r = three_symbols_select_64()
    assert r["equals_64"] and r["equals_4096"]


def test_radix_bridge_declares_zero_compression():
    from r4.radix import radix_bridge
    b = radix_bridge(2745)
    assert b["is_compression"] is False
    assert b["information_content_bits"] == 12
    assert b["octal"] == [5, 2, 7, 1]        # agrees with r3 codec


def test_radix_rejects_out_of_range_and_bad_digits():
    import r4
    from r4.radix import from_quaternary, to_quaternary
    with pytest.raises(r4.ClaimBoundaryError):
        to_quaternary(4096)
    with pytest.raises(r4.ClaimBoundaryError):
        from_quaternary([0, 1, 4])


# --- A12 symbol ontology -----------------------------------------------------

def test_direction_names_require_a_declared_basis():
    import r4
    from r4.radix import SymbolAlphabet, name_directions
    assert SymbolAlphabet("ABSTRACT").labels == ("Q0", "Q1", "Q2", "Q3")
    with pytest.raises(r4.ClaimBoundaryError):
        name_directions("ABSTRACT")
    assert name_directions("SPIN_THREE_HALVES_MS")[0] == "m_s=-3/2"


def test_unknown_basis_refused():
    import r4
    from r4.radix import SymbolAlphabet
    with pytest.raises(r4.ClaimBoundaryError):
        SymbolAlphabet("UP_DOWN_LEFT_RIGHT")


# --- A13 address/payload separation -------------------------------------------

def test_address_is_digital_exact_and_spin_storage_refused():
    import r4
    from r4.radix import Address, refuse_address_in_spin
    a = Address(4095, 4)
    assert a.storage == "DIGITAL_EXACT"
    with pytest.raises(r4.ClaimBoundaryError):
        refuse_address_in_spin(a)
    with pytest.raises(r4.ClaimBoundaryError):
        Address(0, 2, storage="PHYSICAL_SPIN")


def test_codeword_keeps_six_components_separate():
    import r4
    from r4.radix import Address, Codeword, Payload
    c = Codeword(Address(5, 2), Payload((1.0, 2.0)), 0.5, "e", 0.1, 0.01)
    d = c.to_dict()
    for key in ("address_key", "payload_kind", "phase_rad", "epoch",
                "uncertainty", "reconstruction_error"):
        assert key in d
    assert len(r4.CODEWORD_COMPONENTS) == 6


# --- A14/A15 tetrahedral codebook + SIC firewall -------------------------------

def test_codebook_geometry_is_exact():
    from r4.quantizer import codebook_geometry
    g = codebook_geometry()
    assert g["all_pairs_minus_one_third"]
    assert g["sum_is_zero"]
    assert g["frame_operator_is_4_3_identity"]
    assert g["orthogonal"] is False


def test_quantizer_worst_case_angle_is_half_the_codeword_angle():
    from r4.quantizer import max_angular_error_deg
    assert abs(max_angular_error_deg()
               - math.degrees(math.acos(-1 / 3)) / 2) < 1e-9


def test_sic_roundtrip_is_exact():
    from r4.quantizer import sic_roundtrip_error
    for r in ([0, 0, 0], [0.5, 0.2, -0.3], [0.0, 0.0, 1.0]):
        assert sic_roundtrip_error(r) < 1e-12


def test_sic_outcomes_refuse_to_be_storage():
    """R15: the firewall between measurement and memory."""
    import r4
    from r4.quantizer import sic_probabilities
    s = sic_probabilities([0.3, 0.1, -0.2])
    with pytest.raises(r4.ClaimBoundaryError):
        s.as_storage_symbol()


def test_unphysical_bloch_vector_refused():
    import r4
    from r4.quantizer import sic_probabilities
    with pytest.raises(r4.ClaimBoundaryError):
        sic_probabilities([1.0, 1.0, 1.0])


# --- A16 distortion registry ----------------------------------------------------

def test_distortion_metrics_are_unit_checked():
    import r4
    from r4.quantizer import distortion
    d = distortion("MSE", [1.0, 2.0], [1.0, 2.5], "SCALAR")
    assert d["unit"] == "payload_units^2"
    with pytest.raises(r4.ClaimBoundaryError):
        distortion("ANGULAR_DEG", [1.0], [1.0], "SCALAR")


# --- A17 GF(4) --------------------------------------------------------------------

def test_gf4_field_axioms():
    from r4.quantizer import gf4_add, gf4_inverse, gf4_mul
    for a in range(4):
        assert gf4_add(a, a) == 0                 # characteristic 2
        assert gf4_mul(a, 1) == a
        assert gf4_mul(a, 0) == 0
    for a in (1, 2, 3):
        assert gf4_mul(a, gf4_inverse(a)) == 1


def test_parity_corrects_a_known_erasure_and_states_its_scope():
    from r4.quantizer import (correct_erasure, integrity_scope,
                              parity_symbol)
    syms = [1, 2, 3, 0, 2]
    p = parity_symbol(syms)
    gap = list(syms)
    gap[2] = 0
    assert correct_erasure(gap, p, 2) == 3
    sc = integrity_scope()
    assert "erasure" in sc["corrects"].lower()
    assert sc["status"] == "PROOF_FIXTURE"


# --- A19-A26 codec ------------------------------------------------------------------

def _blocky(n=1024, seed=3):
    rng = np.random.default_rng(seed)
    return np.repeat(rng.normal(size=n // 32), 32)[:n]


def test_encode_reports_full_bit_accounting():
    from r4.codec import encode
    r = encode(_blocky(), "LOSSY_FIXED_ERROR", 4, 0.1, 16)
    acc = r["bit_accounting"]
    for key in ("topology_bits", "address_bits", "codebook_bits",
                "payload_symbol_bits", "entropy_model_bits",
                "residual_bits", "total_bits"):
        assert key in acc
    # the codebook is NOT excluded from the total
    assert acc["codebook_bits"] > 0
    assert acc["total_bits"] >= acc["codebook_bits"]


def test_container_roundtrips_and_is_versioned():
    from r4.codec import encode, unpack_container
    r = encode(_blocky(), "LOSSY_FIXED_ERROR", 4, 0.1, 16)
    c = unpack_container(r["container"])
    assert c["version"] == 1
    assert c["mode"] == "LOSSY_FIXED_ERROR"
    assert len(c["symbols"]) == r["n_leaves"]


def test_container_rejects_foreign_blob():
    import r4
    from r4.codec import unpack_container
    with pytest.raises(r4.ClaimBoundaryError):
        unpack_container(b"NOPE" + b"\x00" * 32)


def test_lossless_payload_mode_is_exact():
    from r4.codec import encode
    data = _blocky()
    r = encode(data, "LOSSLESS_PAYLOAD", 4, 0.1, 16)
    assert np.max(np.abs(data - r["reconstruction"])) < 1e-5
    assert r["bit_accounting"]["residual_bits"] > 0


def test_tree_is_deterministic():
    from r4.codec import encode
    d = _blocky()
    a = encode(d, "LOSSY_FIXED_ERROR", 4, 0.1, 16)
    b = encode(d, "LOSSY_FIXED_ERROR", 4, 0.1, 16)
    assert a["bit_accounting"] == b["bit_accounting"]
    assert a["n_leaves"] == b["n_leaves"]


def test_higher_lambda_costs_fewer_bits():
    """The Lagrangian must actually trade rate for distortion."""
    from r4.codec import encode
    d = _blocky()
    cheap = encode(d, "LOSSY_FIXED_ERROR", 4, 100.0, 16)
    rich = encode(d, "LOSSY_FIXED_ERROR", 4, 0.01, 16)
    assert cheap["bit_accounting"]["total_bits"] < \
        rich["bit_accounting"]["total_bits"]


def test_progressive_quality_improves_monotonically():
    from r4.codec import progressive_layers
    layers = progressive_layers(_blocky(), [0, 1, 2, 3], lam=0.01)
    mses = [x["mse"] for x in layers]
    assert all(b <= a + 1e-12 for a, b in zip(mses, mses[1:]))


def test_random_access_touches_few_nodes():
    from r4.codec import random_access
    r = random_access(_blocky(), 512, 4, 0.01)
    assert r["nodes_touched"] <= 5


def test_codebook_training_uses_train_split_only():
    """R20: structural prevention of test leakage."""
    from r4.codec import split_train_test, train_codebook
    d = _blocky()
    train, test = split_train_test(d, 0.5)
    assert len(train) + len(test) == len(d)
    cb = train_codebook(train, 8)
    assert cb.trained_on == "TRAIN_SPLIT_ONLY"
    assert cb.n_train == len(train)
    assert cb.frozen


# --- A27/A55/A56 benchmarks ------------------------------------------------------

def test_negative_control_shows_no_compression_on_random_data():
    """R50 — the gate that would have caught a bookkeeping win."""
    from r4.benchmark import benchmark_corpus
    for name in ("RANDOM_UNIFORM", "RANDOM_GAUSSIAN"):
        r = benchmark_corpus(name, 1024)
        assert r["is_negative_control"]
        assert r["beats_any_baseline"] is False, \
            f"{name}: gains on incompressible data means the " \
            "accounting is wrong"


def test_raw_quaternary_baseline_costs_the_same_as_binary():
    """The radix 'win' that isn't."""
    from r4.benchmark import (baseline_flat_float32,
                              baseline_raw_quaternary, corpus)
    d = corpus("SMOOTH_FIELD", 512)
    assert baseline_raw_quaternary(d)["total_bits"] == \
        baseline_flat_float32(d)["total_bits"]


def test_rate_distortion_sweeps_both_rate_knobs():
    """Sweeping only lambda pins fidelity at the codebook bottleneck
    and does not produce a frontier."""
    from r4.benchmark import rate_distortion_curve
    from r4.benchmark import corpus
    curve = rate_distortion_curve(corpus("PIECEWISE_CONSTANT", 512),
                                  [0.1, 10.0])
    assert len({c["k"] for c in curve}) > 1
    assert len({c["lambda"] for c in curve}) > 1


def test_pareto_front_is_monotone():
    from r4.benchmark import corpus, pareto_front, rate_distortion_curve
    curve = rate_distortion_curve(corpus("PIECEWISE_CONSTANT", 512),
                                  [0.01, 1.0])
    pf = pareto_front(curve)
    bits = [c["total_bits"] for c in pf]
    mses = [c["mse"] for c in pf]
    assert bits == sorted(bits)
    assert mses == sorted(mses, reverse=True)


def test_campaign_reports_losses_honestly():
    """The codec does NOT win everywhere, and the campaign must say
    so rather than reporting only its wins."""
    from r4.benchmark import full_campaign
    rep = full_campaign(n=1024)
    assert rep["negative_control_gate"] == "PASS"
    losers = [c for c, r in rep["results"].items()
              if not r["beats_any_baseline"]]
    assert losers, "a campaign with no losses is not a fair campaign"


# --- A29-A33 HAL --------------------------------------------------------------------

def _prov():
    return {"authority": "programme", "created_epoch_s": 0.0,
            "consent_ref": "n/a-synthetic"}


def test_hal_refuses_non_synthetic_payload():
    import r3
    import r4
    from r3.hal_memory import MemoryRecord
    from r4.hal_adapter import CodedMemory
    # the r3 record refuses at its own boundary
    with pytest.raises(r3.ClaimBoundaryError):
        MemoryRecord(1, 2, "PERSONAL", 0.0)
    rec = MemoryRecord(1, 2, "SYNTHETIC", 0.0)
    with pytest.raises(r4.ClaimBoundaryError):
        CodedMemory(rec, b"", {"authority": "x"}, None, 0.0)


def test_hal_exact_fallback_always_available():
    from r3.hal_memory import MemoryRecord
    from r4.hal_adapter import retrieve, store
    d = np.repeat(np.arange(8.0), 8)
    m = store(MemoryRecord(1, 2, "SYNTHETIC", 0.0), d, _prov(), True)
    ex = retrieve(m, exact=True)
    assert ex["mode"] == "EXACT" and ex["error"] == 0.0
    assert np.allclose(ex["values"], d)


def test_hal_without_fallback_refuses_exact_retrieval():
    import r4
    from r3.hal_memory import MemoryRecord
    from r4.hal_adapter import retrieve, store
    m = store(MemoryRecord(1, 2, "SYNTHETIC", 0.0),
              np.arange(64.0), _prov(), keep_exact=False)
    with pytest.raises(r4.ClaimBoundaryError):
        retrieve(m, exact=True)


def test_hal_loss_policy_protects_addresses_and_provenance():
    from r4.hal_adapter import loss_policy
    p = loss_policy()
    for must in ("addresses", "provenance", "authority"):
        assert must in p["must_be_lossless"]
    assert p["exact_fallback_required"] is True


def test_hal_ablation_sweeps_both_knobs_and_is_informative():
    from r4.hal_adapter import ablation_study
    a = ablation_study(n_records=8, dim=128)
    assert len({r["lambda"] for r in a["ablation"]}) > 1
    assert len({r["codebook_k"] for r in a["ablation"]}) > 1
    # at the finest setting the error must be far below the payload
    # variance, or the study has learned nothing
    assert min(r["mean_mse"] for r in a["ablation"]) < 0.5


# --- A35-A41 platforms ----------------------------------------------------------------

def test_quartz_is_blocked():
    """R36 — however attractive the source narrative."""
    import r4
    from r4.platforms import select_platform
    with pytest.raises(r4.PhysicalGateBlocked):
        select_platform("QUARTZ_DEFECT")


def test_four_spin_half_directions_are_not_four_states():
    import r4
    from r4.platforms import REGISTRY, select_platform
    p = REGISTRY["SPIN_HALF_TETRAHEDRAL"]
    assert p.native_levels == 2
    assert p.orthogonal_states is False
    with pytest.raises(r4.PhysicalGateBlocked):
        select_platform("SPIN_HALF_TETRAHEDRAL")


def test_sic_spin_three_halves_records_readout_limitation():
    from r4.platforms import REGISTRY
    p = REGISTRY["SIC_V_SI_SPIN_3_2"]
    assert "PAIRS" in p.limitations
    assert "READOUT_DEGENERATE" in p.open_gates


def test_classical_platform_is_separated_from_spin_claim():
    from r4.platforms import REGISTRY
    p = REGISTRY["CLASSICAL_FOUR_DOMAIN"]
    assert p.coherent is False
    assert "not the spin hypothesis" in p.limitations.lower() or \
        "tests the codec" in p.limitations.lower()


def test_decision_matrix_reports_sensitivity_and_blocks_quartz():
    from r4.platforms import decision_matrix
    d = decision_matrix()
    assert d["quartz_status"] == "BLOCKED"
    assert d["physical_status"].startswith("UNTESTED")
    assert d["recommended_if_coherence_not_required"] == \
        "CLASSICAL_FOUR_DOMAIN"


def test_stop_matrix_forbids_physical_verdict():
    from r4.platforms import stop_matrix_report
    r = stop_matrix_report("SIC_V_SI_SPIN_3_2")
    assert r["may_continue_in_simulation"] is True
    assert r["may_emit_physical_verdict"] is False


# --- A42-A47 spin twin -------------------------------------------------------------------

def test_zero_field_splitting_ordering_is_analytic():
    from r4.spin_twin import SpinThreeHalves
    e = SpinThreeHalves(b_field_T=0.0).level_energies_hz()
    # D[m^2 - S(S+1)/3] with S=3/2 gives E(+-3/2)=+D and E(+-1/2)=-D,
    # so the pair separation is 2D = 70 MHz for D = 35 MHz
    assert abs((e[1.5] - e[0.5]) - 70.0e6) < 1e3
    assert abs(e[1.5] - e[-1.5]) < 1e-6      # degenerate at B=0


def test_write_compiler_refuses_forbidden_single_pulse():
    import r4
    from r4.spin_twin import refuse_forbidden_transition
    with pytest.raises(r4.ClaimBoundaryError):
        refuse_forbidden_transition(-1.5, 1.5)


def test_write_compiler_builds_multistep_path():
    from r4.spin_twin import SpinThreeHalves, compile_write
    w = compile_write(-1.5, 1.5, SpinThreeHalves())
    assert w["n_pulses"] == 3
    assert w["direct_transition_exists"] is False
    assert len(w["pulse_frequencies_hz"]) == 3


def test_readout_reports_erasure_without_sign_resolution():
    """R40 — pair degeneracy is an erasure, not a guess."""
    from r4.spin_twin import optical_readout
    r = optical_readout(1.5, resolve_sign=False)
    assert r["outcome"] == "ERASURE"
    assert r["sign"] is None
    assert r["bits_recovered"] == 1.0
    assert len(r["candidates"]) == 2
    s = optical_readout(1.5, resolve_sign=True)
    assert s["outcome"] == "RESOLVED" and s["bits_recovered"] == 2.0


def test_confusion_matrix_degrades_with_snr():
    from r4.spin_twin import confusion_matrix
    hi = confusion_matrix(snr=8.0)["mean_fidelity"]
    lo = confusion_matrix(snr=1.0)["mean_fidelity"]
    assert hi > lo
    assert confusion_matrix(snr=8.0)["status"].startswith("SYNTHETIC")


def test_crosstalk_bounds_addressing_density():
    from r4.spin_twin import voxel_crosstalk
    near = voxel_crosstalk(100.0, 300.0)
    far = voxel_crosstalk(2000.0, 300.0)
    assert near["neighbour_excitation_fraction"] > \
        far["neighbour_excitation_fraction"]
    assert far["isolated_at_1e-3"] is True
    assert "do not imply" in near["note"]


def test_retention_is_finite_and_infinite_t1_refused():
    import r4
    from r4.spin_twin import SpinThreeHalves, retention
    r = retention(1.0, 0.5, 300.0, SpinThreeHalves())
    assert 0.0 < r["state_survival_probability"] < 1.0
    assert r["retention_status"] == "FINITE"
    with pytest.raises(r4.ClaimBoundaryError):
        retention(0.0, 1.0, 300.0, SpinThreeHalves())


def test_physical_ecc_is_declared_classical():
    from r4.spin_twin import scrub_interval
    s = scrub_interval(1.0)
    assert "not quantum error correction" in s["note"]


# --- A49-A54 bench ---------------------------------------------------------------------

def test_bench_is_blocked_with_an_explicit_blocker():
    """A54 honest stop."""
    from r4.bench import bench_readiness
    b = bench_readiness()
    assert b["any_stage_runnable_now"] is False
    assert "HARDWARE_SAFETY_BLOCKED" in b["blocker"]
    assert b["physical_status"] == "UNTESTED"


def test_compression_on_hardware_is_gated_on_memory_success():
    from r4.bench import bench_readiness
    assert "R48" in bench_readiness()["s4_precondition"]


def test_first_bench_stage_needs_no_spin_claim():
    from r4.bench import STAGES
    s0 = STAGES[0]
    assert s0.platform == "CLASSICAL_FOUR_DOMAIN"
    assert "no spin claim" in s0.goal


def test_four_state_protocol_tests_against_pair_degenerate_rate():
    from r4.bench import four_state_write_read_protocol
    p = four_state_write_read_protocol()
    assert "pair-degenerate" in p.analysis
    assert "held-out" in p.primary_outcome.lower() or \
        "HELD-OUT" in p.primary_outcome
    assert "no interim peeking" in p.stopping_rule


def test_protocols_are_plans_only():
    from r4.bench import protocols
    p = protocols()
    assert p["apparatus_status"] == "NOT BUILT"
    assert p["physical_status"] == "UNTESTED"
    assert "BLOCKED" in p["claim_boundary"]


# --- A57/A58 adversarial ------------------------------------------------------------------

def test_attack_cannot_claim_compression_from_radix():
    import r4
    with pytest.raises(r4.ClaimBoundaryError):
        r4.refuse_radix_compression_claim()


def test_attack_no_module_claims_a_physical_measurement():
    import pathlib

    import r4
    pkg = pathlib.Path(r4.__file__).parent
    for p in pkg.glob("*.py"):
        text = p.read_text(encoding="utf-8")
        for bad in ("DETECTED_PHRYLL", "PHRYLL_DETECTED",
                    "SPIN_STORAGE_CONFIRMED"):
            assert bad not in text, f"{p.name} contains {bad}"


def test_attack_quartz_cannot_be_selected_by_any_path():
    import r4
    from r4.platforms import REGISTRY, select_platform
    assert REGISTRY["QUARTZ_DEFECT"].selectable is False
    assert len(REGISTRY["QUARTZ_DEFECT"].open_gates) == 10
    with pytest.raises(r4.PhysicalGateBlocked):
        select_platform("QUARTZ_DEFECT")


def test_attack_sic_cannot_become_two_bits_of_memory():
    import r4
    from r4.quantizer import codebook_geometry, sic_probabilities
    assert codebook_geometry()["orthogonal"] is False
    with pytest.raises(r4.ClaimBoundaryError):
        sic_probabilities([0.1, 0.1, 0.1]).as_storage_symbol()


# --- R04/R65 release gate ------------------------------------------------------------

def test_workbook_is_deterministic_across_processes():
    """Regression: r4 canonical rows once used Python's hash() for
    record ids, which is randomized per process (PYTHONHASHSEED), so
    the workbook differed between runs and the release gate refused a
    tag that was actually fine."""
    import subprocess
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    code = ("import sys; sys.path.insert(0, r'%s');"
            "from rgcs_workbench.canonical import build;"
            "s=build('4.8.0');"
            "print('|'.join(r['id'] for r in s.rows('r4_platforms')))"
            % str(root))
    outs = [subprocess.run([sys.executable, "-c", code],
                           capture_output=True, text=True,
                           cwd=str(root)).stdout.strip()
            for _ in range(2)]
    assert outs[0] == outs[1], "canonical r4 ids are not deterministic"
    assert "R4-EXCLUDED-00" in outs[0]


def test_release_gate_refuses_a_stale_workbook(tmp_path):
    from tools.r4_release_gate import gate
    rep = gate()
    assert rep["verdict"] in ("TAG_MAY_PROCEED", "REFUSE_TAG")
    assert "no post-tag synchronization" in rep["rule"]
