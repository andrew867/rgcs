# Claim Register — RGCS v3 / RSCS 1.0

Machine-lintable register of claims. Classes: **EST** (established),
**DER** (derived), **HYP** (hypothesis), **SRC** (source claim, preserved
not endorsed), **ENG** (engineering heuristic — never evidence).
CSV columns follow `internal-docs/plans-v3/templates/CLAIM_REGISTER_TEMPLATE.csv`.

Seed state (Agent 01): the v2 claim base is inherited, not re-litigated —
61 registry equations (classification census in `V2_BASELINE_AUDIT.md`
§5) and 14 pre-registered hypotheses H-01…H-14 (+H-01a/H-06a/H-08b) in
`ROADMAP_TO_FALSIFICATION.md`. New v3 claims are appended below by
Agents 02–08 with full rows; no v2 claim may be upgraded in class without
experimental evidence logged in `NEGATIVE_RESULTS.md`/QA trail.

```csv
claim_id,class,statement,source_or_derivation,observable,controls,failure_condition,uncertainty,status
CLM-3-000,EST,"RGCS v2.0.0 baseline reproduces from frozen archives (232/232 files SHA256-identical; 10/10 release checksums)",docs/V2_BASELINE_AUDIT.md,repo diff vs archives,independent re-extraction,any hash mismatch,exact,verified
CLM-3-001,DER,"4 of 227 v2 tests fail on Windows/Py3.13 due to environment drift and v2 Windows portability defects (V2-WIN-01, V2-PKG-01), not baseline corruption",docs/V2_BASELINE_AUDIT.md §3,pytest results,same suite on Linux/Py3.11/numpy 2.4.4,failures persist in pinned Linux env,n/a,open-until-linux-rerun
```
