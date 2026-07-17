# Inverse design contract (Agent C08)

Coverage: **A17**. Status: `ENGINEERING_PROTOTYPE`.
Implementation: `rscs2_core.calibration.inverse_design`.

## What inverse design may and may not produce

Inverse design produces **candidate geometries**. It does not produce
evidence, and a design that hits its target does not thereby validate
the physics the target came from.

## The contract

1. **Preregistered objective.** The objective function and its weights
   are declared before the search runs. A target changed after seeing
   the Pareto front is post-hoc selection.
2. **Candidate diversity.** The optimizer returns a diverse set, not
   the single prettiest point. A one-candidate answer hides the
   flatness of the objective.
3. **Manufacturing constraints are hard.** A candidate outside the
   tolerance envelope is not a design, it is a wish. Constraints enter
   the search, not the write-up.
4. **Deterministic seed.** Same seed, same candidates. A search that
   cannot be reproduced cannot be reviewed.
5. **Status immutability.** The optimizer cannot promote an evidence
   class. A `SOURCE_HYPOTHESIS` target remains one after the geometry
   is found. `guarded_update` refuses the promotion in code.
6. **Impossible objectives are reported.** If no candidate satisfies
   the constraints, the answer is "no feasible design", not the least
   bad one presented as a success.

## Multiobjective reporting

Where objectives conflict (merit vs manufacturability vs mass), the
report is the trade-off surface, with the chosen point marked and the
choice justified. A single scalarized score hides the trade the
designer actually made.

## Why the merit function is ENG

`spiral_cone.geometry_merit` returns
Γ_s = cusp · |overlap| · log₁₀(1+Q), and it is labelled
`ENGINEERING_PROTOTYPE` with the note *carries no physical
significance claim*.

This is a ranking convention invented for design comparison. Two
designs can be ordered by it. That ordering is **not** a physical
prediction, and Γ_s is not a quantity anyone can measure. The label
exists so a future reader cannot mistake a design score for a result.

## Failure conditions

- Synthetic recovery of a known-optimal design fails → the optimizer
  is broken.
- The returned candidates cluster at a constraint boundary → the
  constraint, not the physics, is driving the design.
- Re-running with the same seed returns different candidates → not
  reproducible; the result is void.

## Current status

Inverse design has been exercised on **synthetic targets only**. No
designed geometry has been fabricated or measured. Every candidate is
a proposal (`ENGINEERING_PROTOTYPE`), and the fabrication route is
documented in [FABRICATION_CONTRACT.md](FABRICATION_CONTRACT.md).
