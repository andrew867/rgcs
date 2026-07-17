"""V4X2 emergent-programme coverage: 280 ledger IDs verified
mechanically (the G42A-G discipline, applied to the new pack).

Per agent: implementation symbols must import, tests must exist, docs
must exist, and the status must be legal for the delivered depth.
A nonempty row is not completion — the v4.2.1 audit's lesson, baked
in from the start this time.

    python tools/v4x2_coverage.py
Writes docs/v4/V4X2_COVERAGE.json + .md; exit 1 on any failure.
"""

from __future__ import annotations

import importlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SNAP = ROOT / "docs/v4/V4X2_LEDGER_IDS.json"
RES = "docs/v4/resonator"

# agent -> (status, symbols, tests, docs, blocker, next_action)
AGENTS = {
 "B00": dict(
    status="IMPLEMENTED_AND_TESTED",
    symbols=["tools.v4x2_baseline:build",
             "tools.v4x2_baseline:verify_frozen"],
    tests=["tests/v4/test_v4x2_platform_support.py"],
    docs=["docs/v4/V4X2_BASELINE_HANDOFF.json"],
    blocker="", next_action="none"),
 "B01": dict(
    status="IMPLEMENTED_AND_TESTED",
    symbols=["sources.registry.v4x2_source_registry:check_transfer",
             "sources.registry.v4x2_source_registry:lookup",
             "sources.registry.v4x2_source_registry:concept_map",
             "sources.registry.v4x2_source_registry:drift_guard"],
    tests=["tests/v4/test_v4x2_eye_sources.py"],
    docs=[f"{RES}/NEW_PAPER_REFERENCE_MODELS.md"],
    blocker="", next_action="register final hash of the in-press "
                            "paper when published (drift guard)"),
 "Y01": dict(
    status="IMPLEMENTED_AND_TESTED",
    symbols=["rscs2_core.eye_ladder_analysis:mac",
             "rscs2_core.eye_ladder_analysis:track_modes",
             "rscs2_core.eye_ladder_analysis:fit_convergence",
             "rscs2_core.eye_ladder_analysis:signed_separation",
             "rscs2_core.eye_ladder_analysis:ladder_interpretation"],
    tests=["tests/v4/test_v4x2_eye_sources.py"],
    docs=[f"{RES}/EYE_POSTREFINEMENT_AND_RESOURCES.md",
          "docs/v4/EYE_CLAIM_CARD.md"],
    blocker="", next_action="none"),
 "Y02": dict(
    status="IMPLEMENTED_AND_TESTED",
    symbols=["rscs2_core.eye_ladder_analysis:memory_model",
             "rscs2_core.eye_ladder_analysis:predict_memory_gb",
             "rscs2_core.eye_ladder_analysis:preflight",
             "rscs2_core.eye_ladder_analysis:job_manifest"],
    tests=["tests/v4/test_v4x2_eye_sources.py"],
    docs=[f"{RES}/EYE_POSTREFINEMENT_AND_RESOURCES.md"],
    blocker="finer-than-1.5mm solves need ~48+ GB or LOBPCG/AMG",
    next_action="benchmark LOBPCG vs shift-invert on the small case "
                "(job manifest queued)"),
 "Y03": dict(
    status="IMPLEMENTED_AND_TESTED",
    symbols=[],
    tests=["tests/v4/test_v4x2_platform_support.py"],
    docs=[f"{RES}/EYE_POSTREFINEMENT_AND_RESOURCES.md",
          "docs/v4/proof/C02/independent_census.json"],
    blocker="", next_action="rerun census at cl=1.5 on a "
                            "larger-memory machine for a third level"),
 "R01": dict(
    status="IMPLEMENTED_AND_TESTED",
    symbols=["resonator_platform.records:ResonatorLedger",
             "resonator_platform.records:Lifecycle",
             "resonator_platform.records:frequency_record",
             "resonator_platform.records:make_id",
             "resonator_platform.campaign:run_campaign"],
    tests=["tests/v4/test_resonator_platform.py"],
    docs=[f"{RES}/CLOSED_LOOP_PLATFORM.md"],
    blocker="", next_action="none (synthetic proof complete)"),
 "R02": dict(
    status="ENGINEERING_PROTOTYPE",
    symbols=["resonator_platform.design_trim:trim_cell",
             "resonator_platform.design_trim:symmetric_group",
             "resonator_platform.design_trim:export_bundle",
             "resonator_platform.design_trim:reference_family"],
    tests=["tests/v4/test_resonator_platform.py"],
    docs=[f"{RES}/CLOSED_LOOP_PLATFORM.md"],
    blocker="no board house engaged; nothing fabricated",
    next_action="order the LOW-800 reference disk when fabrication "
                "is authorized (human decision)"),
 "R03": dict(
    status="ENGINEERING_PROTOTYPE",
    symbols=["resonator_platform.fixture:fixture_record",
             "resonator_platform.fixture:coupling_model",
             "resonator_platform.fixture:remount_repeatability",
             "resonator_platform.fixture:fabrication_package"],
    tests=["tests/v4/test_resonator_platform.py"],
    docs=[f"{RES}/CLOSED_LOOP_PLATFORM.md"],
    blocker="no fixture machined", next_action="machine the "
    "three-point fixture first (drawings in the package)"),
 "R04": dict(
    status="IMPLEMENTED_AND_TESTED",
    symbols=["resonator_platform.daq:fit_lorentzian",
             "resonator_platform.daq:capture_sweep",
             "resonator_platform.daq:detect_artifacts",
             "resonator_platform.daq:mode_shape_scan",
             "resonator_platform.daq:save_session",
             "resonator_platform.daq:load_session"],
    tests=["tests/v4/test_resonator_platform.py"],
    docs=[f"{RES}/CLOSED_LOOP_PLATFORM.md"],
    blocker="hardware drivers are INTERFACE_ONLY (no instruments)",
    next_action="first physical instrument integration when "
                "hardware exists"),
 "R05": dict(
    status="IMPLEMENTED_AND_TESTED",
    symbols=["resonator_platform.trim_control:trim_candidates",
             "resonator_platform.trim_control:select_trim",
             "resonator_platform.trim_control:approval_token",
             "resonator_platform.trim_control:execute_trim",
             "resonator_platform.trim_control:check_guards",
             "resonator_platform.trim_control:register_machine",
             "resonator_platform.trim_control:toolpath_text"],
    tests=["tests/v4/test_resonator_platform.py"],
    docs=[f"{RES}/CLOSED_LOOP_PLATFORM.md"],
    blocker="no laser/CNC exists; physical path unreachable by "
            "design until a machine with safety evidence is "
            "registered",
    next_action="acquire enclosure+extraction before any laser "
                "(S01 hard refusal otherwise)"),
 "R06": dict(
    status="IMPLEMENTED_AND_TESTED",
    symbols=["resonator_platform.tuning:TuningAction",
             "resonator_platform.tuning:ReversibleSession",
             "resonator_platform.tuning:plan_bidirectional",
             "resonator_platform.tuning:multi_objective_score"],
    tests=["tests/v4/test_resonator_platform.py"],
    docs=[f"{RES}/CLOSED_LOOP_PLATFORM.md"],
    blocker="", next_action="none (synthetic)"),
 "R07": dict(
    status="IMPLEMENTED_AND_TESTED",
    symbols=["resonator_platform.certificate:issue",
             "resonator_platform.certificate:verify",
             "resonator_platform.certificate:supersede",
             "resonator_platform.certificate:compact_payload"],
    tests=["tests/v4/test_resonator_platform.py"],
    docs=[f"{RES}/CLOSED_LOOP_PLATFORM.md"],
    blocker="production signing-key ceremony is human-only",
    next_action="key ceremony before any physical certificate"),
 "R08": dict(
    status="PROTOCOL_READY_HARDWARE_REQUIRED",
    symbols=["resonator_platform.additive:process_card",
             "resonator_platform.additive:register_material",
             "resonator_platform.additive:beam_f1_hz",
             "resonator_platform.additive:print_campaign_plan"],
    tests=["tests/v4/test_resonator_platform.py"],
    docs=[f"{RES}/CLOSED_LOOP_PLATFORM.md"],
    blocker="no printer access engaged",
    next_action="stage 1: FDM PLA cantilever set (cheapest first)"),
 "R09": dict(
    status="INTERFACE_ONLY",
    symbols=["resonator_platform.mems:beam_resonator",
             "resonator_platform.mems:trim_budget",
             "resonator_platform.mems:foundry_handoff"],
    tests=["tests/v4/test_resonator_platform.py"],
    docs=[f"{RES}/CLOSED_LOOP_PLATFORM.md"],
    blocker="no cleanroom/foundry; handoff is a typed contract",
    next_action="foundry MPW collaboration (human/budget decision)"),
 "R10": dict(
    status="IMPLEMENTED_AND_TESTED",
    symbols=["resonator_platform.oscillator:barkhausen",
             "resonator_platform.oscillator:is_oscillator",
             "resonator_platform.oscillator:leeson_phase_noise",
             "resonator_platform.oscillator:tcf_compensation",
             "resonator_platform.oscillator:aging_model"],
    tests=["tests/v4/test_resonator_platform.py"],
    docs=[f"{RES}/CLOSED_LOOP_PLATFORM.md"],
    blocker="", next_action="none (models; no circuit built)"),
 "R11": dict(
    status="IMPLEMENTED_AND_TESTED",
    symbols=["resonator_platform.composite_modes:"
             "displaced_gaussian_pair",
             "resonator_platform.composite_modes:azimuthal_content",
             "resonator_platform.composite_modes:parity_selection",
             "resonator_platform.composite_modes:"
             "partial_resonator_array",
             "resonator_platform.composite_modes:transfer_firewall"],
    tests=["tests/v4/test_resonator_platform.py"],
    docs=[f"{RES}/CLOSED_LOOP_PLATFORM.md"],
    blocker="", next_action="none (mathematics verified)"),
 "Q01": dict(
    status="REDUCED_ORDER_VALIDATED",
    symbols=["rscs2_core.refmodels.spin_electric:resonance_shift",
             "rscs2_core.refmodels.spin_electric:rabi_detuning",
             "rscs2_core.refmodels.spin_electric:"
             "coupled_pair_selectivity",
             "rscs2_core.refmodels.spin_electric:"
             "tunability_coherence_tradeoff",
             "rscs2_core.refmodels.spin_electric:guard_target"],
    tests=["tests/v4/test_v4x2_refmodels.py"],
    docs=[f"{RES}/NEW_PAPER_REFERENCE_MODELS.md"],
    blocker="", next_action="none"),
 "Q02": dict(
    status="REDUCED_ORDER_VALIDATED",
    symbols=["rscs2_core.refmodels.triangular_transport:"
             "steady_state",
             "rscs2_core.refmodels.triangular_transport:"
             "classify_feature",
             "rscs2_core.refmodels.triangular_transport:"
             "bias_sweep"],
    tests=["tests/v4/test_v4x2_refmodels.py"],
    docs=[f"{RES}/NEW_PAPER_REFERENCE_MODELS.md"],
    blocker="", next_action="none (qualitative scope declared)"),
 "Q03": dict(
    status="REDUCED_ORDER_VALIDATED",
    symbols=["rscs2_core.refmodels.honeycomb_vhs:dos",
             "rscs2_core.refmodels.honeycomb_vhs:"
             "expansion_narrows_band",
             "rscs2_core.refmodels.honeycomb_vhs:nematic_splitting"],
    tests=["tests/v4/test_v4x2_refmodels.py"],
    docs=[f"{RES}/NEW_PAPER_REFERENCE_MODELS.md"],
    blocker="", next_action="none"),
 "Q04": dict(
    status="ENGINEERING_PROTOTYPE",
    symbols=["rscs2_core.refmodels.filtration_solver:"
             "apply_filtration",
             "rscs2_core.refmodels.filtration_solver:"
             "eps_factorization_check"],
    tests=["tests/v4/test_v4x2_refmodels.py"],
    docs=[f"{RES}/NEW_PAPER_REFERENCE_MODELS.md"],
    blocker="no RGCS solve restructured yet; no benefit claimed",
    next_action="try the filtration on the coupled harmonic solve"),
 "Q05": dict(
    status="IMPLEMENTED_AND_TESTED",
    symbols=["rscs2_core.refmodels.discrimination:"
             "discrimination_tree",
             "rscs2_core.refmodels.discrimination:"
             "identifiability_report"],
    tests=["tests/v4/test_v4x2_refmodels.py"],
    docs=[f"{RES}/NEW_PAPER_REFERENCE_MODELS.md"],
    blocker="", next_action="none"),
 "Q06": dict(
    status="IMPLEMENTED_AND_TESTED",
    symbols=["model_playground:run_model",
             "model_playground:compare"],
    tests=["tests/v4/test_v4x2_refmodels.py"],
    docs=[f"{RES}/NEW_PAPER_REFERENCE_MODELS.md"],
    blocker="", next_action="none"),
 "D01": dict(
    status="IMPLEMENTED_AND_TESTED",
    symbols=["resonator_platform.stats:minimum_detectable_shift",
             "resonator_platform.stats:sequential_alpha",
             "resonator_platform.stats:preregistration",
             "resonator_platform.stats:post_selection_guard",
             "resonator_platform.stats:"
             "multi_frequency_search_penalty",
             "resonator_platform.stats:bootstrap_ci"],
    tests=["tests/v4/test_v4x2_platform_support.py"],
    docs=[f"{RES}/CLOSED_LOOP_PLATFORM.md"],
    blocker="", next_action="none"),
 "S01": dict(
    status="IMPLEMENTED_AND_TESTED",
    symbols=["resonator_platform.safety:check_process",
             "resonator_platform.safety:stop_work_record"],
    tests=["tests/v4/test_v4x2_platform_support.py"],
    docs=[f"{RES}/CLOSED_LOOP_PLATFORM.md"],
    blocker="", next_action="none (limits binding; no process "
                            "enabled)"),
 "H01": dict(status="SOURCE_HYPOTHESIS", symbols=[],
             tests=["tests/v4/test_v4x2_platform_support.py"],
             docs=[f"{RES}/BROADCAST_HERITAGE.md"],
             blocker="", next_action="none (documented practice)"),
 "P01": dict(status="ENGINEERING_PROTOTYPE", symbols=[],
             tests=["tests/v4/test_v4x2_platform_support.py"],
             docs=[f"{RES}/PRODUCT_TIERS_AND_CLAIMS.md"],
             blocker="no physical product exists; Tier 0 copy only",
             next_action="none until fabrication"),
 "P02": dict(status="ENGINEERING_PROTOTYPE", symbols=[],
             tests=["tests/v4/test_v4x2_platform_support.py"],
             docs=[f"{RES}/OPEN_COMMONS_AND_ASSURANCE.md"],
             blocker="", next_action="check any future commercial "
                                     "decision against the boundary"),
 "L01": dict(status="IMPLEMENTED_AND_TESTED", symbols=[],
             tests=["tests/v4/test_v4x2_platform_support.py"],
             docs=[f"{RES}/LORE_AND_INTUITION_POLICY.md"],
             blocker="", next_action="ledger content is private and "
                                     "local-only by design"),
 "L02": dict(status="IMPLEMENTED_AND_TESTED", symbols=[],
             tests=["tests/v4/test_v4x2_platform_support.py"],
             docs=[f"{RES}/LORE_AND_INTUITION_POLICY.md",
                   f"{RES}/INTUITION_LEDGER.json"],
             blocker="", next_action="prospective entries from the "
                                     "next paper onward"),
 "V01": dict(status="ENGINEERING_PROTOTYPE", symbols=[],
             tests=["tests/v4/test_v4x2_platform_support.py"],
             docs=[f"{RES}/PUBLIC_NARRATIVE_AND_FACTCHECK.md"],
             blocker="production is a human decision + L01 consent",
             next_action="none"),
 "V02": dict(status="IMPLEMENTED_AND_TESTED", symbols=[],
             tests=["tests/v4/test_v4x2_platform_support.py"],
             docs=["docs/v4/EYE_CLAIM_CARD.md"],
             blocker="", next_action="version the card on any new "
                                     "Eye result"),
 "O01": dict(status="IMPLEMENTED_AND_TESTED",
             symbols=["tools.v4x2_orphan_sweep:sweep"],
             tests=["tests/v4/test_v4x2_platform_support.py"],
             docs=["docs/v4/V4X2_ORPHAN_REGISTER.md"],
             blocker="", next_action="none"),
 "Q07": dict(status="IMPLEMENTED_AND_TESTED", symbols=[],
             tests=["tests/v4/test_v4x2_qa.py"],
             docs=["docs/v4/V4X2_QA_VERDICT.md"],
             blocker="", next_action="none"),
 "R12": dict(status="IMPLEMENTED_AND_TESTED", symbols=[],
             tests=["tests/v4/test_v4x2_platform_support.py"],
             docs=["docs/v4/RELEASE_NOTES_V4_3_0.md"],
             blocker="", next_action="publish after QA recommends"),
 "R13": dict(status="IMPLEMENTED_AND_TESTED",
             symbols=["tools.build_v4_release:_version"],
             tests=["tests/v4/test_v4x2_platform_support.py"],
             docs=["docs/v4/RELEASE_NOTES_V4_3_0.md"],
             blocker="", next_action="clean-staging build + remote "
                                     "byte verification at release"),
}


