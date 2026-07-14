# RGCS v2 — Claim Audit (Sub-Agent 08)

Date: 2026-07-14. Sampled claims across manuscript, docs, code, and UI, checked against `docs/SCIENTIFIC_CLASSIFICATION_POLICY.md` (Established / Derived / Hypothesis / Source claim) and gates 4, 5, 7. Verdicts: CORRECT (label present and right), MISLABELED, UNLABELED, FALSE.

## A. Manuscript claims (visual inspection of all 28 pages + tex grep)

| # | Claim (location) | Label carried | Verdict |
|---|---|---|---|
| 1 | Half-wave formula f=v/2L (p.6, Eq.5) | formula [EST], choice f₀=4096 Hz [SRC], 1-D applicability H-01a [HYP] | CORRECT — exemplary three-way split |
| 2 | "The celebrated 0.03% agreement … lives inside a ±5% band ~170× wider" (p.6) | [DER], explicitly "never presented as confirmation" | CORRECT — anti-numerology handling verified (0.0342%/5% ≈ 1/146–170, arithmetic checks) |
| 3 | Compact spectrum f_n²=f_b²+(nκ_χ)² (p.7, Eq.10) | [HYP] H-01, adaptation map from Lee–Tsai stated | CORRECT — analogy explicitly mathematical-only |
| 4 | Identifiability: report κ_χ, not (v_χ,R_χ) (p.8 §6.2) | [DER] | CORRECT — unidentifiable-parameter hazard is self-disclosed |
| 5 | Wave speed v̄_L=6310 m/s "imported uncited" (p.5) | [SRC], u_v=0.05 [HYP]/[DER] | CORRECT — source claim flagged as such |
| 6 | K_nm = πg_nm consistency requirement (p.13 §10.1, B.4, Fig.11) | presented as pre-registered requirement under [HYP] H-09 | **FALSE** — the stated map is mathematically wrong (QA-D-04); label discipline fine, content not |
| 7 | Coherence metric properties: pure tone→1, noise→b_w (p.14, Eq.25) | [EST] (metric property) | CORRECT — verified numerically (tone=1.0 exact; MC baseline ≈5% above theory, disclosed as "measured per pipeline") |
| 8 | Amplitude vs coherence "separate observables" box (p.13) | [EST] metric property | CORRECT — golden case (c) demonstrates order outliving amplitude; no amplitude/coherence conflation found anywhere |
| 9 | Case-(d) "ensemble Rayleigh Z_R=1.26, p=0.28" (p.16 caption, p.20 Table 8, tex:894) | [DER] | **MISLABELED/INCONSISTENT** — same statistic shown as 0.10/0.91 in the Fig.8 panel (QA-D-03) |
| 10 | Gan et al. shear damping: "Planck-scale coefficient … dimensionally meaningless for crystals and never imported" (p.15) | [SRC] + exclusion list D.2 | CORRECT — checked D.2: σ₁≃2.498 m_Pl on the binding exclusion list |
| 11 | "No hypothesis carries evidential status other than untested" (abstract, §15, §16) | — | CORRECT — Table 9 lists all 14 with failure conditions; archival negatives kept as amplitude-null, coherence-untested |
| 12 | Spontaneity test / drive-imprint trap (p.16 Fig.8, case f) | [EST] method, H-13 | CORRECT — pump-leakage trap dataset blocks the claim (p=6.4e−35), rendered badly (QA-D-15) |
| 13 | Reference [3] title/authors (p.23) | — | **FALSE** — reconstructed, not verified against the PDF (QA-D-02); ref [2] author names fabricated (QA-D-01); ref [1] verified correct |
| 14 | Ref [4]: "180 automated tests" (p.24) | — | MISLEADING — actual 203 (QA-D-17) |
| 15 | Human loading branch: "non-clinical bench procedure … no physiological measurement, health-related claim, or therapeutic framing" (p.18 §13.2) | boundary stated as absolute | CORRECT — gate 7 honored; no therapeutic/medical/cosmological/consciousness claim found in manuscript, docs, or UI strings |
| 16 | Numerology containment: powers-of-eight, 2.45 GHz, golden angle (p.28 D.4) | [EST] arithmetic / [SRC] significance | CORRECT — arctan√φ=51.827292°, Δ=−0.015708° quantified; "no golden-ratio equality claim" |

