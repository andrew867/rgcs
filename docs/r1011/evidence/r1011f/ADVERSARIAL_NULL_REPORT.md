# R10.11F Adversarial and Null Report

## Exact-T edge inference destruction (the main result)
Under BOTH registered exact operators, every B0-matched landmark edge misses its target by 305-1268 km cross-track (limit 150 km). All four edge inferences are REJECTED; the preregistered ratio family is UNEVALUABLE on exact geometry. The coarse suggestive ratios were artifacts of the regular unfitted solid.

## Null-ratio base rate (log-odds space)
With the 11-member family (incl. reciprocals + retrospective 6/5), a uniform random log-odds in [0.8, 1.25] lands within 0.2 percent of SOME member with probability 0.094. With >=12 coarse readings examined, the family-wise expectation of at least one such hit is O(1.1) - the coarse observations carry no significance on their own.

## Other batteries
- endpoint permutation / edge reversal: canonical reciprocal handling; unchanged.
- symmetry-equivalent relabeling: Hungarian assignment is labeling-free.
- spherical vs chord: the flat-face model IS chord-based; its landmark edges miss by >1000 km either way.
- geodetic vs geocentric: shifts <=20 km; cannot rescue 300-1300 km misses.
- precision perturbation (+/-0.05 deg landmarks): no usable/unusable classification changes.
- T warp version mismatch: V1 vs flat-face give DIFFERENT degenerate odds - edge inferences are operator-dependent, another rejection ground.
- selection leakage: no geographic anchor selected anything; L0 wins lexicographically by default.
