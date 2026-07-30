# Time and ground synchronization

A projection needs BOTH an epoch and a ground reference; frames
without either are refused (`refuse_frame_without_epoch`,
`refuse_frame_without_ground_reference`).

Time selects: gravity state J2(t), magnetic state (dipole moment, tilt
and axis at t), shell geometry Delta_s(t), long-term frame state.
Ground reference selects: rotational phase, body-fixed alignment,
surface synchronization. This run: epoch 2025.0, ground reference
`TERRA_SURFACE_SYNC_V1`, South-Up handedness carried as a declared
flag (consumed explicitly by rendering, never silently flipping an
axis).

Alignment modes:

* `SEALED_R1082` — the sealed CALFREEZE orientations, reused exactly;
  under every one of them the training cell still MISSES Stonehenge
  (locked by test — the freeze is not retuned in place).
* `TRAINING_EQUALITY_R1085A` — sealed context composed with the
  minimal rotation solved from the Stonehenge training equality ONLY,
  then sealed. Context choice rule (smallest minimal-rotation angle)
  was declared before results were seen; all context angles:

{
 "rule": "smallest minimal-rotation sealed context, declared before results were seen",
 "context_angles_deg": {
  "BASE": 88.8918,
  "F4_ROTATED_DIRECT_LE": 74.5843,
  "F2_REVERSED_DIRECT_BE": 29.9567,
  "F1_CANONICAL_DIRECT_BE": 24.142,
  "F3_CANONICAL_ROOTREL_BE": 24.142
 },
 "chosen_context": "F1_CANONICAL_DIRECT_BE",
 "correction_angle_deg": 24.142,
 "undetermined_dof": [
  "ROLL_ABOUT_TRAINING_ANCHOR_AXIS"
 ]
}

The roll about the training-anchor axis is UNDETERMINED and recorded
as such — it is one of the reasons the verdict is YELLOW, not a knob.
