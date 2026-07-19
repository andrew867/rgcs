# R8.1 Prior-Art Review

Three adversarial literature reviews, one per proposed paper. Each was
briefed to *find* prior art rather than clear the way, on the grounds
that "already published" is a result that saves months.

All three found substantial prior art. Two of the three proposed
papers change shape as a result, and one should not be a research
paper at all. Two factual errors in our own material were caught.

---

## Summary of verdicts

| Proposed paper | Verdict | Action |
|---|---|---|
| DDS closure | **formula already published**; residual is the continuous/sampled discrepancy | short correspondence, not a research paper |
| Null calibration | **principle is NOT novel**; synthesis survives as tutorial/methods | reframe, do not claim the principle |
| Relational coordinates | **6 of 7 components textbook** | not a research paper — software paper or technical report |

---

## 1. Null-calibration methods paper

### The principle is not novel and must not be claimed

The thesis — *a null is interpretable only if the detector can recover
a planted signal* — is **Mayo & Spanos's severity requirement**: a
hypothesis that passes a test incapable of detecting a discrepancy
passes with low severity and is poor evidence. It has been
independently renamed in at least four fields:

- astronomy — injection-recovery, detection-efficiency curves;
- particle physics / GW — blind analysis, hardware and software
  injections;
- biology — the positive control;
- machine learning — sanity checks for saliency maps.

A reviewer who finds Mayo before we cite her will reject. A reviewer
handed Mayo will accept the framing.

### Case-study verdicts

| Case | Verdict | Governing literature |
|---|---|---|
| 1. Forced-prefix structure | well covered as principle | Efron (1971) on Bode's law; McKay et al. (1999) on the Bible code; Diaconis & Mosteller (1989) |
| 2. Granularity-mismatched null | known but scattered — **our strongest** | Markello & Misic (2021) spatial nulls; Schreiber & Schmitz (1996) IAAFT; Fosdick et al. (2018) |
| 3. Blind detector | well covered | Klein & Roodman (2005); Christiansen et al. (2020); Adebayo et al. (2018) |

### Correction to our own framing

Case 2 is **not** circular analysis / double dipping. Kriegeskorte's
double dipping is selection-then-test on the same data — a
non-independence error. Ours is a *nuisance mismatch*: the null and
the observed data differ in a property the metric is acutely
sensitive to. Different mechanism. A neuroimaging reviewer would have
said so immediately. Cite Kriegeskorte for contrast, not identity.

### What survives

Two things, both now implemented in `r8/nullcal.py`:

1. **The bits-accounting form** — informative content of a
   retrospective parse = bits used − bits forced by the admissible
   set. Not found published in this form.
   (`retrospective_information`)
2. **Negative controls scoring "better than chance" as a
   self-diagnosing signature** — requires no knowledge of the true
   effect and its failure is unambiguous. Not found presented as a
   general diagnostic. (`negative_control_signature`)

Plus the reusable artifact: a three-question pre-flight checklist with
code behind each question (`PREFLIGHT_CHECKS`, `preflight`).

**Venue:** *Royal Society Open Science*; preprint arXiv `stat.ME`
primary, `physics.data-an` cross-list. Lead with case 3, make case 2's
negative-control signature the portable headline.

---

## 2. Relational coordinate manuscript

### Six of seven components are textbook

| Component | Verdict | Owner |
|---|---|---|
| 1. Root aliasing, dual-carrier thinning | **textbook, three times over** | Teunissen LAMBDA; Melbourne–Wübbena wide-lane; synthetic-wavelength interferometry; robust-CRT sub-Nyquist |
| 2. Typed root certificates | partially covered | **IVOA STC 1.33** (near-direct hit); PhysFrame; certifying algorithms; PTB DCC; PROV-O |
| 3. Recursive barycentric frames | textbook | IAU 2000/2006 resolutions; SPICE; astropy; TEMPO2 |
| 4. Exact radix addressing | **vacuous — delete** | it is arithmetic; "refused as compression" is the absence of a claim |
| 5. Emission coordinates | textbook | Coll–Ferrando–Morales (2006); Rovelli (2002); bifurcation/DOP gating already published |
| 6. Relativity validation | not a novelty claim | see correction below |
| 7. Refusal semantics | possibly novel as framing | "rhetoric with a type signature" — a discipline, not a result |

Alias counting deserves special mention: 4097 candidates over one
second at 4096 Hz is `2·(4096/2)·1 + 1`. Presenting `2N+1` as a
finding is presenting a definition as a discovery.

### The honest residual

> A typed, certificate-carrying coordinate object in which the
> unresolved alias set is retained as data, the frame chain propagates
> uncertainty as a first-class citizen, and insufficiency of evidence
> is a typed output value.

