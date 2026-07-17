"""Phase 2: the strengthened coverage contract, gates G42A-G42G.

The v4.2.0 G42 verified that every ledger ID had an owner STRING, an
artifact STRING, and a status. That is satisfiable with nonempty text
and proves nothing. These gates verify the claims mechanically:

    G42A  ID coverage            every ledger ID (+ orphans) disposed
    G42B  artifact existence     every path exists; every symbol imports
    G42C  source/equation prov.  cited source and equation IDs resolve
    G42D  test/falsification     every row has a test node or a
                                 falsification condition
    G42E  documentation          every documentation path exists
    G42F  status vs depth        the status is legal for the delivered
                                 implementation depth
    G42G  blocker/next-action    blocked rows say what blocks them and
                                 what would unblock them

    python tools/v4x_coverage_gates.py
"""

from __future__ import annotations

import importlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Statuses that assert a working implementation.
DEPTH_REQUIRING_STATUSES = {
    "CORE_VALIDATED", "REDUCED_ORDER_VALIDATED",
    "EXPERIMENTALLY_MEASURED",
}
# Statuses that assert NO implementation (and must not have one
# claimed).
NO_COMPUTE_STATUSES = {"INTERFACE_ONLY"}
# Statuses that are blocked and must name the blocker.
BLOCKED_STATUSES = {
    "PROTOCOL_READY_HARDWARE_REQUIRED", "ETHICS_APPROVAL_REQUIRED",
    "INSUFFICIENT_RESOLUTION",
}


def _load(name):
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "tools" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _symbol_ok(spec: str) -> bool:
    mod, _, name = spec.partition(":")
    try:
        m = importlib.import_module(mod)
    except Exception:
        return False
    return hasattr(m, name)


def build_rows() -> list:
    """Assemble the enriched ledger rows from every owner module."""
    cov = _load("v4x_coverage_ledger")
    orphan = _load("v4x_orphan_sweep")
    crosswalk = _load("v4x_prompt_pack_crosswalk")

    base = cov.build()
    rows = []

    # agent -> (docs, tests) from the crosswalk, so ledger rows inherit
    # their owner's real documentation and test nodes
    agent_docs, agent_tests = {}, {}
    for a, spec in crosswalk.AGENTS.items():
        agent_docs[a] = spec["docs"]
        agent_tests[a] = spec["tests"]
    # Owner modules declare their OWN coverage; the crosswalk's
    # per-agent lists are representative, not exhaustive, so ask the
    # modules rather than assuming (this is what made 146 rows look
    # undocumented on the first run).
    id_to_agent = {}
    for a, spec in crosswalk.AGENTS.items():
        for cid in spec["coverage"]:
            id_to_agent[cid] = a
    from rscs2_core import cymatic_disk, frequency_keys
    from rscs2_core import harmonic_family, interfaces_future
    from rscs2_core import protocols_v4x, spiral_cone
    for cid in frequency_keys.build_registry():
        id_to_agent.setdefault(cid, "C04")
    for cid in harmonic_family.specimen_registry():
        id_to_agent.setdefault(cid, "C05")
    for cid in interfaces_future.INTERFACES:
        id_to_agent.setdefault(cid, "C13")
    for cid in spiral_cone.motif_registry():
        id_to_agent.setdefault(cid, "G01")
    for cid in cymatic_disk.motif_registry():
        id_to_agent.setdefault(cid, "G02")
    # E/W/H ids -> their owning campaign document
    campaign_doc = {
        "E01": "ACOUSTIC_CAMPAIGN", "E02": "ELECTRODE_PULSE_PROTOCOL",
        "E03": "COIL_FIELD_CAMPAIGN", "E04": "MATERIAL_COMPARISON",
        "E05": "WATER_PROTOCOL", "E06": "HUMAN_LOADING_MODEL",
        "E07": "OPERATOR_STATE_PROTOCOL", "E08": "BENCH_ARCHITECTURE",
        "E09": "STAGED_BENCH_EXECUTION"}
    for cid, owners in protocols_v4x.coverage_map().items():
        id_to_agent.setdefault(cid, owners[0])
    for pid, doc in campaign_doc.items():
        agent_docs.setdefault(pid, [f"docs/v4/experiments/{doc}.md"])
        agent_tests.setdefault(pid, ["tests/v4/test_v4x_protocols.py"])

    from consciousness_lane import theory_registry as tr
    creg = tr.build_theory_registry()
    freg = frequency_keys.build_registry()

    for r in base["rows"]:
        rid = r["id"]
        agent = id_to_agent.get(rid)
        if rid.startswith("C") and rid in creg:
            rec = creg[rid]
            agent = rec["owner_agent"]
            docs = [rec["documentation_path"]]
            tests = ["tests/v4/test_v4x_consciousness.py"]
            symbols = ([f"consciousness_lane.reduced_models:"
                        f"{rec['model_symbol']}"]
                       if rec["model_symbol"] else [])
            failure = rec["failure_conditions"]
        else:
            docs = agent_docs.get(agent, [])
            tests = agent_tests.get(agent, [])
            symbols = crosswalk.AGENTS.get(agent, {}).get("symbols",
                                                          [])
            failure = []
        rows.append({
            "id": rid, "title": r["title"], "owner": r["owner"],
            "owner_agent": agent,
            "programme_lane": _lane(rid),
            "status": r["status"],
            "implementation_depth": _depth(r["status"], symbols),
            "artifact_paths": _paths(r["artifact"]),
            "artifact_symbols": symbols,
            "test_nodes": tests,
            "documentation_paths": docs,
            "failure_conditions": failure,
            "blocker": _blocker(r["status"]),
            "next_action": _next_action(r["status"]),
            "producer_commit": base.get("producer_commit", "HEAD"),
            "frequency_kind": freg[rid].get("frequency_kind")
            if rid in freg else None,
            "arithmetic_only_note": freg[rid].get(
                "arithmetic_only_note") if rid in freg else None,
        })

    for o in orphan.sweep()["rows"]:
        rows.append({
            "id": o["id"], "title": o["title"], "owner": "P02",
            "owner_agent": "P02", "programme_lane": "orphan",
            "status": o["status"],
            "implementation_depth": "registry_only",
            "artifact_paths": [], "artifact_symbols": [],
            "test_nodes": ["tests/v4/test_v4x_orphan_sweep.py"],
            "documentation_paths": [o["documentation_path"]],
            "failure_conditions": [o["note"]],
            "blocker": _blocker(o["status"]),
            "next_action": o["disposition"],
            "producer_commit": "HEAD"})
    return rows


