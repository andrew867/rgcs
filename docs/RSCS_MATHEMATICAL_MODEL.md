# RSCS 1.0 — Mathematical Model

**Author:** Agent 03 (RSCS Mathematical Core and Conservative Extension).
**Date:** 2026-07-14. **Status:** implemented in `rscs_core` (schema 1).
Binding authorities: `docs/RSCS_NOTATION_LEDGER.md` (frozen symbols/ids),
`references/equation_provenance.yaml` (adapted-equation provenance),
`docs/ADAPTATION_MATRIX.md` / `docs/EXCLUSION_MATRIX.md` (allow/forbid),
`docs/NOTATION_AND_UNITS.md` (frozen v2 units). RSCS extends v2; it never
redefines a frozen symbol or an RGCS-M.* equation.

## 1. What RSCS is (and is not)

RSCS is a **typed coordinate/state-space** for resonant systems: it names,
with units and manifolds, the quantities a resonant experiment carries —
spatial location and reference frame, phase, frequency, mode identity,
orientation and scale, modal occupancy, propagation and group delay,
coupling, internal-medium/preparation state, uncertainty, provenance, and
observations. It is a *bookkeeping and transformation* layer, not a new
physics.

**Classification of the construction itself: DER/ENG.** RSCS earns its
complexity only where the typing prevents a real error (unit mixing,
flat-vector ambiguity, frame confusion, SRC→EST laundering) or where an
operator generalizes several v2/source special cases into one tested object.
No claim is made that nature "uses" RSCS; that universal claim would be HYP
and would require predictive superiority over a simpler model, which is not
asserted.

### 1.1 Physical space vs. abstract state coordinates

RSCS keeps **physical space** (RSCS-C.1 `x`, mm, in E³) strictly separate
from **abstract state coordinates** (phase C.3, frequency C.4, modal state
C.7, …). Distances in the two are never collapsed into one scalar without
declared weights and units (§7). Two states that are spatially distant may be
phase-close; that is a feature to be represented, not averaged away.

## 2. The RSCS state space

The clean formalism is a **typed product / fibre state**, not a single
manifold and not a flat vector:

    S_RSCS  =  B  x  F  x  I  x  M

- **Base space B** — continuous physical/spectral coordinates: space `x`
  (C.1), time `t` (C.2), phase `φ` (C.3, on S¹), angular frequency `ω`
  (C.4), wavevector `k` (C.5).
- **Fibre / internal state F** — orientation frame `ρ` (C.8, SO(3)×{±}),
  polarization/spin `σ_c` (C.9, on S²), selection coordinate `s` (C.10),
  group delay `τ_g` (C.11).
- **Discrete mode indices M** — mode-index tuples `n` (C.6, in ℤⁿ) and the
  complex modal state `ψ` (C.7, in ℂⁿ). `ψ` is the occupancy/analytic-signal
  coordinate; amplitude |ψ| and phase arg ψ are carried together, reported
  separately (KOS-03).
- **Uncertainty & provenance metadata I** — uncertainty `u` (C.12, wrapping
  the frozen v2 `UncertainValue`) and provenance tag `p` (C.13); the
  quarantined memory-lattice coordinate `m` (C.14, HYP) also lives here.

Why a product/fibre rather than one manifold or one vector: the components
have *different topologies and units* (S¹ phase, ℤ indices, SO(3) frames, ℝ₊
positive reals). Forcing them into a flat float vector loses the topology and
re-introduces exactly the flat-vector ambiguity Quality Gate 5 forbids.
Differential geometry beyond "product of typed manifolds with declared
charts" is deliberately not imposed — no connection or curvature is claimed
on S_RSCS.

### 2.1 Comparison with standard coordinate systems

| Formalism | What RSCS borrows | Why RSCS is not just this |
|---|---|---|
| Cartesian / Minkowski | E³ base space (C.1), time (C.2) | RSCS adds fibre/mode/metadata; no spacetime metric claim |
| Hamiltonian phase space | phase/amplitude pairing in `ψ` | RSCS carries units, provenance, uncertainty as first-class |
| Hilbert-space / Bloch | complex `ψ` (C.7), polarization on S² (C.9) | RSCS states are classical bookkeeping, not quantum amplitudes; no Born rule |
| State-space / latent models | typed product state | components have declared units/manifolds, not a bag of latents |
| Normal-mode coordinates | mode indices (C.6), coupling eigenbasis (O.4/O.5) | RSCS keeps provenance + uncertainty attached to every mode |
| Fibre bundles | base × fibre split (B × F) | used descriptively; no connection/holonomy asserted |

## 3. Operator signatures

