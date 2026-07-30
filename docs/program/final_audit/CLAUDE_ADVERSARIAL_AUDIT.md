# Claude Post-Merge Adversarial Audit — program/integration (2026-07-26)

**Verdict: `PASS_WITH_YELLOW`**

Audited tree: `program/integration` at `b84e6eb` (audit fixes AA-01/02/04
committed on top; see "Fixes made during audit"). Every check below was
**executed**, not inspected-only. Companion machine-readable artifacts:
`CLAIM_LANGUAGE_AUDIT.json`, `RECEIPT_AUTHORITY_AUDIT.json`.

## Findings summary

| ID | Category | Severity | Status |
|---|---|---|---|
| AA-01 | Receipt bypass — `common/receipts.build_receipt` never called `validate_receipt` (Codex builder did; the adapter/hub builder didn't) | HIGH | **FIXED** — both builders now validate before returning; regenerated-fixture bytes unchanged (receipts were conformant; the gate was missing, not violated) |
| AA-02 | Authority-lock crash path — auditing a claim that quotes banned wording ("validated external transmission", "proven source technology", "confirmed anti-gravity") raised `SchemaError` instead of producing a RED/REJECT receipt; API would 500 | HIGH | **FIXED** — dual-pole adapter redacts banned wording in every echo (result, inputs, receipt) while the critic attacks the original text; API returns 422 refusal on residual `SchemaError`. All 7 planted claims now REJECT/RED with typed attacks |
| AA-03 | Self-asserted status — `static/hub/assets/hub.js` hard-codes the 9 badge entries instead of reading generated `fixtures/catalog.json`; verified **in sync today** by exact string match against `module_catalog()` | YELLOW | OPEN (recommendation: emit the JS catalog from `build_static_hub.py`; the per-module fixture statuses already come from receipts) |
| AA-04 | Documentation drift — QUICKSTART used pre-merge CLI forms (`frames earth-south-up`, `lattice run counterrotating-ring` whose positional is reserved/ignored); developer README named the mirror schema as if canonical | LOW | **FIXED** — commands corrected and verified by execution; schema wording now names the canonical packaged copy |
| AA-05 | Standing vs per-run badges — catalog badge for dual_pole is GREEN (infrastructure) while the shipped sample receipt is YELLOW (that sample audit's honest outcome); the hub shows both values in their own contexts | INFO | No action — recorded so the release audit doesn't misread it as a mismatch |

## Dimension-by-dimension results

- **Authority duplication** — one `ModuleStatus`, one `ClaimClass`, one
  `MODULES`/`STATUSES` (all in `common/status_schema.py`); `status.py`
  derives (`CLAIM_CLASSES = tuple(c.value for c in ClaimClass)`, enum
  mirror asserted, envelope validates through `ModuleStatus`). Grep of
  `rgcs_lab/` shows no second definition. PASS.
- **Receipt bypasses** — builders: `common/receipts.build_receipt`
  (AA-01, fixed), `rgcs_lab/receipts.receipt` (validates),
  `authority/dual_pole_machine.receipt` (Claude authority surface,
  consumed by authority tests). All shipped hub receipts re-validated
  against the canonical validator: 9/9 valid. PASS after fix.
- **Self-asserted status** — hub badges: index page uses the hub.js
  catalog (AA-03, in sync, YELLOW); module pages load per-run fixtures
  whose statuses come from executed adapters. PASS_WITH_YELLOW.
- **Fallback promotion** — forced `rgcs_lab.golay` ImportError at
  runtime: adapter fell back to reference, status capped YELLOW,
  `REFERENCE FALLBACK IN USE` warning attached, source attributed to
  the reference module; restored import returns `rgcs_lab.golay`
  backend. No shipped receipt carries the fallback marker; all
  core-backed receipts carry `backend=rgcs_lab.<core>`. PASS.
- **Claim wording** — zero banned-wording hits across static hub,
  release mirror, user/developer docs, examples, packaged corpus
  (CLAIM_LANGUAGE_AUDIT.json). Banned wording in *inputs* is redacted
  and rejected, never echoed (AA-02). PASS.
- **Coordinate regressions** — `git diff eb7d7d4..HEAD -- rgcs_coordinate/
  tests/rgcs_coordinate/` is empty; 30/30 codec tests pass; workbench
  decoder displays UNDERDETERMINED + training-equality badges. PASS.
- **Training leakage** — every "training equality" surface pairing
  verified qualified (UNDERDETERMINED/YELLOW adjacent); the packaged
  memory corpus contains only the four public docs (authority=public;
  no private/operator corpus); scanner-flagged workbench lines reviewed:
  qualified by the adjacent badge (line 51). PASS.
- **Physics conflation** — planted conflations ("gravity inferred from
  electromagnetic simulation", "packet proves location") REJECT with
  typed attack families; metasurface stays YELLOW UNDERDETERMINED and
  declares unmapped inputs; lattice claims bounded to synthetic model.
  PASS.
- **Energy ledgers** — lossless lattice: |initial + pump − stored −
  dissipated − drift| = 7.9e-15, drift −3.9e-15; damped lattice:
  dissipated > 0, stored < initial; metasurface power ledger residual
  0.0 W (all terms present, units declared). PASS.
- **Mutable predictions** — freeze→verify true; tampered hypothesis →
  verify match **False**; freeze after `measurement_started` → typed
  refusal; authority registry additionally requires sham+detuned
  controls and hashes freeze commit. PASS.
- **Private-data exposure** — no emails, local paths, OneDrive paths, or
  operator transcripts on any public surface; the only name hits are the
  public README's intentional GitHub links/author credit. Privacy
  defaults telemetry=False verified in doctor/serve/hub; hub JS performs
  same-origin fetches only. PASS.
- **Documentation drift** — QUICKSTART/developer README fixed (AA-04)
  and every QUICKSTART command re-executed successfully; RGCS_LAB_CLI.md
  matches the merged CLI; AUTHORITY_AND_SCHEMAS.md names the canonical
  schema. PASS after fix.
- **Planted false claims (integrated path)** — 7/7 REJECT + RED with
  typed attacks via the adapter (Codex state machine executing Claude's
  policy); waiver path yields ACCEPT_YELLOW with `waiver_recorded=true`,
  `critic_bypassed=false`, never GREEN; benign EXACT claim without
  exact-match evidence stays ACCEPT_YELLOW. CLI exits 2 on RED. PASS.
- **Hub badge vs receipt files** — 9/9 modules: fixture-embedded receipt
  byte-equals `receipts/<id>.json`, badge status equals receipt status,
  release mirror byte-identical, all receipts validate
  (RECEIPT_AUTHORITY_AUDIT.json). PASS.

## Fixes made during audit

Committed on `program/integration` after this audit (see git log):
AA-01 (validator in `build_receipt`), AA-02 (redact-and-reject +
API 422), AA-04 (docs). Post-fix verification: hub rebuild is
byte-identical (fixtures unchanged), and `tests/rgcs_lab +
tests/rgcs_coordinate + tests/cwatlas` = **1419 passed**.

## Verdict rationale

No unresolved defect in authority, receipts, fallback policy, claim
language, privacy, or the frozen codec. The remaining YELLOW is AA-03
(hand-maintained hub.js badge catalog — currently verified in sync,
with drift risk only if `module_catalog()` changes without a hub
rebuild), plus the standing physics YELLOWs that are policy, not
defects. **PASS_WITH_YELLOW.**
