# NHT / HAL → RSCS Mapping

**Author:** Agent 04 (NHT/HAL and Hydrogenuine Memory Bridge). **Date:**
2026-07-14. Sources: Arisaka NHT/HAL (SRC-3-07), Vision (SRC-3-08),
Colloquium (SRC-3-09), verified page-1 in `references/source_registry.yaml`.

**Scientific posture.** The Arisaka proposal is preserved as source material
and translated into explicit RSCS candidate variables. It is **not** treated
as established consensus. Per `docs/EXCLUSION_MATRIX.md` (SRC-3-07/08): no
consciousness/brain/perception conclusion is imported into RGCS physics, and
nothing here claims quartz realizes memory or cognition. The value Agent 04
adds is a **typed, testable software abstraction**, not an endorsement.

## 1. The proposed mappings (reconstructed from the sources)

| Arisaka concept | Source location | Plain-language content |
|---|---|---|
| Space→phase (NHT) | SRC-3-07 p.10, holographic plane waves `Ψ_i(r,t)=A cos(k_i·r−ωt+φ)` | spatial position encoded in the phase of oriented traveling waves; a set of direction unit vectors {k_i} forms the frame |
| Retinotopy→phase/timing | SRC-3-07 §2.1–2.3 | 2D image reduced to 1D(space)+1D(time) by space-to-time conversion |
| Log-polar scaling→linear translation | SRC-3-08 p.? (V1 log-polar [Roll, Log Eccentricity]) | scale/eccentricity becomes an additive (linear) coordinate in a log-polar chart |
| Rotation/depth/location reaction-time predictions | SRC-3-08 (RT/CRT) | claimed latency ordering for mental rotation, depth, and location tasks |
| Phase-coded 3D coordinates | SRC-3-07 §3 (three brainwaves, 8+8+8 phases) | 3D position as a triple of carrier phases |
| HAL = 2D synaptic memory lattice | SRC-3-07 (HAL) | a ring-attractor lattice storing phase-encoded positions |
| MePMoS ordering | SRC-3-08 (Memory-Prediction-Motion-Sensing) | a processing-loop order: predict → sense → compare → update memory |
| Egocentric↔allocentric | SRC-3-08 (Ege/Body/Object-centric vs Allocentric) | sensing frame vs world/map frame, related by a frame transform |

## 2. RSCS translation (typed coordinates and operators)

| Arisaka concept | RSCS target | Class here |
|---|---|---|
| Space→phase encoding | `space_to_phase` **RSCS-O.3** (`φ = k·x − ωt`) | **HYP** |
| Oriented frame {k_i} | `Wavevector` **RSCS-C.5** (set of) | EST (as vectors) |
| Log-polar scale coordinate | `OrientationFrame` **RSCS-C.8** scale/rotation chart (cf. RGCS-M.32) | EST (as a chart) |
| Phase-coded 3D position | tuple of `PhaseCoordinate` **RSCS-C.3** | HYP (as a position code) |
| HAL 2D memory lattice | `MemoryLattice` **RSCS-C.14** + `store/recall` **RSCS-O.13** | **HYP, quarantined** |
| Egocentric / allocentric | two `SpatialCoordinate` **RSCS-C.1** + `frame_transform` **RSCS-O.1** | EST |
| MePMoS predict→sense→update | HG record predicted/observed + `update` **RSCS-O.16** | ENG |
| Whole memory record | `HydrogenuineRecord` **RSCS-C.15** + `store/replay/update` **RSCS-O.14/15/16** | **ENG** |

## 3. Classification firewall (Task 4)

Each component is placed in exactly one class; the boundaries are enforced by
`docs/EXCLUSION_MATRIX.md` and the `rscs_core` firewall.

**Established neuroscience (EST, cited — NOT our claim):**
- retinotopy in V1 and its approximately log-polar organization;
- ring attractors in the insect central complex (Lyu, Abbott & Maimon 2020);
- theta phase precession in the rodent hippocampus (Skaggs et al. 1996);
- place/grid cells. These are background; RSCS borrows their *coordinate
  forms*, not any claim about their sufficiency.

