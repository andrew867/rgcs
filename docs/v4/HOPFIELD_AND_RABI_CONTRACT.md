# Hopfield coefficients and the Rabi/strong-coupling contract (C01)

Coverage: **A02**. Status: `REDUCED_ORDER_VALIDATED`.
Implementation: `rscs2_core.refmodels.polariton.hopfield_2x2`,
`strong_coupling_criterion`.

## Hopfield coefficients

For each polariton branch the eigenvector of the 2x2 Hamiltonian gives
the exciton and photon content:

    |X_i|^2 + |C_i|^2 = 1

The fractions are what make "polariton" meaningful rather than
decorative: a branch that is 99% photon is a photon with a small
exciton admixture, and calling it a polariton would overstate the
hybridization. `hopfield_2x2` returns both fractions per branch so a
caller cannot quote a splitting without also being able to see the
mixing.

## The strong-coupling contract

**A splitting is not strong coupling.** Two peaks separated by less
than their own widths are one peak. The C01 prompt states the rule
directly: *do not report strong coupling without comparing splitting to
losses*. The v4.2.0 implementation had no such check; the v4.2.1 audit
added `strong_coupling_criterion()` and this contract.

Two criteria are reported, because they disagree in the intermediate
regime and **the disagreement is the honest answer**:

| Criterion | Condition | Meaning |
|---|---|---|
| `standard` | Omega_R > \|gamma_x − gamma_c\|/2 | the complex eigenvalues split in their real parts (above the exceptional point) |
| `strict` | Omega_R > (gamma_x + gamma_c)/2 | the two peaks are separately resolvable |

Reported regime:

- `STRONG_COUPLING` — strict criterion met.
- `INTERMEDIATE_SPLIT_BUT_UNRESOLVED` — the real parts split, but the
  peaks are not resolvable. This is a real state of affairs and it gets
  its own name rather than being rounded to either neighbour.
- `WEAK_COUPLING` — below the exceptional point; no real splitting at
  all.

Cooperativity `C = Omega_R^2 / (gamma_x gamma_c)` is also returned. It
diverges for a lossless mode, which is correct and is not smoothed.

## Why two criteria rather than one

At zero detuning the eigenvalues of the non-Hermitian 2x2 split in the
real axis only when

    4 (Omega_R/2)^2 > ((gamma_x - gamma_c)/2)^2

which is the `standard` line — the exceptional point. But observing
that splitting requires the peaks to be narrower than their
separation, which is the `strict` line. Between the two, the physics
has split and the spectrometer has not. Reporting a single boolean
would hide exactly that regime.

`test_strong_coupling_matches_complex_eigenvalues` verifies the
criterion against the actual complex eigenvalues of `hopfield_2x2`
rather than trusting the rule of thumb.

## Failure conditions

- The criterion disagrees with the complex eigenvalue solution → the
  model is wrong (tested).
- A caller reports `STRONG_COUPLING` from a splitting alone, without
  linewidths → a documentation/QA defect, not a result.
