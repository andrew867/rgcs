# Zenodo Metadata — v4.x releases (copy-ready)

Per docs/DOI_RELEASE_GUIDE.md: the GitHub–Zenodo integration archives
each published release automatically; verify the metadata on the new
Zenodo record, publish there, then add the new version DOI to
CITATION.cff in a follow-up commit. **Update a Zenodo record only
after its GitHub release is valid.**

## v4.1.0 (CURRENT — pending human verification)

| Field | Value |
|---|---|
| Title | RGCS v4.1.0 — RSCS 2.0: capability-aware coupled-field platform with uncertainty-aware Eye Consensus, reduced-order reference systems, and quarantined source hypotheses |
| Creators | Green, Andrew (me@andrewgreen.ca) |
| Resource type | Software |
| License | MIT |
| Abstract | use the `abstract` block of CITATION.cff verbatim |
| Keywords | reproducible-research, research-software, resonance, quartz, elastodynamics, finite-element-method, piezoelectricity, anisotropy, multiphysics, provenance, falsification, uncertainty |
| Related identifiers | `isSupplementTo` → https://github.com/andrew867/rgcs/releases/tag/v4.1.0 ; `isNewVersionOf` → 10.5281/zenodo.21387947 (v3.0.1) |
| Version | 4.1.0 |

Required wording carried into the record (do not soften): all results
are computational; the historical eye is a Source claim; no
experimental confirmation exists; the eye engine's canonical verdict
is **UNCERTAINTY_OVERLAPS_CONVENTIONAL_NODE** — the candidate at
z = 102.240 mm sits 3.906 mm from the nearest conventional station
with a 3.08 mm localization halfwidth; the implemented conventional
model may explain the result within uncertainty, it is not established
that it does. Missing capabilities are typed
MECHANISM_NOT_IMPLEMENTED_FOR_MATERIAL results, never claims of
physical nonexistence.

## v4.0.0 (HISTORICAL — superseded interpretation)

The original v4.0.0 block described the verdict as
CONVENTIONAL_NODE_FOUND under the retired 4 mm proximity rule
(defect V4C-D-001). If a v4.0.0 Zenodo record is ever verified, its
description may keep that historical wording ONLY with an explicit
"superseded by v4.1.0" note; do not create it fresh with the old
wording. Version 4.0.0; release link
https://github.com/andrew867/rgcs/releases/tag/v4.0.0.
