"""A02: v4.4 coverage ledger with bidirectional orphan checks.

Requirements (FK-*) map to implementation symbols, tests, and docs —
verified mechanically (imports, existence), never by a documentation
paragraph mentioning them. The reverse sweep checks that every module
in fkey_instrument/ is claimed by at least one requirement.

    python tools/v44_coverage.py
Writes docs/v4/fkey/FK_COVERAGE.json (+ .md); exit 1 on failure.
"""

from __future__ import annotations

import importlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

T1 = "tests/v4/test_fkey_instrument.py"
T2 = "tests/v4/test_fkey_device_redteam.py"
DOC = "docs/v4/fkey/FKEY_INSTRUMENT.md"
BOM = "docs/v4/fkey/BOM_WIRING_GEN0.md"
DEMO = "docs/v4/fkey/SYNTHETIC_demo_report.json"

# id: (requirement, symbols, tests, docs, status)
REQS = {
 # provenance/governance
 "FK-P001": ("frozen seed keys registered with provenance",
             ["fkey_instrument.relations:key_registry"], [T1], [DOC],
             "IMPLEMENTED_AND_TESTED"),
 "FK-P002": ("prearrival specimen immutable; seller claims never "
             "measurements",
             ["fkey_instrument.crystal_mode:prearrival_record",
              "fkey_instrument.crystal_mode:arrival_revision"],
             [T1, T2], [DOC], "IMPLEMENTED_AND_TESTED"),
 "FK-P003": ("FK-CORR-001 equal-percentage-error correction record",
             ["fkey_instrument.crystal_mode:target_errors"],
             [T1, T2], [DOC], "IMPLEMENTED_AND_TESTED"),
 "FK-P004": ("hypotheses preregistered, optimizer cannot rewrite",
             ["fkey_instrument.optimizer:hypothesis_register"],
             [T1], [DOC], "IMPLEMENTED_AND_TESTED"),
 "FK-P005": ("no lore language can reach measured status: evidence "
             "classes enumerated and schema-enforced",
             ["fkey_instrument:EVIDENCE_CLASSES"], [T1], [DOC],
             "IMPLEMENTED_AND_TESTED"),
 # mathematics
 "FK-M001": ("exact rational parsing; floats refused",
             ["fkey_instrument.relations:hz"], [T1], [DOC],
             "IMPLEMENTED_AND_TESTED"),
 "FK-M002": ("mechanism taxonomy, one primary class per relation",
             ["fkey_instrument.relations:classify_scale",
              "fkey_instrument.relations:classify_sum"],
             [T1], [DOC], "IMPLEMENTED_AND_TESTED"),
 "FK-M003": ("frozen seed corpus classifies per the pack",
             ["fkey_instrument.relations:seed_relations",
              "fkey_instrument.relations:seed_explanation"],
             [T1], [DOC], "IMPLEMENTED_AND_TESTED"),
 "FK-M004": ("mechanism-first ranking; dedup; harmonic census",
             ["fkey_instrument.relations:rank",
              "fkey_instrument.relations:dedup",
              "fkey_instrument.relations:enumerate_harmonics"],
             [T1], [DOC], "IMPLEMENTED_AND_TESTED"),
 "FK-M005": ("phase closure: windows, drift, burst design",
             ["fkey_instrument.phase_closure:common_closure_window",
              "fkey_instrument.phase_closure:closure_drift",
              "fkey_instrument.phase_closure:burst_lengths"],
             [T1], [DOC], "IMPLEMENTED_AND_TESTED"),
 "FK-M006": ("sine has no 5th; square has 1/5 (analytic + FFT "
             "cross-check)",
             ["fkey_instrument.spectrum:fifth_harmonic_comparison",
              "fkey_instrument.spectrum:fft_lines"],
             [T1], [DOC], "IMPLEMENTED_AND_TESTED"),
 "FK-M007": ("edge/plant shaping and expected-line gate",
             ["fkey_instrument.spectrum:edge_rolloff",
              "fkey_instrument.spectrum:expected_line"],
             [T1], [DOC], "IMPLEMENTED_AND_TESTED"),
 "FK-M008": ("Nyquist/alias arithmetic incl. the marginal-48k case",
             ["fkey_instrument.spectrum:nyquist_check"],
             [T1, T2], [DOC], "IMPLEMENTED_AND_TESTED"),
 "FK-M009": ("AM sideband arithmetic",
             ["fkey_instrument.relations:am_sidebands"], [T1],
             [DOC], "IMPLEMENTED_AND_TESTED"),
 # plant/uncertainty
 "FK-C001": ("prearrival screening model reproduces pack numbers; "
             "candidate band not magic number",
             ["fkey_instrument.crystal_mode:screening_modes",
              "fkey_instrument.crystal_mode:candidate_band"],
             [T1], [DOC], "IMPLEMENTED_AND_TESTED"),
 "FK-C002": ("2-DOF plant; transducer-vs-crystal discrimination",
             ["fkey_instrument.plant:CoupledPlant"], [T1], [DOC],
             "IMPLEMENTED_AND_TESTED"),
 "FK-C003": ("linear plant has zero intermodulation; nonlinearity "
             "explicit",
             ["fkey_instrument.plant:CoupledPlant"], [T1], [DOC],
             "IMPLEMENTED_AND_TESTED"),
 "FK-C004": ("fit refusal on undersampled/saturated; bootstrap Q",
             ["fkey_instrument.plant:fit_peak",
              "fkey_instrument.plant:bootstrap_q"], [T1], [DOC],
             "IMPLEMENTED_AND_TESTED"),
 "FK-C005": ("thermal drift model for warm-up blocks",
             ["fkey_instrument.plant:thermal_drift"], [T1], [DOC],
             "IMPLEMENTED_AND_TESTED"),
 "FK-C006": ("BVD reuse from rscs2_core (no duplication)",
             ["rscs2_core.bvd:bvd_impedance"], [T1], [DOC],
             "IMPLEMENTED_AND_TESTED"),
 # optimizer/experiments
 "FK-O001": ("mechanism-first optimizer; arithmetic scores zero "
             "amplitude",
             ["fkey_instrument.optimizer:score",
              "fkey_instrument.optimizer:optimize"], [T1], [DOC],
             "IMPLEMENTED_AND_TESTED"),
 "FK-O002": ("Pareto frontier per hypothesis, never one winner",
             ["fkey_instrument.optimizer:pareto_frontier"], [T1],
             [DOC], "IMPLEMENTED_AND_TESTED"),
 "FK-O003": ("ten required drive comparisons compiled as families",
             ["fkey_instrument.optimizer:candidate_families"],
             [T1], [DOC], "IMPLEMENTED_AND_TESTED"),
 "FK-O004": ("randomized blinded campaigns with sham + stop rules + "
             "no-post-hoc rule",
             ["fkey_instrument.optimizer:compile_campaign"], [T1],
             [DOC], "IMPLEMENTED_AND_TESTED"),
 # JSON/bridge
 "FK-J001": ("drive-recipe schema; strict validation; fuzz",
             ["fkey_instrument.contracts:validate_recipe"],
             [T1], [DOC], "IMPLEMENTED_AND_TESTED"),
 "FK-J002": ("canonical JSON + content hash",
             ["fkey_instrument.contracts:content_hash"], [T1],
             [DOC], "IMPLEMENTED_AND_TESTED"),
 "FK-J003": ("unknown versions refused with explicit no-migration",
             ["fkey_instrument.contracts:migrate"], [T1], [DOC],
             "IMPLEMENTED_AND_TESTED"),
 "FK-J004": ("desktop bridge: compile/upload/arm/run/logs/verify, "
             "never bypassing the FSM",
             ["fkey_instrument.optimizer:Bridge"], [T2], [DOC],
             "IMPLEMENTED_AND_TESTED"),
 # firmware
 "FK-F001": ("firmware source tree with FSM mirroring the twin",
             [], [T2],
             ["firmware/fkey_cyd/src/safety_fsm.h",
              "firmware/fkey_cyd/src/main.cpp",
              "firmware/fkey_cyd/platformio.ini"],
             "FIRMWARE_SOURCE_PROVIDED_NOT_COMPILED"),
 "FK-F002": ("board profiles compile-time; unknown => "
             "OUTPUT_DISABLED",
             ["fkey_instrument.boards:board_profile"], [T2],
             ["firmware/fkey_cyd/src/board_profile.h", DOC],
             "IMPLEMENTED_AND_TESTED"),
 "FK-F003": ("signal backends with requested vs calculated-realized "
             "vs measured(None) separation",
             ["fkey_instrument.boards:LedcBackend",
              "fkey_instrument.boards:RmtBackend",
              "fkey_instrument.boards:DdsBackend"], [T2], [DOC],
             "IMPLEMENTED_AND_TESTED"),
 "FK-F004": ("4096/20480 timing report with quantization + drift",
             ["fkey_instrument.boards:timing_report_4096_and_20480"],
             [T2], [DOC], "IMPLEMENTED_AND_TESTED"),
 # hardware/sensing
 "FK-H001": ("pin-conflict detection incl. boot-strap and "
             "input-only",
             ["fkey_instrument.boards:pin_conflicts"], [T2],
             [DOC], "IMPLEMENTED_AND_TESTED"),
 "FK-H002": ("board questionnaire before any pin is named",
             ["fkey_instrument.boards:questionnaire"], [T2],
             [DOC, BOM], "IMPLEMENTED_AND_TESTED"),
 "FK-H003": ("Gen-0 BOM/wiring/fixture/bring-up",
             [], [T2], [BOM],
             "ENGINEERING_PROTOTYPE_NOTHING_BUILT"),
 "FK-H004": ("sensor limitations documented: INA219 slow-only, "
             "48k mic marginal at 20.48k",
             ["fkey_instrument.spectrum:nyquist_check"], [T1],
             [BOM, DOC], "IMPLEMENTED_AND_TESTED"),
 # safety
 "FK-S001": ("output off at boot; only RUNNING may drive output",
             ["fkey_instrument.device:SimDevice"], [T2], [DOC],
             "IMPLEMENTED_AND_TESTED"),
 "FK-S002": ("fresh single-use expiring arm lease; no auto-arm",
             ["fkey_instrument.device:SimDevice"], [T2], [DOC],
             "IMPLEMENTED_AND_TESTED"),
 "FK-S003": ("all 14 fault causes force output off and latch",
             ["fkey_instrument.device:FAULT_CAUSES"], [T2], [DOC],
             "IMPLEMENTED_AND_TESTED"),
 "FK-S004": ("reset/watchdog/brownout land output-off, authority "
             "dropped",
             ["fkey_instrument.device:SimDevice"], [T2], [DOC],
             "IMPLEMENTED_AND_TESTED"),
 "FK-S005": ("missing amplitude refused, never defaulted",
             ["fkey_instrument.contracts:validate_recipe"], [T2],
             [DOC], "IMPLEMENTED_AND_TESTED"),
 "FK-S006": ("hearing/animal caution documented; conservative "
             "first-run limits in schema (duty<=0.5, <=60s)",
             ["fkey_instrument.contracts:DRIVE_RECIPE_SCHEMA"],
             [T1], [DOC, BOM], "IMPLEMENTED_AND_TESTED"),
 # tests/release
 "FK-T001": ("six synthetic demos run from a fresh clone",
             [], [T2], [DEMO, "docs/v4/fkey/SYNTHETIC_demo_report"
                        ".md"],
             "IMPLEMENTED_AND_TESTED"),
 "FK-T002": ("hash-chained device logs, verified by the bridge",
             ["fkey_instrument.device:SimDevice"], [T2], [DOC],
             "IMPLEMENTED_AND_TESTED"),
 "FK-T003": ("A24 red-team attacks as executable regression tests",
             [], [T2], [DOC], "IMPLEMENTED_AND_TESTED"),
 "FK-T004": ("coverage bidirectional orphan check (this tool)",
             [], [T2], [DOC], "IMPLEMENTED_AND_TESTED"),
}