Classification-label coverage: every equation, table, and figure page inspected carries a colored tag; Table 10 (notation) labels each symbol; Table 11 (traceability matrix) labels every adapted element with its validation. **Gate 4: PASS.**

## B. Hypothesis completeness (gate 5)

Sampled H-05 and H-10 in `docs/ROADMAP_TO_FALSIFICATION.md` (lines 14, 21): both carry observable, controls, pre-registered failure condition, dominant-uncertainty statement, status "untested". Manuscript Table 9 lists failure conditions for all fourteen H-01..H-14; Table 6 lists observables and key controls per branch. **Gate 5: PASS** (spot-checked, structure complete).

## C. Code and UI claims

| # | Claim | Check | Verdict |
|---|---|---|---|
| 17 | Classification metadata on every claim-bearing public core function | machine-checked by `tests/unit/test_experiments_provenance.py` (walks the package) | CORRECT (test passes; sampled functions carry metadata) |
| 18 | Forbidden vocabulary absent from source | test covers `rgcs_core` only (QA-D-11); QA manually ran the checker over `rgcs_desktop` and `docs/USER_GUIDE.md`: clean | CORRECT today, coverage gap in process |
| 19 | "JSON serialization in which NaN/∞ always become null" (§17) | `to_jsonable` honors it, but `fit_exponential_decay`/`control_subtracted_metrics` can emit raw `inf` upstream (QA-D-12) | PARTIALLY CORRECT |
| 20 | Retired spiral closed form "may appear only as labeled approximation with printed error" (p.7) | `spiral.py` exposes `retired_closed_form_mm` with error field; test enforces labeling | CORRECT |
| 21 | Merit score S "ranks configurations … and is never evidence" (p.18) | docstring + manuscript agree; not used in any verdict path | CORRECT |
| 22 | `include_zero_mode` flag "stated with every spectrum citing Lee and Tsai" (p.8) | figures/tables checked: Fig.3/4 and Table 2 state the flag | CORRECT |
| 23 | Workbook formulas all ported or marked spreadsheet-only (gate 1) | 16 sampled: 13 exact matches/documented replacements, 3 unmarked gaps (QA-D-09) | MOSTLY CORRECT — 3 gaps |
| 24 | INCONSISTENCY_REGISTER D-13 residue "−0.328" | code/goldens/manuscript say +0.328 | **FALSE in register** (QA-D-08) |

## D. Scientific-review dimensions (brief §Scientific)

- **Unsupported equivalence:** none found — the "papers as mathematical templates only" rule is enforced at every use (substitution maps stated; D.2 exclusion lists binding).
- **Dimensional errors:** unit discipline verified clean (single, commented conversions matching NOTATION_AND_UNITS.md/DIMENSIONAL_ANALYSIS.md); the one dimensional-analysis blind spot is M.46's K term, dimensionally fine but structurally wrong (QA-D-04).
- **Numerology / post-hoc fitting:** actively contained (set-valued classes, scrambled-label nulls, D.4).
- **Omitted null models:** none — no-decay null, linear null, scrambled-index null all pre-registered.
- **Circular definitions:** none found; coherence baseline is measured, not assumed.
- **Unidentifiable parameters:** disclosed (§6.2, §16 item 4) rather than hidden.
- **Coherence without phase evidence / amplitude-coherence confusion:** the framework's central safeguard; correctly implemented (case c/d/f goldens).
- **Multiple comparisons:** Benjamini–Hochberg pre-registered (§13.1).
- **Source claims as fact:** the two bibliography defects (QA-D-01/02) are the only instances of source material misrepresented — ironic given the ledger discipline, and fixable from the PDFs on disk.
