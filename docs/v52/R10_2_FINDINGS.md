# RGCS R10.2 — Chronology, Node Alignment, Public Evidence: Findings

**Status:** `SOFTWARE_VERIFIED_PHYSICAL_UNTESTED`
**Baseline:** v5.4.0 (`41537be`)
**Evidence class:** `DERIVED_MATHEMATICS`
**Hardware:** deferred by the pack. **No apparatus has been built.**

---

## Gate Zero (S00)

The pack's checkpoint matches repository truth exactly this time —
v5.3.1 at `3fb6874`, clean-clone 2808, CI green before tagging, both
package lists equal. Nothing to reconcile.

---

## The corpus arrived, and the import verified clean

The private corpus was supplied and imported into the private source
root. **70 files in, 53 byte-unique canonical files copied, every one
of the 53 SHA-256 hashes matching the bundle manifest, 17 exact
duplicates skipped.** Exact duplicates are not independent
corroboration and were not counted as such. The import lives in the
private repository (no remote, outside the public worktree); the public
firewall reports zero findings against the public tree.

Two of the 70 files are **public academic papers**, and those are the
part that produces public results. The other 68 are private
source-media transcripts and reference inputs, which stay private.

### Blocked phases now unblocked

- **S05 / S09** — a public conventional-science chronology and the two
  prior-art papers below.
- **Q19 prior art** — the 2018 tetrahedron paper was in the corpus, so
  the "could not verify" caveat from R10.1 is closed.

### Still blocked, and why

The source-message concordance (S06), the sighting/media ledger (S07),
and the contamination graph (S08 over source authors) all operate on
private transcript content. Their **engines** are built and public; the
**rows** that would encode private material are kept in the private
repository and never enter the public tree. That is not a limitation to
be worked around -- it is the publication boundary working as intended.

---

## Two public papers, both correcting an overestimate

**Module:** [`r10/priorart.py`](../../r10/priorart.py)

**The firefly paper** (Silver 2026, *Am. J. Phys.* 94, 520-524,
doi:10.1119/5.0325834) is titled "Resolving a century of
overestimation", and that is its result. A firefly flash contains
roughly **10⁸ to 10¹¹ photons — far fewer than the 10¹³ to 10¹⁴** implied
by Coblentz's 1912 figure: a downward correction of two to six orders of
magnitude. The honest number is a *range*, not a point, and it is
smaller than the famous one. Quoting the old figure, or the top of the
new range, would repeat the error the paper exists to correct.

**The tetrahedron paper** (Vîlcu & Vîlcu 2018, *Annali di Matematica*
197, 487-500, doi:10.1007/s10231-017-0688-6) is the exact prior art for
the R10.1 inverse estimator. Q19 reproduced it but could not fetch the
paper and recorded `prior_art.verified = False`. **The paper is now in
hand and the citation is confirmed.** The reproduction stays a
reproduction — the constants 20 and 60 were derived independently — so
the mathematics does not change, only the provenance. And the paper's
guarantee covers the uniform-interior case *only*, which is exactly the
regime R10.1 showed the estimator needs and the pack's conditions
violate.

Neither citation authenticates any source claim. A source assertion that
mentions fireflies, tetrahedra, or photons is not supported by a paper
that merely shares its vocabulary; `refuse_lore_promotion()` enforces
that.

---

## A public chronology, with the dates kept apart

**Module:** [`r10/chronology.py`](../../r10/chronology.py)

The chronology policy is strict that a "date" is nine separate fields —
event start, observer-local, recording, publication, repost, retrieval,
conventional-discovery, project-derivation, and more. The ledger keeps
them separate and admits only **exact-timestamp or exact-date** items
into the strict timeline.

Populated with **public conventional-science events only** — Coblentz
1912, the Chadwick→Pauli→Fermi beta-decay sequence, the
Freedman→Drukier-Stodolsky→COHERENT CEvNS lineage, the two papers above.
Of ten events, only **one** — Pauli's exactly-dated letter of 4 December
1930 — has a strict date and enters the strict timeline. The other nine
are year-only: real, searchable, but not strictly ordered, because a
year is not a strict date. The sparse strict timeline is the discipline
visible in the output.

**Chronology is not causality.** 45 possible-access edges record who
*could* have read what, by publication year — opportunity, never
influence. `refuse_causal_claim()` refuses to turn precedence into
causation, plagiarism, secrecy, or transfer.

The source-message chronology, which would encode private material, is
built in the private repository and never appears here.

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
- No source-message concordance or precedence result is public — those
  rows stay in the private repository.
- **No person is classified as nonhuman or as any lore species**, and no
  personal encounter record, resemblance, or private journal content
  appears anywhere in this repository. The pack forbids it; so does
  ordinary decency.

---

## Not executed

S12–S16 (node/topology embedding beyond R10.1), S19–S21, S23. The
source-content phases (S06–S08, S10) have public engines but private
rows by policy. Hardware remains deferred.
