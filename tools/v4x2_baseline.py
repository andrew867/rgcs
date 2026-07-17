"""B00: post-closeout baseline snapshot (coverage B001-B008).

Emits a machine-readable JSON handoff describing the verified state of
the repository after the v4.2.1 closeout: HEAD, tags by object id,
release/asset state, test counts from RELEASE_METADATA (never prose),
the final Eye verdict, resource-model facts, environment, blockers,
and next actions.

Works from a fresh clone: everything read is tracked in the repo or
queried from git itself. Facts that need the network (release page,
CI) are captured when available and marked "unverified_offline"
otherwise, never guessed.

    python tools/v4x2_baseline.py           # writes the snapshot
    python tools/v4x2_baseline.py --check   # verify frozen history only
"""

from __future__ import annotations

import json
import pathlib
import platform
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "v4" / "V4X2_BASELINE_HANDOFF.json"

# Frozen authorities: tag -> full commit id. Verified by OBJECT ID.
FROZEN_TAGS = {
    "v2.0.0": "f9fd2c20a05334e12ac9113ba86853c6591fc84e",
    "v3.0.0": "83521f73d6ad02b009ada88f3b8d33a8a00fc253",
    "v3.0.1": "70d032ac25db28e98d217d7bf3311a9013b878ee",
    "v4.0.0": "2fed8fdc5b8c7f11abd880a91dbc84ad7b9004ae",
    "v4.1.0": "4c2a1cc1989fa76e62c3aaade389e1766560f305",
    "v4.1.1": "448037bd284d403cd1d3c9dddb8ec79c3dcee2df",
    "v4.2.0": "d253c2f43206d5d00325f54cb1b62744dcd3e364",
    "v4.2.1": "46074c357aec570075132e876a60cde96680af4c",
}
V2_ARCHIVE_AUTHORITY = "715486b"


def _git(*args) -> str:
    return subprocess.run(["git", *args], capture_output=True,
                          text=True, cwd=ROOT, check=False
                          ).stdout.strip()


def verify_frozen() -> dict:
    """B002: tags by object id + byte-identical v2 archive."""
    problems = []
    tags = {}
    for tag, want in FROZEN_TAGS.items():
        got = _git("rev-parse", f"{tag}^{{commit}}")
        tags[tag] = got
        if got != want:
            problems.append(f"tag {tag}: {got} != frozen {want}")
    diff = _git("diff", "--stat", V2_ARCHIVE_AUTHORITY, "HEAD", "--",
                "archive/v2.0.0")
    if diff:
        problems.append("archive/v2.0.0 modified since authority")
    return {"tags": tags, "archive_v2_intact": not diff,
            "problems": problems, "passed": not problems}


def classify_tree() -> dict:
    """B003: dirty/untracked classification. Generated evidence and
    scratch are distinguished from unrelated user work; nothing is
    deleted."""
    entries = []
    for line in _git("status", "--porcelain").splitlines():
        state, path = line[:2].strip(), line[3:].strip()
        if path.startswith(("release/",)):
            kind = "generated_release_asset"
        elif "baseline/" in path or path.endswith(
                "qa_audit_v4_results.json"):
            kind = "scanner_state_records_HEAD"
        elif "scratch" in path or path.endswith((".msh", ".geo")):
            kind = "regenerable_scratch"
        else:
            kind = "unclassified_user_work_PRESERVE"
        entries.append({"state": state, "path": path, "kind": kind})
    return {"entries": entries,
            "rule": "nothing here is deleted; unclassified entries "
                    "are preserved and flagged for a human"}


