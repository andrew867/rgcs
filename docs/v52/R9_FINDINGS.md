# RGCS v5.2 / R9 — Findings

**Programme status:** `SOFTWARE_VERIFIED_PHYSICAL_UNTESTED`
**Baseline:** v5.1.0 (public)
**Evidence class of everything below:** arithmetic, literature values, and
software. **No measurement was performed by this project.**

---

## Summary

R9 asked one central question:

> Does the source corpus and current physics support a coherent
> hidden-neutral-carrier model, and what measurements would distinguish
> an antineutrino analogy, sterile/right-handed-neutrino physics,
> another hidden sector, an ordinary apparatus effect, or no new
> carrier?

**The answer is that no measurement available to this project
distinguishes any of them, and the reason is more specific than "we
lack equipment".** It is worked out below.

Alongside that, four claims carried in the source material were
examined. Three turned out to be correct arithmetic whose significance
had been overstated; one turned out to be excluded by a measurement
made in 1914. Each is recorded with what survives and what does not,
because "the arithmetic is right and the interpretation is wrong" is a
different result from "this is nonsense", and the difference is worth
keeping.

---

## 1. The hidden neutral carrier (P06, P10)

**Module:** [`r9/carrier.py`](../../r9/carrier.py)

The interesting part of this result is that the rate is **not zero**.

A 100 g quartz crystal under the solar neutrino flux experiences roughly
**1.2 neutrino interactions per year**. Neutrinos are not failing to
interact with the bench. The obstacles are two, and they are ordered:

**First, and binding: there is no readout channel.** A quartz resonator
has no mechanism capable of registering a single sub-keV nuclear recoil.
An interaction that occurs and is never transduced is not a measurement.
This obstacle is prior to any question about rates, and no amount of
integration time addresses it.

**Second, granting a readout that does not exist: the background.** The
same volume passes about 2.1 × 10⁷ cosmic muons per year at sea level.
Signal to background is 5.9 × 10⁻⁸ — roughly one candidate per
17 million muons.

Two caveats that make this weaker than it first looks, both added after
prior-art review:

- The ~1.2/yr figure is a **zero-threshold ceiling**, not an
  expectation. Published solar pp CEvNS rates (~16.6 events/kg·yr in
  germanium) are quoted the same way. Recoils here are sub-keV; at any
  threshold a quartz resonator could reach, the rate above threshold is
  consistent with zero.
- The miniaturisation argument is not ours. Freedman (1974) predicted
  coherent elastic neutrino–nucleus scattering, and Drukier & Stodolsky
  (1984) is the canonical proposal that coherence permits much smaller
  detectors.

### The barrier is readout, not mass (correction)

The first version of this analysis compared the bench against
Super-Kamiokande and concluded the gap was **mass** — a factor of 10⁸.
That framing is wrong, and wrong in a useful direction:

| Detector | Mass | Threshold | Status |
|---|---|---|---|
| NUCLEUS | **10 g** | ~20 eV | commissioning; no detection yet |
| CONUS+ | ~3 kg | ~160 eV | first reactor CEvNS, 3.7σ (2025) |
| COHERENT | 14.6 kg | ~4.8 keV | first CEvNS observation, 6.7σ (2017) |

**NUCLEUS runs a 10 g target — one tenth of the bench crystal.** Mass is
not what the bench lacks. What NUCLEUS has is a readout channel: a
~10 mK cryogenic calorimeter with a ~20 eV threshold, plus depth,
shielding and an active veto. The field solved the small-detector
problem by *engineering transduction* — which is precisely the obstacle
identified as binding above.

The corrected conclusion is stronger than the original: **the bench is
not short of mass, it is short of a way to notice.**

### The model is validated against a working experiment

A feasibility model that refuses everything proves nothing. The same
arithmetic applied to Super-Kamiokande's scale returns
`CONVENTIONALLY_MEASURABLE`, which is correct — Super-K has detected
solar neutrinos since 1996. This is pinned by
`test_model_reproduces_a_working_experiment`, and it exists because the
first version of the module failed it (see R9-D-001 below).

### Hypothesis ordering

The hypothesis ladder is deliberately **mundane first**:

1. `ORDINARY_APPARATUS_MODE`
2. `INSTRUMENTATION_ARTEFACT`
3. `ENVIRONMENTAL_COUPLING`
4. `NO_NEW_CARRIER`
5. `ACTIVE_ANTINEUTRINO`
6. `STERILE_NEUTRINO`
7. `OTHER_HIDDEN_SECTOR`