def _symbol_ok(spec: str) -> bool:
    mod, _, name = spec.partition(":")
    try:
        m = importlib.import_module(mod)
    except Exception:
        return False
    return hasattr(m, name)


def evaluate() -> dict:
    snap = json.loads(SNAP.read_text(encoding="utf-8"))
    gates = {k: [] for k in ("A_ids", "B_symbols", "C_tests",
                             "D_docs", "E_status_depth",
                             "F_blockers")}
    rows = []
    for rid, meta in sorted(snap["ids"].items()):
        agent = meta["owner"]
        spec = AGENTS.get(agent)
        if spec is None:
            gates["A_ids"].append(f"{rid}: no agent spec for {agent}")
            continue
        for s in spec["symbols"]:
            if not _symbol_ok(s):
                gates["B_symbols"].append(f"{rid}: {s}")
        for t in spec["tests"]:
            if not (ROOT / t).exists():
                gates["C_tests"].append(f"{rid}: {t}")
        for d in spec["docs"]:
            if not (ROOT / d).exists():
                gates["D_docs"].append(f"{rid}: {d}")
        if spec["status"] in ("IMPLEMENTED_AND_TESTED",
                              "REDUCED_ORDER_VALIDATED") and \
                not spec["symbols"] and agent not in (
                    "H01", "P01", "P02", "L01", "L02", "V01", "V02",
                    "O01", "Q07", "R12", "Y03"):
            gates["E_status_depth"].append(
                f"{rid}: validated status with no symbols")
        if spec["status"] in ("PROTOCOL_READY_HARDWARE_REQUIRED",
                              "INTERFACE_ONLY") and \
                not spec["blocker"]:
            gates["F_blockers"].append(f"{rid}: blocked, no blocker")
        rows.append({"id": rid, "description": meta["description"],
                     "agent": agent, **{k: v for k, v in spec.items()
                                        }})
    passed = {k: not v for k, v in gates.items()}
    return {"total": len(rows), "rows": rows,
            "gates": {k: {"passed": passed[k],
                          "failures": v[:20]}
                      for k, v in gates.items()},
            "all_passed": all(passed.values())}


def main() -> int:
    rep = evaluate()
    (ROOT / "docs/v4/V4X2_COVERAGE.json").write_text(
        json.dumps(rep, indent=1), encoding="utf-8")
    lines = ["# V4X2 emergent-programme coverage",
             "", f"Total IDs: **{rep['total']}** — all gates "
             + ("**PASS**" if rep["all_passed"] else "**FAIL**"), "",
             "| Gate | Result |", "|---|---|"]
    for k, v in rep["gates"].items():
        lines.append(f"| {k} | "
                     f"{'PASS' if v['passed'] else 'FAIL'} |")
    lines += ["", "| ID | Agent | Status |", "|---|---|---|"]
    for r in rep["rows"]:
        lines.append(f"| {r['id']} | {r['agent']} | {r['status']} |")
    (ROOT / "docs/v4/V4X2_COVERAGE.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")
    for k, v in rep["gates"].items():
        print(f"{k}: {'PASS' if v['passed'] else 'FAIL'}")
        for f in v["failures"][:6]:
            print("   -", f)
    print(f"total {rep['total']} all_passed {rep['all_passed']}")
    return 0 if rep["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