**Arisaka-specific hypotheses (HYP — to test, never presume):**
- that NHT space-to-phase is *the* mechanism of perception and memory;
- that HAL is the physical memory lattice;
- the specific reaction-time orderings for rotation/depth/location.
These map to RSCS-O.3, RSCS-C.14/O.13, and the RT claims — all HYP.

**Project-derived software abstractions (ENG — never evidence):**
- the Hydrogenuine memory record and its store/replay/update semantics
  (RSCS-C.15, RSCS-O.14/15/16). Useful as ordinary spatial memory; makes no
  scientific claim.

**Excluded entirely (no class, may not appear as an RGCS conclusion):**
- consciousness causation; that quartz implements cognition/memory;
  therapeutic effects; any brain conclusion transferred to physics by analogy.

## 4. Falsifiable software claims (Task 8) — H-15..H-19

These are **software** claims about the HG memory implementation, each with a
pre-registered failure condition. They test the *engineering* artifact, not
the neuroscience. Registered in `docs/CLAIM_REGISTER.md`; they are the
observable + failure condition the Agent 03 handoff required before the HYP
memory layer is used.

| ID | Claim (software) | Observable | Success threshold | Pre-registered FAILURE condition |
|---|---|---|---|---|
| H-15 | Retrieval quality: a stored record is retrievable by its allocentric key | exact-match recall rate over N stores | 100% for distinct keys | any distinct-key collision or lost record |
| H-16 | Transform consistency: replay into any frame preserves `allo == frame·ego` | `frame_consistent()` after replay | holds within 1e-6 mm | any inconsistency beyond tol (property test) |
| H-17 | Temporal continuity: event_time ordering is preserved and monotonic under append | sortedness of a replayed sequence | strictly ordered | any reordering/aliasing of timestamps |
| H-18 | Localization / replay fidelity: replay into the original frame reproduces the egocentric position; allocentric anchor invariant | ‖ego_replayed − ego‖, ‖allo_replayed − allo‖ | < 1e-9 mm | drift beyond tol (property test) |
| H-19 | Uncertainty calibration: after `update` with a sharper observation, reported σ does not increase without a flag | σ before/after update | σ_after ≤ σ_before or flagged | silent σ inflation |

H-16 and H-18 are already machine-tested
(`tests/property/test_rscs_hg_properties.py`); H-15/H-17/H-19 are testable at
the persistence layer Agent 08 will build (the store/replay/update primitives
are in place and deterministic).

## 5. Comparison against ordinary approaches (Task 7)

| Baseline | What it does | What the HG record adds |
|---|---|---|
| Vector DB / embeddings | nearest-neighbour recall in a flat latent space | typed allo/ego frames + a checked transform between them; provenance and uncertainty as first-class |
| Scene graph | hierarchy of transforms | event time + predicted/observed pairing (MePMoS loop) and a classification/provenance tag |
| SLAM keyframe | pose + landmarks + covariance | same pose/uncertainty spine, plus the explicit predicted-vs-observed update and a HYP-quarantined phase-encoding slot |
| Event sourcing | append-only event log | deterministic replay/update with frame re-referencing and calibration semantics |
| Recurrent state model | learned latent dynamics | no hidden learned state; every field is a named, unit-tagged RSCS coordinate, reproducible and inspectable |

**Verdict on "earns its complexity":** the HG record is justified only where
the typed allo/ego + checked transform + provenance/uncertainty prevent a
real error (frame confusion, silent σ inflation, un-provenanced recall). Where
a plain vector store suffices, use one; the HG record is for spatial memory
that must stay frame-consistent and auditable.

## 6. What is deliberately NOT built here

- No claim that the NHT encoding is correct; O.3 stays HYP.
- No HAL physical model; C.14/O.13 stay HYP and quarantined.
- No consciousness/perception model. Agent 04 delivers the typed bridge and
  the falsifiable software claims only. The RSCS Foundations memory chapter
  and the software/hardware implementation tranche (Task 10) are drafted for
  Agents 09 and 08 respectively; see `docs/HG_RSCS_MEMORY_ARCHITECTURE.md`.
