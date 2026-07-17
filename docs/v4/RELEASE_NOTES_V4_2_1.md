# RGCS v4.2.1 — release notes

**Master Research Expansion, completeness-audited.**

v4.2.1 is the corrected, published form of the v4.2 expansion. The
`v4.2.0` tag remains immutable at `d253c2f` and is recorded as a
**CI-green tagged expansion candidate whose release publication was
blocked before completion**. It is superseded, not rewritten.

Every prior tag (v2.0.0, v3.0.x, v4.0.0, v4.1.0, v4.1.1) is untouched.

## Read this first

**Nothing in this release is an experimental result.** Every
experimental campaign is a protocol. No hardware was operated, no
specimen was measured, no water was exposed, no person participated.
A protocol is not a completed experiment.

**The Eye question is resolved — computationally — and the answer
changed.** See below.

## Why 4.2.1 exists

A completeness audit of the v4.2.0 candidate ran every attack the QA
prompt requires. **Seven of them succeeded.** The headline finding:

> v4.2.0 reported "coverage ledger 248/248, all gates green". That was
> true and meaningless at the same time — the gate verified that every
> ID had an owner **string** and an artifact **string**. Both are
> satisfiable with any nonempty text.

What was hiding in that gap:

- **C05 metrology** was a registry of seller values wearing an
  implemented workstream's status. There was no metrology pipeline.
- **The consciousness lane** claimed 18 entries `REDUCED_ORDER_VALIDATED`
  while only 6 had models; all 52 pointed at one registry file.
- **The orphan sweep — the agent whose job was to check the 248 against
  the corpus — had never been run.** Running it found 20 more ideas.
- **47 of the ~50 required standalone documents did not exist.** Only
  1 of 38 agents had its full deliverable set.
- Release notes said 681 tests; the report from the same commit said
  682.

## What changed

**Coverage contract (G42A–G42G).** The gate now verifies mechanically:
every path exists, every symbol imports, every source resolves, every
row has a test or a falsification condition, every row has
documentation, **the status is legal for the delivered implementation
depth**, and every blocked row names its blocker and its next action.
**268 rows** (248 fixed + 20 orphans). All seven pass, release-blocking.

**Implementation depth.**
- `rscs2_core/metrology.py` — new. Seller values cannot become
  measurements (enforced in the constructor); XRD returns
  `INTERFACE_ONLY` rather than inferring axes from facets; malformed
  scans are refused, not repaired.
- BVD — open-short-load calibration, multi-branch detection that names
  unmodelled dips instead of calling them noise, identifiability
  reporting, electrode loading, SPICE export.
- Apparatus — coil resistance/inductance/field/power/skin depth,
  Biot-Savart field maps agreeing with the analytic formula to 1 part
  in 10⁴, thermal limits, Hertzian contact loading, transducer transfer
  functions, cable loading.
