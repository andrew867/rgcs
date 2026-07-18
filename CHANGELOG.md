# Changelog

All notable changes to RGCS / RSCS. Semantic versioning; the frozen
v2.0.0 baseline is tag `v2.0.0` and `archive/v2.0.0/`.

## [4.7.1] — 2026-07-18

R3: Root-Space Resolver, Anisotropic Phase Lens, Optical Spin, HAL
Memory, Nested Tetrahedral Atlas (v4.7.x R3 pack, 95 agents).
**SOFTWARE_VERIFIED, PHYSICAL_UNTESTED.** All prior tags untouched.

The R3 correction: a root is NOT "the first zero of the phase
residual" -- wrap(phi)=0 admits integer-cycle aliases (4097 candidates
per second at 4096 Hz). New `r3/` package: six typed root classes, six
forbidden collapses as executable refusals, dual-lattice alias
thinning, gauge orbits with mandatory representative rules, emission-
coordinate localization from >=4 reference worldlines (relational by
construction), and a root-lock certificate whose best status is
ROOT_LOCK_BOUNDED with ABSOLUTE_VACUUM_ROOT_UNSUPPORTED and
NONLOCAL_REFERENCE_FRAME_UNSUPPORTED standing. Plus: anisotropic phase
lens (adjoint-verified Tikhonov inversion, refusal of unregularized
solves), exact 8^d tetrahedral addressing with five declared K
semantics and hard destination certificates, spin/torsion typing that
never merges categories (EC torsion from a fully polarized solid
~6e-25 1/m; a 1e-9 metric wish costs 6.7e17 kg -- REFUSED_BY_
ARITHMETIC), optical spin with SAM/OAM separation and dose ceilings,
synthetic-only HAL memory with a consent gate, and the nested atlas
whose null-rotation campaign rejects grid orientations that cannot
beat seeded random rotations. L'ou source log preserved verbatim,
sha256-pinned. Gate Zero re-verified v4.7.0 remotely; enforce_admins
on main is now ON (operator action) closing the R2 governance gap.
Workbook: 26 sheets (2 new R3).

Tests: 1153 passing (1 archived-environment byte test
deselected by policy D-V3-04).

## [4.7.0] — 2026-07-18

Phase Memory, Worldline-Indexed Multipath Recovery, Causal Channel
Reconstruction, and Phryll Translation Hypothesis (v4.7 pack, agents
A00-A83). **SOFTWARE_VERIFIED, PHYSICAL_UNTESTED**: no apparatus was
built, no data collected, and no Phryll-detected state exists in this
release by construction. All prior tags untouched.

New `pmwr/` package: typed phase authority with a nine-state
synchronization machine (cycle count only while PHASE_LOCKED, no force
flag); finite-Q phase-memory horizon with perfect-memory refusal; six
separated signal stages (propagation always loses the cycle count);
worldline/path schemas on the validated weak-field fixtures; the
arrival/causal-order firewall (reordering is delay geometry; the audit
cannot emit "causal reversal"); closure-window alias analysis (exact
closure IS a delay alias -- 4097 indistinguishable delays per second
for the binary family) with dual coprime lattices extending the
unambiguous range x4096; least-squares recovery behind an
identifiability gate that REFUSES underdetermined and ill-conditioned
cases; the crystal-translation lane (geometry schema with mandatory
reversed-orientation control, excitation registry where
self-oscillation needs a loop AND an energy source, energy ledger that
calls over-unity ACCOUNTING_ERROR); the pyramid-ratio audit (2a/h at
51.843 deg = 1.5714157792, ~5e-4 from pi/2, GEOMETRY_IDENTITY, the
mechanism reading refused); and the guarded Phryll ladder (a residual
requires all eleven ordinary channels bounded plus a sham-drive
control; the source's own power-not-engaged episode is the preserved
warning).

Gate Zero: v4.6 independently re-verified by object ID and remote
download before branching; only CI-verified commits reached main.
enforce_admins remains OFF pending operator action (documented).

Workbench gains an Evidence-ledger panel (14 panels); workbook gains
three PMWR sheets (24 total). Operator note and evaluation contract
hash-pinned before estimator work.

Tests: 1113 passing (1 archived-environment byte test
deselected by policy D-V3-04).

## [4.6.0] — 2026-07-18

Crystalline Spacetime Coordinate Program (v4.6 pack, agents A00-A36).
**SOFTWARE_VERIFIED, PHYSICAL_UNTESTED**: no apparatus was built, no
data collected, and no physical hypothesis is supported. All prior tags
untouched.

New `cspc/` package: exact unit-aware frequency mathematics (floats
refused; sig-figs tracked separately from exactness), a frozen
hash-pinned simplicity metric with matched nulls and Holm/BH
correction, the 64-tetrahedron lane (four non-isomorphic families,
relabeling-invariant spectra, degree-matched nulls), DDS/NCO and
phase-closure compilation, preregistered experiment definitions, a
relativistic clock model validated against Pound-Rebka and GPS, a
metric/energy audit, and structural RF safety with no override flag.

