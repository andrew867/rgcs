# Concepts and claim boundaries

Read this before quoting any output of the workbench.

## What the packet is

A nine-digit decimal transmission value is a **wire representation**
of a 30-bit word. The word splits into typed fields:

```text
F5  — five-bit face token (0–19 valid, 20–31 reserved)
Q22 — eleven quaternary refinement symbols (a recursive path)
S3  — three-bit shell register (0–7)
```

The decode chain is fixed:

```text
decimal -> 30-bit binary -> octal -> F5|Q22|S3 -> hierarchical address
        -> (separate, downstream) physical projection -> lat/lon LAST
```

## What the Morton X/Y/Z numbers are NOT

The Morton/octree audit deinterleaves the nine spatial octal digits
into three bit paths. The resulting X, Y, Z integers are
**hierarchical path indices**. They are never latitude, longitude,
Cartesian coordinates, kilometres, or altitude, and the API refuses
any attempt to read them that way. Converting an address into a
conventional location requires a named projection profile — a
separate, honest step.

## Claim classes

Every result carries one of the machine-readable claim classes
(`rgcs_coordinate.domain.claims.ClaimClass`), most importantly:

* `EXACT_STRUCTURAL` — bit arithmetic on the packet; checkable by
  anyone, GREEN today.
* `TRAINING_EQUALITY` — a supplied calibration pairing. **`165876523 =
  Stonehenge` is this class.** It trained the current frame; it is not
  an independently successful physical decode, and the workbench
  displays both facts without blurring them.
* `OPERATOR_CORRECTION` — a registered data correction whose raw
  extraction stays in provenance (orange-slice B: raw shell 3, active
  shell 7).
* `DERIVED_CANDIDATE` — computed under named profiles; exactly as good
  as the profiles, no better.
* `UNDERDETERMINED` — the declared profiles do not justify a unique
  answer. **The physical projection is this class today.**
* `BLOCKED_MISSING_DATA` — a required input does not exist here and is
  not fabricated (e.g. real IGRF-14 coefficients).

## Standing claims (embedded in every trace)

```text
SOURCE_ORIGIN_VALIDATED: no
STONEHENGE_INDEPENDENTLY_DECODED: no, until the corrected transform passes
OCTAL_PACKET_STRUCTURE_RECOVERED: yes
PHYSICAL_PROJECTION: underdetermined unless a later receipt proves otherwise
```

## Why the projection is YELLOW

The active projection profile (`earth-r1085a`) implements the
corrected outer-in gravity-shell transform (R10.8.5A receipt,
`docs/proofs/r1085a-outer-in-gravity-shell-projection/`). Under it the
Stonehenge training equality *holds* — because the frame was fitted to
it. What remains underdetermined, and is listed in every `project`
result: the roll degree of freedom of the training alignment, the
shell-thickness candidate family, the land-zero family, the
zeta-convention family, the magnetic scalar family, and an open radial
misfit (≥ 6.7 km best-config). A training fit cannot validate itself;
independent validation would require evidence the workbench does not
possess, and it says so.

The verdict string, verbatim:

```text
RGCS_R10_8_5A_YELLOW_PACKET_AUTHORITY_HELD_PROJECTION_UNDERDETERMINED
```

## Separation of layers

1. **Civilization codec** (wire radix + packet layout) — plugin,
   Federation/Terra only today;
2. **Canonical hierarchy** (faces, quaternary refinement, shells) —
   shared semantics;
3. **Body profile** (frame, shells, gravity, magnetics, epoch, ground
   reference) — Earth only today; Mars has no fabricated source root;
4. **Rendering** (conventional lat/lon) — final output only.

A plugin cannot mutate the canonical model or another codec. Epoch
authority: Ba-130 is the sole active long-origin reference;
conventional time scales remain reproducibility metadata.
