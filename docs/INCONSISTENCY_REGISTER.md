# RGCS v2 — Inconsistency Register

**Author:** Sub-Agent 01 (Source Ingestion and Evidence Ledger)
**Date:** 2026-07-14

## Header: assumptions

1. Scope: existing v2 manuscript (TEX), prototype core (`rgcs_v2/core.py`), app.py, RGCS v2 workbook (WB2), timing calculator (WB3), v5 JH-audit workbook (WB5), both SCAD files, README.
2. Severity: **S1** = wrong result or contradictory definitions in shipped artifacts; **S2** = misleading/unsupported claim or hidden assumption that will bite downstream; **S3** = defect of hygiene, duplication or documentation.
3. All numeric checks reproduced with Python (v = 6310 m/s, f₀ = 4096 Hz reference state).

---

### D-01 (S1) — Two contradictory "geometry node" definitions
`core.py::crystal_geometry` returns `geometry_balance_node_mm = (hm·(L−hf)+hf·hm)/(hf+hm)`, which algebraically simplifies to **hm·L/(hf+hm)** = 70.806 mm for the N=5 default (L=154.0527, hf=17.4154, hm=14.8128). WB5 Sheet 13's geometry-weighted estimator is `(hm·wf+(L−hf)·wm)/(wf+wm)` = 75.725 mm (w=1,1); metric center = 77.026 mm. Same name, different formula, ~5 mm discrepancy; the core formula also has no documented derivation and its numerator term `hf·hm` looks like a transcription error of `(L−hf)·wm`.
**Consequence:** any drive-placement or marker generated from core disagrees with the workbook and CAD; node experiments could be run at the wrong coordinate. **Fix:** single estimator definition, derived and documented, or delete the core field and keep only metric/measured.

### D-02 (S1) — SCAD `compact_mode_crystal` render mode silently does nothing new
`vogel_parametric_crystal_models_v6_RGCS_v2.scad` lines 465–468: inside the dispatch branch, `show_compact_mode_rings = true;` is assigned *within the if-block scope*. OpenSCAD scoping means the module `vogel_wand` still sees the top-level `show_compact_mode_rings = false`, so the dedicated compact-mode render mode draws no rings.
**Consequence:** users believe they exported a compact-mode reference model; the v6 headline feature is inert. **Fix:** pass the flag as a module parameter or instruct users to set the customizer variable directly.

### D-03 (S1) — Prototype JSON output can be invalid (NaN)
`core.py::node_positions` returns `"measured_node_mm": math.nan` when no measurement is supplied; `app.py` serializes with `json.dumps`, which emits bare `NaN` — not valid JSON per RFC 8259. Batch reports consumed by strict parsers will fail.
**Fix:** use `None`/omit the key.

### D-04 (S2) — Manuscript worked value 0.0342% is fine, but its label is not
TEX §4 presents the 110 mm ↔ N=7 match (verified: +9.818 Hz, +0.03424%) adjacent to Established formulas without noting the chain: JH source length (Source claim) × 1D half-wave applicability (Hypothesis) × arithmetic (Derived). As printed it reads as confirmation of the 4096 ladder.
**Fix:** classification labels per policy §3 (weakest-link).

### D-05 (S2) — Isotropic wave speed assumed for a strongly anisotropic crystal
Everywhere (TEX, core, WB2, WB5) v_L = 6310 m/s is used as a single scalar. α-quartz is trigonal; longitudinal velocities differ by several percent between axes (and 6310 m/s itself is an undocumented import — no citation anywhere in the corpus). The manuscript names "wave-speed anisotropy" as a calibration excuse (§12.2) but no artifact models it.
**Consequence:** every ideal length and every harmonic-error percentage carries an undeclared systematic of order a few percent — larger than most of the "matches" celebrated (0.03%!). **Fix:** anisotropy module (GAN delta), cite a quartz elastic-constant source, propagate velocity uncertainty into all ladder outputs.

### D-06 (S2) — Resonance-class bins and sweep span are unjustified magic numbers
WB2 Resonance Offset: bins |ε|<10⁻⁴ "VERY CLOSE", <0.01, <0.1; sweep span `MAX(10, 4·|Δf|)` Hz. The 10⁻⁴ edge coincides with Lee–Tsai's dark-sector window (Source claim) and has no relation to crystal linewidths; a Q=1000 mode at 20.48 kHz has fractional FWHM 10⁻³, so "VERY CLOSE" is 10× narrower than measurable.
**Fix:** derive bins from measured/assumed Q; label as Derived heuristics.

