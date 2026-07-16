# Run log — Agent M9 + V4C-D-001 corrective integration

Base `54f5e18`. Owned: rscs2_core/eye_votes.py, eye/proofbundle
updates, docs/v4/WHAT_THIS_QUARTZ_MODEL_DOES_NOT_INCLUDE.md,
docs/v4/EYE_NODE_COINCIDENCE_CORRECTION.md, tests.

M9 first pass: vote layer (5 tests), applicability map, bundle vote
records — bundle regenerated (verdict then CONVENTIONAL_NODE_FOUND
under the OLD rule; that run preserved at docs/v4/proof/
M9-precorrection/).

USER CORRECTION (V4C-D-001, P1): the 4 mm node-proximity rule is
scientifically unacceptable. Corrective integration performed:
- proximity threshold removed; uncertainty-aware
  node_coincidence_comparison (numerical tol 1e-6 mm; interval
  overlap; NEAR/DISTINCT with exact separation always preserved);
- classification moved AFTER persistence gates;
- verdict vocabulary extended; vote layer + bundle vocabulary updated;
- evidence artifacts: node_coincidence.json + frequency_sensitivity
  .json + rewritten conventional_node_comparison.csv columns;
- reason codes: MECHANISM_NOT_IMPLEMENTED_FOR_MATERIAL with
  non-nonexistence note; scope doc replaced with the binding
  does-and-does-not-claim statement;
- regression battery test_v4c_node_coincidence.py (7 tests incl. the
  mandated 3.94 mm / 0.1 mm / exact / coarse-mesh cases);
- full suite 216 passed; bundle regenerated 115/115; QA audit 19/19.

RECLASSIFICATION (result preserved): candidate (-0.295, -0.205,
102.240) mm; nearest station (-0.447, 0.774, 106.018) mm; separation
3.906 mm EXACT; mesh res 3.076 mm; convergence shift 0.353 mm; cloud
rms 0.032 mm -> UNCERTAINTY_OVERLAPS_CONVENTIONAL_NODE ("may explain
within uncertainty", NOT "explains"). Discriminating computation:
clmax ~4 mm meshes. v4.0.0 tag/records frozen; correction ships in
v4.1.0.
