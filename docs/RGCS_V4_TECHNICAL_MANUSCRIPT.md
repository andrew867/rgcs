# RGCS v4 / RSCS 2.0 — Technical Manuscript

**Scope statement (binding, per the v4 required wording):** all v4
results are **computational**. The historical "eye" is a **Source
claim**; computed candidates are **diagnostics**, not discoveries; **no
experimental confirmation exists** for any coupling, region, or effect
described here; the eye engine **may return no candidate**, and for the
canonical crystal it returned a conventional explanation. The **CPU
float64 path is the numerical authority**; GPU statements reflect
**measured device evidence only**. The **nominal (110.000000 mm)** and
**ideal (110.037667410714… mm = 770.263671875/7, arithmetic)**
geometries are **distinct** and never interchanged.

## 1. Architecture

v4 adds `rscs2_core` beside the frozen v3 packages (`rgcs_core`,
`rscs_core` — tags v3.0.x, untouched). New mathematical objects are
registered in the append-only RSCS2 registry with id, units,
classification, provenance, exclusions, and tests (44+ objects at
release). gmsh runs as an external subprocess only (GPL isolation).

## 2. Validated CPU solver (RSCS2-E.1..E.3, S.1..S.4, B.1..B.5)

Second-order tetrahedral vector FEM (scikit-fem), generalized
eigensolve with shift-invert and a deterministic ARPACK start vector
(V4-D-003). Anchors: Euler–Bernoulli cantilever (<0.5% converged),
Timoshenko thick beam (+0.03%), static tip deflection, exact cube Lamé
mode (Demarest 1971; +0.03–0.05%, ν-independent), constrained-bar
P-wave ladder against the frozen Z-axis speed. Boundary machinery:
free/fixed/Robin/surface-mass with limit tests. Defect V4-D-001 (mass
form) is documented with its permanent guards.

## 3. Anisotropic quartz (Agent 04)

Full 3×3×3×3 stiffness from the frozen Voigt constants; Christoffel
speeds reproduce the frozen v3 axes to 1e-9; trigonal class-32
symmetry (120° Z invariance) and Bond-rotation frame invariance are
pinned by tests; orientation sweeps (V.6 conservative extension).

## 4. Canonical 110 mm crystal (Agent 05)

Hexagonal faceted body, SP-Q154 diameter ratios (40/154, 30/154),
face-slope angles 51.843°/60°, across-vertices diameters, frozen v2
cap-height/area helpers. Machine-exact analytic volume matched by the
mesh to 1e-9; deterministic gmsh meshes (SHA256-stable). Ideal and
nominal variants carry exact, distinct lengths.

## 5. Piezoelectricity (Agent 06)

Stress-charge saddle formulation, P2/P2, static condensation with
gauge; single-element energy patch (1e-9) pins tensor order and sign;
e=0 recovers elasticity exactly; short/open electrode conditions with
physical k_eff²; reversal antisymmetry.

## 6. Acceleration (Agent 07)

OpenCL Christoffel kernel with closed-form symmetric-3×3 eigenvalues.
Real hardware: Intel Iris Xe (fp32) 6.6 ms vs 346.6 ms fair CPU
closed-form baseline at 500k directions, parity 3.4e-05 (< 2e-4
registered); i5-1135G7 CPU-CL (fp64) parity 1.8e-14. Kernel status:
MULTI_DEVICE_REPRODUCED. CUDA: INTERFACE_TESTED only. Explicit
backends never fall back silently.

## 7. Projections (Agent 08)

Ghosh (1999) Sellmeier indices anchored to the frozen handbook values;
vector Snell pinned to the frozen scalar law; probe-path menu
(geometric centre / frozen node prior / eye-candidate slot, null);
photoelastic phase projection; Jones elements on the frozen RSCS-C.9
state; Biot–Savart coil pair (exact on-axis anchor; div B = 0);
modal drive projection (Mφ_k → e_k exactly); leakage-gated coupling
records. The octave wavelength presets (c/2⁴⁹, c/2⁴⁸) are arithmetic
statements only.

