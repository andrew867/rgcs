# The V1 coordinate system — overview

The one-page map of how a decimal wire becomes a point on Earth, and where the chain
stops being verified.

```text
The tool verifies geometry. It does not verify that a candidate vertex is
physically true.
```

---

## The pipeline

```
decimal wire
   ↓  binary / octal — never decimal triplets            VERIFIED
30-bit word
   ↓  two exact field cuts                               VERIFIED
F5 | Q22 | S3          and        R4 | S8 | P12 | tail
   ↓  source_face = (F5 + 14) % 20                       DECLARED
icosahedral face
   ↓  11 × 4-way spherical refinement at t = 10/19       DECLARED
kernel vector u
   ↓  lat/lon = normalize(A u)                           UNDERDETERMINED (B01/B02)
candidate position
```

Everything above the projection line is exact arithmetic that reproduces on
re-execution. The projection line is where the open problem lives.

---

## Stage 1 — the wire is binary, not decimal

A direct RGCS word is a 30-bit integer that happens to be written in decimal. Its
leading `16` is an artifact of that rendering, **not a field**. Stripping it yields a
value that is no longer 30 bits and no longer addresses anything.

Enforced structurally by `r1053.kernel.assert_direct_lane`, which refuses anything
wider than 30 bits, and `decimal_header_table_applies`, which returns `False` for every
direct word.

Details: [VARIABLE_LENGTH_CODEC.md](VARIABLE_LENGTH_CODEC.md)

## Stage 2 — two exact cuts of the same word

```
geometric:   F5 | Q22 | S3          (5 + 22 + 3  = 30)
diagnostic:  R4 | S8  | P12 | tail  (4 + 8 + 12 + 6 = 30)
```

Both reversible, neither privileged. `S3` is the mandatory terminal check/shell digit
and is **excluded from the geometry** — eight words differing only in `S3` land in the
identical cell, which is asserted as a test rather than declared.

## Stage 3 — the octal branch

The leading three octal symbols partition the labelled corpus with no observed
crossovers:

```
117 → Britain          120 → North America
```

This is the sharpest structural result in the programme. It also generates a live
contradiction: `165879243` is branch `117` while its working label is in Quebec — see
[BLOCKERS_B01_B07.md](BLOCKERS_B01_B07.md) B03.

## Stage 4 — the Earth frame

A coordinate without a frame is not a coordinate. Following the SPICE separation —
a reference frame is an ordered orthonormal triple *with a centre*, a coordinate system
locates points within it, and both plus an epoch are needed for state data — RGCS emits
typed **address certificates**, never bare lat/lon.

```
R_E = (Earth COM, mean rotation axis South-Up, Wilkes angular root candidate,
       SAA phase hand at shell+epoch, MSL datum)
```

Epoch is **gated, not faked**: structural decoding needs no solved calendar, dynamic
projection does.

Details: [EARTH_ROOT_V1.md](EARTH_ROOT_V1.md) ·
[FRAMES_EPOCHS_AND_GALACTIC_DIRECTIONS.md](FRAMES_EPOCHS_AND_GALACTIC_DIRECTIONS.md)

## Stage 5 — the projection, and its limit

```
lat/lon = normalize(A u)
```

`A` is scale-invariant: **9 entries, 8 free parameters**, fitted against **6
constraints** from 3 anchors. Measured constraint-matrix rank is 6, leaving a
**2-dimensional free family**. Every member fits every anchor to machine precision, and
different members place the same non-anchor word thousands of kilometres apart.

Two results are worth stating:

- **`t = 10/19` wins.** Across all 20 face offsets, depths 9–11, and
  `t ∈ {10/19, 1/2, 9/19}`, the source ratio is the best-performing split at every
  setting.
- **A rotation is refuted.** A rotation would have been testable at three anchors; its
  best anchor RMS is 451.6 km. The free projective form — and its under-determination —
  is forced by the data, not chosen.

**Five** independently sourced hard anchors is the threshold at which `A` first becomes
over-determined and the projection becomes falsifiable.

---

## Scales

| depth | cells | cell edge |
|---:|---:|---:|
| 9 | 5,242,880 | **14.989 km** |
| 10 | 20,971,520 | 7.495 km |
| 11 | 83,886,080 | 3.747 km |

The depth-9 edge is the scale the Drummondville residual is read against — with its
null attached. See
[15KM_CELL_FIELD_ENVELOPE_MODEL.md](15KM_CELL_FIELD_ENVELOPE_MODEL.md).

---

## Where to go next

| document | covers |
|---|---|
| [QUICKSTART.md](QUICKSTART.md) | clone to map in five minutes |
| [VARIABLE_LENGTH_CODEC.md](VARIABLE_LENGTH_CODEC.md) | the codec, staged grammar, wide-envelope gate |
| [EARTH_ROOT_V1.md](EARTH_ROOT_V1.md) | frame D_V1, SAA phase hand, the pinning problem |
| [MAP_PATH_POLYGON_GUIDE.md](MAP_PATH_POLYGON_GUIDE.md) | path and polygon geometry, how it is checked |
| [CLAIM_BOUNDARIES.md](CLAIM_BOUNDARIES.md) | verified vs not verified, claim classes |
| [BLOCKERS_B01_B07.md](BLOCKERS_B01_B07.md) | the open problems, unsoftened |
