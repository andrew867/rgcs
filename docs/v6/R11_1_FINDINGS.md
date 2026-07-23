# R11.1 — Exact Geometry, Mode Mixing, and the π-Correction Registry

**Authority:** RGCS R11.1 / v6.2.0 (candidate)
**Scope:** the eight R11.1 modules, the exact N=7 identity, and the 51.843° audit.
**Last verified commit:** v6.1.0 baseline (branch `v610-r11-1`)
**Prerequisites:** [R11_SPEC.md](R11_SPEC.md), [R11_DELTA_FINDINGS.md](R11_DELTA_FINDINGS.md)
**Related code / tests:** `r11/{n7geom,picorrection,anglerecon,modemix,rotfield,energyledger}.py`, `tests/v6/`
**Known limitations:** nothing measured; no bench, no specimen, no FEM re-run, no historical source located.
**Next review trigger:** any bench data, or a located primary source for the 51.843° derivation.

---

## Gate Zero

Recorded exactly: branch `main` → `v610-r11-1`, commit
`81eea7e86c553c0316b4e29475f4fb020399afbd`, tag `v6.1.0`, clean worktree,
4412 tests, `r11` in **both** package roots and `SOURCE_ROOTS`, firewall
committed gate CLEAN. `private_do_not_commit/` was **listed only — never
read, never committed**. Seven bundled references registered by SHA-256.

**Version note:** the pack proposed v6.1.0 as the target, but v6.1.0 had
already shipped. This tranche is **v6.2.0**.

## The critical identity — `EXACT_IDENTITY`

Under the scalar design model:

```
L = v / (2 N f)   ⇒   2L/v = 1/(N f)   ⇒   f · 2L/v = 1/N turn
```

For N = 7 that is **exactly 1/7 turn = 360/7 = 51.428571428571°**.

Implemented symbolically with `Fraction` and parametrized over
**24 N × 3 f × 3 v** — it holds in every case, because `v` and `f` cancel
identically and never appear in the answer.

**And that is exactly why it is not evidence.** The identity restates the
definition of `L`: we *chose* L so the round trip would take 1/(Nf). It
cannot fail, for any N, f or v, so no measurement could contradict it.
`refuse_identity_as_evidence()` enforces that reading. The *lengths*
(λ = 1.5405273 m, L = 110.0376674 mm, round trip 34.877232 µs) are a
`REPOSITORY_COMPUTATIONAL_RESULT` from a scalar model with a **proxy**
velocity — a control to compare against anisotropic elasticity, not a
prediction about a specimen.

## The 51.843° reconstruction — `RETROSPECTIVE_NUMERIC_MATCH`, capped

```
atan(√φ)            = 51.827292372987752…°
+ π/200             =  0.015707963267948967
                    = 51.843000336255701°
vs target 51.843    → residual 3.36×10⁻⁷°
```

The arithmetic is real. It is capped at `RETROSPECTIVE_NUMERIC_MATCH` for
three independent reasons, all reported:

**1. The input's own precision.** 51.843 is quoted to three decimals, so
it carries **±0.0005°** of slack. The agreement is ~**1487× finer** than
that, so the extra precision is not informative. **60 simple `c/N`
corrections** land inside the slack — φ/103, e/173, √2/90 among them.

*But the nuance cuts both ways:* within the **frozen π/k family**, only
**k = 200** lands inside the slack — the runner-up k = 192 is **1948×
worse**. So the relation *is* distinguishable within the preregistered
family, and *is not* within the broader `c/N` family. Both are stated.

**2. Units.** π/200 is radian-flavoured but used as degrees:
π/200 **radians = 0.9°**, not 0.0157°. The relation only works if the bare
number is *called* degrees → `UNIT_CATEGORY_MIXED`.

**3. History is missing.** `historical_evidence_status()` =
**`BLOCKED_MISSING_DATA`**. No patent, paper, notebook or period
calculator manual documenting this derivation was located here, and
`refuse_authorship_claim()` refuses to infer authorship from arithmetic.

Period-instrument audit: the expression reproduces 51.843 at **5–8
significant digits** (both rounding modes), fails at 3, 4 and 10. Of nine
historical constant combinations, **6 reproduce it and all 3 failures use
π = 3.14** — the sensitivity is in π, not φ. At slide-rule precision the
band contains **6 of 7** candidates → `CANNOT_SINGLE_OUT`. The
historically quoted **51°51'51" = 51.8641667°** is a *different* number,
76 arcsec away, and is not conflated with it.

The π-denominator family is **frozen before scoring**;
`refuse_new_denominator()` blocks post-hoc additions.

## Mode mixing — `MODE_MIXING_DOMAINS_TYPED_NOT_INTERCHANGEABLE`

One shared coupled-mode core (avoided crossing with minimum splitting
2|k|, mixing angle through 45° at zero detuning) with **five typed
adapters**: III-V atomic lattice, macroscopic quartz elastic, BVD
electrical (fs, fp, Q), optical-cavity transverse, dynamic boundary. Each
carries its own units, source class and `does_not_license`.

**Every ordered cross-domain transfer is refused.** The teeth are the
`rotation_versus_squeeze()` demonstration: the photon-conserving part is a
*rotation*, the Bogoliubov part a *squeeze* — both 2×2, both unit
determinant, but they conserve `x²+y²` and `x²−y²` respectively.
Identical algebra, different physics.

## Experiment and energy — both explicitly not run

- **`rotfield`** — the two-channel rotating-field interruption experiment
  is **preregistered and NOT run**. All 14 observables are
  `BLOCKED_MISSING_DATA`; all **eight** controls must be declared before
  any result; the prediction set is SHA-256 frozen.
- **`energyledger`** — transferred energy is **not** loss, hidden-basis
  energy is caught (modal fractions must sum to 1), switching work cannot
  be omitted, and `E_unclosed` is reported as an interval that is
  currently **vacuous** because every term is uncalibrated. A nonzero
  residual with an interval spanning zero is a calibration statement, not
  a discovery.

## Red team — and a real hole it found

Sixteen mandated attacks, each failing with a typed reason. **Attack 16
found a genuine gap:** `refuse_private_delta_read()` did not recognise
`private_do_not_commit/` — the exact directory this pack's Gate Zero
forbids. The marker was added and the guard now blocks it. That is the
red team doing its job on live code, not on a straw man.

## Final verdict

```
R11_1_GREEN_MODELS_AND_EXPERIMENTS_IMPLEMENTED_NO_NEW_PHYSICS_CLAIM
```

No new particle, no Phyrll, no transport, no unknown-energy channel, no
bench measurement, no historical authorship. The release establishes
mathematics, simulations and an experiment plan — nothing more.

`PHYSICAL_VALIDATION_NOT_CLAIMED`
