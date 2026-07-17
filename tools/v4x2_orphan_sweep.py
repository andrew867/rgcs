"""O01: post-pack orphan and fleeting-idea sweep.

Ideas introduced during THIS programme's execution (census
discoveries, addendum structures not yet implemented, queued
benchmarks) that the fixed 280-ID ledger has no row for. Every orphan
gets an owner, status, and disposition; none is deleted for sounding
minor. The count may exceed 280 — that is the rule, not a problem.

    python tools/v4x2_orphan_sweep.py
Writes docs/v4/V4X2_ORPHAN_REGISTER.md (+ .json)
"""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

ORPHANS = [
 ("ORPH2-001", "electrical trim primitives: narrow meanders and "
  "capacitive tuning fingers",
  "tuning addendum §2.1 lists ~10 sacrificial structures; "
  "design_trim implements the five mass-dominated ones. The two "
  "ELECTRICAL primitives change R/L/C rather than mass and need "
  "their own sensitivity model.",
  "R02", "ENGINEERING_PROTOTYPE",
  "deferred_with_owner: add electrical-zone primitives with "
  "impedance sensitivities (bvd.electrode_loading is the starting "
  "point)"),
 ("ORPH2-002", "removable balancing pixels",
  "addendum §2.1: fine-grained balance correction cells distinct "
  "from frequency trim cells (they target the first moment, not "
  "f01).",
  "R02", "ENGINEERING_PROTOTYPE",
  "deferred_with_owner: balance-pixel groups whose target metric is "
  "group_balance_moment, not removal_df01_hz"),
 ("ORPH2-003", "female-apex twin concentration (z ~ 4 mm)",
  "the unbiased census found a mirror strain-energy concentration "
  "near the female apex — never previously examined because every "
  "prior analysis selected nearest-to-candidate.",
  "Y03", "SOURCE_HYPOTHESIS",
  "investigate: is the twin's geometry-mirrored position exact "
  "under mesh refinement? symmetric twins would recast the apex "
  "feature as a tip-pair phenomenon"),
 ("ORPH2-004", "mid-shaft symmetric D2 pair (z ~ 58 mm)",
  "second census discovery: a large symmetric pair in the D2 "
  "diagnostic mid-shaft.",
  "Y03", "SOURCE_HYPOTHESIS",
  "investigate: diagnostic-specific (D2-only) or physical? check "
  "against D1/D8 at matching quantiles"),
 ("ORPH2-005", "LOBPCG/AMG solver benchmark",
  "named as the cheapest path below 1.5 mm spacing (Y012) but the "
  "actual two-solver benchmark on a controlled case has not run.",
  "Y02", "PROTOCOL_READY_HARDWARE_REQUIRED",
  "queued: job manifest exists; needs a quiet machine window "
  "(memory contention invalidates the benchmark)"),
 ("ORPH2-006", "filtration ordering on the coupled harmonic solve",
  "Q04's rgcs_application names the candidate; no RGCS solve has "
  "been restructured and no benefit measured.",
  "Q04", "ENGINEERING_PROTOTYPE",
  "deferred_with_owner: apply apply_filtration to the harmonic_field "
  "coupling matrix and MEASURE the density change"),
 ("ORPH2-007", "angular-Nyquist aliasing in partial arrays",
  "found while testing R11: with n partials, orders m and m+n are "
  "indistinguishable. Now reported in the API, but the design "
  "implication (choose n > 2*m_target) belongs in the composite-"
  "mode design rules.",
  "R11", "IMPLEMENTED_AND_TESTED",
  "resolved_in_code: alias_band + alias_note in "
  "partial_resonator_array; design rule documented here"),
 ("ORPH2-008", "claim-card versioning as a reusable mechanism",
  "the Eye claim card went v3->v4 during this programme when the "
  "census corrected the framing. The card mechanism (versioned "
  "claims + correction trail) should template any future public "
  "finding, not just the Eye.",
  "V02", "IMPLEMENTED_AND_TESTED",
  "resolved_in_docs: EYE_CLAIM_CARD.md is the template; rule 3 "
  "(corrections are news) generalizes"),
]


def sweep() -> dict:
    rows = [{"id": o[0], "title": o[1], "context": o[2],
             "owner": o[3], "status": o[4], "disposition": o[5]}
            for o in ORPHANS]
    return {"orphans_found": len(rows),
            "ledger_fixed": 280,
            "total_coverage": 280 + len(rows),
            "undisposed": [r["id"] for r in rows
                           if not r["disposition"]],
            "rows": rows}


def main() -> int:
    rep = sweep()
    (ROOT / "docs/v4/V4X2_ORPHAN_REGISTER.json").write_text(
        json.dumps(rep, indent=1) + "\n", encoding="utf-8")
    lines = ["# V4X2 orphan register (O01)", "",
             f"Fixed ledger: **280** · orphans: "
             f"**{rep['orphans_found']}** · total: "
             f"**{rep['total_coverage']}**", "",
             "Ideas that surfaced DURING this programme's execution "
             "— census discoveries, addendum structures not yet "
             "implemented, queued benchmarks. None deleted; each "
             "disposed.", "",
             "| ID | Idea | Owner | Status | Disposition |",
             "|---|---|---|---|---|"]
    for r in rep["rows"]:
        lines.append(f"| {r['id']} | {r['title']} | {r['owner']} | "
                     f"{r['status']} | {r['disposition'].split(':')[0]} |")
    lines += ["", "## Context and dispositions in full", ""]
    for r in rep["rows"]:
        lines += [f"### {r['id']} — {r['title']}", "",
                  r["context"], "",
                  f"**Disposition:** {r['disposition']}", ""]
    (ROOT / "docs/v4/V4X2_ORPHAN_REGISTER.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")
    print(f"orphans: {rep['orphans_found']}, total coverage "
          f"{rep['total_coverage']}, undisposed "
          f"{len(rep['undisposed'])}")
    return 0 if not rep["undisposed"] else 1


if __name__ == "__main__":
    sys.exit(main())
