# Summary for AG — R10.72 / v0.7

Your verdict was implemented as written: the arithmetic no longer carries
the physics. v0.7 is an optimizer and a measurement-prep package, and it
proves nothing.

## The three mandated proofs, now tests

1. **No exact 67.3 identity.** `673/10 − 64672/961 = 33/9610` is asserted
   exactly; 67.3 is typed `SOURCE_DISPLAY`, 64672/961 is
   `EXACT_ARITHMETIC`, and rounding is their only relation.
2. **No wall-power thrust.** Wall watts cannot reach the force boundary
   without a declared η_couple, and `thrust_claim()` refuses everything
   except a lane-D measurement with an uncertainty — including a
   lane-B Fraction smuggled inside a Coefficient wrapper. A
   positive-control test shows the gate *would* open for a real
   measurement, so the refusals exercise a working gate, not a stub.
3. **No force in the Brown proxy.** Neither proxy module exposes a
   force/thrust name; a test walks both namespaces.

## What the optimizer found (model-level, no force)

Under the locks (37 / 35 running / 33 active / no rotation / 1,683,456 Hz):

```text
capacitive_gap_weighting   |d_eff| = 0.283   ← best 33-active family
graded_current_taper       |d_eff| = 0.179
graded_phase_taper         |d_eff| = 0.146   (steers direction ~25° off axis)
best binary blanking       |d_eff| = 0.057
```

**Grading beats blanking ~5×**, and every graded family beats an
equal-resource null. Independently, the upgraded Brown proxy says the
same thing: graded drive recovers **46%** of a literal geometric
displacement vs **9%** for binary blanking. Two different models, same
ordering — that convergence is the run's engineering result.

Honest negatives kept: separated and near-opposite blanks *fail* their
nulls; the single-blank null is degenerate and is not scored as a win.

## The natural next sweep

Phase taper is the only family that rotates d_eff off the blank axis;
loading grade is the strongest magnitude knob. **Compose them** — a 2-D
sweep over (loading modulation, phase lag) under the same locks and the
same null — before any bench work. Cheap, and it produces the drive
recipe the bench would actually use.

## Bench gate (all BENCH_REQUIRED)

The carrier lock pins L·C = 8.938e−15 s² exactly, so the electrical
unknowns are one number thinner than they look. The measurement plan
covers η_couple, L_eff, C_eff, Q_L, R_loss with instruments and target
uncertainties; the six-term firewall voids any residual until all seven
control receipts exist.

## Bermuda lane

Retagged as ordered and frozen in code: `236805/142 →
RECORDED_POSTHOC_LEAD`; both vectors → `UNRESOLVED … NO_SUPPORTING_PARSE`;
`BERMUDA_FLORIDA_VERTEX → CANDIDATE_LABEL_ONLY`; projector fitting and
release-as-solved → `FORBIDDEN`.

## Status

```text
32 new tests, all passing; no tautologies, skips or xfails
release filter unchanged; PUBLICATION_HOLD; no tag, no push
performance_claimants() == []   ← the package's ground state
```
