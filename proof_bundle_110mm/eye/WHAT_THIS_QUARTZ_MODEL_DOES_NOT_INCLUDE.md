# What the Canonical Quartz Model Does and Does Not Claim

Binding scientific-scope statement for the canonical 110 mm
alpha-quartz application (adopted verbatim as programme authority,
V4C corrective integration, 2026-07-16; supersedes the earlier
exclusion-only text of this file).

This document defines the limits of the current RGCS implementation.
It does not define the limits of alpha quartz, nature, or future RGCS
discoveries.

A missing capability means RGCS v4 does not currently possess a
validated quantitative model for that mechanism in alpha quartz. It
must not be interpreted as proof that the mechanism is physically
impossible, absent, irrelevant, or incapable of producing an
observable effect.

The capability firewall exists to prevent fabricated numerical results
and unsupported physical claims. It must never suppress, discard,
relabel, or explain away an anomalous result merely because the
current model does not contain a recognized mechanism for it.

## Validated alpha-quartz model

The canonical alpha-quartz application currently includes validated or
tested support for: anisotropic elastic response; crystal-axis and
tensor-frame transformations; modal and static finite-element
analysis; piezoelectric coupling; dielectric response used by the
implemented piezoelectric model; mechanical displacement, strain,
stress, energy, rotation, curl, and circulation diagnostics; geometric
and modal symmetry analysis; mesh, boundary, material, and
numerical-sensitivity studies; registered optical quantities only
where an optical field has actually been solved; calibration and
uncertainty reporting; Eye Consensus diagnostic aggregation; anomaly
localization and comparison with conventional nodes, antinodes,
fixtures, boundaries, and geometric priors.

These capabilities define what RGCS can presently calculate with
declared confidence. They do not define every physical interaction
that may occur in quartz.

## Mechanisms without a validated quartz implementation

RGCS v4 does not currently contain a validated alpha-quartz solver
for: magnetic order; magnon modes; localized or collective spin
dynamics; spin-orbit state blocks; spin-phonon coupling; spin-texture
chirality; excitonic states or exciton-magnon coupling; magnetic
toroidal moments; ferrotoroidic order; dynamical magnetoelectric
tensors; inverse optical magnetoelectric domain writing;
quantum-statistical metacrystal response; microscopic plasmonic
near-field response; microscopic proton-tunnelling dynamics;
chiral-phonon Zeeman splitting; microscopic quantum coherence or
quantum-information dynamics; any proposed historical
spacetime-torsion field.

Requests for quantitative results from these unimplemented quartz
mechanisms must not return invented values or numerical zero. The
correct software responses are:

- `MECHANISM_NOT_IMPLEMENTED_FOR_MATERIAL` (reason code), when no
  validated quartz model exists;
- `INTERFACE_ONLY`, when a typed interface exists but no physical
  quartz implementation exists;
- `SOURCE_HYPOTHESIS`, when the mechanism arises from speculative,
  historical, or independent-source material;
- `CANDIDATE_NEW_COUPLING`, when observed or computed behavior cannot
  be explained adequately by the currently implemented conventional
  model;
- `NOT_APPLICABLE`, only when the term is mathematically or physically
  undefined for the selected model, not merely because RGCS lacks an
  implementation.

`MECHANISM_NOT_IMPLEMENTED_FOR_MATERIAL` must never be presented
publicly as proof of physical nonexistence.

## Discovery and anomaly policy

RGCS must preserve unexpected results even when no implemented
mechanism explains them. When a stable or repeatable feature appears
outside the predictions of the current model, RGCS must report: the
exact calculated coordinate; the localization uncertainty; mesh
spacing and interpolation uncertainty; convergence across mesh levels;
sensitivity to geometry, material constants, boundary conditions, and
solver tolerances; the nearest conventional node, antinode, boundary
feature, fixture feature, and geometric prior; the exact separation
from each comparator; whether uncertainty intervals overlap; whether
the feature persists under perturbation; which diagnostic families
support it; which conventional explanations remain viable; which
existing model classes do not explain it; the minimum new coupling or
hypothesis required to model it.

RGCS must not discard a feature because it lacks a pre-existing
category. RGCS must not move an anomalous coordinate onto the nearest
conventional coordinate. RGCS must not classify a distinct coordinate
as conventional solely because it lies within an arbitrary millimetre
threshold. RGCS must not require a proposed microscopic mechanism
before reporting a reproducible macroscopic anomaly. Discovery begins
with a result that the current model cannot fully explain.

## Conventional-node comparison

A candidate may be classified as an exact conventional-node
coincidence only when its coordinate is coincident with the
conventional node within the declared numerical localization
tolerance. Physical proximity and numerical coincidence are different
concepts.

