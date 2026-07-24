# R13 Phase Receipt

```text
phase_id: 23
phase_title: Speckle, Interferometric, and Photoelastic Imaging
status: COMPLETE
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: r13/imaging.py, tests/v6/test_r13_imaging.py
files_modified: none (r13/__init__.py __all__ and packaging registered in Phase 01)
tests_added: 8
focused_test_result: 8 passed
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: 52e50d49343e1e0b0fb65a13cf7c976d11ed9f2bfaa743ab0c28050b3409a834 (build_meta compute_source_hash over SOURCE_ROOTS incl. r13)
claim_classes_emitted: IMAGING_RECONSTRUCTION_MODEL; NUMERICAL_SIMULATION
private_files_read: false
```

## Work completed

Delivered `r13/imaging.py` with focused tests in
`tests/v6/test_r13_imaging.py`. Verdict **`IMAGING_RECONSTRUCTION_MODEL`**.
Creates low-cost through advanced optical readout stages for quartz deformation
and wave propagation, as a numerical reconstruction model.

## Evidence and equations implemented

- `forward_project(image, angles)` (parallel-beam Radon) and
  `reconstruct(sinogram, angles)` (ramp-filtered back-projection). A full-angle
  round trip recovers a two-disk phantom (error ≈ 0.04).
- `error_vs_angles` shows monotone degradation as views drop; `psf_width`
  broadens from ≈10.3 (full-angle) to ≈17.7 (6-angle).

## Negative results

The phantom, sinogram, and reconstruction are synthetic; no real specimen was
imaged. A few coplanar views underdetermine the field: a 6-angle
reconstruction is streaky and incomplete (error ≈ 0.29, more than 2× worse than
full-angle), tying the imaging limit directly to the six-angle ring (phase 22).
A 6-angle reconstruction is not a complete 3-D image.
`refuse_reconstruction_as_measured` raises (a reconstruction of a synthetic
phantom is not an image of a real source) and `refuse_fewangle_as_complete`
raises (a 6-angle reconstruction is not a complete field).

## Deviations from prompt

None.

## Blocking inputs, when applicable

None for the model. Imaging a real specimen would require operated optical
hardware (out of scope).

## Downstream impact

The few-angle degradation curve confirms the six-angle ring limit (phase 22)
and constrains the optical readout stage of the synchronized DAQ (phase 24).

## Reopening test

Re-run `tests/v6/test_r13_imaging.py`; reopen if the verdict string
`IMAGING_RECONSTRUCTION_MODEL` changes, if the 6-angle reconstruction error
stops exceeding the full-angle error, or if `refuse_reconstruction_as_measured`
or `refuse_fewangle_as_complete` stops raising.

## Acceptance checklist

- [x] focused tests pass (8 passed)
- [x] receipt written
- [x] claim classes recorded
- [x] no private files read
- [x] PHYSICAL_VALIDATION_NOT_CLAIMED
