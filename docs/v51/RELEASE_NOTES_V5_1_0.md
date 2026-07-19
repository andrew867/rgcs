# RGCS v5.1.0 — Open Commons Release

RGCS v5.1.0 is an open, evidence-governed framework for relational
coordinate records, periodic phase ambiguity, nested reference
frames, uncertainty, provenance, and explicit scientific refusal.

**Software verified. Physically untested.** The corpus contains
**zero** bench measurements. See `SCIENTIFIC_BOUNDARIES.md`.

## The motivating question

> It appears possible. Can it be proved, measured, implemented, or
> honestly refused?

So far, for the physical layer, the answer has been *refused* or
*unmeasured* every time. Those results are published alongside
everything else.

## What is in this release

**Coordinate and timing infrastructure** — typed roots with alias
sets retained rather than collapsed, ordered frame chains with
covariance propagation, exact address transcoding, phase authority
and epoch declarations, evidence classes enforced in code, and
refusal as a first-class typed output.

**Three manuscripts**, each positioned by adversarial prior-art
review rather than by ambition:

- *Two Notions of Phase Closure in Multi-Tone DDS* — short
  correspondence. The closure formula itself is published prior art;
  the surviving result is that continuous and sampled closure differ
  by exactly `odd_part(gcd(K))`.
- *Null calibration* — tutorial. The principle is the severity
  requirement and the positive control, and is **not** claimed as new.
  The contribution is an executable harness and three worked failures
  from this project's own history.
- *Relational Root-Space Coordinates* — technical report. Six of
  seven components are textbook; the contribution is the integration,
  and its value still requires external evaluation.

**The negative results**, which are most of the science: metric
actuation refused by arithmetic at ≥17.8 decades, sovereign
navigation unsupported, CW vector structure carrying zero informative
bits, consumer quartz unable to resolve a metre at any integration
time, planetary symmetry with no data to test.

**The corrections**, including several to our own earlier claims —
the Pound–Rebka "validation" that compared a formula against itself,
a covariance clamp that reported perfect knowledge for an impossible
input, and a symmetry detector that was blind at every injection
strength.

## Commons layer

`HUMANITY_COMMONS_CHARTER.md` · `SCIENTIFIC_BOUNDARIES.md` ·
`NON_CLAIMS.md` · `LICENSE_MAP.md` ·
`PATENT_NON_ASSERTION_INTENT.md` (policy intent, **not** a covenant,
pending legal review).

**No relicensing.** MIT stands exactly as attached to earlier
releases.

## Disclosure history

v3.0.0 through v4.8.1 were public under MIT between 2026-07-15 and
2026-07-18 — a dated public source release, not an organised
defensive publication. R6, R7 and R8.1 were developed privately and
are first published here. See
`docs/v51/RGCS_RELEASE_AND_DISCLOSURE_TIMELINE.md`.

## What this release does not claim

No metric actuation. No portal. No gravity control. No nonlocal
transport. No Phryll detection. No spin memory in quartz. No medical
claim. No contact or timeline claim. No standards authority.

Full list: `NON_CLAIMS.md`.

## Verification

```
# expect: 2416 passed
python -m pytest -q --deselect \
  tests/regression/test_generator_determinism.py::test_generator_deterministic
```

Measured from a **clean clone of the tagged commit**, which is what
the published test-report asset contains. A full working copy reports
more because five tests require optional untracked content (prompt
packs, eye corpus, reference PDFs), each skipping with "expected on
CI".

Adversarial audit: 19/19.

## Review invited

This is the point of publishing. See `HOW_TO_REVIEW_RGCS.md` and
`EXTERNAL_REVIEW_REQUEST.md`. The most useful thing a reader can do
is attack the integration claim: does covariance-aware frame chaining
catch real errors, or is it ceremony?

The next real experiment is the differential clock-link baseline — a
common-source split, which costs almost nothing and is the only way
to learn what the measurement chain itself contributes.
