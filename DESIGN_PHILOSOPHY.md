# Design Philosophy

Why this project is built the way it is. Nothing here is new policy —
every rule below is enforced somewhere in the repository; this document
explains the *why* in one place.

## 1. The central problem: inspiration without laundering

The project's questions come partly from unconventional sources — a
historical crystal-practice tradition, personal working logs, a
theoretical neuroscience proposal. Projects in this position usually fail
in one of two ways:

- **Laundering:** source claims are repeated until they read as facts.
- **Erasure:** the source material is discarded or mocked, destroying the
  record of where the questions came from.

Every architectural choice below exists to make both failure modes
*mechanically difficult*, not just discouraged.

## 2. Classification as a type system

Every scientific statement carries one of five labels — Established,
Derived, Hypothesis, Source claim, Engineering plan — attached at the
*definition* (a decorator on the function, a column in the register, a
tag in the manuscript). Derived values inherit the weakest input label,
and a machine firewall rejects strong outputs computed from weak inputs.
Think of it as a type system for epistemic status: the point is not that
mislabeling is forbidden, it's that mislabeling **doesn't compile**.

## 3. Freeze what you ship; extend conservatively

v2.0.0 is byte-frozen (`archive/v2.0.0/`, tag `v2.0.0`) and its 61
equations are immutable. v3 builds *above* it and must prove, on every
test run, that each generalizing operator reproduces the frozen numbers
on the frozen domain (the Conservative Extension Property). Result: a
major version that provably cannot have silently changed its predecessor.
The alternative — "we rewrote it, trust the new tests" — is how projects
quietly lose results.

## 4. Registries over prose

Anything that matters lives in an append-only machine register: equations
(`model_registry.yaml`, `rscs_registry.yaml`), symbols (the notation
ledger), claims (with observable/controls/failure-condition columns),
decisions (the decision log), source adaptations (with a binding
`forbidden_transfer` column). Prose documents cite registers; registers
never cite prose. Ids are never renumbered. This is why a five-agent-long
change history remains auditable.

## 5. Pre-registration, including of nulls

Every hypothesis is registered with its failure condition *before* any
bench work — and where conventional physics predicts nothing (directional
optical asymmetries in unbiased passive quartz), the expected outcome is
registered as a **null**. A project that can say "we expect to see
nothing, and here is exactly what would change our minds" is harder to
fool, including by itself.

## 6. Generated numbers only

No number appearing in a manuscript, README figure, or comparison table
is typed by a human. Generators (`tools/make_*`) pull from the tested
libraries; determinism checks pin the output byte-for-byte
(`SOURCE_DATE_EPOCH` for PDFs). If a document and the code disagree, the
build fails — the document cannot drift.

## 7. Fail loud, never guess

Invalid coordinates raise at construction; NaN never propagates; unknown
schema versions are errors; a missing migration hook is an error; an
uncalibrated timing channel is *phase-invalid* and flagged, not silently
used. Every "helpful" silent fallback is a place where a wrong number
enters a result chain unnoticed.

## 8. Safety as a hard envelope, not advice

Operating limits (D7-003) are encoded in schemas (`maximum:` fields),
checked in code (`safe_drive_check`), compiled into the firmware contract
(config may tighten, never loosen), and repeated in every relevant
document. Dummy-load-first is mandatory. Nothing describable in this
repository operates on a human.

## 9. Earn complexity

Every richer model must beat a simpler baseline before it is used: the
anisotropic model only applies when orientation is measured; the
coupled-mode model only in the strong-coupling regime; the measured node
supersedes every theoretical definition. Complexity that does not change
a prediction is refused — this single rule has deleted more speculative
machinery than any review.

## 10. Negative results are deliverables

`docs/NEGATIVE_RESULTS.md` is a first-class register. A falsified
hypothesis is retired with its evidence, not reinterpreted. The project's
credibility budget is spent on the honesty of its failures.
