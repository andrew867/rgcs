# R13 Phase Receipt

```text
phase_id: 12
phase_title: Chiral Phonons and Magnetic Splitting in Quartz
status: COMPLETE
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: r13/chiral.py, tests/v6/test_r13_chiral.py
files_modified: none
tests_added: 14
focused_test_result: 14 passed
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: build_meta source hash over SOURCE_ROOTS (incl. r13); references hashed by srcregistry
claim_classes_emitted: ANALYTIC_MODEL
private_files_read: false
```

## Work completed

Modeled circular/chiral phonon branches and possible magnetic-field
signatures. Verdict **`CHIRAL_PHONON_MODEL_ANALYTIC`**. The module states the
small algebra of chiral phonons at a hexagonal zone corner: the circular basis
`e± = (e_x ± i e_y)/√2` is orthonormal under the Hermitian inner product and
diagonalises the rotation generator `L = [[0,−i],[i,0]]` with eigenvalues `+1`
and `−1`. `refuse_model_chirality_as_measured` refuses reading any computed
`l_z` as a measured circular-dichroism or phonon-Hall signal.

## Evidence and equations implemented

- `phonon_angular_momentum` returns per-mode `l_z = ħ·⟨v|L|v⟩/⟨v|v⟩`: a
  left-circular mode carries `+ħ`, a right-circular mode `−ħ`, a linear
  polarization exactly zero (a non-eigenvector is refused, not assigned a bogus
  value).
- `valley_pseudo_angular_momentum` locks chirality opposite at the two valleys:
  `+ħ` at `K` and `−ħ` at `K'`, since they are time-reversal partners — a
  common sign would break time-reversal by hand.
- `valley_selection` returns which valley a circular drive addresses, flipping
  with the drive helicity (a linear drive selects neither and is refused).

## Negative results

No lattice, phonon or valley exists; no mode was excited; no angular momentum,
dichroism or magnetic/Hall signal was measured. A computed `l_z` is not an
observed circular-dichroism or phonon-Hall signal, and the K/K' chirality lock
is imposed by time-reversal symmetry in the model, not observed. Every
polarization is a declared vector; `l_z` is a closed form on it and the lattice
form factor is taken as one.

## Deviations from prompt

None.

## Blocking inputs, when applicable

None — software/architecture phase. (A real chiral-phonon / magnetic-splitting
signature would require the inelastic-scattering experiments blocked in phases
32–35.)

## Downstream impact

The chiral-phonon algebra feeds the synthetic INS/IXS chiral-scattering model
(32) and the alternative-probe (Raman/RIXS) survey (35).

## Reopening test

Re-run `tests/v6/test_r13_chiral.py`; reopen if the verdict string changes, if
`l_z` departs from `±ħ`/0 on the circular/linear modes, if the K/K' sign lock
breaks, or if `refuse_model_chirality_as_measured` stops raising.

## Acceptance checklist
- [x] focused tests pass
- [x] receipt written
- [x] claim classes recorded
- [x] no private files read
- [x] PHYSICAL_VALIDATION_NOT_CLAIMED