- Polariton — `strong_coupling_criterion`, which the C01 prompt made
  mandatory ("no strong-coupling claim without comparing splitting to
  losses") and which was absent.

**Status honesty.** 7 consciousness entries **downgraded** to
`SOURCE_HYPOTHESIS` with the reason recorded in each entry; 5 real
models implemented (ring attractor, phase-amplitude coupling, quantum
order effects + the parameter-free QQ equality + a classical
comparator, subjective time). `model_symbol` is now verified by test —
a validated claim must name code that runs.

Nine frequency entries carried `CORE_VALIDATED` on arithmetic
identities (`F002: 20.480 kHz = 4096*5`). The arithmetic is exact; the
status read as "20.48 kHz is a validated resonance". Every such record
now carries an automatic **ARITHMETIC ONLY** note, enforced by G42F.

**The cusp metric.** The audit suspected post-hoc test acceptance. The
premise was wrong — the 5× threshold was never changed — but the metric
was worse: it summed over path *samples*, and a log spiral crowds
θ-uniform samples at its centre, so a **uniform** field scored 0.695.
Arc-length weighting fixed it, validated against an independent
analytic target (uniform → 0.0928 = the arc-length fraction, to four
decimals). Concentrated/uniform is **10.576×** — a real focusing
effect, and a finite one.

**Orphans.** 20 registered, each with a mandatory disposition. The
source-lore terms (Phryll, portals, Atlantis, CERN, torsion, vortices)
are quarantined at SRC and preserved verbatim — **not** deleted and
**not** endorsed; they are source vocabulary held in a separate lane,
never imported into any solver. Two orphans are rejected **on
evidence** with the number cited. Nulls and contradictions preserved
(G48).

**Documentation.** ~50 standalone documents: every computational model,
all nine experimental protocols, all ten consciousness workstreams, the
data contract, the safety and ethics manual, the QA verdict, the defect
register, and the no-omission certificate.

**Release metadata.** Test counts are derived from an actual pytest run
into `docs/v4/RELEASE_METADATA.json` and verified across every document
by a guard, so 681-vs-682 cannot recur.

## The Eye — resolved, and the answer changed

The v4.2.0 ladder ran at 8.0/5.5/4.5 mm and called itself
"sub-millimetre". It returned `INSUFFICIENT_RESOLUTION` because its
halfwidth (4.096 mm) was **larger** than the separation it was meant to
judge (4.149 mm).

The v4.2.1 ladder ran at 3.0/2.0/1.5 mm (30 816 dof):

| Level | spacing | centroid (mm) | d(v4.1 coord) | d(station) |
|---|---|---|---|---|
| cl3.0 | 3.423 | (0.237, −0.010, 100.986) | 1.375 | 5.138 |
| cl2.0 | 2.362 | (−0.053, −0.038, 99.989) | 2.270 | 6.096 |
| **cl1.5** | **1.803** | **(−0.048, −0.020, 99.783)** | **2.476** | **6.298** |

**Verdict: `NEAR_CONVENTIONAL_NODE_BUT_DISTINCT`.** Halfwidth 1.803 mm
< separation 6.298 mm by 3.5×. The comparison finally carries
information, and **the conventional model does not explain the
candidate**. (Per V4C-D-001, "near" is descriptive; near-but-distinct
and distinct are both scientifically *distinct*.)

**And the v4.1 coordinate does not survive refinement.** The
candidate's distance from the recorded (−0.295, −0.205, 102.240) mm
*grows* with resolution — 1.375 → 2.270 → 2.476 mm — converging instead
on **(−0.048, −0.020, 99.78)**. At cl=1.5 there is no cluster at
z = 102.24.

The canonical v4.1 record is **preserved unchanged** (G07): it is a
faithful record of a computation done at ~4 mm spacing. What changes is
its interpretation — that coordinate is resolution-limited, not
converged. The candidate was never moved onto the comparator.

Convergence: transverse agrees to 0.02 mm across the last two levels;
axial shift falls 1.039 → 0.207 mm; f₁ converges 13772.75 → 13772.38 →
13772.28 Hz.

**Bounds.** Computational only. Ideal geometry, not a measured
specimen. First elastic mode. Assumed orientation — no XRD exists, and
the elastic model is orientation-dependent. Final shift 0.207 mm is
small but nonzero. `cl=1.25` was **not attempted**: measured 13.9 GB at
cl=1.5, projected ~45–71 GB at cl=1.25 against 31.6 GB of RAM. The run
stops and says so rather than thrashing.

**This is not "the Eye is real".** A resolvable strain-energy cluster
in a model is a property of the model. No measurement exists.

## Blockers (explicit)

| Blocker | Affected |
|---|---|
| Hardware required | E01–E05, E08, E09 (E001–E027, W001–W017) |
| **Ethics approval required** | E06 human loading, E07 operator state (H001–H017) |
| Compute (≳48 GB) | Eye ladder below 1.5 mm (or an LOBPCG/AMG solver) |
| Deferred by design | I001–I011 microscopic interfaces |
| No XRD | every specimen orientation is unknown |

## Verify

```bash
python -m pytest -q --deselect tests/regression/test_generator_determinism.py::test_generator_deterministic
python tools/v4x_coverage_gates.py          # G42A-G42G, 268 rows
python tools/v4x_prompt_pack_crosswalk.py   # per-agent deliverables
python tools/v4x_orphan_sweep.py            # 20 orphans, 0 undisposed
python tools/qa_audit_v4.py --fast          # 19/19
```

The deselected test is a byte-equality check requiring the archived
v2.0.0 build environment; hosted CI deselects exactly that node id per
policy D-V3-04, and its portable numerical twin runs everywhere.

## Documents

- [QA verdict](V4X_QA_FINAL_VERDICT.md) · [defect register](V4X_DEFECT_REGISTER.md)
- [No-omission certificate](V4X_NO_OMISSION_CERTIFICATE.md) · [orphan register](ORPHAN_IDEA_REGISTER.md)
- [Coverage ledger](V4X_COVERAGE_LEDGER.md) · [prompt-pack crosswalk](V4X_PROMPT_PACK_DELIVERABLE_CROSSWALK.md)
- [Programme report](V4X_PROGRAMME_REPORT.md) · [Eye refinement V5](EYE_REFINEMENT_V5.md)
- [What this quartz model does not include](WHAT_THIS_QUARTZ_MODEL_DOES_NOT_INCLUDE.md)