An exotic carrier is not a candidate explanation until sham drive, empty
mount, environmental logging and an independent measurement chain have
bounded the ordinary ones. That ordering is enforced by test.

**What is reachable:** the ordinary hypotheses are fully testable on a
bench, and cheaply. **What is not:** everything from `ACTIVE_ANTINEUTRINO`
onward.

---

## 2. The omitted antineutrino (P05)

**Module:** [`r9/betadecay.py`](../../r9/betadecay.py)

The source material treats the antineutrino in neutron beta decay as
something that can be left out. It cannot, and the reason is not a
matter of preference.

Q = m_n − m_p − m_e = **0.782333 MeV** (literature: 0.782 MeV).

Omitting the antineutrino turns a three-body decay into a two-body
decay. Two-body kinematics fix the electron energy exactly, so the
omitted account predicts a **monoenergetic** electron. The measured
spectrum is **continuous**. That is the discrepancy Pauli resolved by
postulating the neutrino in 1930, and it remains the cleanest single
argument.

Four conservation laws each exclude the omitted account **independently**
— energy, momentum, angular momentum, lepton number. Any one is
sufficient; they are not one argument restated four times.

### What this does not say

It does not say the antineutrino is well understood. Neutrino masses,
the mass ordering, whether neutrinos are Majorana, and the
beam-versus-bottle neutron lifetime discrepancy (~4 s, ~4σ) are all
genuinely open. *Required by conservation* and *fully characterised* are
different statements, and the module carries both.

---

## 3. The CW vectors (P08)

**Module:** [`r9/cwdecode.py`](../../r9/cwdecode.py)

Five 12-digit values received as CW vectors from the omega region.
R7 analysed them by converting to binary and found zero informative
bits. The fair objection is that the bit conversion was itself the wrong
first move — that a binary frame could destroy decimal structure.

So R9 ran the analysis in the opposite order: **segments, then divisors,
then bits last**, with the order and the test register frozen before any
result was read.

**The bit frame was not the problem.** No content structure survives in
any framing:

| Test | Observed | Null mean | p |
|---|---|---|---|
| `BAND_CLUSTERING` | span 2,109,794 | 6.0 × 10¹¹ | **0.00005** |
| `SEGMENT_RESIDUAL_PREFIX` | 5 digits | 4.878 | 0.859 |
| `SEGMENT_COMMON_SUFFIX` | 0 | 0.0001 | 1.000 |
| `SEGMENT_DIGIT_PAIR_REPEAT` | 2 | 2.036 | 0.930 |
| `DIVISOR_GLOBAL_GCD` | 1 | 1.043 | 1.000 |
| `DIVISOR_PAIRWISE_GCD` | 39 | 105.9 | 0.143 |
| `DIVISOR_SMALL_PRIME_EXCESS` | 2.00 | 1.337 | 0.166 |
| `BIT_INFORMATIVE_WIDTH` | 0 | 0 | 1.000 |

The gcd of all five is 1 and their factorisations share nothing.

### Band structure is real, and is reported separately

One finding does survive: the values are **strongly clustered**,
occupying 2.1 × 10⁶ of a 9 × 10¹¹ space (p = 5 × 10⁻⁵). That is a real
property of the source. It is a fact about the **range they were drawn
from**, not about anything encoded in them — unremarkable if these are
frequencies, timestamps or counter readings — and it is reported under a
separate verdict so a clustering result can never be presented as a
decoding result.

The shared leading digits `16287` are **entirely explained by the
clustering** and have nothing left over (p = 0.86 against a span-matched
null).

### What this does not say

It does not say the vectors are meaningless or randomly generated. Five
values is a very small sample, and this analysis would miss any encoding
that is keyed, compressed, or defined against a reference these tests do
not contain. The honest statement is that **no structure is recoverable
by these means from these five values** — not that none exists.

---

## 4. The octave, the 1↔8 bridge, and "infinite" (P07)

**Module:** [`r9/octave.py`](../../r9/octave.py)

Three claims that look like one. Separating them is the contribution.

**The octave is exact.** 2:1, a genuine equivalence relation whose
quotient is a circle. Computed in `Fraction` throughout, so nothing
rounds at a claim boundary.

**The 1↔8 bridge is an off-by-one.** The diatonic scale has **seven**
degrees; seven steps summing to twelve semitones return you to the
starting pitch class. Calling the arrival "8" counts both endpoints —
the same inclusive counting that named the octave. Degree 8 is not an
eighth element or a hidden state. It is degree 1, one octave up, being
named twice. No mechanism is needed and none is implied.