def eye_state() -> dict:
    """B005: final Eye verdict + resource facts, from the artifacts."""
    v5 = ROOT / "docs/v4/proof/C02/refinement_ladder_v5.json"
    out = {"artifact": str(v5.relative_to(ROOT))}
    if v5.exists():
        d = json.loads(v5.read_text(encoding="utf-8"))
        rv = d["refined_verdict"]
        out.update({
            "verdict": rv["classification"],
            "separation_mm": rv["separation_mm"],
            "halfwidth_mm": rv["candidate_halfwidth_mm"],
            "resolution_status": d["resolution_status"],
            "levels": {k: {"spacing_mm": v["element_spacing_mm"],
                           "centroid_mm": v["centroid_mm"],
                           "n_dof": v["n_dof"]}
                       for k, v in d["levels"].items()},
            "canonical_v41_record": d["canonical_record"],
            "stopped_before_cl": d.get("stopped_before_cl"),
        })
    out["resource_facts"] = {
        "measured_peak_gb_at_cl1_5": 13.9,
        "machine_ram_gb": 31.6,
        "cl1_25_projection_gb": "45-71 (calibrated dof^2 model)",
        "failed_estimate_defect": "first estimate used dof^1.5 (2-D "
                                  "rule) -> 0.29 GB, wrong ~150x; "
                                  "preserved as a defect record, "
                                  "see docs/v4/V4X_DEFECT_REGISTER.md",
    }
    return out


def build() -> dict:
    meta_p = ROOT / "docs/v4/RELEASE_METADATA.json"
    meta = json.loads(meta_p.read_text(encoding="utf-8")) \
        if meta_p.exists() else {}
    # release/CI facts: try the network, mark honestly if absent
    release = {"source": "gh api", "verified": False}
    try:
        r = subprocess.run(
            ["gh", "release", "view", "v4.2.1", "--json",
             "tagName,assets", "--jq",
             "{tag: .tagName, n_assets: (.assets|length)}"],
            capture_output=True, text=True, cwd=ROOT, timeout=30)
        if r.returncode == 0 and r.stdout.strip():
            release.update(json.loads(r.stdout))
            release["verified"] = True
    except Exception:                                   # noqa: BLE001
        release["note"] = "unverified_offline"
    return {
        "schema": "rgcs.v4x2.baseline_handoff/1",
        "programme": "Post-v4.2 Emergent Resonator and "
                     "Structured-Wave Expansion",
        "repository": {
            "head": _git("rev-parse", "HEAD"),
            "branch": _git("branch", "--show-current"),
            "describe": _git("describe", "--tags", "--always"),
        },
        "branch_decision": {
            "programme_branch": "v4-dev",
            "marker_branch": "emergent-resonator (pointer at the "
                             "start commit)",
            "reason": "hosted CI triggers on v4-dev; running the "
                      "programme on a parallel branch would bypass "
                      "the CI gate every prior release used. The "
                      "start point is recorded as a branch pointer "
                      "so the programme's base commit is auditable.",
        },
        "frozen_history": verify_frozen(),
        "working_tree": classify_tree(),
        "test_counts": {
            "authority": "docs/v4/RELEASE_METADATA.json (derived "
                         "from a real pytest run, never prose)",
            **meta,
        },
        "release": release,
        "eye": eye_state(),
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "machine_ram_gb": 31.6,
            "solver_backends": ["scipy shift-invert LU (default)",
                                "pyopencl (validated fp32/fp64)",
                                "CUDA (interface-only, no hardware)"],
        },
        "blockers": [
            {"id": "hardware", "affects": "all E-lane campaigns + "
             "all physical resonator fabrication/measurement"},
            {"id": "ethics", "affects": "E06/E07 human studies"},
            {"id": "compute", "affects": "Eye ladder below cl=1.5 "
             "(needs ~48+ GB or an iterative eigensolver)"},
            {"id": "xrd", "affects": "specimen orientation unknown"},
        ],
        "next_actions": [
            "B01: ingest the five 2026 papers with hashes + firewall",
            "Y01/Y02/Y03: ladder interpretation, calibrated resources, "
            "independent cluster census",
            "R01-R07: synthetic design-to-certificate campaign",
            "O01 orphan sweep, Q07 fresh-clone QA, R13+R12 release",
        ],
    }


def main() -> int:
    if "--check" in sys.argv:
        f = verify_frozen()
        print("frozen history:", "PASS" if f["passed"] else "FAIL")
        for p in f["problems"]:
            print("  -", p)
        return 0 if f["passed"] else 1
    snap = build()
    OUT.write_text(json.dumps(snap, indent=2) + "\n",
                   encoding="utf-8")
    ok = snap["frozen_history"]["passed"]
    print(f"baseline handoff written: {OUT.relative_to(ROOT)}")
    print(f"HEAD {snap['repository']['head'][:9]} on "
          f"{snap['repository']['branch']}; frozen history "
          f"{'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
