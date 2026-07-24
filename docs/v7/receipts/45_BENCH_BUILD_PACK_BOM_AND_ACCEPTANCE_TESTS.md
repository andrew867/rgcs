# R13 Phase Receipt

```text
phase_id: 45
phase_title: Bench Build Pack, BOM, and Acceptance Tests
status: COMPLETE (build pack + BOM); the physical build BLOCKED_MISSING_INPUT
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: r13/apparatus.py, tests/v6/test_r13_apparatus.py
files_modified: (none)
tests_added: 17
focused_test_result: test_r13_apparatus.py 17 passed
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: build_meta source hash over SOURCE_ROOTS (incl. r13)
claim_classes_emitted: ENGINEERING_CANDIDATE
private_files_read: false
```

## Work completed

Assembled every hardware design into one build-ready package, driven by
`r13/apparatus.py`: the apparatus design (phase 20), the detector stack
(phase 21), the six-angle ring (phase 22), and the imaging stages (phase 23).
Claim class `ENGINEERING_CANDIDATE`; the built bench and its measurements are
`BLOCKED_MISSING_INPUT`.

## Evidence and equations implemented

- **Bill of materials.** `apparatus.bill_of_materials()` — 8 components
  (Helmholtz coils, piezo transducer, fixture, generator, amplifier, preamp,
  lock-in/heterodyne receiver, temperature control), each `DESIGN_ONLY` with
  generic vendor categories and an estimated line cost; total is the exact
  line sum.
- **Wiring / signal chains.** `excitation_chain()` and `readout_chain()`,
  validated port-to-port over registered components only.
- **Safety envelope.** `SafetyEnvelope` + `check_safety(settings)` bounds
  drive levels, voltages, and currents and always reports `validated=False`.
- **Acceptance tests (design-time).** The `qcmstack` self-consistency checks
  (Sauerbrey ↔ BVD ↔ ring-down) define the acceptance criteria a built bench
  would have to meet on synthetic-equivalent inputs.
- Refusals: `Component.__post_init__` refuses a `BUILT`/`MEASURED` status;
  `refuse_design_as_built`, `refuse_design_as_measurement`.

## Negative results

A build pack and acceptance criteria are **not** a built, accepted bench. No
hardware was fabricated and no acceptance test was run against a device; the
safety envelope always reports `validated=False`.

## Deviations from prompt

None.

## Blocking inputs, when applicable

The physical build is **BLOCKED_MISSING_INPUT**: fabricating the apparatus and
running the acceptance tests requires an actual bench, which is not available.
The pack, BOM, and design-time criteria are complete; the build is not.

## Downstream impact

The bench is one of the R14 blocked inputs carried to phase 48's handoff;
until it exists, every apparatus-derived number stays `ENGINEERING_CANDIDATE`
and no measurement claim can descend from it.

## Reopening test

Re-run `tests/v6/test_r13_apparatus.py`; reopen if a `BUILT`/`MEASURED`
component status stops being refused, if `check_safety` ever returns
`validated=True`, or if either design-as-built refusal stops raising.

## Acceptance checklist
- [x] focused tests pass
- [x] receipt written
- [x] claim classes recorded
- [x] no private files read
- [x] PHYSICAL_VALIDATION_NOT_CLAIMED
