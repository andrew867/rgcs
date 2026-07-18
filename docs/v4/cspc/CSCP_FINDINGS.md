# RGCS v4.6 — Crystalline Spacetime Coordinate Program: findings

**Status: SOFTWARE_VERIFIED, PHYSICAL_UNTESTED.** No apparatus was
built, no data was collected, and no physical hypothesis in this
programme is supported. Every number below is arithmetic, an analytic
model, or a numerical simulation. The programme's own candidate
frequencies are not evidence that any specimen prefers them.

## The originating question

> **RQ-CSPC-001** — Can crystalline resonators provide a physically
> meaningful bridge between stable phase, cross-domain frequency
> conversion, temporal order, spacetime measurement, and the much
> stronger idea commonly described as space-time travel?

**Answer as far as this programme can take it: no bridge to travel is
supported, and one genuine capability survives — metrology.** The
detail is below, including the parts that went against the hypothesis.

## What the source said, and what is actually true

| source claim | status | correction |
|---|---|---|
| "2.45 GHz is the frequency of water" | **CORRECTED** | Water's microwave response is broad *dipolar relaxation*, not resonance. A single-Debye model puts the loss maximum near **19.2 GHz** — 7.9× above the ISM band, where 2.45 GHz carries only ~25% of peak loss. 2.45 GHz was chosen for penetration depth, component cost and spectrum allocation. |
| "0.0356521923094988 is the fractal relationship" | **CORRECTED** | It retains **hertz**. It is `2.45e9 / 2^36` — the least-significant step of a 36-bit accumulator clocked at 2.45 GHz, i.e. a frequency *resolution*. |
| "the 11th powers-of-eight level" described as an 11th octave | **CORRECTED** | `8^11 = 2^33`: thirty-three octaves, not eleven. |
| "4096 and 64 are linked to a 64-tetrahedron grid" | **UNDERDETERMINED** | The phrase does not say whether 64 counts cells or vertices, nor which geometry. Four readings are registered and analysed; none is promoted. |
| "4096 is a fractal core measure of visible light" | **DERIVED_ARITHMETIC** | `4096 × 2^37 = 2^49 = 562 949 953 421 312 Hz` exactly, λ = 532.538383168912…nm. The arithmetic is exact and supplies **no** coupling mechanism. |

## Findings

### 1. Precision does not survive the input

`2.45e9 / 8^9` is **exactly** 18.25392246246337890625 Hz as arithmetic
and **18.3 Hz** as physics. The input 2.45 GHz is nominal at three
significant figures, and no amount of exact division manufactures more.
Quoting sixteen digits as a physical fact is an overclaim; the code
reports both numbers and flags the overclaim automatically.

### 2. The simplicity metric measures human convention, not nature

A frozen, hash-pinned metric (rational complexity of the exact ratio)
was applied to five corpora against four references, with
Holm–Bonferroni and Benjamini–Hochberg correction over the whole
family. Everything that survives correction is either **constructed
from the reference it is scored against** or is **a table of
human-chosen round numbers**:

- just intonation (small-integer ratios) — detected, as it must be;
- equal temperament (irrational by construction) — **not detected**
  (p ≈ 1.0), exactly as it must be;
- ISM bands — strongly "simple", because regulators picked
  harmonically related round numbers (13.56 / 27.12 / 40.68 MHz);
- quartz clock crystals — "simple" because they are binary by
  manufacture;
- **the programme's own candidates — "simple", flagged CIRCULAR**,
  because they were built from powers of two and eight relative to
  2.45 GHz and 4096.

This is a null result for the interesting version of the hypothesis.

### 3. 4096 from "64 tetrahedra" is a fact about counting

4096 = 64². Any 64-element set has 4096 ordered pairs, so the
"relationship" is available in every 64-object structure, including
unstructured ones. All four construction families demonstrate it. No
labelling creates a preferred 4096 relationship.

Across the four families, graph spectra are relabeling-invariant, and
compared with degree-matched random graphs the geometric lattices are
unusually *poorly* connected (z −3.1 to −16.1) — which is generic for
structured lattices. The hypercube is not unusual at all (p = 0.39).
No construction shows special synchronizability.

### 4. The elegant phase closure does not survive real hardware —
### but a clock choice recovers it

On a 100 MHz reference with a 32-bit accumulator, none of
4096 / 20480 / 40960 Hz is exactly representable, and the common
phase-closure window collapses from the ideal **1/4096 s** to
**16777216/390625 s ≈ 42.9 s** — a factor of ~175 000. The tidy closure
exists only in ideal arithmetic.

On a **binary reference clock** (2²⁶ Hz = 67.108864 MHz, a stock part,
also 32.768 kHz × 2¹¹) every target is exactly representable and the
ideal window returns. **Exactness is an engineering choice of
oscillator, not a property of nature.** This is the programme's most
practically useful output.

### 5. Spacetime: one real capability, one decisive refutation

The weak-field clock model is validated against two published
measurements — Pound–Rebka (computed 2.4551e-15 vs published 2.45e-15)
and the GPS correction (+45.65 gravitational, −7.21 velocity, **net
+38.44 µs/day** vs published +38.5).

- **Capability (real):** resonators are metric *instruments*. Quartz at
  1e-12 fractional stability resolves ~9 km of height; an optical clock
  at 1e-18 resolves ~9 mm. Clock-based geodesy is genuine.
- **Refutation (quantitative):** 100 W for one hour is 3.6e5 J →
  equivalent mass 4.0e-12 kg → Schwarzschild radius **5.9e-39 m**. That
  is **23 orders of magnitude below a proton radius** and smaller than
  the Planck length itself. Earth's own r_s is ~8.9 mm. No arrangement
  of laboratory energy alters a worldline measurably.

Sensing the metric is not controlling it. A thermometer does not heat
the room.

### 6. Temporal order is not travel

A subharmonic response in a driven nonlinear oscillator is textbook
parametric behaviour; the "time crystal" label additionally requires
many-body rigidity, and even a genuine time-crystal candidate makes no
travel claim — the literature itself does not. All five
travel-adjacent claims are **UNSUPPORTED**, each stating the specific
evidence that would change its status. None of that evidence exists.

## Defects found by running the analysis honestly

| id | defect | effect |
|----|--------|--------|
| CSPC-D-001 | source-hash guard hashed raw bytes, so a Windows checkout (CRLF) reported a spurious mismatch | a fresh binary would fail `--build-info`; fixed by LF normalisation |
| CSPC-D-002 | local `main` was stale at v4.4.0 (`push origin v4-dev:main` updates only the remote ref) | branching "from main" produced a v4.4.0 tree; caught before any work landed |
| CSPC-D-003 | statistical nulls matched magnitude but not arithmetic granularity | **every** corpus, including the negative control, scored "simpler than chance" to −42 SD; fixing it inverted the headline result |
| CSPC-D-004 | controls mislabelled (equal temperament as a positive control; ISM as a negative one) | replaced with a true positive control; ISM reclassified as a real detection of human convention |
| CSPC-D-005 | the mandated 20.48 Hz neighbour control was missing from the experiment recipe | caught by test; control set corrected |

## What would change these conclusions

Bench evidence, and only bench evidence: a calibrated measurement with
apparatus provenance, neighbour controls, blinding, a preregistered
stopping rule, and independent replication. The programme ships the
preregistrations; it has run none of them.
