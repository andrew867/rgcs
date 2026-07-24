# R13 Phase Receipt

```text
phase_id: 20
phase_title: Coils, Transducers, Electrodes, and Sample Fixture
status: COMPLETE (design); BLOCKED_MISSING_INPUT for any measurement (hardware not built)
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: r13/apparatus.py, tests/v6/test_r13_apparatus.py
files_modified: none (r13/__init__.py __all__ and packaging registered in Phase 01)
tests_added: 17
focused_test_result: 17 passed
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: 52e50d49343e1e0b0fb65a13cf7c976d11ed9f2bfaa743ab0c28050b3409a834 (build_meta compute_source_hash over SOURCE_ROOTS incl. r13)
claim_classes_emitted: APPARATUS_DESIGN_PREREGISTERED_NOT_BUILT; ENGINEERING_CANDIDATE; BLOCKED_MISSING_INPUT (built apparatus, any measurement)
private_files_read: false
```

## Work completed

Delivered `r13/apparatus.py` with focused tests in
`tests/v6/test_r13_apparatus.py`. Verdict
**`APPARATUS_DESIGN_PREREGISTERED_NOT_BUILT`**. Turns the field and quartz
models into a repeatable apparatus specification. The DESIGN is COMPLETE; no
hardware is built.

## Evidence and equations implemented

- `Component` (name, function, spec, generic `vendor_class`, cost, ports,
  `status="DESIGN_ONLY"`, `claim_class="ENGINEERING_CANDIDATE"`). Its
  `__post_init__` refuses a `BUILT` or `MEASURED` status — nothing here can be
  marked built.
- A `DESIGN` registry of 8 components: Helmholtz drive coils, piezo transducer,
  mechanical fixture, signal generator, power amplifier, low-noise preamp,
  lock-in/heterodyne receiver, temperature control — each with nominal-rating
  specs and a generic vendor category (no real part numbers).
- `bill_of_materials()` (total = exact line sum). `excitation_chain()` and
  `readout_chain()` are validated to reference only registered components and
  to connect port-to-port.
- `SafetyEnvelope` + `check_safety(settings)` returns pass/fail against declared
  bounds and always reports `validated=False`.

## Negative results

Nothing is built and nothing is measured. A bill of materials and a connected
chain diagram are a design, not an operated instrument.
`refuse_design_as_built` and `refuse_design_as_measurement` raise.

## Deviations from prompt

None.

## Blocking inputs, when applicable

The built apparatus and any measurement are `BLOCKED_MISSING_INPUT` — no
hardware exists. Component `status` is fixed at `DESIGN_ONLY`; the
`__post_init__` refuses `BUILT`/`MEASURED`, and `check_safety` always reports
`validated=False`. Building and operating the bench are out of scope for this
phase.

## Downstream impact

The design registry and BOM anchor the bench build pack (phase 45) and the
preregistration/blinding controls (phase 44).

## Reopening test

Re-run `tests/v6/test_r13_apparatus.py`; reopen if the verdict string
`APPARATUS_DESIGN_PREREGISTERED_NOT_BUILT` changes, if a `Component` accepts a
`BUILT`/`MEASURED` status, or if `refuse_design_as_built` or
`refuse_design_as_measurement` stops raising.

## Acceptance checklist

- [x] focused tests pass (17 passed)
- [x] receipt written
- [x] claim classes recorded
- [x] no private files read
- [x] PHYSICAL_VALIDATION_NOT_CLAIMED
