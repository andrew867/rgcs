# V4 Quantum-Statistical Metacrystal Example (Agent M7)

`rscs2_core/refmodels/metacrystal.py` (RGCS-V4-EQ-010; material
reference.metacrystal, plasmonic/statistical REFERENCE ONLY).

Typed input g2(0) with uncertainty; MetaAtomGeometry (size, count,
orientation, arrangement, bounded coupling in [0,1]) with a
transparent registered band (lo,hi) = (1-0.5c, 2+c); the transfer map
is a declared ENG partial-pull rule: identity at c=0, otherwise a
sigmoid pull whose output PROVABLY lies between the input and the band
(asserted in code, tested). Fixtures: coherent g2=1, thermal 2,
subthermal 1.4, superthermal 2.6 (independently constructed —
source figure values unavailable locally, DV4C-003). Deterministic,
monotone in input; first-order uncertainty propagation; inverse query
reports ALL matching couplings with a nonuniqueness flag; bulk quartz
is mechanically NOT_APPLICABLE (gate G3) and every envelope carries
the "NOT bulk quartz / no microscopic plasmonics" assumption.

Honesty note: an early internal assertion claimed strict band
membership; the sigmoid pull can legitimately stop between input and
band edge — the declared bound was corrected to the partial-pull rule
rather than tuning the function to hide it.
