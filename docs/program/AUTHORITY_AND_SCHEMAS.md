# Program authority and shared schemas (Claude lane)

How Codex and Cursor consume the shared contracts. Everything here is
implemented and tested (`tests/rgcs_lab/`, 25 passing) — not proposed.

## Status and claim vocabulary

`rgcs_lab.common.status_schema` is the single source of the module
list (nine), statuses (GREEN/YELLOW/RED), claim classes (the 01_SHARED
ten), and banned public wording (Project Authority Lock). Construct a
`ModuleStatus`; UI badge text comes from `.badge_text()`. Banned
wording inside result payloads raises at construction — a UI cannot
render what the schema refuses to build.

## Receipts

`rgcs_lab/common/receipt_schema.json` is the canonical JSON Schema
(packaged). `validate_receipt()` is the in-process gate; write module
receipts to `docs/program/receipts/<module>.json`. **The hub derives
every card's live status from those files** via
`rgcs_lab.authority.hub_registry.module_status`: no receipt → RED
`NOT_EXECUTED`; invalid receipt → RED `INVALID_RECEIPT`; otherwise the
receipt's status verbatim. A module can never be GREEN because a UI
rendered — build the receipt by *executing* the module (see
`coordinate_status.build_coordinate_receipt` as the pattern).

## Physics Truth Gate (machine-readable)

`rgcs_lab.authority.physics_truth_gate` carries the implementable-
effects whitelist, the 13 never-promote claims, the mandatory 12-field
energy ledger with `validate_energy_ledger` (arithmetic closure or
refusal — WS07 solvers must emit ledgers that pass it), the nine-step
promotion protocol, and `screen_text_for_banned_claims` for doc/UI
copy. **Parametric resonance, intrinsic spin, torsion, and QET are
four separate `ConceptBoundary` records** with exact energy and
evidence boundaries; `refuse_concept_conflation` refuses chaining them
into a combined mechanism. The conclusion ceiling for any residual is
verbatim: `anomalous residual detected under protocol X`.

## Workstream authority modules

* WS01 `coordinate_status` — bridges the shipped `rgcs_coordinate`
  workbench into the shared schema; receipt built by execution;
  projection lane carries the verbatim R10.8.5A YELLOW verdict.
* WS04 `memory_spec` — provenance graph types (summaries without
  children are refused), PUBLIC/PRIVATE_OPERATOR authorities (private
  material never enters fixtures), the five equal-budget benchmark
  arms, four mandatory ablations, metrics with units.
  `validate_benchmark_report` is the gate Codex's runner must pass.
* WS05 `dual_pole_machine` — deterministic proposer/critic state
  machine: no approval without evidence bindings, MEASUREMENT claims
  need RECEIPT bindings, no BLOCKED→APPROVED edge, append-only ledger.
  LLM prompting layers on top; the guarantees do not depend on it.
* WS07 — energy-ledger authority above; solver ownership is Codex.
  Required non-claims are on the hub card: MHz spoof-SPPs are not
  optical plasmons; field confinement is not gravity modification;
  simulated gain is not excess energy.
* WS08 `prediction_registry` — freeze-with-controls (sham + detuned
  mandatory), sha256 digest over canonical JSON + freeze commit,
  measurements bind to the digest after the freeze, closed outcome
  vocabulary, non-claims embedded in every status.
* WS09 `hub_registry` — the nine cards with
  demonstrates / does-not-demonstrate / I/O / owner, and
  `hub_index()` for Cursor to render.

## Coordination

Claimed files: `docs/program/coordination/CLAIMED_FILES_claude.txt`.
The single `pyproject.toml` hunk (adding `rgcs_lab*`) is flagged as a
merge-coordination point — Cursor owns package wiring; integration
adapters win on conflict. No Codex or Cursor receipts existed at this
writing to review; the review obligation stands open and is listed in
each handoff receipt.
