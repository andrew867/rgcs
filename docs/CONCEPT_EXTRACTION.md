# Concept Extraction — RGCS v3 / RSCS 1.0

Agent 02, Task 5. The orchestrator/ingestion brief names 13 concepts that
must be extracted explicitly from the sources. Each row states where the
concept lives (source + provenance ID in `references/equation_provenance.yaml`),
the reusable mathematical content, and the RSCS target — with the physical
interpretation held at its source (see `docs/EXCLUSION_MATRIX.md`).

| # | Concept | Primary source(s) | Provenance ID(s) | Reusable math | RSCS target (reserved) |
|---|---|---|---|---|---|
| 1 | Nonlinear state-dependent susceptibility | Wang SRC-3-04 | EP-04-02 | coupling = bias + χ⁽³⁾ term ∝ field spin (E×E*); state-dependent coupling coefficient | `coupling` + `state_preparation`: state-dependent coupling coordinate |
| 2 | Circular polarization / spin preparation | Wang SRC-3-04 | EP-04-02 | σ± circular basis; local spin E×E* as the state variable that sets the coupling | `state_preparation`: spin/polarization preparation coordinate |
| 3 | Acousto-optic mode conversion | Sohn SRC-3-01; Cheng SRC-3-02 | EP-01-01, EP-02-01/02 | phonon-mediated coupling between two optical modes; parametric coupling e^{±iΩt}; conversion via a coupling wave of wavevector q | `coupling`: parametric two-mode conversion operator |
| 4 | Symmetric / antisymmetric mode parity | Cheng SRC-3-02; Chao SRC-3-06 | EP-02-02, EP-06-02 | even/odd (|+⟩,|−⟩) supermode basis; amplitudes as normalized column vectors | `modes`: parity supermode basis |
| 5 | Phase matching and momentum matching | Cheng SRC-3-02 | EP-02-01 | k₊(ω₀)+q(Ω)=k₋(ω₀+Ω); Δq_pm linear in detuning; sinc² response | `coupling`/`propagation`: phase-matching predicate + mismatch coordinate |
| 6 | Group-delay balancing and dispersion | Cheng SRC-3-02 | EP-02-03 | diag delay matrix; fringe period set by group-delay difference; dispersion balancing to widen bandwidth | `propagation`: group-delay coordinate |
| 7 | Autler–Townes splitting and strong-coupling threshold | Sohn SRC-3-01 | EP-01-02 | two-Lorentzian split by Rabi frequency Gph; threshold Gph ≫ κ (Gph > √(κ₁κ₂)) | `observation`: lineshape; ties RGCS-M.24/M.27 |
| 8 | Critical coupling and insertion-loss / isolation metrics | Sohn SRC-3-01; Wang SRC-3-04; Zhang SRC-3-05 | EP-01-03, EP-04-03, EP-05-02 | κ_int = κ_ex critical point; IL = −10log T_f, isolation = −10log T_b; e^{−4k·Im(χ)L} | `observation`: coupling / IL / isolation metrics |
| 9 | Transfer matrices and modal beating | Cheng SRC-3-02; Chao SRC-3-06 | EP-02-02/03, EP-06-03 | unitary 2×2 T-matrices; cascade; L_beat = 2π/|β_e−β_o|; swap-on-reversal ⇒ nonreciprocity | `transforms`: cascadable T-matrix + beating-length coordinate |
| 10 | Fabrication path dependence (spiral-helix writing) | Lapointe SRC-3-03 | EP-03-01 | spiral-helix writing trajectory parameterization; process-history as a state variable | `provenance`/`state_preparation`: fabrication-path coordinate; feeds `rgcs_core.geometry.spiral` |
| 11 | Velocity-class / internal-state population coordinates | Zhang SRC-3-05 | EP-05-01 | population indexed by velocity/detuning class v = Δp/k; direction selectivity | `state_preparation`/`modes`: population-over-selection-coordinate |
| 12 | Signal fidelity and quantum-noise measurement principles | Zhang SRC-3-05 | EP-05-02 | normalized correlation g⁽²⁾ and ratio R as a fidelity/noise figure of merit (principle) | `observation`: fidelity / noise metric |
| 13 | NHT space-to-phase representation and HAL memory lattice | Arisaka SRC-3-07 (+ SRC-3-08) | EP-07-01/02, EP-08-01 | space→phase map Ψ_i(r,t)=A cos(k_i·r−ωt+φ); oriented-plane-wave frame {k_i}; ring-attractor lattice of phase/orientation states | `memory` (candidate, **HYP**); Agent 04 memory bridge |

## Classification note

Concepts 1–12 come from peer-reviewed / preprint physics and enter RSCS as
**mathematical templates** (EST/DER once re-derived with RSCS units and
tests). Concept 13 (NHT/HAL) is **SRC/HYP only**: it may seed candidate
coordinates for the Agent 04 memory bridge but carries no physical weight
and must acquire an observable, uncertainty, and pre-registered failure
condition before any downstream use — it may never be presumed true.

Every "RSCS target" above is a **reservation**, not an implemented
equation. An entry becomes real only when Agents 03/06 assign it a registry
ID (`RSCS-O.*`/`RSCS-C.*`), canonical units, a dimensional check, and a
machine test, per the migration rules in `docs/V2_TO_V3_MIGRATION_MAP.md` §4.
