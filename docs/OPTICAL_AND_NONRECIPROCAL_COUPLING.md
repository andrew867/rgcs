# Optical, Photon–Phonon, and Nonreciprocal Coupling (RSCS 1.0)

**Author:** Agent 06. **Date:** 2026-07-15. Builds on the RSCS backbone
(Agent 03), the crystal application (Agent 05), and the frozen source
provenance ledger (Agent 02). Governance: notation ledger §4c, DECISION_LOG
D6-001..D6-003. Machine registry: RSCS-C.16/C.17, RSCS-O.18..O.23.

**Binding posture (D6-003).** Every reference paper in this tranche achieves
nonreciprocity or photon–phonon conversion through an *active* ingredient —
a travelling acoustic drive, a χ⁽³⁾ optical nonlinearity, a Doppler-selected
atomic population, or a magneto-optic material. α-quartz is **not claimed to
have any of them**. A passive, lossless, unbiased quartz optical path is
reciprocal, and the pre-registered null expectation for every directional
observable is **no asymmetry**. What crosses from the sources into RSCS is
mathematics only, re-derived and machine-tested; the generated table
`docs/generated/OPTICAL_MECHANISM_COMPARISON.md` lists, per source, what is
adapted and what is forbidden.

## 1. Required models — implementation map

| Brief item | RSCS home | Status |
|---|---|---|
| 1. Optical carrier / envelope as separate coordinates | RSCS-C.16 `OpticalCarrier` (λ₀, envelope bandwidth) | implemented + tested |
| 2. Polarization: Stokes/Jones, circular, optical spin | RSCS-C.9 (existing Poincaré coordinate) + new `from_jones`/`jones` round-trip; spin s₃ = helicity | implemented + tested |
| 3. Refractive-index tensor, birefringence, photoelasticity | `rgcs_core.optics` (n_o/n_e, photoelastic p_ij, Δn = −½n³pS); photothermal as declared artifact channel; Raman/Brillouin framed §6 | implemented (core) / framed (Raman–Brillouin) |
| 4. Photon–phonon conversion with frequency/momentum/parity/overlap rules | RSCS-O.19 `mode_conversion` + `overlap_integral` | implemented + tested |
| 5. Group delay & dispersion ΔΦ(ω) expansion | RSCS-O.18 `dispersion_phase` / `dispersion_group_delay` | implemented + tested |
| 6. Coupled-mode / transfer matrices (sym/antisym) | RSCS-O.5/O.6 (Agent 03, reused) | pre-existing, regression-extended |
| 7. State-dependent susceptibility & preparation | RSCS-O.22 `state_dependent_susceptibility`; RSCS-O.9 (Agent 03) | implemented + tested |
| 8. ATS, avoided crossings, strong coupling, critical coupling | RSCS-O.20 `autler_townes_response`/`is_strong_coupling`; RSCS-O.21 `critical_coupling_transmission`; avoided crossings via frozen O.4 | implemented + tested |
| 9. Directional observables & reversal tests | RSCS-C.17 + RSCS-O.23; O.6 `reverse_cascade`; O.10 contrast dB; schema reversal pairs | implemented + tested |
| 10. Signal fidelity, phase/polarization preservation, noise, correlation | O.10 metrics (coherence, IL, isolation, contrast); correlation-figure principle adapted from EP-05-02; full measurement battery is Agent 07's | implemented (metrics) / Agent 07 (protocol) |

## 2. The operator set (all provenance-pinned)

- **RSCS-O.18 — dispersion phase.** ΔΦ(ω) = ΔΦ₀ + Δτ(ω−ω₀) + ½Δβ₂(ω−ω₀)²
  (rad); `dispersion_group_delay` is its exact ω-derivative. EST (Taylor
  expansion); EP-02-01/03. Balancing Δτ (O.8) widens any
  reciprocity-breaking band a *driven* coupler could have.
- **RSCS-O.19 — photon–phonon conversion.** All four selection rules of the
  acousto-optic template: frequency (ω_out = ω_in + Ω), momentum
  (η ∝ sinc²(Δq·L/2)), parity (the drive couples opposite-parity supermodes
  — must flip), overlap (η ∝ |⟨a|b⟩|²). Any rule fails → conversion
  blocked. DER; EP-02-01/02.
- **RSCS-O.20 — Autler–Townes.** Two-Lorentzian dressed response, peaks
  split by G; strong-coupling threshold G > √(κ₁κ₂). The regression test
  pins the mapping onto the frozen coupled-mode model: **G = 2π·(2g)**, so
  the ATS peaks sit exactly at the RGCS-M.24 hybrid frequencies f₀ ± g.
  EST; EP-01-02.
- **RSCS-O.21 — critical coupling.** T(Δ) = |1 − κ_ex/((κ_int+κ_ex)/2 −
  iΔ)|²; T(0) = 0 iff κ_int = κ_ex. Drive/readout coupling-budget
  definition for Agent 07. EST; EP-01-03.
- **RSCS-O.22 — state-dependent susceptibility.** χ_xy = χ⁽¹⁾B_z + χ⁽³⁾s_z
  (bias + field-spin term, EP-04-02) with directional metrics
  T_b/T_f = e^(−4k·Im χ·L), φ_nr = 2k·Re χ·L (EP-04-03). **Defaults to the
  reciprocal null**: both drivers zero ⇒ χ_xy = 0 ⇒ ratio 1, phase 0
  (machine-tested). DER.
- **RSCS-O.23 — directional propagation & beating.** β_f/β_b = β ± δβ
  (RSCS-C.17; δβ = 0 default) and L_beat = 2π/|β_e−β_o|. EST;
  EP-06-01/03.

