# Pre-consolidation Repository Truth (2026-07-26)

## Canonical base

- Branch `program/integration`, worktree `../rgcs-integration`
- START_COMMIT: `991446e` (adversarial audit PASS_WITH_YELLOW), clean tree
- Remote: `origin = https://github.com/andrew867/rgcs.git` — integration
  branch NOT pushed; nothing tagged beyond `v8.2.0` (pre-program)
- Tags: latest `v8.2.0`; no program/lab tag exists (correct: do-not-tag)

## Branch / worktree inventory

| Branch | Tip | Worktree | State | Disposition |
|---|---|---|---|---|
| `program/integration` | `991446e` | `../rgcs-integration` | clean | canonical base |
| `program/claude-authority-docs` | `188caab` | `../rgcs-claude` | clean | fully merged (15afa9e) — no newer commits |
| `program/codex-core-algorithms` | `71e7342` | `RGCS/codex-worktree` | clean | fully merged (f06a4a8) — no newer commits |
| `program/cursor-app-integration` | `d4baf0d` | `../rgcs-cursor` | clean | fully merged (4b9ec05) — no newer commits |
| `program/codex-numerical-audit` | `42fc284` | `RGCS/audit-worktree` | clean | **NEW** — post-merge Codex numerical audit, based on `b84e6eb`; docs-only (+3 files, 405 lines); merged in Phase 1 (`a8c09c6`) |
| `rcw-public-workbench` | `eb7d7d4` | main checkout | clean | shared base (unchanged) |

**Cursor release-build lane: no branch, worktree, or commit exists.**
Recorded as fact; no work invented for it. The release-build evidence in
this consolidation therefore comes from the integration lane's own
executed gates (wheel/sdist build, clean-venv install, serve smoke) plus
the Phase 4/5 re-runs at the final commit.

## Commits newer than 991446e

Only `program/codex-numerical-audit @ 42fc284` (docs-only). Reviewed
before merging: adds `docs/program/final_audit/CODEX_NUMERICAL_AUDIT.md`
(verdict PASS, 178/178 independent assertions over golay/frames/memory/
dual-pole/lattice/metasurface/CLI/installed wheel),
`NUMERICAL_TEST_RECEIPT.json`, `PYTEST_HANG_FINAL_STATUS.md` (hang
closed: not reproduced; documents a machine-local pytest temp-root ACL
caveat with `--basetemp` workaround). No code changes; no conflicts.

## Handoffs / audits / receipts read

- `docs/program/integration/*` — PREMERGE_INVENTORY, TREE_DIFFS,
  INTEGRATION_REPORT, CONFLICT_RESOLUTION (IR-01..IR-09),
  CODEX_PYTEST_HANG_INVESTIGATION, RECEIPT_PROMOTION_REPORT,
  TEST/PACKAGE/STATIC_HUB receipts, FINAL_MERGE_HANDOFF
- `docs/program/final_audit/*` — CLAUDE_ADVERSARIAL_AUDIT
  (PASS_WITH_YELLOW; AA-01/02/04 fixed, AA-03 open, AA-05 info),
  CLAIM_LANGUAGE_AUDIT, RECEIPT_AUTHORITY_AUDIT, and the newly imported
  Codex trio
- `docs/program/receipts/HANDOFF_claude_WS01..WS09.json`,
  `docs/program/coordination/HANDOFF_{codex,cursor}.json` + claimed-file
  manifests

## Known-YELLOW register entering consolidation

1. AA-03 — hand-maintained hub.js badge catalog (in sync; to be closed
   in Phase 2)
2. Physics lanes (policy YELLOW, not defects): unique physical Terra
   projection; transport-header grammar / federation-group value;
   variable-length packet transcoding; physical spoof-SPP validation;
   residual-force experiment; gravity/torsion interpretation;
   prospective solar-flare prediction (pending deadline/data)
3. Codex-audit environment caveat: machine-local pytest temp-root ACL
   (workaround documented; not a repository defect)
