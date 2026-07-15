# RGCS v3 / RSCS 1.0 — Programme Progress Register

Authoritative execution ledger. One row per agent; updated at each agent
completion. Inherited failures = documented frozen-baseline Windows/numpy
discrepancies — NOT regressions, re-verified at every checkpoint.
† As of Agent 06 the inherited count dropped 4 → 2: two vertical-slice
failures were missing-`jsonschema` artifacts and pass once
`jsonschema`/`referencing` are installed (environment fix; Agent 08
declares them in pyproject). Remaining 2: V2-WIN-01 (zip arcname
backslashes) and NR3-001 (Linux-generated golden CSVs).
‡ Agent 08 fixed V2-WIN-01 (POSIX bundle arcnames) and declared the
schema deps, so the inherited count is now 1: only NR3-001 (byte-equality
of Linux-generated golden CSVs; deselected in Windows CI, passes on the
Linux reference platform).

| Agent | Scope | Status | Commits | Suite (passed/inherited-failed/new-regressions) | Handoff |
|---|---|---|---|---|---|
| 01 | v2.0.0 baseline freeze + migration map | COMPLETE | `f9fd2c2` (baseline), `715486b` | 223/4/0 (of 227 v2) | `V2_BASELINE_AUDIT.md`, `V2_TO_V3_MIGRATION_MAP.md` |
| 02 | Source ingestion, equation provenance, frozen notation | COMPLETE | `939e030`, `af0b22f` | 227+6 lint /4/0 | `RSCS_NOTATION_LEDGER.md` (GATE OPEN, D3-008) |
| 03 | RSCS mathematical core + Conservative Extension | COMPLETE | `5048687`, `c4cde1c`, `a1cdd80`, `b42f977` | 293/4/0 | `AGENT_03_HANDOFF.md` |
| 04 | NHT/HAL → Hydrogenuine memory bridge | COMPLETE | `7e00f19` | 307/4/0 | `NHT_HAL_RSCS_MAPPING.md`, `HG_RSCS_MEMORY_ARCHITECTURE.md` |
| 05 | Crystal application (anisotropic Christoffel) | COMPLETE | `4ccdd89` | 315/4/0 | `RGCS_CRYSTAL_APPLICATION.md` |
| 06 | Optical / photon–phonon / nonreciprocal coupling | COMPLETE | `1052c24` | 347/2/0 † | `AGENT_06_HANDOFF.md` |
| 07 | Coil / laser / timing / experiment design | COMPLETE | `8751b51` | 364/2/0 | `AGENT_07_HANDOFF.md` |
| 08 | Software / hardware / CAD / portability (T1) | COMPLETE | `75229cc` | 376/1/0 ‡ | `AGENT_08_HANDOFF.md` |
| 09 | Four manuscripts + public docs + Lessons Learned | COMPLETE | `7baad8c` | 376/1/0 | `AGENT_09_HANDOFF.md` |
| 10 | Independent adversarial QA | COMPLETE | (this commit) | 376/1/0; 3 new defects D-V3-01..03 documented | `QA_REPORT_V3.md` |
| 11 | Integration, repair, release, public package | pending | — | — | — |

## Registry / claims state

- RSCS registry ids: **40** (C.1–17 minus reserved; O.1–23) —
  `rscs_core/registry/rscs_registry.yaml`. Frozen RGCS-M registry: 61,
  schema 1, untouched.
- Claims: H-01..H-14 (v2, frozen), H-15..H-19 (Agent 04, ENG software),
  H-20..H-23 (Agent 06, optical; H-21/H-23 pre-registered nulls),
  H-24..H-30 (Agent 07: node-menu rows + timing gates).
- DECISION_LOG: D3-001..015, D4-001..003, D5-001..002, D6-001..003,
  D7-001..003.

## Standing verification (every checkpoint)

1. `.\.venv\Scripts\python -m pytest -q` → only the 4 inherited failures.
2. `git diff --stat 715486b HEAD -- archive/v2.0.0` → empty (freeze).
3. `python tools/generate_optical_comparison.py --check` → up to date.
4. `python experiments/schemas/validate.py` → all OK (needs jsonschema).