## 8. Eye diagnostics and consensus (Agent 09)

Sixteen registered diagnostics (all Derived; never Established) and a
sequential multi-criterion consensus: family-deduplicated agreement,
localization, validity, null comparison, mesh persistence (required
for any STABLE verdict — V4-D-004), boundary sensitivity, mode
dependence, uncertainty persistence. Adversarial battery: planted
candidate found; flat/noise/outside/collapse/artifact/boundary cases
all rejected correctly; NO_STABLE_CANDIDATE is a first-class outcome.

**Canonical result (corrected, V4C-D-001):**
UNCERTAINTY_OVERLAPS_CONVENTIONAL_NODE — one 3-family region at
(−0.295, −0.205, 102.240) mm near the male cap/shaft junction, an
exactly reported **3.906 mm** from the nearest ordinary node/antinode
station at (−0.447, 0.774, 106.018) mm. The separation is real and
preserved; at the current mesh-dominated localization uncertainty
(±3.08 mm per side) the intervals overlap, so the implemented
conventional model MAY explain the feature — deliberately weaker than
"explains". The candidate is unambiguously distinct from the
geometric centre (~47 mm) and the frozen RGCS node prior (~50.6 mm);
the junction plane (~0.4 mm away) remains a viable, untested
conventional explanation; mesh levels near clmax ≈ 4 mm would
discriminate. The v4.0.0 release used a proximity-threshold rule
(defect V4C-D-001, corrected in the v4.1.0 line; v4.0.0 records are
frozen history). `eye_coordinate` remains null everywhere.

## 9. Reference systems (Agent 10)

Cavity vs exact Helmholtz spectrum (1.7e-4, degeneracy resolved);
base-fixed tuning fork weak-coupling pair (S₀ = 8.70 Hz, CMR 0.26);
V.9: the frozen two-mode model tracks FEM avoided-crossing splitting
within 6.4% under Rayleigh tip-mass detuning. The free fork's
strong-coupling regime is documented as a diagnosed pitfall.

## 10. Reproducibility (Agents 11–12)

One deterministic command builds the 111-file proof bundle
(bit-identical data artifacts across builds; SHA256 manifest); the
`rgcs-v4` CLI exposes every capability; a 10-step scripted demo runs
from a clean workspace to exit 0 with runtime/memory/hash records.

## 11. QA (Agent 13)

Independent adversarial audit (19 programmatic checks), defect
register V4-D-001..004 (all closed, each with a regression test),
domain audits, and the G1–G30 gate table in
RELEASE_RECOMMENDATION.md.

## 12. Crystalline Spacetime Coordinate Program (v4.6, agents A00–A36)

A source-motivated programme translating 4096 / 64 / 2.45 GHz /
visible-light relationships into exact software, statistical nulls,
and falsification structure (`cspc/`). **Software verified, physical
untested**: no apparatus was built and no data collected. Full account
in [CSCP findings](v4/cspc/CSCP_FINDINGS.md); ledger and defect
register in [programme ledger](v4/cspc/PROGRAMME_LEDGER.md).

**Method.** Frequencies are exact `Fraction` quantities carrying SI
dimension vectors, with empirical significance tracked *separately*
from arithmetic exactness. Seventeen candidates reproduce frozen
decimal fixtures. Statistical work uses a hash-pinned simplicity
metric (rational complexity of the exact ratio, no free parameters),
frozen before any corpus was evaluated, with granularity-matched nulls
and Holm–Bonferroni / Benjamini–Hochberg correction.

**Results, which are largely null.**

1. *Precision does not survive its input.* `2.45e9 / 8^9` is exactly
   18.25392246246337890625 Hz and, because 2.45 GHz is nominal at
   three significant figures, is 18.3 Hz as physics.
2. *The simplicity metric measures human convention.* Everything
   surviving correction is either constructed from its own reference
   or a table of round numbers (ISM allocations, binary clock
   crystals). The programme's own candidate set scores "simple" and is
   flagged circular.
