# Numerology and look-elsewhere audit (Agent C04)

Coverage: **A13, F001–F052**. Gate: **G11**.
Implementation: [`rscs2_core/frequency_keys.py`](../../rscs2_core/frequency_keys.py).

## The problem this document exists to prevent

Given enough candidate numbers and enough targets, **something will
match**. That is arithmetic, not physics. This audit quantifies how
much matching to expect by chance, so a coincidence cannot be promoted
by enthusiasm.

## The null model

Under a uniform null on a band of width W, a single candidate lands
within ±tol of any of K targets with probability

    p ≈ K · 2·tol / W

and with M candidates tried, the expected number of chance hits is

    E = M · K · 2·tol / W

`coincidence_significance()` returns `expected_chance_hits` and marks
`significant: false` whenever E ≥ 0.05. **A match with E ≳ 1 is not
evidence of anything.**

Worked example (tested): a candidate matching one target to ±5 Hz in a
10 kHz band after trying 5000 candidates gives E = 5.0 — five chance
hits expected. The registry reports `within_tolerance: true` and
`significant: false` simultaneously, which is the honest pairing.

## Exact misses are recorded as misses

**21 × 195 = 4095 Hz. The target is 4096 Hz. It misses by 1 Hz.**

The registry records the separation as 1.0 Hz and `within_tolerance:
false` at a 0.5 Hz tolerance. It is not rounded, not called "essentially
4096", and not promoted. This is the single most instructive entry in
the F-registry: the arithmetic is *almost* beautiful, and almost is a
miss.

## Kinds, so a number cannot change category

The frequency schema forces every entry into exactly one kind:

| Kind | Example | Rule |
|---|---|---|
| `exact_physical_frequency` | a computed modal frequency | has a physical equation |
| `arithmetic_motif` | 4096 = 2¹² framing from 8 Hz | arithmetic only |
| `source_label` | 465/787/880 Hz body labels | source vocabulary; **no medical claim** |
| `harmonic_relation` | 2:1, 3:2 ratios | exact algebra |
| `timing_inverse` | 46 ms ↔ 21.74 Hz | 1/T |
| `dimensionless_ratio` | φ, √3, √5, 2.45 GHz ratio | no units |
| `angle_derived_numeric_motif` | 51.843° chains | **degrees are not hertz** |
| `non_frequency_value` | 454 Ω | resistance, not frequency |

## Dimensional violations that are refused

- **Angles do not become hertz.** A unitless angle multiplier cannot
  acquire hertz without a declared physical equation. 51.843 × 60 is a
  number, not a frequency (ORPHAN-011 keeps the angle conventions
  distinct as *angles*).
- **454 Ω is not a frequency.** Registered as
  `non_frequency_value` so it can never enter the harmonic graph
  (ORPHAN-010).
- **2.45 GHz is not a water resonance.** It is an ISM band chosen by
  regulation. The widespread "microwave ovens tune to water's
  resonance" claim is false; it is recorded as an arithmetic ratio
  motif with the correction attached (ORPHAN-012).

## Body-mapped labels carry no medical claim

465/787/880 Hz and similar are retained as **source labels**. The C04
prompt forbids treating chakra/body mappings as medical facts. This
programme makes no medical claim of any kind, and these entries exist
to preserve the source vocabulary, not to endorse it (ORPHAN-020).

## Registry contents

All F001–F052, including: the 4096 ninth-octave framing from 8 Hz;
20.48/40.96 Hz bridges; 4096/4160/4225 tuner families; 1496/587/644;
210.42; 20.6061; 7/9/14/21/42 and multiples of 9; the progressive
10..550 sequence; 46 ms, 60π/4096, 192 cycles, φ⁸, 552 ms, 2260.992,
1507.328; the density ladder; φ, √φ, √3, √5, 60/72° relations; and the
7.6 Hz φ-EEG lead (ORPHAN-013).

Each entry carries value, unit, exact formula, source tier, intended
channel, dimensional validity, physical hypothesis, controls, expected
artifact, and failure condition.

## Neighbour controls

Any protocol dispatching a "special" frequency must also dispatch its
neighbours. A frequency that only works at its own value, and not
0.5% away, is making a claim; one that works equally at its neighbours
is describing the instrument. See
[TIMING_FAMILY_AUDIT.md](TIMING_FAMILY_AUDIT.md).

## Boundary

Do not call a close match a resonance. No optimizer, visual
resemblance, source repetition, or preference may upgrade an evidence
class — and in this registry, none can: the status field is set by the
kind and the null model, not by the interest of the number.
