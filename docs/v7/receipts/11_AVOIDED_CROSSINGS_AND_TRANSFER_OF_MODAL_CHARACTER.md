# R13 Phase Receipt

```text
phase_id: 11
phase_title: Avoided Crossings and Transfer of Modal Character
status: COMPLETE
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: r13/avoided.py, tests/v6/test_r13_avoided.py
files_modified: none
tests_added: 16
focused_test_result: 16 passed
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: build_meta source hash over SOURCE_ROOTS (incl. r13); references hashed by srcregistry
claim_classes_emitted: ANALYTIC_MODEL
private_files_read: false
```

## Work completed

Modeled coupled-mode signatures and distinguished real hybridization from
numeric proximity. Verdict **`AVOIDED_CROSSING_MODEL_ANALYTIC`**. The module
states the closed-form theory of an avoided crossing in the two-level
Hamiltonian `H(x) = [[E1(x), g], [conj(g), E2(x)]]`, whose eigenvalues are
`E± = mean ± √(δ² + |g|²)` with `δ = (E1−E2)/2`.
`refuse_model_crossing_as_measured` refuses reading a modelled anticrossing as
an observed mode repulsion — a model gap has no linewidth, no calibrated tuning
axis and no apparatus.

## Evidence and equations implemented

- The load-bearing distinction between hybridization and proximity is the
  minimum gap: the branch separation `2√(δ² + |g|²)` bottoms out at the
  degeneracy point at exactly `2|g|`, zero iff the coupling is zero — split
  branches never touch unless uncoupled.
- `avoided_crossing_sweep` sweeps tuning through the crossing and confirms the
  minimum matches `2|g|` and the branches never cross.
- `diabatic_adiabatic_swap` shows eigenvectors exchange diabatic character
  (small far-side overlap) while adiabatic eigenvalue ordering stays continuous.
- `landau_zener_probability` gives `P = exp(−2π|g|²/(ħ|dΔ/dt|))`, diabatic for
  a fast sweep and adiabatic for a slow one.

## Negative results

No two-level system, resonator or pair of modes exists; no level was tuned; no
gap, splitting, coupling or transition probability was measured. A minimum gap
in a model spectrum is not an observed mode repulsion. Every level, coupling
and sweep is a declared input; the spectrum is a closed form on it.

## Deviations from prompt

None.

## Blocking inputs, when applicable

None — software/architecture phase.

## Downstream impact

The anticrossing theory is the model consumed by the avoided-crossing sweep
experiment (26) and informs the transfer-of-character analysis in the
cross-domain transfer benchmark (30).

## Reopening test

Re-run `tests/v6/test_r13_avoided.py`; reopen if the verdict string changes, if
the minimum gap departs from `2|g|` or the branches cross when coupled, if the
Landau-Zener limits fail, or if `refuse_model_crossing_as_measured` stops
raising.

## Acceptance checklist
- [x] focused tests pass
- [x] receipt written
- [x] claim classes recorded
- [x] no private files read
- [x] PHYSICAL_VALIDATION_NOT_CLAIMED