Corrections to the source material: 2.45 GHz is not a unique resonance
of water (Debye loss peak ~19.2 GHz; 2.45 GHz carries ~25% of peak
loss); "0.0356521923..." retains HERTZ and is a 36-bit DDS resolution
step; 8^11 is 33 octaves not 11; the "64-tetrahedron grid" phrase is
underdetermined and stays so.

Headline results are null or cautionary: the simplicity metric measures
human number-choosing convention, not nature, and the programme's own
candidates are flagged CIRCULAR; 4096 = 64^2 holds for any 64 objects;
the ideal phase closure collapses ~175,000x on a decimal reference
clock and is only restored by choosing a binary oscillator; a
laboratory energy budget implies a Schwarzschild radius 23 orders of
magnitude below a proton. All five travel-adjacent claims are
UNSUPPORTED.

Four new Master Evidence Workbook sheets read the canonical store and
show exact vs physically-supported precision side by side.

Five defects found by running the analysis honestly (CSPC-D-001..005),
including a null model that made every corpus -- including the negative
control -- appear significant; fixing it inverted the headline result.

Tests: 1062 passing (1 archived-environment byte test
deselected by policy D-V3-04).

## [4.5.2] — 2026-07-17

Windows Workbench clean-rebuild patch. The v4.5.0 and v4.5.1 release
binaries were invalid: every build after the first freeze used
`--skip-freeze`, which re-zipped a **stale** PyInstaller executable. The
current source handled `--first-run` correctly, but the shipped exe was
built before that code existed, so the installer's post-install launch
(`RGCSWorkbench.exe --first-run`) created a workspace literally named
`--first-run`.

Fixes:

- **Clean rebuild from current source** — `build/` and `dist/` deleted,
  full freeze (no `--skip-freeze`).
- **Build provenance embedded in the exe** (`rgcs_desktop/build_meta.py`,
  `_build_stamp.json` bundled): version, git commit, and a source hash
  over every packaged `.py`. New `--build-info` prints it.
- **`--skip-freeze` now refuses a stale/mismatched `dist/`** — the build
  aborts if the frozen tree's source hash differs from the working tree,
  so the failure that shipped twice cannot recur.
- **`--first-run` can never be a workspace path** — startup selection
  moved to a pure, tested `plan_startup()`; `--first-run` (and any
  `--flag`) maps to the wizard, never to creating/opening a directory.
- **Source + packaged regression tests** — `plan_startup` unit tests,
  and frozen-binary tests that run the installer's exact command and
  assert no `--first-run` directory is ever created, plus build-info
  hash match, 13-panel smoke, wizard/demo/workbook self-test.
- Installer's exact post-install launch, wizard creation, demo seed,
  workbook, all 13 panels, restart, upgrade, and uninstall verified on
  this machine (still not a clean VM; clean-machine verdict not claimed;
  installer still unsigned).

Tests: 945 passing (1 archived-environment byte test
deselected by policy D-V3-04).

## [4.5.1] — 2026-07-17

Windows Workbench packaging patch on 4.5.0. No source logic or
scientific claim changed; all prior tags untouched.

The v4.5.0 portable build crashed on launch: the model-browser panel
reads `docs/model_registry.yaml` (and the provenance graph reads
`references/` and `experiments/schemas/`), none of which the
PyInstaller spec bundled, so the frozen app raised `FileNotFoundError`
while constructing its panels. `--doctor` returns before any panel is
built, so the build check never saw it.

Fixed: `packaging/RGCSWorkbench.spec` now bundles every runtime data
tree the desktop reads (`docs/model_registry.yaml`, `references/`,
`experiments/schemas/` alongside the two `registry/` trees), guarded by
a new regression test; `tools/v45_build_windows.py` verifies the frozen
exe with `--smoke-check` (constructs all 13 panels + a real background
job), not just `--doctor`. New deliverable: a compiled per-user
(unsigned) Inno Setup installer EXE; the silent install → launch →
uninstall cycle was verified on a developer machine (not a clean VM —
the clean-machine verdict is still not claimed).

Tests: 939 passing (1 archived-environment byte test deselected by
policy D-V3-04).

## [4.5.0] — 2026-07-17

Windows Workbench, portable package, and Master Evidence Workbook
(v4.5 pack). **SOFTWARE_GREEN, PHYSICAL_UNTESTED** unchanged: this is
a packaging and interoperability release; no physical result is
validated and no evidence class was promoted.

**Canonical export model** (`rgcs_workbench/`): a typed `Record` /
`CanonicalStore` layer pulls live data from every v4.x lane —
frequency keys, harmonic relations, specimens, mode estimates, timing
recipes, hypotheses, the Eye numerical ladder, the resonator
platform campaign, hardware BOM, experiment queue, corrections,
source registry, and PUBLIC_SAFE lore. Each row carries an evidence
class from the eight-rung ladder and a privacy class; the store is
the single source of truth and the workbook is generated one-way from
it (never the reverse).