The Eye report always preserves: candidate coordinate; comparator
coordinate; signed and absolute separation; localization confidence
interval; comparator uncertainty; mesh resolution; convergence shift;
classification rule; raw diagnostic evidence.

Required classifications (implemented in
`rscs2_core.eye.node_coincidence_comparison`):

- `EXACT_CONVENTIONAL_NODE_COINCIDENCE`, when the coordinates coincide
  within numerical tolerance;
- `UNCERTAINTY_OVERLAPS_CONVENTIONAL_NODE`, when the candidate and
  comparator uncertainty intervals overlap;
- `NEAR_CONVENTIONAL_NODE_BUT_DISTINCT`, when the coordinates are
  close but their intervals do not overlap;
- `DISTINCT_FROM_CONVENTIONAL_NODE`, when a resolved separation
  exists;
- `CONVENTIONAL_MODEL_INSUFFICIENT`, when the feature persists but no
  tested conventional comparator accounts for it;
- `NO_STABLE_CANDIDATE`, when the feature does not survive the
  required stability and perturbation gates.

A separation of 3.94 mm must be reported as 3.94 mm. It must not be
rounded conceptually to zero or absorbed into a 4 mm
conventional-node threshold. (This corrects defect V4C-D-001; the
published v4.0.0 records used the old rule and remain frozen history.)

## Eye Consensus posture

Eye Consensus is a diagnostic and anomaly-classification system. It is
not a mechanism for forcing every result into a conventional or null
category. Unsupported mechanisms are not counted as positive evidence.
However, their absence from the current software must not count as
evidence against an anomaly. Optical diagnostics without a solved
optical field remain `INTERFACE_ONLY`. Magnetic, excitonic,
ferrotoroidic, microscopic-tunnelling, and other unimplemented quartz
mechanisms remain unevaluated, not disproved.

The consensus system may return: `NO_STABLE_CANDIDATE`;
`EXACT_CONVENTIONAL_NODE_COINCIDENCE`;
`UNCERTAINTY_OVERLAPS_CONVENTIONAL_NODE`;
`NEAR_CONVENTIONAL_NODE_BUT_DISTINCT`; `DISTINCT_STABLE_CANDIDATE`;
`CONVENTIONAL_MODEL_INSUFFICIENT`; `CANDIDATE_NEW_COUPLING`;
`INSUFFICIENT_RESOLUTION`; `CONTRADICTORY_DIAGNOSTICS`.

A positive discovery verdict requires repeatability, localization,
uncertainty control, perturbation stability, and failure of tested
conventional explanations. It does not require RGCS to already know
the final microscopic mechanism. A stable eye is not required for
release. A stable unexplained candidate must not be erased to simplify
the release.

## Separate reference systems

The reduced-order reference systems (exciton-magnon, avoided
crossings, dynamical magnetoelectric response, metacrystal statistics,
LiNiPO4 domain writing, MnF2 optical annealing, nonlinear
antiferromagnetic trajectories, phonon-controlled exchange, chiral
phonons, dressed spins) remain separate reference systems. They must
not silently inherit alpha-quartz identity or parameters. However,
they MAY be used as comparison models, hypothesis generators, or
candidate mathematical structures when an alpha-quartz anomaly cannot
be explained by the validated quartz model — explicitly classified as
cross-system analogy, candidate mathematical correspondence,
reduced-order hypothesis, proposed experiment, or rejected comparison.
Similarity is not proof, but prohibition of comparison would also
prevent discovery.

## Physics not implemented anywhere in RGCS v4

Density-functional theory; Bethe-Salpeter calculations; ab-initio spin
dynamics; quantum field theory; microscopic quantum electrodynamics;
microscopic plasmonic simulation; full microscopic proton-tunnelling
dynamics; full uniaxial double-refraction walk-off; generation of
nonclassical photon statistics; photon creation from classical
boundary switching; a complete microscopic theory of anomalous Eye
Consensus candidates. These limitations restrict the strength of RGCS
conclusions. They do not justify replacing unresolved observations
with conventional explanations.

## Required interpretation

RGCS v4 distinguishes four different statements that must never be
collapsed into one another:

1. The implemented conventional model explains the result.
2. The implemented conventional model may explain the result within
   uncertainty.
3. The implemented conventional model does not explain the result.
4. RGCS lacks enough resolution or physics to determine the
   explanation.

The correct scientific response to an unexplained, repeatable result
is not to invent a mechanism and not to suppress the result. It is to
preserve the result, quantify its uncertainty, test conventional
explanations, identify missing model classes, and state exactly what
experiment or computation would discriminate among them.
