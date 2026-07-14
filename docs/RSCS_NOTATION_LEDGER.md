# RSCS 1.0 — Frozen Notation Ledger

**Author:** Agent 02 (Source & Reference Ingestion), extending the v2
authority. **Date:** 2026-07-14. **Status: FROZEN — GATE for Agents 03–08.**

## 0. Relationship to the v2 notation authority

`docs/NOTATION_AND_UNITS.md` (v2, FROZEN) remains the single authority for
all RGCS crystal-application symbols (`L`, `v_L`, `χ`, `R_χ`, `g`, `Ω_j`,
`Ω_s`, `ϑ_mix`, `z(t)`, `𝒞_w`, …) and for the collision resolutions in its
§1. **This ledger does not redefine, re-letter, or re-unit any v2 symbol**
(orchestrator integration rule; migration rule §4.4). It adds the RSCS
coordinate/operator layer *above* the crystal application. Where an RSCS
object generalizes a v2 quantity, the v2 symbol is the concrete instance
and is cited, not replaced.

Two namespaces, both append-only and immutable once used:
- **Registry IDs.** `RSCS-C.*` = coordinate/schema definitions;
  `RSCS-O.*` = operators. `RGCS-M.1…61` stay frozen; `RSCS-M.*` is
  **reserved and unused** to avoid confusion.
- **Symbols.** New RSCS base letters/decorations registered in §2–§4 below.
  Any symbol not registered here or in the v2 authority is non-compliant.

## 1. Policy (inherited + RSCS additions)

1. Inherits all four v2 policies (single-owner base letters; subscript
   rule; canonical units with unit-suffixed code identifiers; classification
   attaches to a *definition*).
2. **Typed coordinates, no bare vectors.** Every RSCS state is a *typed
   coordinate record*, never an untyped flat array (Quality Gate 5). A
   coordinate names each component, its unit, and its manifold/topology
   (ℝ, ℝ₊, S¹ periodic, ℤ index, enum). Transforms declare domain, codomain,
   inverse (or explicit non-invertibility), and singularity handling.
3. **Operators carry units and a test.** An `RSCS-O.*` operator states input
   and output coordinate types, the unit action, its classification, source
   provenance (for adapted math, the `EP-*` ID), and at least one machine
   test (round-trip, consistency vs. the v2 instance, or dimensional).
4. **Provenance is a coordinate.** Every RSCS state may carry a provenance
   tag (source id, classification, fabrication-path); it travels with the
   data, it is not metadata bolted on later.
5. **SRC/HYP quarantine.** Coordinates seeded from NHT/HAL (`memory` layer)
   are HYP until they have an observable, uncertainty, and a pre-registered
   failure condition. They may not be presumed physical.

## 2. RSCS coordinate primitives (`RSCS-C.*`)

Canonical units follow v2: Hz for frequency, rad/s for angular frequency,
rad for phase, mm for geometry lengths, m for wave-formula lengths, s for
time. Manifold column: ℝ real line, ℝ₊ positive reals, S¹ = periodic
[0,2π), 𝕋ⁿ n-torus, ℤ integer index, 𝔼³ Euclidean 3-space.

| ID | Symbol | Name | Components (unit) | Manifold | Class | Notes / v2 instance |
|---|---|---|---|---|---|---|
| RSCS-C.1 | `𝐱` | spatial coordinate | (x,y,z) mm | 𝔼³ | EST | crystal-axis frame of `NOTATION §2.6` is a chart of this |
| RSCS-C.2 | `t` | time | t (s) | ℝ | EST | shared with v2 |
| RSCS-C.3 | `φ` | phase coordinate | φ (rad) | S¹ | EST | generalizes v2 `χ` (compact phase) and `r_φ` |
| RSCS-C.4 | `ω` | angular frequency | ω (rad/s) | ℝ | EST | `ω = 2πf`; f in Hz per v2 |
| RSCS-C.5 | `𝐤` | wavevector / oriented frame element | 𝐤 (rad/mm) | ℝ³ | EST | source basis {k_i} (EP-07-01); phase-matching (EP-02-01) |
| RSCS-C.6 | `𝐧` | mode index tuple | integers | ℤⁿ | EST | v2 `N` (axial), `n` (compact), parity `P` are instances |
| RSCS-C.7 | `𝛙` | modal state (occupancy) | complex amplitudes (√units·rad-normalized) | ℂⁿ | EST/DER | generalizes v2 analytic signal `z(t)` and modal amplitudes |
| RSCS-C.8 | `𝛒` | orientation / reference frame | rotation (SO(3)) + handedness | SO(3)×{±} | EST | scale-rotation (EP-08-01); v2 `λ_s` eigenstructure is a chart |
| RSCS-C.9 | `𝛔_c` | polarization/spin state | Stokes/σ± (dimensionless) | S² (Poincaré) | EST | circular preparation (EP-04-02, concept 2) |
| RSCS-C.10 | `𝐬` | selection coordinate | class label (unit of the selector) | ℝ or ℤ | DER | velocity/detuning class v=Δp/k (EP-05-01, concept 11) |
| RSCS-C.11 | `𝛕_g` | group-delay coordinate | τ_g (s) per mode | ℝⁿ | DER | group-delay balancing (EP-02-03, concept 6) |
| RSCS-C.12 | `𝐮` | uncertainty descriptor | (value, std, dist-type) | — | DER | generalizes v2 `UncertainValue`; carried with any coordinate |
| RSCS-C.13 | `𝐩` | provenance tag | (source_id, class∈{EST,DER,HYP,SRC,ENG}, path) | enum tuple | EST | fabrication path (EP-03-01); travels with the state |
| RSCS-C.14 | `𝐦` | memory-lattice coordinate | (orientation index, carrier phase φ) | 𝕋ⁿ | **HYP** | NHT/HAL candidate (EP-07-01/02); quarantined per §1.5 |

