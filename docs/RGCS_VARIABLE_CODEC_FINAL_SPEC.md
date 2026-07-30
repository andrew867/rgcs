# RGCS Variable Codec — Final Specification

```text
CODEC_STATUS: STRUCTURAL_GREEN
LANE_SEPARATION: ENFORCED_IN_CODE
```

---

## 1. The direct 9-digit lane

**Do not parse direct nine-digit words as decimal triplets.** The leading `16` is a
coincidence of the decimal rendering, not a field. Stripping it produces a value that
is no longer 30 bits wide and no longer addresses anything.

The active lane is:

```
decimal wire → binary → octal → ordered recursive path
```

This is enforced structurally by `r1053.kernel.assert_direct_lane`, which refuses any
value wider than 30 bits, and by
`r1053.kernel.decimal_header_table_applies`, which returns `False` for every direct
word.

### 1.1 Maximum-envelope diagnostic view

```
R4 | S8 | P12 | tail        (4 + 8 + 12 + 6 = 30 bits)
PATH7 = S8_oct3 || P12_oct4
```

Every decomposition below is **verified arithmetically** in
`test_r1059_docs.py::test_codec_spec_path7_decompositions_are_exact`:

| vector | R4 | S8 | S8₈ | P12 | P12₈ | PATH7 | branch |
|---|---|---|---|---|---|---|---|
| `165876523` Stonehenge | 2 | 120 | 170 | 3148 | 6114 | `1706114` | 117 |
| `165892743` Orange A | 2 | 120 | 170 | 3402 | 6512 | `1706512` | 117 |
| `165892763` Orange B | 2 | 120 | 170 | 3402 | 6512 | `1706512` | 117 |
| `165892783` Orange C | 2 | 120 | 170 | 3402 | 6512 | `1706512` | 117 |
| `167849523` Erie | 2 | 128 | 200 | 1208 | 2270 | `2002270` | 120 |
| `168930443` Toronto | 2 | 132 | 204 | 1714 | 3262 | `2043262` | 120 |

The orange triplet shares an identical `PATH7` and differs only in the tail — a
same-cell family, which is exactly what their ~16 km mutual extent shows.

### 1.2 Geometric cut

The projector uses a different, equally exact cut of the same 30 bits:

```
F5 | Q22 | S3          (5 + 22 + 3 = 30 bits)
```

`F5` selects the source face via `(F5 + 14) % 20`; `Q22` supplies 11 two-bit
refinement symbols; `S3` is the **M3 check digit and is not geometry**. Eight words
differing only in `S3` land in the identical cell — asserted in
`test_m3_is_kept_out_of_the_geometry`.

Both cuts are views of the same word. Neither is "the" parse.

---

## 2. Staged maximum-envelope grammar

The fixed `R4|S8|P12|tail` grammar is **demoted to a diagnostic view**. The active
grammar is staged, and every boundary floats:

```
root → section(s) → path step(s) → epoch/state step(s) → shell/check digit
```

| field | capacity | note |
|---|---|---|
| `ROOT` | **fixed** 4 bits, zero-padded | the source says "always 4-bit root zero padded" |
| `SECTION` | ≤ 8 bits | splits into layer2 + **optional** layer3 |
| `PATH` | ≤ 12 bits | up to 4 octal path steps |
| `EPOCH` | optional 3-bit chunks | may remain unresolved |
| `M3` | 3 bits, mandatory, always last | shell / check / type digit |

**Field labels are maximum envelopes, not always-full fields.** A refinement may be
shorter than 20 bits, but must draw at least one unit from the 8-bit section **and**
at least one octal step from the 12-bit path. Implemented in
`r1028.staged.legal_splits` with `SECTION_MIN = 1`, `PATH_MIN = 3`.

Legal split counts after all source constraints: **27 → 9, 30 → 6, 33 → 3, 36 → 1**.

---

## 3. Long envelope lane

Transport envelope:

```
16 | binary-packed payload | terminal
```

Payload layout:

```
C_L,3^dL | E3 | S_tor,6 | S_pol,6 | S_rad,6 | C_R,3^dR
```

Legal width:

```
W = 21 + 3(d_L + d_R)
```

**There is no one-bit extension flag.** Apparent overflow means the next legal 3-bit
refinement depth.

### 3.1 The gate

Wide-envelope records are **refused, never truncated**. Truncating a 41-bit record to
30 bits would manufacture a false address. The seven gated records:

| record | digits | bits | admitted |
|---|---|---|---|
| `1687293589323` | 13 | 41 | ✗ |
| `16872394203` | 11 | 34 | ✗ |
| `168732948753` | 12 | 38 | ✗ |
| `168752934853` | 12 | 38 | ✗ |
| `168752493633` | 12 | 38 | ✗ |
| `1687529232333` | 13 | 41 | ✗ |
| `16875938393` | 11 | 34 | ✗ |

The bridge that would translate them is **REFUTED** (blocker B07). At R10.47C a third
labelled pair (`1658274383 → 165892733`) was the first out-of-sample test of the
header-stripped affine `y = (923x + 550585316) mod 2³⁰`, and it missed by 484,856,892.
Enumerating the full 32-member `(A,B)` family that fits the first two pairs, **zero**
members reproduce the third. Two points cannot over-determine an affine mod 2³⁰ — the
earlier "2 of 2 exact" was the minimum needed to *define* the map, never a test of it.

---

## 4. Epoch handling

Epoch/state chunks can exist, but **spatial structural parsing does not require a
solved calendar**. Epoch becomes required only when projecting dynamic references.
See [Frames, Epochs and Galactic Directions](RGCS_FRAMES_EPOCHS_AND_GALACTIC_DIRECTIONS.md).

```
STRUCTURAL_DECODE:  epoch optional / may remain unresolved
DYNAMIC_PROJECTION: epoch required
PUBLIC_RECEIPT:     declared epoch metadata required
```
