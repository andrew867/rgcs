# RGCS Knowledge and Evidence Audit

Assembled 2026-07-19 from the canonical store (`rgcs_workbench.
canonical.build`), the module sources, and the prior-art reviews.

**Scope caveat, stated first.** The R8.1 pack commissioned a
120-agent full-repository audit. The agent assigned to it was stopped
before completion, so this is a **coordinator-assembled audit built
from the canonical store and the prior-art record**, not the
exhaustive per-result inventory the contract specifies. It is
accurate on everything it covers and it does not cover everything.
Gaps are listed in §6.

---

## 1. Evidence distribution — measured, not asserted

271 records across 36 canonical tables.

| Evidence class | Count | Share |
|---|---:|---:|
| DERIVED_ARITHMETIC | 140 | 52% |
| ANALYTIC_MODEL | 49 | 18% |
| SOURCE_CLAIM | 48 | 18% |
| UNSUPPORTED | 16 | 6% |
| NUMERICAL_SIMULATION | 9 | 3% |
| GEOMETRY_IDENTITY | 7 | 3% |
| SYNTHETIC_RUN | 1 | <1% |
| LORE | 1 | <1% |

### The headline number

**`BENCH_MEASUREMENT`: 0. `INDEPENDENT_REPLICATION`: 0.
`CALIBRATED_MEASUREMENT`: 0. `REPLICATED_MEASUREMENT`: 0.**

Across every programme generation from v2 to v5.1, **nothing in this
repository has ever been measured.** 70% of records are arithmetic or
analytic model; 18% are raw source claims; 6% are explicit refusals.

This is not a criticism — it is accurately labelled throughout, and
the software refuses to emit a physical class (`cspc.
require_non_physical`, `r6.bench.refuse_synthetic_as_measurement`).
But it is the single most important fact about the corpus and it
governs everything below.

## 2. What is actually established

### KNOWN / DERIVED — sound and verified

| Result | Where | Status |
|---|---|---|
| Exact radix identity 4096 = 8⁴ = 4⁶ = 2¹² | `r4/radix.py` | exhaustively verified, all 4096 keys; explicitly refused as compression |
| DDS common closure T = q/(p·gcd K) | `r8/dds.py` | proved, brute-force validated — **but published prior art** |
| Continuous vs accumulator closure discrepancy = odd_part(gcd K) | `r8/dds.py` | proved, verified across 6 gcd cases; **not found in prior art** |
| Closure IS the delay alias | `pmwr/recovery.py` | true, and trivially so (f·W ∈ ℤ by definition) |
| Zero-residual alias count 2N+1 | `r3/root_space.py` | correct; it is elementary sampling theory |
| Wigner D-matrices and polyhedral projectors | `r6/wigner.py` | idempotent, Hermitian, integer traces; reproduces textbook invariant degrees |
| Weak-field clock formulae | `cspc/spacetime.py` | reproduces standard results correctly — **see correction R8-D-001** |

### NEGATIVE RESULTS — the corpus's real output

| Result | Verdict |
|---|---|
| Metric actuation from apparatus energy | `REFUSED_BY_ARITHMETIC` at every configuration, ≥17.8 decades below best instrument |
| CW vector "protocol" structure | zero informative bits; matched null p = 1.000 |
| Sovereign navigation | `SOVEREIGN_NAVIGATION_UNSUPPORTED`, 0/7 methods infrastructure-free |
| Source frequencies (1496/644/587 Hz) | not significant, p = 0.662 |
| Planetary polyhedral symmetry | `NO_REAL_DATA` — no geophysical dataset exists here |
| Alternating drive "torsion" claim | not purely differential; equal common-mode component |
| Consumer quartz metre-scale geodesy | unresolvable at any integration time |
| Passive crystal self-oscillation | refused — no gain element |
| Quartz four-state spin memory | `BLOCKED`, all gates open |

### QUARANTINED

Phryll (no `DETECTED` state exists, grep-enforced); nine biological
and medical claims registered `REFUSED_NOT_TESTED`; the
consciousness lane, quarantined with no quartz imports in either
direction.

## 3. Novelty status after prior-art review

| Body of work | Verdict |
|---|---|
| DDS closure formula | **already published** — Nicholas & Samueli 1987; Hwang 2017; Fujifilm US12422666B2 |
| Continuous/sampled discrepancy | **not found** — the one surviving DDS contribution |
| Null-calibration principle | **not novel** — Mayo & Spanos severity; positive controls |
| Bits-accounting form | **not found published in this form** |
| Negative-control signature | **not found as a general diagnostic** |
| Coordinate framework | **6 of 7 components textbook** |
| Uncertainty-carrying frame chain | real unmet gap in SPICE/astropy/tf2 |
| PMWR multipath recovery | **textbook** — declared as such by the programme itself |

## 4. Publishability matrix

| Item | Status | Route |
|---|---|---|
| Continuous/sampled DDS discrepancy | **PUBLISHABLE NOW** | short correspondence, IEEE TCAS-II / T-UFFC |
| Null-calibration synthesis | **PUBLISHABLE** with reframing | tutorial/methods, *R. Soc. Open Sci.* |
| Bits-accounting + negative-control signature | **PUBLISHABLE** as part of the above | — |
| Uncertainty-carrying frame chain | **REQUIRES WORK** — needs a demonstrated caught error | software paper (JOSS) |
| Coordinate framework | **NOT PUBLISHABLE** as research | technical report |
| PMWR / multipath recovery | **NOT PUBLISHABLE** | textbook |
| Everything physical | **REQUIRES DATA** | no measurement exists |
| Phryll, biological lane | **QUARANTINED** | not for publication |

## 5. Software / release corrections (defect register)

Selected, cross-generation:

| ID | Defect |
|---|---|
| CSPC-D-003 | null model carried denominator 10⁶ — inverted the headline |
| R6-D-001 | `tests/v49` outside `testpaths` — would never have run in CI |
| R6-D-004 | grid detector blind at every injection strength |
| R6-D-005 | Wigner phase error invisible to all structural checks |
| R8-D-001 | Pound–Rebka "validation" compared a formula with itself |
| R8-D-002 | quadrature accumulation contradicted the covariance field |
| R8-D-003 | MDEV/TDEV specified but not implemented |
| R8-D-004 | "frozen" must not imply third-party registration |

## 6. Not audited — explicit gaps

- **Per-result inventory** with the contract's full 15-field schema
  (`RESULT_ID`…`PUBLICATION_RISK`) was not produced. This document is
  a summary layer above it.
- `rgcs_core/`, `rscs_core/`, `rscs2_core/`, `fkey_instrument/`,
  `resonator_platform/`, `embedded/`, `firmware/` were **not
  individually audited** — they predate the coordinate thread and
  carry their own registers.
- The **unresolved-question graph** required by the contract was not
  built.
- Whether any `FINDINGS` document contains a claim the code does not
  support was checked only for the Pound–Rebka case (which failed).
  A systematic sweep was not run — and the one case that *was*
  checked failed, which is weak evidence that others would too.

## 7. Disclosure status

See `RGCS_RELEASE_AND_DISCLOSURE_TIMELINE.md`. In summary: **18
releases were published while the repository was public and
MIT-licensed** between 2026-07-15 and 2026-07-18, covering CSCP,
PMWR, R3 and R4. R6, R7 and R8.1 were released privately. This
materially affects the `PRIVATE_RC` decision and needs a patent
agent.
