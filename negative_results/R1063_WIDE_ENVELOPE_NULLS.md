# R10.63 — Wide-envelope decode nulls

Five hypotheses about how a 40-decimal-digit wide-envelope record decodes, each
tested against an explicit null and each refuted. Published beside the positive
outputs, as the evidence policy requires.

**Specimen.** A single operator-supplied 40-digit record. After stripping the `16`
transport header and the terminal, the payload is **42 octal digits = 126 bits**, and
it satisfies the codec's own width law exactly:

```
W = 21 + 3(d_L + d_R)     126 = 21 + 3(35)     d_L + d_R = 35, integer
```

The record is therefore **well-formed** under the wide-envelope lane. Only one `16`
appears in the whole string, so it is **one record**, not a run of concatenated words.
What remains unknown is the *semantics* of the two refinement chains.

---

## N1: The record is not Hamming(36,30)-framed

- **class:** NULL
- **test:** syndrome of every 12-octal (36-bit) word across all legal segmentations,
  under four parity conventions (even/odd, MSB-first/bit-reversed, complemented)
- **result:** **0 zero-syndrome words out of 48**; whole-stream framing gave 2/66
  against 1.03 expected
- **null:** P(syndrome = 0) = 1/64 per word
- **ordinary explanation:** 132 bits is not divisible by 36 (3.67), so the code cannot
  frame the stream at all
- **what would change it:** a record whose bit length is a multiple of 36

## N2: The record is not Reed-Muller(32,6)

- **class:** NULL
- **test:** nearest-codeword distance over the 64 RM(1,5) codewords, all bit offsets
- **result:** mean nearest-distance **9.2**, against a random-data mean of **9.29**
- **null:** 20,000 random 32-bit blocks; P(d ≤ 7) = 0.068
- **ordinary explanation:** the message sits exactly on the null. RM decoding always
  succeeds, so distance is the only signal, and there is none
- **what would change it:** blocks landing within distance 7 at a rate above 0.068
- **note:** the Mariner 9 precedent is real — 6-bit pixel data under RM(32,6) — but
  this record does not carry that framing

## N3: The record is not Golay(24,12)

- **class:** NULL
- **test:** `rgcs_lab.golay.decode_block` over 5 blocks, all 13 offsets
- **result:** mean distance **3.0–3.8** against a random-data mean of **3.35**; no
  offset decoded all five blocks
- **null:** 20,000 random 24-bit words. **56.7% of random words "decode" successfully**
  — decode success alone is not evidence, only distance is
- **ordinary explanation:** 132 bits is not divisible by 24 (5.5)
- **what would change it:** a bit length divisible by 24 with mean distance well below
  3.35

## N4: The record is not packed text

- **class:** NULL
- **test:** 6-bit SIXBIT, 7-bit ASCII, 8-bit, 9-bit Multics, Radix-50 (PDP-10 and
  PDP-11 packings), at every bit offset, on both the raw stream and the corrected
  126-bit payload
- **result:** **zero common English trigrams in every variant**; letter fractions at or
  below the 0.39 null
- **null:** 400 random 132-bit strings under the same screens
- **ordinary explanation:** every PDP-10 packing lives in a 36-bit word, and neither
  132 nor 126 bits is a multiple of 36
- **correction recorded:** an earlier version of this test computed divisibility over
  the *framed* stream, including header and terminal bits, and wrongly concluded that
  6-, 7- and 9-bit packings were arithmetically impossible. On the stripped 126-bit
  payload all three fit exactly. They were re-tested and still produce noise. **The
  arithmetic objection was wrong; the null result stands on the measurement.**

## N5: Chain digits are not compass bearings

- **class:** NULL
- **test:** each octal digit of `C_L`/`C_R` read as a 45° compass step; routes walked
  for all 36 legal `(d_L, d_R)` splits; scored on straightness and mean absolute turn
- **null:** **permutation** — 3,000 shuffles of the same digits per split, which
  destroys order while holding digit frequency fixed
- **result (relative-heading mode, where order genuinely matters):**
  **0 hits at raw p < 0.05 across 48 tests, against 2.4 expected by chance.** None
  survive Bonferroni (α = 0.00104)
- **digit frequency:** consistent with uniform, χ² = 8.29 vs 14.07 critical — so the
  result is not a frequency artifact either
- **test-design defect found and corrected:** the first pass used absolute-bearing
  mode and reported 11 splits beating a uniform-random null. That was an artifact.
  In absolute mode a step's direction depends only on the digit's value, so net
  displacement is essentially a vector sum, and **vector addition is commutative**.
  The permutation null exposed this by returning a shuffled mean equal to the observed
  value in almost every row. A second correction was then needed: the invariance is
  **exact in the plane** (measured deviation 1.7e-16) but only **approximate on a
  sphere** (measured 4.1e-5 relative), because spherical translations do not quite
  commute. That residual sits an order of magnitude below the null's own spread
  (~1e-3), so the metric still cannot carry routing information — but the first
  statement of this defect claimed exact invariance and was too strong. The finding
  was withdrawn before it was recorded as a result, and the correction is asserted by
  `test_absolute_mode_straightness_is_order_invariant_to_1e4`.
- **ordinary explanation:** the chains are not direction sequences under this reading
- **what would change it:** a source statement on chain semantics, or a second
  wide-envelope record to cross-reference

---

## What survives

| holds | status |
|---|---|
| Payload satisfies `W = 21 + 3(d_L + d_R)` exactly, d_L + d_R = 35 | structural, exact |
| One record — a single `16`, a single terminal | structural |
| Fields extract cleanly: `E3`, `S_tor`, `S_pol`, `S_rad`, two chains | structural |
| Chain **semantics** | **unknown**; the bearing reading is refuted |

The blocker is the same shape as V1-B02: **one sample cannot determine a rule.** Thirty-six
admissible splits against one record is underdetermined exactly as eight projector
parameters against six constraints are. A second wide-envelope record would do more
than any further analysis of this one.

## Boundary

These are nulls about **one specimen under specific framings**. None of them refutes
the wide-envelope lane, the Hamming(36,30) codec (whose own tests pass on sample
payloads), or `rgcs_lab.golay` (which is correct and tested). They refute five
readings of one record.
