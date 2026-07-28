"""R10.13 Phases 01-05 — repository truth, supersession graph, and the
machine-readable documentation command status registry.

Gate Zero found the drafting baseline STALE; the typed mismatches are
recorded here as executable truth, and everything downstream runs
against actual authority.
"""

from __future__ import annotations

#: Phase 01 — typed mismatch receipt: drafting baseline vs repository.
GATE_ZERO_MISMATCHES = [
    {"id": "GZ-01", "field": "public release",
     "baseline": "v8.0.0", "actual": "v8.2.0 (tag) + unreleased "
     "R10.8.5A/R10.11x/R10.12 commits on program branches",
     "resolution": "target version 8.3.0 for the R10.13 private "
                   "candidate; public history preserved"},
    {"id": "GZ-02", "field": "console entry points",
     "baseline": "rgcs-v4, rgcs-workbook",
     "actual": "rgcs-v4, rgcs-workbook, rgcs-coordinate, rgcs-lab, "
               "rgcs (bound to the R10.12 codec CLI r1012.cli:main)",
     "resolution": "the unified normal-user CLI r1013.cli:main takes "
                   "the rgcs name and DELEGATES every R10.12 codec "
                   "subcommand to r1012.cli unchanged; nothing "
                   "breaks"},
    {"id": "GZ-03", "field": "python",
     "baseline": ">=3.11", "actual": ">=3.11 (pyproject), 3.13.2 in "
     "the working venv", "resolution": "no change"},
    {"id": "GZ-04", "field": "canonical variants",
     "baseline": "ideal_n7, nominal", "actual": "confirmed",
     "resolution": "custom specimens construct CanonicalCrystal "
                   "records directly; the two canonical variants are "
                   "unchanged"},
    {"id": "GZ-05", "field": "19-wire dataset shape",
     "baseline": "eight compact/refined pairs and one three-depth "
                 "chain (source-stated)",
     "actual": "the corrected 19 wires parse as 15 compact + 4 "
               "refined records; 8 pairs each requiring a refined "
               "member cannot exist under the executable link tests",
     "resolution": "the exact-cover solver exhausts the bounded "
                   "partition space and reports the typed negative "
                   "with the next source request; the source "
                   "statement is preserved as provenance, not "
                   "promoted to fact"},
]

#: Phase 03 — R10.13 corrections, extending the R10.12 ledger
#: (COR-01..08 live in r1012.ledger and remain in force).
CORRECTIONS_R1013 = [
    {"id": "COR-09", "supersedes": "one-bit extension field",
     "current": "NO extension bit; variable refinement exists on the "
                "left and right of the fixed core "
                "(C_L^dL|E3|S|S|S|C_R^dR, W = 21+3(dL+dR))",
     "status": "ACTIVE"},
    {"id": "COR-10", "supersedes": "unlabelled S6 state triple",
     "current": "toroidal/poloidal/radial phase semantics are "
                "SOURCE-REPORTED labels carried as provenance; the "
                "state-to-geometry mapping remains UNDERDETERMINED",
     "status": "ACTIVE"},
    {"id": "COR-11", "supersedes": "global 10/9 edge law",
     "current": "global law REJECTED (R10.11F-A); the state-dependent "
                "10/9 BASE ratio family remains an active bounded "
                "hypothesis with no selected modifier",
     "status": "ACTIVE"},
    {"id": "COR-12", "supersedes": "627-step fitted warp",
     "current": "REVOKED (unchanged); no fitted or precomputed warp "
                "may substitute", "status": "ACTIVE"},
    {"id": "COR-13", "supersedes": "E2 frame",
     "current": "E3 octal-aligned frame (unchanged from R10.11D)",
     "status": "ACTIVE"},
    {"id": "COR-14", "supersedes": None,
     "current": "publication remains on HOLD; no tag, push, public "
                "release, or manuscript submission",
     "status": "ACTIVE"},
]

