# Agent 08 Handoff — Optical, Coil, and Drive Projections

Status: COMPLETE. 16 new tests; registry RSCS2-E.8/E.9/E.10/E.11.

## Delivered

- `rscs2_core/projections.py`: wavelength presets (octave targets
  declared ARITHMETIC, no coupling claim), Ghosh-1999 Sellmeier
  (anchors frozen constants at 589.3 nm), uniaxial n(θ), vector Snell
  (pinned to frozen scalar), canonical-crystal probe-path menu
  (targets: geometric centre / frozen node prior / eye-candidate=None),
  photoelastic phase projection, Beer–Lambert proxy, Jones elements on
  frozen PolarizationState, Biot–Savart polyline + coil pair
  (frozen coil_pair_phases × winding handedness), field gradient +
  energy density, modal drive projection, capacitive traction proxy,
  leakage-gated coupling report, macro sequences (honest half-spacing
  non-closure flags), drive phase table (frozen six-term budget).
- Evidence: `evidence/v4/agent08/` — ray_paths.png, probe_paths.csv,
  coil_field_overlay.png, phase_delay_budget.png/csv,
  drive_mode_overlap.csv, macro_sequences.csv.
- `docs/plans-v4/OPTICAL_AND_COIL_PROJECTION_REPORT.md`.

## Interfaces Agent 09 (eye engine) consumes

- `crystal_targets(c)` / `probe_paths(c, eye_candidate_mm=...)`:
  the eye-candidate slot takes the Agent-09 coordinate when (and only
  when) the consensus engine produces one.
- `photoelastic_phase_shift_rad`: diagnostic D (optical projection of a
  candidate mode's strain along a probe path).
- `project_force_vector` / `assemble_body_force`: drive-side
  addressability of a candidate mode.

## Honesty rails already in force

- Octave presets: arithmetic disclaimer in the preset dict AND module
  docstring (tested string match).
- Walk-off not modelled: declared; fail-loud requirement documented.
- No coupling record without the coil-only leakage baseline (raises).
- Half-spacing sequences flagged not-closing via frozen exact_closure.
- No toroidal-eye assumption in the coil field.