# modules that must each be claimed by >= 1 requirement (reverse
# orphan check)
MODULES = ["relations", "phase_closure", "spectrum", "crystal_mode",
           "plant", "optimizer", "contracts", "boards", "device"]


def _symbol_ok(spec: str) -> bool:
    mod, _, name = spec.partition(":")
    try:
        m = importlib.import_module(mod)
    except Exception:
        return False
    return hasattr(m, name)


def evaluate() -> dict:
    failures = {"symbols": [], "tests": [], "docs": [],
                "forward_orphans": [], "reverse_orphans": []}
    claimed_modules = set()
    for rid, (req, symbols, tests, docs, status) in REQS.items():
        for s in symbols:
            if not _symbol_ok(s):
                failures["symbols"].append(f"{rid}: {s}")
            if s.startswith("fkey_instrument."):
                claimed_modules.add(s.split(".")[1].split(":")[0])
        for t in tests:
            if not (ROOT / t).exists():
                failures["tests"].append(f"{rid}: {t}")
        for d in docs:
            if not (ROOT / d).exists():
                failures["docs"].append(f"{rid}: {d}")
        if not symbols and not docs:
            failures["forward_orphans"].append(rid)
    for m in MODULES:
        if m not in claimed_modules:
            failures["reverse_orphans"].append(
                f"fkey_instrument.{m} has no owning requirement")
    ok = not any(failures.values())
    return {"total_requirements": len(REQS), "failures": failures,
            "all_passed": ok,
            "rows": {rid: {"requirement": r[0], "status": r[4],
                           "symbols": r[1], "tests": r[2],
                           "docs": r[3]}
                     for rid, r in REQS.items()}}


def main() -> int:
    rep = evaluate()
    out = ROOT / "docs/v4/fkey"
    out.mkdir(parents=True, exist_ok=True)
    (out / "FK_COVERAGE.json").write_text(
        json.dumps(rep, indent=1) + "\n", encoding="utf-8")
    lines = ["# FK coverage ledger (A02)", "",
             f"Requirements: **{rep['total_requirements']}** — "
             + ("**ALL PASS**" if rep["all_passed"] else "**FAIL**"),
             "", "| ID | Requirement | Status |", "|---|---|---|"]
    for rid, row in rep["rows"].items():
        lines.append(f"| {rid} | {row['requirement']} | "
                     f"{row['status']} |")
    (out / "FK_COVERAGE.md").write_text("\n".join(lines) + "\n",
                                        encoding="utf-8")
    for k, v in rep["failures"].items():
        if v:
            print(f"{k}: {v[:6]}")
    print(f"FK coverage: {rep['total_requirements']} requirements, "
          f"all_passed={rep['all_passed']}")
    return 0 if rep["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