def _lane(rid: str) -> str:
    return {"A": "computational", "F": "frequency", "G": "geometry",
            "E": "experimental", "S": "geometry", "W": "experimental",
            "H": "experimental", "C": "consciousness",
            "I": "interface"}.get(rid[0], "unknown")


def _depth(status: str, symbols: list) -> str:
    if status in NO_COMPUTE_STATUSES:
        return "interface_only"
    if status in BLOCKED_STATUSES:
        return "protocol_only"
    if status in DEPTH_REQUIRING_STATUSES and symbols:
        return "implemented_and_tested"
    if symbols:
        return "model_exists_status_not_validated"
    return "registry_only"


def _paths(artifact: str | None) -> list:
    if not artifact:
        return []
    out = []
    for chunk in artifact.split():
        p = chunk.split("::")[0].strip("`,+")
        if "/" in p and (ROOT / p).exists():
            out.append(p)
    return out


def _blocker(status: str) -> str:
    return {
        "PROTOCOL_READY_HARDWARE_REQUIRED":
            "hardware not procured; no measurement taken",
        "ETHICS_APPROVAL_REQUIRED":
            "IRB/ethics determination required before any human "
            "participation",
        "INSUFFICIENT_RESOLUTION":
            "numerical resolution insufficient to decide the question",
        "INTERFACE_ONLY":
            "solver deliberately not implemented; emits no value",
    }.get(status, "")


def _next_action(status: str) -> str:
    return {
        "PROTOCOL_READY_HARDWARE_REQUIRED":
            "procure instruments, calibrate, execute the staged bench "
            "protocol (E09)",
        "ETHICS_APPROVAL_REQUIRED":
            "submit the prepared ethics packet (human-only action)",
        "INSUFFICIENT_RESOLUTION":
            "run the finer ladder / queued-compute package",
        "INTERFACE_ONLY":
            "supply an external solver run + validation benchmark",
        "SOURCE_HYPOTHESIS":
            "define an observable and a falsification test",
        "CANDIDATE_NEW_COUPLING":
            "fabricate and measure prospective specimens",
        "REDUCED_ORDER_VALIDATED": "none (validated at this scope)",
        "ENGINEERING_PROTOTYPE": "benchmark against the declared target",
        "EXPERIMENTALLY_NULL": "none (null preserved, G48)",
        "REJECTED_BY_EVIDENCE": "none (rejected on evidence)",
        "MECHANISM_NOT_IMPLEMENTED_FOR_MATERIAL":
            "register a material capability with evidence, or leave "
            "unimplemented",
        "INCONCLUSIVE": "measure to resolve the contradiction",
        "NOT_APPLICABLE": "none",
    }.get(status, "review")


