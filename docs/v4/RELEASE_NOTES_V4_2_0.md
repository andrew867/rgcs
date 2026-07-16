# RGCS v4.2.0 — release notes

**Master Research Expansion.** The post-v4.1 backlog is translated into
equations, observables, controls, uncertainty, failure conditions, and an
honest status per item. The validated v4.1 quartz core is unchanged, and
every prior tag (v2.0.0, v3.0.x, v4.0.0, v4.1.0, v4.1.1) is untouched.

## Read this first

**Nothing in this release is an experimental result.** Every experimental
campaign is a protocol. No hardware was operated. No data was measured.
A protocol is not a completed experiment, and this release does not claim
otherwise anywhere.

**The Eye sub-millimetre question is open.** The refinement returned
`INSUFFICIENT_RESOLUTION`: the mesh ladder ran out of resolution before it
answered the question. It did not refute coincidence with the conventional
node and it did not establish distinctness. The canonical v4.1 record
(candidate (−0.295, −0.205, 102.240) mm, separation 3.906 mm, halfwidth
3.08 mm) stands unchanged and is not superseded. No proximity threshold is
used anywhere; exact coincidence means the 1e-6 mm numerical tolerance.

## What is in it

- **Coverage ledger, 248/248.** Every master-ledger ID has an owner, an
  artifact, and a disposition. Gate G42 is enforced by a test, so an
  uncovered ID fails the build.
- **Computational**: polariton reference models (2×2/3×3 Hopfield),
  Eye refinement, harmonic family N=5…12, frequency-key registry with a
  look-elsewhere null model, BVD extraction, apparatus models, and
  eleven typed microscopic interfaces that refuse to compute.
- **Geometry**: spiral-cone mathematics, pinched twisted-cone variant,
  cymatic PCB disks, matched controls, fabrication exports.
- **Experimental**: nine campaigns, fully specified —
  `PROTOCOL_READY_HARDWARE_REQUIRED` for the bench work,
  `ETHICS_APPROVAL_REQUIRED` for the two human-subject campaigns.
- **Consciousness**: a separate quarantined lane, 52 entries, each with a
  layer, status, evidence tag, and falsification condition.
- **Adversarial QA**: eight attack tests, all repelled.

## Blockers (explicit)

| Blocker | Affected |
|---|---|
| Hardware required | E01–E05, E08, E09 (E001–E027, W001–W017) |
| Ethics approval required | E06, E07 (H001–H017) |
| Resolution insufficient | Eye sub-mm refinement (A07, A08) |
| Deferred by design | I001–I011 microscopic interfaces |

## Verify

```bash
python -m pytest -q --deselect tests/regression/test_generator_determinism.py::test_generator_deterministic
# expect: 681 passed
python tools/v4x_coverage_ledger.py    # expect: coverage 248/248 G42=PASS
```

The deselected test is a byte-equality check that requires the archived
v2.0.0 build environment; hosted CI deselects exactly that node id per
policy D-V3-04, and its portable numerical twin runs everywhere.

## Documents

- [Programme report](V4X_PROGRAMME_REPORT.md) — all lanes and limitations
- [Coverage ledger](V4X_COVERAGE_LEDGER.md)
- [Eye sub-mm refinement](V4X_EYE_SUBMM_REFINEMENT.md)
- [What this quartz model does not include](WHAT_THIS_QUARTZ_MODEL_DOES_NOT_INCLUDE.md)
