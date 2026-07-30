# R10.11 Convexity and Edge Audit

Fitted node set (`R10_11_NODE_LAYOUT.csv`, de-regularized up to 41.3°
from the rigid mesh at four nodes):

- **Convexity**: all 12 nodes lie on their convex hull; all 20 flat
  faces outward-consistent. PASS.
- **Shared-edge continuity**: every lifted edge node is a function of
  its two endpoint nodes only; numerically verified over all 30 edges
  at machine precision (0 mismatches). PASS.
- **Orientation**: 0 reversals among 20,480 depth-5 and 81,920
  depth-6 terminal facets (sign measured against each root face's
  handedness under the fixed corner convention). PASS.
- **Node lifting**: single-valued, outward (rho=1 spherical control
  profile; radial gravity-line rendering; star-shaped trivially).
  PASS.
- **Inverse**: exact hierarchical ray-descent lookup; 60/60 random
  address→point→address round trips exact to depth 11. PASS.
- **Root/phase**: Wilkes face-0 centroid residual 1e-6°; SAA phase
  vertex (rigid vertex 7, the vertex nearest the SAA direction) moved
  0.0° — both locks held.

No stored displacement field exists: the entire operator is 12 unit
vectors + the deterministic subdivision/lift rule.
