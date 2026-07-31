# BATSE adapter

**Status: ADAPTER_STUB - not implemented.**

The typed adapter interface and the mission entry exist, so this attaches without
touching the codec core. `python -m rgcs_archive adapter-info batse` reports the
blocker rather than pretending the lane works.

## Blocker

The burst-trigger package reader is not implemented. Each product type must
stay distinct, with declared burst windows plus off-burst controls.

## What must not be assumed when it is built

- Calibrated spectral products are **not** the same object as raw waveform or
  event frames. Keep them distinct.
- Each instrument product type stays separate; detectors are never mixed without
  a recorded interleave recipe.
- Declared event windows always ship with matched off-window controls.
- A famous target is never a training label for RGCS output.

See [SOURCE_AND_REPRESENTATION_BOUNDARIES](SOURCE_AND_REPRESENTATION_BOUNDARIES.md).
