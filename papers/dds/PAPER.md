# Exact Common-Phase Closure in Multi-Tone Direct Digital Synthesis

**Draft — novelty positioning pending prior-art review.**

## Abstract

For an *N*-bit direct digital synthesiser driven by reference
frequency *f_r*, we give a closed form for the least interval over
which a set of synthesised tones returns simultaneously to its
starting phase. Writing the synthesis quantum δ = *f_r*/2^*N* = *p*/*q*
in lowest terms, the common phase-closure interval for integer tuning
words *K₁…K_m* is

> **T = q / (p · gcd(K₁,…,K_m)).**

Two consequences follow. First, exact closure is a property of the
*reference frequency*, not of accumulator resolution: a decimal
reference cannot represent a dyadic tone set exactly at any width,
because no power of two cancels a factor of 5. Second, and less
obviously, accumulator width and phase closure are **anti-correlated**
— widening the accumulator improves frequency accuracy geometrically
while degrading common closure geometrically. A designer optimising
the specification datasheets quote is degrading the one a
phase-coherent multi-tone instrument depends on.

We give the worked case of a 100 MHz reference with a 32-bit
accumulator and tones {4096, 20480, 40960} Hz, where an ideal closure
of 1/4096 s becomes 2²⁴/5⁸ = 42.94967296 s, and show that a *slower*
2²⁶ Hz (67.108864 MHz) reference restores exact closure.

## 1. Setup

An *N*-bit phase accumulator with integer tuning word *K* driven at
*f_r* emits

    f = K · f_r / 2^N.

Every realisable output is therefore an integer multiple of the
**synthesis quantum**

    δ = f_r / 2^N,

and every question about multi-tone phase closure is a question about
δ, not about the DAC, the reconstruction filter, or the phase noise.

We take "closure" to mean the least positive *T* such that every tone
completes a whole number of cycles: *f_i·T* ∈ ℤ for all *i*. At that
instant the whole tone set is back in its initial phase relationship.

## 2. Theorem

**Theorem.** Write δ = *p*/*q* in lowest terms. For tuning words
*K₁…K_m* the realised tones are *f_i* = *K_i p/q*, and the least
positive *T* with *f_i T* ∈ ℤ for all *i* is

    T = q / (p · g),   g = gcd(K₁,…,K_m).

*Proof.* *f_i T* ∈ ℤ means *K_i p T / q* ∈ ℤ. Write *K_i* = *g k_i*
with gcd(*k_i*) = 1. Every *f_i* is then a multiple of *gp/q*, and
because the *k_i* are collectively coprime, *gp/q* is the largest such
common divisor — the tone set generates exactly the lattice (*gp/q*)ℤ.
*T* closes the lattice iff *T* is a multiple of *q/(gp)*, and the
least positive such value is *q/(gp)*. Since *p/q* is in lowest terms,
gcd(*p*,*q*) = 1 and no further cancellation occurs. ∎

The result is computed in closed form. Brute-force phase stepping over
the canonical case below would visit 4.3 × 10⁹ accumulator states.

### 2.1 Corollary — exactness belongs to the reference

A requested tone *f* is exactly representable iff *f·2^N/f_r* ∈ ℤ.
For *f_r* = 10⁸ = 2⁸·5⁸ and dyadic *f*, this requires 5⁸ | 2^k, which
never holds. **No accumulator width recovers exactness.** Verified for
*N* = 8…64.

### 2.2 Corollary — the degradation factor

    T_q / T_ideal = W_fund / g,

where *W_fund* is the **unrounded** tuning word of the ideal
fundamental. This explains an otherwise puzzling near-collision in the
worked case: the ratio is 2³⁶/5⁸ = 175921.8604…, while the tuning word
for 4096 Hz is 175922. They are not coincidentally close — the ratio
*is* the unrounded word, and the word is its rounding. Reporting the
ratio as the integer 175922 is wrong, and wrong in the direction that
looks tidier.

### 2.3 Corollary — accuracy and closure are anti-correlated

Widening the accumulator halves δ, so realised tones land closer to
requested ones and frequency error falls geometrically. But *q*
doubles with every bit while the tuning words remain collectively
coprime, so *T* = *q*/(*p·g*) grows geometrically.

| *N* | max frequency error (Hz) | closure ratio |
|---:|---:|---:|
| 24 | 1.161 | 687.2 |
| 32 | 9.210 × 10⁻³ | 1.759 × 10⁵ |
| 40 | 3.352 × 10⁻⁵ | 4.504 × 10⁷ |
| 48 | 1.216 × 10⁻⁷ | 1.153 × 10¹⁰ |
| 56 | 6.547 × 10⁻¹⁰ | 2.951 × 10¹² |
| 64 | 1.854 × 10⁻¹² | 7.556 × 10¹⁴ |

Across 24→64 bits, frequency error improves by 6.26 × 10¹¹ while
closure degrades by 1.10 × 10¹² — near-perfectly reciprocal.

This is the practical point of the paper. Frequency resolution is
quoted on every datasheet; multi-tone phase closure is quoted on none.
Optimising the first degrades the second.

## 3. Worked case

*N* = 32, *f_r* = 100 MHz, ℱ = {4096, 20480, 40960} Hz.

- δ = 5⁸/2²⁴ Hz
- tuning words (rounded): 175922, 879609, 1759219
- none exactly representable
- ideal closure: 1/4096 s
- realised closure: **2²⁴/5⁸ s = 42.94967296 s**
- degradation: 2³⁶/5⁸ ≈ 175921.86×

With *f_r* = 2²⁶ Hz = 67.108864 MHz — a stock part, and *slower* than
100 MHz:

- δ = 1/2⁶ Hz
- tuning words: 262144, 1310720, 2621440, all exact
- closure: **1/4096 s, ideal recovered**
- frequency error: exactly zero

The smallest dyadic reference satisfying a 10× oversampling floor is
2¹⁹ = 524.288 kHz; 2²⁶ is the practical choice with ample headroom.

## 4. What this is not

The result concerns **exact rational closure only**. It says nothing
about, and must not be confused with:

- phase truncation spurs (the accumulator's low bits driving the
  phase-to-amplitude map);
- DAC quantisation, images, and harmonic distortion;
- reference phase noise and jitter;
- analogue reconstruction;
- the distinction between requested and realised tone sets, which the
  analysis makes explicit but does not eliminate.

A binary-friendly reference preserves exact closure without being
faster and without improving any of the above.

## 5. Reproducibility

All values are computed with exact rational arithmetic
(`fractions.Fraction`); no floating point appears in any closure
computation. A float implementation agrees to ten digits and hides
the effect entirely — which is the failure mode this paper is about.

Implementation: `r8/dds.py`. Tests: `tests/v51/test_r8_dds.py`
(33 tests, no tolerance on any closure value). The theorem is
additionally validated against brute-force enumeration on a small
case.

## 6. Novelty statement

*To be completed from the prior-art review. The relevant question is
whether the multi-tone gcd result, as distinct from the well-known
single-tone accumulator rollover ("grand repetition rate"), is already
published — and whether the anti-correlation corollary is. If the core
result is known, the surviving contribution is the reference-selection
design rule and the anti-correlation framing; if that is known too,
this becomes a technical note.*

**Standing instruction: no novelty claim is retained that the review
does not support.**