**"Infinite" is true as arithmetic and false as physics.** Nothing bounds
the chain on the number line. Physically, between one cycle per age of
the universe and the Planck frequency there is room for about **202
octaves**. Large, and finite.

Both halves matter. *"It's just numerology"* is as wrong as *"it's
infinite"*: the relation really is exact and really does extend without
limit as arithmetic, and there is still no infinite physical series to
reach or descend from.

**Not licensed:** treating "source" or "infinite octave" as a place, a
state, or an energy reservoir. An unbounded sequence is not a
destination, and no measurement here could tell the two apart.

---

## 5. The vortex grammar (P09)

**Module:** [`r9/vortex.py`](../../r9/vortex.py)

The doubling cycle on digital roots — 1, 2, 4, 8, 7, 5, with 3, 6 and 9
outside it — is real, and every step of it is correct arithmetic. The
module reproduces it faithfully, and checks the closed form against
naive repeated digit-summing rather than asserting they agree.

**What it is:** the digital root in base *b* is *n* mod (*b*−1), so base
10 is mod 9, and repeated doubling is the cyclic subgroup generated by 2
in (ℤ/9ℤ)\*. Its order is 6 — exactly the cycle length. 3 and 6 are
unreachable because gcd(3,9) = gcd(6,9) = 3, so neither is a unit; 9 ≡ 0.

**The decisive test is base generality.** If 3-6-9 were fundamental it
would not depend on how many fingers we happen to have:

| Base | Modulus | Cycle | Excluded |
|---|---|---|---|
| 6 | 5 | 1,2,4,3 | — |
| 8 | 7 | 1,2,4 | 3, 5, 6 |
| 10 | 9 | 1,2,4,8,7,5 | 3, 6 |
| **12** | **11** | **1,2,4,8,5,10,9,7,3,6** | **nothing** |
| 16 | 15 | 1,2,4,8 | ten of fourteen |

**In base 12 nothing is excluded at all.** There is no trinity to find.

### Two exclusion mechanisms, not one (correction)

The first version of this analysis said base 12 excludes nothing
"because 2 is a primitive root mod 11". Prior-art review objected that
the real reason is that 11 is prime. **Both statements are wrong**, and
base 8 settles it: 7 *is* prime, and 3, 5, 6 are still excluded.

There are two distinct mechanisms:

1. **Non-units** — gcd(a, m) > 1, so a is not in the multiplicative
   group at all. This is why 3 and 6 are excluded mod 9.
2. **Units outside the orbit** — a is a unit but not in ⟨2⟩. This is why
   3, 5, 6 are excluded mod 7.

| Base | Modulus | Prime? | 2 primitive root? | Excluded as non-units | Excluded as units outside ⟨2⟩ |
|---|---|---|---|---|---|
| 8 | 7 | yes | no | — | 3, 5, 6 |
| 10 | 9 | no | yes | 3, 6 | — |
| 12 | 11 | yes | yes | — | — |

Base 10 and base 8 exclude residues for **completely different reasons**.
An empty exclusion set requires *both* a prime modulus (no non-units)
*and* 2 a primitive root (the orbit covers every unit). Base 12 satisfies
both; base 8 only the first.

The exclusion in base 10 is a property of 9 = 10−1 being composite, which
is a property of our notation.

**What survives:** the arithmetic, completely. Digital roots, cyclic
subgroups and multiplicative order are real tools and this is a correct
instance of them.
**What does not:** any claim that 3, 6 and 9 are physically or
cosmologically privileged. Nature does not know what base we write in.

---

## Defects found and fixed during R9

### R9-D-001 — feasibility model refuted a working experiment

The first version of `carrier.py` applied **sea-level muon flux to every
target**, including Super-Kamiokande. It therefore reported Super-K as
`REFUSED_BY_ARITHMETIC` — a detector that has been seeing solar
neutrinos since 1996.

A feasibility model that refutes a working experiment is wrong. The
omission was overburden: deep sites suppress muons by five to six orders
of magnitude, which is precisely why they are deep. Fixed by adding
`overburden_mwe` and a `MUON_ATTENUATION` table, and pinned by a test
requiring the model to reproduce Super-K.

This is the R8.1 detector lesson applied to a physics model: **a model
that refuses everything proves nothing.**

### R9-D-002 — a null conditioned on the data it was testing

