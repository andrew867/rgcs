# Consolidation Decisions (2026-07-26)

Every decision made after START_COMMIT `991446e`, in order.

## CD-01 — Import Codex numerical audit (merge, not cherry-pick)

`program/codex-numerical-audit @ 42fc284` (based on `b84e6eb`, clean,
docs-only: +3 files under `docs/program/final_audit/`) reviewed by full
diff before merging; verdict PASS with 178/178 independent assertions
and the pytest hang closed as not reproduced. Merged `--no-ff` as
`a8c09c6`. No conflicts; no code touched. Canonical ownership
unaffected.

## CD-02 — Cursor release-build lane: nothing to import

No branch, worktree, or commit exists for a Cursor release build.
Recorded as fact (PRECONSOLIDATION_STATE.md); release-build evidence is
supplied by this consolidation's own executed Phase 4/5 gates instead.
No work was invented under Cursor's name.

## CD-03 — AA-03 closure design (Phase 2)

Chosen: `build_static_hub.py` GENERATES `assets/catalog.data.js`
(`window.RGCS_CATALOG = <module_catalog() JSON>` + generated-at-commit
header); `index.html` loads it before `hub.js`; `hub.js` consumes
`window.RGCS_CATALOG` and contains no module literals. Rejected
alternative: fetching `fixtures/catalog.json` in static mode — fails
under `file://` (fetch/CORS), and losing static mode was not
acceptable. Badge semantics unchanged (same fields, same values, same
render path). Six tests in `tests/rgcs_lab/test_rlab_hub_catalog.py`
pin derivation, ordering, per-entry page/fixture/receipt existence, and
mirror equality.

## CD-04 — Typed CLI refusal for out-of-family vectors

Surfaced during Phase 3 checks: `rgcs-lab coordinate decode 1643789253`
(31-bit) crashed with a raw `PacketError` traceback. The frozen parser
is CORRECT (refuses, never truncates) and was not touched; only the
Cursor-owned CLI wrapper now converts `PacketError`/`ValueError` into a
typed RED refusal JSON with exit code 4. The API decode route already
returned 400.

## CD-05 — New provenance goes to the private operator area only

`internal-docs/` is gitignored (`.gitignore:1`); the federation-group /
node-23 / Erie-Montreal-Toronto record was written to
`internal-docs/provenance/PROVENANCE_2026-07-26_federation-group_node23.md`
in the operator's working area — NOT committed, NOT in the public tree.
All items recorded as user-reported provenance (SOURCE_REPORTED /
UNDERDETERMINED); no transport-header width or group ID invented; the
Stonehenge training equality unchanged; 31-bit vectors verified to be
refused (typed), not forced through the 30-bit parser. Public tree
carries only the generic refusal-surfacing fix (CD-04), which encodes
no provenance data.

## CD-06 — Receipt/artifact commit convention

Receipts and generated artifacts record the FINAL IMPLEMENTATION commit
(`69f2174`) via `RGCS_SOURCE_COMMIT` at generation time. The last
consolidation commit adds only generated artifacts and final documents
(no behavior change), so no receipt references an earlier
implementation state. Earlier receipts under `docs/program/integration/`
and `docs/program/final_audit/` are explicitly historical records of
their own phases and keep their original commits.

## CD-07 — SBOM method

CycloneDX 1.5 JSON generated from the CLEAN wheel venv's installed
distribution metadata (`importlib.metadata`), anchored to the wheel
SHA-256 and the final source commit. Chosen over adding a new build
dependency; the venv contains exactly the wheel + `[workbench]` extra
closure.