**Master Evidence Workbook**: `python -m rgcs_workbench.workbook`
(or the app's `--export-workbook`) writes a 17-sheet formula-visible
xlsx — Dashboard, Frequency Keys, Harmonic Relations, Specimens, Mode
Estimates, Timing Recipes, Hypotheses, Evidence Ledger, Eye Results,
Resonator Platform, Hardware BOM, Experiment Queue, Corrections,
Source Registry, Lore Registry, Installer Metadata, Workbook Guide.
Derived cells stay live formulas (mode-estimate percentage errors,
dashboard sums); evidence classes are colour-coded; a public export
provably contains no PRIVATE row content. Excel is never required to
run the app — the workbook is interoperability only.

**Windows packaging** (`packaging/`): a PyInstaller onedir build
frozen from `RGCSWorkbench.spec` produces `RGCSWorkbench.exe`, zipped
into a portable ZIP that runs with no install, no admin, no
telemetry, and no auto-start; per-user data lives in
`Documents\RGCS Workspace`. Headless `--doctor` and `--smoke-check`
verify the frozen build. The Inno Setup installer script
(`RGCS_Workbench.iss`, per-user, `PrivilegesRequired=lowest`) is
shipped in-tree; the compiled Setup EXE and clean-machine VM
verification are **honestly gated** — Inno Setup is not present in the
build environment and no clean VM was available, so this release ships
the verified portable ZIP and workbook and does NOT claim a
signed installer or clean-machine proof.

Tests: 938 passing (1 archived-environment byte test deselected by
policy D-V3-04), including 22 new workbench, workbook, and packaging tests.

## [4.4.0] — 2026-07-17

Frequency-Key Harmonic Excitation and ESP32-CYD Instrument (v4.4
pack, agents A00–A26). All prior tags untouched. **SOFTWARE_GREEN,
PHYSICAL_UNTESTED**: the specimen is an eBay listing, no board has
been powered, and all six preregistered hypotheses are UNTESTED.

**Exact relation engine** (`fkey_instrument/`): all frequency
arithmetic in `fractions.Fraction` (floats refused at the parse
boundary); every relation carries exactly one primary mechanism
class from the pack's taxonomy. The frozen seed corpus classifies as
required: 4096×5 is a low-order HARMONIC; 8×2560, 20.48×1000 and
40.96×500 are exact but PHASE_CLOSURE_ONLY; the mixed sums
(1496+32×587, order 33; the four-tone sum, order 21) are
ARITHMETIC_COINCIDENCE — not emitted frequencies in a linear system.
The A06 engine proves (analytically AND by independent FFT) that an
ideal sine has no fifth harmonic while a 50% square carries one at
exactly 1/5; duty error resurrects even harmonics.

**Pre-arrival specimen model**: immutable revision 1 from seller
claims (77.8 mm → quarter-wave 20278.959 Hz, half-wave 40557.918 Hz);
correction record FK-CORR-001 verifies the two target percentage
errors are ONE number (both ∝ v/L); the model licenses a search band,
never a magic frequency; arrival measurements create revision 2 with
mandatory instrument provenance.

**Mechanism-first optimizer**: expected amplitude comes from the
spectrum engine through a 2-DOF plant (transducer-vs-crystal
discrimination by response-to-perturbation), so sine-"harmonics" and
arithmetic coincidences score zero by construction; Pareto dominance
runs within hypotheses (a sham is not a substitute for a resonance
tone); campaigns compile randomized, blinded, sham-included, with the
no-post-hoc-frequency rule declared.

**Fail-off instrument twin + firmware**: strict JSON contracts
(missing amplitude REFUSED, never defaulted; invalid JSON faults at
load, before any output authority); safety FSM with fresh single-use
expiring arm leases, no auto-arm, 14 latching fault causes,
reset-lands-output-off; hash-chained SYNTHETIC logs; CYD board
profiles are candidates (verified=False) with boot-strap/input-only/
peripheral pin-conflict detection and UNKNOWN ⇒ OUTPUT_DISABLED;
LEDC/RMT/DDS backends report requested vs calculated-realized
frequency as exact rationals with measured=None until a measurement
exists. Firmware source tree provided
(`firmware/fkey_cyd/`, PlatformIO) mirroring the tested twin —
NOT compiled here (no toolchain, no hardware).

**Six demos** run entirely in simulator (relation census, waveform
distinction, nominal sweep + bootstrap Q, optimizer + 4 validated
recipes, full device cycle with intact log chain, fault refusal),
every artifact SYNTHETIC-labelled. **46 FK coverage requirements**
verified mechanically with bidirectional orphan checks; A24 red-team
attacks are executable regression tests.

Tests: 916 passing (1 archived-environment byte test deselected
by policy D-V3-04).

## [4.3.0] — 2026-07-17

Post-v4.2 Emergent Resonator and Structured-Wave Expansion. All prior
tags untouched. Coverage: 280 fixed IDs + 8 orphans = 288, verified
mechanically (symbols import, tests exist, docs exist, status legal
for depth) from the programme's first commit.

**Closed-loop resonator platform** (`resonator_platform/`, 14
modules): lifecycle state machine without a force flag; append-only
hash-chained ledger; predicted/measured/fitted/accepted frequency
separation enforced in constructors; digital twin with fabrication
variation and execution noise; Lorentzian DAQ fits that report
non-identifiability; conservative trim planner (overshoot is
unrecoverable, so the selector refuses rather than burns); approval
tokens + machine-capability registry requiring fume-extraction and
interlock evidence (no machine registered → the physical path
refuses, truthfully); reversible-trial tuning with exact rollback;
HMAC certificates that refuse unfitted or out-of-band acceptance and
print the claims they do NOT make; a complete synthetic
design-to-certificate campaign (2 trim iterations, ACCEPTED in band,
32-event intact ledger, deterministic per seed). Additive process
cards (printed silica enforced ≠ quartz), MEMS twin with
INTERFACE_ONLY foundry handoff, oscillator models with the
resonator≠oscillator boundary in code, neutron-paper composite-mode
mathematics with computationally verified parity selection and the
angular-Nyquist alias band reported.

**Eye: the census corrected the programme's own headline.** The
unbiased full-domain cluster census (Y03) shows the v4.1
(z=102.24 mm) and v4.2.1 (z=99.78 mm) coordinates are two
resolution-dependent estimates of ONE male-apex feature — with a
symmetric family (female-apex twin z≈4 mm, mid-shaft pair z≈58 mm)
invisible to every earlier nearest-to-candidate analysis. Station
comparison stands (5.1–6.7 mm vs ~1.8 mm halfwidth); eigenspace
tracked <2.7° (no mode switch). Claim card v3 → v4 with the
correction trail appended. Calibrated resource model with range
predictions and preflight refusal; the 150× estimator failure is
preserved as its calibration history.

**Five 2026 papers ingested** with hashes, claim cards, equation
provenance, and per-source transfer firewalls that raise on quartz
claims; five reference models with tested analytic limits (a sign
error in the triangular-transport removal rate was caught by its own
redistribution test during development). Mechanism-discrimination
tree defaults to INCONCLUSIVE; the model playground is structurally
unable to write evidence.

**Policy lanes**: broadcast heritage, product tiers (targeted ≠
measured), Hydrogenuine open-commons/assurance boundary, private-lore
mechanism (content local-only, never tracked), intuition pipeline
with retrospective baseline labelled non-evidence, versioned claim
cards.

Nothing physical exists: no board, fixture, laser, instrument,
printer, or cleanroom. Every physical path is capability-gated and
currently refuses.

Tests: 857 passing (1 archived-environment byte test deselected by
policy D-V3-04).

## [4.2.1] — 2026-07-17

Completeness audit of the v4.2 expansion. The `v4.2.0` tag stays
immutable at `d253c2f` and is recorded as a CI-green tagged expansion
candidate whose release publication was blocked before completion; it
is superseded, not rewritten. All prior tags untouched.

**Why this release exists.** v4.2.0 reported "coverage ledger 248/248,
all gates green". That was true and meaningless at the same time: the
gate verified that every ID had an owner *string* and an artifact
*string*, both satisfiable with any nonempty text. Seven of the QA
prompt's attacks succeeded against it.

**Found and fixed (11 defects, no open P0/P1):**

- **V4X-D-006 (P0)** C05 metrology was a registry of seller values
  wearing an implemented workstream's status; no pipeline existed. New
  `rscs2_core/metrology.py`: seller values cannot become measurements
  (constructor-enforced), XRD returns `INTERFACE_ONLY` rather than
  inferring axes from facets, malformed scans are refused not repaired.
- **V4X-D-007 (P0)** consciousness-lane status laundering: 18 entries
  claimed `REDUCED_ORDER_VALIDATED`, only 6 had models. Implemented 5
  real models (ring attractor with saturation, phase-amplitude coupling
  with surrogates, quantum order effects + parameter-free QQ equality +
  classical comparator, subjective time); **downgraded 7** with the
  reason recorded per entry. `model_symbol` now verified by test.
- **V4X-D-012 (P1)** G42 verified strings → gates **G42A–G42G** verify
  paths exist, symbols import, sources resolve, tests and docs exist,
  status is legal for the delivered depth, and blocked rows name their
  blocker and next action. 268 rows, all pass.
- **V4X-D-010 (P1)** the P02 orphan sweep had never run. 20 orphans
  registered with mandatory dispositions; coverage 248 → **268**.
- **V4X-D-009 (P1)** 47 required standalone documents missing (1/38
  agents complete) → ~50 documents written.
- **V4X-D-005 (P1)** the cusp metric summed over path *samples*; a log
  spiral crowds θ-uniform samples at its centre, so a **uniform** field
  scored 0.695 concentration. Arc-length weighting fixed it, validated
  against an independent analytic target (uniform → 0.0928 = the
  arc-length fraction). Concentrated/uniform = **10.576×**, finite. The
  audit's premise (that the >5× test was changed post-hoc) was wrong —
  git history shows the threshold never moved.
- **V4X-D-013 (P1)** nine frequency entries carried `CORE_VALIDATED` on
  arithmetic identities; `F002: 20.480 kHz = 4096*5` read as a
  validated resonance. Automatic **ARITHMETIC ONLY** note, enforced.
- **V4X-D-008 (P1)** C01 lacked the mandatory strong-coupling
  criterion. Added, verified against the complex eigenvalues.
- **V4X-D-011 (P1)** "sub-millimetre refinement" ran at 8.0/5.5/4.5 mm.
  Renamed honestly; a genuinely finer ladder was run.
- **V4X-D-004 (P1)** release notes said 681 tests, the report said 682.
  Counts now derive from a real pytest run into
  `docs/v4/RELEASE_METADATA.json` and are guard-verified across docs.
- **V4X-D-002 (P1)** the asset builder hardcoded its version.

Also: BVD gains OSL calibration, multi-branch detection, identifiability
reporting and SPICE export; the apparatus twin gains coil
resistance/field/thermal/contact/transducer/cable models with the
Biot-Savart map agreeing with the analytic formula to 1e-4.

**The Eye is resolved, computationally, and the answer changed.** A
finer ladder (3.0/2.0/1.5 mm, 30 816 dof) puts the halfwidth
(1.803 mm) below the separation (6.298 mm) for the first time:
`NEAR_CONVENTIONAL_NODE_BUT_DISTINCT` — the conventional model **does
not explain** the candidate. The candidate also does not converge on
the v4.1 coordinate: its distance from (−0.295, −0.205, 102.240) mm
*grows* with resolution (1.375 → 2.270 → 2.476 mm), settling near
(−0.048, −0.020, 99.78) mm. The canonical record is preserved unchanged
(G07) — it faithfully records a ~4 mm-spacing computation — but it is
resolution-limited, not converged. `cl=1.25` was not attempted:
measured 13.9 GB at cl=1.5, projected ~45–71 GB against 31.6 GB of RAM,
so the run stopped honestly. (The first resource estimate used the
textbook dof^1.5 LU rule and was wrong by ~150x; it was corrected
against the measurement.)

**Unchanged and honest:** no measured data exists anywhere; every
experimental campaign is protocol-only; E06/E07 are ethics-blocked; the
Eye result is computational, on an ideal geometry, for one mode, with
an assumed orientation — it is not evidence that any physical crystal
does anything.

## [4.2.0] — 2026-07-16

Master Research Expansion: the post-v4.1 backlog translated into
equations, protocols, controls, and honest statuses. The v4.1 quartz
core, its corrected Eye verdict, and all prior tags are unchanged.
Nothing in this release is an experimental result.

**Coverage contract.** All 248 master-ledger IDs (A01–A18, F001–F052,
G001–G030, E001–E027, S001–S024, W001–W017, H001–H017, C001–C052,
I001–I011) have an owner, an artifact, and a disposition;
`docs/v4/V4X_COVERAGE_LEDGER.md` is generated and gate G42 is enforced
by `tests/v4/test_v4x_coverage_ledger.py`.

**Eye sub-millimetre refinement (C02) — INSUFFICIENT_RESOLUTION.** A
three-level mesh ladder (clmax 8.0/5.5/4.5 mm, 8 elastic modes) with
complex driven response (`fem.harmonic_field`), D9/D10 phase
diagnostics, and a frequency-sensitivity map. The axial coordinate is
stable (z ≈ 102.05–102.31 mm) and modal frequencies converge, but the
transverse centroid still moves at the mesh scale: halfwidth 4.096 mm
versus separation 4.149 mm. The run therefore does **not** resolve
whether the candidate coincides with the conventional node — it neither
refutes nor establishes distinctness. The canonical v4.1 record
(separation 3.906 mm, halfwidth 3.08 mm) is preserved and not
superseded. No proximity threshold is used; exact coincidence remains
the 1e-6 mm numerical tolerance only.

**Eye D9/D10 guard fix.** The realness guards in
`phase_coherence_field` and `phase_singularities_on_plane` moved from an
absolute `np.allclose(w.imag, 0)` test to a relative one
(`max|Im w| < 1e-12 × scale`). The absolute form rejected genuine complex
driven responses at small amplitude — a solver-scale artifact, not
physics.

**Geometry (G01/G02, S001–S024).** Spiral-cone mathematics (curvature
invariant κ·r = 1/√(1+a²), focus eigenvalues −a ± i, per-turn ratio
e^(−2πa)), pinched twisted-cone variant, clamped-plate Bessel modes,
Mohan spiral inductance, structural-versus-electrical resonance
separation, matched controls, and SCAD/DXF/STL/Gerber/drill exports.
`cusp_response_metric` is now arc-length weighted so concentration does
not depend on path sampling density. Merit functionals are declared ENG
constructs with no physical significance.

**Experimental lane (E001–E027, W001–W017, H001–H017).** Nine campaigns
with channels, control matrices, randomization, blinding,
preregistration, and safety-gate evaluation. E01–E05/E08/E09 are
`PROTOCOL_READY_HARDWARE_REQUIRED`; E06 human loading and E07
operator-state are `ETHICS_APPROVAL_REQUIRED` and the gate enforces that
regardless of engineering safety. Water protocols require a
no-ingestion/no-therapeutic-claims acknowledgement. Synthetic DAQ
analysis validated on planted ring-down fixtures; the schema refuses to
label synthetic data as measured. **No hardware was operated and no data
was measured.**

**Consciousness lane (C001–C052) — quarantined.** New `consciousness_lane/`
package with a layered theory registry (layer, status, evidence tag,
falsification condition per entry) and reduced models: Kuramoto against
its analytic K_c = 2γ, state-change decay, dream–wake constraint with a
quarantined K_ext, and the microtubule causal threshold
(τ_c·η_φ·K_cross > θ), which does not clear at the reference 310 K
decoherence estimate and never upgrades on a favourable parameter guess.
THz/superheterodyne items are analogies only; quantum-probability models
are not a quantum brain; Hydrogenuine items make no consciousness claim;
first-person and private-myth layers are retained non-public, unendorsed
and unrefuted. The package may not import quartz solvers — enforced by
test. No consciousness record is usable as evidence in quartz
computation.

**Adversarial QA (Q01).** Eight attack tests: threshold reintroduction,
source laundering, future-interface coercion, quarantine leakage, ethics
gate bypass, synthetic-as-measured, frequency near-miss rounding, and
stale coverage. All repelled.

Post-rc CI hardening (V4X-D-001/002/003): G51 consciousness-lane
quarantine audit check (structural, AST-verified both directions);
release-asset builder reads the version from pyproject instead of a
hardcoded constant; the coverage contract is snapshotted into the
repository (`docs/v4/V4X_LEDGER_IDS.json`) so CI and fresh clones can
evaluate gate G42 without the gitignored prompt pack.

Tests: 737 passing (1 archived-environment byte test deselected by
policy D-V3-04). Hosted CI 10/10 green at the release commit.

## [4.1.1] — 2026-07-16

Documentation-only patch release (no code, solver, or evidence
changes; v4.1.0 remains tagged and frozen). Reason: the v4.1.0
manuscripts asset shipped four documents (USER_GUIDE_V4,
RELEASE_NOTES_V4, ZENODO_METADATA_V4, EYE_METHODOLOGY) that still
asserted the retired CONVENTIONAL_NODE verdict as current without a
correction marker — contradicting the release's own V4C-D-001
correction. This patch: full documentation consistency audit
(`docs/v4/DOCUMENTATION_AUDIT_V4_1_FINAL.md` + machine-readable JSON);
README rewritten for v4.1 (release, install, CLI quick start, corrected
Eye record with the 3.906 mm separation and uncertainty interpretation,
capability-firewall and reference-system distinctions, unimplemented-
physics list); corrected/labelled the four stale documents; historical
banners on superseded v4.0.0 texts; closeout guard tests
(`tests/v4/test_v4c_docs_closeout.py`) that fail the build if the 4 mm
rule, the retired verdict-as-current, or physical-nonexistence claims
are reintroduced; documentation/asset audit of the release builder.

## [4.1.0] — 2026-07-16

Capability-aware multiphysics completion of v4 (all results
computational; no experimental confirmation exists).

**Corrected (V4C-D-001, user-identified):** the Eye Consensus
node-classification rule that absorbed any candidate within a ~4 mm
physical radius into a "conventional node" verdict is REMOVED and
replaced by an uncertainty-aware comparison
(`rscs2_core.eye.node_coincidence_comparison`): exact coincidence only
within declared numerical tolerance (1e-6 mm); interval overlap and
resolved separations reported at their exact values. The canonical
110 mm candidate (z ≈ 102.240 mm) is PRESERVED and reclassified:
separation 3.906 mm from the nearest conventional station, localization
halfwidth 3.08 mm (mesh-resolution dominated), convergence shift
0.353 mm, draw-cloud rms 0.032 mm → verdict
`UNCERTAINTY_OVERLAPS_CONVENTIONAL_NODE`. The published v4.0.0 tag and
bundle are frozen history; this release supersedes their
interpretation.

**Added:** source registry + equation ledger with mechanical
classification ceilings (SRC-V4-00..19, RGCS-V4-EQ-001..015); material
capability firewall (16 records, coupling graph with operator-
capability floors, rgcs.v4.result.1 envelopes, no fake zeros;
MECHANISM_NOT_IMPLEMENTED_FOR_MATERIAL is never presented as physical
nonexistence); 12-quantity torsion/circulation/optical-AM/chiral
registry with identity prohibitions; Saint-Venant torsion benchmark;
Frenet-Serret; canonical SAM/OAM/topological-charge diagnostics;
reduced-order reference systems (exciton-magnon, avoided crossing
anchored to frozen v3, block Hamiltonian, dressed spin, dynamic
magnetoelectric tensor, metacrystal g2 transfer, LiNiPO4 IOME with
channel discriminators, MnF2 comparator, nonlinear AFM trajectories,
phonon-controlled exchange with direct/indirect classifier); dynamic
boundaries + symmetry lowering with work-energy closure; deterministic
calibration/inverse design with immutable observation ledgers;
quarantined FDT adapter + source-lore translation companion (import-
firewalled, pre-registered predictions); expanded Eye vote layer with
applicability; binding scope statement (What the Canonical Quartz
Model Does and Does Not Claim); adversarial QA (V4C-D-002 NaN
leakage, V4C-D-003 capability laundering — both closed with
regressions).

Frozen: v2.0.0/v3.0.x/v4.0.0 tags, archives, registries, Zenodo
records.

## [3.0.1] — 2026-07-16

Archival and community patch release (no mathematical or behavioral
changes to the v3.0.0 scientific baseline). Contents since v3.0.0:
figure-rendering fixes D-V3-05/06 (README PNG mathtext; siunitx
scientific notation in the Crystal Application manuscript) with
refreshed manuscript assets; the complete laboratory validation
campaign (Agent 14); the archival/community package incl.
`.zenodo.json` (Agent 15). Published to trigger the Zenodo webhook
(enabled after v3.0.0 shipped) and mint the DOI.

- Agent 14 (post-release): measurement-campaign design (ENG, no new
  physics/equations/ids — D14-001): `LAB_MANUAL.md`,
  `CALIBRATION_GUIDE.md`, `BENCH_HARDWARE.md`,
  `MEASUREMENT_PROTOCOL.md`, `DATA_PIPELINE.md`, `VALIDATION_PLAN.md`
  with per-hypothesis observable/measurement/expected/null/controls/
  confidence rows for H-01..H-30, phase gates (H-29/H-30 first),
  TOST-quantified null acceptance for the pre-registered reciprocity
  nulls, and campaign acceptance/failure criteria (D14-002 phasing).
- Agent 15 (post-release): archival + community package — `.zenodo.json`
  machine metadata + `docs/ZENODO_METADATA.md` (no DOI invented);
  `docs/community/` communication kit (press summary, community
  announcement, forum/reddit/LinkedIn/email posts, release FAQ — all
  stating what RGCS is, is not, current evidence, limitations, and how
  to contribute); `docs/CONTRIBUTOR_ROADMAP.md` (software vs
  experimental lanes explicit); `docs/MODELLING_ROADMAP.md` (v4 tier
  plan under reproducibility invariants: CPU oracle, seeded MC,
  typed I/O); `docs/FINAL_PUBLICATION_REPORT.md` → **PUBLISH COMPLETE**.

## [3.0.0] — 2026-07-15

Final release. Agent 13: GitHub repository bootstrapped
(https://github.com/andrew867/rgcs), hosted CI matrix green
(ubuntu/windows/macos × Python 3.11/3.13 portable + pinned ubuntu
reference), NR3-001 determinism policy completed (D-V3-04: portable
tolerance-aware golden-regeneration test on every platform; byte
equality scoped to the archived v2 environment), versions flipped to
3.0.0, release artifacts rebuilt, tag `v3.0.0`, GitHub release
published, repository public. Agent 12 (publication polish) preceded:
README rewrite, contributor documents, docs index, communication kit,
publication readiness report.

## [3.0.0-rc1] — 2026-07-15

Release candidate: all 12 quality gates GREEN (gate 8 with the documented
Linux-execution limitation). Agent 11 fixed the three QA defects
(D-V3-01 coordinate count, D-V3-02 figure reproducibility via
SOURCE_DATE_EPOCH, D-V3-03 CITATION.cff), rebuilt and repackaged the
manuscripts, and shipped `release/` (source zip, manuscript bundle,
sample-experiments bundle, SHA256SUMS, PROVENANCE.json, release notes
with gate table, limitations, and recommended public wording). Final
3.0.0 is gated only on a green Linux CI run.

## [Unreleased] — 3.0.0 programme (RSCS 1.0)

### Added
- Agent 01: `docs/V2_BASELINE_AUDIT.md` (baseline reproduced: 232/232
  archive files identical, 10/10 release checksums verified, 223/227
  tests pass on Windows with all 4 discrepancies explained).
- Agent 01: `docs/V2_TO_V3_MIGRATION_MAP.md` (all 61 equations and 14
  hypotheses dispositioned; registry/versioning rules for v3).
- Programme control documents: `DECISION_LOG.md`, `CLAIM_REGISTER.md`,
  `SOURCE_REGISTER.md`, `ASSUMPTIONS.md`, `NEGATIVE_RESULTS.md`
  (v2's `INCONSISTENCY_REGISTER.md` and `TRACEABILITY_MATRIX.md`
  continue as living registers).
- v3 skeleton per `EXPECTED_TREE`: `rscs_core/` (10 subpackages),
  `manuscripts/` (4 works), `embedded/`, `references/`,
  `tests/adversarial/`, `experiments/protocols|notebooks`.
- `.gitattributes` line-ending normalization.

- Agent 02: verified source registry, equation-provenance ledger, adaptation
  /exclusion matrices, and the frozen `docs/RSCS_NOTATION_LEDGER.md`
  (RSCS-C.1..14 coordinates, RSCS-O.1..13 operators).
- Agent 03: `rscs_core` mathematical backbone — 14 typed coordinates, 13
  operators, RGCS→RSCS embedding with the Conservative Extension Property
  (reproduces RGCS-M.23/24/28/46/55/56/10-11), a claim/provenance firewall,
  and a machine-readable RSCS registry. 64 new tests; anti-Hermitian coupling
  `K=i·2πg` (QA-D-04) enforced. Docs: `RSCS_MATHEMATICAL_MODEL.md`,
  `RSCS_OPERATOR_REGISTRY.md`, `RSCS_COORDINATE_SCHEMA.md`,
  `AGENT_03_HANDOFF.md`.
- Agent 04: Hydrogenuine memory bridge — RSCS-C.15 HG record (ENG) +
  RSCS-O.14/15/16 store/replay/update; NHT/HAL kept HYP-quarantined;
  falsifiable software claims H-15..H-19. Docs: `NHT_HAL_RSCS_MAPPING.md`,
  `HG_RSCS_MEMORY_ARCHITECTURE.md`.
- Agent 05: anisotropic crystal propagation — RSCS-O.17 Christoffel wave
  speeds (`rscs_core.propagation`) + `rgcs_core/anisotropy` (α-quartz
  elastic constants, closes v2 D-19a); resolves the scalar `v_L`
  Hypothesis into a measured-orientation model reproducing v2 at the
  crystal axes. Doc: `RGCS_CRYSTAL_APPLICATION.md`.
- Agent 06: optical/photon-phonon/nonreciprocal layer — RSCS-C.16/C.17
  coordinates, Jones↔Stokes on C.9, RSCS-O.18..O.23 (dispersion phase,
  conversion selection rules, Autler–Townes, critical coupling,
  state-dependent susceptibility with reciprocal-null default, directional
  betas/beating); `rgcs_core/optics` (quartz optical constants, ray/path
  model, photoelastic/M2 estimates); optical experiment schema +
  generated mechanism comparison table; claims H-20..H-23 (H-21/H-23
  pre-registered nulls, D6-003). Doc:
  `OPTICAL_AND_NONRECIPROCAL_COUPLING.md`.
- Agent 07: synchronized excitation/measurement architecture —
  `rgcs_core/timing` (master clock, exact-cycle closures with golden
  125 ms → 512 & 187, modulation families 20/20.48/21/40.96 Hz, coil A/B
  phases, phase-at-coordinate with six declared delay terms, coil
  electrical model, D7-003 safety envelope + dummy-load-first, sweeps +
  ten-branch factorial control matrix with seeded blinding,
  cross-correlation fidelity, signal-level function-generator presets);
  timing programme schema + example; claims H-24..H-30 (node-menu rows
  H-24..H-28); docs `COIL_LASER_TIMING_AND_PHASE.md`,
  `EXPERIMENTAL_PROGRAMME.md`.
- Agent 08: platform tranche T1 — **V2-WIN-01 fixed** (POSIX zip
  arcnames; vertical slice fully green on Windows), specimen-listing
  defect re-diagnosed as missing `jsonschema` (deps declared), Windows CI
  matrix; `rgcs_core/fea_export` (sha256-verified material-card contract),
  `rgcs_core/crystal_db` (schema-versioned persistence + migration),
  `rscs_core/memory/persistence` (H-15/H-17/H-19 machine-tested);
  headless desktop services (provenance graph, waveform/timing preview,
  phase-budget rows); SCAD v7 fixes D-02 with CAD provenance notes;
  HG Embedded OS contract + app-manifest schema; quantified DDS/TCXO/PLL/
  CPLD roadmap (FPGA explicitly not justified). Docs:
  `SOFTWARE_HARDWARE_ARCHITECTURE.md`, enterprise-doc addenda.
- Agent 09: the four v3 manuscripts (RSCS Foundations, RGCS Crystal
  Application, Software & Hardware Roadmap, Historical & Source
  Companion) — XeLaTeX, shared preamble, every number generated by
  `tools/make_v3_artifacts.py`, packaged with per-manuscript
  CHECKSUMS/VERSIONS/BUILD by `tools/package_manuscripts.py`; layout QA
  0 undefined refs / 0 overfull boxes (`docs/LAYOUT_QA_REPORT_V3.md`);
  README v3 header + public Lessons Learned section; QA-D-02 verified
  fixed in the v2 bib and closed.
- Agent 10: independent adversarial QA — fresh `QA_REPORT_V3.md` (22
  dimensions), `CLAIM_AUDIT_V3.md`, `REPRODUCIBILITY_AUDIT_V3.md`,
  defect-register addendum documenting D-V3-01 (coordinate count 18→17),
  D-V3-02 (figure PDFs carry CreationDate), D-V3-03 (CITATION.cff still
  v2) BEFORE fixes; gate recommendation YELLOW → GREEN after Agent 11
  repairs.

### Changed
- `pyproject.toml`: project renamed `rgcs-v3` 3.0.0a1 (D3-001); missing
  `pyyaml` dependency declared (fixes V2-PKG-01 for v3 builds); `rscs_core`
  packaged with its registry yaml.
- v2 release artifacts moved unchanged to `archive/v2.0.0/release/`;
  top-level `release/` reserved for v3 outputs.

## [2.0.0] — 2026-07-14

Frozen baseline. See `archive/v2.0.0/release/RELEASE_NOTES.md`.




