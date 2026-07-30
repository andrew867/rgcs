# RGCS R10.11D: E3 octal frame and transition-table envelope

## Result

The four confirmed compact/refined pairs and twelve sparse transitions remain
exact. The full 64 by 8 source table still cannot be reconstructed uniquely
from twelve cells.

Two useful results were obtained:

1. the segmented frame needs one arithmetic correction from `E2` to an
   octal-aligned three-bit field;
2. under a deliberately restricted affine-permutation hypothesis, child
   columns 5 and 6 each collapse to 32 possible full permutations, with 32 of
   64 entries invariant across every completion.

Neither result is physical or geographic validation.

## 1. Exact octal-aligned frame

The `E2` proposal fails on the sealed vector `1687209343`.

After removing header `16` and terminal `3`, its coordinate payload is:

```text
8720934
```

That value requires 24 bits, so it cannot fit:

```text
E2 | S6 | S6 | S6 | C3
2 + 18 + 3 = 23 bits
```

The minimal frame that preserves all known transitions and covers the complete
width family is:

```text
1_3 | 6_3 | E3 | S6 | S6 | S6 | C3^depth | terminal_3
```

Compact total:

```text
3 + 3 + 3 + 18 + 3 = 30 bits
```

Each added precision level contributes one more three-bit child.

This preserves every previously extracted training state because the known
`E2=2` and `E2=3` records simply acquire a leading zero in `E3`.

Selected parses:

```text
1687209343
E3 = 4
states = [10, 9, 4]
children = [6]
terminal = 3

16752349783
E3 = 4
states = [30, 63, 58]
children = [4, 2]
terminal = 3

16782953437
E3 = 4
states = [42, 43, 4]
children = [5, 7]
terminal = 7
```

The E3 width is an arithmetic result. Its exact semantic split remains
unconfirmed.

## 2. What can and cannot be computed from twelve table cells

A completely arbitrary child column is a permutation of 64 states. Six known
input/output pairs do not determine the remaining 58 rows.

I tested the narrower hypothesis:

```text
T_c(x) = A_c x XOR b_c
```

over six-bit vectors in GF(2), with `A_c` required to be invertible.

For both child 5 and child 6:

```text
all affine solutions:       64
invertible completions:     32
entries fixed in all 32:    32
entries still ambiguous:    32
```

This does not establish that the source table is affine. It creates a finite,
falsifiable envelope.

### Child 5 envelope

```text
fixed-input hyperplane:
parity(state & 10) = 0

fixed-output hyperplane:
parity(output & 14) = 1
```

### Child 6 envelope

```text
fixed-input hyperplane:
parity(state & 26) = 0

fixed-output hyperplane:
parity(output & 57) = 1
```

The complete invariant and ambiguous rows are in
`AFFINE_CONSENSUS_TABLE.csv`. All 32 full candidate permutations for each
child are included as JSON.

## 3. Two decisive probes, not sixteen random pairs

### Child 5 probe

```text
compact: 165872393
states:  [15, 23, 39]
child:   5
```

Under the affine envelope:

```text
next state at position 1 = 5
next(position 2) XOR next(position 3) = 58
```

There are 32 possible refined wires. One actual refined wire selects the
completion, while the XOR relation supplies an internal check.

### Child 6 probe

```text
compact: 165879633
states:  [15, 34, 59]
child:   6
```

Under the affine envelope:

```text
next state at position 1 = 49
next(position 2) XOR next(position 3) = 48
```

Again, one actual refined wire selects the completion and the second outside
state tests it.

A mismatch falsifies the affine hypothesis immediately. It does not falsify
the confirmed segmented frame or the twelve source-reported entries.

## 4. Conditional predictions

Several compact triples lie entirely in an affine consensus hyperplane. Their
child-5 or child-6 refined output is identical under all 32 completions.

These are exported in `CONDITIONAL_REFINED_PREDICTIONS.csv`.

They remain conditional mathematical predictions. In particular,
`167854923` must not be treated as a Terra prediction because its revealed
source label is lunar.

## 5. Additional corpus corrections

- `1687209343` is no longer blocked by width under E3.
- The old `E2` width statement is insufficient for the full corpus.
- Three British-cluster vectors end in terminal 5, 7, or 9, so they cannot be
  silently treated as broad-surface class 3.
- The `167` Luna interpretation and the Earth-labelled Erie record
  `167849523` remain in direct tension.
- No geographic map was retuned.
- No sealed label was used to select an affine completion.
- No full transition table was fabricated.

## Verdict

```text
RGCS_R10_11D_YELLOW_E3_OCTAL_FRAME_CLOSES_FULL_WIDTH_CORPUS_
AFFINE_CHILD5_CHILD6_ENVELOPES_COMPUTED_SOURCE_TABLE_UNRESOLVED
```
