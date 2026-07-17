# V4X defect register (Q01)

Defects found by the v4.2.1 completeness audit against the tagged
v4.2.0 expansion candidate. **Every defect was registered before it was
fixed** (Q01 rule), and every P0/P1 carries a regression test.

Severity: **P0** scientific integrity · **P1** completeness or a
misleading public statement · **P2** hygiene.

| ID | Sev | Defect | Status |
|---|---|---|---|
| V4X-D-004 | P1 | release notes claim 681 tests; the report at the same commit says 682 | CLOSED |
| V4X-D-005 | P1 | cusp metric measured its own sampling density | CLOSED |
| V4X-D-006 | P0 | C05 metrology was registry-only, labelled as implemented | CLOSED |
| V4X-D-007 | P0 | T-lane status laundering: 18 claimed validated, 6 had models | CLOSED |
| V4X-D-008 | P1 | C01 lacked the mandatory strong-coupling criterion | CLOSED |
| V4X-D-009 | P1 | 47 required standalone documents missing (1/38 agents complete) | CLOSED |
| V4X-D-010 | P1 | the P02 orphan sweep was never run | CLOSED |
| V4X-D-011 | P1 | "sub-millimetre refinement" ran at 8.0/5.5/4.5 mm | CLOSED |
| V4X-D-012 | P1 | G42 verified strings, not artifacts | CLOSED |
| V4X-D-013 | P1 | arithmetic identities carried CORE_VALIDATED | CLOSED |
| V4X-D-014 | P2 | C02 scratch meshes shipped in source assets | CLOSED |

**No open P0 or P1.**

---

## V4X-D-006 (P0) — registry-only work labelled implemented

The ledger satisfied the C05 metrology workstream by pointing at
`harmonic_family.specimen_registry()` — a table of declared seller
values. The C05 prompt required a metrology pipeline: calibrated
measurement records, seller-vs-measured separation, uncertainty
propagation, XRD orientation, scan-to-mesh.

**None of it existed.** A row with an owner, an artifact string, and a
status looked identical to a delivered workstream.

Fix: `rscs2_core/metrology.py` (9 public functions, 9 tests). Seller
values cannot become measurements — enforced in the constructor. XRD
returns `INTERFACE_ONLY` rather than inferring axes from facets.
Malformed scans are refused, not repaired.

Regression: `test_seller_values_cannot_become_measurements`,
`test_xrd_never_infers_axes_from_facets`,
`test_scan_to_mesh_refuses_to_repair`.

## V4X-D-007 (P0) — status laundering in the consciousness lane

18 of 52 entries claimed `REDUCED_ORDER_VALIDATED`. Only 6 had models.
All 52 pointed at a single registry file as their artifact.

`REDUCED_ORDER_VALIDATED` asserts that a model exists, runs, and is
tested. For 12 entries — including "Holographic Ring Attractor
Lattice", "quantum cognition", "active inference" — **nothing ran**.

Fix: implemented 5 real models (`ring_attractor`,
`phase_amplitude_coupling`, `order_effect_model`/`qq_equality`/
`classical_comparator`, `subjective_time`); **downgraded 7** to
`SOURCE_HYPOTHESIS` with the reason recorded in the entry itself.
`model_symbol` is now a required, verified field.

Regression: `test_reduced_order_claims_have_models` — a validated
claim must name a callable that exists.

## V4X-D-005 (P1) — the cusp metric measured its sampling

The audit brief suspected post-hoc test acceptance ("the test expected
>5× and was changed after observing ~1.44×"). **The premise was
wrong**: `git log -S` shows the 5× threshold in exactly one commit,
never modified.

The real defect was in the metric. It summed over path *samples*, and a
log spiral sampled uniformly in θ crowds samples at its centre:

| | inner 10% radius |
|---|---|
| fraction of **samples** | 69.5% |
| fraction of **arc length** | 9.3% |

So a **uniform** field scored 0.695 — the metric was reporting the
grid. Arc-length weighting fixed it (uniform → 0.0928, matching the
arc-length fraction to four decimals; concentrated/uniform = 10.576).

The fix is justified by an **independent analytic control**, not by the
test passing. Regression:
`test_uniform_field_metric_equals_arclength_fraction`.

## V4X-D-011 (P1) — "sub-millimetre" at 4.5 mm

The v4.2.0 document titled its work a *sub-millimetre refinement*. Its
finest characteristic length was **4.5 mm** and its finest element
spacing **4.096 mm** — off by an order of magnitude from the claim in
its own title.

The body text was honest about the numbers; only the framing oversold.
Fix: renamed the preliminary ladder for what it is, and ran a genuinely
finer ladder ([EYE_REFINEMENT_V5.md](EYE_REFINEMENT_V5.md)).

## V4X-D-012 (P1) — G42 verified strings

The v4.2.0 G42 checked that every ID had an owner string, an artifact
string, and a status. All three are satisfiable with any nonempty text,
so "248/248 coverage" proved only that 248 rows had been typed.

Fix: gates **G42A–G42G** verify paths exist, symbols import, sources
resolve, tests exist, docs exist, status is legal for the delivered
depth, and blocked rows name their blocker and next action. 268 rows;
all seven pass.

## V4X-D-013 (P1) — arithmetic identities wearing a physics status

`F002: 20.480 kHz = 4096*5 — CORE_VALIDATED`.

The arithmetic is exact. The status reads as "20.48 kHz is a validated
resonance". This is the numerology trap expressed as a status field,
and nine registry entries had it.

Fix: any arithmetic-kind record at `CORE_VALIDATED` now automatically
carries `ARITHMETIC ONLY: ... not a claim that the value is a resonance
of any quartz body`, enforced by G42F and by
`test_arithmetic_identity_never_wears_a_physics_status`.

## V4X-D-014 (P2) — scratch-data audit

The audit asked whether `docs/v4/proof/C02/scratch/` is tracked,
whether it enters release assets, whether it is reproducible, and
whether it is a required proof artifact. Verified directly against the
tree and the built asset:

**`docs/v4/proof/C02/scratch/` — clean.** Not tracked (`git ls-files`
returns only the three ladder JSONs) and **not** in the v4.2.0 source
zip. Only `refinement_ladder.json`,
`driven_phase_diagnostics.json`, and `frequency_sensitivity_map.json`
ship. The meshes regenerate on demand via
`tools/v4x_eye_refinement_run.py`.

**`evidence/v4/agent05/scratch/` — ships, and is legitimate.** 21
entries reach the source zip. Despite the directory name these are
**not** unexplained intermediates: every `.msh` is accompanied by its
`.geo` source and a `.manifest.json` carrying `gmsh_cmd` (the exact
producer command), `nodes_sha256` and `tets_sha256` (content hashes),
element counts, mesh quality, and a `volume_rel_err` check against the
analytic volume. That is already "a properly manifested proof-data
package with hashes and producer commands".

Disposition: **the content satisfies the rule; the directory name does
not.** Calling a manifested, hashed, reproducible proof package
"scratch" invites exactly the suspicion this audit arrived with. The
name is recorded as misleading and left in place, because the directory
is v4.0-era evidence referenced by existing manifests and tests, and
renaming frozen evidence to improve a label would be a worse trade than
documenting it. No unexplained scratch data ships.
