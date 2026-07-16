# Forum Post (technical long-form; HN "Show", research-software forums)

**Title:** Show: RGCS — a claim-classification type system for research
software, demonstrated on a resonant-crystal falsification programme

I've released a research framework with an unusual origin and, I think,
a genuinely useful discipline layer. The origin: a corpus of historical
crystal-practice material (operating frequencies, timing recipes, a
special locus called "the eye") plus a theoretical neuroscience
proposal. The obvious failure modes are laundering (repeat until it
sounds like fact) and erasure (mock and discard). I tried to build a
third option and make it *mechanical*.

**The discipline layer, concretely:**

- Every public function carries a classification decorator
  (Established / Derived / Hypothesis / Source claim / Engineering).
  Derived inherits the weakest input label. A firewall test fails the
  build if a strong claim is computed from weak inputs.
- The previous major version is byte-frozen in-tree (`archive/v2.0.0/`
  + tag), and every generalizing operator must reproduce the frozen
  numbers on the frozen domain, machine-checked on every test run
  ("Conservative Extension Property"). v3 provably didn't rewrite v2.
- Every adapted equation from the literature has a page-level
  provenance row with a *binding* forbidden-transfer clause ("the math
  crosses; the physical conclusion does not"), re-verified by a lint
  that re-hashes the source PDFs.
- Every hypothesis is pre-registered with observable, controls,
  uncertainty, and a failure condition. Several are pre-registered
  **nulls** — e.g. unbiased passive quartz optics is reciprocal, so
  the directional-asymmetry rows *predict no effect* and quantify null
  acceptance with TOST equivalence bounds.
- No number in any manuscript/README figure is hand-typed: generators
  pull from the tested libraries; byte-stability is pinned
  (SOURCE_DATE_EPOCH and friends).

**Status, honestly:** the physics is 100 % unconfirmed and the repo
says so on every surface. What's real today: the 378-test suite,
3-OS CI, the anisotropic elastodynamics (standard Christoffel theory,
handbook constants — the interesting part is that it *explains* the old
scalar model's declared uncertainty band as physical anisotropy), and
a complete bench-validation plan for all 30 registered hypotheses.

**War stories the methodology caught:** independent QA overturned the
project's own coupling sign convention (anti-Hermitian K = i·2πg — the
wrong convention is now a permanent failing-contrast test); two of
three "Windows defects" turned out to be an undeclared dependency;
byte-exact float reproduction turned out to require the archived build
toolchain, not just pinned libraries — the portable CI now verifies
printed-precision equivalence instead, which is the honest claim.

Repo: https://github.com/andrew867/rgcs (MIT). The
`DESIGN_PHILOSOPHY.md` is the 10-minute read if you only read one file.
I'd genuinely value: replication attempts of any bench branch (nulls
welcome — they're pre-registered), portability reports, and criticism
of the statistics plan (`docs/VALIDATION_PLAN.md`) *before* the bench
data exists — that's the point of pre-registration.