3. *4096 = 64² is counting.* Every 64-element structure has 4096
   ordered pairs. Across four non-isomorphic constructions the
   geometric lattices are unusually *poorly* connected against
   degree-matched nulls; none is specially synchronizable.
4. *Ideal phase closure is not realizable by default.* On a 100 MHz
   reference the common closure window for 4096/20480/40960 Hz
   degrades from 1/4096 s to ≈42.9 s; a binary reference oscillator
   (2²⁶ Hz) restores exactness. Exactness is an engineering choice.
5. *Spacetime.* The weak-field clock model reproduces Pound–Rebka and
   the GPS correction (net +38.44 µs/day). Resonators are metric
   *instruments*: an optical clock at 1e-18 resolves ~9 mm of height.
   A 100 W, one-hour apparatus implies a Schwarzschild radius of
   5.9e-39 m — 23 orders of magnitude below a proton radius.

**Corrections carried.** 2.45 GHz is not a unique resonance of water
(Debye loss peaks near 19.2 GHz; the ISM band carries ~25% of peak
loss and the response is relaxation, not resonance); the supplied
"fractal relationship" retains hertz and is a 36-bit DDS resolution
step; `8^11 = 2^33` is thirty-three octaves, not eleven; the
"64-tetrahedron grid" phrase remains underdetermined.

**Boundaries.** Eight transfer firewalls are enforced in code, and all
five travel-adjacent claims are recorded `UNSUPPORTED` with the
specific evidence each would require. None of that evidence exists.

## 13. Phase Memory, Worldline Channel Recovery, and the Phryll
## Translation Hypothesis (v4.7, agents A00–A83)

A typed chain — phase authority → generated state → transduction →
propagation → observation → bounded reconstruction → evidence claim —
with each stage a distinct type and estimation the only way back up
(`pmwr/`). **Software verified, physical untested.** Full account in
[PMWR findings](v4/pmwr/PMWR_FINDINGS.md).

**Method.** A phase authority couples frequency to epoch, timescale, a
nine-state synchronization machine, and a cycle count that only
`PHASE_LOCKED` may assert. Finite-Q memory ends at the earlier of
amplitude death and phase diffusion; beyond it the state is
`CYCLE_COUNT_UNKNOWN` and perfect-memory claims are refusals.
Recovery runs behind an identifiability gate (rank, conditioning,
posterior width) and returns `REFUSED` rather than a guess.

**Results.**

1. *Exact closure is a delay alias.* The 1/4096 s closure window of
   the binary family is an alias grid (4097 indistinguishable delays
   per second); a second, coprime lattice extends the unambiguous
   range by ×4096. The v4.6 synchronization feature and the v4.7
   ambiguity are the same arithmetic fact.
2. *Worldline-indexed phase is metrology.* Weak-field proper-rate
   offsets reproduce the validated fixtures (LEO negative, GPS
   +38.5 µs/day); receivers on different worldlines accumulate
   different proper phase, and arrival reordering is delay geometry —
   the audit cannot emit a "causal reversal".
3. *The pyramid ratio is a geometry identity.* 2a/h at 51.843° is
   1.5714157792, within ~5×10⁻⁴ of π/2 — a statement about a chosen
   angle's tangent, carried as `GEOMETRY_IDENTITY` /
   `ANTHROPOGENIC_STRUCTURE`, with the mechanism reading refused.
4. *Phryll stays unresolved by construction.* The source term is
   operationalized as a five-rung ladder in which a residual requires
   all eleven ordinary output channels bounded plus a sham-drive
   control (the source's own power-not-engaged episode is preserved
   as the warning), and no detected-state exists anywhere in v4.7.

## 14. R3: Root Space, Phase Lens, Optical Spin, HAL Memory, Atlas
## (v4.7.x, agents A00-A96)