Each leg is individually prior art; the claim can only be about the
composition. And **the composition's value is unproven** — we have no
case where the integrated object caught an error the separate tools
miss. PhysFrame is the bar: frames as types, evaluated on 180 real
projects, 154 true-positive inconsistencies found. Without that, this
is a design document.

The most defensible single piece is the **uncertainty-carrying frame
chain**, because SPICE, astropy and ROS tf2 all verifiably lack it and
tf2's omission is a long-standing acknowledged limitation.

**Recommendation: software paper (JOSS / SoftwareX / *Astronomy &
Computing*) if the code is real, otherwise a technical report.** Not
*Phys. Rev. D*, not *Journal of Geodesy*, not *GPS Solutions* — those
communities will recognise their own textbook material immediately.

Reaching for a research paper would contradict the project's own
stated discipline about not over-claiming, which is a conspicuous
irony for a referee to point out.

---

## 3. Corrections to our own material

### R8-D-001 — the Pound–Rebka "validation" is not a validation

`docs/v4/cspc/CSCP_FINDINGS.md` claims the clock model is "validated
against two published **measurements** — Pound–Rebka (computed
2.4551e-15 vs published 2.45e-15)".

**This is wrong.** 2.45e-15 is the *theoretical prediction* `gh/c²`
for the ~22.5 m Jefferson tower, not the measured value. Verified
directly: `9.80665 × 22.5 / c² = 2.4551e-15`. So the comparison is
between our arithmetic and the same formula's arithmetic — a
self-consistency check with no evidential weight.

The **measured** Pound–Rebka result was ≈ (2.57 ± 0.26) × 10⁻¹⁵,
agreeing with the prediction to roughly 10%. That 10% is the actual
empirical constraint, and it is the number an honest validation would
quote.

The GPS figure has a related problem: the third digit of
+38.44 vs +38.5 µs/day is a modelling convention (assumed orbit
radius, eccentricity handling), not a measured quantity. Fine to
include; not fine to present as three-digit validation.

**Consequence:** the claim that this machinery is "validated against
published measurements" is withdrawn. It reproduces standard
formulae correctly, which is worth stating and is not the same thing.

### R8-D-002 — quadrature accumulation contradicted the covariance field

`r6.mailbox.FrameGraph.total_uncertainty_m` added link uncertainties
in quadrature, which assumes independence. A frame chain typically
shares an ephemeris, a time scale and a calibration across several
transforms, so the errors are correlated and quadrature *understates*
the total. Meanwhile the certificate carried a covariance field — so
the object claimed to track correlation and then discarded it.

**Fixed.** `total_uncertainty_m(correlation)` implements the uniform
pairwise-correlation form, reducing to quadrature at ρ=0 and to linear
addition at ρ=1, with `worst_case_uncertainty_m()` giving the bound.
For a 9-link chain at 2 m per link, quadrature reports 6.0 m against a
fully-correlated 18.0 m — understating by 3×.

---

## 4. Open items the reviews could not settle

- **ISO 19111 / OGC Abstract Topic 2** (geospatial CRS standard, formal
  typed model of coordinate reference systems and datums) was not
  checked and should be before any coordinate submission.
- Whether **Orekit**, GEODYN, GIPSY-OASIS, Bernese or Basilisk already
  propagate covariance through a frame chain in production. SPICE,
  astropy and tf2 verifiably do not.
- Whether metrology's **limit-of-detection** framework already names
  "a null from an uncalibrated detector is uninterpretable".
- Citation metadata across all three reviews was assembled from search
  results, not fetched full texts, and needs a verification pass
  before submission. One review self-reported a miscitation of
  Gelman & Loken it had found in a source.
- Non-English literature was not searched.

---

## 5. DDS vendor-documentation sweep (follow-up)

A second, narrower sweep targeted vendor application notes
specifically. It tightens the picture and does **not** overturn the
main verdict.

### ⚠ Verification caveat — this is not a clean search

`analog.com` was **unreachable for the entire sweep** (ECONNRESET or
60 s timeout on every HTML page and PDF; the r.jina.ai proxy returned
403). Several PDFs that did download were image-only and yielded no
extractable text.

**Every ADI quotation below is a search-engine extraction, not a
direct fetch.** They recur consistently across independent queries
with consistent page attribution, so confidence is reasonable — but
**AN-1396 and the full FSK/PSK article text must be read directly
before any filing or defensive publication.** Either could close the
remaining gap.

### What the sweep found

