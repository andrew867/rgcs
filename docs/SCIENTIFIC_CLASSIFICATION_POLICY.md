# RGCS v2 — Scientific Classification Policy

**Author:** Sub-Agent 01 (Source Ingestion and Evidence Ledger)
**Date:** 2026-07-14
**Status:** NON-NEGOTIABLE project policy. Binding on all agents, code, workbooks, CAD, UI, and manuscript text.

## Header: assumptions

1. This policy governs *epistemic labeling*, not scientific merit. A Hypothesis is not an insult; an Established label is not an endorsement of relevance.
2. The policy applies to every claim-bearing artifact: manuscript sentences, code docstrings and outputs, workbook cells, SCAD echo statements, UI text, test names, and release notes.

---

## 1. The four categories

| Label | Definition | Examples |
|---|---|---|
| **Established** | Standard, independently verifiable mathematics, physics, or measurement technique. Anyone with a textbook can check it without trusting this project or its sources. | Half-wave formula f = v/2L; 2×2 eigenvalues; log-spiral arc length; shear-scalar definition σ² = (1/3)Σ(Hᵢ−Hⱼ)²; Bose–Einstein occupation integral; autocorrelation coherence definition; I/Q demodulation; unit conversions (10⁻¹⁴ A = 62,415 e/s). |
| **Derived** | Computed *within RGCS* from explicitly stated inputs by explicitly stated (usually Established) mathematics. Reproducible from the inputs; inherits the weakest label of its inputs (see §3). | L₅ = 154.052734375 mm given v=6310 m/s and f₀=4096 Hz; ε_R^(f)=0 for (40960, 20480, p=2); exact-cycle allocation 1508 = 754+377+377; k_H = 0.98668 from the 152 mm shortfall; the coupling merit S; the class bins. |
| **Hypothesis** | An RGCS conjecture about the physical world that measurement could falsify. Must ship with a pre-registered test and failure condition. | The compact-coordinate spectrum applies to any RGCS closed path; enhancement localizes near ε_R^(f)=0; the spiral cone beats matched controls; hand loading is first-order added modal mass with η=0.5; relaxation is exponential with branch-independent rate. |
| **Source claim** | A statement made by an external source, reported with provenance but not endorsed. Includes: (a) the JH/Vogel corpus claims (frequencies, angles, node descriptions, operating points, effects); (b) the three papers' *physical* conclusions in their own domains (dark-matter viability, mLQC-I cosmology, magnon-BEC interpretation, setup-specific numbers like 21 dBm or σ₁ ≃ 2.498 m_Pl). | "4096 Hz is the core frequency"; "the eye is vorticial, not the metric center"; "1496 Hz is preferred"; "shear decays with σ₁≃2.498 m_Pl"; "threshold at 21 dBm"; "10⁻⁸ ≤ ε_R ≤ 10⁻⁴ is the desired resonance level". |

**Categories are never merged.** No artifact may use hybrid labels ("semi-established", "effectively confirmed", "consistent with the source"). A claim carrying two aspects is split into two claims (e.g., RG-01: the half-wave *formula* is Established; the *choice* of 4096 Hz is Source claim; the *applicability* to a faceted crystal is Hypothesis).

## 2. Special rule for the three reference papers

The papers (Lee & Tsai 2026; Gan et al. 2025; Koster et al. 2026) are peer-reviewed physics. Within RGCS:

- Their **mathematical identities and measurement definitions** are Established (LT Eqs. 1–2, 9–10, 13 as algebra; GAN Eq. 2; KOS coherence definition).
- Their **model-dependent results and numbers** are Source claims (LT viable κ² range; GAN σ₁ ≃ 2.498 m_Pl; KOS 21 dBm threshold).
- Their **physical subject matter is never physically equivalent to RGCS systems.** RGCS adapts *mathematics as analogy*; the manuscript, UI, and code must say "analogue", "template", or "adapted from" — never "the crystal's Kaluza–Klein modes", "the crystal condenses", or "quantum damping in quartz".
- Every adapted equation must cite the exact source equation number and state the substitution map (e.g., m → f, 1/R → v_χ/(2πR_χ)).
- Every *not-adapted* concept in the ledger's exclusion lists (LT-10/18/19/20/21; GAN-15's cosmology-specific list; KOS-15's magnon-specific list) is forbidden as an RGCS physical claim.

## 3. Label propagation through derived quantities

