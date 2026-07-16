# Reference System Audit (Agent 13 Role B)

All four conventional reference systems reproduce INDEPENDENT physics
with quantified error (G15–G17):

| system | reference | error |
|---|---|---|
| Cantilever (G16) | Euler–Bernoulli / Timoshenko closed forms | <0.5% converged EB; +0.03% thick-beam z-bend |
| Cube Lamé mode | exact ν-independent f = v_s/(√2 a) (Demarest 1971) | +0.03–0.05%, ν-independence confirmed |
| Acoustic cavity (G17) | exact rigid-wall Helmholtz spectrum | ≤1.7e-4 incl. exactly-3-fold cube degeneracy |
| Tuning fork (G15) | classical pair structure + FROZEN two-mode model | sym/antisym + CMR 0.26; V.9 splitting within 6.4% |

Audit specifics:

- The fork coupling REGIME was diagnosed, not assumed: the free fork
  is strongly coupled (2699 Hz split via base flexure — mode ordering
  x-anti, y-anti, x-sym, y-sym); the weak-coupling pair (S₀ = 8.70 Hz)
  requires the base-clamped configuration. The naive "modes 0/1 are
  the pair" assumption is FALSE and the tests identify the pair by
  signed tip displacement instead — this was itself a caught-and-fixed
  error during Agent 10 (documented in REFERENCE_SYSTEM_COMPARISON.md).
- V.9 avoided crossing uses the FROZEN `coupled_two_mode`
  (RSCS-O.4/RGCS-M.24) with the Rayleigh tip-mass detuning map; error
  grows smoothly 0→6.4% with detuning, attributable to the single-mode
  Rayleigh map — the frozen model itself is not strained.
- Cavity degeneracy is reported, not averaged (3-fold cube mode within
  1e-3 spread at the exact frequency).
- All values recomputed live in every proof-bundle build
  (benchmarks/*.csv) except tuning_fork.csv (copied, declared —
  regeneration needs ~6 fork solves).

No defects found.