## 3. Crystal-specific questions (brief §2) — answered

**Q1. Can an optical path through a selected facet address a measured
mode-overlap region?** Geometrically, **yes — established**.
`rgcs_core.optics.ray_to_target` gives the straight-ray path from an entry
facet point to any interior target with Snell entry handling, OPL, transit
time, and phase. The target menu keeps **geometric centre, predicted node,
and measured node as three distinct locations** (node menu, crystal
application §3); the schema forces the operator to record which is
addressed. Whether anything *measurable* happens there is a separate,
classified question (H-20).

**Q2. Which conventional mechanisms predict measurable responses?** Three,
with DER magnitude estimates from `rgcs_core.optics`:
1. *Photoelastic phase modulation*: Δn = −½n³pS. With p₁₁ = 0.16 and a
   typical acoustic strain S ~ 10⁻⁷: Δn ≈ −3×10⁻⁸ — small but standard
   interferometric territory over a ~100 mm path (ΔΦ ~ 3×10⁻² rad at
   633 nm).
2. *Birefringence modulation*: strain-induced rotation of the index
   ellipsoid → polarization modulation between crossed polarizers.
3. *Photothermal absorption*: bulk heating from absorbed beam power — an
   **artifact channel**, bounded by the matched-power off-node control.
Quartz's acousto-optic figure of merit M₂ = n⁶p²/(ρv³) ≈ 10⁻¹⁵ s³/kg
(computed with the Agent 05 anisotropic X-axis speed — cross-layer
consistency test) is 100–1000× below dedicated AO materials: an honest
sensitivity bound, not a defect.

**Q3. What controls distinguish path geometry from absorption/heating?**
The schema's control enum is binding: `heating_matched_power_off_node`
(same absorbed power, non-overlap path), `glass_isotropic_control` (no
birefringence/photoelastic anisotropy), `no_drive_baseline`,
`dummy_crystal`, `rotated_crystal`. A geometric-path effect must vanish
when the path misses the overlap region at matched power; a heating effect
follows absorbed power wherever the path goes.

**Q4. Does reversal invert any observable asymmetry?** Pre-registered
expectation: **there is no asymmetry to invert** (D6-003). The reversal
battery (beam direction, circular polarization σ⁺/σ⁻, coil phase, crystal
orientation, sham timing) is encoded in the schema; the transfer-matrix
regression tests show the algebra of both outcomes (symmetric cascade →
reversal-invariant; parity-asymmetric cascade → swap signature). An
asymmetry that survives the battery would be a major HYP finding (H-21/
H-23) and would still need a conventional-mechanism audit before any class
upgrade.

## 4. New falsifiable claims (CLAIM_REGISTER H-20..H-23)

| ID | Class | Claim | Failure condition |
|---|---|---|---|
| H-20 | HYP | An intensity-modulated probe addressing the measured overlap region shows a photoelastic sideband at the acoustic frequency, magnitude within 10× of the DER estimate | no sideband above noise floor at predicted magnitude with drive verified on |
| H-21 | HYP | Any directional (fwd/bwd) optical asymmetry reverses sign under beam reversal | asymmetry absent (expected null, D6-003) or fails to reverse ⇒ artifact |
| H-22 | ENG | The control battery separates path-geometry effects from heating at matched absorbed power | controls cannot separate ⇒ optical branch results unusable |
| H-23 | HYP | Circular-polarization (σ⁺ vs σ⁻) dependence of any response at low power | no dependence (expected null in transparent quartz) |

## 5. Experiment schema

`experiments/schemas/optical_probe.schema.json` (registered in
`validate.py`; example `experiments/templates/optical_probe.example.json`).
Enforces: laser class 1/1M/2/2M/3R only (power ≤ 5 mW; Class 3B/4 not
representable), interlock metadata, direction + reversal-pair id, the
control enum of §3, mechanism predictions with classification, and
hypothesis-row links. No human exposure or therapeutic protocol exists or
is representable.

## 6. Framed for downstream agents

- **Raman/Brillouin channels** (brief item 3): standard inelastic-scattering
  bookkeeping is DER; quartz Brillouin shift for a 633 nm probe against a
  ~6 km/s acoustic wave is ~25 GHz — outside the v3 measurement plan's
  bandwidth. Framed for the Crystal Application monograph (Agent 09);
  no operator claimed.
- **Electro-optics** (quartz is piezoelectric, class 32; r₁₁ small):
  documented as a candidate cross-coupling channel for the monograph.
- **Measurement protocol, timing, and correlation battery** → Agent 07
  (uses O.10 metrics, O.21 coupling budgets, the schema, and H-20..H-23).
- **Optical-path and phase-delay desktop views** → Agent 08 (consumes
  `ray_to_target` output and O.18 phases).
- **Manuscript chapter** → Agent 09 (`manuscripts/rscs_foundations` optical
  chapter + Crystal Application optical section), from this document and
  the generated comparison table.

## Deliverable status

- **Implemented & tested:** C.16/C.17 coordinates, Jones↔Stokes on C.9,
  O.18–O.23 operators, `rgcs_core.optics` (constants, ray model,
  photoelastic/M₂ estimates), optical experiment schema + example,
  generated mechanism comparison table (determinism-pinned).
- **Registered:** notation ledger §4c; registry 40 ids; DECISION_LOG
  D6-001..003; claims H-20..H-23.
- **Excluded (binding):** all device performance values; acousto-optic ATS,
  self-induced nonreciprocity, TMOKE, Faraday isolation as quartz
  properties.
