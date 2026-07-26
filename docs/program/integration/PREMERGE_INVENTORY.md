# Pre-merge Inventory — RGCS Integration (2026-07-26)

Integration worktree: `../rgcs-integration`, branch `program/integration`,
created from the shared Coordinate Workbench base.

## Branch tips and dirty state (verified before merging)

| Lane | Branch | Tip | Worktree | Dirty state |
|---|---|---|---|---|
| Base | `rcw-public-workbench` | `eb7d7d4a3c9c9d900eeb508a7a9684a0784e099e` | main checkout | clean (one untracked helper dir `codex-worktree/`) |
| Claude | `program/claude-authority-docs` | `188caab` (parent `a66ee05`) | `../rgcs-claude` | clean |
| Codex | `program/codex-core-algorithms` | `71e73423031f911c3145ad4fd17ec7dec9c79eca` | `RGCS/codex-worktree` | clean |
| Cursor | `program/cursor-app-integration` | `d4baf0d` (parents `6aabd7c`, `b3a6720`) | `../rgcs-cursor` | clean |

`git merge-base` of every pair of lane branches is `eb7d7d4` — all three
lanes branched from the same Coordinate Workbench base; that commit was
used as the integration starting point.

## Claimed-file manifests and handoff JSONs

- `docs/program/coordination/CLAIMED_FILES_claude.txt` (Claude lane)
- `docs/program/coordination/CLAIMED_FILES_codex.txt` + `HANDOFF_codex.json` (Codex lane)
- `docs/program/coordination/CLAIMED_FILES_cursor.txt` + `HANDOFF_cursor.json`,
  `MERGE_NOTES_cursor.md`, `REPO_TRUTH_CURSOR.md` (Cursor lane)
- `docs/program/receipts/HANDOFF_claude_WS01..WS09.json` (Claude workstreams)

All are merged verbatim into the integration branch.

## Tree diffs vs the shared base

Full per-branch `git diff --name-status eb7d7d4 <tip>` output:
`docs/program/integration/PREMERGE_TREE_DIFFS.txt`.

## `rgcs_lab` overlaps (files added by more than one lane)

| Path | Claude | Codex | Cursor | Resolution owner |
|---|---|---|---|---|
| `rgcs_lab/__init__.py` | ✔ | ✔ | ✔ | merged (Claude docstring + Cursor product constants; MODULES imported from canonical schema) |
| `rgcs_lab/common/__init__.py` | ✔ | — | ✔ | merged re-export of the canonical contract |
| `rgcs_lab/cli.py` | — | ✔ | ✔ | merged; Codex core subcommands + Cursor hub subcommands |
| `pyproject.toml` | ✔ (package-data) | ✔ (entry point) | ✔ (extras, testpaths) | auto-merged; verified by hand |

Non-conflicting but policy-relevant duplication resolved during merge:

- Claude `rgcs_lab/common/status_schema.py` vs Cursor `rgcs_lab/common/status.py`
  (two status/claim vocabularies) → one canonical vocabulary (Claude), Cursor
  file rewritten to derive from it.
- Claude `rgcs_lab/common/receipt_schema.json` vs Cursor
  `schemas/lab/receipt.schema.json` → **byte-identical files**; the packaged
  Claude copy is canonical, `schemas/lab/` copy retained as the distribution
  mirror for external tooling.
- Codex cores (`rgcs_lab/golay.py`, `frames.py`, `memory.py`, `dual_pole.py`,
  `lattice.py`, `metasurface.py`) vs Cursor `rgcs_lab/reference/*` demos →
  adapters execute Codex cores; reference demoted to labelled fallback.

## Receipt schemas

- Claude: `rgcs_lab/common/receipt_schema.json` + stdlib validator
  `rgcs_lab.common.status_schema.validate_receipt` (required keys: module,
  version, source_commit, status, claim_class, inputs, models, result, tests).
- Cursor: `schemas/lab/receipt.schema.json` — byte-identical to Claude's;
  builder `rgcs_lab.common.receipts.build_receipt` already emitted every
  required key.
- Codex: no schema file; builder `rgcs_lab.receipts.receipt` emitted every
  required key but used non-canonical `claim_class` strings (see
  CONFLICT_RESOLUTION.md, IR-04).

## CLI entry points

- Codex `pyproject`: `rgcs-lab = "rgcs_lab.cli:main"`
- Cursor `pyproject`: `rgcs-lab = "rgcs_lab.cli:main"` (+ `rgcs_lab/__main__.py`)
- Identical target string → single entry point survives the merge; the two
  different `cli.py` bodies were merged by hand (see CONFLICT_RESOLUTION.md).

## Test directories

- Claude: `tests/rgcs_lab/test_rlab_{schema_gate,dual_pole,hub_coordinate,memory_predictions}.py` (25 tests)
- Codex: `tests/rgcs_lab/test_{golay,frames,memory_dual,lattice,metasurface}.py` (11 tests)
- Cursor: `tests/rgcs_lab/test_lab_{core,api}.py`, `tests/rgcs_lab/browser/test_hub_a11y_static.py` (+ edit to `tests/v51/test_r8_source_coverage.py`)
- No test file collides between lanes except the repo-wide basename collision
  `tests/rgcs_lab/test_frames.py` vs pre-existing `tests/cwatlas/test_frames.py`
  (rootdir has no per-directory `__init__.py`); the new Codex file was renamed
  to `tests/rgcs_lab/test_rlab_frames_core.py` with contents unchanged.

## `pyproject.toml` differences

- Claude added: `rgcs_lab*` to packages.find, `"rgcs_lab.common" = ["*.json"]`
  package-data.
- Codex added: `rgcs-lab` console script.
- Cursor added: `workbench` extra (fastapi/uvicorn/httpx), same deps appended
  to `dev`, `tests/rgcs_coordinate` + `tests/rgcs_lab` to testpaths.
- Integration added: `"rgcs_lab.data" = ["memory_corpus/*.json"]` package-data
  for the packaged memory corpus (wheel runs need a corpus without the repo).
