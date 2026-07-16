# RGCS v4.1.0 Release Notes

All results are computational; no experimental confirmation exists;
the historical eye is a Source claim; CPU float64 remains the
numerical authority; the nominal (110.000000 mm) and ideal
(110.037667410714… mm) geometries are distinct. The v4.0.0 release
and its records are frozen history — v4.1.0 supersedes their
interpretation without rewriting them.

## The correction that headlines this release (V4C-D-001)

v4.0.0's Eye Consensus classified any candidate within ~4 mm of a
conventional node/antinode station as "conventional node explains
result". That physical-proximity threshold was scientifically
unacceptable (it conceptually rounded a resolved 3.9 mm separation to
zero) and is REMOVED. The corrected rule
(`rscs2_core.eye.node_coincidence_comparison`) separates numerical
coincidence from physical proximity:

- `EXACT_CONVENTIONAL_NODE_COINCIDENCE` — only within the declared
  numerical tolerance (1e-6 mm);
- `UNCERTAINTY_OVERLAPS_CONVENTIONAL_NODE` — localization intervals
  overlap the comparator;
- `NEAR_CONVENTIONAL_NODE_BUT_DISTINCT` / `DISTINCT_FROM_CONVENTIONAL_NODE`
  — resolved separations, reported at their exact values;
- plus `CONVENTIONAL_MODEL_INSUFFICIENT`, `CANDIDATE_NEW_COUPLING`,
  `INSUFFICIENT_RESOLUTION`, `CONTRADICTORY_DIAGNOSTICS` in the
  verdict vocabulary.

**Canonical 110 mm result (preserved, reclassified):** candidate at
(−0.295, −0.205, 102.240) mm; nearest conventional station
(−0.447, 0.774, 106.018) mm; separation **3.906 mm** (exact);
localization halfwidth 3.08 mm (mesh-resolution dominated);
convergence shift between mesh levels 0.353 mm; material-draw cloud
rms 0.032 mm; per-mode frequency sensitivity recorded in the bundle.
Verdict: **UNCERTAINTY_OVERLAPS_CONVENTIONAL_NODE** — the implemented
conventional model MAY explain the result within uncertainty; it is
no longer asserted that it DOES. Finer meshes would discriminate.

## Platform additions (RSCS 2.0 completion)

- **Provenance layer:** source registry (20 records; primary papers
  metadata-only with verified citations — Toyoda 10.1038/
  s41563-026-02608-4, Schlauderer Nature 569, Afanasiev Nat. Mater.
  2021), equation ledger with classification ceilings that make
  SRC/HYP → EST/DER laundering raise mechanically.
- **Capability firewall:** 16 material/reference records; alpha quartz
  keeps exactly its validated capabilities; unsupported mechanisms
  return typed `MECHANISM_NOT_IMPLEMENTED_FOR_MATERIAL` results (null
  value + reason) — never numeric zeros, and never presented as proof
  of physical nonexistence. Coupling graph with operator-capability
  floors (closes the lying-edge laundering attack, V4C-D-003).
- **Typed quantity registry:** mechanical twist, curve torsion,
  circulation, optical SAM/OAM/transverse spin, chiral-phonon angular
  momentum, spin-texture chirality, magnetic toroidal moment, and the
  historical spacetime-torsion claim (SOURCE_HYPOTHESIS, no solver)
  are DISTINCT types; asserting identity raises.
- **Validated diagnostics:** Saint-Venant torsion benchmark vs FEM;
  Frenet-Serret fixtures; Stokes-checked circulation; canonical
  optical angular momentum with a real-field vortex guard.
- **Reduced-order reference systems** (all capability-gated, never
  quartz): exciton-magnon modulation, avoided crossing (anchors the
  frozen v3 two-mode model at 1e-12), block Hamiltonian, dressed spin,
  dynamic magnetoelectric tensor (KK-checked), metacrystal g2
  transfer, LiNiPO4 IOME (k/T reversal signs, polarization-invariance
  vs IFE/thermal comparators, held-out saturation-law comparison),
  MnF2 comparator, nonlinear AFM switching (π phase slip), phonon-
  controlled exchange with a direct-vs-indirect mechanism classifier.
- **Dynamic boundaries + symmetry lowering** with closed work-energy
  ledgers; **deterministic calibration/inverse design** with immutable
  hash-chained observations and a policy guard (optimizers cannot
  touch classification/provenance); **optical channel ablation**
  (mechanisms respond only to declared channels — enforced
  structurally); **quarantined FDT + source-lore adapters** (triple-
  layered import firewall, dimensional/algebraic/empirical audits,
  six pre-registered discriminators, no Toyoda-confirmation).
- **Binding scope statement:** `docs/v4/
  WHAT_THIS_QUARTZ_MODEL_DOES_NOT_INCLUDE.md` — what is validated,
  what is not implemented, the discovery/anomaly policy, and the rule
  that missing capability is never evidence of physical nonexistence.

## QA

Defects V4C-D-001 (node-threshold rule, user-identified), V4C-D-002
(NaN/inf leakage into IOME envelopes), V4C-D-003 (capability
laundering via lying edges) — all closed with regression tests.
Adversarial QA final verdict: no open P0/P1.

## Limitations (honest)

New-wave source PDFs were not locally supplied: primary-paper numeric
comparisons are marked SOURCE_VALUE_COMPARISON_PENDING_LOCAL_SOURCE
(DV4C-003). The Eye localization uncertainty is mesh-resolution
dominated (±3.08 mm at the shipped mesh levels); the 3.906 mm
separation question is open until finer meshes resolve it. D9/D10
phase diagnostics still require driven complex responses. No DFT/BSE/
ab-initio/QFT/microscopic solvers anywhere. iGPU evidence remains the
v4.0.0 measured Iris Xe / i5-1135G7 results (unchanged hardware).
