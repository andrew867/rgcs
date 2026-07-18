# RGCS v4.6 — Crystalline Spacetime Coordinate Program (CSCP) ledger

Run ledger for the v4.6 programme. One row per agent, appended as work
lands. **Nothing in this programme is physical evidence.** Every
physical hypothesis is `UNTESTED` unless a calibrated bench record with
apparatus provenance exists — and none does.

- Branch: `v4.6-cspc`, cut from verified `main` @ `8bda6e8` (v4.5.2).
- Baseline: [`BASELINE_V4_6.json`](BASELINE_V4_6.json) (RELEASE_EVIDENCE).
- Doctrine constants: [`cspc/__init__.py`](../../../cspc/__init__.py) —
  evidence ladder, 8 transfer firewalls, excluded claims.
- Verdict contract: the final token may only be emitted when every
  software gate is green **and** all physical claims remain untested.

## Originating question (RQ-CSPC-001)

> Can crystalline resonators provide a physically meaningful bridge
> between stable phase, cross-domain frequency conversion, temporal
> order, spacetime measurement, and the much stronger idea commonly
> described as space-time travel?

The programme does **not** assume the answer is yes. Success does not
require supporting the originating hypothesis; publishable null results
are a success condition.

## Standing corrections carried into v4.6

| id | correction | status |
|----|-----------|--------|
| CSPC-CORR-001 | 2.45 GHz is not a unique fundamental resonance of water | carried from source ingest |
| CSPC-CORR-002 | `0.035652…` retains **Hz** units in the recovered equation | carried |
| CSPC-CORR-003 | the 11th powers-of-eight level is **not** an 11th octave | carried |
| CSPC-CORR-004 | arithmetic relationships do not establish coupling or spacetime travel | carried |
| CSPC-CORR-005 | source precision does not confer measurement precision (a 16-digit decimal derived from a nominal 2.45 GHz input carries the input's significance, not 16 digits) | carried |

## Defects found and fixed during the programme

| id | defect | resolution |
|----|--------|-----------|
| CSPC-D-001 | `compute_source_hash` (v4.5.2 anti-stale guard) hashed **raw bytes**, so a Windows checkout with `core.autocrlf=true` re-materialised `.py` files as CRLF and reported a spurious source mismatch for identical source. A genuinely fresh binary would fail `--build-info` verification after a clean clone or branch switch. | Normalise CRLF→LF before hashing; regression tests assert both line-ending invariance and that a real edit still changes the hash. Failure mode was fail-safe (never passed a stale binary as fresh). |
| CSPC-D-003 | The statistical null model matched only the **magnitude range** of the observed corpus, not its arithmetic granularity. Nulls were rounded to a fixed 10⁻⁶ grid, giving them denominator 10⁶ and enormous rational complexity, while every real corpus is integers. Result: *every* corpus — including the deliberate negative control — scored "simpler than chance" at the p-floor with effect sizes to −42 SD. The test was detecting "real frequency tables use round numbers". | Nulls now reuse the denominator of the observed member they replace, matching magnitude **and** granularity. Re-run: the positive control (just intonation) is detected at −6.8 SD and the irrational control (equal temperament) is correctly *not* detected (p≈1.0). Regression test pins denominator matching and determinism. |
| CSPC-D-004 | Control mislabelling. `MUSICAL_A440` (equal temperament) was declared a *positive* control, but 440·2^(n/12) is irrational by construction and cannot be rationally simple; `ISM_BANDS` was declared a *negative* control but 13.56/27.12/40.68 MHz are harmonically related round numbers chosen by regulators. | Split into `JUST_INTONATION` (true positive control, small-integer ratios) and `EQUAL_TEMPERAMENT` (irrational control that must NOT be detected). ISM reclassified as a true detection of human convention. Both controls asserted in tests. |
| CSPC-D-002 | Local `main` was stale at v4.4.0 because releases were fast-forwarded with `git push origin v4-dev:main`, which updates the remote ref only. Branching "from main" silently produced a v4.4.0 tree. | Branch reset to `origin/main`; local `main` re-pointed. Verified v4.5.2 content present before proceeding. |

## Agent ledger

| agent | workstream | commit | evidence class | physical status |
|-------|-----------|--------|----------------|-----------------|
| A00 | Baseline, branch, release isolation | `4d79b20` | RELEASE_EVIDENCE | UNTESTED |
| A01–A03 | Provenance, dimensional/precision audit, exact fixtures | `82990d2` | SOURCE_CLAIM / DERIVED_ARITHMETIC | UNTESTED |
| A04–A07 | Coordinates, ladder, frozen nulls, corpus decoder | `9ab26be` | NUMERICAL_SIMULATION | UNTESTED |
| A08–A11 | 64-tetrahedron ambiguity, constructions, spectra, nulls | `f36ff50` | DERIVED_ARITHMETIC | UNTESTED |
| A12–A17 | DDS/NCO, phase closure, clock model, RF safety | `e4eb982` | DERIVED_ARITHMETIC / ANALYTIC_MODEL | UNTESTED |
| A18–A29 | Experiments, spacetime metrology, firewalls | `18e59a0` | ANALYTIC_MODEL | UNTESTED |
| A30–A36 | Workbook integration, findings, adversarial, release prep | `caa15c3` | RELEASE_EVIDENCE | UNTESTED |

## Release gate status

| gate | state | evidence |
|------|-------|----------|
| all tests green | **PASS** | 1062 passed, 6 skipped, 1 deselected (local, full suite) |
| QA audit green | **PASS** | `qa_audit_v4.py --fast` 19/19 |
| metadata guard consistent | **PASS** | 1062 across 3 documented sites |
| adversarial campaign | **PASS** | 17 attacks, all refusals hold |
| workbook integration | **PASS** | 21 sheets incl. 4 CSCP; 16 prior workbook tests still pass |
| hosted CI green | **PASS** | run 29640235954, all 10 jobs success (was queued on a runner backlog, later cleared) |
| binary freshness proven | **PASS** | frozen `--build-info` reports 4.6.0 @ `a04b910` with matching source hash |
| installer first-run path tested | **PASS** | 6 frozen-binary tests incl. the installer's exact `--first-run` command; no `--first-run` directory created |
| tag + publish | **PASS** | `v4.6.0-rc1` + `v4.6.0` at `a04b910`; 12 assets published |
| remote asset verification | **PASS** | portable ZIP, Setup.exe and workbook re-downloaded — hashes match; the downloaded binary reports 4.6.0 @ `a04b910`, resolves `--first-run` to the wizard, builds 13 panels; workbook shows 21 sheets incl. 4 CSCP |
| claim boundaries visible | **PASS** | workbook shows exact vs physically-supported precision per candidate; travel claims render `UNSUPPORTED` |
| manuscript updated | **PASS** | `docs/RGCS_V4_TECHNICAL_MANUSCRIPT.md` §12 + extended Limitations |

**All software gates are satisfied, so the final verdict token is
emitted.** It certifies software only: every physical hypothesis in the
programme remains UNTESTED, no apparatus was built, and no measurement
was made.

Remaining honest gaps, unchanged by the release: the installer is
UNSIGNED, no clean-VM install cycle was run for v4.6.0, and the
programme's own candidate register is circular by construction.

## Binary freshness

The baseline records whether `dist/` matches current source. At
programme start it is **STALE by construction** — the v4.5.2 binary
predates the `cspc` package — and that is the honest answer, not a
defect. Packaging (A35) re-freezes from the final source; the v4.5.2
guard refuses to package a mismatched tree.
