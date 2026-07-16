"""Master coverage ledger generator (gate G42, release-blocking).

Parses the binding ledger from the prompt pack, asks every owner
module which IDs it disposes, and writes docs/v4/V4X_COVERAGE_LEDGER
.{json,md}. An ID with no owner is a P1 release blocker.

Owners declare coverage either through a `coverage_map()` function or
through the static OWNERS table below (for modules whose IDs are
structural rather than enumerated)."""

from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

LEDGER_MD = ROOT / "internal-docs" / "plans-v4" / \
    "RGCS_Master_Research_Expansion_Prompt_Pack" / \
    "03_MASTER_COVERAGE_LEDGER.md"

# The prompt pack lives under gitignored internal-docs/, so it is absent
# on CI and on any fresh clone. A binding coverage contract cannot depend
# on a file that is not in the repository, so the ID list is snapshotted
# here. When the pack IS present it is authoritative and any drift from
# the snapshot is an error rather than a silent divergence.
LEDGER_SNAPSHOT = ROOT / "docs" / "v4" / "V4X_LEDGER_IDS.json"

# Static dispositions: {id: (owner, artifact, status)}
OWNERS: dict = {}


def _add(ids, owner, artifact, status):
    for i in ids:
        OWNERS[i] = (owner, artifact, status)


# A-lane computational
_add(["A01", "A02", "A03"], "C01 polaritons",
     "rscs2_core/refmodels/polariton.py::hopfield_2x2,"
     "cavity_dispersion_ev,polariton_dispersion",
     "REDUCED_ORDER_VALIDATED")
_add(["A04", "A05"], "C01 polaritons",
     "rscs2_core/refmodels/polariton.py::hopfield_3x3,"
     "polarization_channel", "REDUCED_ORDER_VALIDATED")
_add(["A06"], "C01/C13", "rscs2_core/refmodels/polariton.py::"
     "transduction_interface", "INTERFACE_ONLY")
_add(["A07", "A08"], "C02 Eye refinement",
     "rscs2_core/eye_refinement.py::candidate_ladder,refined_verdict"
     " + docs/v4/proof/C02/refinement_ladder.json",
     "INSUFFICIENT_RESOLUTION")
_add(["A09"], "C02 Eye refinement",
     "rscs2_core/fem.py::harmonic_field + eye_refinement.py::"
     "driven_phase_diagnostics", "REDUCED_ORDER_VALIDATED")
_add(["A10"], "C02 Eye refinement",
     "rscs2_core/eye_refinement.py::frequency_sensitivity_map",
     "REDUCED_ORDER_VALIDATED")
_add(["A11", "A12"], "C03 harmonic family",
     "rscs2_core/harmonic_family.py::build_family_member,"
     "tolerance_sensitivity,specimen_registry", "CANDIDATE_NEW_"
     "COUPLING")
_add(["A13"], "C04 frequency keys",
     "rscs2_core/frequency_keys.py::build_registry,"
     "coincidence_significance", "REDUCED_ORDER_VALIDATED")
_add(["A14", "A15"], "C06 BVD",
     "rscs2_core/bvd.py::extract_bvd,derived_parameters",
     "REDUCED_ORDER_VALIDATED")
_add(["A16"], "C07 apparatus",
     "rscs2_core/apparatus.py::wheeler_inductance_h,"
     "crossed_coil_coupling,apparatus_registry,"
     "ordinary_artifact_model", "REDUCED_ORDER_VALIDATED")
_add(["A17"], "C08 calibration/inverse design",
     "rscs2_core/calibration.py (v4.1 module)",
     "REDUCED_ORDER_VALIDATED")
_add(["A18"], "C13 future interfaces",
     "rscs2_core/interfaces_future.py::request_computation",
     "INTERFACE_ONLY")


def _dynamic_maps() -> dict:
    """Ask owner modules for their coverage."""
    out = {}
    from rscs2_core import frequency_keys, harmonic_family
    from rscs2_core import interfaces_future, protocols_v4x
    from rscs2_core import spiral_cone, cymatic_disk
    from consciousness_lane import theory_registry

    for rid, rec in frequency_keys.build_registry().items():
        out[rid] = ("C04 frequency keys",
                    "rscs2_core/frequency_keys.py::build_registry",
                    rec["status"])
    for rid, rec in harmonic_family.specimen_registry().items():
        out[rid] = ("C03/C05 specimen registry",
                    "rscs2_core/harmonic_family.py::"
                    "specimen_registry", rec["status"])
    for rid in interfaces_future.INTERFACES:
        out[rid] = ("C13 future interfaces",
                    "rscs2_core/interfaces_future.py::"
                    "interface_record",
                    interfaces_future.interface_record(rid)
                    ["classification"])
    for rid, owners in protocols_v4x.coverage_map().items():
        rec = protocols_v4x.build_protocols()[owners[0]]
        out[rid] = (f"E-lane {'/'.join(owners)}",
                    "rscs2_core/protocols_v4x.py::build_protocols",
                    rec["status"])
    for mod, owner in ((spiral_cone, "G01 spiral cone"),
                       (cymatic_disk, "G02 cymatic disk")):
        for rid, rec in mod.motif_registry().items():
            out[rid] = (owner, f"rscs2_core/{mod.__name__.split('.')[-1]}.py",
                        rec["status"])
    for rid, rec in theory_registry.build_theory_registry().items():
        out[rid] = ("T-lane theory registry",
                    "consciousness_lane/theory_registry.py",
                    rec["status"])
    return out