## 3. RSCS operators (`RSCS-O.*`)

Every operator lists input→output coordinate types. "v2 consistency" means
the operator must reproduce the named `RGCS-M.*` result on the v2 domain
(the required machine test).

| ID | Symbol | Name | Type (in → out) | Class | Provenance | Required test |
|---|---|---|---|---|---|---|
| RSCS-O.1 | `𝒯` | frame transform | (𝐱,𝛒) → (𝐱′) | EST | v2 geometry; EP-08-01 | round-trip 𝒯⁻¹𝒯 = id; singularity handling |
| RSCS-O.2 | `ℱ` | time↔frequency map | 𝛙(t) → 𝛙(ω) | EST | v2 analytic signal (M.55) | Parseval / inverse round-trip |
| RSCS-O.3 | `𝒮₂` | space→phase map | (𝐱,𝐤,ω,t) → φ | HYP | EP-07-01 (SRC/HYP) | defined only with an observable + failure condition |
| RSCS-O.4 | `𝒦` | mode-coupling operator | 𝛙 → 𝛙 (matrix) | EST/DER | EP-01-01, EP-04-01 | **anti-Hermitian convention frozen: K = i·2πg** (QA-D-04); reproduce RGCS-M.46 |
| RSCS-O.5 | `𝒫` | parity/supermode basis change | 𝛙 → 𝛙 (even/odd) | EST | EP-02-02, EP-06-02 | unitary; reproduce RGCS-M.23–25 two-mode eigenbasis |
| RSCS-O.6 | `𝕄` | transfer-matrix cascade | 𝛙 → 𝛙 (∏ Tᵢ) | EST | EP-02-02/03, EP-06-03 | unitarity where lossless; swap-on-reversal ⇒ nonreciprocity |
| RSCS-O.7 | `𝒬` | phase-matching predicate | (𝐤,ω,q) → {matched, Δq} | EST | EP-02-01 | Δq→0 at match; sinc² response |
| RSCS-O.8 | `𝒟` | group-delay/dispersion balance | (𝕄,𝛕_g) → 𝛕_g | DER | EP-02-03 | balanced Δτ_g widens reciprocity-break band |
| RSCS-O.9 | `𝒜` | state preparation | (𝛔_c,𝐬) → 𝛙 | DER | EP-04-02, EP-05-01 | occupancy conserved; maps to v2 drive families |
| RSCS-O.10 | `𝒪` | observation / metric | 𝛙 → (IL, isolation, 𝒞, R) | EST | EP-01-03, EP-04-03, EP-05-02 | reproduce v2 coherence `𝒞_w` (M.56); dB defs |
| RSCS-O.11 | `𝒰` | uncertainty propagation | (op,𝐮) → 𝐮 | DER | v2 uncertainty.py | matches v2 propagation on shared inputs |
| RSCS-O.12 | `𝒫r` | provenance propagation | (op,𝐩) → 𝐩 | EST | v2 provenance | class never silently upgraded (EST≥DER≥HYP≥SRC ordering preserved) |
| RSCS-O.13 | `ℋ` | memory-lattice store/recall | (𝛙,𝐦) → 𝐦 | **HYP** | EP-07-02 (SRC/HYP) | quarantined; Agent 04 must attach observable + failure condition |

## 4. Reserved decorations and collision guards (RSCS layer)

- **Bold upright** = coordinate record or operator matrix (`𝐱`, `𝕄`);
  *italic* = scalar component (`φ`, `ω`). Script capitals = operators
  (`𝒯`,`ℱ`,`𝒦`,…).
- `𝐤` (RSCS oriented-frame wavevector, rad/mm) does **not** collide with v2
  `κ_χ` (compact spectral slope, Hz) or `κ` decay rates; different letters,
  different units, kept distinct.
- `𝐬` (selection coordinate) does **not** reuse v2 `S` (engineering merit
  score) or `s_D` (diameter scale factor); registered as bold `𝐬`.
- `φ` (RSCS phase coordinate) is the umbrella; v2 `χ` (compact phase) and
  `r_φ` (phase residue) remain the specific instances and keep their v2
  definitions.
- `𝒦` coupling **must** use the frozen anti-Hermitian sign K = i·2πg. Any
  operator introducing a coupling with a different sign/units is a
  compliance failure and requires a DECISION_LOG entry + INCONSISTENCY row,
  exactly as QA-D-04 was handled.
- Anything an agent needs that is not here goes through an append-only edit
  to this ledger **before** first use, logged in `docs/DECISION_LOG.md`.

## 5. Gate status

This ledger + `references/source_registry.yaml` +
`references/equation_provenance.yaml` + the adaptation/exclusion matrices
constitute the frozen **notation, source ledger, and provenance** required
by the orchestrator before Agents 03–08 may run in parallel. **GATE: OPEN.**
