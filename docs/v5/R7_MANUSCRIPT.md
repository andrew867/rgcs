# RGCS v5.0 R7 — Results

**Root Reference, CW Vector Decoder, Differential Clock Link,
Interferometric Crystal Alignment, Directional Field Geometry,
Falsifiable Metric Challenge, and Open-Legacy Decision**

Software implemented. Physically untested. No oscillator pair has been
compared, no crystal aligned or excited, no field mapped, no force
measured. Publication path: **`PRIVATE_RC`** — nothing new published.

---

## 1. The result that subsumes the others

R7 was asked, among other things, to produce a falsifiable metric
prediction. It produced one, and the prediction is that **nothing
this apparatus can do is detectable**.

The chain is `u_a(t) → T_μν → g_μν`, and the first link is energy.
Whatever the apparatus does electrically, elastically, acoustically or
optically, its gravitational signature is set by `E/c²`.

| Configuration | Energy | Equivalent mass | Clock shift | Gap to best optical clock |
|---|---:|---:|---:|---:|
| Hand-held crystal | 1 µJ | 1.1e-23 kg | 8.3e-50 | **30.1 decades** |
| Bench coil drive | 19 J | 2.1e-16 kg | 1.6e-42 | **22.8 decades** |
| 1 kJ pulsed discharge | 2.9 kJ | 3.2e-14 kg | 2.4e-40 | **20.6 decades** |
| Absurd upper bound | 2 MJ | 2.2e-11 kg | 1.7e-37 | **17.8 decades** |

Every configuration returns `REFUSED_BY_ARITHMETIC`, including a
2 megajoule bound far beyond anything this programme could build or
safely operate. The comparison is made against the *best instruments
that exist* — a 1e-19 optical clock, a 1e-11 superconducting
gravimeter — which makes the refusal stronger, not weaker.

The number that makes the scale intuitive:

> **Raising a clock by one millimetre against Earth's field produces a
> fractional shift 6.6 × 10¹⁷ times larger than the entire apparatus
> does.**

The device is not competing with a subtle effect. It is competing with
the floor of the building.

This result does not depend on whether the crystal, the geometry, the
drive pattern, or the source corpus are right about anything. It is
arithmetic on the energy budget.

**What it does not say:** relativity is not untestable at bench scale.
Optical clocks resolve centimetre height differences routinely. It
says the apparatus's *own* stress-energy is irrelevant, so any real
experiment here measures Earth's field, not the device's.

## 2. The CW vectors carry zero informative bits

The pack's most striking observation: all five 12-digit source strings
need exactly 38 bits, `38 = 2 + 3×12 = 2 + 6×6` matches the RGCS
4096-state and 64-state architecture, and under the 3×12 parse every
value shares header `10` and first field `1516`.

Computed rather than admired, this carries **zero informative bits**.

The five values occupy an interval whose endpoints share their top
**15** binary digits. The header (2 bits) plus the first 12-bit field
occupy the top **14** — entirely inside that forced prefix. "Every
value has header 10 and field one 1516" is a restatement of "these
five numbers are close together."

The matched null settles it empirically. Integers drawn uniformly from
the same interval, with no encoding whatsoever, reproduce the
identical structure in **20 000 of 20 000 draws (p = 1.000)**. Same
for the 6×6 parse.

Two further points of hygiene:

- `38 = 2 + 3×12` is a fact about the integer 38. *Every* 38-bit value
  admits both parses, so admitting them is not a property of these
  particular numbers.
- The decoder is frozen by digest, and after-the-fact field
  reassignment raises. That is what makes "we did not move the
  goalposts" checkable rather than assertable.

This does **not** show the strings are not a protocol. It shows this
observation cannot distinguish a protocol from five arbitrary nearby
numbers. Only prospective vectors, decoded without changing field
boundaries, could settle it.

## 3. The clock link: a reachable ceiling, and where it actually sits

R6 ended by recommending the two-oscillator comparison as the cheapest
high-information experiment. R7 computed its ceiling.