The first version of `cwdecode.py` measured "range-forced" digit
agreement against the **observed min and max**. But the min and max *are
two of the five values*, so their common prefix is always at least the
common prefix of all five. The residual could never be positive. **The
test could not fire.**

Worse, the matched null was drawn from `[min, max]` too, so it
reproduced the same forced digits by construction — null mean 5.027
against observed 5. It read as a careful null result and was a tautology.

**A baseline conditioned on the data cannot test the data.** Both the
baseline and the null are now anchored to a 12-digit band declared
independently of the observations, and the conflated test split into two
honest ones (clustering, and residual prefix given clustering). The
residual test is now checked for *power* — it must fire on planted
structure — which the original never was.

---

### R9-D-003 — the anti-stale guard had a hole its own shape

R8-D-006 added a test requiring every shipped package to appear in
`SOURCE_ROOTS`, so a stale build could not pass the freshness check.
It detected packages by the presence of `__init__.py`.

`r9` had no `__init__.py`. Neither did `r8`, as shipped in v5.1.0. Both
import perfectly well as PEP 420 namespace packages — and both were
invisible to the guard written specifically to catch this. Rewritten to
treat any directory of `.py` files as a package. It immediately found
`r9` and one more directory.

### R9-D-004 — three public releases shipped without their research code

Found by the R9-D-003 fix, and the worse of the two.

`SOURCE_ROOTS` governs the build-freshness hash. The packaging `include`
list governs what `pip install` puts on disk. **They are different lists,
and nothing was checking that they agreed.**

They did not agree. The `include` list stopped at `r4`. So
`pip install` of **v4.9.0, v5.0.0 and v5.1.0** installed **none of r6, r7
or r8** — the headline research packages of those very releases.

Working from a clone hid this completely: `pythonpath = ["."]` makes the
source tree importable whether or not packaging agrees, so every test and
every local run passed. Fixed, and pinned by a test that compares the two
lists directly rather than trusting either.

---

## Prior art

An adversarial prior-art review was run against every headline claim.
**Five for five came back established. Nothing in R9 is novel.**

| Claim | Verdict | Key prior art |
|---|---|---|
| Vortex cycle = ⟨2⟩ in (ℤ/9ℤ)\*, base-dependent | ESTABLISHED | Casting out nines (centuries); RationalWiki; Chu-Carroll (2018) |
| ~202 octaves, universe to Planck | ESTABLISHED | Camber (2017), same figure by the same method; Cousto (1978) for the method |
| Continuous β spectrum ⇒ third body | ESTABLISHED | Chadwick 1914; Ellis & Wooster 1927; Pauli 1930; Fermi 1934 |
| 100 g quartz ν feasibility | ESTABLISHED | Freedman 1974; Drukier & Stodolsky 1984; NUCLEUS; CONUS+; COHERENT |
| Preregistration + matched nulls + multiplicity | ESTABLISHED | McKay et al., *Statistical Science* 14(2), 1999 — the definitive template |

This is consistent with every prior review in this programme's history
(R6, R7, R8.1), and the honest framing for R9 is **replication and
correct exposition, not discovery**. Where this work has value it is in
stating the mechanisms precisely — for instance separating the two
exclusion mechanisms in §5, which the popular critiques generally do not
do, and which the review itself got wrong.

---

## Method notes

Every claim-bearing analysis in R9 carries:

- **Preregistration.** The test register is frozen before results are
  read, and `report()` refuses to publish a finding not in it. With five
  values and free choice of segmentation, divisor and threshold,
  something always looks meaningful.
- **Matched nulls**, seeded and reproducible. An unseeded null is not a
  null anyone can check.
- **Multiplicity correction** (Bonferroni across the full register), with
  the null running the same multi-way scan the analysis does.
- **Power checks.** A test that cannot fail is not a test, and each is
  shown to fire on planted structure.
- **Refusal functions.** Every module exposes an explicit refusal for the
  claim it does *not* license.

---

## What R9 does not claim

- No physical measurement was performed.
- No carrier was detected, and none was searched for; this project owns
  no particle detector.
- The CW vectors are **not decoded**.
- No medical, biological, or consciousness claim of any kind.
- Nothing here establishes that the source material's interpretations are
  correct. Where its arithmetic is correct, that is recorded. Where its
  significance claims fail, that is recorded too.

Source attribution for the CW vectors is kept at region granularity —
*from the omega region* — and no analysis step depends on provenance.