### D-07 (S2) — Duplicated symbols across the corpus
(a) `p` = pair multiple in ε_R^(f) (TEX §7) *and* cone exponent in the spiral z-law (TEX §5) *and* pulse-mode symbol in WB5; (b) `a` = spiral scale parameter and (in GAN, entering v2) scale factor; (c) `γ` planned as node fraction γ_g (TEX §10) while GAN uses γ for Barbero–Immirzi and Γ for linewidths already exists (TEX §8); (d) `Q` = quality factor vs LT's Q_E charge; (e) `S` = engineering score (TEX §13) and state vector 𝒮 (TEX §3); (f) `σ` = node-position uncertainty σ_x (TEX §10) will collide with GAN shear scalar σ².
**Fix:** math-foundations agent must issue a project-wide symbol table before writing v2 equations.

### D-08 (S2) — `micro_pulse_metrics` hides topology assumptions
`event_rate_energy_w = E·f_carrier` assumes exactly one energized pulse per carrier period. The authoritative JH topology (JH-023) is two independent generators alternating 180° out of phase, never simultaneous — plausibly two pulse events per period (one per coil), i.e., 2× the average power. Also `inferred_inductance_uh = V·t_rise/I` neglects resistance (stated in WB5 audit note but not in the core docstring), and `decay_voltage_scale_v` is a linear-ramp proxy presented without model statement.
**Fix:** explicit `pulses_per_period` parameter; copy WB5's "measure, don't infer" caveat into docstrings.

### D-09 (S2) — Spiral path length: closed form vs numeric disagree by construction
WB5 Sheet 11 / WB2 Spiral 4D use the exact planar log-spiral length ℓ = R₀√(1+a²)/a·(1−e^{−2πaT}) times a crude 3D correction `√(1+(H/ℓ)²)` (which assumes the whole climb happens along the whole planar length uniformly); `core.py::spiral_metrics` computes the true numeric 3D polyline length. These can differ by percent-level amounts depending on the cone exponent, yet both feed "effective compact radius" R_χ = ℓ_turn/(2π).
**Consequence:** workbook and core produce different R_χ from identical inputs; the compact-spectrum "prior" is implementation-dependent. **Fix:** define R_χ once (numeric 3D), make the workbook match, and record the mean-per-turn averaging assumption (each turn's length actually differs by factor 1/q — see ledger RG-09).

### D-10 (S2) — Loading model conflates length ratio with frequency ratio without stating it
`human_loading_from_length` sets k_H = L_actual/L_target and calls it a loading factor (defined in TEX §9 as f_loaded/f_free). This silently assumes the cut-short crystal is *intended* to be pulled down to target by loading, and that frequency scales exactly as 1/L. η = 0.5 modal-mass fraction is asserted, not measured. WB5 Sheet 10 documents this as a hypothesis with four selectable modes; core.py exposes only the length-shortfall route and returns "mass_loading_compatible: yes" with no hypothesis label.
**Fix:** carry WB5's mode structure and hypothesis language into core; classification metadata per policy.

### D-11 (S2) — Workbook hardcodes N=5 in loading sheet
WB2 Loading Calibration B17: `Target frequency = 'Design Inputs'!B5*5` — the harmonic index 5 is hardcoded while everything else is parameterized. Changing the design harmonic silently leaves the loading sheet on N=5.
**Fix:** link to a shared N cell.

### D-12 (S3) — WB2 Drive Systems status column is dead logic
H31–H35: `=IF(D31="Pulse duty", IF(...), "CALCULATED")` — the condition tests the *label text* of each row, so all rows except "Pulse duty" always return "CALCULATED" and the range check runs only on one row; copy-paste artifact.
**Fix:** per-row range checks or drop the column.

### D-13 (S2) — Nominal-vs-exact cycle counts: phase-residue formula error in WB5
WB5 "12 Pulse Modes" B37: `Macro phase residue (cycles) = B35 − ROUND(B35,0)` — but B35 is the *duty* (0.5), not the cycle count (B36). Residue should be `B36 − ROUND(B36,0)`. WB3's equivalent sheet (B38 = B37−ROUND(B37,0) on macro cycles) is correct; the two workbooks disagree.
**Consequence:** anyone reading WB5's phase-residue (and its degrees conversion B38) gets duty-derived nonsense (residue 0.5 → 180° for half-spacing regardless of carrier). **Fix:** correct WB5 formula; add golden test: half-spacing nominal 1507.328 cycles → residue **+0.328** (+118.08°).
*Erratum trail:* this entry originally quoted the residue as −0.328 (−118.08°); Agent 02's implementation, the golden test, Table 5/8, and the manuscript all give **+0.328** (`phase_residue_cycles(1507.328) = +0.328`, residue defined as nominal − round(nominal) with round-half-to-even: round(1507.328) = 1507, residue = +0.328). The sign here was corrected 2026-07-14 (QA-D-08); the register text, not the code, was wrong.

### D-14 (S2) — Even-family zero mode divergence from the LT template
LT imposes ∮B_μ dy = 0, removing the mediator zero mode (ledger LT-04). RGCS's even-parity filter starts at n=2 only because n runs from 1; a base mode f_b>0 with n=0 is not representable, and nothing documents whether the RGCS even family should include a "zero mode". The analogy is silently partial.
**Fix:** math-foundations agent to decide and document n=0 handling per family.

### D-15 (S2) — README/TEX "validated unit tests" overstatement
TEX abstract says "validated unit tests"; the prototype suite (13 tests) covers happy paths only — no error-path tests, no property tests, no golden tests for `crystal_geometry` volume/mass, none for `coupling_score`, none for the spiral closed-form-vs-numeric agreement (D-09 would have been caught).
**Fix:** manuscript wording; expanded suite for the rebuild.

### D-16 (S3) — app.py `design_summary` reuses `resonance_level` default silently
The Overview tab computes ε with default p=2 while the Coupled tab exposes p; two tabs can show different ε for the same inputs if the user changed p. Minor UI inconsistency.

### D-17 (S3) — SCAD spiral z-laws differ between files
SCAD1 uses z = H(1−(r/R)^p) (matches core); SCAD2's `spiral_reference_z(t) = H(1−q^{−turns·t})` is the p=1 special case with no exponent control, and its radius floor (0.5 mm vs SCAD1's `inner_cutoff_mm=0.8`) differs. Printed "matched controls" from the two files are not actually matched.
**Fix:** one shared spiral definition with explicit parameters.

