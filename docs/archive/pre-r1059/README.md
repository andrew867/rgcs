# Archived documents — pre-R10.59

> **ARCHIVED: superseded by RGCS V1 release-candidate docs. This file may contain old
> assumptions, including fixed-field parse, rigid icosahedron, old Montreal label, or
> pre-V1 projector wording.**
>
> Retained unmodified for provenance and **not** deleted.

Known superseded content in this directory:

- **`165879243` labelled as Montréal.** Retired at R10.53 to
  `HINT_PROVENANCE_ONLY`; the active working label is
  *Drummondville / Saint-Eugène farm corridor working target*. Neither label may fit
  the projector, and the vector's octal branch `117` remains in conflict with any
  North American label (blocker B03).
- **The header-stripped affine transport bridge** described as confirmed. It was
  **refuted** at R10.47C by a third labelled pair; no member of the fitting family
  reproduces it (blocker B07).
- **Fixed-field `R4|S8|P12|tail` treated as the grammar.** Demoted to a
  maximum-envelope diagnostic view; the active grammar is staged with floating
  boundaries.
- **Nine-digit words read as `16 | payload | 3`.** The leading `16` is a decimal
  rendering artifact, not a field.

For current material see:

- [README](../../../README.md)
- [V1 Earth Root Final Spec](../../EARTH_ROOT_V1.md)
- [Variable Codec Final Spec](../../VARIABLE_LENGTH_CODEC.md)
- [User Manual](../../USER_MANUAL.md)
