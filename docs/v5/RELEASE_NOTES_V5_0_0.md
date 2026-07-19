# RGCS v5.0.0 — R7

**Root Reference, CW Vector Decoder, Differential Clock Link,
Interferometric Crystal Alignment, Directional Field Geometry,
Falsifiable Metric Challenge, and Open-Legacy Decision**

Software implemented. Physically untested. No oscillator pair has been
compared, no crystal aligned or excited, no field mapped, no force
measured.

**Publication path: `PRIVATE_RC`.** The repository remains private and
nothing new is published. This release exists to preserve artifacts
for a later decision.

## R7 was asked for a falsifiable metric prediction. It produced one.

The prediction is that **nothing this apparatus can do is detectable**.

The chain is `u_a(t) → T_μν → g_μν`, and the first link is energy.
Every configuration returns `REFUSED_BY_ARITHMETIC`:

| Configuration | Energy | Clock shift | Gap to best optical clock |
|---|---:|---:|---:|
| Hand-held crystal | 1 µJ | 8.3e-50 | **30.1 decades** |
| Bench coil drive | 19 J | 1.6e-42 | **22.8 decades** |
| 1 kJ pulsed discharge | 2.9 kJ | 2.4e-40 | **20.6 decades** |
| Absurd upper bound | 2 MJ | 1.7e-37 | **17.8 decades** |

Refuted against the best instruments that exist, which makes the
refusal stronger. The comparison that fixes the scale:

> Raising a clock by **one millimetre** produces a fractional shift
> **6.6 × 10¹⁷** times larger than the entire apparatus does.

The device is not competing with a subtle effect. It is competing with
the floor of the building. The result does not depend on whether the
crystal, the geometry, the drive pattern or the source corpus are
right about anything.

It does *not* say relativity is untestable at bench scale — optical
clocks resolve centimetre heights routinely. It says the apparatus's
own stress-energy is irrelevant.

## The CW vectors carry zero informative bits

All five 38-bit source strings share header `10` and first field
`1516` under the architecture-matching `2 + 3×12` parse. Computed
rather than admired, this carries **zero informative bits**.

The five values occupy an interval whose endpoints share their top
**15** bits. Header plus first field occupy the top **14** — entirely
inside that forced prefix. Integers drawn uniformly from the same
interval, with no encoding at all, reproduce the identical structure
in **20 000 of 20 000 draws (p = 1.000)**.

`38 = 2 + 3×12` is a fact about the integer 38; every 38-bit value
admits both parses. The decoder is frozen by digest and after-the-fact
field reassignment raises, so a prospective test remains possible —
which is the only thing that could settle it.

## The clock link: where the ceiling actually sits

The naive figure says two OCXOs reach a 1 m height shift after ~2.7
years of averaging. That flatters the hardware. White FM averages as
`1/√τ`; real oscillators stop at their **flicker floor**. An OCXO pair
floors at 1.4e-13, three decades above the target. The answer is not
"longer" — it is *never with this hardware*.

Sweeping links surfaced the useful result: **the bottleneck moves.**
Consumer quartz is oscillator-limited. The best clocks are
link-limited — an optical pair on short coax cannot resolve a metre,
while the same pair on stabilised fibre resolves it in ~1.7 s. Buying
a better clock without a better link buys nothing.

The experiment still earns its place, ranking first on
information-per-dollar at 4.6× the runner-up.

## Alignment, excitation, geometry

- **"Perpendicular to the surface" and "toward the planet's centre"
  are different directions**, separated by up to 0.1924° (693 arcsec)
  from the WGS84 flattening alone — about **693×** an autocollimator's
  resolution, before deflection of the vertical is added.
- The crystallographic c-axis cannot be read from external morphology;
  Dauphiné twinning is invisible optically, so Laue back-reflection is
  the only direct method. Finer instruments that measure a *different*
  quantity buy nothing.
- A passive crystal cannot self-oscillate. Barkhausen needs loop gain
  **and** phase; a hand-held crystal that seems to keep going is being
  driven by tremor, triboelectric charge and contact.
- The 45° field pair sums to `2cos(θ)` for any θ, with the
  perpendicular cancelling at every angle. **30° gives √3 > √2**, so
  if magnitude were evidence, 30° would be better evidence. 45° is
  nowhere special.

## Publication

`PRIVATE_RC` — the only reversible path. `FILE_THEN_PUBLISH` preserves
the ability to publish later; `DEFENSIVE_PUBLICATION` preserves
neither, creating public prior art and destroying the author's own
novelty in the same instant.

A git commit is evidence of a date and a content hash. It is not a
filing, not a defensive publication, not publication at all while the
repository is private, and not legal advice.

## Standing

- Workbook: **39 sheets** (four new R7 sheets).
- Branch protection still unavailable (private repo, plan without
  protected branches). CI verified green on the tagged commit via PR;
  operator discipline, not a platform gate.

## Verification

```
# expect: 2161 passed
python -m pytest -q --deselect \
  tests/regression/test_generator_determinism.py::test_generator_deterministic
```

2161 is measured from a **clean clone of the tagged commit**, which is
what the published test-report asset contains and what anyone
reproducing from the source archive will see.

A full working copy reports **2166**, because five tests require
optional content that is not tracked in git: the prompt packs (3
tests), the eye corpus (1) and the reference PDFs (1). Each of those
skips is labelled "expected on CI".

The reproducible figure is documented deliberately. Publishing the
working-copy number would have recreated defect **V4X-D-004** — release
notes claiming one count while the test-report asset built from the
same commit says another.

Adversarial audit: 19/19.

## Next real step

Unchanged, and now ranked: the differential clock-link baseline. A
common-source split costs almost nothing and is the only way to learn
what the measurement chain itself contributes. Every later claim
depends on that number.