The 13 operators (`RSCS-O.1..13`, `docs/RSCS_OPERATOR_REGISTRY.md`) act on
these typed coordinates. Signatures (in → out):

- **O.1 frame transform** `𝒯`: (C.1, C.8) → C.1. Rigid `x' = R x`; invertible.
- **O.2 time↔frequency** `ℱ`: real record → complex analytic signal.
  Delegates to frozen v2 RGCS-M.55 (exact).
- **O.3 space→phase** `𝒮₂`: (C.1, C.5, ω, t) → C.3. `φ = k·x − ωt`. **HYP.**
- **O.4 coupling** `𝒦`: (frequencies, g-matrix) → {H (Hz), K (rad/s),
  hybrids}. **K = i·2π·g, anti-Hermitian** (frozen).
- **O.5 parity basis** `𝒫`: C.7(2) → C.7(2). Fixed unitary even/odd change,
  self-inverse.
- **O.6 transfer-matrix cascade** `𝕄`: sequence of 2×2 → 2×2; `reverse_cascade`
  gives the swap-on-reversal nonreciprocity signature.
- **O.7 phase-matching** `𝒬`: (k₊, q, k₋) → {Δq, matched}.
- **O.8 group-delay balance** `𝒟`: C.11 → C.11 (re-reference to zero mean).
- **O.9 state preparation** `𝒜`: (C.9, C.10) → C.7. Occupancy-conserving.
- **O.10 observation** `𝒪`: C.7/segment → (coherence, IL, isolation,
  contrast). Coherence delegates to frozen v2 RGCS-M.56.
- **O.11 uncertainty propagation** `𝒰`: (C.12, factor) → C.12. Delegates to v2.
- **O.12 provenance propagation** `𝒫r`: (op, out-class, *C.13) → C.13.
  Enforces the firewall (§6).
- **O.13 memory store/recall** `ℋ`: (C.7, index) → C.14; recall → phases.
  **HYP, quarantined.**

## 4. Composition laws

- **Frame transforms** compose by rotation product with handedness product
  (`OrientationFrame.compose`); the identity frame is the unit; every frame
  has an inverse. `𝒯(𝒯(x, ρ), ρ⁻¹) = x` (round-trip identity, tested).
- **Transfer matrices** compose by ordered matrix product,
  `cascade([T₁,…,Tₙ]) = Tₙ…T₁`; associative (tested). Lossless ⇒ unitary.
- **Parity basis** is an involution: `𝒫∘𝒫 = id`.
- **Provenance** composes by the class-capping rule (§6): the output class is
  the operator's declared class, checked against the weakest input.

## 5. State preparation and observation maps

- **Preparation** `𝒜` (O.9) maps a spin state (helicity h) and a selection
  class (population P) to a two-mode occupancy `ψ` with
  `|ψ_up|² = (1+h)/2·P`, `|ψ_dn|² = (1−h)/2·P`, so total occupancy `= P`
  (conserved; tested). Adapted from EP-04-02/EP-05-01; no atomic physics
  imported.
- **Observation** `𝒪` (O.10) projects a state to scalar observables:
  autocorrelation coherence (frozen v2 RGCS-M.56), and the log-ratio metrics
  `IL = −10 log₁₀ T_f`, `isolation = −10 log₁₀ T_b`,
  `contrast = 10 log₁₀(T_f/T_b)`. Definitions only; device performance
  numbers stay with their sources (EXCLUSION_MATRIX).

## 6. Coupling algebra (the keystone)

The time-domain coupling generator is **anti-Hermitian**,
`K_nm = i·2π·g_nm` (QA-D-04, frozen). The frequency-domain Hermitian matrix
is `H = diag(f) + g` (Hz). The two are linked by the exact evolution

    dψ/dt = i·2π·H·ψ   ⇒   ψ(t) = exp(i·2π·H·t)·ψ(0),

so `exp(i·2π·H·t)` is **unitary** (H Hermitian): occupancy `Σ|ψ|²` is
conserved (no growth). The eigenvalues of `H` are the hybrid frequencies
`f₀ ± g` for a degenerate pair, i.e. a **2g Hz frequency splitting** with a
`1/(4g)` amplitude beat. This reproduces RGCS-M.23/24/28 exactly (Conservative
Extension, §8) and is machine-tested. The forbidden real-symmetric
`K = π·g` instead splits **growth rates** (norm blows up) and is guarded
against by a contrast regression test.

## 7. Distance / similarity metrics

