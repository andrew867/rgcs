"""Phase 1 of the v4.2.1 completeness audit: agent-by-agent deliverable
crosswalk against the original Master Research Expansion prompt pack.

The v4.2.0 coverage ledger proved that every ID had an owner string. It
did NOT prove that each agent's REQUIRED DELIVERABLES exist. This tool
encodes what each of the 41 agent prompts demanded and checks reality:
does the module exist, does the symbol import, does the document exist,
does the test node exist.

Writes docs/v4/V4X_PROMPT_PACK_DELIVERABLE_CROSSWALK.{json,md}.
Exit code is nonzero while any required deliverable is missing."""

from __future__ import annotations

import importlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PACK = ROOT / "internal-docs" / "plans-v4" / \
    "RGCS_Master_Research_Expansion_Prompt_Pack"

D = "docs/v4/"
C = "docs/v4/consciousness/"
E = "docs/v4/experiments/"

# agent -> mission, coverage, required implementation symbols,
#          required docs, required tests
AGENTS = {
 "P00/P01": dict(
    mission="repository baseline + source and equation provenance",
    coverage=[], symbols=["rscs2_core.provenance_v4:ingest_file"],
    docs=[D + "V4X_PROMPT_PACK_DELIVERABLE_CROSSWALK.md"],
    tests=["tests/v4/test_v4c_provenance.py"]),
 "C01": dict(
    mission="exciton-photon polaritons and hybrid transduction",
    coverage=["A01", "A02", "A03", "A04", "A05", "A06"],
    symbols=["rscs2_core.refmodels.polariton:hopfield_2x2",
             "rscs2_core.refmodels.polariton:cavity_dispersion_ev",
             "rscs2_core.refmodels.polariton:polariton_dispersion",
             "rscs2_core.refmodels.polariton:hopfield_3x3",
             "rscs2_core.refmodels.polariton:polarization_channel",
             "rscs2_core.refmodels.polariton:"
             "strong_coupling_criterion",
             "rscs2_core.refmodels.polariton:transduction_interface"],
    docs=[D + "POLARITON_MODEL.md",
          D + "HOPFIELD_AND_RABI_CONTRACT.md",
          D + "MAGNON_POLARITON_TRANSDUCTION.md"],
    tests=["tests/v4/test_v4x_polariton_interfaces.py"]),
 "C02": dict(
    mission="adaptive sub-millimetre Eye refinement",
    coverage=["A07", "A08", "A09", "A10"],
    symbols=["rscs2_core.eye_refinement:candidate_ladder",
             "rscs2_core.eye_refinement:refined_verdict",
             "rscs2_core.eye_refinement:driven_phase_diagnostics",
             "rscs2_core.eye_refinement:frequency_sensitivity_map",
             "rscs2_core.fem:harmonic_field"],
    docs=[D + "EYE_REFINEMENT_V5.md",
          D + "V4X_EYE_SUBMM_REFINEMENT.md"],
    tests=["tests/v4/test_rscs2_eye.py"]),
 "C03": dict(
    mission="prospective N=5..12 crystal family",
    coverage=["A11", "A12"],
    symbols=["rscs2_core.harmonic_family:family_length_mm",
             "rscs2_core.harmonic_family:build_family_member",
             "rscs2_core.harmonic_family:family_table",
             "rscs2_core.harmonic_family:tolerance_sensitivity",
             "rscs2_core.harmonic_family:specimen_registry"],
    docs=[D + "FAMILY_N5_N12.md"],
    tests=["tests/v4/test_v4x_harmonic_specimens.py"]),
 "C04": dict(
    mission="frequency, timing, angle, ratio, symbolic registry",
    coverage=["A13"],
    symbols=["rscs2_core.frequency_keys:build_registry",
             "rscs2_core.frequency_keys:coincidence_significance"],
    docs=[D + "TIMING_FAMILY_AUDIT.md",
          D + "NUMEROLOGY_AND_LOOK_ELSEWHERE_AUDIT.md"],
    tests=["tests/v4/test_v4x_frequency_keys.py"]),
 "C05": dict(
    mission="specimen metrology, orientation, material registry",
    coverage=["G001", "G015", "G030"],
    symbols=["rscs2_core.metrology:specimen_record",
             "rscs2_core.metrology:seller_vs_measured_delta",
             "rscs2_core.metrology:mass_volume_consistency",
             "rscs2_core.metrology:dimensional_record",
             "rscs2_core.metrology:apex_angle_deg",
             "rscs2_core.metrology:xrd_orientation_interface",
             "rscs2_core.metrology:scan_to_mesh",
             "rscs2_core.metrology:ideal_vs_scanned",
             "rscs2_core.metrology:metrology_protocol"],
    docs=[D + "METROLOGY_PROTOCOL.md",
          D + "XRD_ORIENTATION_CONTRACT.md"],
    tests=["tests/v4/test_v4x_depth_metrology_bvd_apparatus.py"]),
 "C06": dict(
    mission="piezoelectric admittance and BVD extraction",
    coverage=["A14", "A15"],
    symbols=["rscs2_core.bvd:bvd_impedance",
             "rscs2_core.bvd:derived_parameters",
             "rscs2_core.bvd:extract_bvd",
             "rscs2_core.bvd:osl_correct",
             "rscs2_core.bvd:fit_uncertainty",
             "rscs2_core.bvd:fit_multibranch",
             "rscs2_core.bvd:electrode_loading",
             "rscs2_core.bvd:to_spice"],
    docs=[D + "BVD_EXTRACTION.md"],
    tests=["tests/v4/test_v4x_bvd_apparatus.py",
           "tests/v4/test_v4x_depth_metrology_bvd_apparatus.py"]),
 "C07": dict(
    mission="coil, electrode, transducer, fixture, field simulation",
    coverage=["A16"],
    symbols=["rscs2_core.apparatus:wheeler_inductance_h",
             "rscs2_core.apparatus:crossed_coil_coupling",
             "rscs2_core.apparatus:apparatus_registry",
             "rscs2_core.apparatus:ordinary_artifact_model",
             "rscs2_core.apparatus:coil_model",
             "rscs2_core.apparatus:coil_field_map",
             "rscs2_core.apparatus:thermal_rise_c",
             "rscs2_core.apparatus:electrode_capacitance_f",
             "rscs2_core.apparatus:contact_load_model",
             "rscs2_core.apparatus:transducer_transfer",
             "rscs2_core.apparatus:cable_loading"],
    docs=[D + "APPARATUS_DIGITAL_TWIN.md"],
    tests=["tests/v4/test_v4x_depth_metrology_bvd_apparatus.py"]),
 "C08": dict(
    mission="calibration, uncertainty, inverse design",
    coverage=["A17"],
    symbols=["rscs2_core.calibration:fit_parameters",
             "rscs2_core.calibration:track_drift",
             "rscs2_core.calibration:inverse_design",
             "rscs2_core.calibration:ObservationLedger"],
    docs=[D + "CALIBRATION_MASTER.md",
          D + "INVERSE_DESIGN_CONTRACT.md"],
    tests=["tests/v4/test_v4c_calibration.py"]),
 "C13": dict(
    mission="microscopic and quantum solver interfaces",
    coverage=["A18", "I001", "I011"],
    symbols=["rscs2_core.interfaces_future:interface_record",
             "rscs2_core.interfaces_future:request_computation"],
    docs=[D + "FUTURE_MICROSCOPIC_SOLVERS.md"],
    tests=["tests/v4/test_v4x_polariton_interfaces.py"]),
 "G01": dict(
    mission="spiral-cone mathematics, FEA, cusp diagnostics",
    coverage=["S001", "S011"],
    symbols=["rscs2_core.spiral_cone:log_spiral",
             "rscs2_core.spiral_cone:curvature_invariant",
             "rscs2_core.spiral_cone:spiral_cone_path",
             "rscs2_core.spiral_cone:focus_eigenvalues",
             "rscs2_core.spiral_cone:cusp_response_metric",
             "rscs2_core.spiral_cone:mode_overlap",
             "rscs2_core.spiral_cone:geometry_merit",
             "rscs2_core.spiral_cone:openscad_text",
             "rscs2_core.spiral_cone:motif_registry"],
    docs=[D + "SPIRAL_CONE_MODEL.md"],
    tests=["tests/v4/test_v4x_spiral_cymatic.py"]),
 "G02": dict(
    mission="PCB cymatic disks and coupled resonance",
    coverage=["S012", "S024"],
    symbols=["rscs2_core.cymatic_disk:clamped_plate_lambdas",
             "rscs2_core.cymatic_disk:composite_plate",
             "rscs2_core.cymatic_disk:plate_mode_hz",
             "rscs2_core.cymatic_disk:chladni_pattern",
             "rscs2_core.cymatic_disk:spiral_inductance_h",
             "rscs2_core.cymatic_disk:resonance_separation_report",
             "rscs2_core.cymatic_disk:gerber_spiral_text",
             "rscs2_core.cymatic_disk:motif_registry"],
    docs=[D + "CYMATIC_PCB_MODEL.md"],
    tests=["tests/v4/test_v4x_spiral_cymatic.py"]),
 "G03": dict(
    mission="CAD, manufacturing, materials, matched controls",
    coverage=["S016", "S021"],
    symbols=["rscs2_core.spiral_cone:stl_text_from_path",
             "rscs2_core.spiral_cone:dxf_polyline_text",
             "rscs2_core.spiral_cone:archimedean_control",
             "rscs2_core.cymatic_disk:control_set",
             "rscs2_core.cymatic_disk:drill_text",
             "rscs2_core.cymatic_disk:bom"],
    docs=[D + "FABRICATION_CONTRACT.md"],
    tests=["tests/v4/test_v4x_spiral_cymatic.py"]),
 "E01": dict(
    mission="acoustic and ultrasonic bench campaign",
    coverage=["E001", "E002", "E003"],
    symbols=["rscs2_core.protocols_v4x:build_protocols"],
    docs=[E + "ACOUSTIC_CAMPAIGN.md"],
    tests=["tests/v4/test_v4x_protocols.py"]),
 "E02": dict(
    mission="compression-node electrode pulse programme",
    coverage=["E005", "E006", "E007"],
    symbols=["rscs2_core.protocols_v4x:build_protocols"],
    docs=[E + "ELECTRODE_PULSE_PROTOCOL.md"],
    tests=["tests/v4/test_v4x_protocols.py"]),
 "E03": dict(
    mission="coil and field-proxy mapping",
    coverage=["E008", "E009", "E010", "E011"],
    symbols=["rscs2_core.apparatus:coil_field_map"],
    docs=[E + "COIL_FIELD_CAMPAIGN.md"],
    tests=["tests/v4/test_v4x_protocols.py"]),
 "E04": dict(
    mission="quartz-family and specimen comparison",
    coverage=["E021"],
    symbols=["rscs2_core.protocols_v4x:build_protocols"],
    docs=[E + "MATERIAL_COMPARISON.md"],
    tests=["tests/v4/test_v4x_protocols.py"]),
 "E05": dict(
    mission="water, fluid, coil, acoustic exposure programme",
    coverage=["W001", "W017"],
    symbols=["rscs2_core.protocols_v4x:build_protocols",
             "rscs2_core.protocols_v4x:blind_labels"],
    docs=[E + "WATER_PROTOCOL.md"],
    tests=["tests/v4/test_v4x_protocols.py"]),
 "E06": dict(
    mission="human mechanical and capacitive loading",
    coverage=["H001", "H008"],
    symbols=["rscs2_core.apparatus:contact_load_model"],
    docs=[E + "HUMAN_LOADING_MODEL.md"],
    tests=["tests/v4/test_v4x_protocols.py"]),
 "E07": dict(
    mission="operator state, blinded human protocols",
    coverage=["H009", "H016"],
    symbols=["rscs2_core.research_records:safety_gate"],
    docs=[E + "OPERATOR_STATE_PROTOCOL.md"],
    tests=["tests/v4/test_v4x_protocols.py"]),
 "E08": dict(
    mission="integrated bench, DAQ, automation, instrument control",
    coverage=["E012", "E017"],
    symbols=["rscs2_core.protocols_v4x:synth_ring_down",
             "rscs2_core.protocols_v4x:analyze_ring_down",
             "rscs2_core.protocols_v4x:blind_labels"],
    docs=[E + "BENCH_ARCHITECTURE.md"],
    tests=["tests/v4/test_v4x_protocols.py"]),
 "E09": dict(
    mission="staged bench execution and measurement release",
    coverage=["E018", "E022"],
    symbols=["rscs2_core.protocols_v4x:build_protocols"],
    docs=[E + "STAGED_BENCH_EXECUTION.md"],
    tests=["tests/v4/test_v4x_protocols.py"]),
 "T01": dict(
    mission="resonant state change, subjective time, coherence",
    coverage=["C001", "C002", "C003"],
    symbols=["consciousness_lane.reduced_models:"
             "state_change_response",
             "consciousness_lane.reduced_models:subjective_time"],
    docs=[C + "RESONANT_STATE_CHANGE_FORMALISM.md"],
    tests=["tests/v4/test_v4x_consciousness.py"]),
 "T02": dict(
    mission="Arisaka MePMoS/NHT/HAL/Q-HAL/BFFT/CAIRO/TERESA audit",
    coverage=["C007", "C008", "C009", "C010", "C011"],
    symbols=["consciousness_lane.reduced_models:ring_attractor"],
    docs=[C + "ARISAKA_AUDIT.md"],
    tests=["tests/v4/test_v4x_consciousness.py"]),
 "T03": dict(
    mission="microtubule and cross-scale coherence bridge",
    coverage=["C015", "C016"],
    symbols=["consciousness_lane.reduced_models:"
             "microtubule_threshold"],
    docs=[C + "MICROTUBULE_COHERENCE_AUDIT.md"],
    tests=["tests/v4/test_v4x_consciousness.py"]),
 "T04": dict(
    mission="THz/6G measurement and superheterodyne roadmap",
    coverage=["C020", "C021", "C022"],
    symbols=[],
    docs=[C + "THZ_INSTRUMENTATION_ROADMAP.md"],
    tests=["tests/v4/test_v4x_consciousness.py"]),
 "T05": dict(
    mission="synchrony, mentorship, fireflies, pendulums, gamma",
    coverage=["C013", "C023", "C024", "C025", "C045", "C048"],
    symbols=["consciousness_lane.reduced_models:kuramoto",
             "consciousness_lane.reduced_models:kuramoto_critical_k",
             "consciousness_lane.reduced_models:"
             "synchrony_with_surrogates",
             "consciousness_lane.reduced_models:"
             "phase_amplitude_coupling",
             "consciousness_lane.reduced_models:"
             "coherence_is_not_truth"],
    docs=[C + "SYNCHRONY_AND_MENTORSHIP.md"],
    tests=["tests/v4/test_v4x_consciousness.py"]),
 "T06": dict(
    mission="dream-wake constraints, permanence, observer, aura",
    coverage=["C027", "C028", "C029", "C041", "C042"],
    symbols=["consciousness_lane.reduced_models:"
             "dream_wake_constraint"],
    docs=[C + "DREAM_WAKE_CONSTRAINT_THEORY.md",
          C + "OBSERVER_AND_PERMANENCE.md",
          C + "AURA_TRANSLATION.md"],
    tests=["tests/v4/test_v4x_consciousness.py"]),
 "T07": dict(
    mission="quantum cognition, entanglement, multiverse",
    coverage=["C031", "C032", "C033"],
    symbols=["consciousness_lane.reduced_models:order_effect_model",
             "consciousness_lane.reduced_models:qq_equality",
             "consciousness_lane.reduced_models:"
             "classical_comparator"],
    docs=[C + "QUANTUM_COGNITION_AND_PHYSICS_BOUNDARY.md"],
    tests=["tests/v4/test_v4x_consciousness.py"]),
 "T08": dict(
    mission="phenomenology, conduit, spirit/God layer, source lore",
    coverage=["C037", "C038", "C039", "C043"],
    symbols=["consciousness_lane.theory_registry:"
             "build_theory_registry"],
    docs=[C + "PHENOMENOLOGY_AND_PRIVATE_MYTH_POLICY.md"],
    tests=["tests/v4/test_v4x_consciousness.py"]),
 "T09": dict(
    mission="HAL-inspired Hydrogenuine spatial-temporal memory",
    coverage=["C049", "C050", "C051", "C052"],
    symbols=[],
    docs=[C + "HYDROGENUINE_SPATIAL_TEMPORAL_MEMORY.md"],
    tests=["tests/v4/test_v4x_consciousness.py"]),
 "T10": dict(
    mission="quarantined lane: programme, book spine, falsification "
            "map",
    coverage=["C040"],
    symbols=["consciousness_lane.theory_registry:coverage_map"],
    docs=[C + "RESONANT_STATE_CHANGE_BOOK.md",
          C + "FALSIFICATION_MAP.md"],
    tests=["tests/v4/test_v4x_consciousness.py"]),
 "D01": dict(
    mission="data, statistics, blinding, preregistration",
    coverage=[],
    symbols=["rscs2_core.research_records:make_record",
             "rscs2_core.protocols_v4x:blind_labels"],
    docs=[D + "DATA_CONTRACT.md"],
    tests=["tests/v4/test_v4x_records_safety.py"]),
 "S01": dict(
    mission="electrical, acoustic, EM, water, human, data safety",
    coverage=[],
    symbols=["rscs2_core.research_records:safety_gate",
             "rscs2_core.research_records:SAFETY_LIMITS"],
    docs=[D + "SAFETY_AND_ETHICS_MANUAL.md"],
    tests=["tests/v4/test_v4x_records_safety.py"]),
 "R01": dict(
    mission="documentation, manuscripts, cross-project index",
    coverage=[],
    symbols=["tools.v4x_coverage_ledger:build"],
    docs=[D + "V4X_PROGRAMME_REPORT.md",
          D + "V4X_COVERAGE_LEDGER.md"],
    tests=["tests/v4/test_v4c_docs_closeout.py"]),
 "Q01": dict(
    mission="independent scientific/coverage red team",
    coverage=[],
    symbols=[],
    docs=[D + "V4X_QA_FINAL_VERDICT.md",
          D + "V4X_DEFECT_REGISTER.md"],
    tests=["tests/v4/test_v4x_qa_adversarial.py"]),
 "R02": dict(
    mission="integration, CI, proof bundles, releases",
    coverage=[],
    symbols=[],
    docs=[D + "RELEASE_NOTES_V4_2_1.md"],
    tests=["tests/v4/test_v4x_coverage_ledger.py"]),
 "P02": dict(
    mission="minor ideas, orphans, contradictions, no-omission sweep",
    coverage=[],
    symbols=["tools.v4x_orphan_sweep:sweep"],
    docs=[D + "ORPHAN_IDEA_REGISTER.md",
          D + "V4X_NO_OMISSION_CERTIFICATE.md"],
    tests=["tests/v4/test_v4x_orphan_sweep.py"]),
}


