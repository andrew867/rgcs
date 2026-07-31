# Fermi GBM adapter

**Status: ADAPTER_STUB - not implemented.**

The typed adapter interface and the mission entry exist, so this attaches without
touching the codec core. `python -m rgcs_archive adapter-info fermi_gbm` reports the
blocker rather than pretending the lane works.

## Blocker

The trigger package reader is not implemented. TTE, CTIME and CSPEC are
distinct products. Start from bounded trigger packages, never continuous
mission-scale TTE. GRB 221009A is a declared target, not a training label.

## What must not be assumed when it is built

- Calibrated spectral products are **not** the same object as raw waveform or
  event frames. Keep them distinct.
- Each instrument product type stays separate; detectors are never mixed without
  a recorded interleave recipe.
- Declared event windows always ship with matched off-window controls.
- A famous target is never a training label for RGCS output.

See [SOURCE_AND_REPRESENTATION_BOUNDARIES](SOURCE_AND_REPRESENTATION_BOUNDARIES.md).
