# R13 Phase Receipt

```text
phase_id: 05
phase_title: Response Functions, Green Functions, and S-Matrix Core
status: COMPLETE
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: r13/response.py, tests/v6/test_r13_response.py
files_modified: none
tests_added: 15
focused_test_result: 15 passed
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: build_meta source hash over SOURCE_ROOTS (incl. r13); references hashed by srcregistry
claim_classes_emitted: ANALYTIC_MODEL
private_files_read: false
```

## Work completed

Provided one common mathematical interface for linear response while
preserving domain-specific adapters. Verdict **`LINEAR_RESPONSE_CORE_IMPLEMENTED`**.
The module gathers four faces of linear response behind the `LinearSystem`
protocol with three typed adapters — MECHANICAL, ELECTRICAL_BVD and OPTICAL —
each building a Green-function response in its own units. Two governance
refusals hold the line: `refuse_cross_domain_without_certificate` and
`refuse_simulation_as_measurement`.

## Evidence and equations implemented

- Damped-oscillator Green function `G(w) = 1/(w0^2 - w^2 - i*gamma*w)`, with
  FWHM equal to `gamma` in the weakly damped limit.
- Lorentzian susceptibility whose real part is reconstructed from its imaginary
  part by the Kramers-Kronig Hilbert transform (the load-bearing identity the
  tests check).
- Lossless 2x2 beamsplitter S-matrix that is exactly unitary (`S†S = I`, so
  `|Sx|² = |x|²`).
- State-space transfer function `H(s) = C(sI-A)⁻¹B + D`, reducing to `1/(s+a)`
  for a single real pole.

## Negative results

A shared response function is not a shared mechanism: a mechanical resonance,
an electrical motional branch and an optical cavity are not the same physics
because they share a Lorentzian. `refuse_cross_domain_without_certificate`
refuses carrying a response between domains on that strength — the transfer is
licensed only by the bridge-module certificate (phase 06/10). Every response
is evaluated on a declared model; no oscillator, cavity, scatterer or circuit
exists, and `refuse_simulation_as_measurement` refuses reading any evaluated
number as a bench result.

## Deviations from prompt

None.

## Blocking inputs, when applicable

None — software/architecture phase.

## Downstream impact

The Green/S-matrix core is the shared response interface used by the bridge
graph (06), the piezo→BVD bridge (10), the two-mode cavity (18) and the
published-response transfer validation (36).

## Reopening test

Re-run `tests/v6/test_r13_response.py`; reopen if the verdict string changes,
if the Kramers-Kronig reconstruction or S-matrix unitarity identity fails, or
if either refusal stops raising.

## Acceptance checklist
- [x] focused tests pass
- [x] receipt written
- [x] claim classes recorded
- [x] no private files read
- [x] PHYSICAL_VALIDATION_NOT_CLAIMED