The naive calculation says two OCXOs reach the 1.09e-16 shift of a
1 m height difference after averaging for about 2.7 years. That is
wrong in a way that flatters the hardware. White frequency noise
averages down as `1/√τ`, but real oscillators stop at their **flicker
floor** and then drift. An OCXO pair floors at 1.4e-13 — three decades
above the target. The honest answer is not "longer". It is *never with
this hardware*.

Sweeping the transfer link surfaced the more useful engineering
result: **the bottleneck moves.**

| Pairing | Limiter | Resolves 1 m? |
|---|---|---|
| OCXO + any good link | oscillator | no |
| Caesium + short coax | comparable | no |
| Optical + short coax | **link** | no |
| Optical + stabilised fibre | link | **yes, ~1.7 s** |

Consumer quartz is oscillator-limited and no link helps it. The best
clocks are link-limited: an optical pair on short coax cannot resolve
a metre, while the same pair on stabilised fibre resolves it in
seconds. **Buying a better clock without buying a better link buys
nothing.**

The experiment is still worth running. The common-source split costs
almost nothing and is the only way to learn what the measurement chain
itself contributes — validated phase transfer, a measured instrument
floor, noise decomposition into white FM, flicker and drift, and an
honest sensitivity budget for any later claim. No amount of modelling
substitutes for that number.

## 4. Directional field geometry is vector addition

The source's 45° field-pair drawings are correct and unremarkable. Two
unit vectors at ±45° about a desired axis sum to `√2 d̂` with the
perpendicular components cancelling exactly.

The general result is `2cos(θ) d̂` for any half-angle θ, so 45° is
visibly not special — it is simply where `2cos(45°) = √2`. This is a
statement about adding two unit vectors. It is not a discovery about
fields, and it is not about force.

A commanded or even measured field vector sum is not thrust, pinch,
gravity, or motion. Labelling it requires force measurement surviving
controls: sham drive at equal power, reversed geometry (the sign must
flip), thermal and convective nulls, electrostatic attraction to
nearby surfaces, magnetic interaction with the mount and Earth's
field, tether stiffness, and buoyancy from heating. Thermal and
electrostatic artifacts have historically dominated every claimed
anomalous-thrust result at these power levels.

## 5. Alignment and excitation

The source claims the crystal's body axis, the local gravity axis, and
the crystallographic C-axis should coincide. R7 models them as three
genuinely distinct objects, because they coincide only if the crystal
was cut and mounted so they do.

Two honest points fall out. The crystallographic c-axis cannot be
determined from external morphology — Brazil and Dauphiné twinning
specifically defeat it, and only diffraction or conoscopic methods
find it directly. And "alignment with the planet's centre core" is not
the plumb line: geodetic and geocentric verticals differ by up to
~0.2° from the equatorial bulge, plus deflection of the vertical from
local terrain and density. That difference is larger than good
alignment hardware's resolution, so the claim has to choose which axis
it means.

On excitation, a passive crystal cannot self-oscillate — there is no
gain element, and a passive resonator can only ring down.
Self-oscillation requires the Barkhausen conditions: loop gain at
least unity *and* phase a multiple of 2π. A hand-held crystal that
appears to keep going is being driven — physiological tremor is
broadband at ~8–12 Hz and couples mechanically, skin contact supplies
triboelectric charge, and contact damping dominates Q by orders of
magnitude against free suspension.

## 6. Publication

Path chosen: **`PRIVATE_RC`**. The repository stays private, nothing
new is published, all artifacts are preserved.

The three paths are not symmetric. `PRIVATE_RC` forecloses nothing;
`FILE_THEN_PUBLISH` preserves the ability to publish later;
`DEFENSIVE_PUBLICATION` preserves neither — it creates public prior
art and destroys the author's own novelty in the same instant.

A git commit is evidence of a date and a content hash. It is not a
patent filing, not a defensive publication, not publication at all
while the repository is private, and not legal advice. A private
repository discloses nothing, so it neither establishes prior art nor
endangers novelty. Making it public is the single act that does both
at once.

## 7. Standing

Nothing in R7 is bench data. The programme's honest position is
unchanged and now more precisely quantified: the reachable experiment
is the clock link, the apparatus cannot produce a detectable metric
effect at any energy it could reach, and the most striking numerical
observation in the source material turns out to be arithmetic about
how close five numbers are to each other.