1. **Weakest-link rule.** A derived quantity inherits the *weakest* label among its inputs and its method, with the ordering Established > Derived > Hypothesis > Source claim being a *provenance* ordering, not a confidence ordering. Practically:
   - Established method + Established inputs → Derived (it is still a project computation).
   - Established method + Source-claim input → **Derived-from-Source-claim**: label "Derived" with mandatory provenance note naming the Source claim (e.g., G-04: 110 mm match is arithmetic resting on the JH length and the Hypothesis that the 1D model applies).
   - Any chain containing a Hypothesis → the output is at best Hypothesis-conditioned; it may be labeled Derived only if the text/metadata names the conditioning Hypothesis.
2. **No laundering.** Repeating a computation, averaging it, plotting it, or embedding it in a score never upgrades its label. In particular the coupling merit S and the workbook "resonance class" strings are Derived heuristics and can never be reported as evidence.
3. **Measurement upgrades.** Only a pre-registered, control-subtracted measurement campaign (with the ledger's test consequences satisfied) can move a Hypothesis toward "supported"; even then the label remains Hypothesis with a recorded evidential status field (`untested | testing | supported | refuted | ambiguous`). RGCS v2 itself contains no claim with status other than `untested` or `refuted/ambiguous` (the JH negative results).
4. **Sign and uncertainty propagate with labels.** ε_R^(f) computed from corrected frequencies must carry the correction ledger's uncertainty; a resonance-class string without uncertainty is non-compliant.
5. **Numerical constants.** Golden values (ledger Part E) are Derived and versioned; source-specific operating numbers (21 dBm, 2.498 m_Pl, 281 mT, 10⁻⁸–10⁻⁴) may appear ONLY in source-summary contexts, never as RGCS defaults, targets, or thresholds.

## 4. Enforcement requirements

### 4.1 Code (rgcs_core)
- Every public function returning claim-bearing quantities carries a machine-readable classification: a `classification` field in returned dicts or a documented module-level `CLASSIFICATIONS` map, naming the label and (for Derived/Hypothesis) the source rows (e.g., `"LT-15"`, `"RG-06"`).
- Docstrings of adapted functions must contain the substitution map and the citation (paper, equation).
- Functions implementing heuristics (`coupling_score`, class bins, sweep spans) must state "engineering heuristic — not evidence" in docstring and output.
- Forbidden-vocabulary lint: automated check that code/UI strings never apply `dark matter`, `Kaluza-Klein mode of the crystal`, `BEC`, `condensate`, `quantum damping` (etc.) to RGCS measured quantities outside clearly marked source-summary text.
- Tests must include the golden values (ledger Part E) and at least one test asserting the classification metadata exists.

### 4.2 UI / desktop app
- Every displayed result panel shows its label as a badge (Established / Derived / Hypothesis / Source claim) with hover provenance (source ID, page/equation).
- Source presets (20 Hz/15 V, 1496 Hz, 46/46/184, 45 V/1 µs...) are always rendered under a "Source claim — JH log p.X" banner.
- Hypothesis-labeled outputs display their pre-registered failure condition.
- No UI element may present the coupling merit or resonance class as a measurement.

### 4.3 Workbooks
- Each sheet carries a classification legend; each output block names its label and source row.
- Cells mixing labels are split. The "Interpretation" strings (e.g., "VERY CLOSE") must be annotated as Derived heuristics.

### 4.4 Manuscript
- The traceability matrix gains a Classification column and a **Not adapted** section per paper (from ledger exclusion rows).
- Every equation is introduced with its label; adapted equations state the substitution map and citation inline.
- The abstract and conclusion may not contain unlabeled claims; the phrase "physical correspondence is determined by measurement, not assumed by terminology" (existing TEX) is retained verbatim.
- Negative results (JH-015, JH-031, JH-033) appear in a dedicated ledger section labeled Source claim (negative), with the KOS-motivated caveat "amplitude-null, coherence-untested" where applicable.
- Numerology content (powers-of-eight ladder, golden angle, 2.45 GHz decoding) appears only as Established arithmetic auditing Source claims; no physical inference.

### 4.5 CAD / SCAD
- Header comments state the label of every embedded constant (preset dimensions = Source claim; ideal lengths = Derived; mode rings = Hypothesis visual aid).
- `echo` output includes the label for computed quantities used downstream.

### 4.6 QA gates (for Sub-Agent 08)
1. Grep gate: no unlabeled adapted equation in manuscript.
2. Vocabulary gate: forbidden physical-equivalence phrases absent.
3. Ledger-coverage gate: every equation in manuscript/core maps to a SOURCE_EVIDENCE_LEDGER row.
4. Golden-value gate: Part E values reproduced by tests.
5. Category-merge gate: no hybrid labels anywhere.
