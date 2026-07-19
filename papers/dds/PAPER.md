# Two Notions of Phase Closure in Multi-Tone Direct Digital Synthesis, and Where They Disagree

**Status: reframed after prior-art review. The originally proposed
contribution — a closed form for multi-tone common closure — is
already published. What follows is what survived.**

## Abstract

Direct digital synthesis admits two distinct and non-equivalent
notions of when a set of tones "returns to its starting phase": the
closure of the ideal continuous phase ramps, and the recurrence of the
phase accumulator to state zero. The literature's grand repetition
rate is the second. Practitioners reasoning about phase-coherent
multi-tone measurement frequently want the first.

We show the two coincide if and only if the greatest common divisor of
the tuning words is a power of two, and otherwise differ by exactly
its odd part:

> **T_accumulator / T_continuous = odd_part(gcd(K₁,…,K_m)).**

The continuous figure is therefore never pessimistic and can overstate
closure quality without bound. We give a worked case where it is
optimistic by a factor of 3.

## 1. Prior art, stated first

The multi-tone closure formula itself is **not new**, and we say so
before deriving it.

Writing the synthesis quantum δ = *f_r*/2^*N* = *p*/*q* in lowest
terms, the common closure of the continuous ramps is
*T* = *q*/(*p*·gcd(*K_i*)). This is algebraically identical to
*T* = 1/gcd(*f_i*) — the textbook fundamental period of a sum of
commensurate sinusoids — rewritten on the DDS grid. It is published:

- **Nicholas & Samueli (1987)** established the number-theoretic
  accumulator-period analysis; the single-tone grand repetition rate
  GRR = 2^*N*/gcd(FTW, 2^*N*) is a named, standard quantity restated
  in Cordesses (*IEEE Signal Processing Magazine*, 2004) and in the
  Analog Devices DDS tutorials.
- **Hwang et al.** (*Scientific Reports* 7:14075, 2017) publish the
  multi-frequency GCD closure rule as a design principle for Lissajous
  scanning — choose drive frequencies to maximise their GCD.
- **Fujifilm US12422666B2** (2022) performs exactly this computation
  on DDS tuning words.

Likewise, the observation that a power-of-two reference gives exact
integer tuning words, and that 67.108864 MHz = 2²⁶ is therefore a
preferred clock, is standard engineering practice with its own patent
literature (Bruker US6411093B2; Broadcom EP1357460B1 for the negative
case).

**None of that is claimed here.**

## 2. The discrepancy

The two notions of closure answer different questions.

**Continuous closure** asks when every *reconstructed analog tone* has
completed a whole number of cycles. It is *T* = *q*/(*p·g*) with
*g* = gcd(*K_i*).

**Accumulator closure** asks when the *digital phase accumulator*
returns to state zero. Per tone this is 2^*N*/gcd(*K*, 2^*N*) clock
ticks; for a tone set it is the lcm of those.

These differ because the continuous ramp can reach 2π at a moment
lying *between* clock ticks. The analog phase closes; the accumulator
never lands on zero at that instant.

**Result.** The ratio is exactly the odd part of the gcd:

    T_accumulator / T_continuous = odd_part(gcd(K₁,…,K_m)).

They agree iff gcd(*K_i*) is a power of two. Since odd_part ≥ 1, the
continuous figure is **never pessimistic** — quoting it for a system
whose behaviour depends on accumulator state always overstates closure
quality.

### Worked case

*N* = 32, *f_r* = 100 MHz, tuning words {3, 6, 9}, gcd = 3:

| Notion | Closure |
|---|---|
| continuous | 2²⁴/(3·5⁸) s ≈ 14.3166 s |
| accumulator | 2²⁴/5⁸ s ≈ 42.9497 s |
| ratio | **3** = odd_part(3) |

Verified across gcd ∈ {3, 5, 6, 7, 21, 2¹⁸} — the prediction holds
exactly in every case.

The canonical 100 MHz / {4096, 20480, 40960} Hz example that motivated
this work has gcd(*K*) = 1, and the 2²⁶ Hz example has gcd(*K*) = 2¹⁸.
Both are powers of two, so **both hide the discrepancy entirely** —
which is how it went unnoticed.

## 3. Which notion is correct

It depends on the application, and the choice must be stated:

- **Continuous** is right for a measurement that observes the
  reconstructed analog waveform and cares about relative phase between
  tones.
- **Accumulator** is right for any system that latches, resets,
  synchronises, or compares accumulator state — including
  multi-channel DDS alignment, which is where the GRR is normally
  invoked.

Reporting one where the other governs is an error of up to
odd_part(gcd(*K*)), unbounded in general.

## 4. Secondary observations

These are exposition of known facts, not claims.

**Exactness belongs to the reference, not the resolution.** A tone is
exactly representable iff *f*·2^*N*/*f_r* ∈ ℤ. For *f_r* = 10⁸ =
2⁸·5⁸ and dyadic tones this requires 5⁸ | 2^*k*, which never holds —
no accumulator width helps. Verified for *N* = 8…64.

**Accumulator width trades accuracy against closure.** Widening the
accumulator shrinks δ, improving frequency accuracy, while *q* doubles
and closure lengthens. Over 24→64 bits both effects are structurally
2⁴⁰.

*Honesty note:* an earlier draft reported these as 6.26 × 10¹¹ and
1.10 × 10¹² and presented the near-agreement as notable. That was
overstated. The closure figure is exactly 2⁴⁰; the frequency-error
figure is the *realised* rounding error for three particular tones and
depends on where each falls relative to the grid. There is one
mechanism, not a coincidence between two.

## 5. Errors corrected during this work

Recorded because they are instructive:

1. The degradation factor for the canonical case was stated as
   "exactly 175922". It is 2³⁶/5⁸ = 175921.8604…, and 175922 is the
   *rounded tuning word* — a different quantity. The ratio is the
   unrounded word, so the collision is structural. The error was in
   the direction that looks tidier.
2. A search for an exact dyadic reference returned 2 Hz for a
   40960 Hz tone set: arithmetically valid, physically impossible.
   Exactness constrains only *f*·2^*N*/*f_r* and says nothing about
   whether the tone can be emitted. Now requires a declared
   oversampling floor with Nyquist as a hard minimum.
3. A brute-force validation searched in an order that found *T* = 1
   before *T* = 1/3, and would have "confirmed" a wrong closed form.

## 6. Reproducibility

All closure values are exact rationals (`fractions.Fraction`); no
floating point appears in any closure computation. Implementation:
`r8/dds.py`. Tests: `tests/v51/test_r8_dds.py` (43 tests, no tolerance
on any closure value), including validation of the single-tone
accumulator formula against the published GRR.

## 7. Recommended disposition

Per the prior-art review, the original framing does not support a
research paper and would be rejected on prior art. The
continuous-versus-sampled discrepancy is real, verified, and was not
found in the literature.

Suggested venues, in order: a short correspondence in *IEEE
Transactions on Circuits and Systems II*, or *IEEE Transactions on
UFFC* — both carry the Nicholas/Samueli lineage and take short
number-theoretic DDS notes. Alternatively a technical note in *Review
of Scientific Instruments* if paired with a real instrument.

**The reference-selection rule and the anti-correlation framing are
exposition and should be presented as such.**
