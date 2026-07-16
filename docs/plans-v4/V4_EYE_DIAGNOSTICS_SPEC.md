# V4 Eye Diagnostics Spec — `rscs2_core.diagnostics` (RSCS2-D.*)

**Status:** PLANNING. **The historical "eye" is SRC. Any computed
candidate is DER (a field diagnostic) or HYP (a falsifiable claim),
NEVER EST (DV4-010).** No unique eye coordinate is asserted without the
full robustness + uncertainty battery; the framework must be able to
return **NULL** ("no stable candidate").

## 1. The registered diagnostic family (RSCS2-D.1..15)

Each is a scalar/vector field on the mesh, classified, with a defined
"candidate = local extremum/feature of this field" rule.

| id | Diagnostic | Field | Class | Requires |
|---|---|---|---|---|
| D.1 | displacement amplitude | \|u(x)\| | DER | elastic modes |
| D.2 | strain-energy density | ½ ε:C:ε | DER | elastic modes |
| D.3 | kinetic-energy density | ½ ρω²\|u\|² | DER | elastic modes |
| D.4 | piezo charge / electric-energy density | ½ E·D | DER | L3 piezo |
| D.5 | optical intensity + path sensitivity | I(x), ∂φ/∂(perturb) | DER | L5 optical |
| D.6 | normalized drive-mode overlap | ⟨φ_drive, φ_n⟩/norms | DER | drive projection |
| D.7 | cross-modal overlap | ⟨φ_m, φ_n⟩ region density | DER | ≥2 modes |
| D.8 | local phase coherence | windowed phase order of the field | DER | complex field |
| D.9 | phase singularity / topological charge | winding of arg(field) where valid | DER | complex field + validity guard |
| D.10 | displacement vorticity / circulation | ∇×u, ∮u·dl | DER | vector field |
| D.11 | Poynting circulation | ∇×⟨E×H⟩ where an EM soln exists | DER | L5 EM |
| D.12 | boundary-perturbation sensitivity | Δ(candidate)/Δ(BC) | DER | perturbation sweep |
| D.13 | mesh persistence | candidate stability across refinement ℓ | DER | convergence sweep |
| D.14 | uncertainty persistence | candidate stability across MC samples | DER | RSCS2-U.1 |
| D.15 | cross-channel agreement | overlap of candidates from independent physics | DER | ≥2 channels |

**Guards (fail-loud):** D.9/D.10/D.11 only report where the field is
mathematically valid (nonzero magnitude, defined phase); a circulation
value is a *field feature*, explicitly **not** a physical vortex
(exclusion). D.9 topological charge is reported only on a validity mask.

## 2. Eye Consensus Functional (RSCS2-D.0, DER/ENG — never EST)

A registered, weighted aggregation of the normalized diagnostics into a
single field E(x) ∈ [0,1], with:
- **explicit, versioned weights** (an ENG choice, logged; not "the" eye);
- a **candidate-region extraction** (thresholded connected components),
  never a single false-precision point;
- a **stability/confidence score** per region from D.12/D.13/D.14/D.15;
- a **NULL verdict** when no region clears the persistence + agreement
  thresholds.

The functional is classified **DER/ENG until experimentally correlated**;
it can never be reported as an Established physical structure.

## 3. Mandatory comparisons (every eye run emits all)

- vs **geometric centre** of the body;
- vs **conventional modal nodes and antinodes** (from the eigenmodes);
- vs the **v3 RGCS node prior** (`rgcs_core.geometry.nodes`) and the v3
  node-menu definitions (H-07/H-24..H-28);
- a **taxonomy label** for every candidate: mathematical field feature /
  numerical artifact / mesh artifact / boundary-condition artifact /
  conventional node-or-antinode / coupled-mode overlap region / robust
  cross-physics candidate / historical source interpretation. A
  candidate is only called "robust cross-physics candidate" when it
  survives D.13 (mesh) **and** D.14 (uncertainty) **and** D.15
  (cross-channel) — otherwise it wears the weaker label honestly.

## 4. Robustness battery (the gate between DER and HYP)

A candidate may be elevated from "field feature" (DER) to a
**pre-registered HYP (H-31, see claim register)** only if it:
1. persists across mesh refinement (D.13) within a tolerance;
2. persists across the uncertainty ensemble (D.14);
3. agrees across ≥2 independent physical channels (D.15);
4. is stable under boundary perturbation (D.12);
5. is distinguishable from the geometric centre and conventional
   nodes/antinodes (§3).
Failing any → the run reports the candidate at its honest weaker class,
or **NULL**. This is the numerical analogue of the Agent-14
measured-node-supersedes rule.

## 5. Outputs

Field map(s), candidate regions with confidence, the four comparisons,
the taxonomy label per candidate, uncertainty envelopes, and a verdict
∈ {robust-candidate (HYP H-31) / weak-feature (DER) / NULL}. All
classification chips on every value; provenance graph to the diagnostics
and their inputs.

## 6. Tests

RSCS2-V.10 (asymmetric geometry → candidate shifts predictably);
NULL-model test (a mode with no distinguished region returns NULL);
artifact-injection tests (a deliberate mesh sliver / BC change must be
labelled artifact, not candidate); each diagnostic's unit + dimensional
test; consensus-functional weight-versioning test; cross-channel
agreement on a synthetic case with a known shared feature; guard tests
(D.9/D.10/D.11 refuse invalid regions); exclusion lint (no "vortex"/
"eye-is-real" language emitted).
