# RGCS v6.2.0 — Release Notes

**Status:** `SOFTWARE_VERIFIED_PHYSICAL_UNTESTED`
**Baseline:** v6.1.0
**Licence:** MIT, unchanged. No relicensing.

R11.1: exact N=7 acoustic geometry and its one-seventh phase identity, a
multiscale mode-mixing layer, a frozen π-correction registry, a historical
angle audit, a preregistered rotating-field experiment, and an energy
ledger. Eight new `r11` modules, additive only.

**Final verdict:
`R11_1_GREEN_MODELS_AND_EXPERIMENTS_IMPLEMENTED_NO_NEW_PHYSICS_CLAIM`**

---

## The critical identity — and why it proves nothing

```
L = v/(2Nf)  ⇒  2L/v = 1/(Nf)  ⇒  f·2L/v = 1/N turn
N = 7  →  exactly 1/7 turn = 360/7 = 51.428571428571°
```

Proved symbolically with `Fraction`, parametrized over **24 N × 3 f × 3 v**
— it holds every time, because `v` and `f` cancel identically.

**That invariance is the point.** A relation that holds for every N, f and
v cannot fail, so it is a *definition*, not a discovery, and says nothing
about quartz or about 4096 Hz. `refuse_identity_as_evidence()` enforces it.
The lengths (L = 110.0376674 mm, round trip 34.877232 µs) come from a
scalar model with a **proxy** velocity — a control, not a specimen
prediction.

## The 51.843° reconstruction — `RETROSPECTIVE_NUMERIC_MATCH`, capped

`atan(√φ) + π/200 = 51.843000336°`, residual **3.36×10⁻⁷**. Real
arithmetic, capped for three independent reasons:

1. **Input precision.** 51.843 is quoted to 3 decimals → **±0.0005°** of
   slack. The agreement is ~**1487× finer** than the input's own
   precision, and **60** simple `c/N` corrections fit inside it (φ/103,
   e/173, √2/90…). *But* within the **frozen π/k family**, only k = 200
   fits — runner-up k = 192 is **1948× worse**. Both stated.
2. **Units.** π/200 rad = 0.9°, not 0.0157° → `UNIT_CATEGORY_MIXED`.
3. **History.** `BLOCKED_MISSING_DATA` — no primary source located.
   A slide rule **cannot single it out** (6 of 7 candidates fit the band),
   and 51°51'51" = 51.8641667° is a **different number**.

The π-denominator family is **frozen before scoring**.

## Mode mixing — five typed domains, no transfer

One shared coupled-mode core; five adapters (III-V lattice, macroscopic
quartz elastic, BVD electrical, optical cavity, dynamic boundary). **Every
ordered cross-domain transfer is refused.** The teeth:
`rotation_versus_squeeze()` — both 2×2 with unit determinant, but
conserving `x²+y²` vs `x²−y²`. Identical algebra, different physics.

## Not run, and said so

The rotating-field interruption experiment is **preregistered and NOT
run** — 14 observables `BLOCKED_MISSING_DATA`, eight controls required,
prediction set SHA-256 frozen. The energy ledger refuses to call
transferred energy loss, catches hidden-basis energy, requires switching
work, and reports `E_unclosed` as an interval that is currently **vacuous**
because every term is uncalibrated.

## Red team found a real hole

Sixteen mandated attacks, each failing with a typed reason. **Attack 16
was not theatre:** `refuse_private_delta_read()` did not recognise
`private_do_not_commit/` — the very directory this pack's Gate Zero
forbids. Marker added; the guard now blocks it.

## Verification

```bash
git clone https://github.com/andrew867/rgcs && cd rgcs
pip install -e ".[dev]"
pytest -q --deselect tests/regression/test_generator_determinism.py::test_generator_deterministic
# expect: 4936 passed
```

> **CI note.** Free-tier GitHub Actions minutes are exhausted; the
> verification of record is the full local suite on the exact commit.

## What this release does not claim

No new particle, no Phyrll, no transport, no unknown-energy channel, no
bench measurement, and no historical authorship. It establishes
mathematics, simulations, CAD-level models and an experiment plan —
nothing more.

See [R11_1_FINDINGS.md](R11_1_FINDINGS.md) for the full analysis.
