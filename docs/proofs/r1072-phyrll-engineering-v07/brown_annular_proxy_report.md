# Brown Annular Proxy report (v0.7 upgrade)

Data: `brown_annular_proxy_data.json`. The proxy remains an
energy-density direction measure — **no force function exists in either
proxy module, and a test walks both namespaces to keep it that way.**

## The upgrade

v0.6 compared centered / off-center / binary-masked. v0.7 adds the
**weighted mask** — graded per-sector drive applied as a real boundary
condition (the ring electrode potential is v_ring · w_k per sector, with
the open sector genuinely open, not grounded).

## Results (41-grid, identical geometry across cases)

| Configuration | Asymmetry | Ratio to physical |
|---|---|---|
| centered symmetric | **0.00000** | — |
| physical displacement | 0.32572 | 1.000 (yardstick) |
| binary mask (4 blanks) | 0.02941 | **0.090** |
| **weighted mask (graded)** | **0.15057** | **0.462** |

## Reading

The v0.6 result stood at: electronic displacement is real but ~11× weaker
than physical displacement. The v0.7 graded drive closes most of that
gap — **46% of a literal geometric offset, a 5.1× gain over binary
blanking**, with no moving parts and the 33-active lock intact.

This agrees independently with the ring optimizer (same ordering:
graded ≫ binary), which is the useful cross-check: two different models —
a field solve and a mode sum — rank the same drive families the same way.

Centered stays exactly zero, as it must. Every output remains
`MODEL_OUTPUT` / `PRIOR_ART_ANALOGUE`; the asymmetry scalar is a
direction of field energy, not a thrust, and the ratio is the honest
yardstick against the one configuration a bench could also realise
mechanically.
