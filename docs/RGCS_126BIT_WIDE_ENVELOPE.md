# The 126-bit wide envelope

How a long decimal record frames, pads, and splits — and the two framing errors
that produced wrong answers before this was written down.

---

## Framing is decimal, not octal

```
record   = decimal_header | decimal_payload | decimal_terminal
header   = "16"
terminal = "3"
```

For the reference fixture:

```
record   1687549873523387598456323376543328567433   (40 digits)
payload  8754987352338759845632337654332856743     (37 digits)
```

### Error 1 — stripping the terminal in octal space

R10.63 removed the header in decimal and then dropped the **last octal digit** of
what remained. That also yields 126 bits, so it survived casual inspection. It is
a different number:

```
octal-stripped   (wrong)  101672770075311773227352216477536105260021
decimal-stripped (right)  064542306375724625654273330377576404214647
```

Every result computed on the first string is void. It is retained as
`wide_envelope.SUPERSEDED_PAYLOAD_OCTAL` so it cannot quietly return, and
`fixture_receipt()` raises if the parser ever reproduces it.

### Error 2 — measuring divisibility with the framing still attached

An earlier analysis computed which character packings could fit while the header
and terminal bits were still in the stream, and concluded that 6-, 7- and 9-bit
packings were *arithmetically impossible*. On the stripped payload all three fit
exactly. The arithmetic objection was simply wrong; the null result that followed
had to be re-established on measurement instead.

---

## Padding, and a convention worth noticing

The payload integer is **123 significant bits**. The width law is:

```
W = 21 + 3D
```

and **123 is itself a legal width** — `123 = 21 + 3(34)`. The specification
nonetheless pads to **126**. So "next legal width" means the next one *strictly
greater*: the envelope always carries at least one leading pad bit.

```
REQUIRE_PAD_BIT = True
next_legal_width(123, require_pad=False) == 123
next_legal_width(123, require_pad=True)  == 126
```

That is a **choice, not arithmetic**, and it changes `D` from 34 to 35 and the
split count from 35 to 36. It is recorded in every parse as `pad_convention` and
asserted by test, because a reader could reasonably have stopped at 123.

| quantity | value |
|---|---|
| significant bits | 123 |
| padded width | 126 |
| pad bits | 3 |
| octal digits | 42 |
| `D` | 35 |
| legal splits | 36 |

---

## Grammar

```
C_L^(dL) | E3 | S_tor,6 | S_pol,6 | S_rad,6 | C_R^(dR)
dL + dR = 35,   dL in 0..35   ->   36 legal splits
```

The 7-octal-digit core is `E3` (3 bits) plus toroidal, poloidal and radial
6-bit state values. The remaining 35 digits are the two refinement chains.

### One record, not four words

Earlier width segmentations admitted four blocks. That was an artifact of leaving
the framing bits in place. The record contains exactly **one** `16` header and
**one** terminal, so it is a single wide envelope. `header_count_in_record` is
carried in every parse.

### The outbound/inbound reading

The candidate interpretation is that `C_L` ascends from the source-local shell
toward a pivot and `C_R` descends into the destination-local shell.

**This is source-provenance guidance, not verified semantics.** Every split
carries `pivot_semantics: UNVERIFIED_SOURCE_PROVENANCE_GUIDANCE` and
`authority: STRUCTURAL_PARSE_ONLY`.

### No split is selected

`enumerate_splits()` returns all 36 and ranks nothing. `selected_split` is
`None`. A split may only be chosen by an independently frozen rule — never
because its map or its plaintext looks attractive.

One reading has already been tested and refuted: chain digits as 45° compass
bearings produced **0 hits at p < 0.05 across 48 permutation tests against 2.4
expected by chance**. See
[`negative_results/R1063_WIDE_ENVELOPE_NULLS.md`](../negative_results/R1063_WIDE_ENVELOPE_NULLS.md).

---

## Conventional packings over the corrected payload

126 bits divides evenly by **6, 7, 9, 14, 18, 21, 42**. All the character
profiles therefore *fit*; none of them *survives*:

| profile | fits | survives null |
|---|---|---|
| DEC SIXBIT (PDP-6/PDP-10) | yes | no |
| CDC display code | yes | no |
| 7-bit ASCII | yes | no |
| 9-bit Multics | yes | no |
| RADIX-50 (3 chars / 16 bits) | — | no |

The expected result is that **no convincing conventional text survives**. That is
a regression expectation, not an immutable conclusion — `text_lanes.assess()`
compares the best candidate against the 95th percentile of matched random
controls under the same hypothesis count, and would report
`CONVENTIONAL_TEXT_CANDIDATE` if one ever cleared it.

---

## Reproducing

```bash
python -m rgcs_archive verify
python -m rgcs_archive route 1687549873523387598456323376543328567433
```

`verify` asserts every quoted value rather than trusting it. If the parser ever
stops reproducing the fixture it raises instead of re-framing silently.