RSCS does **not** define a single global metric on S_RSCS. Distances are
component-wise and unit-carrying:
- spatial distance in mm on C.1 (Euclidean);
- phase distance on S¹ as the wrapped geodesic `min(|Δφ|, 2π−|Δφ|)`;
- modal distance as a norm on C.7 (ℂⁿ);
- coherence/PLV as similarity on time series (O.10).
Any combined "state distance" must declare explicit weights and units for
each component; collapsing physical distance and state distance into one
arbitrary scalar is prohibited (§1.1).

## 8. Conservative Extension Property (the binding contract)

Define the embedding **ι: X_RGCS → X_RSCS** (value-preserving; e.g. a Hz
frequency → `AngularFrequency`, an `UncertainValue` → `Uncertainty`, a real
record → itself). For every RSCS operator O_RSCS that generalizes a frozen v2
equation O_RGCS:

    O_RSCS(ι(x)) = ι(O_RGCS(x))    within rtol 1e-9, atol 1e-12

over the frozen v2 test domain (`rscs_core/units.py`). This is the **RSCS
Conservative Extension Property (CEP)**. It is implemented in
`rscs_core/embedding/` and enforced by
`tests/regression/test_rscs_conservative_extension.py`:

| RSCS operator | reproduces | evidence |
|---|---|---|
| O.4 coupling | RGCS-M.23/24/28 (hybrids, 2g splitting) | `test_two_mode_cep`, `test_n_mode_cep`, golden G-08 |
| O.2 time↔freq | RGCS-M.55 (analytic signal) | `test_analytic_signal_cep` (exact; delegates) |
| O.10 observation | RGCS-M.56 (coherence) | `test_coherence_cep` (exact; delegates) |
| O.11 uncertainty | RGCS-M.10/11 | `test_uncertainty_cep` |

## 9. Invariants, identifiability, gauge, singularities, missing data

- **Invariants.** Unitary operators (O.4 evolution, O.5, lossless O.6)
  conserve modal occupancy `Σ|ψ|²`. Frame transforms preserve spatial norm.
  Group-delay *imbalance* is invariant under O.8's common-offset removal.
- **Identifiability.** Only combinations identifiable from data are exposed:
  e.g. from mode spacing only the spectral slope `κ_χ` is identifiable (v2
  RGCS-M.14), and the coupling magnitude `|K| = 2π g` is what a splitting
  measurement constrains — the sign/phase of K beyond anti-Hermitian is a
  gauge choice.
- **Gauge / reference choices.** The world frame (C.8 identity), the phase
  origin (C.3 chart start), and the campaign observable unit X are gauge
  choices; results are reported so a gauge change is explicit.
- **Singularities.** Polar amplitude/phase is singular at |ψ|→0; RSCS carries
  the complex `ψ` (never a bare angle) so the singular chart is avoided,
  matching the v2 RGCS-M.46 choice. Frame inverses use the transpose (always
  defined for orthogonal R).
- **Missing data.** Non-finite inputs are rejected at construction
  (NaN/inf), never silently propagated; JSON serialization uses the v2
  null-not-NaN rule.
- **Uncertainty propagation boundary.** Uncertainty is propagated only where
  a declared rule exists (exact scale, reciprocal scale, quadrature of
  independent relatives, O.11); RSCS does not invent covariance it cannot
  justify.

## 10. Failure conditions

An RSCS computation fails loudly (raises) when: a coordinate is non-finite or
wrong-shape; a frame is not orthogonal; a coupling matrix is not symmetric or
has a nonzero diagonal; an operator's input type/size is wrong; the claim
firewall would be violated (weak→strong, §6); or the quarantined memory
coordinate is built without `acknowledge_hypothesis`. The CEP tests fail if
any generalized operator diverges from its frozen v2 counterpart beyond
tolerance.

## 11. Why RSCS earns its complexity (the key test)

For each implemented area, the simpler baseline and RSCS's added value:

| Area | Simpler baseline | What RSCS adds |
|---|---|---|
| Coupling | call `rgcs_core.coupled_modes` directly | one operator that returns BOTH the Hz Hermitian and the frozen anti-Hermitian rad/s form with a machine-checked `K†=−K` and CEP to v2 |
| Coordinates | pass floats around | unit/finiteness/frame validation at construction; NaN can't enter |
| Provenance | a comment | a runtime firewall that blocks SRC/HYP → EST/DER laundering |
| Memory (NHT) | write the formula | a quarantined HYP type that cannot be used in EST/DER paths by accident |
| Uncertainty | bare floats | every scale/reciprocal carries the v2 relative-σ, CEP-verified |

Where RSCS would add only ceremony (e.g. a trivial identity wrapper), it is
kept thin and delegates to the frozen v2 implementation so the CEP holds by
construction (O.2, O.10, O.11).
