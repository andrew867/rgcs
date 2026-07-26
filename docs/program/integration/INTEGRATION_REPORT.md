# Integration Report — RGCS Recursive Infrastructure Lab (2026-07-26)

**Verdict: RGCS_INTEGRATION_GREEN_READY_FOR_FINAL_AUDIT**
(see Verdict rationale at the end; physics lanes remain YELLOW by design
and are documented, not hidden — this is the bounded-capability GREEN
defined by the receipt promotion rules.)

## What was merged

| Step | Commit | Content |
|---|---|---|
| base | `eb7d7d4` | shared Coordinate Workbench base (`rcw-public-workbench` tip) |
| 1 | `15afa9e` | Claude lane `188caab` — authority, schemas, truth gate, receipts, docs (merged clean) |
| 2 | `f06a4a8` | Codex lane `71e7342` — six domain cores, CLI, numerical/property tests (1 add/add conflict resolved) |
| 3 | `4b9ec05` | Cursor lane `d4baf0d` — adapters, FastAPI, static hub, packaging, CI (3 conflicts + policy reconciliation) |
| 4 | `f4635cc`+ | integration: fixtures regenerated from executed Codex cores, release mirror synced, docs and receipts |

Branch: `program/integration` in worktree `../rgcs-integration`.
Pre-merge inventory: `PREMERGE_INVENTORY.md`; file-level decisions:
`CONFLICT_RESOLUTION.md` (IR-01 … IR-09).

## Objective compliance

- **One coherent implementation** — single package `rgcs_lab` with
  Claude's contracts (`common/status_schema.py`, packaged receipt
  schema, physics truth gate, prediction authority, dual-pole policy),
  Codex's pure cores + tests, Cursor's adapters/API/hub/packaging/CI.
- **No duplicate public APIs** — one `ModuleStatus` (Claude), the
  `ModuleResult` envelope validates through it; one receipt schema
  (packaged canonical + byte-identical distribution mirror); one
  `rgcs-lab` console entry point; one CLI module; one claim vocabulary
  (Codex core literals rewritten to it, IR-04).
- **No reference fallback promoted to GREEN** — adapters execute the
  bundled Codex cores; `guard_fallback` caps any fallback at YELLOW with
  an explicit warning; every shipped receipt records
  `backend=rgcs_lab.<core>` (IR-03).
- **No hidden test failure** — full gate matrix below ran to completion
  with normal exit; the Codex teardown-hang report was investigated and
  classified (environment, not repository —
  `CODEX_PYTEST_HANG_INVESTIGATION.md`); no plugin silenced, no timeout
  masking.
- **No unsupported physics claim** — physics lanes stay YELLOW
  (`physical_status`) in catalog, fixtures, hub pages; banned wording is
  enforced at object-construction time (Project Authority Lock scan in
  `ModuleStatus`); the planted anti-gravity example is REJECTED by the
  executed Codex state machine with typed attack findings, CLI exit 2.

## Gate results

| Gate | Result |
|---|---|
| `pytest tests/rgcs_lab -k "authority or receipt or claim …"` (post-Claude) | 25 passed |
| `pytest tests/rgcs_lab` (post-Codex) | 36 passed, normal exit (hang not reproduced; see investigation) |
| `pytest tests/rgcs_lab` (post-Cursor reconciliation) | 55 passed (25 Claude + 11 Codex + 19 Cursor) |
| `pytest tests/rgcs_coordinate -q` | 30 passed (frozen codec untouched) |
| `pytest tests -q` (full repository, CI-mirroring NR3-001 deselect) | **7931 passed, 15 skipped, 1 deselected, exit 0** (TEST_RECEIPT.json) |
| `python -m build` | wheel + sdist built (PACKAGE_RECEIPT.json) |
| installed wheel outside repo | every CLI module + `rgcs-lab serve` executed (PACKAGE_RECEIPT.json) |
| static hub from disk + static server | verified, no telemetry, YELLOW physics visible (STATIC_HUB_RECEIPT.json) |

## Mandatory-rule attestation

1. Frozen coordinate packet parser: untouched (no diff under
   `rgcs_coordinate/`; 30/30 tests pass).
2. Golden vectors: unchanged; Codex golden/property tests pass unmodified.
3. Claude earned-status logic: preserved (only the IR-01 slug spelling
   changed; all 25 authority tests pass).
4. Reference fallbacks cannot report GREEN when a Codex core is
   available: enforced in code (`guard_fallback`), not just documented.
5. One `ModuleStatus`, one receipt schema, one `rgcs-lab` entry point:
   yes (IR-02/04/05).
6. "Bodies reached 100%" was not treated as passing: every gate above is
   a completed pytest run with a normal exit code.
7. No pytest plugin silenced; the one environment knob used during
   diagnosis (`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`) was diagnostic only and
   is not baked into any config.

## Known limitations (documented, deliberate)

- Physics lanes YELLOW: coordinate physical projection, golay signal
  origin, frames field effect, lattice interpretation, metasurface
  physics, predictions mechanism — all UNDERDETERMINED, surfaced in the
  hub and receipts.
- Metasurface UI inputs `groove_depth_m` / `loss_tan` are not
  representable in the Codex reduced-order RLCG core; they are declared
  in `unmapped_inputs` + a warning instead of being silently ignored
  (previously the reference model consumed them; the honest reduced-order
  answer supersedes the prettier one).
- `source_commit` is `unknown` for receipts generated from an installed
  wheel outside a git tree unless `RGCS_SOURCE_COMMIT` is set (documented
  gitmeta behavior); all shipped fixtures were generated in-tree with the
  real commit.
- Predictions hub demo (reference, YELLOW) is intentionally distinct
  from the stricter authority registry contract (IR-08).

## Verdict rationale

All integration gates passed with executed code and normal exits; the
only YELLOW items are physics lanes that are YELLOW **by policy** (they
can never be upgraded by software results) and are fully surfaced in
receipts, catalog, and UI. Software integration itself carries no
unresolved defect, so the verdict is
`RGCS_INTEGRATION_GREEN_READY_FOR_FINAL_AUDIT`. The three post-merge
audit prompts in `02_POST_MERGE/` should now run against
`program/integration`.
