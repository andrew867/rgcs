# Polariton reference model (Agent C01)

Coverage: **A01, A02, A03**. Gate: **G06** (analytic limits).
Status: `REDUCED_ORDER_VALIDATED`.
Implementation: [`rscs2_core/refmodels/polariton.py`](../../rscs2_core/refmodels/polariton.py).
Tests: [`tests/v4/test_v4x_polariton_interfaces.py`](../../tests/v4/test_v4x_polariton_interfaces.py),
[`tests/v4/test_v4x_depth_metrology_bvd_apparatus.py`](../../tests/v4/test_v4x_depth_metrology_bvd_apparatus.py).

## What this is, and what it is not

This is a **separate reference system**. It models exciton-photon
polaritons in a planar cavity — a well-established regime in
semiconductor and van der Waals materials. It is **not** a model of
alpha quartz, and nothing in it is imported into quartz computation.

Alpha quartz has no registered `exciton_frenkel` capability, so
`polariton_dispersion()` called with a quartz material id returns
`MECHANISM_NOT_IMPLEMENTED_FOR_MATERIAL` rather than a number. That
refusal is the point of the capability firewall: an analogy in another
material is not evidence about this one.

A missing capability is **not** a claim that the mechanism cannot
exist in quartz. It is a statement that this programme has not
registered the material-specific evidence that would license it.

## The model

Cavity photon dispersion versus in-plane angle:

    E_c(theta) = E_c0 / sqrt(1 - sin^2(theta)/n_eff^2)

Two-mode non-Hermitian Hamiltonian (exciton X, cavity photon C), with
linewidths entering as imaginary parts:

    H = [ E_x - i gamma_x/2      Omega_R/2        ]
        [ Omega_R/2              E_c - i gamma_c/2 ]

The complex eigenvalues give the upper and lower polariton energies
and their linewidths; the eigenvector moduli give the Hopfield
fractions, normalized so |X|^2 + |C|^2 = 1 per branch.

Units: all energies in eV, angles in degrees at the API boundary and
radians internally.

## Validated limits (G06)

| Limit | Expected | Tested |
|---|---|---|
| Zero coupling | branches reduce to the bare E_x, E_c | yes |
| Large detuning | branches asymptote to the bare modes; Hopfield fractions → 0/1 | yes |
| Exact resonance | splitting = Omega_R | yes |
| Hopfield sum | |X|^2 + |C|^2 = 1 per branch | yes |
| Hermitian limit | gamma = 0 → real eigenvalues | yes |
| Quartz | refuses to compute (capability floor) | yes |

## Boundaries (from the C01 prompt)

- This is a coupled-oscillator model. It is **not** a Bethe-Salpeter
  calculation, and it must not be described as one.
- No condensation claim is made. Nothing here computes a
  thermodynamic phase.
- **No strong-coupling claim without comparing the splitting to the
  losses** — see [HOPFIELD_AND_RABI_CONTRACT.md](HOPFIELD_AND_RABI_CONTRACT.md).
  This rule is enforced by `strong_coupling_criterion()`, which the
  v4.2.1 audit added after finding the criterion was required by the
  prompt but absent from the code.

## Sources

`SRC-V4-06` (van der Waals excitons, FULL_TEXT_LOCAL). Adapted
equations carry their provenance in the source registry; the Hopfield
transformation itself is a standard result (EST).