The R3 correction: zero wrapped residual is never a root -- it admits
integer-cycle aliases. A root is one of six typed, calibrated,
alias-resolved, gauge-declared relational reference states (`r3/`),
and the root-lock certificate's ceiling is a BOUNDED relational lock;
absolute vacuum roots and non-local preferred frames carry standing
UNSUPPORTED statuses. Supporting lanes: an adjoint-verified anisotropic
phase lens with refusal of unregularized inversion; exact 8^d
tetrahedral addressing whose destination certificates demand frame,
epoch, metric, ephemeris and calibration; spin/torsion typing in which
categories never merge and Einstein-Cartan torsion from any laboratory
source is stated at its true ~1e-25 1/m scale; an inverse Einstein
calculator that prices metric wishes in unpayable mass budgets;
SAM/OAM-separated optical spin with dose ceilings and finite
relaxation; synthetic-only HAL memory behind a consent gate; and a
nested tetrahedral atlas whose null-rotation campaign is the standing
refutation of grid-orientation claims. Full account:
[R3 findings](v4/pmwr/R3_FINDINGS.md).

## 15. R4: Tetrahedral Spin-Addressed Codec and Four-State Memory
## Qualification (v4.8, agents A00-A63)

An exact radix bridge (4096 = 8^4 = 4^6 = 2^12, verified exhaustively
over all 4096 keys), a multiresolution codec with full bit accounting,
and a physical four-state platform qualification (`r4/`).
**Software verified, physical spin untested.** Full account:
[R4 findings](v4/r4/R4_FINDINGS.md).

*Radix conversion contributes zero compression* — the same twelve bits
in another base — and the claim is refused in code with a
`RAW_QUATERNARY` baseline that costs exactly what flat binary costs.
Real compression is measured against fair baselines with topology,
address, codebook, symbol, entropy-model and residual bits all
counted. The honest outcome: the hierarchy beats quantizer baselines
on piecewise-constant payloads, *loses to general-purpose DEFLATE on
that same data*, and offers nothing on smooth, sparse or ramp
payloads; the random-data negative control correctly shows no gain
anywhere.

*Four spin-1/2 directions are not four states.* The tetrahedral SIC
frame (overlap −1/3, Σn_i = 0, Σn_i n_iᵀ = (4/3)I) is an
informationally complete measurement representation, and its outcome
object refuses to act as storage. Spin-3/2 is the strongest native
four-level candidate, with its real limitation recorded: common optical
readout resolves |m_s| pairs, so the readout engine returns an explicit
ERASURE rather than guessing a sign. Quartz remains BLOCKED with all
ten stop-matrix gates open, and no bench stage is runnable because no
apparatus exists.

## Limitations

The R4 programme adds these: compression results are on synthetic
corpora only and the codec is beaten by an off-the-shelf general
compressor on its own best case; the digital twin is analytic with no
fitted instrument data; the 4x4 confusion matrix is synthetic; and no
four-state write, read, or reset has been performed in any material.

## Limitations

The R3 programme adds these: root locks are demonstrated on synthetic
channels against declared references only; the lens forward model is
synthetic; the atlas campaign refutes orientation claims but cannot
survey real landmark corpora it was never given; and the HAL memory
lane is a synthetic model with no biological claim of any kind.

The v4.7 programme adds these: every crystal-translation statement is
a `SOURCE_CLAIM` with a preregistration around it — no apparatus
exists; recovery quality is demonstrated on synthetic channels under
the frozen evaluation contract only; the worldline channel model is
weak-field and O(v²/c²); and the Phryll ladder's upper rungs are
unreachable without independent replication that no one has performed.

The v4.6 programme adds these: its candidate register is circular by
construction (built from the references it is scored against) and must
not be cited as independent structure; the simplicity metric detects
number-choosing convention and cannot distinguish "chosen by humans"
from "preferred by nature"; every experiment is a preregistration with
no apparatus and no data; and the spacetime lane establishes only
measurement sensitivity, never metric control.

See proof bundle `reports/LIMITATIONS.md`: STEP export untested
(declared); phase diagnostics require driven complex responses;
consensus covered 4 elastic modes × 2 mesh levels × 1 boundary
variant × 3 material draws; acceleration evidence is device-specific;
cross-platform bit-identity is not claimed (tolerance-level CI only).