#: Phases 02/05/19 — machine-readable status for every command family
#: in the imported CLI reference. Statuses: CURRENT (executes in this
#: release), IMPLEMENTED (new in R10.13, executes), TARGET (documented
#: for a future release; must NOT appear in release-facing docs),
#: REFUSED (deliberately not shipped, with reason), HISTORICAL.
#: The doc-execution test suite executes every CURRENT/IMPLEMENTED row.
COMMAND_STATUS = {
    "rgcs-v4 *": {"status": "CURRENT", "provider": "rscs2_core.cli"},
    "rgcs-workbook": {"status": "CURRENT",
                      "provider": "rgcs_workbench.workbook"},
    "rgcs-workbench": {"status": "CURRENT",
                       "provider": "rgcs_desktop.app.main",
                       "note": "GUI; presence-tested, not driven in CI"},
    "rgcs --version": {"status": "IMPLEMENTED", "provider": "r1013.cli"},
    "rgcs doctor": {"status": "IMPLEMENTED", "provider": "r1013.cli"},
    "rgcs self-test": {"status": "CURRENT",
                       "provider": "r1012.cli (codec workflows), "
                                   "extended by r1013 doctor"},
    "rgcs schema verify": {"status": "IMPLEMENTED",
                           "provider": "r1013.cli"},
    "rgcs examples verify": {"status": "IMPLEMENTED",
                             "provider": "r1013.cli"},
    "rgcs crystal new|validate|inspect|migrate|hash":
        {"status": "IMPLEMENTED", "provider": "r1013.cli"},
    "rgcs crystal geometry|density-check|estimate|christoffel":
        {"status": "IMPLEMENTED", "provider": "r1013.cli"},
    "rgcs crystal mesh|modes|converge|piezo":
        {"status": "IMPLEMENTED", "provider": "r1013.cli",
         "note": "mesh/modes/converge need gmsh on PATH"},
    "rgcs crystal report|bundle": {"status": "IMPLEMENTED",
                                   "provider": "r1013.cli"},
    "rgcs bundle verify": {"status": "IMPLEMENTED",
                           "provider": "r1013.cli"},
    "rgcs frequency list|compare": {"status": "IMPLEMENTED",
                                    "provider": "r1013.cli over "
                                    "rscs2_core.frequency_keys"},
    "rgcs frequency coordinate": {
        "status": "REFUSED",
        "reason": "a frequency-to-coordinate mapping would assert the "
                  "S6-state-to-geometry bridge, which is "
                  "UNDERDETERMINED; shipping it would fabricate "
                  "geography. The command is removed from release "
                  "docs."},
    "rgcs wire parse|explain|roundtrip": {"status": "CURRENT",
                                          "provider": "r1012.cli"},
    "rgcs transition candidates": {"status": "CURRENT",
                                   "provider": "r1012.cli"},
    "rgcs mesh trace": {"status": "CURRENT", "provider": "r1012.cli"},
    "rgcs help error": {"status": "IMPLEMENTED",
                        "provider": "r1013.cli"},
    "desktop New Specimen wizard": {
        "status": "REFUSED",
        "reason": "deferred from the R10.13 release: the seven-page "
                  "wizard is not implemented; current-release wording "
                  "is removed from the desktop guide and the CLI "
                  "workflow is the supported path. The desktop app "
                  "itself (rgcs-workbench) is unchanged."},
}


def gate_zero_receipt(head: str, branch: str, test_count: int) -> dict:
    return {"schema": "rgcs.r1013.gate-zero.v1",
            "branch": branch, "head": head,
            "full_suite_at_gate": test_count,
            "mismatches": GATE_ZERO_MISMATCHES,
            "corrections": CORRECTIONS_R1013,
            "command_status_entries": len(COMMAND_STATUS)}


def command_status_table() -> dict:
    return {"schema": "rgcs.r1013.command-status.v1",
            "statuses": COMMAND_STATUS,
            "rule": "no TARGET-marked command may appear in "
                    "release-facing docs; every CURRENT/IMPLEMENTED "
                    "row is executed by tests/r1013/test_doc_execution"}
