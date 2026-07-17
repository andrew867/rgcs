# Eye post-refinement, resource calibration, and independent
replication (Agents Y01, Y02, Y03)

Coverage: **Y001–Y024**. Implementation:
[`rscs2_core/eye_ladder_analysis.py`](../../../rscs2_core/eye_ladder_analysis.py),
[`tools/v4x2_eye_census.py`](../../../tools/v4x2_eye_census.py).
Artifacts: `docs/v4/proof/C02/independent_census.json`.
Current public wording: [EYE_CLAIM_CARD.md](../EYE_CLAIM_CARD.md),
card **v4**.

## Y01 — interpretation without extrapolation laundering

- The canonical v4.1 record and the v4.2.1 ladder are module-level
  constants; the accessor returns copies; the interpretation record
  **appends** (`supersedes: None`) and names everything it appends to.
- Convergence is fitted with THREE models (linear-h, quadratic-h²,
  geometric), and the **spread across models is reported as the
  extrapolation uncertainty** — one extrapolated number without its
  model dependence is laundering, and the code refuses to produce
  one.
- Mode identity is MAC-based (`mac`, `track_modes`): permuted modes
  are tracked correctly, sub-threshold matches are reported
  LOST_OR_SWITCHED, double-claims are conflicts. An index is not an
  identity.
- Separations are signed (axial/transverse decomposition).

## Y03 — the independent census, and what it corrected

The V5 ladder selected the cluster nearest the v4.1 coordinate —
a selection that cannot see the rest of the field. The census
removes the bias: all clusters, all three diagnostics, full domain,
plus eigenspace tracking across meshes.

Result (cl3.0 + cl2.0, committed artifact):

| Region | Content |
|---|---|
| male apex (z ≈ 99.3–101) | ONE persistent concentration — the v4.1 (102.24) and V5 (99.78) coordinates are two resolution-dependent **estimates of this single feature** (they differ by 2.53 mm) |
| female apex (z ≈ 4) | a mirror concentration — the apex feature has a twin |
| mid-shaft (z ≈ 58) | a symmetric D2 pair |
| eigenspace | tracked across meshes, principal angles < 2.7° — no mode switch |

Corrections this forced (claim card v3 → v4):

1. "The v4.1 coordinate does not survive refinement" conflated the
   estimate with the feature. The **feature survives**; the estimate
   was resolution-dependent.
2. The apex feature is **not unique** — it has a symmetric family,
   which any special-point narrative must now confront.
3. The station comparison stands: 5.1–6.7 mm across meshes and
   diagnostics against a ~1.8 mm halfwidth.

Language rule (from the closeout delta, enforced in the census
output): the census reports what the pipeline did and did not
identify **under the tested configuration** — never a bare
nonexistence claim. And throughout: *computational comparison
resolved for this implemented idealized model; physical Eye
hypothesis open and untested.*

## Y02 — resources, calibrated against the failure

The calibrated memory model (`memory_model`) fits the three measured
points (5.4k → 0.6 GB, 14.6k → 2.8 GB, 30.8k → 13.9 GB), reports its
own residual, and predicts **ranges** (`predict_memory_gb`), not
points. Its history field preserves the 150× failure of the dof^1.5
estimate as a defect record, per the closeout delta.

`preflight()` refuses any solve whose HIGH estimate exceeds 60% of
machine RAM — refusal is the success path. `job_manifest()` packages
refused solves for larger machines with expected ranges and the
per-level checkpointing already built into the V5 runner.

Solver alternatives (Y012): LOBPCG+AMG is the cheapest real path
below 1.5 mm spacing (O(dof) memory, no LU factor); nested local
refinement stays second choice because it entangles convergence rate
with the size-field shape; domain decomposition and contour solvers
are documented options for HPC. Benchmarking two paths on a
controlled small case is queued in the job manifest; no infeasible
solve was launched to satisfy a prompt.