### D-18 (S3) — Dead/misleading SCAD code
SCAD2 `render_named_preset` contains `old = selected_preset;` with a comment admitting it does nothing; `phase_conjugate_pair_markers` places markers at z = L·n/(max(a,b)+1), an arbitrary mapping inconsistent with `compact_mode_rings` (z = L·n/(count+1)) — two different mode-index→position conventions in one file, neither derived from any mode shape.
**Fix:** document that marker positions are decorative until FEA mode shapes exist; unify the mapping.

### D-19 (S2) — Provenance gaps: equations copied without citation
(a) v_L = 6310 m/s appears in every artifact with no citation (which mode? which axis? which reference?). (b) Density 2.65 g/cm³ uncited (acceptable, but should cite). (c) TEX §8's strong-coupling criterion 2g/(Γ_A+Γ_B) ≳ 1 is standard cavity-QED lore but uncited. (d) The Lorentzian detuning factor D_f = 1/(1+(2Q_effΔ_f)²) is asserted without derivation (it is the standard resonance-response half-power form, but the harmonic-mean Q_eff choice is a modeling decision). (e) WB2 "Compact fundamental v/(2πR)" duplicates the compact-term formula without back-reference to LT Eqs. (9)–(10).
**Fix:** every Established equation gets a textbook/paper citation in the v2 manuscript; PROVENANCE_REGISTER covers files, the ledger covers equations.

### D-20 (S2) — Negative results adjudicated on amplitude only
JH-015 (no singing at 20/40/60 V), JH-031 (plant test null), JH-033 (charge-amp signals attributed to pickup) are all amplitude-based conclusions. Koster et al. demonstrate coherence can persist and be detectable below the amplitude noise floor (ledger KOS-10).
**Consequence:** the corpus's "null" labels are epistemically weaker than stated. **Fix:** re-label as "amplitude-null, coherence-untested"; protocol agent adds coherence re-analysis to these branches.