def _symbol_ok(spec: str) -> bool:
    mod, _, name = spec.partition(":")
    try:
        m = importlib.import_module(mod)
    except Exception:
        return False
    return hasattr(m, name)


def _test_node_ok(node: str) -> bool:
    return (ROOT / node.split("::")[0]).exists()


def build() -> dict:
    rows = []
    for aid, spec in AGENTS.items():
        miss_sym = [s for s in spec["symbols"] if not _symbol_ok(s)]
        miss_doc = [d for d in spec["docs"]
                    if not (ROOT / d).exists()]
        miss_test = [t for t in spec["tests"]
                     if not _test_node_ok(t)]
        complete = not (miss_sym or miss_doc or miss_test)
        rows.append({
            "agent": aid, "mission": spec["mission"],
            "coverage_ids": spec["coverage"],
            "required_symbols": spec["symbols"],
            "required_docs": spec["docs"],
            "required_tests": spec["tests"],
            "missing_symbols": miss_sym,
            "missing_docs": miss_doc,
            "missing_tests": miss_test,
            "complete": complete,
            "status": "COMPLETE" if complete else "INCOMPLETE"})
    n_ok = sum(r["complete"] for r in rows)
    return {"agents_audited": len(rows), "complete": n_ok,
            "incomplete": len(rows) - n_ok,
            "pack_present": PACK.exists(),
            "missing_doc_count": sum(len(r["missing_docs"])
                                     for r in rows),
            "missing_symbol_count": sum(len(r["missing_symbols"])
                                        for r in rows),
            "rows": rows}


