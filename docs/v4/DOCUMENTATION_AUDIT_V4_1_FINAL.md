# Final Documentation Audit — RGCS v4.1 Closeout

Scope: every public/release-facing documentation surface, audited
against the v4.1.0 release reality (commit `4c2a1cc`, tag `v4.1.0`,
605 tests, CI 10/10, audit 19/19, bundle 115/115, corrected Eye
verdict UNCERTAINTY_OVERLAPS_CONVENTIONAL_NODE, separation 3.906 mm).
Machine-readable companion: `DOCUMENTATION_AUDIT_V4_1_FINAL.json`.
Repository state at audit start: HEAD = `4c2a1cc` (= v4.1.0), local ==
remote for `v4-dev`; `main` 31 commits behind with zero unrelated
commits; dirty files only the scanner-regenerated baseline JSONs.

## Searches performed

Repo-wide (current docs; frozen archives and labelled history
excluded) for: retired verdict strings (CONVENTIONAL_NODE_FOUND,
CONVENTIONAL_NODE_EXPLAINS_RESULT), threshold language (4 mm, 3.94 mm,
node_tol), canonical numbers (3.906 / 102.240 / 106.018 / 3.08 /
0.353 / 0.032), version strings (v4.0.0/v4.1.0), test/asset counts
(471/605, 110/111/115 files), reason-code vocabulary (NOT_APPLICABLE
vs MECHANISM_NOT_IMPLEMENTED_FOR_MATERIAL), nonexistence claims,
reference-system-as-quartz claims, FDT/lore promotion, machine paths.

## Findings and dispositions

### FIXED (current-facing, stale verdict asserted as current)

| file | defect | fix |
|---|---|---|
| README.md | entire header still v3.0.0-era; wrong quick start (377 tests), no v4 content | rewritten: v4.1 release/link, verified install + CLI quick start, corrected Eye record with uncertainty interpretation, capability firewall, reference-system separation, unimplemented-physics list, updated limitations, Zenodo status |
| docs/CANONICAL_110MM_CASE_STUDY.md | body asserted retired verdict + "within 4 mm" (banner only) | body replaced by the corrected uncertainty-aware record |
| docs/EYE_METHODOLOGY.md | old null-comparison gate + old verdict as current | corrected gate description + corrected canonical result |
| docs/USER_GUIDE_V4.md | CONVENTIONAL_NODE_FOUND as current; 110/110 count | corrected verdict + interpretation; 115/115 |
| docs/ZENODO_METADATA_V4.md | v4.0.0 metadata with old verdict as the record to publish | rewritten: v4.1.0 block current, v4.0.0 block explicitly historical |
| docs/PROGRAMME_PROGRESS.md | ended at v4.0.0 | v4.1 completion row appended (old rows preserved as history) |
| pyproject/CITATION/builder | 4.1.0 | bumped to 4.1.1 (patch release, below) |

### HISTORICAL — intentionally preserved, labelled

docs/RELEASE_NOTES_V4.md (banner added), docs/plans-v4/
EYE_DIAGNOSTIC_REPORT_110MM.md (corrective addendum already present),
docs/plans-v4 agent handoffs/audits/defect register/lessons (execution
records), docs/v4/baseline/* (v4.0.0-era authority map), docs/v4/
proof/M9-precorrection/ (preserved pre-correction run),
docs/v4/runlogs/* (execution history), archive/v2.0.0 and all frozen
release assets. WHAT_THIS_QUARTZ_MODEL_DOES_NOT_INCLUDE.md quotes
"3.94 mm" only as the binding didactic rule (correct as-is).

### VERIFIED CURRENT (no change needed)

docs/RGCS_V4_TECHNICAL_MANUSCRIPT.md and docs/v4/
RGCS_V4_1_COMPLETION_MANUSCRIPT.md (corrected at 97936cc),
docs/v4/EYE_NODE_COINCIDENCE_CORRECTION.md, capability matrix,
V4_WHAT_IS_NOT_MODELLED.md, provenance registries, examples.

### Commands executed during this audit (all passed)

`pip install -e .` metadata → rgcs 4.1.1 (dev venv re-registered from
the stale rgcs-v3 dist name); `rgcs-v4 --help`; `rgcs-v4 capabilities
material.alpha_quartz --check magnon_modes` →
MECHANISM_NOT_IMPLEMENTED_FOR_MATERIAL; `rgcs-v4 verify-checksums` →
115/115; clean-venv install from the downloaded v4.1.0 source asset
(verified during the release, unchanged). README quick-start commands
match these verified invocations; the full-suite command was executed
at the release commit (605 passed).

### Release-asset audit → v4.1.1 REQUIRED

The v4.1.0 manuscripts asset ships four documents asserting the
retired verdict as current with NO correction marker (USER_GUIDE_V4,
RELEASE_NOTES_V4, ZENODO_METADATA_V4, EYE_METHODOLOGY at 4c2a1cc) —
a material scientific contradiction inside the release that headlines
the correction. Step-13 criteria met → documentation-only patch
release v4.1.1 with rebuilt assets; v4.1.0 remains tagged, frozen,
untouched. No restricted PDFs, build caches, or machine-specific paths
ship in any asset (V4_REPO_INVENTORY.json contains a local path but is
NOT included in the manuscripts asset, which packages only .md/.yaml).

### Guard tests added

`tests/v4/test_v4c_docs_closeout.py` (7 tests): retired wording only
with history markers; canonical numbers + corrected verdict in
flagship docs; no proximity phrasing; no affirmative nonexistence
claims; version consistency; relative links resolve; reference systems
never described as quartz physics; bundle machine verdict matches the
docs (3.906/102.240/106.018 checked against eye/node_coincidence.json).

## Pending human action

1. Verify/publish the auto-created Zenodo record for the final v4.1.x
   release; 2. add the minted version DOI to CITATION.cff (follow-up
   commit). The DOI is NOT invented anywhere; current docs label
   10.5281/zenodo.21387947 as the latest minted (v3.0.1) DOI.

## Verdict

Documentation state: CONSISTENT with the corrected v4.1 interpretation
after the fixes in this commit; enforcement is mechanical (guard
tests). Release-asset correctness restored via v4.1.1.
