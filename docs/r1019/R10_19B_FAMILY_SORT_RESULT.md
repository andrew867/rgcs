# R10.19B — bridge-family sorted vector ledger

**Verdict:** `R10_19B_VARIABLE_VECTOR_FAMILIES_SORTED`
**Claim:** `NO_UNIVERSAL_BRIDGE_CLAIM`
**Evidence class:** DERIVED (symbolic). No physical validation claimed.

## The structural split

One test does the real work: **`value < 2^30`**.

| | meaning | bridge needed |
|---|---|---|
| below 2^30 | the value **is** a SurfaceWord (all 9-digit in this ledger) | none |
| at/above 2^30 | a variable/transport form | yes — and *which* decoder is a question of **provenance**, not digits |

Family within each side is therefore taken from the declared
`record_group`. This module never infers a private-path or two-sided
codec family from a digit string.

## Sorted result — 92 live rows (2 Montréal rows quarantined out)

| n | family | affine allowed |
|---:|---|---|
| 27 | `R10_11F_TWO_SIDED_VARIABLE_CODEC` | no |
| 17 | `DIRECT_OR_CANONICAL_30BIT_SURFACEWORD` | n/a — no bridge needed |
| 14 | `PRIVATE_PATH_BASE100_OR_TWO_SIDED_VARIABLE_CODEC` | no |
| 12 | `DIRECT_30BIT_SURFACEWORD_RAW` | n/a — no bridge needed |
| 6 | `PACKED40_4BIT_HEADER_36BIT_PATH` | no |
| 6 | `BASE100_OR_NON16_VARIABLE_ROUTE` | no |
| 2 | `HEADER_STRIPPED_AFFINE_SAME_LOCATION_BRIDGE` | **yes — closed at 2** |
| 2 | `KNOWN_SAME_LOCATION_CANONICAL_TARGET` | n/a |
| 2 | `WORKED_EXAMPLE_NOT_GEOGRAPHIC` | no |
| 2 | `UNRESOLVED_VARIABLE_ROUTE` | no |
| 1 | `PAYLOAD_OCTAL_STONEHENGE_RIGHT_APPEND_FAMILY` | no — different route |
| 1 | `CORRUPTED_COLLISION_EXCLUDED` | no |

**33 projectable** into the R10.18D projector · **58 never affine**.

## Two confirmed relations, in two different spaces

**1. Header-stripped affine — CLOSED at two rows.**

    1643789253 -> 43789253 -> 165876523   Stonehenge   EXACT
    1672875493 -> 72875493 -> 168930443   Toronto      EXACT

Constants `923` / `550585316` are read from `r109.superseded`, recorded
before this analysis; nothing was fitted here. Honest strength: two
points do not pin an affine mod 2^30 — `gcd(ΔX, 2^30) = 32`, so 32
`(A,B)` pairs fit both, and the recorded pair is the **smallest-`A`
member** of that family. A pre-recorded pair landing inside it by
chance: `32/2^60 = 2.8 × 10⁻¹⁷`.

**2. Payload-octal right-append — a different space entirely.**

    Stonehenge 165876523  payload octal = 2173604
    Avebury    1647012173 payload octal = 21736041 = 2173604 || 1

Exact in decimal: `4701217 = 587652 × 8 + 1`. Avebury is Stonehenge's
child one octal level deeper.

This is why the earlier affine cross-check on Avebury "failed": it was
the wrong family. `bridge("1647012173")` gives 993148035, sharing 0 of
10 prefix symbols. That was a category error on my part, not evidence
against the append relation.

## Why there is no affine fallback

R10.19 applied the affine to all 66 transport rows:

- 3 of 62 matched the anchor F5/S3 profile — but **two of those three
  are Stonehenge and Toronto themselves**, which sit inside the
  transport list. Counting them is training leakage.
- **Independent confirmations: 1 of 60, against 0.5 expected by
  chance.** That is chance.
- Apparent structure in the output (61 of 62 odd `S3`) is a multiplier
  artifact: `A` odd and `B ≡ 4 (mod 8)` force `S3 = (3X+4) mod 8`.

So `r1019.families.classify` has **no `else: return AFFINE` branch**.
Unrecognised variable rows return `UNRESOLVED_VARIABLE_ROUTE`.

## Defects found in the shipped pack

**D-19B-01 — `src/bridge_family_sorter.py` disagrees with its own
ledger on 77 of 94 rows.** Its `classify()` tests the lexical `16`
header *before* the 30-bit test, so 60+ rows — including direct
SurfaceWords like `165829473` — are routed into the affine lane. Running
it would have produced exactly the universal-bridge error this pack
forbids. **The ledger CSV is authoritative; the script is not. Do not
run it.** `r1019/families.py` fixes the precedence.

**D-19B-02 — wire/target labels swapped on 4 rows.** The ledger files
`1643789253` and `1672875493` as `KNOWN_SAME_LOCATION_CANONICAL_TARGET`,
but those are the 10-digit **transport wires** (≥ 2^30). The canonical
targets are `165876523` and `168930443`, filed as
`DIRECT_OR_CANONICAL_30BIT_SURFACEWORD`. This is the TransportWire /
SurfaceWord type split again, inverted.

**D-19B-03 — Avebury filed under `worked_examples`.** `1647012173`
carries a real structural relation, so the append test outranks the
group label in this implementation.

## Agreement

83 of 92 rows match the curated ledger. All 9 differences are
deliberate: 5 are rows the ledger itself marks
`DIAGNOSTIC_WEAK_GENERALITY` where this implementation refuses an affine
label outright, and 4 are D-19B-02.

## What this does not license

The hard independent anchor count remains **3**. The 17
projection-derived rows are internal-consistency only and are never
validation. The ≥8-independent-anchor requirement before the codec
search becomes discriminating is unchanged. Montréal
(`165879243` / `168500683` / `168729543`) stays quarantined and
`assert_clean` gates every scoring path.

NO_TAG · NO_PUSH · PUBLICATION_HOLD
