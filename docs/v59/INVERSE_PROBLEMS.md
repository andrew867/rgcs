# Inverse Problems and Non-Identifiability

**Authority:** RGCS R10.10 / v5.9.0 (candidate)
**Scope:** Nonlinear parameter estimation with calibrated uncertainty, and detection of non-identifiable fits.
**Last verified commit:** v5.8.0 baseline (branch v580-r10-10)
**Prerequisites:** none (self-contained); helpful background in [CRYSTAL_SPECIMEN_PROGRAM.md](CRYSTAL_SPECIMEN_PROGRAM.md)
**Related code / tests / schemas:** [../../r10/nlinverse.py](../../r10/nlinverse.py), [../../r10/inverse.py](../../r10/inverse.py); tests/v52/test_r10_nlinverse.py, tests/v52/test_r10_inverse.py
**Known limitations:** These are estimators over supplied or simulated data. They fit no physical measurement from this repository and validate no model against the world. Hardware and real datasets are deferred.
**Next review trigger:** A new forward model added to the fitter, a change to the identifiability test, or introduction of real measured data.

## The problem this exists to catch

A forward model `y = f(params, x)` is easy to fit. The danger is that a
nonlinear least-squares fit almost always *returns* a point estimate, and
the point estimate almost always *looks* precise. `nlinverse.py` separates
those two facts: it fits, but before reporting a single number it asks
whether the parameters are even identifiable, and it proves — by
simulation — that its reported uncertainty is calibrated, not decorative.

## Non-identifiability

Fitting minimises `Σ_i (y_i − f(p, x_i))²`. Two failures hide behind a
tight-looking covariance:

- **Structural.** For the double exponential `a·exp(−b·t) + c·exp(−d·t)`,
  the pairs `(a,b)` and `(c,d)` swap without changing any prediction, so
  labelling is never unique. As `b → d` the model collapses to
  `(a+c)·exp(−b·t)`: only the sum `a+c` and the common rate are
  determined.
- **Practical.** When the Jacobian is rank-deficient (or near-so) over
  the data's support, directions in parameter space are unconstrained.

When the Jacobian is rank-deficient the module returns:

    NON_IDENTIFIABLE

rather than a falsely precise point estimate. A fit that "converged" is
not a fit that is determined.

## Calibrated uncertainty

The module runs a **coverage test**: it simulates many datasets from a
known truth, fits each, and checks that (say) nominal 95% intervals
actually contain the truth about 95% of the time. Uncertainty that does
not pass coverage is reported as uncalibrated rather than trusted.

## Relationship to the rest of R10

This is the general tool behind several specific refusals: a fitted
optical coefficient (see [NONLINEAR_OPTICS.md](NONLINEAR_OPTICS.md)), a
fitted decay in a resonator model, or any "the numbers fit, therefore the
model is true" argument. `inverse.py` is the earlier linear/simpler
companion; `nlinverse.py` is the nonlinear, uncertainty-aware version.

A tight fit is necessary but never sufficient. Identifiability and
coverage are the sufficiency tests, and both can fail silently without
this machinery.

PHYSICAL_VALIDATION_NOT_CLAIMED