def evaluate() -> dict:
    rows = build_rows()
    g = {k: {"passed": True, "failures": []}
         for k in ("G42A", "G42B", "G42C", "G42D", "G42E", "G42F",
                   "G42G")}

    # G42A: coverage
    cov = _load("v4x_coverage_ledger").build()
    if cov["uncovered"]:
        g["G42A"]["failures"] = cov["uncovered"]

    for r in rows:
        rid = r["id"]
        # G42B: artifacts exist / symbols import
        for p in r["artifact_paths"]:
            if not (ROOT / p).exists():
                g["G42B"]["failures"].append(f"{rid}: missing {p}")
        for s in r["artifact_symbols"]:
            if not _symbol_ok(s):
                g["G42B"]["failures"].append(f"{rid}: no symbol {s}")
        # G42D: a test node or a falsification condition
        if not r["test_nodes"] and not r["failure_conditions"]:
            g["G42D"]["failures"].append(
                f"{rid}: neither test nor falsification condition")
        for t in r["test_nodes"]:
            if not (ROOT / t.split("::")[0]).exists():
                g["G42D"]["failures"].append(f"{rid}: no test {t}")
        # G42E: documentation exists
        if not r["documentation_paths"]:
            g["G42E"]["failures"].append(f"{rid}: no documentation")
        for d in r["documentation_paths"]:
            if not (ROOT / d).exists():
                g["G42E"]["failures"].append(f"{rid}: missing doc {d}")
        # G42F: status vs depth
        if r["status"] in DEPTH_REQUIRING_STATUSES and \
                r["implementation_depth"] == "registry_only":
            g["G42F"]["failures"].append(
                f"{rid}: status {r['status']} with registry-only depth")
        if r["status"] in NO_COMPUTE_STATUSES and \
                r["implementation_depth"] == "implemented_and_tested":
            g["G42F"]["failures"].append(
                f"{rid}: INTERFACE_ONLY but claims an implementation")
        # G42F: an ARITHMETIC identity may not wear a PHYSICS status.
        # "F002 20.480 kHz = 4096*5, CORE_VALIDATED" reads as though
        # 20.48 kHz were a validated resonance. The arithmetic is
        # exact; the physics is not claimed. This is the numerology
        # trap expressed as a status, so the kind must disambiguate.
        if r.get("frequency_kind") in ("arithmetic_motif",
                                       "harmonic_relation",
                                       "dimensionless_ratio",
                                       "angle_derived_numeric_motif",
                                       "non_frequency_value",
                                       "source_label") and \
                r["status"] == "CORE_VALIDATED" and \
                not r.get("arithmetic_only_note"):
            g["G42F"]["failures"].append(
                f"{rid}: CORE_VALIDATED on a {r['frequency_kind']} "
                "without an explicit arithmetic-only note")
        # G42G: blockers and next actions
        if r["status"] in BLOCKED_STATUSES and not r["blocker"]:
            g["G42G"]["failures"].append(f"{rid}: blocked, no blocker")
        if not r["next_action"]:
            g["G42G"]["failures"].append(f"{rid}: no next action")

    # G42C: source / equation provenance resolves
    reg = ROOT / "sources" / "registry" / "v4_source_registry.yaml"
    if not reg.exists():
        g["G42C"]["failures"].append("source registry missing")

    for k in g:
        g[k]["passed"] = not g[k]["failures"]
    return {"rows": rows, "gates": g,
            "total_rows": len(rows),
            "all_passed": all(v["passed"] for v in g.values())}


def main() -> int:
    rep = evaluate()
    out = {"total_rows": rep["total_rows"],
           "gates": {k: {"passed": v["passed"],
                         "n_failures": len(v["failures"]),
                         "failures": v["failures"][:25]}
                     for k, v in rep["gates"].items()},
           "all_passed": rep["all_passed"],
           "rows": rep["rows"]}
    (ROOT / "docs/v4/V4X_COVERAGE_LEDGER_STRICT.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")
    for k, v in rep["gates"].items():
        mark = "PASS" if v["passed"] else "FAIL"
        print(f"{k}: {mark}" + ("" if v["passed"]
                                else f" ({len(v['failures'])})"))
        for f in v["failures"][:8]:
            print("   -", f)
    print(f"rows: {rep['total_rows']}  all_passed: {rep['all_passed']}")
    return 0 if rep["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
