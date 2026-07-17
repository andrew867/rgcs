# V4X final QA verdict (Q01)

Scope: the v4.2 Master Research Expansion, audited at the v4.2.1
closeout. This supersedes nothing: `V4_QA_FINAL_VERDICT.md` remains the
**v4.1** verdict and is a historical record.

Companion: [V4X_DEFECT_REGISTER.md](V4X_DEFECT_REGISTER.md).

## Verdict

**RELEASE APPROVED as v4.2.1** — a research-and-protocol release with
explicit hardware, ethics, and resolution blockers.

No open P0. No open P1. Eleven defects found, all closed with
regression tests.

## What the attacks found

Each attack below was run against the tagged v4.2.0 candidate. The ones
that **succeeded** are the interesting part.

| Attack | Result |
|---|---|
| Fake 100% coverage through nonempty strings | **SUCCEEDED** → V4X-D-012 |
| Registry-only work labelled validated | **SUCCEEDED** → V4X-D-006 (C05), V4X-D-007 (T-lane) |
| Status laundering | **SUCCEEDED** → V4X-D-007, V4X-D-013 |
| Missing docs | **SUCCEEDED** → V4X-D-009 (47 missing) |
| Orphan ideas absent from the ledger | **SUCCEEDED** → V4X-D-010 (20 found) |
| Post-hoc cusp acceptance | **partly** → V4X-D-005 (premise wrong; a worse metric bug found) |
| Stale test counts | **SUCCEEDED** → V4X-D-004 |
| Missing symbols | repelled (all declared symbols import) |
| Synthetic data labelled measured | repelled (constructor refuses) |
| Import from the quarantined lane into quartz | repelled (AST-verified, G51) |
| Import from quartz into the quarantined lane | repelled (G51, both directions) |
| Source laundering | repelled (classification ceilings hold) |
| Frequency numerology | repelled (look-elsewhere null; 4095≠4096) |
| Capability bypass | repelled (operator-capability floor) |
| Eye threshold regression | repelled (1e-6 mm tolerance; no proximity rule) |
| Invalid Gerber/CAD | repelled (structural checks pass) |
| BVD non-identifiability | repelled (reports it rather than fitting) |
| Apparatus residual overclaim | repelled (artifact budget precedes residuals) |
| Unsafe protocol enablement | repelled (envelopes enforced) |
| Absent ethics gate | repelled (returns before engineering checks) |
| Scratch-data leakage | repelled → V4X-D-014 (C02 clean; agent05 manifested) |
| Private-source inclusion | repelled (layer ceilings + release filter) |
| Release-builder drift | **SUCCEEDED** → V4X-D-002 (hardcoded version) |

**Seven attacks succeeded.** That is the honest headline: v4.2.0's
coverage proof was checking strings, two workstreams were registries
wearing an implementation's status, and the completeness agent had
never run.

## Gates

| Gate | Status |
|---|---|
| G42A ID coverage | PASS (268 rows) |
| G42B artifact existence | PASS (paths exist, symbols import) |
| G42C source/equation provenance | PASS |
| G42D test or falsification per row | PASS |
| G42E documentation per row | PASS |
| G42F status legal for depth | PASS |
| G42G blocker + next action | PASS |
| G51 lane quarantine (separate consciousness lane) | PASS (AST, both directions) |
| Adversarial audit | 19/19 |

## What this release does NOT contain

- **No measured data.** Not one experimental data point exists.
- **No experimental confirmation** of anything.
- **No resolved Eye question** — see below.
- **No fabricated specimen, PCB, or spiral cone.**
- **No human participant.**

## The Eye — RESOLVED, and the answer changed

The preliminary ladder (8.0/5.5/4.5 mm) was mis-titled "sub-millimetre"
(V4X-D-011) and returned `INSUFFICIENT_RESOLUTION`. The v4.2.1 audit ran
a genuinely finer ladder (3.0/2.0/1.5 mm, 30 816 dof at the finest).

**Verdict: `NEAR_CONVENTIONAL_NODE_BUT_DISTINCT` — resolved.**
Halfwidth **1.803 mm** < separation **6.298 mm**, by 3.5×. For the
first time the comparison carries information, and the implemented
conventional model **does not explain** the candidate.

**The v4.1 candidate coordinate does not survive refinement.** Its
distance from the recorded (−0.295, −0.205, 102.240) mm *grows*
monotonically with resolution — 1.375 → 2.270 → 2.476 mm — converging
instead on (−0.048, −0.020, 99.78). At cl=1.5 there is no cluster at
z = 102.24.

QA position: this is a **scientific finding, not a defect**. The v4.1
record is a faithful record of a computation performed at ~4 mm
spacing, where the halfwidth exceeded the distances under discussion.
It is preserved unchanged (G07); what changes is its interpretation —
it is resolution-limited, not converged. The candidate was never moved
onto the comparator.

Bounds on the claim: computational only, ideal geometry, first elastic
mode, assumed orientation (no XRD exists), final convergence shift
0.207 mm, and cl=1.25 infeasible on this hardware (~45–71 GB projected
against 31.6 GB total). **No experimental confirmation of anything.**

## Remaining limitations

1. Every experimental campaign is a protocol. Hardware and ethics
   blockers are real and are listed per campaign.
2. Reference-system models (polaritons, magnons) are mathematics about
   other materials, retained for comparison only.
3. The specimen orientation is unknown (no XRD), and the elastic model
   is orientation-dependent — so the material-comparison lane is
   **interpretively blocked**, not merely data-blocked.
4. Source-derived items remain SRC/HYP and cannot be promoted by
   repetition, optimization, resemblance, or preference.
5. A no-omission certificate is a proof that the searches ran, not a
   proof of exhaustiveness.

## Auditor's note

The most valuable finding was not any single defect. It was that
**"248/248 coverage, all gates green" was true and meaningless at the
same time**: the ledger verified that 248 rows had text in them. A
completeness contract that cannot fail is not a contract, and the seven
successful attacks all lived in that gap.
