# RGCS R10.2 — Chronology, Node Alignment, Public Evidence: Findings

**Status:** `SOFTWARE_VERIFIED_PHYSICAL_UNTESTED`
**Baseline:** v5.3.1 (`3fb6874`)
**Evidence class:** `DERIVED_MATHEMATICS`
**Hardware:** deferred by the pack. **No apparatus has been built.**

---

## Gate Zero (S00)

The pack's checkpoint matches repository truth exactly this time —
v5.3.1 at `3fb6874`, clean-clone 2808, CI green before tagging, both
package lists equal. Nothing to reconcile.

---

## Most of this pack is blocked, and for the same reason as last time

`RGCS-private/sources/` contains **0 files**. The checkpoint describes a
working concordance of 65 transcript files, 48 byte-unique texts, and 17
duplicate groups — **none of that material is present on this machine.**

Blocked outright, because they operate on corpus bytes that do not exist:

| Phase | Needs |
|---|---|
| S01 | private corpus to ingest |
| S02 | the 65 files, to deduplicate |
| S03 | source items, to build a metadata registry |
| S06 | dated source messages, for earliest-claim precedence |
| S07 | sighting records with timestamps and media hashes |
| S08 | the corpus, to model contamination and independence |
| S10 | differently-worded source concepts, to concord |
| S22 | all of the above, to attack |

Partially blocked: S04, S05, S11, S12 (schemas are implementable; the
content that would populate them is not).

**No metadata was fabricated for any of it.** The pack forbids it, and it
is the same discipline that kept `144.000` an untyped decimal.

---

## S17 — "breach" becomes measurable, which means it can be wrong

**Module:** [`r10/breach.py`](../../r10/breach.py)

Defining breach as *a persistent change in a crystal's resonant
frequency* is a genuine improvement: a narrative term becomes a number.

The immediate problem is that a quartz resonator's frequency moves for a
long list of ordinary reasons, most of them larger than intuition
suggests:

| Cause | Typical | Worst | Controllable? |
|---|---:|---:|---|
| Aging (first year) | 2 ppm | 5 ppm | **No** |
| Temperature off-turnover | 5 ppm | 30 ppm | Yes |
| Load capacitance | 10 ppm | 100 ppm | Yes |
| Drive level | 1 ppm | 10 ppm | Yes |
| Mount stress | 5 ppm | 100 ppm | Yes |
| Contamination | 1 ppm | 50 ppm | Yes |

Combined in quadrature:

- **12.5 ppm** — typical budget, nothing controlled
- **153 ppm** — worst case, nothing controlled
- **2.0 ppm** — everything controllable controlled, aging alone remaining

So a few-ppm shift is not an anomaly. It is Tuesday.

### The verdicts, and what is missing from them

`ORDINARY` · `WITHIN_UNCONTROLLED_BUDGET` · `UNEXPLAINED_BY_THIS_BUDGET`
· `REFUSED_NO_BASELINE`

**There is no exotic verdict on any code path**, and a test enforces
that: no verdict string may contain `BREACH`, `CONFIRMED`, `EXOTIC` or
`ANOMAL`. The best available outcome names what was *not controlled*
rather than what was discovered.

`UNEXPLAINED_BY_THIS_BUDGET` carries its own disclaimer: it means this
budget does not cover the shift. **The commonest explanation for a shift
outside a budget is a cause missing from the budget.**

### No baseline is refused outright

Aging alone guarantees the frequency was already drifting, so without a
characterised before-state there is nothing for a shift to be measured
*from*. A 1000 ppm claim with no baseline returns `REFUSED_NO_BASELINE`,
not a large number.

### The control that matters most

A **second, untreated crystal on the same instrument throughout**. It
converts an absolute frequency measurement — which drifts for a dozen
reasons — into a differential one, which mostly does not. Without it,
instrument drift and room temperature are indistinguishable from the
effect.

---

## S18 — the pump branches are different frequencies

`8 Hz × 2⁹ = 4096 Hz` exactly, and `4096 = 2¹²`. Also exact:
**20.48 = 512/25, and 20.48 × 200 = 4096.**

The pack requires that 20 / 20.48 / 21 Hz not be collapsed into one
resonance. They differ by 2.4% to 5% — small enough to invite rounding,
and the question of whether that matters is **not a matter of taste**:

| Q | 20 vs 20.48 Hz |
|---|---|
| 10 | inside one linewidth — not resolvable |
| 41 (≈ 1/separation) | the turnover |
| 10⁵ (a quartz crystal) | **2400 linewidths apart** |

At any Q a quartz resonator actually has, these are unambiguously
different frequencies. `resolvable()` decides it from Q, and a test
confirms the answer flips either side of the turnover — so it is
measuring something rather than asserting a preference.

### What the ladder does not show

Nine doublings from 8 reaches 4096 the same way nine doublings from 7
reaches 3584. The relation is a property of the radix, **not evidence
that either frequency is physically privileged.**

---

## What R10.2 does not claim

- No apparatus built, no crystal measured, no baseline exists.
- No breach observed. `refuse_breach_claim()` raises unconditionally.
- No chronology, concordance, or precedence result — the corpus is
  absent.
- **No person is classified as nonhuman or as any lore species**, and no
  personal encounter record, resemblance, or private journal content
  appears anywhere in this repository. The pack forbids it; so does
  ordinary decency.

---

## Not executed

S01–S08, S10–S16, S19–S23. That is most of the pack. The corpus-dependent
phases are blocked; the remainder was not reached in this tranche and is
not claimed as done.