def _parse_pack() -> dict:
    text = LEDGER_MD.read_text(encoding="utf-8")
    ids = {}
    for m in re.finditer(r"^\|\s*([ACEFGHISW]\d{2,3})\s*\|\s*"
                         r"([^|]+?)\s*\|", text, re.M):
        ids[m.group(1)] = m.group(2).strip()
    return ids


def parse_ledger() -> dict:
    """The committed snapshot is the portable contract; the pack is the
    authority when it is available."""
    snap = json.loads(LEDGER_SNAPSHOT.read_text(encoding="utf-8")) \
        if LEDGER_SNAPSHOT.exists() else None
    if not LEDGER_MD.exists():
        if snap is None:
            raise SystemExit(
                "no ledger source: neither the prompt pack nor "
                f"{LEDGER_SNAPSHOT.relative_to(ROOT)} is present")
        return snap["ids"]
    pack = _parse_pack()
    if snap is not None and snap["ids"] != pack:
        added = sorted(set(pack) - set(snap["ids"]))
        removed = sorted(set(snap["ids"]) - set(pack))
        raise SystemExit(
            "ledger snapshot has drifted from the prompt pack "
            f"(added {added}, removed {removed}); re-run with "
            "--refresh-snapshot after confirming the change is "
            "intended")
    return pack


def write_snapshot() -> int:
    ids = _parse_pack()
    LEDGER_SNAPSHOT.write_text(
        json.dumps({"source": "03_MASTER_COVERAGE_LEDGER.md "
                              "(RGCS Master Research Expansion Prompt "
                              "Pack)",
                    "note": "portable snapshot of the binding coverage "
                            "contract; the pack itself lives under "
                            "gitignored internal-docs/",
                    "total": len(ids), "ids": ids}, indent=1,
                   sort_keys=True) + "\n", encoding="utf-8")
    print(f"snapshot written: {len(ids)} ids")
    return 0


def build() -> dict:
    ledger = parse_ledger()
    disposition = dict(OWNERS)
    disposition.update(_dynamic_maps())
    rows, uncovered = [], []
    for rid, title in sorted(ledger.items()):
        d = disposition.get(rid)
        if d is None:
            uncovered.append(rid)
            rows.append({"id": rid, "title": title, "owner": None,
                         "artifact": None, "status": "UNCOVERED_P1"})
        else:
            rows.append({"id": rid, "title": title, "owner": d[0],
                         "artifact": d[1], "status": d[2]})
    return {"total_ids": len(ledger), "covered": len(ledger) -
            len(uncovered), "uncovered": uncovered, "rows": rows,
            "gate_G42_pass": not uncovered}


def main() -> int:
    if "--refresh-snapshot" in sys.argv:
        return write_snapshot()
    rep = build()
    out = ROOT / "docs" / "v4"
    out.mkdir(parents=True, exist_ok=True)
    (out / "V4X_COVERAGE_LEDGER.json").write_text(
        json.dumps(rep, indent=2), encoding="utf-8")
    lines = ["# RGCS V4X master coverage ledger", "",
             f"Total ledger IDs: **{rep['total_ids']}** — covered "
             f"**{rep['covered']}** — uncovered "
             f"**{len(rep['uncovered'])}**", "",
             f"Gate G42: {'PASS' if rep['gate_G42_pass'] else 'FAIL'}",
             "", "| ID | Item | Owner | Artifact | Status |",
             "|---|---|---|---|---|"]
    # INTERFACE_ONLY rows carry their disclaimer in the row itself:
    # the ledger is read row-by-row, so a header note far above does
    # not travel with the claim.
    gloss = {"INTERFACE_ONLY": "INTERFACE_ONLY — deferred by design, "
                               "no solver, not implemented",
             "ETHICS_APPROVAL_REQUIRED": "ETHICS_APPROVAL_REQUIRED — "
                                         "not performed",
             "PROTOCOL_READY_HARDWARE_REQUIRED":
                 "PROTOCOL_READY_HARDWARE_REQUIRED — protocol only, "
                 "not performed",
             "SOURCE_HYPOTHESIS": "SOURCE_HYPOTHESIS — retained "
                                  "without endorsement, not established"}
    for r in rep["rows"]:
        lines.append(f"| {r['id']} | {r['title']} | "
                     f"{r['owner'] or '**NONE (P1)**'} | "
                     f"`{r['artifact'] or '-'}` | "
                     f"{gloss.get(r['status'], r['status'])} |")
    (out / "V4X_COVERAGE_LEDGER.md").write_text("\n".join(lines) +
                                                "\n", encoding="utf-8")
    print(f"coverage {rep['covered']}/{rep['total_ids']} "
          f"G42={'PASS' if rep['gate_G42_pass'] else 'FAIL'}")
    if rep["uncovered"]:
        print("UNCOVERED:", ", ".join(rep["uncovered"]))
    return 0 if rep["gate_G42_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
