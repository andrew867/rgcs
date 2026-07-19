# v5.1.0 Final Operator Report

Release published and publicly verified 2026-07-19.
Tag `v5.1.0` at `cfcfaa5`. Repository visibility: **PUBLIC**.

## 1. What exists

A coordinate, timing, evidence and assurance framework: typed roots
with alias sets retained rather than collapsed, ordered frame chains
with covariance propagation, exact address transcoding, phase
authority and epoch declarations, evidence classes enforced in code,
and refusal as a first-class typed output. Plus a Windows workbench,
a 39-sheet evidence workbook, and 2420 tests.

## 2. What is mathematically correct

- The exact radix identity, exhaustively verified over all 4096 keys.
- The DDS common-closure formula and its continuous/sampled
  discrepancy, `odd_part(gcd K)`, verified across six gcd cases and
  against brute force.
- Wigner D-matrices and polyhedral projectors, reproducing the
  textbook invariant degrees independently.
- Weak-field clock formulae, reproduced correctly.
- MDEV/TDEV against their definitional anchors.

## 3. What is standard prior art

Almost all of it, and this is now stated in the published documents
rather than discovered by a referee:

- DDS closure — Nicholas & Samueli (1987), Hwang et al. (2017),
  Fujifilm US12422666B2.
- Null-calibration principle — the severity requirement (Mayo &
  Spanos), the positive control, injection-recovery, blind analysis.
- Integer ambiguity, wide-lane, dual-carrier thinning — textbook GNSS.
- Barycentric frames, emission coordinates, relativistic clock models
  — IAU, SPICE, astropy, Coll–Ferrando–Morales, Rovelli, Ashby.
- Multipath channel estimation — declared textbook by the programme
  itself in v4.7.

## 4. What integration may be useful

One thing, honestly: **the covariance-carrying frame chain**. SPICE,
astropy and ROS tf2 verifiably do not propagate covariance through a
frame chain, and tf2's omission is a long-standing acknowledged
limitation.

Its value is **unproven**. There is no case on record where the
integrated object caught an error the separate standard tools would
miss. That is the evaluation being requested.

## 5. What was corrected

| ID | Correction |
|---|---|
| R8-D-001 | Pound–Rebka "validation" compared a formula against itself; claim withdrawn |
| R8-D-002 | frame-chain quadrature contradicted the covariance field |
| R8-D-003 | MDEV/TDEV named in the plan but not implemented |
| R8-D-004 | `frozen: true` implied external preregistration |
| R8-D-005 | non-PSD correlation returned 0.0 m — reporting perfect knowledge |
| R8-D-006 | anti-stale hash covered none of r6, r7 or r8 across three releases |

Earlier generations: the granularity-mismatched null that inverted a
headline, the blind symmetry detector, the Wigner phase error
invisible to structural checks, the workbook column loss.

## 6. What failed

Nearly every physical claim. Metric actuation refused by arithmetic
at ≥17.8 decades. Sovereign navigation unsupported. CW vector
structure carrying zero informative bits. Source frequencies not
significant at p = 0.662. Consumer quartz unable to resolve a metre
at any integration time. Planetary symmetry with no data to test.
Passive self-oscillation refused. Quartz spin memory blocked.

## 7. What remains unmeasured

**Everything.** 271 canonical records, zero at any physical evidence
class. No coil wound, no crystal driven, no oscillator pair compared,
no field mapped, no geophysical data loaded.

## 8. What was published

Repository public under MIT. Release v5.1.0 with 17 assets, all
hashes verified after anonymous download. Source, Windows binaries,
workbook, test report, provenance, and the five commons documents.

Anonymous verification passed: unauthenticated API reports
`private: false`, MIT detected; unauthenticated raw fetches of
LICENSE, SCIENTIFIC_BOUNDARIES, HUMANITY_COMMONS_CHARTER and
NON_CLAIMS all returned 200; unauthenticated asset download returned
200.

## 9. What remains private

`internal-docs/` (gitignored, confirmed 404 anonymously) and
`source_claims/` (untracked). No prompt packs, no third-party corpus,
no personal material.

## 10. What external humans should review first

1. **Does covariance-aware frame chaining catch real errors, or is it
   ceremony?** This is the whole integration claim.
2. Are the refusal states useful or burdensome in practice?
3. Is the continuous/sampled DDS distinction real and worth a
   correspondence, or did we miss prior art? ADI AN-1396 and the full
   FSK/PSK article were **not** directly readable during review —
   analog.com was unreachable — so that search is explicitly
   incomplete.
4. Is IVOA STC 1.33 close enough to make the certificate redundant?

## 11. What experiment comes next

The differential clock-link baseline: a common-source split. It costs
almost nothing, and it is the only way to learn what the measurement
chain itself contributes. Every later claim depends on that number.

Second finding worth acting on: at the minimal tier the **counter**,
not the oscillator, sets the short-τ floor until about 2000 s. Spend
on the counter first.

## 12. Exact legal and stewardship steps remaining

1. **Pull the true visibility-flip timestamp** from the GitHub
   account audit log. The repository can only infer it; the log
   records it.
2. **Patent-agent triage**, using the checklist in
   `PATENT_NON_ASSERTION_INTENT.md`. Publishing did not remove this
   need — it changed what the triage is about. Determine which
   subject matter was first disclosed in the 2026-07-15→18 public
   window versus first disclosed at v5.1.0.
3. **Decide whether the non-assertion intent becomes a covenant.** It
   is currently marked policy intent, deliberately not binding.
4. **Stewardship transfer** to a purpose-bound non-profit, if pursued.
5. **ISO 19111 / OGC Abstract Topic 2** was never checked and should
   be before any coordinate submission.

---

## Personal provenance and research history

Excluded from this release at the operator's instruction. No file,
reference or index entry was created.

The channelling transcript referenced by the closeout prompt was
never supplied in-conversation and was therefore not archived. No
placeholder was created — an empty record that looks like an archive
is worse than an absent one.
