# Conflict Resolution — RGCS Integration (2026-07-26)

Merge order: base `eb7d7d4` → Claude `188caab` (clean) → Codex `71e7342`
(1 conflict) → Cursor `d4baf0d` (3 conflicts + policy reconciliation).
Every overlapping file was reconciled individually; no lane's directory
was taken wholesale.

## IR-01 — module slug `prediction` vs `predictions`

Claude's `status_schema.MODULES` and `authority/hub_registry.py` used the
singular slug `prediction`; Cursor's entire distribution surface (catalog,
adapters, API routes, fixtures, receipts, module pages — ~40 files) and
the product UI used `predictions`. No Claude test hard-coded the singular
slug. **Resolution:** unified on the plural slug `predictions` in the two
authority-side definitions. This is a slug spelling, not claim wording;
all Claude semantic content (purpose, non-claims, claim classes) is
preserved verbatim. Recorded here as the single authority-side edit made
by integration.

## IR-02 — one status/claim vocabulary (Claude canonical)

Cursor's `rgcs_lab/common/status.py` restated the claim vocabulary and
defined an unvalidated `ModuleResult`. Rewritten so that:

- `CLAIM_CLASSES` is derived from the canonical `ClaimClass` enum;
- the `Status` enum is asserted to mirror canonical `STATUSES`;
- `ModuleResult.__post_init__` constructs a canonical `ModuleStatus`,
  so unknown modules, unknown claim classes, and banned public wording
  (Project Authority Lock) raise `SchemaError` at construction time;
- the hub catalog is asserted to list exactly the canonical `MODULES`.

There is exactly one `ModuleStatus` (Claude's); `ModuleResult` is the UI
envelope that validates through it.

## IR-03 — reference fallbacks can never be GREEN (Cursor adapters rewritten)

Cursor's adapters resolved external package names (`rgcs_golay`,
`rgcs_memory`, …) that do not exist, so every adapter silently ran the
`rgcs_lab.reference` demos while reporting GREEN. Rewritten:

- `adapters.resolve_core` prefers the bundled Codex cores
  (`rgcs_lab.golay`, `rgcs_lab.frames`, `rgcs_lab.memory`,
  `rgcs_lab.dual_pole`, `rgcs_lab.lattice`, `rgcs_lab.metasurface`);
- `adapters.guard_fallback` caps any fallback run at YELLOW and appends
  `REFERENCE FALLBACK IN USE …` to warnings — a fallback can never emit a
  GREEN executed-core receipt;
- every payload and receipt records the executing backend
  (`backend=rgcs_lab.golay` etc.) and `source_commit`;
- reference modules remain in-tree as labelled demos and as the explicit
  fallback path only.

Shape mapping performed by adapters (cores untouched):
golay `OK/CORRECTED/UNCORRECTABLE_OR_AMBIGUOUS` → `ok/corrected/uncorrectable`;
dual-pole `BLOCK/ACCEPT_GREEN/ACCEPT_YELLOW` → `REJECT/ACCEPT/ACCEPT_YELLOW`
(plus `critic_bypassed`, `attacks`); memory rankings → `top_id` (flagship
`complete_proposed_system`); lattice adds `hermitian_residual` computed from
the core Hamiltonian; metasurface maps `power_ledger.numerical_residual` →
`max_conservation_residual` and lists inputs the reduced-order RLCG core
does not represent (`groove_depth_m`, `loss_tan`) instead of pretending to
use them.

## IR-04 — one receipt contract

The two schema JSON files were byte-identical; the packaged
`rgcs_lab/common/receipt_schema.json` is canonical and
`schemas/lab/receipt.schema.json` remains as the distribution mirror.
Codex's `rgcs_lab.receipts.receipt()` now validates every core receipt
through the canonical `validate_receipt` before returning it, and the
Codex core call sites now use the canonical claim vocabulary (their
previous strings `EXACT_STRUCTURAL`, `ERROR_CORRECTION`, `EXACT_MATH`,
`FRAME_ROTATION`, `BENCHMARK_HARNESS`, `DETERMINISTIC_RETRIEVAL`,
`ADVERSARIAL_RESEARCH_LOOP`, `SYNTHETIC_DIMENSION`, `ENERGY_LEDGER`,
`REDUCED_ORDER_EM_SIMULATION`, `UNDERDETERMINED_PHYSICS_LANE` were not in
the shared contract). Numerical behavior and golden vectors unchanged;
no Codex test asserts those strings.

## IR-05 — one CLI

`rgcs_lab/cli.py` merged: the six core subcommands keep the Codex lane's
canonical argument surface and execute cores directly (`golay demo
--address/--flip/--random-flips`, `frames example`, `memory benchmark
[corpus]`, `dual-pole audit`, `lattice run`, `metasurface sweep`);
`doctor`, `serve` (loopback-refusal preserved), `modules`, `coordinate`,
`predictions` come from the Cursor lane through the adapter layer.
`memory benchmark` gains a default corpus (the packaged
`rgcs_lab/data/memory_corpus/`) so the installed wheel works outside the
repository; an explicit corpus path still behaves exactly as in the Codex
lane. One console script `rgcs-lab` plus `python -m rgcs_lab`.

## IR-06 — `rgcs_lab/__init__.py`

Claude's authority docstring (updated to the post-merge layout) +
Cursor's product constants; `MODULES` imported from the canonical schema
(single source). Constants are defined before the import because
`common.receipts` reads `rgcs_lab.__version__` during package import.

## IR-07 — packaged memory corpus

Cursor's reference memory had a built-in 4-doc corpus; the Codex engine
requires a corpus directory. The four hub documents now ship as package
data (`rgcs_lab/data/memory_corpus/*.json`) in the Codex corpus format,
and the memory adapter runs the Codex engine over them. The Codex example
corpus (`examples/rgcs_lab/memory/`) is untouched and still used by the
Codex tests.

## IR-08 — predictions module

No Codex predictions core exists by design. The hub demo remains the
Cursor reference implementation (always YELLOW, so the fallback rule is
not violated) and its receipts/warnings now name the authority contract
(`rgcs_lab.authority.prediction_registry`, Claude) as the governing
specification. The two APIs serve different layers (public hub demo vs
authority registry with mandatory sham/detuned controls); this is
recorded as intentional, not duplication.

## IR-09 — test module basename collision

`tests/rgcs_lab/test_frames.py` (Codex) collided with the pre-existing
`tests/cwatlas/test_frames.py` under pytest's rootdir import mode,
breaking full-suite collection. Renamed to
`tests/rgcs_lab/test_rlab_frames_core.py`; contents unchanged.

## Frozen surfaces — verified untouched

- Coordinate packet parser (`rgcs_coordinate/*`): no lane and no
  integration change touches it; `tests/rgcs_coordinate` 30/30 pass.
- Golden vectors: unchanged; Codex property/golden tests pass unmodified.
- Claude earned-status logic (`authority/*`, `common/status_schema.py`
  except the IR-01 slug): unchanged; all 25 authority tests pass.