| Element | Verdict |
|---|---|
| Rollover/repeat period from *f_r*/2^*N* | **found decisively** — ADI states GRR via the rightmost nonzero FTW bit; Cordesses states T_ACC = 2^*N*/gcd(2^*N*, ACC) |
| Exact representability iff integer tuning word | **found** — ubiquitous |
| Prime-factorisation corollary (100 MHz = 2⁸·5⁸ forecloses dyadic tones at any *N*) | **not found** — ADI's "power of two" and "relatively prime integers" language approaches but stops short |
| Binary reference as a stated design rule | **not found in any vendor document** — only circumstantial (2²⁴ Hz parts are catalogued) |
| Multi-tone gcd closure | **partially found, closer than expected** — the ADI FSK article applies GRR across a *pair* of tuning words, which is arithmetically gcd(K₁,K₂,2^*N*). No *m* > 2 generalisation, and no q/(p·gcd) form with an arbitrary rational reference |
| Resolution-vs-closure tradeoff | **partially found** — stated for a single tone; never framed as a multi-tone penalty or as a design warning. The literature treats larger *N* as an unqualified good |

### Why this reinforces rather than threatens the salvage

The ADI two-tone construction keys on `gcd(K₁, K₂, 2^N)` — **it
includes the 2^N modulus**. That is the *sampled/accumulator* notion.
Our continuous formula uses `gcd(K₁…K_m)` **without** the modulus.

So the closest vendor prior art computes precisely the other one of
the two quantities whose disagreement is the surviving contribution.
Where gcd(K) carries an odd factor, ADI's construction and the
continuous formula give different answers — by exactly odd_part(gcd K).

Verified: ADI's worked example (1 GHz clock, 32-bit FTW, 2¹⁹-tick
period) reproduces as 1907.3486 Hz against their quoted ~1907 Hz.
`tests/v51/test_r8_dds.py` now pins this as a validation anchor,
which is what establishes that our `accumulator_closure` is the same
quantity the literature names, rather than a redefinition.

### Revised residual for the DDS work

1. The continuous-vs-sampled discrepancy and its odd-part law
   (unchanged — still the primary contribution).
2. The prime-factorisation framing of reference selection
   (not found, but exposition).
3. Inversion of the "bigger *N* is always better" assumption for
   multi-tone closure (not found as a warning, but a corollary).

The *m* > 2 generalisation is technically unanticipated but is one
value of *m* away from published work, which is a weak position. It
should not carry the paper.

---

## 6. Open gaps recorded by the measurement lane (P11–P13)

Recorded rather than quietly carried, because each would otherwise
become an overstatement later.

**R8-D-003 — MDEV and TDEV are specified but not implemented.**
`r8.measurement.analysis_plan()` names modified Allan deviation and
time deviation as required statistics. Only overlapping ADEV exists in
code (`r7.clocklink.overlapping_adev`). The plan currently points at
nothing for two of its three estimators. This is a real gap if P11 is
ever described as analysis-complete.

**R8-D-004 — "frozen" must not drift into implying registration.**
`analysis_plan()` returns `frozen: True`, which is a statement about
this module's content, not about registration with any third party.
`r6.bench` already records `PREREGISTERED_ANALYSIS: ABSENT` and that
remains true. The word is doing local work only.

**Unfounded parameters, declared as such.** BOM prices are
catalogue-class order-of-magnitude estimates with no supplier, date or
solicited quote (`price_basis: CATALOGUE_CLASS_ESTIMATE_NOT_A_QUOTE`).
Counter single-shot resolutions are part-category typicals, and they
drive the instrument/oscillator crossover times, so those are
order-of-magnitude too. The per-level referencing uncertainty in P12
has no empirical basis and is a caller-supplied knob, not a claimed
value.

### A result worth keeping from P11

No tier resolves one metre — verified independently against
`r7.clocklink.height_resolution`, and it falls out of the flicker
floor rather than being asserted:

| Tier | Cost | Floor | Min. resolvable height |
|---|---|---|---|
| minimal (TCXO) | $312 | 7.07e-11 | 648 km |
| standard (OCXO) | $2,200 | 1.41e-13 | 1.30 km |
| good (rubidium) | $14,100 | 1.42e-14 | 130 m |

All return `UNRESOLVABLE_AT_ANY_INTEGRATION_TIME`.

Secondary and more actionable: the minimal tier is **instrument**
-limited until τ ≈ 2000 s — its counter, not its oscillators, sets the
short-τ floor. Standard crosses over at 600 s, good at 100 s. Most of
what the upper tiers buy at short τ is counter, not clock.

---

## 7. Process note

`tests/v51/test_r8_framemem.py` and the three P11–P13 modules were
swept into commits by a broad `git add` from the coordinator while the
specialist was still working. Nothing was lost and the working tree
matched HEAD, but it crossed the pack's do-not-commit boundary in the
wrong direction: **code was committed before it was reviewed.** The
capability claims have since been reverified independently against
`r7.clocklink` (table above). Narrow, explicit paths on `git add`
would have prevented it.
