# T03 — Microtubule and cross-scale coherence bridge

Coverage: **C015–C019, C033**. Gate: **G33**. Lane: **quarantined**.
Implementation: `consciousness_lane.reduced_models.microtubule_threshold`.

## The causal threshold

Any claim that subcellular coherence influences neural dynamics must
clear:

    tau_c * eta_phi * K_cross > theta_neural_bias

| Symbol | Meaning | Unit |
|---|---|---|
| `tau_c` | coherence lifetime | s |
| `eta_phi` | phase-transfer efficiency to a neural variable | 1/s scale |
| `K_cross` | cross-scale coupling gain | dimensionless |
| `theta_neural_bias` | the bias a synaptic event already produces | reference 1 |

The threshold exists so the hypothesis **can lose**. A proposal that
cannot be outcompeted by an ordinary synaptic event is not a mechanism
for anything.

## Where the numbers actually land

At the reference thermal decoherence estimate for a microtubule at
310 K (Tegmark-type, τ_c ≈ 1e-13 s), with generous η_φ and K_cross of
1, the product is ~1e-13 against a threshold of 1. **It fails by
thirteen orders of magnitude.**

`microtubule_threshold(1e-13, 1.0, 1.0)` → `clears_threshold: False`.

The counter-argument (Hameroff/Penrose-adjacent) is that shielding,
ordered water, or topological protection extend τ_c. That is a real
hypothesis, and the threshold accommodates it: supply a larger τ_c and
the product rises. `microtubule_threshold(1e-3, 1e4, 1.0)` clears.

**But the status never upgrades.** Even when the product clears, the
function returns `SOURCE_HYPOTHESIS` / `HYP`, because a favourable
parameter *guess* is not a measurement. Tested:
`test_microtubule_threshold_honest`.

> A hypothesis clears this threshold only with **measured** τ_c, η_φ,
> and K_cross in a biological preparation. None exist.

## C017 — ordered water and aromatic electrons

Retained as `SOURCE_HYPOTHESIS`. **Falsified if** no coherent
transition is observed in the declared band in vivo. The proposed
mechanisms are chemically specific and therefore testable in
principle — which is more than most of this lane can say.

## C018 — Hz/kHz/MHz/GHz/THz resonance claims

The claimed resonance frequencies span **twelve orders of magnitude**.
A mechanism that predicts everything predicts nothing. Registered with
the look-elsewhere requirement: **falsified if** the claimed resonances
are absent above the corrected noise floor.

## C019 — fractal time crystal

`SOURCE_HYPOTHESIS`. **Falsified if** no subharmonic response persists
without drive — which is the actual definition of a time crystal, and
the reason the claim is checkable rather than decorative.

## C033 — entanglement in biology

`SOURCE_HYPOTHESIS`. **Falsified if** no CHSH-type violation is
demonstrated in any biological preparation. None has been.
Correlation is not entanglement; a Bell test is the standard, and warm
wet tissue is the hardest possible place to run one.

## Boundaries

- **Do not claim microtubules generate or receive consciousness.**
- **Do not treat controversial studies as consensus.** The
  source-quality hierarchy separates replicated results from single
  papers from conference abstracts.
- Conventional cellular explanations (ordinary biochemistry, ion
  channels, network dynamics) are the null and are not displaced by an
  unexplained observation.
