# V4 Reference Systems Spec (RSCS2-V.*) — mandatory external validation

**Status:** PLANNING. **These are gates, not extras (DV4-008):** the two
mandatory systems must pass before any crystal eye result is reported.
All reference truths are EST closed-form or published values.

## Example 2 (mandatory) — tuning fork (steel or aluminium)

- **Why:** isotropic, well-characterized, symmetric/antisymmetric mode
  structure, a different geometry class from the crystal.
- **Reference truth:** analytic beam-on-fork approximation for the
  fundamental; published FEM/experimental values where **licensed and
  available** (licence recorded; none embedded without permission).
- **Validation:** first symmetric & antisymmetric modes vs analytic;
  **mesh-convergence study** (RSCS2-V.8) showing monotone convergence to
  the reference band; free-boundary rigid-mode handling.
- **Exit criteria:** converged eigenfrequencies within the reference
  tolerance; convergence order matches element theory.

## Example 3 (mandatory) — EB / Timoshenko cantilever (beam / MEMS)

- **Why:** exact closed-form eigenfrequencies and mode shapes — the
  cleanest possible solver oracle.
- **Reference truth:** Euler–Bernoulli fixed-free βₙL roots
  (1.875, 4.694, 7.855, …) → ωₙ = (βₙL)²√(EI/ρAL⁴); **Timoshenko
  correction** (RSCS2-V.3) for thick beams (shear + rotary inertia).
- **Validation:** eigenfrequencies vs closed form; **mode-shape
  correlation** (MAC ≥ threshold) vs analytic shapes; slenderness sweep
  showing EB→Timoshenko divergence at the predicted aspect ratio.
- **Exit criteria:** first ≥4 eigenfrequencies within tolerance; MAC ≥
  0.99 on those modes; Timoshenko case matches the thick-beam reference.

## Optional Example 4 — different solver branch

One of: acoustic cavity (Helmholtz eigenproblem → exercises a scalar
field + different BC), circular plate (Kirchhoff/Mindlin → 2D flexural),
or optical ring resonator (exercises the optical/wave branch). Chosen to
stress a solver path the crystal + fork + beam do not. Ships when a
tranche-G phase has budget; not a release blocker.

## The full benchmark set (RSCS2-V.1..10)

| id | System | Truth | Gate |
|---|---|---|---|
| V.1 | free-free rod | analytic longitudinal | solver sanity |
| V.2 | fixed-free EB beam | closed form | **mandatory** |
| V.3 | Timoshenko beam | corrected closed form | **mandatory** |
| V.4 | tuning fork | analytic + published | **mandatory** |
| V.5 | isotropic cube/sphere | published eigenvalues | solver sanity |
| V.6 | α-quartz Christoffel | frozen v3 (DV4-009) | **conservative ext.** |
| V.7 | piezo single element | IEEE-176 form | L3 gate |
| V.8 | mesh convergence | order estimate | **every benchmark** |
| V.9 | degenerate splitting | frozen v3 (DV4-009) | **conservative ext.** |
| V.10 | asymmetric geometry | predicted diagnostic shift | eye gate |

## Tests / acceptance

Each benchmark is a golden analytic-reference test with a recorded
tolerance and a convergence study. V.6 and V.9 are the
conservative-extension anchors (CI-gated). A crystal eye report is
**blocked** by the pipeline until V.2, V.3, V.4 (mandatory) and V.6, V.9
(conservative extension) are green for the active build.