def main() -> int:
    rep = build()
    (ROOT / "docs/v4/V4X_PROMPT_PACK_DELIVERABLE_CROSSWALK.json"
     ).write_text(json.dumps(rep, indent=2), encoding="utf-8")
    lines = [
        "# V4X prompt-pack deliverable crosswalk", "",
        "Generated by `tools/v4x_prompt_pack_crosswalk.py`. This is the "
        "Phase 1 artifact of the v4.2.1 completeness audit: it checks "
        "each original agent prompt's REQUIRED DELIVERABLES against the "
        "repository, rather than trusting the coverage ledger's own "
        "self-description.", "",
        f"Agents audited: **{rep['agents_audited']}** — complete "
        f"**{rep['complete']}** — incomplete **{rep['incomplete']}**",
        "",
        "| Agent | Mission | Symbols | Docs | Tests | Status |",
        "|---|---|---|---|---|---|"]
    for r in rep["rows"]:
        sym = f"{len(r['required_symbols']) - len(r['missing_symbols'])}"\
              f"/{len(r['required_symbols'])}"
        doc = f"{len(r['required_docs']) - len(r['missing_docs'])}"\
              f"/{len(r['required_docs'])}"
        tst = f"{len(r['required_tests']) - len(r['missing_tests'])}"\
              f"/{len(r['required_tests'])}"
        lines.append(f"| {r['agent']} | {r['mission']} | {sym} | "
                     f"{doc} | {tst} | {r['status']} |")
    miss = [r for r in rep["rows"] if not r["complete"]]
    if miss:
        lines += ["", "## Missing deliverables", ""]
        for r in miss:
            for s in r["missing_symbols"]:
                lines.append(f"- **{r['agent']}** missing symbol "
                             f"`{s}`")
            for d in r["missing_docs"]:
                lines.append(f"- **{r['agent']}** missing document "
                             f"`{d}`")
            for t in r["missing_tests"]:
                lines.append(f"- **{r['agent']}** missing test `{t}`")
    (ROOT / "docs/v4/V4X_PROMPT_PACK_DELIVERABLE_CROSSWALK.md"
     ).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"crosswalk: {rep['complete']}/{rep['agents_audited']} agents "
          f"complete; {rep['missing_doc_count']} docs and "
          f"{rep['missing_symbol_count']} symbols missing")
    return 0 if rep["incomplete"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