### D-21 (S3) — Manuscript default-config mismatch risk
TEX Appendix B lists compact radius 100 mm as a default alongside spiral (q=e, 4 turns, R₀=60, H=80). The spiral-derived R_χ for those defaults is *not* 100 mm (core numeric path/2π differs); the two defaults are unrelated numbers presented in one list, inviting the reader to assume consistency.
**Fix:** state that 100 mm is an arbitrary placeholder or compute the spiral-derived prior and use it.

### D-22 (S3) — WB2 "Nearest 4096 N" column on compact spectrum invites numerology
Compact Spectrum column G rounds every mode frequency to the nearest multiple of f₀. With 32 modes and any R_χ, some rows will always land near an integer — a post-hoc coincidence generator contradicting the project's own pre-registration ethic (TEX §14, WB2 Experiment Planner "scrambled n/parity labels" control).
**Fix:** keep the column only with an explicit look-elsewhere warning, or move alignment testing to a pre-registered statistic.

### D-23 (S2) — LT citation metadata inconsistency
TEX bibliography and README give DOI 10.1103/tsq1-bhsz (matches PDF). TEX §2 says "boundary conditions selecting odd fermion modes and even dark-photon modes" (correct per Table I) but TEX never mentions that B_μ and B₅ have *different* BCs and that B₅ carries the chirality-flipping vertex — the manuscript's parity story is a simplification of a three-field structure. Not an error, but the traceability matrix row "Odd/even boundary modes ← Table I" overstates directness.
**Fix:** traceability row should cite "Table I + Eqs. (1)–(2), simplified to two families".

### D-24 (S3) — Prototype package docs are stale relative to code
`RGCS_v2_Mathematical_Specification.md` omits: node functions, electrode/sound/micro-pulse metrics, drive exact-cycle allocation, loading-status logic — all present in core.py. SOURCE_MAPPING.md lists seven LT mappings; the ledger now documents 22 LT rows including exclusions.
**Fix:** superseded by this ledger and the coming math spec; mark the old files as archived.

---

## Addendum: workbook port status (QA-D-09, Agent 09, 2026-07-14)

Quality gate 1 requires every workbook formula to be ported to `rgcs_core`
(with tests) or explicitly marked spreadsheet-only. QA sampled 16 formulas;
13 match to full float precision or are documented replacements. The three
gaps are hereby resolved by explicit marking:

### WB-SO-1 — Spiral 4D WB B23/B24 (compact radius R_χ): SPREADSHEET-ONLY, SUPERSEDED
The workbook computes R_χ = ℓ_3D/2π (= 60.986 mm for the default spiral).
The authoritative definition per **RGCS-M.36** is the *mean per-turn* compact
radius R_χ^(s) = ℓ_3D/(2π·T) (T = turns; = 15.280 mm for the same inputs),
implemented and tested as `rgcs_core.geometry.spiral` →
`compact_radius_prior_mm`, with the per-turn candidates ℓ_k/2π exposed as
`per_turn_compact_radius_mm` (both shown in manuscript Fig. 6 / H-06a).
The workbook cells omit the ÷T and are NOT to be used; the 4× discrepancy
on identical inputs is expected and explained (workbook = total path over
2π; core = per-turn mean per M.36). Status: spreadsheet-only, superseded
by core.

### WB-SO-2 — 4096 Ladder columns E–H: SPREADSHEET-ONLY
Power-of-2 detector, ratio-vs-N=5, and Long/Primary/Short display labels
are presentation heuristics for browsing the ladder, not physics; they feed
no downstream computation, no manuscript number, and no experiment gate.
No port planned. Status: spreadsheet-only by design.

### WB-SO-3 — Loading Calibration B17–B19: SPREADSHEET-ONLY
Target frequency, predicted-free frequency, and required-shift are one-line
compositions of ported, tested primitives (`rgcs_core.harmonics` ladder ×
harmonic index; `rgcs_core.loading.loading_factor`/`added_modal_mass_g`).
The composed convenience cells are not separately ported (see also D-11:
B17 hardcodes N=5). Any calibration workflow must use the core functions.
Status: spreadsheet-only convenience cells over ported primitives.
